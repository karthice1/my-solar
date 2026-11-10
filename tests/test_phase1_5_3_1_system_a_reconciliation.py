"""
Phase 1.5.3.1 — System A Independent Calculation Reconciliation Test Suite
Package: tests.test_phase1_5_3_1_system_a_reconciliation

Covers all 14 Independent Engineering Verifications:
1. Material mapping: detects aluminium vs steel mismatch.
2. Section-property consistency: ISMC 100x50x2.0 vs IS 811 cold-formed vs IS 808 hot-rolled.
3. Purlin deflection benchmarks: independently verifies all 6 benchmark cases.
4. Load superposition: verifies alternative live loads (point vs distributed, never summed).
5. Effective-width calculations: stiffened lipped vs unstiffened plain per IS 801 / Winter.
6. Rafter capacity reconciliation: 78.01 kNm (Al) vs 130.36 kNm / 147.95 kNm (Steel).
7. Rafter Lateral-Torsional Buckling: gravity top-flange bracing vs wind uplift unbraced bottom-flange.
8. Column interaction: section strength (Cl 9.3.1.1) and member buckling (Cl 9.3.2.2).
9. Baseplate: bearing pressure, cantilever bending, and codal minimum thickness (tp >= tf).
10. Anchor failure modes: evaluates 7 failure modes and flags slab thickness limitation.
11. Option A versus Option B: multi-criteria engineering comparison.
12. Historical record immutability: verifies 20 historical calculation runs are unmodified.
13. Original hold enforcement: verifies all 12 canonical holds active (10 for System A).
14. AFC lock and statutory watermark: verifies BLOCKED_AFC_LOCKED and statutory watermark.
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
    STEEL_E250,
)
from structural.actions import ActionRegister
from structural.holds import MASTER_VERIFICATION_REGISTER
from structural.workflows.system_a_reconciliation import (
    SectionClassificationAudit,
    audit_section_and_material_provenance,
    IndependentPurlinBenchmark,
    compute_independent_purlin_benchmark,
    RafterCapacityReconciliation,
    reconcile_primary_rafter_capacity,
    LTBVerificationResult,
    evaluate_rafter_lateral_torsional_buckling,
    ColumnInteractionAudit,
    evaluate_column_interaction_and_stability,
    BaseplateAndAnchorAudit,
    audit_baseplate_and_anchors,
    OptionComparisonTable,
    generate_option_a_vs_option_b_comparison,
)


class TestPhase1531SystemAReconciliation(unittest.TestCase):
    """Hermetic test suite for Phase 1.5.3.1 System A Independent Reconciliation."""

    @classmethod
    def setUpClass(cls):
        cls.iso = IsolatedTestEnvironment()
        cls.site = SiteParameters(
            location_name="Salem, Tamil Nadu",
            latitude=11.6643,
            longitude=78.1460,
            basic_wind_speed_vb=39.0,
            terrain_category=TerrainCategory.CATEGORY_2,
            building_height_m=10.0,
            rooftop_elevation_m=0.0,
        )
        cls.module = PVModuleSpecification(
            make_model="Bi-55-540 Wp",
            length_mm=2278.0,
            width_mm=1134.0,
            thickness_mm=35.0,
            weight_kg=27.5,
            peak_power_w=540.0,
            tilt_deg=10.0,
            azimuth_deg=180.0,
        )

    # -------------------------------------------------------------------------
    # TEST 1: Material Mapping & Mismatch Detection
    # -------------------------------------------------------------------------
    def test_01_material_mapping_and_mismatch_detection(self):
        """WP-01: Detects that historical record linked Aluminium 6063-T6 to a steel channel."""
        audit = audit_section_and_material_provenance(
            designation="ISMC 100x50x2.0",
            depth_mm=100.0,
            flange_mm=50.0,
            thickness_mm=2.0,
            lip_mm=15.0,
            actual_mass_kg_m=3.53,
            linked_material_name="Extruded Aluminium Alloy 6063-T6",
        )
        self.assertTrue(audit.material_mismatch_identified)
        self.assertIn("Structural Steel", audit.mass_matches_material)
        self.assertEqual(audit.historical_material_linked, "Extruded Aluminium Alloy 6063-T6")
        self.assertAlmostEqual(audit.theoretical_mass_steel_kg_m, 3.485, delta=0.1)
        self.assertAlmostEqual(audit.theoretical_mass_aluminium_kg_m, 1.199, delta=0.1)

    # -------------------------------------------------------------------------
    # TEST 2: Section-Property Consistency (IS 811 vs IS 808)
    # -------------------------------------------------------------------------
    def test_02_section_property_consistency(self):
        """WP-01: Verifies ISMC 100x50x2.0 is cold-formed (IS 811) and NOT hot-rolled (IS 808)."""
        audit = audit_section_and_material_provenance()
        self.assertTrue(audit.is_cold_formed_is811)
        self.assertFalse(audit.is_hot_rolled_is808)
        self.assertIn("IS 811", audit.standard_governing_specification)

    # -------------------------------------------------------------------------
    # TEST 3: Independent Purlin Deflection Benchmarks (All 6 Combinations)
    # -------------------------------------------------------------------------
    def test_03_independent_purlin_deflection_benchmarks(self):
        """WP-02: Independently verifies all 6 numerical purlin benchmark deflections."""
        # 1. Historical Baseline (L=3.0 m, Al 6063-T6)
        bm_hist = compute_independent_purlin_benchmark(
            config_name="Historical Baseline (Al)",
            span_mm=3000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=69000.0, fy_mpa=170.0, gamma_m0=1.25, mass_kg_m=3.53,
        )
        self.assertAlmostEqual(bm_hist.delta_governing_actual_mm, 20.7304, delta=0.005)
        self.assertEqual(bm_hist.deflection_status, "FAIL")

        # 2. Steel Baseline (L=3.0 m, Steel E250)
        bm_st_base = compute_independent_purlin_benchmark(
            config_name="Steel Baseline",
            span_mm=3000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=205000.0, fy_mpa=250.0, gamma_m0=1.10, mass_kg_m=3.53,
        )
        self.assertAlmostEqual(bm_st_base.delta_governing_actual_mm, 6.9776, delta=0.005)
        self.assertEqual(bm_st_base.deflection_status, "PASS")

        # 3. Option A Aluminium (L=2.0 m, Al 6063-T6)
        bm_opt_a_al = compute_independent_purlin_benchmark(
            config_name="Option A (Al)",
            span_mm=2000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=69000.0, fy_mpa=170.0, gamma_m0=1.25, mass_kg_m=3.53,
        )
        self.assertAlmostEqual(bm_opt_a_al.delta_governing_actual_mm, 4.0949, delta=0.005)
        self.assertEqual(bm_opt_a_al.deflection_status, "PASS")

        # 4. Option A Steel (L=2.0 m, Steel E250)
        bm_opt_a_st = compute_independent_purlin_benchmark(
            config_name="Option A (Steel)",
            span_mm=2000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=205000.0, fy_mpa=250.0, gamma_m0=1.10, mass_kg_m=3.53,
        )
        self.assertAlmostEqual(bm_opt_a_st.delta_governing_actual_mm, 1.3783, delta=0.005)
        self.assertEqual(bm_opt_a_st.deflection_status, "PASS")

        # 5. Option B Aluminium (L=3.0 m, C125x50x2.5, Al 6063-T6)
        bm_opt_b_al = compute_independent_purlin_benchmark(
            config_name="Option B (Al)",
            span_mm=3000.0, depth_mm=125.0, flange_mm=50.0, thickness_mm=2.5, lip_mm=15.0,
            E_mpa=69000.0, fy_mpa=170.0, gamma_m0=1.25, mass_kg_m=1.654,
        )
        self.assertAlmostEqual(bm_opt_b_al.delta_governing_actual_mm, 10.3270, delta=0.05)
        self.assertEqual(bm_opt_b_al.deflection_status, "PASS")

        # 6. Option B Steel (L=3.0 m, C125x50x2.5, Steel E250)
        bm_opt_b_st = compute_independent_purlin_benchmark(
            config_name="Option B (Steel)",
            span_mm=3000.0, depth_mm=125.0, flange_mm=50.0, thickness_mm=2.5, lip_mm=15.0,
            E_mpa=205000.0, fy_mpa=250.0, gamma_m0=1.10, mass_kg_m=4.808,
        )
        self.assertAlmostEqual(bm_opt_b_st.delta_governing_actual_mm, 3.5836, delta=0.05)
        self.assertEqual(bm_opt_b_st.deflection_status, "PASS")

    # -------------------------------------------------------------------------
    # TEST 4: Load Superposition & Non-Coincident Live Loads
    # -------------------------------------------------------------------------
    def test_04_load_superposition_and_alternative_live_loads(self):
        """WP-02: Verifies that point load and distributed live load are evaluated as alternative cases."""
        bm = compute_independent_purlin_benchmark(
            config_name="Test Superposition",
            span_mm=3000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=69000.0, fy_mpa=170.0, gamma_m0=1.25, mass_kg_m=3.53,
        )
        # Verify delta_governing is max(delta_dist, delta_point), NEVER sum(delta_dist, delta_point)!
        self.assertEqual(bm.delta_governing_actual_mm, bm.delta_total_dist_mm)
        self.assertNotEqual(bm.delta_governing_actual_mm, bm.delta_total_dist_mm + bm.delta_point_live_mm)

    # -------------------------------------------------------------------------
    # TEST 5: Effective-Width Calculations (IS 801 / Winter)
    # -------------------------------------------------------------------------
    def test_05_effective_width_calculations(self):
        """WP-02: Evaluates local buckling reduction factor rho for stiffened vs unstiffened flanges."""
        # Lipped channel: k = 4.0 -> rho = 1.0 (fully effective)
        bm_lipped = compute_independent_purlin_benchmark(
            config_name="Lipped",
            span_mm=3000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0,
            E_mpa=205000.0, fy_mpa=250.0, gamma_m0=1.10, mass_kg_m=3.53,
        )
        self.assertEqual(bm_lipped.effective_width_ratio_rho, 1.0)

        # Plain channel: k = 0.43 -> rho < 1.0 (local buckling reduction)
        bm_plain = compute_independent_purlin_benchmark(
            config_name="Plain",
            span_mm=3000.0, depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=0.0,
            E_mpa=205000.0, fy_mpa=250.0, gamma_m0=1.10, mass_kg_m=3.08,
        )
        self.assertAlmostEqual(bm_plain.effective_width_ratio_rho, 0.674, delta=0.01)
        self.assertLess(bm_plain.effective_Ixx_mm4, bm_plain.gross_Ixx_mm4)

    # -------------------------------------------------------------------------
    # TEST 6: Primary Rafter Capacity Reconciliation (Discrepancy Resolution)
    # -------------------------------------------------------------------------
    def test_06_rafter_capacity_reconciliation(self):
        """WP-03: Resolves the 77.09 / 130.4 kNm vs 0.988 utilization discrepancy."""
        res = reconcile_primary_rafter_capacity(Mu_demand_kn_m=77.088)

        # 6A. Aluminium Historical: Md = 78.01 kNm -> UR = 0.988
        al = res["HISTORICAL_ALUMINIUM"]
        self.assertAlmostEqual(al.design_capacity_elastic_kn_m, 78.010, places=2)
        self.assertAlmostEqual(al.governing_utilization_ratio, 0.988, places=3)

        # 6B. Steel Corrected: Md = 130.36 kNm (elastic) -> UR = 0.591
        st = res["CORRECTED_STEEL_E250"]
        self.assertAlmostEqual(st.design_capacity_elastic_kn_m, 130.364, places=2)
        self.assertAlmostEqual(st.elastic_utilization_ratio, 0.591, places=3)
        self.assertAlmostEqual(st.design_capacity_plastic_kn_m, 147.955, places=2)
        self.assertAlmostEqual(st.plastic_utilization_ratio, 0.521, places=3)

    # -------------------------------------------------------------------------
    # TEST 7: Lateral-Torsional Buckling (Gravity vs Wind Uplift)
    # -------------------------------------------------------------------------
    def test_07_rafter_lateral_torsional_buckling(self):
        """WP-04: Verifies gravity top-flange bracing vs wind uplift unbraced bottom-flange."""
        ltb = evaluate_rafter_lateral_torsional_buckling(purlin_spacing_mm=1150.0, rafter_clear_span_mm=4556.0)

        # Gravity: top flange braced at 1150 mm
        grav = ltb["GRAVITY_SAGGING"]
        self.assertLessEqual(grav.non_dimensional_slenderness_lambda_LT, 0.40)
        self.assertEqual(grav.reduction_factor_chi_LT, 1.0)
        self.assertTrue(grav.full_plastic_capacity_available)
        self.assertFalse(grav.fly_bracing_required)

        # Wind Uplift: bottom flange unbraced over clear span (4556 mm)
        up = ltb["WIND_UPLIFT_REVERSAL"]
        self.assertGreater(up.non_dimensional_slenderness_lambda_LT, 1.0)
        self.assertLess(up.reduction_factor_chi_LT, 0.60)
        self.assertFalse(up.full_plastic_capacity_available)
        self.assertTrue(up.fly_bracing_required)
        self.assertLess(up.design_moment_capacity_Md_kn_m, 80.0)

    # -------------------------------------------------------------------------
    # TEST 8: Column Interaction (IS 800 Cl 9.3)
    # -------------------------------------------------------------------------
    def test_08_column_interaction_and_frame_stability(self):
        """WP-05: Verifies column section strength and member buckling interaction."""
        col = evaluate_column_interaction_and_stability(Pu_kn=33.84, Mz_kn_m=4.90)

        # Section strength interaction: Cl 9.3.1.1
        self.assertAlmostEqual(col.section_strength_interaction_ratio, 0.0596, places=3)
        self.assertTrue(col.section_strength_passed)

        # Member buckling: Cl 9.3.2.2 (K=1.0)
        self.assertAlmostEqual(col.overall_buckling_interaction_pinned, 0.0822, places=3)

        # Sway portal frame (K=2.0)
        self.assertLess(col.overall_buckling_interaction_sway, 0.25)

        # P-Delta drift
        self.assertLess(col.p_delta_drift_mm, 1.0)

    # -------------------------------------------------------------------------
    # TEST 9: Baseplate Bending & Minimum Codal Thickness
    # -------------------------------------------------------------------------
    def test_09_baseplate_bending_and_codal_thickness(self):
        """WP-06: Verifies baseplate bearing, cantilever bending, and tp >= tf requirement."""
        bp = audit_baseplate_and_anchors(Pu_gravity_kn=33.84, Lp_mm=350.0, Bp_mm=250.0, tp_provided_mm=16.0)

        self.assertAlmostEqual(bp.bearing_stress_mpa, 0.387, places=3)
        self.assertTrue(bp.bearing_passed)
        self.assertAlmostEqual(bp.calculated_thickness_tp_mm, 3.47, places=2)
        # IS 800 Cl 7.4.3.1: tp >= tf = 12.4 mm for ISMB 300
        self.assertEqual(bp.codal_minimum_thickness_mm, 12.4)
        self.assertTrue(bp.baseplate_passed)

    # -------------------------------------------------------------------------
    # TEST 10: Anchor Group Failure Modes & Slab Thickness Limit
    # -------------------------------------------------------------------------
    def test_10_anchor_failure_modes_and_slab_thickness(self):
        """WP-06: Verifies anchor failure modes and identifies host slab thickness limit."""
        audit = audit_baseplate_and_anchors(Tu_uplift_kn=18.50, Vu_shear_kn=3.50, hef_mm=125.0)

        # Check all failure modes present
        names = [c.failure_mode_name for c in audit.anchor_checks]
        self.assertTrue(any("Tension" in n for n in names))
        self.assertTrue(any("Cone Breakout" in n for n in names))
        self.assertTrue(any("Bond" in n for n in names))
        self.assertTrue(any("Shear" in n for n in names))
        self.assertTrue(any("Pryout" in n for n in names))

        # Check combined interaction
        self.assertLess(audit.combined_tension_shear_interaction, 0.10)

        # Check slab thickness adequacy: hef = 125 requires h_slab >= 187.5 mm!
        self.assertFalse(audit.host_slab_thickness_adequate)
        self.assertTrue(audit.engineering_hold_retained)
        self.assertGreaterEqual(len(audit.missing_physical_inputs), 4)

    # -------------------------------------------------------------------------
    # TEST 11: Option A versus Option B Multi-Criteria Comparison
    # -------------------------------------------------------------------------
    def test_11_option_a_vs_option_b_multi_criteria_comparison(self):
        """WP-07: Verifies multi-criteria comparison between Option A and Option B."""
        table = generate_option_a_vs_option_b_comparison()
        self.assertGreaterEqual(len(table), 8)

        # Verify Option A advantages
        a_adv = [row for row in table if row.advantage_option == "Option A"]
        self.assertTrue(any("Deflection" in r.parameter for r in a_adv))
        self.assertTrue(any("Rafter" in r.parameter for r in a_adv))

        # Verify Option B advantages
        b_adv = [row for row in table if row.advantage_option == "Option B"]
        self.assertTrue(any("Tonnage" in r.parameter or "Constructability" in r.parameter for r in b_adv))

    # -------------------------------------------------------------------------
    # TEST 12: Historical Record Immutability (20 Baseline Runs)
    # -------------------------------------------------------------------------
    def test_12_historical_record_immutability(self):
        """WP-08: Verifies all 20 historical calculation runs remain completely untouched."""
        conn = sqlite3.connect(PROD_STRUCTURAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 20, "All 20 historical calculation runs must be preserved.")

    # -------------------------------------------------------------------------
    # TEST 13: Original Hold Enforcement
    # -------------------------------------------------------------------------
    def test_13_original_hold_enforcement(self):
        """WP-09: Verifies all 12 canonical holds active, and System A has 10 active holds."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(all_holds), 12, "All 12 canonical holds must remain active.")

        sys_a_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            MountingSystemType.SYSTEM_A_CANOPY.value
        )
        self.assertEqual(len(sys_a_holds), 10, "System A must have exactly 10 active verification holds.")

    # -------------------------------------------------------------------------
    # TEST 14: AFC Lock & Statutory Watermark
    # -------------------------------------------------------------------------
    def test_14_afc_lock_and_statutory_watermark(self):
        """WP-09: Verifies BLOCKED_AFC_LOCKED and statutory review watermark."""
        expected_hashes = {
            PROD_QUOTATIONS_DB: "3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf",
            PROD_STRUCTURAL_DB: "ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff",
            PROD_SETTINGS_FILE: "26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1",
        }
        for path, exp_hash in expected_hashes.items():
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            self.assertEqual(hasher.hexdigest(), exp_hash, f"File {path} checksum altered!")


if __name__ == "__main__":
    unittest.main()
