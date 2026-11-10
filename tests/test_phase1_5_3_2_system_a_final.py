"""
Phase 1.5.3.2B — System A Defect Correction & Test-Isolation Remediation Test Suite
Package: tests.test_phase1_5_3_2_system_a_final

Remediates all six defects identified in Phase 1.5.3.2A:
- DEF-01: Rafter LTB with moment gradient factor C1 = 1.75 (IS 800 Table 42) & 2-span framing.
- DEF-02: Fly-bracing restraint stiffness (IS 800 Cl 8.9.2), single-leg eccentricity & cleat bearing.
- DEF-03: Baseplate fillet weld combined normal and shear stresses (IS 800 Cl 10.5.10).
- DEF-04: Host slab unbalanced moment punching shear (IS 456 Cl 31.6.2.2) & uplift tension breakout.
- DEF-05: 100% Hermetic test isolation using IsolatedTestEnvironment (zero production DB access).
- DEF-06: Independent first-principles calculation solvers embedded in test methods.
"""

import hashlib
import json
import math
import os
import shutil
import sqlite3
import unittest

from tests.test_isolation_helper import (
    IsolatedTestEnvironment,
    PROJECT_ROOT,
    PROD_QUOTATIONS_DB,
    PROD_STRUCTURAL_DB,
    PROD_SETTINGS_FILE,
)
from structural.models import (
    MountingSystemType,
    SiteParameters,
    TerrainCategory,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    STEEL_E250,
)
from structural.actions import ActionRegister
from structural.holds import MASTER_VERIFICATION_REGISTER
from structural.workflows.system_a_final import (
    LTBCalculationMethod,
    WindUpliftRafterAudit,
    evaluate_wind_uplift_rafter_flexure,
    FlyBracingDesignCheck,
    design_bottom_flange_fly_bracing,
    StatutoryAnchorStandardBasis,
    get_chemical_anchor_standards_hierarchy,
    ProjectSpecificAnchorTestingProtocol,
    generate_project_anchor_testing_protocol,
    SlabThicknessEvaluation,
    evaluate_slab_thickness_and_anchorage_feasibility,
    FoundationLoadPathStep,
    CompleteFoundationLoadPathReport,
    verify_complete_foundation_load_path,
    WeldSegment,
    ParametricWeldGroupProperties,
    ParametricWeldGroupSolver,
    create_ismb300_contour_weld_group,
    ProductSpecificChemicalAnchorModel,
    AnchorDesignCheckResult,
)


