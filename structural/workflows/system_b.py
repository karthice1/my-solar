"""
System B Workflow: Low-Height Aluminium Rail
Package: structural.workflows.system_b

Engineering Specifications:
- Low-height rooftop rail system (100 mm to 300 mm clearance)
- Extruded aluminium alloy 6063-T6 / 6005-T5 mounting rails (IS 733 / IS 8147: 1976)
- Stainless steel A2-70 / A4-70 module clamping hardware
- Governed by ALUMINIUM_DERIVATION_HOLD and FASTENER_TORQUE_UNVERIFIED_HOLD
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from structural.models import (
    MountingSystemType,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldRecord,
)
from structural.engine import (
    StructuralCalculationEngine,
    CalculationReport,
)


class SystemBAluminiumRailWorkflow:
    """Specialized engineering workflow for System B: Low-Height Aluminium Rail."""

    SYSTEM_TYPE = MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL

    def __init__(self, site: SiteParameters, geometry: ArrayGeometry):
        if geometry.mounting_system != self.SYSTEM_TYPE:
            raise ValueError(f"Geometry mounting system {geometry.mounting_system} does not match System B.")
        self.site = site
        self.geometry = geometry
        self.engine = StructuralCalculationEngine(site=site, geometry=geometry)

    def get_applicable_holds(self) -> List[HoldRecord]:
        return MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(self.SYSTEM_TYPE.value)

    def run_workflow_analysis(
        self,
        rail_section: SectionProperty,
        bracket_spacing_mm: float = 1400.0,
    ) -> CalculationReport:
        """Executes full multi-component analysis for aluminium mounting rail."""
        report = CalculationReport(
            project_id=f"RENSUN-SYS-B-{self.site.location_name}",
            system_type=self.SYSTEM_TYPE,
            governing_summary="System B Low-Height Aluminium Rail Engineering Assessment",
        )

        # 1. Verification holds check
        holds = self.get_applicable_holds()
        report.active_holds = [h.hold_id for h in holds]
        report.log(f"System B Active Verification Holds: {len(holds)}")
        for h in holds:
            report.log(f"  [{h.hold_id}] ({h.category.value}) — ACTIVE")

        # 2. Rail Bending & Deflection Checks
        trib_width_mm = self.geometry.module.width_mm / 2.0  # Two rails per module
        rail_results = self.engine.check_purlin_member(
            section=rail_section,
            span_mm=bracket_spacing_mm,
            tributary_width_mm=trib_width_mm,
        )
        for res in rail_results:
            res.notes += (
                " LIMITATION: Evaluated with gross section properties (Zxx). Thin-walled effective section (Zeff), "
                "local/distortional plate buckling (IS 8147 Cl 5.2 / EN 1999-1-1), HAZ softening, and clamp lip yielding "
                "are NOT VERIFIED and governed by ALUMINIUM_DERIVATION_HOLD."
            )
            report.add_result(res)
            report.log(res.summary_line())

        # 3. Clamp Pull-out & Fastener Tensile Check (ULS-02 Wind Uplift)
        _, pz_kpa, _ = self.engine.calculate_design_wind_speed_and_pressure()
        cn_up, _ = self.engine.compute_aerodynamic_coefficients()
        tributary_clamp_area_m2 = (self.geometry.module.length_mm * self.geometry.module.width_mm / 4.0) / 1.0e6
        Tu_wind_uplift_kn = 1.5 * abs(cn_up) * pz_kpa * tributary_clamp_area_m2

        # A2-70 M8 bolt tensile capacity: As = 36.6 mm2, fub = 700 MPa
        # T_capacity = (0.9 * fub * As) / gamma_m2 per IS 800 Cl 10.3.5
        As_m8_mm2 = 36.6
        gamma_m2 = 1.25
        T_capacity_kn = (0.9 * 700.0 * As_m8_mm2 / gamma_m2) / 1000.0
        unity_clamp = Tu_wind_uplift_kn / T_capacity_kn if T_capacity_kn > 0 else 999.0

        res_clamp = CalculationResult(
            check_name="Module Mid-Clamp Fastener Tension (ULS-02 Wind Suction)",
            demand_value=Tu_wind_uplift_kn,
            capacity_value=T_capacity_kn,
            unity_ratio=unity_clamp,
            units="kN",
            governing_combination="ULS-02 (1.5 WL_up on clamp tributary)",
            passed=(unity_clamp <= 1.0),
            clause_reference="IS 800: 2007 Clause 10.3.5 & ISO 3506-1",
            notes="Requires manufacturer certified torque curve under FASTENER_TORQUE_UNVERIFIED_HOLD.",
        )
        report.add_result(res_clamp)
        report.log(res_clamp.summary_line())

        # Explicitly log unsupported checks and provisional parameters for System B
        report.unsupported_checks = [
            "Extruded Aluminium Thin-Walled Local Buckling & HAZ Reduction (IS 8147: 1976 / EN 1999-1-1)",
            "L-Foot / Bracket Baseplate Tear-Out and Bolt Shear/Tension Interaction",
            "Module Top-Clamp Lip Yielding & Dynamic Slip Resistance",
            "Thermal Expansion & Contraction Stress in Continuous Rails",
            "Chemical / Mechanical Anchor Pull-out from Host RCC Roof Slab (IS 456: 2000)",
        ]
        report.provisional_inputs = [
            "Extruded aluminium alloy 6063-T6 characteristic yield and tensile strength (catalogue default)",
            "Stainless steel A2-70 fastener torque tightening specification",
            "Chemical anchor proof load capacity",
        ]
        for uc in report.unsupported_checks:
            report.log(f"  [UNSUPPORTED_CHECK] {uc} — Requires physical laboratory test / manufacturer MTC.")

        return report
