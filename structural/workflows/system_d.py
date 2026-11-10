"""
System D Workflow: Ballasted Non-Penetrating System
Package: structural.workflows.system_d

Engineering Specifications:
- Non-penetrating flat roof mounting system
- Precast concrete ballast blocks (M25 grade) with EPDM protective friction pads
- Aerodynamic rear wind deflector to reduce upward suction
- Relies strictly on gravitational weight and friction interface to resist wind shear and uplift
- Zero adverse live load (IL = 0) during wind sliding and overturning checks
- Governed by FRICTION_UNVERIFIED_HOLD and AERODYNAMIC_UNSUPPORTED_HOLD
"""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Tuple

from structural.models import (
    MountingSystemType,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
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


class SystemDBallastedWorkflow:
    """Specialized engineering workflow for System D: Ballasted Non-Penetrating System."""

    SYSTEM_TYPE = MountingSystemType.SYSTEM_D_BALLASTED

    def __init__(self, site: SiteParameters, geometry: ArrayGeometry):
        if geometry.mounting_system != self.SYSTEM_TYPE:
            raise ValueError(f"Geometry mounting system {geometry.mounting_system} does not match System D.")
        self.site = site
        self.geometry = geometry
        self.engine = StructuralCalculationEngine(site=site, geometry=geometry)

    def get_applicable_holds(self) -> List[HoldRecord]:
        return MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(self.SYSTEM_TYPE.value)

    def run_workflow_analysis(
        self,
        ballast_weight_kn_per_m2: float = 0.65,
        friction_coeff_mu: float = 0.40,
    ) -> CalculationReport:
        """Executes ballast sizing, contact-loss check, and sliding resistance evaluation."""
        report = CalculationReport(
            project_id=f"RENSUN-SYS-D-{self.site.location_name}",
            system_type=self.SYSTEM_TYPE,
            governing_summary="System D Ballasted Non-Penetrating Engineering Assessment",
        )

        # 1. Verification holds check
        holds = self.get_applicable_holds()
        report.active_holds = [h.hold_id for h in holds]
        report.log(f"System D Active Verification Holds: {len(holds)}")
        for h in holds:
            report.log(f"  [{h.hold_id}] ({h.category.value}) — ACTIVE")

        # 2. Ballast Stability Evaluation
        ballast_results = self.engine.check_ballast_stability(
            ballast_dead_weight_kn_per_m2=ballast_weight_kn_per_m2,
            friction_coeff_mu=friction_coeff_mu,
        )
        for res in ballast_results:
            report.add_result(res)
            report.log(res.summary_line())

        # 3. Ballast Overturning Moment Stability Check (ULS-02, IL = 0)
        # Chassis length in m: module length * cos(tilt)
        import math
        tilt_rad = math.radians(self.geometry.module.tilt_deg)
        chassis_len_m = (self.geometry.module.length_mm / 1000.0) * math.cos(tilt_rad)
        h_cg_m = 0.5 * (self.geometry.module.length_mm / 1000.0) * math.sin(tilt_rad)

        _, pz_kpa, _ = self.engine.calculate_design_wind_speed_and_pressure()
        cn_up, _ = self.engine.compute_aerodynamic_coefficients()
        q_wind_kpa = abs(cn_up) * pz_kpa
        F_wind_h_kn_m2 = 1.5 * q_wind_kpa * math.sin(tilt_rad)
        F_wind_v_kn_m2 = 1.5 * q_wind_kpa * math.cos(tilt_rad)

        total_dl_kn_m2 = self.geometry.module.dead_load_kn_per_m2 + ballast_weight_kn_per_m2
        total_added_dl_kn_m2 = total_dl_kn_m2
        M_restoring_kn_m = (0.9 * total_dl_kn_m2) * (chassis_len_m / 2.0)
        M_overturn_kn_m = (F_wind_h_kn_m2 * h_cg_m) + (F_wind_v_kn_m2 * (chassis_len_m / 2.0))

        fos_ot = M_restoring_kn_m / M_overturn_kn_m if M_overturn_kn_m > 0 else 999.0
        unity_ot = (1.4 * M_overturn_kn_m) / M_restoring_kn_m if M_restoring_kn_m > 0 else 999.0

        res_overturn = CalculationResult(
            check_name="Ballast Overturning Stability about Leeward Toe",
            demand_value=1.4 * M_overturn_kn_m,
            capacity_value=M_restoring_kn_m,
            unity_ratio=unity_ot,
            units="kN*m/m2",
            governing_combination="ULS-02 (0.9 DL Restoring vs 1.5 WL Overturning, IL = 0)",
            passed=(unity_ot <= 1.0),
            clause_reference="IS 875 (Part 3) & IS 800: 2007 Clause 5.3",
            notes=f"Overturning FOS={fos_ot:.2f} (Required >= 1.40) with adverse live load strictly zero.",
        )
        report.add_result(res_overturn)
        report.log(res_overturn.summary_line())

        # 4. Host Roof Slab Additional Load Assessment (ULS-01 Gravity)
        # Total added dead load = Module DL + Ballast DL
        max_permitted_slab_dl_kn_m2 = 1.50  # Typical residential/commercial roof live load reserve

        unity_slab = total_added_dl_kn_m2 / max_permitted_slab_dl_kn_m2
        res_slab = CalculationResult(
            check_name="Host Roof Slab Additional Dead Load vs Nominal Allowance (1.50 kN/m2 — UNVERIFIED PROVISIONAL)",
            demand_value=total_added_dl_kn_m2,
            capacity_value=max_permitted_slab_dl_kn_m2,
            unity_ratio=unity_slab,
            units="kN/m2",
            governing_combination="ULS-01 (Dead Load of Module + Ballast Blocks)",
            passed=(unity_slab <= 1.0),
            clause_reference="IS 875 (Part 2) & TNCDBR-2019 Rule 35",
            notes=(
                f"NOMINAL SCREENING CHECK ONLY: Added dead weight of {total_added_dl_kn_m2:.2f} kN/m2 is compared "
                f"to an assumed 1.50 kN/m2 allowance. This does NOT verify parent RCC slab bending, punching shear, "
                "supporting beams, columns, or foundations. Formal slab structural certification required under INSPECTION_REQUIRED_HOLD."
            ),
        )
        report.add_result(res_slab)
        report.log(res_slab.summary_line())

        # Explicitly log unsupported checks and provisional parameters for System D
        report.unsupported_checks = [
            "In-Situ Static Friction Pull-Slip Testing under Wet & Dry Conditions (ASTM C1028)",
            "Boundary Layer Wind Tunnel Aerodynamic Wind Uplift Factor Calibration",
            "Host RCC Slab Concentrated Ballast Point Load Punching Shear Check",
            "Parent Building Beam & Column Structural Reserve Capacity for Added Dead Weight",
            "Parapet Aerodynamic Shielding / Cavity Wake Turbulence Modeling",
            "Elastomeric EPDM Pad Long-Term Aging & Creep Under UV Exposure",
        ]
        report.provisional_inputs = [
            "Static friction coefficient mu (assumed 0.40 catalogue default, held by FRICTION_UNVERIFIED_HOLD)",
            "Host roof allowable superimposed dead load (assumed 1.50 kN/m2 without structural drawings)",
            "Effective parapet height around perimeter",
        ]
        for uc in report.unsupported_checks:
            report.log(f"  [UNSUPPORTED_CHECK] {uc} — Requires in-situ testing / RSE slab load verification.")

        return report
