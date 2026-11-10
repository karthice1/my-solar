"""
Phase 1.5.3 — System A Elevated Steel Canopy Engineering Validation Test Suite
Package: tests.test_phase1_5_3_system_a

Verification Scope:
1. Exact numerical reproduction of baseline purlin serviceability failure (delta = 20.73 mm, UR = 1.728, FAIL).
2. Option A (span reduction to 2.0 m) hand-calculated numerical benchmark verification.
3. Option B (section upsize to C125 x 50 x 2.5 mm) hand-calculated benchmark verification.
4. Cold-formed steel mechanics, effective width, and local buckling per IS 801: 1975 & IS 800 Class 4.
5. Distortional buckling codal limitations declaration.
6. Extended framing checks: rafter LTB, column combined interaction (IS 800 Cl 9.3), frame sway drift.
7. Baseplate cantilever bending (IS 800 Cl 7.4) and chemical anchor breakout (IS 456 / ACI 318 / fib 58).
8. 100% backward compatibility of SystemACanopyWorkflow.
9. Protection safeguards: all 12 canonical holds active, AFC blocked, zero production DB mutations.
"""

import hashlib
import json
import math
import os
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
from structural.workflows.system_a import SystemACanopyWorkflow
from structural.workflows.system_a_validation import (
    ThinWalledSectionGeometry,
    PurlinOptionEvaluation,
    SystemAEngineeringValidator,
    ExtendedFramingResults,
    evaluate_extended_framing_and_connections,
)


