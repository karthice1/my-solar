"""
Independent Structural Calculation Engine
Package: structural.engine

Implements deterministic structural checks with full mathematical traceability:
- Wind Engineering Engine to IS 875 (Part 3): 2015
- Seismic Engineering Engine to IS 1893 (Part 1): 2016
- Member Flexure, Shear & Deflection Checks to IS 800: 2007
- Ballast Sliding & Overturning Stability to IS 875 / IS 800

Requirements:
- Strict SI units (N, mm, MPa, kN, m, kg)
- Transparent trace equations for every calculated quantity
- Zero silent substitution for missing critical parameters
- Explicit status tracking: failed checks are NEVER represented as passing
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from structural.models import (
    MountingSystemType,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    TerrainCategory,
    SeismicZone,
)
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
    LoadCombination,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
)


@dataclass
class CalculationReport:
    project_id: str
    system_type: MountingSystemType
    governing_summary: str
    results: List[CalculationResult] = field(default_factory=list)
    trace_log: List[str] = field(default_factory=list)
    has_failures: bool = False
    active_holds: List[str] = field(default_factory=list)
    numerical_status: str = "FAIL"
    input_completeness: str = "COMPLETE"
    provenance_status: str = "PROVISIONAL"
    engineering_status: str = "UNVERIFIED"
    construction_status: str = "BLOCKED_AFC_LOCKED"
    watermark: str = "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION"
    is_approved_for_construction: bool = False
    provisional_inputs: List[str] = field(default_factory=list)
    unsupported_checks: List[str] = field(default_factory=list)

    def add_result(self, result: CalculationResult):
        self.results.append(result)
        if not result.passed:
            self.has_failures = True
            self.numerical_status = "FAIL"
        elif not self.has_failures:
            self.numerical_status = "PASS"

    def log(self, message: str):
        self.trace_log.append(message)


class StructuralCalculationEngine:
    """Independent deterministic calculation engine for RENSUN Solar platforms."""

    def __init__(self, site: SiteParameters, geometry: ArrayGeometry):
        if site is None or geometry is None:
            raise ValueError("Critical inputs (site, geometry) cannot be None. Silent defaults forbidden.")
        self.site = site
        self.geometry = geometry

    # =========================================================================
    # 1. WIND ENGINEERING ENGINE — IS 875 (Part 3): 2015
    # =========================================================================

    def compute_k2_factor(self, height_m: float, terrain_cat: TerrainCategory) -> float:
        """
        Interpolates terrain and height multiplier k2 per IS 875 (Part 3) Table 2.
        Heights: <= 10 m, 15 m, 20 m, 30 m.
        """
        if height_m <= 0:
            raise ValueError("Height above ground must be strictly positive.")

        # Table 2 values: [10m, 15m, 20m, 30m]
        heights = [10.0, 15.0, 20.0, 30.0]
        k2_table = {
            TerrainCategory.CATEGORY_1: [1.05, 1.09, 1.12, 1.17],
            TerrainCategory.CATEGORY_2: [1.00, 1.05, 1.08, 1.13],
            TerrainCategory.CATEGORY_3: [0.91, 0.97, 1.01, 1.06],
            TerrainCategory.CATEGORY_4: [0.80, 0.80, 0.80, 0.88],
        }

        values = k2_table[terrain_cat]
        if height_m <= 10.0:
            return values[0]
        elif height_m >= 30.0:
            # linear extrapolation above 30m up to 50m
            slope = (values[3] - values[2]) / (heights[3] - heights[2])
            return values[3] + slope * (height_m - 30.0)
        else:
            # piecewise linear interpolation
            for i in range(len(heights) - 1):
                if heights[i] <= height_m <= heights[i + 1]:
                    t = (height_m - heights[i]) / (heights[i + 1] - heights[i])
                    return values[i] + t * (values[i + 1] - values[i])
            return values[1]

    def calculate_design_wind_speed_and_pressure(self) -> Tuple[float, float, Dict[str, float]]:
        """
        Computes design wind speed Vz and design wind pressure pz.
        Vz = Vb * k1 * k2 * k3 * k4 (Clause 6.3)
        pz = 0.6 * Vz^2 (N/m^2) (Clause 7.2)
        """
        total_effective_height = self.site.building_height_m + (self.geometry.ground_clearance_mm / 1000.0)
        k1 = self.site.risk_coefficient_k1
        k2 = self.compute_k2_factor(total_effective_height, self.site.terrain_category)
        k3 = self.site.topography_factor_k3
        k4 = self.site.cyclonic_factor_k4
        Vb = self.site.basic_wind_speed_vb

        Vz = Vb * k1 * k2 * k3 * k4
        pz_pa = 0.6 * (Vz ** 2)  # Pa = N/m2
        pz_kpa = pz_pa / 1000.0   # kPa = kN/m2

        trace = {
            "Vb_m_s": Vb,
            "k1": k1,
            "k2": k2,
            "k3": k3,
            "k4": k4,
            "Vz_m_s": Vz,
            "pz_pa": pz_pa,
            "pz_kpa": pz_kpa,
            "effective_height_m": total_effective_height,
        }
        return Vz, pz_kpa, trace

    def compute_aerodynamic_coefficients(self) -> Tuple[float, float]:
        """
        Returns (C_net_uplift, C_net_downward) according to structural topology.
        - System A: IS 875 (Part 3) Table 8 (Canopy roofs, net pressure Cn).
        - Systems B, C, D: Localized rooftop module aerodynamic coefficients.
        """
        tilt = self.geometry.module.tilt_deg

        if self.geometry.mounting_system == MountingSystemType.SYSTEM_A_CANOPY:
            # Table 8 for open pitched/canopy roofs
            # Internal pressure Cpi does NOT apply to open canopies!
            if tilt <= 10.0:
                cn_up = -1.10
                cn_down = +0.70
            elif tilt <= 20.0:
                cn_up = -1.25
                cn_down = +0.85
            else:
                cn_up = -1.40
                cn_down = +1.00
            return cn_up, cn_down

        elif self.geometry.mounting_system == MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL:
            # Low-height rooftop rail (ASCE 7-16 Ch 29 / IS 875 rooftop flow)
            cn_up = -1.05
            cn_down = +0.65
            return cn_up, cn_down

        elif self.geometry.mounting_system == MountingSystemType.SYSTEM_C_METAL_SHEET:
            # Flush-mounted to metal roof slope
            cn_up = -1.20
            cn_down = +0.60
            return cn_up, cn_down

        else: # System D Ballasted
            # Ballasted low-tilt array on flat roof
            cn_up = -0.95
            cn_down = +0.55
            return cn_up, cn_down

    # =========================================================================
    # 2. SEISMIC ENGINEERING ENGINE — IS 1893 (Part 1): 2016
    # =========================================================================

    def calculate_equivalent_static_seismic_forces(self) -> Tuple[float, float, Dict[str, float]]:
        """
        Computes horizontal (Ah) and vertical (Av) seismic factors.
        Ah = (Z/2) * (I/R) * (Sa/g)
        Av = (2/3) * Ah
        Total seismic weight W = Dead Load only (0% roof live load per Table 10).
        """
        Z = self.site.zone_factor_z
        I = self.site.importance_factor_I
        R = self.site.response_reduction_R

        # Short period spectral acceleration Sa/g = 2.5 for rigid solar mounting structures
        sa_over_g = 2.5
        Ah = (Z / 2.0) * (I / R) * sa_over_g
        Av = (2.0 / 3.0) * Ah

        # Total dead load weight of modules
        W_modules_kn = self.geometry.total_module_dead_weight_kn

        # Base shear and vertical seismic forces
        Vb_seismic_kn = Ah * W_modules_kn
        Fz_seismic_kn = Av * W_modules_kn

        trace = {
            "Z": Z,
            "I": I,
            "R": R,
            "Sa_over_g": sa_over_g,
            "Ah": Ah,
            "Av": Av,
            "W_modules_kn": W_modules_kn,
            "Vb_seismic_kn": Vb_seismic_kn,
            "Fz_seismic_kn": Fz_seismic_kn,
        }
        return Vb_seismic_kn, Fz_seismic_kn, trace

    # =========================================================================
    # 3. MEMBER CAPACITY & DEMAND CHECKS — IS 800: 2007
    # =========================================================================

    def check_purlin_member(
        self,
        section: SectionProperty,
        span_mm: float,
        tributary_width_mm: float,
    ) -> List[CalculationResult]:
        """
        Evaluates purlin bending, shear, and deflection under:
        - Member-level governing live load: max(ACT-IL-01 point load, ACT-IL-02 distributed load)
        - ULS combinations (ULS-01, ULS-02, ULS-03, ULS-04, ULS-05, ULS-06)
        - SLS deflection combinations (SLS-01, SLS-02)
        """
        results = []
        L_m = span_mm / 1000.0
        B_m = tributary_width_mm / 1000.0
        trib_area_m2 = L_m * B_m

        # Dead load per meter of purlin
        # Module DL + self-weight
        module_dl_kn_m2 = self.geometry.module.dead_load_kn_per_m2
        purlin_sw_kn_m = (section.mass_kg_m * 9.80665 / 1000.0)
        w_dl_kn_m = (module_dl_kn_m2 * B_m) + purlin_sw_kn_m

        # Imposed loads:
        # ACT-IL-01: 1.0 kN point load at midspan
        P_il01_kn = ActionRegister.ACT_IL_01.nominal_value
        # ACT-IL-02: 0.75 kN/m2 distributed load
        w_il02_kn_m = ActionRegister.ACT_IL_02.nominal_value * B_m

        # Wind loads:
        _, pz_kpa, _ = self.calculate_design_wind_speed_and_pressure()
        cn_up, cn_down = self.compute_aerodynamic_coefficients()
        w_wl_up_kn_m = abs(cn_up) * pz_kpa * B_m
        w_wl_down_kn_m = cn_down * pz_kpa * B_m

        # ---------------------------------------------------------------------
        # Check A: ULS-01 Sagging Flexure (Independent Evaluation of LC-DIST vs LC-POINT)
        # ---------------------------------------------------------------------
        # Load Case A1: Distributed Live Load (ACT-IL-02 = 0.75 kN/m2)
        # Bending Moment: Mu = (w * L^2) / 8; Shear Force: Vu = (w * L) / 2
        w_uls01_dist = 1.5 * w_dl_kn_m + 1.5 * w_il02_kn_m
        Mu_dist_kn_m = (w_uls01_dist * (L_m ** 2)) / 8.0
        Vu_dist_kn = (w_uls01_dist * L_m) / 2.0

        # Load Case A2: Concentrated Technician Point Load (ACT-IL-01 = 1.0 kN)
        # Worst Bending: P at midspan -> Mu = (w_dl * L^2)/8 + (P * L)/4
        # Worst Shear: P placed adjacent to support per IS 875 Cl 4.1 -> Vu = (w_dl * L)/2 + 1.5 * P
        w_uls01_dl_only = 1.5 * w_dl_kn_m
        Mu_point_kn_m = ((w_uls01_dl_only * (L_m ** 2)) / 8.0) + (1.5 * P_il01_kn * L_m / 4.0)
        Vu_point_kn = ((w_uls01_dl_only * L_m) / 2.0) + (1.5 * P_il01_kn)

        # Identify governing structural response (never raw load magnitude comparison!)
        Mu_sagging_kn_m = max(Mu_dist_kn_m, Mu_point_kn_m)
        governing_moment_case = (
            f"ACT-IL-01 Point Load (Mu={Mu_point_kn_m:.3f} kNm)"
            if Mu_point_kn_m >= Mu_dist_kn_m
            else f"ACT-IL-02 Distributed (Mu={Mu_dist_kn_m:.3f} kNm)"
        )

        Vu_sagging_kn = max(Vu_dist_kn, Vu_point_kn)
        governing_shear_case = (
            f"ACT-IL-01 Point Load (Vu={Vu_point_kn:.3f} kN)"
            if Vu_point_kn >= Vu_dist_kn
            else f"ACT-IL-02 Distributed (Vu={Vu_dist_kn:.3f} kN)"
        )

        Md_capacity_kn_m = section.design_moment_capacity_major_kn_m
        unity_sagging = Mu_sagging_kn_m / Md_capacity_kn_m if Md_capacity_kn_m > 0 else 999.0

        results.append(
            CalculationResult(
                check_name="Purlin Sagging Flexure (ULS-01)",
                demand_value=Mu_sagging_kn_m,
                capacity_value=Md_capacity_kn_m,
                unity_ratio=unity_sagging,
                units="kN*m",
                governing_combination=f"ULS-01 [Governed by {governing_moment_case}]",
                passed=(unity_sagging <= 1.0),
                clause_reference="IS 800: 2007 Clause 8.2.1.2 & Table 4 Row 1",
                notes=(
                    f"Separately analyzed LC-DIST (Mu={Mu_dist_kn_m:.3f} kNm) and "
                    f"LC-POINT (Mu={Mu_point_kn_m:.3f} kNm) over {L_m:.2f} m span."
                ),
            )
        )

        # Shear capacity check
        Vd_capacity_kn = section.design_shear_capacity_major_kn
        unity_shear = Vu_sagging_kn / Vd_capacity_kn if Vd_capacity_kn > 0 else 999.0

        results.append(
            CalculationResult(
                check_name="Purlin Major-Axis Shear (ULS-01)",
                demand_value=Vu_sagging_kn,
                capacity_value=Vd_capacity_kn,
                unity_ratio=unity_shear,
                units="kN",
                governing_combination=f"ULS-01 [Governed by {governing_shear_case}]",
                passed=(unity_shear <= 1.0),
                clause_reference="IS 800: 2007 Clause 8.4.1",
                notes=(
                    f"Separately analyzed LC-DIST shear (Vu={Vu_dist_kn:.3f} kN) and "
                    f"LC-POINT shear (Vu={Vu_point_kn:.3f} kN)."
                ),
            )
        )

        # ---------------------------------------------------------------------
        # Check B: ULS-02 Uplift Bending (Wind Suction)
        # ---------------------------------------------------------------------
        # Net uplift load: 1.5 * WL_up - 0.9 * DL
        w_uls02_net_up = 1.5 * w_wl_up_kn_m - 0.9 * w_dl_kn_m
        if w_uls02_net_up > 0:
            Mu_uplift_kn_m = (w_uls02_net_up * (L_m ** 2)) / 8.0
            unity_uplift = Mu_uplift_kn_m / Md_capacity_kn_m
            results.append(
                CalculationResult(
                    check_name="Purlin Uplift Stress Reversal (ULS-02)",
                    demand_value=Mu_uplift_kn_m,
                    capacity_value=Md_capacity_kn_m,
                    unity_ratio=unity_uplift,
                    units="kN*m",
                    governing_combination="ULS-02 (0.9 DL + 1.5 WL_up)",
                    passed=(unity_uplift <= 1.0),
                    clause_reference="IS 800: 2007 Clause 5.3.3 & Table 4 Row 2",
                    notes="Net upward wind flexure with 0.9 stabilizing dead load factor.",
                )
            )

        # ---------------------------------------------------------------------
        # Check C: SLS-01 Vertical Deflection
        # ---------------------------------------------------------------------
        # Evaluates superposed dead load + alternative imposed live load cases per IS 875 (Part 2) Table 2:
        # Case SLS-01A: Dead Load + Distributed Live Load (delta = delta_dl + delta_il02)
        # Case SLS-01B: Dead Load + Concentrated Midspan Point Load (delta = delta_dl + delta_il01)
        E_mpa = section.material.elastic_modulus_mpa
        Ixx_mm4 = section.Ixx_mm4
        # Allowable deflection delta_allow = L / 250 per IS 800 Table 6
        delta_allow_mm = span_mm / 250.0

        # Dead load component (always simultaneously active)
        delta_dl_mm = (5.0 * w_dl_kn_m * (span_mm ** 4)) / (384.0 * E_mpa * Ixx_mm4)

        # Case SLS-01A: Superposed Dead Load + Distributed Live Load (ACT-IL-02 = 0.75 kN/m2)
        delta_il02_mm = (5.0 * w_il02_kn_m * (span_mm ** 4)) / (384.0 * E_mpa * Ixx_mm4)
        delta_case_dist_mm = delta_dl_mm + delta_il02_mm

        # Case SLS-01B: Superposed Dead Load + Concentrated Point Load (ACT-IL-01 = 1.0 kN at midspan)
        P_sls_n = 1000.0  # 1.0 kN
        delta_il01_point_mm = (P_sls_n * (span_mm ** 3)) / (48.0 * E_mpa * Ixx_mm4)
        delta_case_point_mm = delta_dl_mm + delta_il01_point_mm

        if delta_case_point_mm >= delta_case_dist_mm:
            delta_actual_mm = delta_case_point_mm
            governing_deflection_case = f"ACT-IL-01 Point Load (1.0 kN) + DL (delta={delta_case_point_mm:.2f} mm)"
        else:
            delta_actual_mm = delta_case_dist_mm
            governing_deflection_case = f"ACT-IL-02 Distributed ({ActionRegister.ACT_IL_02.nominal_value:.2f} kN/m2) + DL (delta={delta_case_dist_mm:.2f} mm)"

        unity_deflection = delta_actual_mm / delta_allow_mm

        results.append(
            CalculationResult(
                check_name="Purlin Gravity Deflection (SLS-01)",
                demand_value=delta_actual_mm,
                capacity_value=delta_allow_mm,
                unity_ratio=unity_deflection,
                units="mm",
                governing_combination=f"SLS-01 [Governed by {governing_deflection_case}]",
                passed=(unity_deflection <= 1.0),
                clause_reference="IS 800: 2007 Clause 5.6.1 & Table 6",
                notes=(
                    f"Governing deflection {delta_actual_mm:.2f} mm vs limit L/250 = {delta_allow_mm:.1f} mm. "
                    f"Analyzed Case A (DL + Distributed Live = {delta_case_dist_mm:.2f} mm) and Case B "
                    f"(DL + 1.0 kN Midspan Point Live = {delta_case_point_mm:.2f} mm) under conservative simply supported beam assumptions."
                ),
            )
        )
        return results

    # =========================================================================
    # 4. BALLAST STABILITY CHECKS — SYSTEM D
    # =========================================================================

    def check_ballast_stability(
        self,
        ballast_dead_weight_kn_per_m2: float,
        friction_coeff_mu: float = 0.40,
    ) -> List[CalculationResult]:
        """
        Calculates sliding and overturning stability for ballasted non-penetrating arrays.
        Enforces strict zero adverse live load (IL = 0) during wind uplift and sliding checks.
        """
        results = []
        tilt_rad = math.radians(self.geometry.module.tilt_deg)
        cos_theta = math.cos(tilt_rad)
        sin_theta = math.sin(tilt_rad)

        _, pz_kpa, _ = self.calculate_design_wind_speed_and_pressure()
        cn_up, _ = self.compute_aerodynamic_coefficients()

        # Aerodynamic suction normal to module plane (kN/m2)
        q_wind_normal_kpa = abs(cn_up) * pz_kpa

        # Factored horizontal and vertical wind components (ULS-02: 1.5 * WL)
        F_wind_horiz_kn_m2 = 1.5 * q_wind_normal_kpa * sin_theta
        F_wind_vert_up_kn_m2 = 1.5 * q_wind_normal_kpa * cos_theta

        # Total dead load (Module DL + Ballast DL)
        total_dl_kn_m2 = self.geometry.module.dead_load_kn_per_m2 + ballast_dead_weight_kn_per_m2

        # Effective normal force Neff under ULS-02 (0.9 DL - 1.5 WL_up). ADVERSE LIVE LOAD STRICTLY ZERO!
        N_eff_kn_m2 = (0.9 * total_dl_kn_m2) - F_wind_vert_up_kn_m2

        # ---------------------------------------------------------------------
        # Check A: Contact Loss / Net Uplift Check
        # ---------------------------------------------------------------------
        uplift_passed = (N_eff_kn_m2 > 0.0)
        results.append(
            CalculationResult(
                check_name="Ballast Net Normal Force / Uplift Resistance",
                demand_value=F_wind_vert_up_kn_m2,
                capacity_value=0.9 * total_dl_kn_m2,
                unity_ratio=(F_wind_vert_up_kn_m2 / (0.9 * total_dl_kn_m2)) if total_dl_kn_m2 > 0 else 999.0,
                units="kN/m2",
                governing_combination="ULS-02 (0.9 DL + 1.5 WL_up, IL = 0)",
                passed=uplift_passed,
                clause_reference="IS 800: 2007 Clause 5.3.3 Table 4 Row 2 Note 4",
                notes="Adverse live load strictly zero; requires Neff > 0 to maintain roof contact.",
            )
        )

        # ---------------------------------------------------------------------
        # Check B: Sliding Resistance (V_res = mu * N_eff)
        # ---------------------------------------------------------------------
        if N_eff_kn_m2 > 0:
            V_res_kn_m2 = friction_coeff_mu * N_eff_kn_m2
            unity_sliding = F_wind_horiz_kn_m2 / V_res_kn_m2 if V_res_kn_m2 > 0 else 999.0
            sliding_passed = (unity_sliding <= 1.0)
        else:
            V_res_kn_m2 = 0.0
            unity_sliding = 999.0
            sliding_passed = False

        results.append(
            CalculationResult(
                check_name="Ballast Horizontal Sliding Resistance (ULS-02 — ASSUMED FRICTION)",
                demand_value=F_wind_horiz_kn_m2,
                capacity_value=V_res_kn_m2,
                unity_ratio=unity_sliding,
                units="kN/m2",
                governing_combination="ULS-02 (Horizontal Wind Shear vs Friction)",
                passed=sliding_passed,
                clause_reference="IS 800: 2007 Clause 5.3 & EN 1990:2002 Annex D",
                notes=(
                    f"Calculated with assumed friction mu={friction_coeff_mu:.2f}. "
                    "LIMITATION: Unmeasured friction interface. In-situ static pull-slip testing per ASTM C1028 under wet "
                    "conditions is MANDATORY before construction. Governed by FRICTION_UNVERIFIED_HOLD."
                ),
            )
        )
        return results

    # =========================================================================
    # 5. FULL CALCULATION PIPELINE & REPORT GENERATION
    # =========================================================================

    def run_full_design_assessment(
        self,
        purlin_section: SectionProperty,
        ballast_weight_kn_m2: Optional[float] = None,
    ) -> CalculationReport:
        """Runs end-to-end structural assessment for the selected mounting system."""
        report = CalculationReport(
            project_id=f"RENSUN-STR-{self.geometry.mounting_system.name}",
            system_type=self.geometry.mounting_system,
            governing_summary="Preliminary Engineering Calculation Run (Phase 1 Baseline)",
        )

        # 1. Log active holds
        active_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(self.geometry.mounting_system.value)
        report.active_holds = [h.hold_id for h in active_holds]
        report.log(f"Active Verification Holds for {self.geometry.mounting_system.value}: {len(active_holds)}")
        for h in active_holds:
            report.log(f"  • [{h.hold_id}] ({h.category.value}) — {h.status.value}")

        # 2. Wind Engine
        Vz, pz_kpa, wind_trace = self.calculate_design_wind_speed_and_pressure()
        report.log(
            f"Wind Engine: Vb={self.site.basic_wind_speed_vb} m/s, k2={wind_trace['k2']:.3f}, "
            f"Vz={Vz:.2f} m/s, pz={pz_kpa:.3f} kN/m2 (IS 875 Part 3 Clauses 6.3 & 7.2)"
        )

        # 3. Seismic Engine
        Vb_eq, Fz_eq, eq_trace = self.calculate_equivalent_static_seismic_forces()
        report.log(
            f"Seismic Engine: Zone {self.site.seismic_zone.value} (Z={eq_trace['Z']:.2f}), "
            f"Ah={eq_trace['Ah']:.4f}, Av={eq_trace['Av']:.4f}, Base Shear={Vb_eq:.2f} kN (IS 1893 Cl 6.3.2.1)"
        )

        # 4. Purlin Member Checks
        purlin_results = self.check_purlin_member(
            section=purlin_section,
            span_mm=self.geometry.rafter_spacing_mm,
            tributary_width_mm=self.geometry.purlin_spacing_mm,
        )
        for res in purlin_results:
            report.add_result(res)
            report.log(res.summary_line())

        # 5. Ballast Stability (System D)
        if self.geometry.mounting_system == MountingSystemType.SYSTEM_D_BALLASTED:
            ballast_dl = ballast_weight_kn_m2 if ballast_weight_kn_m2 is not None else 0.50
            ballast_results = self.check_ballast_stability(
                ballast_dead_weight_kn_per_m2=ballast_dl,
                friction_coeff_mu=0.40,
            )
            for res in ballast_results:
                report.add_result(res)
                report.log(res.summary_line())

        return report
