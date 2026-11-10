"""
System C Workflow: Metal-Sheet Roof Mounting
Package: structural.workflows.system_c

Engineering Specifications:
- Flush/parallel mounting on pitched industrial metal sheet roofs (trapezoidal / standing-seam)
- Extruded aluminium short-rails or non-penetrating standing-seam clamps
- EPDM isolation gaskets to prevent galvanic bimetallic corrosion
- Pull-out and pull-over resistance checks against sheet substrate
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


class SystemCMetalSheetWorkflow:
    """Specialized engineering workflow for System C: Metal-Sheet Roof Mounting."""

    SYSTEM_TYPE = MountingSystemType.SYSTEM_C_METAL_SHEET

    def __init__(self, site: SiteParameters, geometry: ArrayGeometry):
        if geometry.mounting_system != self.SYSTEM_TYPE:
            raise ValueError(f"Geometry mounting system {geometry.mounting_system} does not match System C.")
        self.site = site
        self.geometry = geometry
        self.engine = StructuralCalculationEngine(site=site, geometry=geometry)

    def get_applicable_holds(self) -> List[HoldRecord]:
        return MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(self.SYSTEM_TYPE.value)

    def run_workflow_analysis(
        self,
        sheet_clamp_tensile_capacity_kn: float = 3.50,
        sheet_gauge_bmt_mm: float = 0.50,
    ) -> CalculationReport:
        """Executes sheet fixing pull-out and clamp uplift check."""
        report = CalculationReport(
            project_id=f"RENSUN-SYS-C-{self.site.location_name}",
            system_type=self.SYSTEM_TYPE,
            governing_summary="System C Metal Sheet Roof Mount Engineering Assessment",
        )

        # 1. Verification holds check
        holds = self.get_applicable_holds()
        report.active_holds = [h.hold_id for h in holds]
        report.log(f"System C Active Verification Holds: {len(holds)}")
        for h in holds:
            report.log(f"  [{h.hold_id}] ({h.category.value}) — ACTIVE")

        # 2. Wind Uplift on Sheet Clamp
        _, pz_kpa, _ = self.engine.calculate_design_wind_speed_and_pressure()
        cn_up, _ = self.engine.compute_aerodynamic_coefficients()

        # Tributary area per clamp (4 clamps per module)
        tributary_clamp_area_m2 = (self.geometry.module.length_mm * self.geometry.module.width_mm / 4.0) / 1.0e6
        Tu_clamp_uplift_kn = 1.5 * abs(cn_up) * pz_kpa * tributary_clamp_area_m2

        # Characteristic capacity of sheet clamp
        unity_clamp = Tu_clamp_uplift_kn / sheet_clamp_tensile_capacity_kn if sheet_clamp_tensile_capacity_kn > 0 else 999.0

        res_sheet_clamp = CalculationResult(
            check_name="Metal Sheet Clamp Seam Tensile Pull-Out (ULS-02 Provisional)",
            demand_value=Tu_clamp_uplift_kn,
            capacity_value=sheet_clamp_tensile_capacity_kn,
            unity_ratio=unity_clamp,
            units="kN",
            governing_combination="ULS-02 (1.5 WL_up on clamp tributary)",
            passed=(unity_clamp <= 1.0),
            clause_reference="IS 800: 2007 Clause 10.3 & IS 875 (Part 3) Table 5",
            notes=(
                f"UNVERIFIED PROVISIONAL CAPACITY: Assumed clamp tensile capacity of {sheet_clamp_tensile_capacity_kn:.2f} kN "
                f"is a catalogue screening assumption, NOT a derived physical capacity for the host roof sheet (BMT={sheet_gauge_bmt_mm:.2f} mm). "
                "Fastener pull-out, pull-over, standing seam distortion, and purlin gauge adequacy are UNSUPPORTED and governed by "
                "FASTENER_TORQUE_UNVERIFIED_HOLD and ASSUMED_DATA_CERTIFICATION_HOLD."
            ),
        )
        report.add_result(res_sheet_clamp)
        report.log(res_sheet_clamp.summary_line())

        # Explicitly log unsupported checks and provisional parameters for System C
        report.unsupported_checks = [
            "In-Situ Self-Drilling Screw (SDS) Pull-Out & Pull-Over Capacity (AISI S100 / ASTM E1592)",
            "Standing Seam Clamp Mechanical Friction-Grip Slip Resistance",
            "Host Sheet Metal Profile Crushing & Crest Bending Distortion",
            "Underlying Purlin-to-Rafter Load Transfer Capacity",
            "Waterproofing Gasket Degradation & Corrosion Under Environmental Exposure",
        ]
        report.provisional_inputs = [
            "Sheet clamp tensile pull-out capacity (assumed 3.50 kN catalogue default)",
            "Roof sheet base metal thickness (assumed 0.50 mm BMT without ultrasonic gauge)",
            "Host roof purlin spacing and gauge",
        ]
        for uc in report.unsupported_checks:
            report.log(f"  [UNSUPPORTED_CHECK] {uc} — Requires in-situ pull-out testing per SHEET_PULLOUT_HOLD.")

        return report
