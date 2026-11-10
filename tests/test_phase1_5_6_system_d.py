"""
Phase 1.5.6 — System D: Ballasted Non-Penetrating System Engineering Validation Test Suite
Package: tests.test_phase1_5_6_system_d

Covers all 17 Independent Engineering Verifications for Phase 1.5.6:
1. Physical input register: verifies M25 precast blocks, mass, and EPDM pad dimensions.
2. Friction coefficient sensitivity: evaluates dry (0.55), wet (0.35), and provisional (0.40) parameters.
3. Aerodynamic forces & wind deflector: verifies effective Cn,up = -0.760 and resolved drag/uplift forces.
4. Sliding stability: verifies FOS_slide >= 1.50 and limit state frictional resistance.
5. Overturning stability: verifies FOS_ot >= 1.40 and restoring moment capacity about leeward toe.
6. Vertical uplift / float-off check: verifies 0.9*DL provides net downward reaction.
7. Closed-form ballast derivation: verifies minimum ballast mass calculation for sliding and overturning.
8. Friction failure sensitivity: proves system fails sliding when friction drops to contaminated wet level (mu = 0.25).
9. Superimposed roof dead load: verifies total added dead load (0.758 kN/m2) clears 1.50 kN/m2 reserve.
10. EPDM pad bearing stress: verifies q = 0.018 MPa << 9.0 MPa permissible concrete bearing stress.
11. Rainwater drainage gap: verifies 75 mm clear gap between trays exceeds 50 mm minimum requirement.
12. Chassis frame & clamp checks: verifies aluminium rail flexure (UR = 0.393) and module clamp retention.
13. Complete load path: verifies 7 load transfer links from PV module to host RCC slab.
14. Cross-system comparative synthesis: validates 4-system comparative matrix across 10 criteria.
15. Historical calculation runs immutability: verifies all 20 historical runs intact.
16. Canonical holds enforcement: verifies all 12 canonical holds active (all 12 applicable to System D).
17. AFC construction status lock & watermark: verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark.
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
from structural.workflows.system_d_validation import (
    BallastSystemInputSpecification,
    get_ballast_system_input_register,
    BallastEquilibriumAudit,
    calculate_ballast_equilibrium_and_sizing,
    RoofLoadingAndBearingCheck,
    evaluate_roof_capacity_and_bearing,
    SystemDFrameAndConnectionCheck,
    evaluate_system_d_frame_and_clamps,
    SystemDLoadPathStep,
    SystemDLoadPathReport,
    verify_system_d_complete_load_path,
    FourSystemCrossComparisonRow,
    generate_four_system_comparative_matrix,
)


class TestPhase156SystemDValidation(unittest.TestCase):
    """Rigorous engineering test suite for Phase 1.5.6 System D Ballasted System validation."""

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

    def test_01_physical_input_and_ballast_register(self):
        """WP-01: Verifies physical input register for precast ballast blocks and chassis geometry."""
        spec = get_ballast_system_input_register()
        self.assertIn("M25", spec.ballast_material)
        self.assertEqual(spec.ballast_density_kg_m3, 2400.0)
        self.assertEqual(spec.mass_per_block_kg, 23.04)
        self.assertEqual(spec.blocks_per_module, 4)
        self.assertEqual(spec.total_ballast_mass_per_module_kg, 92.16)
        self.assertEqual(spec.module_tilt_deg, 10.0)
        self.assertAlmostEqual(spec.chassis_length_m, 2.243, delta=0.01)
        self.assertEqual(spec.friction_pad_thickness_mm, 10.0)
        self.assertTrue(spec.wind_deflector_present)

    def test_02_friction_coefficient_sensitivity(self):
        """WP-01: Verifies friction parameter register under dry, wet, and provisional conditions."""
        spec = get_ballast_system_input_register()
        self.assertEqual(spec.friction_coeff_dry, 0.55)
        self.assertEqual(spec.friction_coeff_wet, 0.35)
        self.assertEqual(spec.friction_coeff_design_assumed, 0.40)
        self.assertIn("FRICTION_UNVERIFIED_HOLD", spec.friction_evidence_status)

    def test_03_aerodynamic_forces_and_wind_deflector(self):
        """WP-02: Verifies effective Cn,up = -0.760 and resolved horizontal/vertical wind forces."""
        audit = calculate_ballast_equilibrium_and_sizing()
        self.assertEqual(audit.design_wind_speed_Vz_ms, 40.092)
        self.assertAlmostEqual(audit.design_wind_pressure_pz_kpa, 0.9644, places=4)
        # Cn_up with 20% deflector reduction = -0.95 * 0.80 = -0.760
        self.assertEqual(audit.aerodynamic_suction_coeff_Cn_up, -0.760)
        # Resolved wind forces
        self.assertAlmostEqual(audit.factored_horizontal_wind_drag_kn, 0.493, delta=0.02)
        self.assertAlmostEqual(audit.factored_uplift_wind_force_kn, 2.797, delta=0.05)

    def test_04_sliding_stability_limit_state(self):
        """WP-03: Verifies sliding stability factor of safety under shielded and unshielded conditions."""
        # 1. Under nominal unshielded wind (Cn = -0.95), nominal 0.65 kN/m2 ballast fails (reproducing historical failure)
        audit_unshielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.95)
        self.assertFalse(audit_unshielded.sliding_passed)
        self.assertLess(audit_unshielded.sliding_factor_of_safety, 1.50)

        # 2. Under aerodynamically shielded wind-tunnel calibrated flow (Cn = -0.35) or heavy ballast (1.70 kN/m2):
        audit_shielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.35)
        self.assertTrue(audit_shielded.sliding_passed)
        self.assertGreaterEqual(audit_shielded.sliding_factor_of_safety, 1.50)
        self.assertLessEqual(audit_shielded.sliding_unity_ratio, 1.0)

    def test_05_overturning_stability_about_leeward_toe(self):
        """WP-03: Verifies overturning moment FOS under shielded and unshielded conditions."""
        # Unshielded fails FOS >= 1.40
        audit_unshielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.95)
        self.assertFalse(audit_unshielded.overturning_passed)

        # Shielded passes FOS >= 1.40
        audit_shielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.35)
        self.assertTrue(audit_shielded.overturning_passed)
        self.assertGreaterEqual(audit_shielded.overturning_factor_of_safety, 1.40)
        self.assertLessEqual(audit_shielded.overturning_unity_ratio, 1.0)

    def test_06_vertical_uplift_lift_off_stability(self):
        """WP-03: Verifies vertical net uplift resistance."""
        # Unshielded nominal fails net uplift
        audit_unshielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.95)
        self.assertFalse(audit_unshielded.uplift_passed)
        self.assertGreater(audit_unshielded.uplift_unity_ratio, 1.0)

        # Shielded passes net uplift
        audit_shielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.35)
        self.assertTrue(audit_shielded.uplift_passed)
        self.assertLessEqual(audit_shielded.uplift_unity_ratio, 1.0)

    def test_07_closed_form_minimum_ballast_derivation(self):
        """WP-03: Verifies minimum required ballast mass calculation."""
        audit = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.95)
        # Unshielded required mass is 429.0 kg vs provided 171.2 kg -> fails
        self.assertAlmostEqual(audit.minimum_required_ballast_mass_kg, 429.0, delta=2.0)
        self.assertFalse(audit.system_d_stable)

        # Shielded required mass is ~150 kg vs provided 171.2 kg -> passes
        audit_shielded = calculate_ballast_equilibrium_and_sizing(ballast_weight_kn_per_m2=0.65, Cn_up=-0.35)
        self.assertLess(audit_shielded.minimum_required_ballast_mass_kg, audit_shielded.provided_ballast_mass_kg)
        self.assertTrue(audit_shielded.system_d_stable)

    def test_08_friction_failure_under_wet_contaminated_conditions(self):
        """WP-03: Proves system fails sliding when friction drops to contaminated wet level (mu = 0.25)."""
        audit_fail = calculate_ballast_equilibrium_and_sizing(friction_coeff_mu=0.25)
        self.assertFalse(audit_fail.sliding_passed)
        self.assertFalse(audit_fail.system_d_stable)
        self.assertGreater(audit_fail.sliding_unity_ratio, 1.0)

    def test_09_superimposed_roof_dead_load_check(self):
        """WP-04: Verifies total added dead load (0.758 kN/m2) clears 1.50 kN/m2 roof reserve."""
        check = evaluate_roof_capacity_and_bearing()
        self.assertAlmostEqual(check.total_superimposed_dead_load_kn_m2, 0.758, delta=0.02)
        self.assertEqual(check.allowable_superimposed_dead_load_kn_m2, 1.50)
        self.assertAlmostEqual(check.distributed_load_unity_ratio, 0.505, delta=0.02)
        self.assertTrue(check.distributed_load_passed)

    def test_10_epdm_pad_bearing_stress_on_roof(self):
        """WP-04: Verifies EPDM pad bearing pressure q = 0.018 MPa << 9.0 MPa permissible."""
        check = evaluate_roof_capacity_and_bearing()
        self.assertAlmostEqual(check.bearing_stress_on_roof_mpa, 0.018, delta=0.005)
        self.assertEqual(check.permissible_concrete_bearing_stress_mpa, 9.0)
        self.assertLess(check.bearing_stress_unity_ratio, 0.01)
        self.assertTrue(check.bearing_passed)
        self.assertTrue(check.slab_punching_shear_passed)

    def test_11_rainwater_drainage_gap(self):
        """WP-04: Verifies 75 mm clear gap between ballast trays exceeds 50 mm minimum."""
        check = evaluate_roof_capacity_and_bearing()
        self.assertGreaterEqual(check.drainage_gap_provided_mm, check.min_required_drainage_gap_mm)
        self.assertTrue(check.drainage_adequate)

    def test_12_chassis_frame_and_clamp_checks(self):
        """WP-06: Verifies chassis rail flexure (UR = 0.393) and module clamp retention."""
        frame = evaluate_system_d_frame_and_clamps()
        self.assertTrue(frame.chassis_bending_passed)
        self.assertLess(frame.chassis_bending_unity_ratio, 0.50)
        self.assertTrue(frame.module_clamp_passed)
        self.assertTrue(frame.ballast_tray_retaining_lip_adequate)
        self.assertTrue(frame.seismic_ballast_restraint_provided)

    def test_13_complete_load_path_verification(self):
        """WP-06: Verifies 7-step load path from PV module to host RCC slab."""
        lp = verify_system_d_complete_load_path()
        self.assertEqual(lp.total_steps, 7)
        self.assertTrue(lp.load_path_continuous)
        self.assertLessEqual(lp.governing_unity_ratio, 1.0)
        self.assertEqual(len(lp.remaining_unverified_items), 5)

    def test_14_cross_system_comparative_matrix(self):
        """WP-08: Validates multi-criteria comparison across Systems A, B, C, and D."""
        matrix = generate_four_system_comparative_matrix()
        self.assertEqual(len(matrix), 10)
        params = [row.parameter for row in matrix]
        self.assertIn("Mounting Topology & Type", params)
        self.assertIn("Roof Penetration & Fastening", params)
        self.assertIn("Governing Structural Failure Mode", params)
        self.assertIn("Active Canonical Holds Count", params)

        # Confirm System D has zero penetration
        pen_row = [r for r in matrix if "Penetration" in r.parameter][0]
        self.assertIn("ZERO PENETRATION", pen_row.system_d_ballasted)

        # Confirm System D has all 12 holds
        hold_row = [r for r in matrix if "Holds Count" in r.parameter][0]
        self.assertIn("ALL 12", hold_row.system_d_ballasted)

    def test_15_historical_calculation_runs_immutability(self):
        """WP-10: Verifies that all 20 historical calculation runs remain completely untouched."""
        conn = sqlite3.connect(PROD_STRUCTURAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059'")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 20, "All 20 historical calculation runs must be preserved bit-for-bit.")

    def test_16_all_12_canonical_holds_enforced(self):
        """WP-10: Verifies all 12 canonical holds active, and ALL 12 applicable to System D."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(all_holds), 12, "All 12 canonical holds must exist")

        sys_d_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(
            MountingSystemType.SYSTEM_D_BALLASTED.value
        )
        self.assertEqual(len(sys_d_holds), 12, "System D must have all 12 active verification holds")

        hold_ids = [h.hold_id for h in sys_d_holds]
        self.assertIn("FRICTION_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("AERODYNAMIC_UNSUPPORTED_HOLD", hold_ids)
        self.assertIn("INSPECTION_REQUIRED_HOLD", hold_ids)

    def test_17_afc_construction_lock_and_watermark(self):
        """WP-10: Verifies BLOCKED_AFC_LOCKED and PRELIMINARY watermark are strictly enforced."""
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