class TestPhase1532SystemAFinal(unittest.TestCase):
    """Rigorous engineering test suite with hermetic isolation and independent benchmarks."""

    iso: IsolatedTestEnvironment

    @classmethod
    def setUpClass(cls):
        # 1. Capture production hashes to guard against any accidental mutation
        def hash_file(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()

        cls.orig_quotations_hash = hash_file(PROD_QUOTATIONS_DB)
        cls.orig_structural_hash = hash_file(PROD_STRUCTURAL_DB)
        cls.orig_settings_hash = hash_file(PROD_SETTINGS_FILE)

        # 2. Instantiate and activate hermetic test environment (DEF-05 Remediation)
        cls.iso = IsolatedTestEnvironment()
        cls.iso.activate()
        cls.iso.assert_isolated_paths()

        # 3. Populate isolated temporary database from read-only baseline backup
        backup_db_path = os.path.join(PROJECT_ROOT, "backups", "phase_1_5_1_baseline", "structural_runs.db")
        if os.path.exists(backup_db_path):
            with sqlite3.connect(backup_db_path) as src_conn:
                with sqlite3.connect(cls.iso.structural_db_path) as dst_conn:
                    src_conn.backup(dst_conn)

    @classmethod
    def tearDownClass(cls):
        # Deactivate and clean up isolated test environment
        cls.iso.deactivate(verify_production_non_interference=True)

        # Assert production databases were untouched
        def hash_file(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()

        assert hash_file(PROD_QUOTATIONS_DB) == cls.orig_quotations_hash, "MUTATION DETECTED: quotations.db"
        assert hash_file(PROD_STRUCTURAL_DB) == cls.orig_structural_hash, "MUTATION DETECTED: structural_runs.db"
        assert hash_file(PROD_SETTINGS_FILE) == cls.orig_settings_hash, "MUTATION DETECTED: quotation_settings.json"

    # -------------------------------------------------------------------------
    # TEST 01: Wind Uplift Demand — Independent First-Principles Solver (DEF-06)
    # -------------------------------------------------------------------------
    def test_01_wind_uplift_factored_moment_demand(self):
        """[Category A: Demand & Action Combinations] ASME V&V 10 Eq 4.1 / IS 875 Part 3: Independently derives net wind uplift and factored moment demand."""
        # Independent Test-Side Solver:
        indep_Vz = 39.0 * 1.0 * 1.028 * 1.0 * 1.0  # 40.092 m/s
        indep_pz = 0.60 * (indep_Vz ** 2) / 1000.0   # 0.964418 kPa
        indep_w_wl_up = 1.10 * indep_pz * 3.0        # 3.18258 kN/m
        indep_mod_dl = 0.104396 * 3.0                # 0.313188 kN/m
        indep_raf_dl = 44.2 * 9.80665 / 1000.0       # 0.433454 kN/m
        indep_pur_dl = (3.53 * 9.80665 / 1000.0) * (9.112 / 1.15) / 9.112  # 0.030103 kN/m
        indep_w_dl = indep_mod_dl + indep_raf_dl + indep_pur_dl + 0.20       # 0.976745 kN/m
        indep_w_net = 1.5 * indep_w_wl_up - 0.9 * indep_w_dl                # 3.89480 kN/m
        indep_Mu_full = (indep_w_net * (9.112 ** 2)) / 8.0                   # 40.4223 kNm

        # Production workflow call
        audit = evaluate_wind_uplift_rafter_flexure()

        self.assertAlmostEqual(audit.design_wind_speed_Vz_ms, indep_Vz, places=3)
        self.assertAlmostEqual(audit.design_wind_pressure_pz_kpa, indep_pz, places=4)
        self.assertAlmostEqual(audit.w_net_uplift_uls02_kn_m, indep_w_net, places=3)
        self.assertAlmostEqual(audit.factored_moment_demand_full_span_kn_m, indep_Mu_full, delta=0.05)

    # -------------------------------------------------------------------------
    # TEST 02: Rafter LTB with Moment Gradient Cb = 1.30 & IS 800 Annex E (DEF-01 & DEF-06)
    # -------------------------------------------------------------------------
    def test_02_rafter_ltb_with_moment_gradient_and_boundary_conditions(self):
        """[Category B: Member Stability & LTB] ASME V&V 10 Cl 5 / IS 800 Cl 8.2.2 & Annex E: Verifies LTB capacity with rational parabolic Cb = 1.30, uniform lower bound C1 = 1.0, and full span failure."""
        audit = evaluate_wind_uplift_rafter_flexure()

        # 1. Full unbraced span L = 9112 mm: confirms LTB structural failure
        self.assertEqual(audit.unbraced_length_full_span_mm, 9112.0)
        self.assertAlmostEqual(audit.Mcr_full_span_kn_m, 46.29, delta=1.0)
        self.assertAlmostEqual(audit.Md_capacity_full_span_kn_m, 37.12, delta=1.0)
        self.assertGreater(audit.unity_ratio_full_span, 1.0)
        self.assertAlmostEqual(audit.unity_ratio_full_span, 1.089, delta=0.02)
        self.assertFalse(audit.full_span_passes_without_bracing)
        self.assertIn("STRUCTURAL FAILURE", audit.governing_conclusion)

        # 2. Independent Test-Side First-Principles Solver for ISMB 300 Cross Section:
        E = 205000.0
        G = E / (2.0 * 1.30)
        Iy = 4.539e6
        h = 300.0
        b = 140.0
        tw = 7.5
        tf = 12.4
        It = (2.0 * b * (tf ** 3) + (h - 2.0 * tf) * (tw ** 3)) / 3.0  # 216651.57 mm4
        Iw = (Iy * ((h - tf) ** 2)) / 4.0                              # 9.386e10 mm6
        Zpx = 651000.0
        fy = 250.0
        gamma_m0 = 1.10
        L_mm = 4556.0
        term1 = (math.pi ** 2 * E * Iy) / (L_mm ** 2)
        term2 = G * It + (math.pi ** 2 * E * Iw) / (L_mm ** 2)
        Mcr_0 = math.sqrt(term1 * term2) / 1e6  # 107.73 kNm

        # 3. Rational Parabolic Moment Gradient Solver (Kirby-Nethercot / AISC 360-16 / IS 800 Annex E Eq 1):
        # Under UDL across 9.112 m rafter, moments along half-span segment (0 to 4.556 m):
        w_net = audit.w_net_uplift_uls02_kn_m
        L_span = audit.rafter_total_length_m
        def M_x(x):
            return 0.5 * w_net * x * (L_span - x)

        MA = M_x(1.139)  # 17.68 kNm
        MB = M_x(2.278)  # 30.32 kNm
        MC = M_x(3.417)  # 37.89 kNm
        Mmax = M_x(4.556) # 40.42 kNm
        indep_Cb = (12.5 * Mmax) / (2.5 * Mmax + 3.0 * MA + 4.0 * MB + 3.0 * MC)  # 1.2987 ~ 1.30

        Mcr_parabolic = indep_Cb * Mcr_0  # 139.91 kNm
        lam_parabolic = math.sqrt((Zpx * fy) / (Mcr_parabolic * 1e6))
        phi_parabolic = 0.5 * (1.0 + 0.21 * (lam_parabolic - 0.2) + (lam_parabolic ** 2))
        chi_parabolic = 1.0 / (phi_parabolic + math.sqrt(phi_parabolic ** 2 - lam_parabolic ** 2))
        Md_parabolic = (chi_parabolic * Zpx * fy) / (gamma_m0 * 1e6)  # 90.40 kNm
        ur_parabolic = Mmax / Md_parabolic  # 0.447

        self.assertAlmostEqual(audit.moment_gradient_factor_Cb_parabolic, indep_Cb, places=3)
        self.assertAlmostEqual(audit.Mcr_parabolic_gradient_kn_m, Mcr_parabolic, delta=1.0)
        self.assertAlmostEqual(audit.Md_capacity_parabolic_kn_m, Md_parabolic, delta=1.0)
        self.assertAlmostEqual(audit.unity_ratio_parabolic, ur_parabolic, delta=0.01)
        self.assertLessEqual(audit.unity_ratio_parabolic, 0.45)
        self.assertTrue(audit.load_height_stabilizing_yg_considered)

        # Explicit Governing LTB Architecture Verification (WP-01 / DEF-01 Mandate):
        self.assertEqual(audit.governing_calculation_method, LTBCalculationMethod.IS800_ANNEX_E_EQUATION_1_PARABOLIC.value)
        self.assertAlmostEqual(audit.governing_Md_capacity_kn_m, 90.40, delta=0.5)
        self.assertAlmostEqual(audit.governing_unity_ratio, 0.447, delta=0.01)
        self.assertAlmostEqual(audit.governing_moment_gradient_factor, 1.2987, places=3)
        self.assertAlmostEqual(audit.governing_Mcr_kn_m, Mcr_parabolic, delta=1.0)
        self.assertEqual(audit.historical_linear_reference_C1, 1.75)
        self.assertAlmostEqual(audit.historical_linear_reference_Md_kn_m, 105.64, delta=0.5)
        self.assertAlmostEqual(audit.historical_linear_reference_unity_ratio, 0.383, delta=0.01)

        # 4. Uniform-Moment Lower Bound (C1 = 1.0 per IS 800 Table 42):
        lam_0 = math.sqrt((Zpx * fy) / (Mcr_0 * 1e6))
        phi_0 = 0.5 * (1.0 + 0.21 * (lam_0 - 0.2) + (lam_0 ** 2))
        chi_0 = 1.0 / (phi_0 + math.sqrt(phi_0 ** 2 - lam_0 ** 2))
        Md_0 = (chi_0 * Zpx * fy) / (gamma_m0 * 1e6)  # 75.74 kNm
        ur_0 = Mmax / Md_0  # 0.534

        self.assertAlmostEqual(audit.Mcr_clear_span_kn_m, Mcr_0, delta=1.0)
        self.assertAlmostEqual(audit.Md_capacity_clear_span_kn_m, Md_0, delta=1.0)
        self.assertAlmostEqual(audit.unity_ratio_clear_span, ur_0, delta=0.01)
        self.assertLessEqual(audit.unity_ratio_clear_span, 0.55)

        # 5. Historical Linear Moment Gradient Reference (C1 = 1.75):
        Mcr_grad = 1.75 * Mcr_0  # 188.53 kNm
        lam_grad = math.sqrt((Zpx * fy) / (Mcr_grad * 1e6))
        phi_grad = 0.5 * (1.0 + 0.21 * (lam_grad - 0.2) + (lam_grad ** 2))
        chi_grad = 1.0 / (phi_grad + math.sqrt(phi_grad ** 2 - lam_grad ** 2))
        Md_grad = (chi_grad * Zpx * fy) / (gamma_m0 * 1e6)  # 105.64 kNm
        ur_grad = Mmax / Md_grad  # 0.383

        self.assertEqual(audit.moment_gradient_factor_C1, 1.75)
        self.assertAlmostEqual(audit.Mcr_gradient_kn_m, Mcr_grad, delta=1.0)
        self.assertAlmostEqual(audit.Md_capacity_gradient_kn_m, Md_grad, delta=1.0)
        self.assertAlmostEqual(audit.unity_ratio_gradient, ur_grad, delta=0.02)
        self.assertLess(audit.unity_ratio_gradient, 0.45)

        # 6. Two-span continuous framing model: demand is 10.11 kNm, UR = 0.133
        self.assertEqual(audit.continuous_2span_moment_demand_kn_m, 10.11)
        self.assertAlmostEqual(audit.continuous_2span_unity_ratio, 0.133, delta=0.01)

    # -------------------------------------------------------------------------
    # TEST 03: Fly-Bracing Required Force & Geometry (DEF-02)
    # -------------------------------------------------------------------------
    def test_03_fly_bracing_required_stabilizing_force(self):
        """[Category C: Stabilizing Bracing Forces] IS 800 Cl 8.3.2: Independently verifies stabilizing force Pbr = 2.5% Nc."""
        indep_Nc = 40.42 / 0.2876  # 140.54 kN
        indep_Pbr = 0.025 * indep_Nc  # 3.514 kN
        indep_F_brace = indep_Pbr / math.cos(math.radians(45.0))  # 4.969 kN

        check = design_bottom_flange_fly_bracing(Mu_uplift_kn_m=40.42)
        self.assertAlmostEqual(check.compression_flange_force_Nc_kn, indep_Nc, delta=0.1)
        self.assertAlmostEqual(check.required_stabilizing_force_Pbr_kn, indep_Pbr, delta=0.01)
        self.assertAlmostEqual(check.axial_force_demand_F_brace_kn, indep_F_brace, delta=0.01)

    # -------------------------------------------------------------------------
    # TEST 04: Fly-Bracing Restraint Stiffness & Eccentricity (DEF-02 & DEF-06)
    # -------------------------------------------------------------------------
    def test_04_fly_bracing_stiffness_and_single_leg_eccentricity(self):
        """[Category D: Restraint Stiffness & System Stability] ASME V&V 10 / Winter-Yura / IS 800 Cl 8.3.2: Verifies series spring stiffness, HSFG pre-tensioning requirement, and purlin roll."""
        check = design_bottom_flange_fly_bracing(brace_length_mm=600.0)

        # 1. Independent Restraint Stiffness Check per IS 800:2007 Cl 8.3.2 & Winter-Yura:
        # K_req = 4 * Nc / Lb = 4 * 140.54 / 4.556 = 123.39 kN/m = 0.1234 kN/mm
        indep_Nc = 40.42 / 0.2876  # 140.54 kN
        indep_K_req = (4.0 * indep_Nc) / (4.556 * 1000.0)  # 0.1234 kN/mm

        # Component 1: Diagonal Strut Axial/Lateral Stiffness
        # Provided lateral stiffness: (A*E/L) * cos^2(45) = (379 * 205 / 600) * 0.5 = 64.75 kN/mm
        indep_K_lat = ((379.0 * 205.0) / 600.0) * 0.5  # 64.75 kN/mm

        self.assertAlmostEqual(check.required_lateral_stiffness_Kreq_kn_mm, indep_K_req, places=3)
        self.assertAlmostEqual(check.provided_brace_lateral_stiffness_Klat_kn_mm, indep_K_lat, places=1)
        self.assertTrue(check.stiffness_passed)
        self.assertGreater(check.stiffness_ratio, 500.0)

        # Component 2 & 3: Complete Series Spring Stiffness Model
        # K_cleat (6 mm stiffened cleat, b = 100 mm, L = 40 mm):
        I_cleat = 100.0 * (6.0 ** 3) / 12.0  # 1800.0 mm4
        indep_K_cleat = (3.0 * 205000.0 * I_cleat) / ((40.0 ** 3) * 1000.0)  # 17.297 kN/mm
        indep_K_bolt = 50.0  # 50.0 kN/mm
        indep_1_Ksys = (1.0 / indep_K_lat) + (1.0 / indep_K_cleat) + (1.0 / indep_K_bolt)
        indep_K_sys = 1.0 / indep_1_Ksys  # 10.72 kN/mm
        indep_sys_ratio = indep_K_sys / indep_K_req  # 86.9

        self.assertAlmostEqual(check.cleat_flexural_stiffness_Kcleat_kn_mm, indep_K_cleat, places=2)
        self.assertAlmostEqual(check.bolt_bearing_stiffness_Kbolt_kn_mm, indep_K_bolt, places=1)
        self.assertAlmostEqual(check.system_series_stiffness_with_cleat_kn_mm, indep_K_sys, places=2)
        self.assertAlmostEqual(check.system_series_stiffness_ratio, indep_sys_ratio, delta=0.5)
        self.assertGreaterEqual(check.system_series_stiffness_ratio, 80.0)

        # Contrast with unreinforced 2.0 mm purlin web (without stiffened cleat):
        I_web = 100.0 * (2.0 ** 3) / 12.0  # 66.67 mm4
        indep_K_web = (48.0 * 205000.0 * I_web) / ((100.0 ** 3) * 1000.0)  # 0.656 kN/mm
        indep_1_Ksys_no_cleat = (1.0 / indep_K_lat) + (1.0 / indep_K_web)
        indep_K_sys_no_cleat = 1.0 / indep_1_Ksys_no_cleat  # 0.650 kN/mm

        self.assertAlmostEqual(check.purlin_web_flexural_stiffness_Kweb_kn_mm, indep_K_web, places=3)
        self.assertAlmostEqual(check.system_series_stiffness_without_cleat_kn_mm, indep_K_sys_no_cleat, places=3)
        self.assertTrue(check.direct_cleat_attachment_mandatory)

        # 2. Single-Leg Eccentricity Interaction Check (IS 800 Cl 7.5.1 / 9.3):
        indep_F_brace = 4.969
        indep_Mecc = (indep_F_brace * 11.6) / 1000.0  # 0.0576 kNm
        indep_Pd = (379.0 * 141.1) / 1000.0           # 53.48 kN
        indep_Md = (1940.0 * 250.0) / (1.10 * 1e6)     # 0.4409 kNm
        indep_IR = (indep_F_brace / indep_Pd) + (indep_Mecc / indep_Md)  # 0.0929 + 0.1307 = 0.224

        self.assertEqual(check.eccentricity_ex_mm, 11.6)
        self.assertAlmostEqual(check.eccentricity_moment_Mecc_kn_m, indep_Mecc, delta=0.005)
        self.assertAlmostEqual(check.combined_interaction_ratio, indep_IR, delta=0.01)
        self.assertTrue(check.combined_interaction_passed)
        self.assertLess(check.combined_interaction_ratio, 0.30)

        # 3. Mandatory HSFG Pre-Tensioning & Diaphragm Governance Checks (WP-02 / DEF-02):
        self.assertEqual(check.bolt_connection_type, "Pre-tensioned HSFG M12 Grade 8.8 (IS 4000) / Welded Cleat")
        self.assertTrue(check.is_hsfg_pretension_mandatory)
        self.assertAlmostEqual(check.hsfg_slip_resistance_capacity_kn, 17.00, places=1)
        self.assertAlmostEqual(check.hsfg_slip_resistance_unity_ratio, 0.292, delta=0.01)
        self.assertEqual(check.restraint_system_governance_status, "CONDITIONALLY_ADEQUATE_PENDING_SITE_DIAPHRAGM_VERIFICATION")
        self.assertTrue(check.purlin_torsional_stiffness_considered)
        self.assertFalse(check.diaphragm_shear_stiffness_verified)

    # -------------------------------------------------------------------------
    # TEST 05: Bolt Shear, Cleat Bearing, and Purlin Web Protection (DEF-02 & DEF-06)
    # -------------------------------------------------------------------------
    def test_05_fly_bracing_bolt_bearing_and_purlin_cleat(self):
        """[Category E: Connection Strength & Purlin Web Protection] IS 800 Cl 10.3: Verifies bolt bearing on cleat and purlin web stiffener requirement with independent solvers."""
        check = design_bottom_flange_fly_bracing(purlin_web_thickness_mm=2.0, cleat_thickness_mm=5.0)

        # 1. Independent Bolt Shear Capacity (IS 800 Cl 10.3.2):
        # Single M12 Gr 8.8: fub = 800 MPa, gamma_mb = 1.25, Anb = 84.3 mm2
        indep_Vdsb = (800.0 / (math.sqrt(3.0) * 1.25) * 84.3) / 1000.0  # 31.150 kN
        self.assertAlmostEqual(check.bolt_shear_capacity_kn, indep_Vdsb, delta=0.05)
        self.assertTrue(check.bolt_passed)

        # 2. Independent Bolt Bearing on 5 mm Cleat (IS 800 Cl 10.3.3):
        # kb = 0.738, d = 12 mm, t = 5 mm, fu = 410 MPa, gamma_mb = 1.25
        indep_kb = 0.738
        indep_Vdpb_5mm = (2.5 * indep_kb * 12.0 * 5.0 * 410.0) / (1.25 * 1000.0)  # 36.310 kN
        self.assertAlmostEqual(check.bolt_bearing_capacity_kn, indep_Vdpb_5mm, delta=0.05)
        self.assertTrue(check.bolt_bearing_passed)
        self.assertLess(check.bolt_bearing_unity_ratio, 0.20)

        # 3. Independent Bolt Bearing on 6 mm Cleat:
        indep_Vdpb_6mm = (2.5 * indep_kb * 12.0 * 6.0 * 410.0) / (1.25 * 1000.0)  # 43.571 kN
        check_6mm = design_bottom_flange_fly_bracing(purlin_web_thickness_mm=2.0, cleat_thickness_mm=6.0)
        self.assertAlmostEqual(check_6mm.bolt_bearing_capacity_kn, indep_Vdpb_6mm, delta=0.05)

        # Web stiffener flag
        self.assertTrue(check.purlin_web_stiffener_required)
        self.assertEqual(check.cleat_plate_thickness_min_mm, 6.0)

    # -------------------------------------------------------------------------
    # TEST 06: Chemical Anchor Standards Hierarchy (Statutory Mapping)
    # -------------------------------------------------------------------------
    def test_06_chemical_anchor_standards_hierarchy(self):
        """[Category F: Statutory Basis & Standard Hierarchy] IEEE 1012 Traceability: Verifies formal retraction of IS 800 Cl 10 and establishment of authoritative fib 58 / EN 1992-4 hierarchy."""
        hierarchy = get_chemical_anchor_standards_hierarchy()
        self.assertEqual(len(hierarchy), 5)

        is800_basis = [b for b in hierarchy if "IS 800" in b.governing_document][0]
        self.assertFalse(is800_basis.is_applicable_to_chemical_anchors)
        self.assertIn("RETRACTED", is800_basis.citation_status)

        fib_basis = [b for b in hierarchy if "fib" in b.governing_document][0]
        self.assertTrue(fib_basis.is_applicable_to_chemical_anchors)
        self.assertEqual(fib_basis.citation_status, "PRIMARY TECHNICAL SPECIFICATION")

    # -------------------------------------------------------------------------
    # TEST 07: Anchor Testing Protocol Classification (DEF-04)
    # -------------------------------------------------------------------------
    def test_07_project_specific_anchor_testing_protocol(self):
        """[Category G: Quality Assurance & Proof Testing Protocol] BS 8539 / ASTM E488: Verifies anchor proof test parameters as engineer-selected criteria requiring RSE sign-off."""
        protocol = generate_project_anchor_testing_protocol(Tu_uplift_kn=18.50, hef_mm=125.0)
        self.assertEqual(protocol.project_id, "RS-STR-RENSUN-2026-0059")
        self.assertEqual(protocol.proof_test_load_factor, 1.50)
        self.assertEqual(protocol.proof_test_load_kn, 27.75)
        self.assertEqual(protocol.sample_size_percentage, 25.0)
        self.assertEqual(protocol.minimum_sample_anchors, 3)
        self.assertEqual(protocol.maximum_allowable_slip_mm, 0.20)
        self.assertTrue(protocol.rse_sign_off_required)

    # -------------------------------------------------------------------------
    # TEST 08: Slab Thickness Physical Incompatibility (WP-04)
    # -------------------------------------------------------------------------
    def test_08_slab_thickness_evaluation_and_alternatives(self):
        """[Category H: Physical Feasibility & Geometry Constraints] ETA-20/0541: Verifies physical impossibility of 125 mm embedment in 125-150 mm slabs without plinths or through-bolts."""
        eval_slab = evaluate_slab_thickness_and_anchorage_feasibility(
            assumed_slab_thickness_mm=150.0,
            hef_mm=125.0,
            d_bolt_mm=16.0,
        )
        self.assertEqual(eval_slab.chemical_anchor_eta_hmin_mm, 161.0)
        self.assertFalse(eval_slab.is_hef_125_feasible_in_125mm_slab)
        self.assertFalse(eval_slab.is_hef_125_feasible_in_150mm_slab)
        self.assertEqual(len(eval_slab.engineering_alternatives), 3)

    # -------------------------------------------------------------------------
    # TEST 09: Parametric Fillet Weld & Slab Punching Solvers (DEF-03 & DEF-04 & DEF-06)
    # -------------------------------------------------------------------------
    def test_09_weld_combined_stress_and_slab_unbalanced_moment(self):
        """[Category I: Multi-Axis Stress Integration & Unsymmetric Bending] IS 800 Cl 10.5.10 & Blodgett (1966): Verifies inclined weld local inertia, 6-DOF stress integration, and load path step 4 governing capacity."""
        report = verify_complete_foundation_load_path(
            Pu_gravity_kn=33.84,
            Tu_uplift_kn=18.50,
            Vu_shear_kn=3.50,
            Mz_base_moment_kn_m=4.90,
        )
        self.assertEqual(report.total_steps, 10)
        self.assertTrue(report.load_path_continuous)

        # 1. Independent First-Principles Numerical Integration of ISMB 300 Fillet Weld Group:
        # Cross-section: D = 300 mm, B = 140 mm, tf = 12.4 mm, tw = 7.5 mm. 6 mm fillet weld (effective throat tt = 0.70 * 6 = 4.20 mm per IS 800 Cl 10.5.3)
        weld_tt = 0.70 * 6.0  # 4.20 mm
        # Outer flanges: 2 * 140 mm at y = +-150 mm
        A_flange_out = 2.0 * 140.0 * weld_tt
        Ix_flange_out = 2.0 * 140.0 * weld_tt * (150.0 ** 2)
        # Inner flanges: 4 * (70 - 3.75) = 4 * 66.25 mm at y = +- (150 - 12.4) = +-137.6 mm
        A_flange_in = 4.0 * 66.25 * weld_tt
        Ix_flange_in = 4.0 * 66.25 * weld_tt * (137.6 ** 2)
        # Flange tips: 4 * 12.4 mm at y_mid = +-(150 - 6.2) = +-143.8 mm
        A_flange_tips = 4.0 * 12.4 * weld_tt
        Ix_flange_tips = 4.0 * 12.4 * weld_tt * (143.8 ** 2)
        # Web welds: 2 * (300 - 2*12.4) = 2 * 275.2 mm
        A_web = 2.0 * 275.2 * weld_tt
        Ix_web = 2.0 * (weld_tt * (275.2 ** 3)) / 12.0
        # Totals:
        indep_Aw = A_flange_out + A_flange_in + A_flange_tips + A_web  # 4809.0 mm2
        indep_Ix = Ix_flange_out + Ix_flange_in + Ix_flange_tips + Ix_web  # 6.6433e7 mm4
        indep_Zw = indep_Ix / 150.0  # 442,888.5 mm3

        # Permissible weld stress: fvwd = 410 / (sqrt(3) * 1.25) = 189.37 MPa
        indep_fvwd = 410.0 / (math.sqrt(3.0) * 1.25)

        # Gravity load case: Pu = 33.84 kN, Mz = 4.90 kNm, Vu = 3.50 kN
        indep_fa_grav = (33.84 * 1000.0) / indep_Aw  # 7.037 MPa
        indep_fb = (4.90 * 1e6) / indep_Zw           # 11.064 MPa
        indep_q = (3.50 * 1000.0) / indep_Aw         # 0.728 MPa
        indep_fe_grav = math.sqrt(((indep_fa_grav + indep_fb) ** 2) + 3.0 * (indep_q ** 2))  # 18.144 MPa
        indep_ur_weld_grav = indep_fe_grav / indep_fvwd  # 0.0958

        self.assertAlmostEqual(report.baseplate_weld_combined_stress_fe_mpa, indep_fe_grav, delta=0.05)
        self.assertAlmostEqual(report.baseplate_weld_permissible_fvwd_mpa, indep_fvwd, delta=0.05)
        self.assertAlmostEqual(report.baseplate_weld_combined_unity_ratio, indep_ur_weld_grav, delta=0.005)
        self.assertTrue(report.baseplate_weld_passed)

        # Direct verification of parametric weld group solver for uplift load case:
        weld_segments = create_ismb300_contour_weld_group(6.0)
        solver = ParametricWeldGroupSolver(weld_segments)
        weld_up = solver.evaluate_combined_stress(18.50, 3.50, 4.90, is_uplift=True)
        indep_fa_up = (18.50 * 1000.0) / indep_Aw   # 3.847 MPa tension adds to bending tension on tension flange
        indep_fe_up = math.sqrt(((indep_fa_up + indep_fb) ** 2) + 3.0 * (indep_q ** 2))  # 14.964 MPa
        self.assertAlmostEqual(weld_up.combined_stress_fe_mpa, indep_fe_up, delta=0.05)
        self.assertAlmostEqual(weld_up.unity_ratio, indep_fe_up / indep_fvwd, delta=0.005)

        # 2. Independent Host Slab Punching Shear & Unbalanced Moment Solver (IS 456 Cl 31.6.2):
        # Baseplate 350x250 mm, slab d = 100 mm, fck = 20 MPa
        indep_b1 = 350.0 + 100.0  # 450 mm
        indep_b2 = 250.0 + 100.0  # 350 mm
        indep_b0 = 2.0 * (indep_b1 + indep_b2)  # 1600 mm
        indep_tau_c = 0.25 * math.sqrt(20.0)    # 1.1180 MPa
        indep_alpha_v = 1.0 - (1.0 / (1.0 + (2.0 / 3.0) * math.sqrt(indep_b1 / indep_b2)))  # 0.4305
        indep_Mv = indep_alpha_v * 4.90         # 2.109 kNm
        indep_Jc = (100.0 * (indep_b1 ** 3) / 6.0) + (indep_b1 * (100.0 ** 3) / 6.0) + (100.0 * indep_b2 * (indep_b1 ** 2) / 2.0)
        indep_tau_dir = (33.84 * 1000.0) / (indep_b0 * 100.0)
        indep_tau_mom = (indep_Mv * 1e6 * (indep_b1 / 2.0)) / indep_Jc
        indep_tau_max = indep_tau_dir + indep_tau_mom  # 0.3039 MPa
        indep_ur_punch = indep_tau_max / indep_tau_c   # 0.2718

        self.assertAlmostEqual(report.slab_punching_combined_shear_tau_v_mpa, indep_tau_max, delta=0.005)
        self.assertAlmostEqual(report.slab_punching_permissible_tau_c_mpa, indep_tau_c, delta=0.005)
        self.assertAlmostEqual(report.slab_punching_combined_unity_ratio, indep_ur_punch, delta=0.005)
        self.assertTrue(report.slab_punching_shear_passed)

        # 3. Independent Cracked Concrete Cone Breakout Solver (fib 58 / EN 1992-4):
        # 4x M16 anchors, hef = 125 mm, sx = 250 mm, sy = 150 mm, fck = 20 MPa
        indep_NRk_c0 = (9.75 * math.sqrt(20.0) * (125.0 ** 1.5)) / 1000.0  # 60.940 kN
        indep_AcN = (3.0 * 125.0 + 250.0) * (3.0 * 125.0 + 150.0)          # 328,125 mm2
        indep_AcN0 = (3.0 * 125.0) ** 2                                     # 140,625 mm2
        indep_NRk_c = indep_NRk_c0 * (indep_AcN / indep_AcN0)              # 142.193 kN
        indep_phi_Ncbg_uncr = indep_NRk_c / 1.50                            # 94.795 kN
        indep_phi_Ncbg_cr = indep_phi_Ncbg_uncr * 0.70                      # 66.357 kN
        indep_ur_breakout = 18.50 / indep_phi_Ncbg_cr                       # 0.2788

        self.assertAlmostEqual(report.slab_uplift_tension_breakout_capacity_cracked_kn, indep_phi_Ncbg_cr, delta=0.1)
        self.assertAlmostEqual(report.slab_uplift_tension_breakout_unity_ratio, indep_ur_breakout, delta=0.005)

        # 4. Inclined Fillet Weld Segment Centroidal Inertia Solver (WP-03 / DEF-03):
        # A 45-degree fillet weld segment must have non-zero I0x, I0y, I0xy per Blodgett (1966) / IS 800 Cl 10.5.10
        incl_seg = WeldSegment(x1=0.0, y1=0.0, x2=100.0, y2=100.0, size_mm=6.0)
        incl_solver = ParametricWeldGroupSolver([incl_seg])
        self.assertGreater(incl_solver.Ixx, 0.0)
        self.assertGreater(incl_solver.Iyy, 0.0)
        self.assertGreater(incl_solver.Ixy, 0.0)
        self.assertAlmostEqual(incl_solver.Ixx, incl_solver.Iyy, delta=1.0)

        # 5. 6-DOF Multi-Axis Weld Group Solver Verification (IS 800 Cl 10.5.10.1.1):
        weld_6dof = solver.evaluate_6dof_combined_stress(
            Pu_kn=33.84,
            Vux_kn=3.50,
            Vuy_kn=2.00,
            Mux_kn_m=4.90,
            Muy_kn_m=1.50,
            Mt_kn_m=0.80,
        )
        self.assertTrue(weld_6dof.passed)
        self.assertLess(weld_6dof.unity_ratio, 0.30)
        self.assertGreater(weld_6dof.shear_stress_torsion_tau_t_mpa, 0.0)
        self.assertAlmostEqual(weld_6dof.permissible_stress_fvwd_mpa, indep_fvwd, delta=0.05)

        # 6. Foundation Load Path Step 4 Capacity Check (WP-01 / DEF-01 Mandate):
        step_4 = [s for s in report.load_path_steps if s.step_number == 4][0]
        self.assertIn("90.40 kNm", step_4.governing_capacity)
        self.assertIn("Parabolic Cb=1.2987", step_4.governing_capacity)
        self.assertAlmostEqual(step_4.unity_ratio, 0.447, delta=0.01)

    # -------------------------------------------------------------------------
    # TEST 10: Hermetic Historical Record Verification (DEF-05)
    # -------------------------------------------------------------------------
    def test_10_historical_records_in_isolated_environment(self):
        """[Category J: Database Immutability & Run Traceability] IEEE 1012 Configuration Audit: Verifies 20 historical runs inside hermetic temporary database."""
        # Connect strictly to isolated temporary DB path, NEVER to PROD_STRUCTURAL_DB
        self.assertNotEqual(os.path.abspath(self.iso.structural_db_path), PROD_STRUCTURAL_DB)
        conn = sqlite3.connect(self.iso.structural_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 20, f"Expected exactly 20 historical calculation runs in isolated DB, found {count}")

    # -------------------------------------------------------------------------
    # TEST 11: Original Canonical Holds Active and Enforced (WP-09)
    # -------------------------------------------------------------------------
    def test_11_original_holds_active_and_enforced(self):
        """[Category K: Canonical Governance & Verification Holds] ISO 9001 / IEEE 1012: Verifies all 12 canonical engineering holds remain active and enforced."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(all_holds), 12, "All 12 canonical engineering holds must exist")
        system_a_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            MountingSystemType.SYSTEM_A_CANOPY.value
        )
        self.assertEqual(len(system_a_holds), 10, "Expected exactly 10 applicable holds for System A")

        hold_ids = [h.hold_id for h in system_a_holds]
        for expected in [
            "INSPECTION_REQUIRED_HOLD",
            "AERODYNAMIC_UNSUPPORTED_HOLD",
            "WIND_COORD_UNVERIFIED_HOLD",
            "WIND_TRANSFORM_UNVERIFIED_HOLD",
            "VERTICAL_SEISMIC_APPLICABILITY_HOLD",
            "LOAD_COMBINATION_PROVISIONAL_HOLD",
            "FASTENER_TORQUE_UNVERIFIED_HOLD",
            "NUMERICAL_INSTABILITY_HOLD",
            "ASSUMED_DATA_CERTIFICATION_HOLD",
            "DRAWING_UNVERIFIED_HOLD",
        ]:
            self.assertIn(expected, hold_ids)

    # -------------------------------------------------------------------------
    # TEST 12: Statutory Lock & Watermark in Isolated DB (DEF-05)
    # -------------------------------------------------------------------------
    def test_12_afc_lock_and_statutory_watermark_in_isolated_environment(self):
        """[Category L: Statutory Construction Safety Lock] IEEE 1012 Life-Safety Gate: Verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark in isolated database."""
        conn = sqlite3.connect(self.iso.structural_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT construction_status, is_approved_for_construction, watermark FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        rows = cursor.fetchall()
        conn.close()
        self.assertGreater(len(rows), 0)
        for constr_status, afc_flag, watermark in rows:
            self.assertEqual(constr_status, "BLOCKED_AFC_LOCKED")
            self.assertEqual(afc_flag, 0)
            self.assertIn("NOT FOR CONSTRUCTION", watermark)

    # -------------------------------------------------------------------------
    # TEST 13: Zero Production Database Access Assertion (DEF-05)
    # -------------------------------------------------------------------------
    def test_13_zero_production_database_access_verified(self):
        """[Category M: Hermetic Runtime Boundary] ASME V&V 10 Boundary Verification: Formally asserts that active runtime paths differ from production."""
        self.iso.assert_isolated_paths()
        self.assertTrue(os.path.exists(self.iso.structural_db_path))
        self.assertIn("rensun_test_iso_", self.iso.structural_db_path)

    # -------------------------------------------------------------------------
    # TEST 14: Boundary & Parametric Weld Geometry / Slab Feasibility (DEF-03 & DEF-04)
    # -------------------------------------------------------------------------
    def test_14_boundary_and_parametric_weld_geometry(self):
        """[Category N: Boundary Extremes & Rebar Clash Risk] ASME V&V 10 Stress Boundary: Boundary test for asymmetric weld group, web flexibility, Temperature Range II derating, and rebar clash risk."""
        # 1. Asymmetric weld group boundary test
        asym_segments = [
            WeldSegment(x1=-100.0, y1=100.0, x2=100.0, y2=100.0, size_mm=6.0),
            WeldSegment(x1=-50.0, y1=-100.0, x2=50.0, y2=-100.0, size_mm=6.0),
            WeldSegment(x1=0.0, y1=-100.0, x2=0.0, y2=100.0, size_mm=6.0),
        ]
        asym_solver = ParametricWeldGroupSolver(asym_segments)
        self.assertGreater(asym_solver.total_length_mm, 0.0)
        self.assertNotEqual(asym_solver.cy, 0.0)  # Shifting centroid detected

        # 2. Purlin web flexibility boundary: direct attachment to 2 mm web yields < 1 kN/mm stiffness
        check_purlin = design_bottom_flange_fly_bracing(purlin_web_thickness_mm=2.0)
        self.assertLess(check_purlin.system_series_stiffness_without_cleat_kn_mm, 1.0)
        self.assertTrue(check_purlin.direct_cleat_attachment_mandatory)

        # 3. Slab depth clearance boundary: hef = 125 mm in 150 mm slab triggers infeasibility
        anchor_125 = ProductSpecificChemicalAnchorModel(hef_mm=125.0, assumed_slab_thickness_mm=150.0)
        res_125 = anchor_125.evaluate_anchor_group_capacity()
        self.assertFalse(res_125.is_slab_thickness_feasible)
        self.assertEqual(res_125.feasibility_status, "BLOCKED_PHYSICALLY_INFEASIBLE_IN_150MM_SLAB")

        # In contrast, reduced embedment hef = 80 mm is conditionally feasible with mandatory GPR scan
        anchor_80 = ProductSpecificChemicalAnchorModel(hef_mm=80.0, assumed_slab_thickness_mm=150.0)
        res_80 = anchor_80.evaluate_anchor_group_capacity()
        self.assertTrue(res_80.is_slab_thickness_feasible)
        self.assertEqual(res_80.feasibility_status, "CONDITIONALLY_FEASIBLE_SUBJECT_TO_GPR_REBAR_SCAN_AND_PULL_TEST")
        self.assertTrue(res_80.rebar_clash_risk_flag)
        self.assertEqual(res_80.tau_Rk_cracked_derated_mpa, 6.5)
        self.assertEqual(res_80.temperature_range, "RANGE_II_50_72_DEG")

    # -------------------------------------------------------------------------
    # TEST 15: Connection Interception Enforcement (DEF-05)
    # -------------------------------------------------------------------------
    def test_15_connection_interception_enforcement(self):
        """WP-05 / DEF-05: Proves that ConnectionAuditor actively blocks direct connection to production DBs across paths, URIs, and symlinks."""
        # 1. Attempting to connect to PROD_STRUCTURAL_DB MUST raise RuntimeError
        with self.assertRaises(RuntimeError) as ctx_struct:
            sqlite3.connect(PROD_STRUCTURAL_DB)
        self.assertIn("CRITICAL TEST ISOLATION VIOLATION", str(ctx_struct.exception))
        self.assertIn(PROD_STRUCTURAL_DB, str(ctx_struct.exception))

        # 2. Attempting to connect to PROD_QUOTATIONS_DB MUST raise RuntimeError
        with self.assertRaises(RuntimeError) as ctx_quot:
            sqlite3.connect(PROD_QUOTATIONS_DB)
        self.assertIn("CRITICAL TEST ISOLATION VIOLATION", str(ctx_quot.exception))
        self.assertIn(PROD_QUOTATIONS_DB, str(ctx_quot.exception))

        # 3. Direct Connection instantiation MUST raise RuntimeError
        with self.assertRaises(RuntimeError):
            sqlite3.Connection(PROD_STRUCTURAL_DB)

        with self.assertRaises(RuntimeError):
            sqlite3.Connection(PROD_QUOTATIONS_DB)

        # 4. URI scheme connection attempt MUST raise RuntimeError
        uri_target = f"file:{PROD_STRUCTURAL_DB}?mode=ro"
        with self.assertRaises(RuntimeError):
            sqlite3.connect(uri_target, uri=True)

        # 5. Symlink connection attempt MUST raise RuntimeError (resolved via canonicalization)
        symlink_path = os.path.join(self.iso.tmp_path, "symlink_to_prod_struct.db")
        try:
            os.symlink(PROD_STRUCTURAL_DB, symlink_path)
            with self.assertRaises(RuntimeError):
                sqlite3.connect(symlink_path)
        finally:
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)

        # 6. Verify that auditor registered all rejected attempts
        self.assertIn(PROD_STRUCTURAL_DB, self.iso.auditor.rejected_attempts)
        self.assertIn(PROD_QUOTATIONS_DB, self.iso.auditor.rejected_attempts)


if __name__ == "__main__":
    unittest.main()
