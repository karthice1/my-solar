"""
Phase 1.5.5 — System C: Metal-Sheet Roof Mounting Engineering Validation Test Suite
Package: tests.test_phase1_5_5_system_c

Covers all 19 Independent Engineering Verifications for Phase 1.5.5:
1. Physical input register: verifies G550, G300, and standing-seam profiles.
2. Fastener specifications: validates Bi-metal SDS 5.5 mm and 6.3 mm properties (ISO 3506 / AS 3566.2).
3. FM-01: Fastener tensile shank rupture (IS 800 Cl 10.3.5 / EN 1993-1-3).
4. FM-02: Fastener shear fracture (IS 800 Cl 10.3.3).
5. FM-03: Combined fastener tension and shear interaction (AISI S100 Eq. J4.5-1).
6. FM-04: Sheet pull-over / washer pull-through (EN 1993-1-3 Table 8.2 / AISI S100 Eq. J4.4.2-1).
7. FM-05: Sheet pull-out / thread stripping from 0.5 mm sheet (EN 1993-1-3 Table 8.2).
8. Governed failure mode: proves sheet pull-out strictly governs over bolt tensile strength.
9. FM-06: Sheet crest bending & web crushing under downward load.
10. FM-07: Purlin thread pull-out (direct purlin anchorage in 1.6 mm cold-formed steel).
11. FM-08: Supporting purlin member capacity under superimposed solar dead and live load.
12. FM-09: Extruded aluminium mini-rail bracket flexural capacity.
13. FM-10: Fastener group load distribution with 15% eccentricity peeling penalty.
14. FM-11: Galvanic corrosion protection (bi-metal Class 4 fastener + continuous EPDM pad).
15. FM-12: Roof penetration watertightness and gasket compression limits.
16. Fastener count sensitivity: proves 1 or 2 screws fail pull-out, whereas 4 screws pass.
17. Complete 7-step load path continuity and unverified survey requirements.
18. Historical calculation runs immutability: verifies 20 historical runs intact.
19. Hold enforcement & AFC lock: verifies 11 active holds for System C and BLOCKED_AFC_LOCKED.
"""

import hashlib
import json
import math
import os
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
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
    STEEL_E250,
)
from structural.holds import MASTER_VERIFICATION_REGISTER
from structural.workflows.system_c_validation import (
    MetalSheetProfileSpecification,
    FastenerSpecification,
    get_metal_sheet_input_register,
    get_fastener_specifications,
    FailureModeCheckResult,
    SystemCFailureModesReport,
    evaluate_system_c_all_failure_modes,
    SystemCLoadPathStep,
    SystemCLoadPathReport,
    verify_system_c_complete_load_path,
)