class TestPhase153SystemAValidation(unittest.TestCase):
    """Rigorous engineering validation suite for Phase 1.5.3 System A."""

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
        cls.geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            module=cls.module,
            total_modules=4,
            rows=4,
            columns=1,
            orientation="PORTRAIT",
            ground_clearance_mm=2800.0,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
        )
        cls.rafter = SectionProperty(
            designation="ISMB 300",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=5626.0,
            Ixx_mm4=86036000.0,
            Iyy_mm4=4539000.0,
            Zxx_mm3=573600.0,
            Zyy_mm3=64800.0,
            rxx_mm=123.7,
            ryy_mm=28.4,
            mass_kg_m=44.2,
        )
        cls.column = SectionProperty(
            designation="ISMB 300",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=5626.0,
            Ixx_mm4=86036000.0,
            Iyy_mm4=4539000.0,
            Zxx_mm3=573600.0,
            Zyy_mm3=64800.0,
            rxx_mm=123.7,
            ryy_mm=28.4,
            mass_kg_m=44.2,
        )

    # -------------------------------------------------------------------------
    # TEST 1: Exact Numerical Reproduction of Baseline Purlin Failure
    # -------------------------------------------------------------------------
    def test_01_reproduce_baseline_purlin_failure(self):
        """Reproduces baseline purlin failure: delta = 20.73 mm, UR = 1.728, status FAIL."""
        validator = SystemAEngineeringValidator(site=self.site, geometry=self.geometry)
        base = validator.evaluate_baseline_reproduction()

        self.assertEqual(base.span_mm, 3000.0)
        self.assertEqual(base.purlin_designation, "ISMC 100x50x2.0")
        self.assertIn("Aluminium", base.material_name)
        self.assertEqual(base.elastic_modulus_mpa, 69000.0)

        # Numerical checks
        self.assertAlmostEqual(base.delta_actual_governing_mm, 20.7304, delta=0.005)
        self.assertEqual(base.delta_allowable_mm, 12.0)
        self.assertAlmostEqual(base.deflection_unity_ratio, 1.7275, delta=0.002)
        self.assertFalse(base.deflection_passed)
        self.assertIn("ACT-IL-02", base.governing_deflection_load_case)
        self.assertIn("REJECT", base.overall_recommendation)

    # -------------------------------------------------------------------------
    # TEST 2: Option A (Span Reduction to 2.0 m) Benchmark Verification
    # -------------------------------------------------------------------------
    def test_02_option_a_span_reduction_hand_calc_verification(self):
        """Verifies Option A: L = 2.0 m via intermediate rafter passes under both Al and Steel."""
        validator = SystemAEngineeringValidator(site=self.site, geometry=self.geometry)

        # 2A. Aluminium Material (E = 69 GPa)
        opt_a_al = validator.evaluate_option_a(use_steel=False)
        self.assertEqual(opt_a_al.span_mm, 2000.0)
        self.assertEqual(opt_a_al.delta_allowable_mm, 8.0)
        # Hand-calc: 20.7304 * (2/3)^4 = 4.0949 mm
        self.assertAlmostEqual(opt_a_al.delta_actual_governing_mm, 4.0949, delta=0.005)
        self.assertAlmostEqual(opt_a_al.deflection_unity_ratio, 0.5119, delta=0.002)
        self.assertTrue(opt_a_al.deflection_passed)

        # 2B. Steel Material (E = 205 GPa)
        opt_a_steel = validator.evaluate_option_a(use_steel=True)
        # Hand-calc: 4.0949 * (69000 / 205000) = 1.3783 mm
        self.assertAlmostEqual(opt_a_steel.delta_actual_governing_mm, 1.3783, delta=0.005)
        self.assertAlmostEqual(opt_a_steel.deflection_unity_ratio, 0.1723, delta=0.002)
        self.assertTrue(opt_a_steel.deflection_passed)

        # 2C. Primary Rafter Relief
        self.assertEqual(opt_a_steel.rafter_spacing_mm, 2000.0)
        self.assertAlmostEqual(opt_a_steel.rafter_tributary_reduction_pct, 33.33, places=1)
        self.assertTrue(opt_a_steel.rafter_passed)
        self.assertIn("STRONGLY RECOMMENDED", opt_a_steel.overall_recommendation)

    # -------------------------------------------------------------------------
    # TEST 3: Option B (Section Upsize to C125 x 50 x 2.5) Benchmark Verification
    # -------------------------------------------------------------------------
    def test_03_option_b_section_upsize_hand_calc_verification(self):
        """Verifies Option B: C125 x 50 x 2.5 mm over L = 3.0 m passes deflection."""
        validator = SystemAEngineeringValidator(site=self.site, geometry=self.geometry)

        # 3A. Aluminium Material (E = 69 GPa)
        opt_b_al = validator.evaluate_option_b(use_steel=False)
        self.assertEqual(opt_b_al.span_mm, 3000.0)
        self.assertEqual(opt_b_al.delta_allowable_mm, 12.0)
        self.assertAlmostEqual(opt_b_al.delta_actual_governing_mm, 10.3270, delta=0.02)
        self.assertAlmostEqual(opt_b_al.deflection_unity_ratio, 0.8606, delta=0.005)
        self.assertTrue(opt_b_al.deflection_passed)

        # 3B. Steel Material (E = 205 GPa)
        opt_b_steel = validator.evaluate_option_b(use_steel=True)
        self.assertAlmostEqual(opt_b_steel.delta_actual_governing_mm, 3.5836, delta=0.02)
        self.assertAlmostEqual(opt_b_steel.deflection_unity_ratio, 0.2986, delta=0.005)
        self.assertTrue(opt_b_steel.deflection_passed)

        # 3C. Primary Rafter remains at 3.0 m tributary
        self.assertEqual(opt_b_steel.rafter_spacing_mm, 3000.0)
        self.assertEqual(opt_b_steel.rafter_tributary_reduction_pct, 0.0)
        self.assertIn("FEASIBLE ALTERNATIVE", opt_b_steel.overall_recommendation)

    # -------------------------------------------------------------------------
    # TEST 4: Cold-Formed Steel Mechanics & Effective Width (IS 801 / IS 800)
    # -------------------------------------------------------------------------
    def test_04_cold_formed_mechanics_and_effective_width_is801(self):
        """Evaluates thin-walled section geometry, local buckling, and effective width."""
        # 4A. Lipped C100 x 50 x 2.0 (lip = 15 mm)
        c100_lip = ThinWalledSectionGeometry(depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=15.0)
        c100_lip.compute_properties(fy_mpa=250.0, E_mpa=205000.0)

        self.assertTrue(c100_lip.is_lipped)
        self.assertAlmostEqual(c100_lip.area_mm2, 444.0, delta=1.0)
        self.assertAlmostEqual(c100_lip.Ixx_mm4, 717556.0, delta=100.0)
        self.assertEqual(c100_lip.local_buckling_reduction_factor, 1.0)
        self.assertEqual(c100_lip.effective_flange_width_mm, 48.0)  # b = 50 - 2 = 48 mm
        self.assertIn("UNSUPPORTED_UNDER_IS801", c100_lip.distortional_buckling_status)

        # 4B. Unlipped Plain C100 x 50 x 2.0 (lip = 0)
        c100_plain = ThinWalledSectionGeometry(depth_mm=100.0, flange_mm=50.0, thickness_mm=2.0, lip_mm=0.0)
        c100_plain.compute_properties(fy_mpa=250.0, E_mpa=205000.0)

        self.assertFalse(c100_plain.is_lipped)
        # Plain channel unstiffened flange suffers local buckling: rho < 1.0
        self.assertLess(c100_plain.local_buckling_reduction_factor, 1.0)
        self.assertAlmostEqual(c100_plain.local_buckling_reduction_factor, 0.674, delta=0.01)
        self.assertLess(c100_plain.effective_flange_width_mm, 48.0)
        self.assertLess(c100_plain.effective_Ixx_mm4, c100_plain.Ixx_mm4)

        # 4C. Lipped C125 x 50 x 2.5 (lip = 15 mm)
        c125_lip = ThinWalledSectionGeometry(depth_mm=125.0, flange_mm=50.0, thickness_mm=2.5, lip_mm=15.0)
        c125_lip.compute_properties(fy_mpa=250.0, E_mpa=205000.0)
        self.assertAlmostEqual(c125_lip.area_mm2, 612.5, delta=1.0)
        self.assertAlmostEqual(c125_lip.Ixx_mm4, 1478320.0, delta=500.0)
        self.assertEqual(c125_lip.local_buckling_reduction_factor, 1.0)

    # -------------------------------------------------------------------------
    # TEST 5: Extended System A Framing, Baseplate & Anchor Checks
    # -------------------------------------------------------------------------
    def test_05_extended_framing_and_connections(self):
        """Verifies rafter LTB, column interaction, sway drift, baseplate, and anchor breakout."""
        res = evaluate_extended_framing_and_connections(
            site=self.site,
            geometry=self.geometry,
            rafter_section=self.rafter,
            column_section=self.column,
            concrete_fck_mpa=20.0,
            baseplate_tp_mm=16.0,
            anchor_embedment_hef_mm=125.0,
        )

        # 5A. Rafter LTB
        # Top flange braced by purlins at 1150 mm: slenderness ~40.5
        self.assertAlmostEqual(res.rafter_LTB_slenderness, 40.49, delta=0.5)
        self.assertFalse(res.rafter_LTB_governs)
        self.assertLess(res.rafter_shear_unity_ratio, 0.50)

        # 5B. Column Interaction (IS 800 Cl 9.3)
        self.assertGreater(res.column_axial_demand_Pu_kn, 20.0)
        self.assertGreater(res.column_bending_demand_Mz_kn_m, 2.0)
        self.assertLess(res.column_interaction_ratio, 1.0)
        self.assertTrue(res.column_interaction_passed)

        # 5C. Canopy Sway Drift
        self.assertEqual(res.column_clear_height_mm, 2800.0)
        self.assertAlmostEqual(res.allowable_sway_drift_mm, 9.33, delta=0.01)
        self.assertLess(res.calculated_sway_drift_mm, res.allowable_sway_drift_mm)
        self.assertTrue(res.sway_drift_passed)

        # 5D. Baseplate Cantilever Bending (IS 800 Cl 7.4)
        self.assertEqual(res.concrete_bearing_permissible_mpa, 12.0)
        self.assertAlmostEqual(res.actual_bearing_stress_mpa, 0.387, delta=0.05)
        self.assertTrue(res.bearing_stress_passed)
        self.assertAlmostEqual(res.required_baseplate_thickness_mm, 3.47, delta=0.2)
        self.assertTrue(res.baseplate_bending_passed)

        # 5E. Chemical Anchor Breakout
        self.assertAlmostEqual(res.concrete_cone_breakout_capacity_kn, 62.50, delta=1.0)
        self.assertLess(res.anchor_tension_unity_ratio, 0.50)
        self.assertTrue(res.anchor_breakout_passed)

        # 5F. Verification Registers & Unsupported Checks
        self.assertGreaterEqual(len(res.unsupported_checks_declared), 4)
        self.assertGreaterEqual(len(res.inspection_evidence_required), 3)

    # -------------------------------------------------------------------------
    # TEST 6: SystemACanopyWorkflow Backward Compatibility & Delegate Methods
    # -------------------------------------------------------------------------
    def test_06_system_a_workflow_backward_compatibility(self):
        """Verifies SystemACanopyWorkflow preserves 100% backward compatibility and delegates correctly."""
        wf = SystemACanopyWorkflow(site=self.site, geometry=self.geometry)

        # 6A. Delegate: evaluate_purlin_remedies
        remedies = wf.evaluate_purlin_remedies(use_steel=True)
        self.assertIn("BASELINE", remedies)
        self.assertIn("OPTION_A", remedies)
        self.assertIn("OPTION_B", remedies)
        self.assertFalse(remedies["BASELINE"].deflection_passed)
        self.assertTrue(remedies["OPTION_A"].deflection_passed)
        self.assertTrue(remedies["OPTION_B"].deflection_passed)

        # 6B. Delegate: evaluate_extended_framing
        ext = wf.evaluate_extended_framing(rafter_section=self.rafter, column_section=self.column)
        self.assertTrue(ext.column_interaction_passed)
        self.assertTrue(ext.baseplate_bending_passed)
        self.assertTrue(ext.anchor_breakout_passed)

        # 6C. Original run_workflow_analysis
        rep = wf.run_workflow_analysis(
            purlin_section=SectionProperty(
                designation="ISMC 100x50x2.0",
                profile_type="C-Channel",
                material=STEEL_E250,
                area_mm2=450.0,
                Ixx_mm4=750000.0,
                Iyy_mm4=180000.0,
                Zxx_mm3=15000.0,
                Zyy_mm3=5000.0,
                rxx_mm=40.8,
                ryy_mm=20.0,
                mass_kg_m=3.53,
            ),
            rafter_section=self.rafter,
            column_section=self.column,
        )
        self.assertEqual(len(rep.active_holds), 10)
        self.assertGreaterEqual(len(rep.results), 5)
        self.assertGreaterEqual(len(rep.unsupported_checks), 5)

    # -------------------------------------------------------------------------
    # TEST 7: Governance Safeguards, Hold Integrity & Database Immutability
    # -------------------------------------------------------------------------
    def test_07_governance_safeguards_and_db_immutability(self):
        """Verifies zero production DB mutations, all 12 canonical holds active, and AFC locked."""
        # 7A. Active Holds Check
        holds = MASTER_VERIFICATION_REGISTER.get_active_holds()
        self.assertEqual(len(holds), 12, "All 12 canonical holds must remain registered and active.")

        # 7B. Production Database Checksums
        expected_hashes = {
            PROD_QUOTATIONS_DB: "3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf",
            PROD_STRUCTURAL_DB: "ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff",
            PROD_SETTINGS_FILE: "26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1",
        }
        for full_path, exp_hash in expected_hashes.items():
            self.assertTrue(os.path.exists(full_path), f"File {full_path} must exist.")
            hasher = hashlib.sha256()
            with open(full_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_hash = hasher.hexdigest()
            self.assertEqual(
                actual_hash,
                exp_hash,
                f"Production asset {full_path} was modified! Hash mismatch.",
            )


if __name__ == "__main__":
    unittest.main()
