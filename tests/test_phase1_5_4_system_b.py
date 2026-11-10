"""
Phase 1.5.4 — System B: Low-Height Aluminium Rail Engineering Validation Test Suite
Package: tests.test_phase1_5_4_system_b

Covers all 15 Independent Engineering Verifications for Phase 1.5.4:
1. Aluminium material register: verifies 6063-T6, 6005A-T6, and 6082-T6 properties per IS 733 / IS 8147 / EN 1999.
2. Material provenance & MTC requirement: rejects assumed properties without certified EN 10204 Type 3.1 MTC.
3. Extruded section properties: validates gross area, Ixx, Iyy, Zxx, and rxx for STD_40x40 and HEAVY_40x60.
4. Thin-walled plate slenderness: evaluates element classification (Class 1-3 vs Class 4 local buckling reduction).
5. Member flexural capacity: compares gross (Md,gross) vs effective (Md,eff) capacity under ULS-01 and ULS-02.
6. Serviceability deflection: verifies SLS deflection delta <= L/200 and module cell micro-crack safety limit.
7. Shear capacity & interaction: checks VRd and confirms Vu <= 0.5 VRd prevents interaction penalty.
8. HAZ strength reduction: evaluates precipitate dissolution, 56% strength loss, and mandatory 100% bolted rule.
9. Fastener tension vs slot lip pull-out: proves aluminium slot lip yielding (8.92 kN) governs over M8 bolt tension (18.45 kN).
10. Thermal expansion & joint sizing: verifies elongation Delta-L over 14 m and mandatory expansion joint at <= 12 m.
11. Bimetallic galvanic corrosion: flags 0.65 V potential difference and enforces EPDM isolating pads and anodization.
12. Complete load path verification: verifies 7 structural load transfer links and identifies remaining physical inputs.
13. Historical records immutability: verifies all 20 historical calculation runs remain completely untouched.
14. System B hold enforcement: verifies all 12 canonical holds active, exactly 11 applicable to System B.
15. AFC construction lock & watermark: verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark.
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
)
from structural.holds import MASTER_VERIFICATION_REGISTER
from structural.workflows.system_b_validation import (
    AluminiumMaterialSpecification,
    get_aluminium_material_register,
    AluminiumRailProfile,
    calculate_aluminium_rail_properties,
    AluminiumMemberBendingShearCheck,
    evaluate_aluminium_rail_member_strength,
    HAZSofteningEvaluation,
    evaluate_haz_strength_reduction,
    FastenerAndConnectionCheck,
    evaluate_system_b_connections,
    ThermalExpansionCheck,
    evaluate_thermal_expansion_and_joints,
    SystemBLoadPathStep,
    SystemBLoadPathReport,
    verify_system_b_complete_load_path,
)


class TestPhase154SystemBValidation(unittest.TestCase):
    """Rigorous engineering test suite for Phase 1.5.4 System B Aluminium Rail validation."""

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

    def test_01_aluminium_material_register(self):
        """WP-01: Verifies aluminium material specifications for 6063-T6, 6005A-T6, and 6082-T6."""
        reg = get_aluminium_material_register()
        self.assertEqual(len(reg), 3)
        self.assertIn("6063-T6", reg)
        self.assertIn("6005A-T6", reg)
        self.assertIn("6082-T6", reg)

        # 6063-T6 baseline
        m6063 = reg["6063-T6"]
        self.assertEqual(m6063.yield_strength_fo_mpa, 170.0)
        self.assertEqual(m6063.ultimate_strength_fu_mpa, 215.0)
        self.assertEqual(m6063.elastic_modulus_E_mpa, 69000.0)
        self.assertEqual(m6063.density_kg_m3, 2700.0)
        self.assertAlmostEqual(m6063.thermal_expansion_alpha, 2.3e-5)
        self.assertEqual(m6063.partial_safety_factor_gamma_m1, 1.10)

        # 6005A-T6 comparison (higher yield)
        m6005 = reg["6005A-T6"]
        self.assertEqual(m6005.yield_strength_fo_mpa, 215.0)
        self.assertGreater(m6005.yield_strength_fo_mpa, m6063.yield_strength_fo_mpa)

        # 6082-T6 comparison (highest structural yield)
        m6082 = reg["6082-T6"]
        self.assertEqual(m6082.yield_strength_fo_mpa, 260.0)
        self.assertEqual(m6082.ultimate_strength_fu_mpa, 310.0)

    def test_02_material_provenance_and_mtc_requirement(self):
        """WP-01: Verifies that material certificate (MTC Type 3.1) is explicitly required."""
        reg = get_aluminium_material_register()
        for alloy, spec in reg.items():
            self.assertIn("EN 10204 Type 3.1", spec.material_certificate_required)
            self.assertTrue(spec.suitable_for_solar_mounting)

    def test_03_extruded_rail_section_properties(self):
        """WP-02: Verifies gross geometric section properties for standard and heavy rail profiles."""
        std = calculate_aluminium_rail_properties("STD_40x40", "6063-T6")
        self.assertEqual(std.height_mm, 40.0)
        self.assertEqual(std.width_mm, 40.0)
        self.assertEqual(std.gross_area_mm2, 328.0)
        self.assertEqual(std.mass_kg_m, 0.89)
        self.assertEqual(std.Ixx_gross_mm4, 64500.0)
        self.assertEqual(std.Zxx_gross_mm3, 3225.0)

        heavy = calculate_aluminium_rail_properties("HEAVY_40x60", "6063-T6")
        self.assertEqual(heavy.height_mm, 60.0)
        self.assertEqual(heavy.gross_area_mm2, 492.0)
        self.assertEqual(heavy.Ixx_gross_mm4, 194500.0)
        self.assertEqual(heavy.Zxx_gross_mm3, 6483.0)
        self.assertGreater(heavy.Ixx_gross_mm4, std.Ixx_gross_mm4)

    def test_04_thin_walled_plate_slenderness_and_effective_width(self):
        """WP-02: Verifies element classification and effective section modulus reduction."""
        profile = calculate_aluminium_rail_properties("STD_40x40", "6063-T6")
        self.assertIn("Class", profile.section_classification)
        # Verify effective section properties are populated
        self.assertGreater(profile.effective_area_Aeff_mm2, 0.0)
        self.assertLessEqual(profile.effective_area_Aeff_mm2, profile.gross_area_mm2)
        self.assertLessEqual(profile.effective_Zxx_mm3, profile.Zxx_gross_mm3)
        self.assertGreaterEqual(profile.effective_reduction_rho_c, 0.5)

    def test_05_member_flexural_capacity_gross_vs_effective(self):
        """WP-03: Evaluates design bending resistance using effective section properties."""
        check = evaluate_aluminium_rail_member_strength(bracket_span_mm=1400.0)
        # Gross capacity = Zxx * fo / gamma_m1 = 3225 * 170 / (1.10 * 1e6) = 0.498 kNm
        self.assertAlmostEqual(check.design_moment_capacity_gross_kn_m, 0.498, delta=0.02)
        # Effective capacity <= gross capacity
        self.assertLessEqual(check.design_moment_capacity_effective_kn_m, check.design_moment_capacity_gross_kn_m)
        self.assertTrue(check.bending_passed)
        self.assertLess(check.bending_unity_ratio, 0.70)

    def test_06_serviceability_deflection_and_pv_cell_protection(self):
        """WP-03: Verifies rail deflection under SLS loads clears L/200 and 12 mm cell crack limit."""
        check = evaluate_aluminium_rail_member_strength(bracket_span_mm=1400.0)
        # Allowable: L / 200 = 1400 / 200 = 7.00 mm
        self.assertEqual(check.allowable_deflection_mm, 7.00)
        # Actual deflection: 5.57 mm <= 7.00 mm
        self.assertAlmostEqual(check.actual_deflection_mm, 5.57, delta=0.2)
        self.assertLess(check.actual_deflection_mm, check.allowable_deflection_mm)
        self.assertTrue(check.deflection_passed)
        self.assertTrue(check.pv_cell_microcrack_safe)

    def test_07_shear_capacity_and_interaction(self):
        """WP-03: Verifies shear capacity VRd and confirms Vu <= 0.5 VRd prevents interaction penalty."""
        check = evaluate_aluminium_rail_member_strength(bracket_span_mm=1400.0)
        # Two webs: Av = 2 * 40 * 2.0 = 160 mm2 -> Vd = 160 * (170 / sqrt(3)) / 1.10 = 14.28 kN
        self.assertAlmostEqual(check.design_shear_capacity_Vd_kn, 14.28, delta=0.5)
        # Demand Vu is ~0.71 kN -> UR = 0.71 / 14.28 = 0.05
        self.assertLess(check.shear_unity_ratio, 0.10)
        self.assertTrue(check.shear_passed)
        # Because Vu << 0.5 Vd, interaction ratio equals flexural unity ratio
        self.assertEqual(check.shear_bending_interaction_ratio, check.bending_unity_ratio)

    def test_08_haz_softening_and_mandatory_bolting_rule(self):
        """WP-04: Verifies HAZ precipitate softening, 56% yield loss, and mandatory 100% bolting rule."""
        haz = evaluate_haz_strength_reduction("6063-T6")
        self.assertEqual(haz.parent_metal_yield_fo_mpa, 170.0)
        self.assertEqual(haz.haz_reduction_factor_rho_haz, 0.44)
        # HAZ yield: 170 * 0.44 = 74.8 MPa (~75 MPa)
        self.assertAlmostEqual(haz.haz_yield_strength_fo_haz_mpa, 74.8, delta=0.5)
        self.assertAlmostEqual(haz.strength_loss_percentage, 56.0, delta=0.5)
        self.assertFalse(haz.is_welded_construction_recommended)
        self.assertIn("100% BOLTED", haz.mandatory_solar_connection_method)

    def test_09_fastener_tension_vs_slot_lip_pull_out(self):
        """WP-05: Proves rail slot lip yielding (8.92 kN) governs over M8 bolt tension (18.45 kN)."""
        conn = evaluate_system_b_connections(bolt_dia_mm=8.0, lip_thickness_mm=2.5)
        # Stainless Steel A2-70 M8 tensile capacity: 18.45 kN
        self.assertAlmostEqual(conn.bolt_tensile_capacity_Ft_kn, 18.45, delta=0.2)
        # Slot lip pull-out capacity: 2 * (20 * 2.5 * 170 / sqrt(3)) / 1.10 = 8.92 kN
        self.assertAlmostEqual(conn.slot_lip_pull_out_capacity_Plip_kn, 8.92, delta=0.2)
        # Lip capacity < Bolt capacity -> Lip yielding governs!
        self.assertLess(conn.slot_lip_pull_out_capacity_Plip_kn, conn.bolt_tensile_capacity_Ft_kn)
        self.assertEqual(conn.governing_connection_capacity_kn, conn.slot_lip_pull_out_capacity_Plip_kn)
        self.assertIn("SLOT LIP", conn.governing_failure_mode)
        self.assertTrue(conn.connection_passed)
        self.assertEqual(conn.recommended_tightening_torque_nm, 14.0)

    def test_10_thermal_expansion_and_joint_sizing(self):
        """WP-05: Verifies thermal expansion and mandatory expansion joint gap at length > 12 m."""
        therm = evaluate_thermal_expansion_and_joints(continuous_length_m=14.0, T_min_C=15.0, T_max_C=75.0)
        # Delta-T = 60 C
        self.assertEqual(therm.temperature_differential_delta_T_C, 60.0)
        # Elongation = 23e-6 * 14000 * 60 = 19.32 mm
        self.assertAlmostEqual(therm.thermal_elongation_delta_L_mm, 19.32, delta=0.1)
        self.assertTrue(therm.expansion_joint_required)
        self.assertGreaterEqual(therm.expansion_joint_gap_required_mm, 20.0)

        # Length <= 12 m does not mandate expansion joint
        therm_short = evaluate_thermal_expansion_and_joints(continuous_length_m=10.0)
        self.assertFalse(therm_short.expansion_joint_required)

    def test_11_bimetallic_galvanic_corrosion_mitigation(self):
        """WP-05: Verifies galvanic risk between SS and Al and enforces EPDM isolating washers."""
        conn = evaluate_system_b_connections()
        self.assertIn("HIGH", conn.bimetallic_galvanic_risk)
        self.assertIn("EPDM", conn.isolation_requirement)
        self.assertIn("anodization", conn.isolation_requirement)

    def test_12_complete_system_b_load_path(self):
        """WP-06: Verifies complete 7-step load path and identifies unverified physical items."""
        lp = verify_system_b_complete_load_path()
        self.assertEqual(lp.total_steps, 7)
        self.assertTrue(lp.load_path_continuous)
        self.assertLessEqual(lp.governing_unity_ratio, 1.0)
        self.assertIn("Aluminium Rail", lp.governing_component)
        # Must list remaining unverified manufacturer/physical items
        self.assertGreaterEqual(len(lp.remaining_unverified_items), 4)

    def test_13_historical_runs_immutability(self):
        """WP-08: Verifies that all 20 historical calculation runs remain completely untouched."""
        conn = sqlite3.connect(PROD_STRUCTURAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 20, "All 20 historical runs must be preserved bit-for-bit.")

    def test_14_system_b_canonical_holds_enforcement(self):
        """WP-08: Verifies all 12 canonical holds active, and exactly 11 active for System B."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(all_holds), 12, "All 12 canonical holds must exist")

        sys_b_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL.value
        )
        self.assertEqual(len(sys_b_holds), 11, "System B must have exactly 11 active verification holds")

        hold_ids = [h.hold_id for h in sys_b_holds]
        self.assertIn("ALUMINIUM_DERIVATION_HOLD", hold_ids)
        self.assertIn("FASTENER_TORQUE_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("INSPECTION_REQUIRED_HOLD", hold_ids)
        self.assertNotIn("FRICTION_UNVERIFIED_HOLD", hold_ids)  # Only for System D

    def test_15_afc_construction_lock_and_watermark(self):
        """WP-08: Verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark are enforced."""
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
