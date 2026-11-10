"""
System A Workflow: Elevated Steel Rooftop Canopy
Package: structural.workflows.system_a

Engineering Specifications:
- High clearance canopy (2.4 m to 3.5 m clearance for accessible roof utilization)
- Primary rafter, column, and purlin framing in Structural Steel E250 / E350 (IS 2062)
- Governed by IS 875 (Part 3) Table 8 (Canopy roofs, net pressure Cn). Internal pressure Cpi does NOT apply!
- Primary framing carries simultaneous array live load (ACT-IL-02) and walkway live load (ACT-IL-04)
  using IS 800 Table 4 leading (1.5/1.2) and accompanying (1.05/0.53) factors.
- Dedicated construction erection phase governed by Row 4 (1.2 DL + 1.2 ER).
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
    STEEL_E250,
)
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
    LoadCombination,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldRecord,
)
from structural.engine import (
    StructuralCalculationEngine,
    CalculationReport,
)
from structural.workflows.system_a_validation import (
    ThinWalledSectionGeometry,
    PurlinOptionEvaluation,
    SystemAEngineeringValidator,
    ExtendedFramingResults,
    evaluate_extended_framing_and_connections,
)


class SystemACanopyWorkflow:
    """Specialized end-to-end engineering workflow for System A: Elevated Steel Canopy."""

    SYSTEM_TYPE = MountingSystemType.SYSTEM_A_CANOPY

    def __init__(self, site: SiteParameters, geometry: ArrayGeometry):
        if geometry.mounting_system != self.SYSTEM_TYPE:
            raise ValueError(f"Geometry mounting system {geometry.mounting_system} does not match System A.")
        self.site = site
        self.geometry = geometry
        self.engine = StructuralCalculationEngine(site=site, geometry=geometry)

    def get_applicable_holds(self) -> List[HoldRecord]:
        return MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(self.SYSTEM_TYPE.value)

    def run_workflow_analysis(
        self,
        purlin_section: SectionProperty,
        rafter_section: SectionProperty,
        column_section: SectionProperty,
        walkway_width_m: float = 0.80,
    ) -> CalculationReport:
        """Executes full multi-component analysis for elevated steel canopy."""
        report = CalculationReport(
            project_id=f"RENSUN-SYS-A-{self.site.location_name}",
            system_type=self.SYSTEM_TYPE,
            governing_summary="System A Elevated Canopy Engineering Assessment",
        )

        # 1. Verification holds check
        holds = self.get_applicable_holds()
        report.active_holds = [h.hold_id for h in holds]
        report.log(f"System A Active Verification Holds: {len(holds)}")
        for h in holds:
            report.log(f"  [{h.hold_id}] ({h.category.value}) — ACTIVE")

        # 2. Purlin Member Check (Member-level max(IL_point, IL_dist))
        purlin_results = self.engine.check_purlin_member(
            section=purlin_section,
            span_mm=self.geometry.rafter_spacing_mm,
            tributary_width_mm=self.geometry.purlin_spacing_mm,
        )
        for res in purlin_results:
            report.add_result(res)
            report.log(res.summary_line())

        # 3. Primary Rafter Check (Simultaneous Array Live Load + Walkway Live Load)
        rafter_span_m = (self.geometry.rows * self.geometry.module.length_mm) / 1000.0
        rafter_trib_b_m = self.geometry.rafter_spacing_mm / 1000.0

        # Primary rafter gravity actions:
        # DL = Module DL + Purlin tributary + Rafter self-weight + Walkway dead load
        module_dl = self.geometry.module.dead_load_kn_per_m2 * rafter_trib_b_m
        rafter_sw = (rafter_section.mass_kg_m * 9.80665 / 1000.0)
        purlins_total_sw = (purlin_section.mass_kg_m * 9.80665 / 1000.0) * (rafter_span_m / (self.geometry.purlin_spacing_mm / 1000.0))
        purlin_sw_per_m = purlins_total_sw / rafter_span_m if rafter_span_m > 0 else 0.0
        walkway_dl = 0.25 * walkway_width_m  # 0.25 kN/m2 grating self weight
        rafter_dl_kn_m = module_dl + rafter_sw + purlin_sw_per_m + walkway_dl

        # Simultaneous Live Loads:
        # Load Case 1: Array Live leading (1.5 * ACT-IL-02 + 1.05 * ACT-IL-04)
        rafter_il_array_kn_m = ActionRegister.ACT_IL_02.nominal_value * rafter_trib_b_m
        rafter_il_walkway_kn_m = ActionRegister.ACT_IL_04.nominal_value * walkway_width_m

        w_rafter_case1 = 1.5 * rafter_dl_kn_m + 1.5 * rafter_il_array_kn_m + 1.05 * rafter_il_walkway_kn_m
        # Load Case 2: Walkway Live leading (1.5 * ACT-IL-04 + 1.05 * ACT-IL-02)
        w_rafter_case2 = 1.5 * rafter_dl_kn_m + 1.05 * rafter_il_array_kn_m + 1.5 * rafter_il_walkway_kn_m

        if w_rafter_case1 >= w_rafter_case2:
            w_rafter_uls01 = w_rafter_case1
            governing_live_subcase = f"Array Live Leading (1.5*IL_array + 1.05*IL_walkway = {w_rafter_case1:.2f} kN/m)"
        else:
            w_rafter_uls01 = w_rafter_case2
            governing_live_subcase = f"Walkway Live Leading (1.5*IL_walkway + 1.05*IL_array = {w_rafter_case2:.2f} kN/m)"

        Mu_rafter_kn_m = (w_rafter_uls01 * (rafter_span_m ** 2)) / 8.0
        Md_rafter_kn_m = rafter_section.design_moment_capacity_major_kn_m
        unity_rafter = Mu_rafter_kn_m / Md_rafter_kn_m if Md_rafter_kn_m > 0 else 999.0

        res_rafter = CalculationResult(
            check_name="Primary Rafter Sagging Flexure (ULS-01 Simultaneous Live)",
            demand_value=Mu_rafter_kn_m,
            capacity_value=Md_rafter_kn_m,
            unity_ratio=unity_rafter,
            units="kN*m",
            governing_combination=f"ULS-01 [{governing_live_subcase}]",
            passed=(unity_rafter <= 1.0),
            clause_reference="IS 800: 2007 Clause 8.2.1 & Table 4 Row 1",
            notes=(
                f"Evaluated simultaneous array ({rafter_il_array_kn_m:.2f} kN/m) and walkway "
                f"({rafter_il_walkway_kn_m:.2f} kN/m) live loads with leading/accompanying factors."
            ),
        )
        report.add_result(res_rafter)
        report.log(res_rafter.summary_line())

        # 4. Construction Stage Erection Check (ULS-06: 1.2 DL + 1.2 ER)
        w_bare_frame_dl = rafter_sw + purlin_sw_per_m
        w_er = ActionRegister.ACT_ER_01.nominal_value * rafter_trib_b_m
        w_rafter_uls06 = 1.2 * w_bare_frame_dl + 1.2 * w_er
        Mu_erection_kn_m = (w_rafter_uls06 * (rafter_span_m ** 2)) / 8.0
        unity_erection = Mu_erection_kn_m / Md_rafter_kn_m if Md_rafter_kn_m > 0 else 999.0

        res_erection = CalculationResult(
            check_name="Primary Rafter Construction Erection Flexure (ULS-06)",
            demand_value=Mu_erection_kn_m,
            capacity_value=Md_rafter_kn_m,
            unity_ratio=unity_erection,
            units="kN*m",
            governing_combination="ULS-06 (1.2 DL_bare + 1.2 ER)",
            passed=(unity_erection <= 1.0),
            clause_reference="IS 800: 2007 Table 4 Row 4",
            notes="Temporary construction stage check before module placement.",
        )
        report.add_result(res_erection)
        report.log(res_erection.summary_line())

        # 5. Canopy Column Axial Compression & Buckling Check (IS 800 Clause 7.1.2)
        # Tributary vertical load transferred from rafter to column
        Pu_column_kn = (w_rafter_uls01 * rafter_span_m) / 2.0
        col_height_mm = self.geometry.ground_clearance_mm
        effective_length_mm = 1.0 * col_height_mm # pinned base approximation
        ry_mm = column_section.ryy_mm
        slenderness = effective_length_mm / ry_mm if ry_mm > 0 else 999.0

        # Euler buckling stress: fcc = (pi^2 * E) / lambda^2
        E_col = column_section.material.elastic_modulus_mpa
        fy_col = column_section.material.yield_strength_mpa
        gamma_m0_col = column_section.material.gamma_m0
        fcc = (math.pi ** 2 * E_col) / (slenderness ** 2) if slenderness > 0 else 1.0

        # Non-dimensional slenderness lambda_0 = sqrt(fy / fcc)
        lambda_0 = math.sqrt(fy_col / fcc) if fcc > 0 else 999.0
        # Buckling curve b: alpha = 0.34
        alpha_b = 0.34
        phi = 0.5 * (1.0 + alpha_b * (lambda_0 - 0.2) + (lambda_0 ** 2))
        disc = phi ** 2 - lambda_0 ** 2
        chi = 1.0 / (phi + math.sqrt(disc)) if disc >= 0 else 0.5
        chi = min(chi, 1.0)
        fcd = (chi * fy_col) / gamma_m0_col
        Pd_column_kn = (column_section.area_mm2 * fcd) / 1000.0
        unity_column = Pu_column_kn / Pd_column_kn if Pd_column_kn > 0 else 999.0

        res_column = CalculationResult(
            check_name="Canopy Column Axial Buckling Resistance (ULS-01 Concentric Axial Pinned)",
            demand_value=Pu_column_kn,
            capacity_value=Pd_column_kn,
            unity_ratio=unity_column,
            units="kN",
            governing_combination="ULS-01 (Concentric Gravity Axial Force)",
            passed=(unity_column <= 1.0),
            clause_reference="IS 800: 2007 Clause 7.1.2 & Table 9c",
            notes=(
                f"Height={col_height_mm:.0f} mm, Slenderness={slenderness:.1f}, fcd={fcd:.1f} MPa. "
                "LIMITATION: Evaluates concentric compression only. Frame sway stability, second-order (P-Delta) moments, "
                "combined biaxial bending (IS 800 Cl 9.3), and rafter-column moment transfer are UNSUPPORTED and require RSE 2D/3D portal analysis."
            ),
        )
        report.add_result(res_column)
        report.log(res_column.summary_line())

        # Explicitly log unsupported checks and provisional parameters for System A
        report.unsupported_checks = [
            "Column Combined Axial Force & Biaxial Bending Interaction (IS 800: 2007 Clause 9.3)",
            "Portal Frame Second-Order (P-Delta) Stability & Non-Sway Effective Length Derivation",
            "Rafter-to-Column Moment Connection Transfer & Stiffener Web Crippling",
            "Column Baseplate Bending & Concrete Cone Breakout (ACI 318 / fib 58)",
            "Canopy Lateral Sway Drift Serviceability Check (IS 800 Cl 5.6.1)",
            "Sloping Roof Purlin Biaxial Bending Interaction (IS 800 Cl 9.3.1)",
            "Cold-Formed Light-Gauge Steel Local Buckling Check (IS 801: 1975)",
            "Host RCC Roof Slab Punching Shear & Flexural Verification (IS 456: 2000)",
        ]
        report.provisional_inputs = [
            "Site basic wind speed Vb (provisional manual regional contour interpolation)",
            "Property coordinates (municipal centroid fallback, unverified rooftop GPS)",
            "Column base fixity degree (assumed pinned)",
        ]
        for uc in report.unsupported_checks:
            report.log(f"  [UNSUPPORTED_CHECK] {uc} — Requires RSE manual calculation / NDT testing.")

        return report

    def evaluate_purlin_remedies(self, use_steel: bool = True) -> Dict[str, PurlinOptionEvaluation]:
        """Evaluates baseline purlin failure vs Option A (span reduction) vs Option B (section upsize)."""
        validator = SystemAEngineeringValidator(site=self.site, geometry=self.geometry)
        return {
            "BASELINE": validator.evaluate_baseline_reproduction(),
            "OPTION_A": validator.evaluate_option_a(use_steel=use_steel),
            "OPTION_B": validator.evaluate_option_b(use_steel=use_steel),
        }

    def evaluate_extended_framing(
        self,
        rafter_section: SectionProperty,
        column_section: SectionProperty,
        concrete_fck_mpa: float = 20.0,
        baseplate_tp_mm: float = 16.0,
        anchor_embedment_hef_mm: float = 125.0,
    ) -> ExtendedFramingResults:
        """Executes extended primary framing, connection, and stability assessment."""
        return evaluate_extended_framing_and_connections(
            site=self.site,
            geometry=self.geometry,
            rafter_section=rafter_section,
            column_section=column_section,
            concrete_fck_mpa=concrete_fck_mpa,
            baseplate_tp_mm=baseplate_tp_mm,
            anchor_embedment_hef_mm=anchor_embedment_hef_mm,
        )