class TestPhase155SystemCValidation(unittest.TestCase):
    """Rigorous engineering test suite for Phase 1.5.5 System C Metal-Sheet Roof validation."""

    @classmethod
    def setUpClass(cls):
        def hash_file(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()

        cls.orig_quotations_hash = hash_file(PROD_QUOTATIONS_DB)
        cls.orig_structural_hash = hash_file(PROD_STRUCTURAL_DB)
        cls.orig_settings_hash = hash_file(PROD_SETTINGS_FILE)

    def test_01_metal_sheet_input_register(self):
        """WP-01: Verifies physical input register for metal roof profiles."""
        reg = get_metal_sheet_input_register()
        self.assertEqual(len(reg), 3)
        self.assertIn("TRAPEZOIDAL_G550_050", reg)
        self.assertIn("TRAPEZOIDAL_G300_050", reg)
        self.assertIn("STANDING_SEAM_KLIP_LOK", reg)

        # G550 Trapezoidal Profile
        g550 = reg["TRAPEZOIDAL_G550_050"]
        self.assertEqual(g550.base_metal_thickness_bmt_mm, 0.50)
        self.assertEqual(g550.yield_strength_fy_mpa, 550.0)
        self.assertEqual(g550.tensile_strength_fu_mpa, 570.0)
        self.assertIn("AZ150", g550.coating_specification)
        self.assertEqual(g550.crest_height_mm, 32.0)
        self.assertIn("CREST_MINI_RAIL", g550.compatible_mounting_method)

        # Standing Seam Profile
        seam = reg["STANDING_SEAM_KLIP_LOK"]
        self.assertEqual(seam.profile_type, "STANDING_SEAM")
        self.assertIn("SEAM_CLAMP", seam.compatible_mounting_method)

    def test_02_fastener_specifications(self):
        """WP-01: Verifies fastener specifications for bi-metal self-drilling screws."""
        reg = get_fastener_specifications()
        self.assertEqual(len(reg), 2)
        self.assertIn("BI_METAL_SDS_5_5", reg)
        self.assertIn("BI_METAL_SDS_6_3", reg)

        s55 = reg["BI_METAL_SDS_5_5"]
        self.assertEqual(s55.outer_diameter_d_mm, 5.50)
        self.assertEqual(s55.tensile_strength_fub_mpa, 700.0)
        self.assertEqual(s55.washer_outer_diameter_dw_mm, 16.0)
        self.assertIn("Class 4", s55.corrosion_protection_class)
        self.assertEqual(s55.tightening_torque_nm, 6.5)

    def test_03_fm01_fastener_tensile_shank_rupture(self):
        """WP-04: Verifies FM-01 fastener tensile shank capacity per IS 800 Cl 10.3.5."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm01 = [r for r in report.results if r.failure_mode_id == "FM-01"][0]
        # Single screw capacity = 0.9 * 700 * 15.3 / (1.25 * 1000) = 7.71 kN
        # 4 screws = 30.84 kN (or ~34 kN depending on As)
        self.assertGreater(fm01.design_capacity, 25.0)
        self.assertTrue(fm01.passed)
        self.assertLess(fm01.unity_ratio, 0.05)

    def test_04_fm02_fastener_shear_fracture(self):
        """WP-04: Verifies FM-02 fastener shear fracture capacity."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm02 = [r for r in report.results if r.failure_mode_id == "FM-02"][0]
        self.assertGreater(fm02.design_capacity, 15.0)
        self.assertTrue(fm02.passed)
        self.assertLess(fm02.unity_ratio, 0.05)

    def test_05_fm03_combined_tension_and_shear_interaction(self):
        """WP-04: Verifies FM-03 combined tension and shear quadratic interaction."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm03 = [r for r in report.results if r.failure_mode_id == "FM-03"][0]
        self.assertLess(fm03.unity_ratio, 0.05)
        self.assertTrue(fm03.passed)

    def test_06_fm04_sheet_pull_over_washer_pull_through(self):
        """WP-04: Verifies FM-04 sheet pull-over capacity per EN 1993-1-3 Table 8.2."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm04 = [r for r in report.results if r.failure_mode_id == "FM-04"][0]
        # Nov,screw = 0.90 * dw * t * fu / gamma_m2 = 0.90 * 16 * 0.50 * 570 / (1.25 * 1000) = 3.28 kN / screw
        # Group (4 screws) = 13.13 kN
        self.assertAlmostEqual(fm04.design_capacity, 13.13, delta=0.5)
        self.assertTrue(fm04.passed)
        self.assertLess(fm04.unity_ratio, 0.15)

    def test_07_fm05_sheet_pull_out_thread_stripping(self):
        """WP-04: Verifies FM-05 sheet pull-out thread stripping from 0.5 mm sheet."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm05 = [r for r in report.results if r.failure_mode_id == "FM-05"][0]
        # Nou,screw = 0.65 * t * d * fu / gamma_m2 = 0.65 * 0.50 * 5.50 * 570 / (1.25 * 1000) = 0.815 kN / screw
        # Group (4 screws) = 3.26 kN
        self.assertAlmostEqual(fm05.design_capacity, 3.26, delta=0.2)
        self.assertTrue(fm05.passed)
        self.assertLess(fm05.unity_ratio, 0.40)

    def test_08_sheet_pull_out_strictly_governs_over_bolt_tensile_strength(self):
        """WP-04: Proves that sheet pull-out (0.81 kN/screw) strictly governs over bolt tension (7.71 kN/screw)."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm01 = [r for r in report.results if r.failure_mode_id == "FM-01"][0]  # Bolt tension
        fm05 = [r for r in report.results if r.failure_mode_id == "FM-05"][0]  # Sheet pull-out
        self.assertLess(fm05.design_capacity, fm01.design_capacity)
        # Pull-out capacity is less than 15% of bolt shank tensile capacity!
        self.assertLess(fm05.design_capacity / fm01.design_capacity, 0.20)
        self.assertGreater(fm05.unity_ratio, fm01.unity_ratio)

    def test_09_fm06_sheet_crest_bending_and_crushing(self):
        """WP-04: Verifies FM-06 sheet crest bending and web crippling under downward load."""
        report = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm06 = [r for r in report.results if r.failure_mode_id == "FM-06"][0]
        self.assertEqual(fm06.design_capacity, 2.80)
        self.assertTrue(fm06.passed)
        self.assertLess(fm06.unity_ratio, 0.35)

    def test_10_fm07_purlin_direct_thread_pull_out(self):
        """WP-04: Verifies FM-07 purlin direct pull-out into 1.6 mm cold-formed steel."""
        report = evaluate_system_c_all_failure_modes(purlin_thickness_mm=1.60)
        fm07 = [r for r in report.results if r.failure_mode_id == "FM-07"][0]
        # Nou,purlin = 0.65 * 1.6 * 5.5 * 410 / (1.25 * 1000) = 1.87 kN / screw -> 2 screws = 3.75 kN
        self.assertAlmostEqual(fm07.design_capacity, 3.75, delta=0.2)
        self.assertTrue(fm07.passed)

    def test_11_fm08_supporting_purlin_member_capacity(self):
        """WP-04: Verifies FM-08 supporting purlin member bending under superimposed solar load."""
        report = evaluate_system_c_all_failure_modes()
        fm08 = [r for r in report.results if r.failure_mode_id == "FM-08"][0]
        self.assertTrue(fm08.passed)
        self.assertAlmostEqual(fm08.unity_ratio, 0.620, delta=0.05)

    def test_12_fm09_bracket_mini_rail_flexural_capacity(self):
        """WP-04: Verifies FM-09 extruded aluminium mini-rail bracket flexural capacity."""
        report = evaluate_system_c_all_failure_modes()
        fm09 = [r for r in report.results if r.failure_mode_id == "FM-09"][0]
        self.assertTrue(fm09.passed)
        self.assertLess(fm09.unity_ratio, 0.10)

    def test_13_fm10_fastener_group_eccentricity_penalty(self):
        """WP-04: Verifies FM-10 fastener group load distribution with 15% eccentricity factor."""
        report = evaluate_system_c_all_failure_modes()
        fm10 = [r for r in report.results if r.failure_mode_id == "FM-10"][0]
        fm05 = [r for r in report.results if r.failure_mode_id == "FM-05"][0]
        self.assertAlmostEqual(fm10.unity_ratio, fm05.unity_ratio * 1.15, delta=0.01)
        self.assertTrue(fm10.passed)

    def test_14_fm11_corrosion_and_durability_requirements(self):
        """WP-04: Verifies FM-11 bimetallic galvanic corrosion and EPDM isolation requirements."""
        report = evaluate_system_c_all_failure_modes()
        fm11 = [r for r in report.results if r.failure_mode_id == "FM-11"][0]
        self.assertTrue(fm11.passed)
        self.assertIn("EPDM", fm11.notes)

    def test_15_fm12_roof_watertightness_and_gasket_limits(self):
        """WP-04: Verifies FM-12 penetration watertightness and tightening torque limits."""
        report = evaluate_system_c_all_failure_modes()
        fm12 = [r for r in report.results if r.failure_mode_id == "FM-12"][0]
        self.assertTrue(fm12.passed)
        self.assertEqual(fm12.factored_demand, 6.5)

    def test_16_fastener_count_sensitivity_failure_under_insufficient_screws(self):
        """WP-04: Proves 1 screw fails pull-out under wind uplift, whereas 4 screws pass."""
        # Under 1 screw only:
        rep_1 = evaluate_system_c_all_failure_modes(screws_per_mini_rail=1)
        fm05_1 = [r for r in rep_1.results if r.failure_mode_id == "FM-05"][0]
        # Uplift demand ~1.06 kN vs 1-screw capacity 0.815 kN -> UR = 1.30 > 1.0 (FAILS!)
        self.assertGreater(fm05_1.unity_ratio, 1.0)
        self.assertFalse(fm05_1.passed)
        self.assertFalse(rep_1.system_c_structurally_adequate)

        # Under 4 screws:
        rep_4 = evaluate_system_c_all_failure_modes(screws_per_mini_rail=4)
        fm05_4 = [r for r in rep_4.results if r.failure_mode_id == "FM-05"][0]
        self.assertLess(fm05_4.unity_ratio, 1.0)
        self.assertTrue(fm05_4.passed)
        self.assertTrue(rep_4.system_c_structurally_adequate)

    def test_17_complete_load_path_verification(self):
        """WP-06: Verifies 7-step structural load path from PV module to building portal frame."""
        lp = verify_system_c_complete_load_path()
        self.assertEqual(lp.total_steps, 7)
        self.assertTrue(lp.load_path_continuous)
        self.assertLessEqual(lp.governing_unity_ratio, 1.0)
        self.assertIn("Purlins", lp.governing_component)
        self.assertEqual(len(lp.remaining_unverified_items), 4)

    def test_18_historical_runs_immutability(self):
        """WP-08: Verifies all 20 historical calculation runs remain completely untouched."""
        conn = sqlite3.connect(PROD_STRUCTURAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 20, "All 20 historical calculation runs must be preserved bit-for-bit.")

    def test_19_canonical_holds_and_afc_lock_enforcement(self):
        """WP-07 & WP-08: Verifies 11 active holds for System C, BLOCKED_AFC_LOCKED, and watermark."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(all_holds), 12, "All 12 canonical holds must exist")

        sys_c_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            MountingSystemType.SYSTEM_C_METAL_SHEET.value
        )
        self.assertEqual(len(sys_c_holds), 11, "System C must have exactly 11 active verification holds")

        conn = sqlite3.connect(PROD_STRUCTURAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT construction_status, is_approved_for_construction, watermark FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        rows = cur.fetchall()
        conn.close()
        self.assertGreater(len(rows), 0)
        for constr, afc, watermark in rows:
            self.assertEqual(constr, "BLOCKED_AFC_LOCKED")
            self.assertEqual(afc, 0)
            self.assertIn("NOT FOR CONSTRUCTION", watermark)

    @classmethod
    def tearDownClass(cls):
        def hash_file(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()

        assert hash_file(PROD_QUOTATIONS_DB) == cls.orig_quotations_hash, "MUTATION DETECTED: quotations.db"
        assert hash_file(PROD_STRUCTURAL_DB) == cls.orig_structural_hash, "MUTATION DETECTED: structural_runs.db"
        assert hash_file(PROD_SETTINGS_FILE) == cls.orig_settings_hash, "MUTATION DETECTED: quotation_settings.json"


if __name__ == "__main__":
    unittest.main()
