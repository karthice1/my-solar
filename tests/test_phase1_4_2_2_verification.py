#!/usr/bin/env python3
"""
Phase 1.4.2.2 Independent Verification & Governance Test Suite
Package: tests.test_phase1_4_2_2_verification

Covers:
- WP-01: Deterministic hold applicability matching (rejects partial/prefix/suffix/unrelated) & provisional data enforcement.
- WP-02: Action register and load combination integrity and traceability.
- WP-03: Purlin serviceability deflection superposition (DL + distributed vs DL + point load).
- WP-04: System A primary frame limitations, concentric axial caveats, and unsupported checks.
- WP-05: System B aluminium rail gross section modulus caveats and ALUMINIUM_DERIVATION_HOLD.
- WP-06: System C metal sheet unverified provisional clamp capacity caveats.
- WP-07: System D ballasted assumed friction caveats and nominal slab screening allowance.
- WP-08: Input completeness truthfulness (PROVISIONAL / INCOMPLETE, never falsely COMPLETE).
- WP-09: API transaction rollback, orphan prevention, and 403 AFC deliverable gatekeeper.
- WP-10: Historical snapshot cryptographic hash stability and run count reconciliation.
- WP-11: DXF statutory caveats, schematic rail notes, and preliminary watermark.
"""

import os
import sys
import json
import math
import hashlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from structural.models import (
    MountingSystemType,
    TerrainCategory,
    SeismicZone,
    SiteParameters,
    PVModuleSpecification,
    ArrayGeometry,
    MaterialProperty,
    SectionProperty,
    CalculationResult,
    STEEL_E250,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.actions import (
    ActionRegister,
    CombinationGenerator,
    CANONICAL_ACTION_KEYS,
    LoadCombination,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldStatus,
    HoldRecord,
    resolve_system_token,
    CANONICAL_SYSTEM_TOKENS,
)
from structural.provenance import (
    ProvenanceLevel,
    ProvenanceTracker,
    ProvenanceRecord,
)
from structural.engine import (
    StructuralCalculationEngine,
    CalculationReport,
)
from structural.db import StructuralDatabase
from structural.integration import QuotationStructuralBridge
from structural.drawing import DXFDrawingEngine, DrawingClassification
from structural.workflows.system_a import SystemACanopyWorkflow
from structural.workflows.system_b import SystemBAluminiumRailWorkflow
from structural.workflows.system_c import SystemCMetalSheetWorkflow
from structural.workflows.system_d import SystemDBallastedWorkflow


class TestPhase1422Verification(unittest.TestCase):
    """Exhaustive test suite verifying Phase 1.4.2.2 corrections."""

    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db_file.name
        self.temp_db_file.close()
        self.db = StructuralDatabase(self.db_path)

        # Standard site setup
        self.site = SiteParameters(
            location_name="Salem Site",
            latitude=11.6643,
            longitude=78.1460,
            basic_wind_speed_vb=39.0,
            terrain_category=TerrainCategory.CATEGORY_2,
            topography_factor_k3=1.0,
            cyclonic_factor_k4=1.0,
            building_height_m=12.0,
            rooftop_elevation_m=15.0,
            seismic_zone=SeismicZone.ZONE_III,
            soil_type=2,
            importance_factor_I=1.0,
            response_reduction_R=4.0,
        )

        self.module = PVModuleSpecification(
            make_model="Bi-55-540 Wp",
            peak_power_w=540.0,
            length_mm=2278.0,
            width_mm=1134.0,
            thickness_mm=35.0,
            weight_kg=27.5,
            tilt_deg=10.0,
            azimuth_deg=180.0,
        )

        self.purlin_section = SectionProperty(
            designation="ISMC 100x50x2.0",
            profile_type="C-Channel",
            material=ALUMINIUM_6063_T6,
            area_mm2=450.0,
            mass_kg_m=3.53,
            Ixx_mm4=750000.0,
            Iyy_mm4=180000.0,
            Zxx_mm3=15000.0,
            Zyy_mm3=5000.0,
            rxx_mm=40.8,
            ryy_mm=20.0,
        )

        self.rafter_section = SectionProperty(
            designation="ISMB 300",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=5626.0,
            mass_kg_m=44.2,
            Ixx_mm4=86036000.0,
            Iyy_mm4=4539000.0,
            Zxx_mm3=573600.0,
            Zyy_mm3=64800.0,
            rxx_mm=123.7,
            ryy_mm=28.4,
        )

        self.column_section = SectionProperty(
            designation="ISMB 300",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=5626.0,
            mass_kg_m=44.2,
            Ixx_mm4=86036000.0,
            Iyy_mm4=4539000.0,
            Zxx_mm3=573600.0,
            Zyy_mm3=64800.0,
            rxx_mm=123.7,
            ryy_mm=28.4,
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    # -------------------------------------------------------------------------
    # WP-01: Hold Matching & Exact Applicability
    # -------------------------------------------------------------------------
    def test_wp01_deterministic_hold_applicability_matching(self):
        """Verifies exact token resolution and rejection of loose substring matches."""
        # 1. Positive exact matches
        self.assertEqual(resolve_system_token("System A"), "SYSTEM_A")
        self.assertEqual(resolve_system_token("A"), "SYSTEM_A")
        self.assertEqual(resolve_system_token("System A: Elevated Steel Canopy"), "SYSTEM_A")
        self.assertEqual(resolve_system_token("SYSTEM_A"), "SYSTEM_A")

        self.assertEqual(resolve_system_token("System B"), "SYSTEM_B")
        self.assertEqual(resolve_system_token("B"), "SYSTEM_B")
        self.assertEqual(resolve_system_token("System B: Low-Height Aluminium Rail"), "SYSTEM_B")

        self.assertEqual(resolve_system_token("System C"), "SYSTEM_C")
        self.assertEqual(resolve_system_token("C"), "SYSTEM_C")
        self.assertEqual(resolve_system_token("System C: Metal-Sheet Roof Mounting"), "SYSTEM_C")

        self.assertEqual(resolve_system_token("System D"), "SYSTEM_D")
        self.assertEqual(resolve_system_token("D"), "SYSTEM_D")
        self.assertEqual(resolve_system_token("System D: Ballasted Non-Penetrating System"), "SYSTEM_D")

        # 2. Negative partial, prefix, suffix, and unrelated matches
        self.assertIsNone(resolve_system_token("System"))
        self.assertIsNone(resolve_system_token("Sys"))
        self.assertIsNone(resolve_system_token("System AB"))
        self.assertIsNone(resolve_system_token("Canopy"))
        self.assertIsNone(resolve_system_token("A_extra"))
        self.assertIsNone(resolve_system_token("Steel Canopy"))
        self.assertIsNone(resolve_system_token("System X"))
        self.assertIsNone(resolve_system_token(""))
        self.assertIsNone(resolve_system_token("   "))
        self.assertIsNone(resolve_system_token(None))

        # 3. Test HoldRecord.applies_to deterministic behavior
        friction_hold = MASTER_VERIFICATION_REGISTER.get_hold("FRICTION_UNVERIFIED_HOLD")
        self.assertIsNotNone(friction_hold)
        self.assertTrue(friction_hold.applies_to("System D"))
        self.assertTrue(friction_hold.applies_to("D"))
        self.assertTrue(friction_hold.applies_to("System D: Ballasted Non-Penetrating System"))

        # Must reject other systems and invalid substrings
        self.assertFalse(friction_hold.applies_to("System A"))
        self.assertFalse(friction_hold.applies_to("System B"))
        self.assertFalse(friction_hold.applies_to("System C"))
        self.assertFalse(friction_hold.applies_to("System"))
        self.assertFalse(friction_hold.applies_to("D_extra"))
        self.assertFalse(friction_hold.applies_to("Ballasted"))

    def test_wp01_assumed_data_hold_provisional_enforcement(self):
        """
        Verifies automatic provisional data hold activation during normal lifecycle,
        database persistence, and survival across fresh connection reload.
        """
        pid = "PROV-HOLD-TEST"
        self.db.create_project(pid, "Prov Hold Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)
        geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=4,
            rows=4,
            columns=1,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geometry)
        self.db.set_section(pid, "PURLIN", self.purlin_section)
        self.db.set_section(pid, "RAFTER", self.rafter_section)
        self.db.set_section(pid, "COLUMN", self.column_section)

        # 1. Automatic hold activation upon recording Level 5 provisional parameter
        tracker = ProvenanceTracker(db=self.db, project_id=pid)
        tracker.record_parameter(
            parameter_key="purlin_yield_strength",
            value=250.0,
            units="MPa",
            level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            source_reference="Catalogue provisional default",
        )
        self.assertTrue(tracker.has_unverified_assumptions())
        self.assertTrue(tracker.requires_certification_hold())

        # Verify hold is automatically persisted in SQLite project_holds
        holds = self.db.get_project_holds(pid)
        assumed_hold = next((h for h in holds if h["hold_id"] == "ASSUMED_DATA_CERTIFICATION_HOLD"), None)
        self.assertIsNotNone(assumed_hold)
        self.assertEqual(assumed_hold["status"], HoldStatus.ACTIVE_ENFORCED.value)
        self.assertIn("purlin_yield_strength", assumed_hold["evidence_notes"])

        # 2. Execute calculation workflow without manually calling enforce_assumed_data_hold()
        run_res = self.db.execute_and_record_run(pid)
        self.assertIn("ASSUMED_DATA_CERTIFICATION_HOLD", run_res["active_holds"])
        self.assertEqual(run_res["input_completeness"], "PROVISIONAL")
        self.assertEqual(run_res["provenance_status"], "PROVISIONAL")

        # 3. Fresh tracker, fresh database connection, and reload test
        fresh_db = StructuralDatabase(self.db_path)
        fresh_tracker = ProvenanceTracker(db=fresh_db, project_id=pid)
        self.assertTrue(fresh_tracker.has_unverified_assumptions())
        self.assertTrue(fresh_tracker.requires_certification_hold())
        fresh_holds = fresh_db.get_project_holds(pid)
        fresh_assumed = next((h for h in fresh_holds if h["hold_id"] == "ASSUMED_DATA_CERTIFICATION_HOLD"), None)
        self.assertIsNotNone(fresh_assumed)
        self.assertEqual(fresh_assumed["status"], HoldStatus.ACTIVE_ENFORCED.value)

        # 4. Negative test: Certified parameters do not trigger provisional hold
        pid_cert = "CERT-HOLD-TEST"
        self.db.create_project(pid_cert, "Cert Hold Test", MountingSystemType.SYSTEM_A_CANOPY)
        cert_tracker = ProvenanceTracker(db=self.db, project_id=pid_cert)
        cert_tracker.record_parameter(
            parameter_key="basic_wind_speed_vb",
            value=39.0,
            units="m/s",
            level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            source_reference="IS 875 (Part 3): 2015 Figure 1 & Annex A",
        )
        self.assertFalse(cert_tracker.has_unverified_assumptions())
        self.assertFalse(cert_tracker.requires_certification_hold())

    # -------------------------------------------------------------------------
    # WP-02: Action Register and Load Combination Integrity
    # -------------------------------------------------------------------------
    def test_wp02_action_register_combination_integrity(self):
        """Verifies canonical action mapping, generic WL alias, and rejection of unmapped keys."""
        combs = CombinationGenerator.generate_gravity_and_wind_combinations()
        seismic_combs = CombinationGenerator.generate_seismic_combinations(include_vertical=True)
        all_combs = combs + seismic_combs

        for comb in all_combs:
            is_valid, errors = CombinationGenerator.validate_combination_integrity(comb)
            self.assertTrue(is_valid, f"Combination {comb.comb_id} failed integrity: {errors}")
            for k in comb.factors.keys():
                self.assertIn(k, CANONICAL_ACTION_KEYS)

        # 1. Direct physical action lookup
        self.assertEqual(CombinationGenerator.get_action_for_key("DL").action_id, "ACT-DL-01")
        self.assertEqual(CombinationGenerator.get_action_for_key("IL_lead").action_id, "ACT-IL-01")
        self.assertEqual(CombinationGenerator.get_action_for_key("IL_acc").action_id, "ACT-IL-03")
        self.assertEqual(CombinationGenerator.get_action_for_key("ER").action_id, "ACT-ER-01")
        self.assertEqual(CombinationGenerator.get_action_for_key("WL").action_id, "ACT-WL-UP")
        self.assertEqual(CombinationGenerator.get_action_for_key("WL_up").action_id, "ACT-WL-UP")
        self.assertEqual(CombinationGenerator.get_action_for_key("WL_down").action_id, "ACT-WL-DOWN")
        self.assertEqual(CombinationGenerator.get_action_for_key("EX").action_id, "ACT-EQ-H")
        self.assertEqual(CombinationGenerator.get_action_for_key("EZ").action_id, "ACT-EQ-V")

        # 2. Negative test: Reject unknown key in combination instantiation
        with self.assertRaises(KeyError):
            LoadCombination(
                comb_id="INVALID-01",
                limit_state="ULS",
                name="Invalid Action Comb",
                table_4_row="None",
                factors={"DL": 1.5, "UNKNOWN_ACTION_KEY": 1.2},
                formula_latex="1.5 DL + 1.2 UNKNOWN",
                description="Testing unknown factor rejection",
            )

    # -------------------------------------------------------------------------
    # WP-03: Purlin Serviceability Deflection Superposition
    # -------------------------------------------------------------------------
    def test_wp03_purlin_deflection_superposition_and_benchmark(self):
        """Verifies purlin deflection superposition under DL + distributed vs DL + point load."""
        geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=4,
            rows=4,
            columns=1,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2800.0,
        )
        engine = StructuralCalculationEngine(site=self.site, geometry=geometry)

        results = engine.check_purlin_member(
            section=self.purlin_section,
            span_mm=3000.0,
            tributary_width_mm=1150.0,
        )
        defl_res = next(r for r in results if "Purlin Gravity Deflection" in r.check_name)

        # Salem purlin independent benchmark verification:
        # L = 3000 mm, E = 69000 MPa, Ixx = 750000 mm4
        # w_dl = 0.1548 N/mm, w_il02 = 0.8625 N/mm, P = 1000 N
        # delta_dl = 5 * 0.1548 * 3000^4 / (384 * 69000 * 750000) = 3.153 mm
        # delta_il02 = 5 * 0.8625 * 3000^4 / (384 * 69000 * 750000) = 17.577 mm
        # Case A: delta_case_dist = 3.153 + 17.577 = 20.730 mm
        # Case B: delta_point = 1000 * 3000^3 / (48 * 69000 * 750000) = 10.870 mm
        #         delta_case_point = 3.153 + 10.870 = 14.023 mm
        # Governing: max(20.730, 14.023) = 20.730 mm
        # Allowable: 3000 / 250 = 12.0 mm
        # Unity ratio: 20.730 / 12.0 = 1.727537 (FAIL)
        self.assertAlmostEqual(defl_res.demand_value, 20.7304, places=2)
        self.assertEqual(defl_res.capacity_value, 12.0)
        self.assertAlmostEqual(defl_res.unity_ratio, 1.727537, places=4)
        self.assertFalse(defl_res.passed)
        self.assertIn("ACT-IL-02 Distributed", defl_res.governing_combination)
        self.assertIn("Case A (DL + Distributed Live", defl_res.notes)
        self.assertIn("Case B (DL + 1.0 kN Midspan Point Live", defl_res.notes)

    # -------------------------------------------------------------------------
    # WP-04 to WP-07: Four Systems Governance & Caveats
    # -------------------------------------------------------------------------
    def test_wp04_system_a_concentric_column_caveat_and_unsupported(self):
        """Verifies System A column check declares concentric axial limitation and frame sway unsupported."""
        geometry_a = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=4,
            rows=4,
            columns=1,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2800.0,
        )
        wf_a = SystemACanopyWorkflow(site=self.site, geometry=geometry_a)
        rep = wf_a.run_workflow_analysis(
            purlin_section=self.purlin_section,
            rafter_section=self.rafter_section,
            column_section=self.column_section,
        )
        col_res = next(r for r in rep.results if "Canopy Column" in r.check_name)
        self.assertIn("Concentric", col_res.check_name)
        self.assertIn("Axial Buckling Resistance", col_res.check_name)
        self.assertIn("Frame sway stability", col_res.notes)
        self.assertIn("combined biaxial bending", col_res.notes)
        self.assertTrue(any("Biaxial Bending" in u for u in rep.unsupported_checks))
        self.assertTrue(any("P-Delta" in u for u in rep.unsupported_checks))

    def test_wp05_system_b_gross_properties_limitation(self):
        """Verifies System B rail checks note gross section modulus and ALUMINIUM_DERIVATION_HOLD."""
        geometry_b = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL,
            total_modules=4,
            rows=2,
            columns=2,
            module=self.module,
            purlin_spacing_mm=1000.0,
            rafter_spacing_mm=1400.0,
            ground_clearance_mm=200.0,
        )
        wf_b = SystemBAluminiumRailWorkflow(site=self.site, geometry=geometry_b)
        rep = wf_b.run_workflow_analysis(
            rail_section=self.purlin_section,
            bracket_spacing_mm=1400.0,
        )
        for r in rep.results:
            if "Purlin" in r.check_name:
                self.assertIn("gross section properties", r.notes)
                self.assertIn("ALUMINIUM_DERIVATION_HOLD", r.notes)

    def test_wp06_system_c_provisional_clamp_capacity(self):
        """Verifies System C sheet clamp check explicitly warns of provisional catalogue capacity."""
        geometry_c = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_C_METAL_SHEET,
            total_modules=4,
            rows=2,
            columns=2,
            module=self.module,
            purlin_spacing_mm=1000.0,
            rafter_spacing_mm=1400.0,
            ground_clearance_mm=100.0,
        )
        wf_c = SystemCMetalSheetWorkflow(site=self.site, geometry=geometry_c)
        rep = wf_c.run_workflow_analysis(sheet_clamp_tensile_capacity_kn=3.50)
        clamp_res = next(r for r in rep.results if "Metal Sheet Clamp" in r.check_name)
        self.assertIn("Provisional", clamp_res.check_name)
        self.assertIn("catalogue screening assumption", clamp_res.notes)

    def test_wp07_system_d_assumed_friction_and_nominal_slab_allowance(self):
        """Verifies System D sliding check notes assumed friction and slab check notes nominal screening."""
        geometry_d = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_D_BALLASTED,
            total_modules=4,
            rows=2,
            columns=2,
            module=self.module,
            purlin_spacing_mm=1000.0,
            rafter_spacing_mm=1400.0,
            ground_clearance_mm=100.0,
        )
        wf_d = SystemDBallastedWorkflow(site=self.site, geometry=geometry_d)
        rep = wf_d.run_workflow_analysis(ballast_weight_kn_per_m2=0.65, friction_coeff_mu=0.40)
        slide_res = next(r for r in rep.results if "Sliding Resistance" in r.check_name)
        self.assertIn("ASSUMED FRICTION", slide_res.check_name)
        self.assertIn("FRICTION_UNVERIFIED_HOLD", slide_res.notes)

        slab_res = next(r for r in rep.results if "Host Roof Slab" in r.check_name)
        self.assertIn("UNVERIFIED PROVISIONAL", slab_res.check_name)
        self.assertIn("NOMINAL SCREENING CHECK ONLY", slab_res.notes)

    # -------------------------------------------------------------------------
    # WP-08: Input Completeness & Truthful Status
    # -------------------------------------------------------------------------
    def test_wp08_input_completeness_truthfulness(self):
        """Verifies that projects with provisional inputs are labelled PROVISIONAL, never false COMPLETE."""
        pid = "COMPLETENESS-TEST"
        self.db.create_project(pid, "Completeness Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)

        geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=4,
            rows=4,
            columns=1,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geometry)
        self.db.set_section(pid, "PURLIN", self.purlin_section)
        self.db.set_section(pid, "RAFTER", self.rafter_section)
        self.db.set_section(pid, "COLUMN", self.column_section)

        # 1. Run calculation when missing provenance records (defaults to unverified/provisional)
        run = self.db.execute_and_record_run(pid)
        self.assertEqual(run["input_completeness"], "PROVISIONAL")
        self.assertEqual(run["provenance_status"], "UNVERIFIED")
        self.assertEqual(run["engineering_status"], "UNVERIFIED")
        self.assertEqual(run["construction_status"], "BLOCKED_AFC_LOCKED")

        # 2. Add Level 5 provisional parameter: status remains PROVISIONAL
        tracker = ProvenanceTracker(db=self.db, project_id=pid)
        tracker.record_parameter(
            parameter_key="basic_wind_speed_vb",
            value=39.0,
            units="m/s",
            level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            source_reference="Unverified field assumption",
        )
        run2 = self.db.execute_and_record_run(pid)
        self.assertEqual(run2["input_completeness"], "PROVISIONAL")
        self.assertEqual(run2["provenance_status"], "PROVISIONAL")

        # 3. Complete certified provenance for all required parameters: status becomes COMPLETE & CERTIFIED
        required_keys = [
            ("basic_wind_speed_vb", 39.0, "m/s", ProvenanceLevel.LEVEL_4_STATUTORY_CODE, "IS 875 Part 3"),
            ("terrain_category", 2, "index", ProvenanceLevel.LEVEL_4_STATUTORY_CODE, "IS 875 Part 3 Table 2"),
            ("building_height_m", 12.0, "m", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Architectural as-built"),
            ("rooftop_elevation_m", 15.0, "m", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Architectural as-built"),
            ("seismic_zone", "Zone III", "zone", ProvenanceLevel.LEVEL_4_STATUTORY_CODE, "IS 1893 Part 1"),
            ("module_length_mm", 2278.0, "mm", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Manufacturer datasheet"),
            ("module_width_mm", 1134.0, "mm", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Manufacturer datasheet"),
            ("module_weight_kg", 27.5, "kg", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Manufacturer datasheet"),
            ("module_peak_power_w", 540.0, "Wp", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Manufacturer datasheet"),
            ("total_modules", 4, "count", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Array layout DWG-01"),
            ("rows", 4, "count", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Array layout DWG-01"),
            ("columns", 1, "count", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Array layout DWG-01"),
            ("purlin_spacing_mm", 1150.0, "mm", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Structural GA DWG-02"),
            ("rafter_spacing_mm", 3000.0, "mm", ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED, "Structural GA DWG-02"),
        ]
        pid_full = "COMPLETENESS-FULL"
        self.db.create_project(pid_full, "Full Certified Project", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid_full, self.site)
        self.db.set_module(pid_full, self.module)
        self.db.set_geometry(pid_full, geometry)
        self.db.set_section(pid_full, "PURLIN", self.purlin_section)
        self.db.set_section(pid_full, "RAFTER", self.rafter_section)
        self.db.set_section(pid_full, "COLUMN", self.column_section)
        full_tracker = ProvenanceTracker(db=self.db, project_id=pid_full)
        for k, val, unit, lvl, src in required_keys:
            full_tracker.record_parameter(parameter_key=k, value=val, units=unit, level=lvl, source_reference=src)

        run3 = self.db.execute_and_record_run(pid_full)
        self.assertEqual(run3["input_completeness"], "COMPLETE")
        self.assertEqual(run3["provenance_status"], "CERTIFIED")

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # WP-09: TEST-01 Transaction Rollback Verification & AFC 403 Gatekeeper
    # -------------------------------------------------------------------------
    def test_wp09_api_transaction_rollback_and_afc_gatekeeper(self):
        """
        TEST-01: Verifies API transaction safety and atomicity against active application database:
        - Successful project creation with quotation linkage.
        - Injected failure after project creation triggers complete cascading rollback.
        - Zero orphaned structural projects or quotation linkages.
        - Strict AFC 403 gatekeeper blocking.
        """
        from starlette.testclient import TestClient
        from server import app
        from quotation.settings_manager import generate_owner_token, load_owner_settings
        from quotation.quotation_history import save_quotation
        from tests.test_isolation_helper import IsolatedTestEnvironment
        from unittest.mock import patch

        with IsolatedTestEnvironment() as iso:
            iso.assert_isolated_paths()
            client = TestClient(app)
            pin = load_owner_settings().get("admin_pin", "admin123")
            valid_token = generate_owner_token(pin)
            auth_headers = {"X-Owner-Token": valid_token}

            # Seed test quotation in isolated quotation DB
            save_quotation({
                "quotation_no": "RENSUN/2026/TEST-ROLLBACK-01",
                "consumer_no": "044060072111",
                "customer_name": "Rollback Test Client",
                "status": "Draft",
                "sizing": {"recommended_capacity_kw": 10.0},
                "pricing": {"net_customer_payable": 450000.0}
            })

            # 1. Successful project creation with quotation linkage
            res_succ = client.post(
                "/api/structural/projects",
                json={
                    "name": "Successful Project",
                    "mounting_system": "A",
                    "quotation_no": "RENSUN/2026/TEST-ROLLBACK-01",
                    "project_id": "RS-STR-ROLLBACK-SUCCESS",
                    "site_location": "Salem, TN"
                },
                headers=auth_headers
            )
            self.assertEqual(res_succ.status_code, 200)
            # Verify active application DB has both project and link
            self.assertIsNotNone(iso.structural_db.get_project("RS-STR-ROLLBACK-SUCCESS"))
            self.assertIsNotNone(iso.structural_db.get_link_by_quotation("RENSUN/2026/TEST-ROLLBACK-01"))
            self.assertIsNotNone(iso.structural_db.get_site("RS-STR-ROLLBACK-SUCCESS"))

            # Seed second quotation for rollback failure test
            save_quotation({
                "quotation_no": "RENSUN/2026/TEST-ROLLBACK-02",
                "consumer_no": "044060072222",
                "customer_name": "Rollback Injected Fail Client",
                "status": "Draft",
                "sizing": {"recommended_capacity_kw": 15.0},
                "pricing": {"net_customer_payable": 650000.0}
            })

            # 2. Injected failure after project creation:
            # Simulate failure during standard section preset application
            from structural.integration import QuotationStructuralBridge
            with patch.object(
                QuotationStructuralBridge,
                "_apply_standard_sections_preset",
                side_effect=RuntimeError("Simulated post-creation hardware failure")
            ):
                res_fail = client.post(
                    "/api/structural/projects",
                    json={
                        "name": "Failure Project",
                        "mounting_system": "A",
                        "quotation_no": "RENSUN/2026/TEST-ROLLBACK-02",
                        "project_id": "RS-STR-ROLLBACK-FAIL",
                        "site_location": "Salem, TN"
                    },
                    headers=auth_headers
                )
                self.assertEqual(res_fail.status_code, 400)
                self.assertIn("Simulated post-creation hardware failure", res_fail.text)

            # Rollback verification against the ACTIVE application database
            self.assertIsNone(iso.structural_db.get_project("RS-STR-ROLLBACK-FAIL"))
            self.assertIsNone(iso.structural_db.get_site("RS-STR-ROLLBACK-FAIL"))
            self.assertIsNone(iso.structural_db.get_link_by_project("RS-STR-ROLLBACK-FAIL"))
            self.assertIsNone(iso.structural_db.get_link_by_quotation("RENSUN/2026/TEST-ROLLBACK-02"))

            # Direct SQL check ensuring ZERO orphan records exist in any table
            with iso.structural_db.get_connection() as conn:
                for tbl in ("structural_projects", "project_sites", "project_modules", "project_geometries", "project_sections", "project_holds", "quotation_structural_links"):
                    cur = conn.cursor()
                    cur.execute(f"SELECT COUNT(*) FROM {tbl} WHERE project_id = 'RS-STR-ROLLBACK-FAIL';")
                    self.assertEqual(cur.fetchone()[0], 0, f"Found orphaned records in {tbl}!")

            # 3. Deliverable and AFC Gatekeeper checks
            res_dl_unauth = client.get("/api/structural/projects/RS-STR-ROLLBACK-SUCCESS/deliverables/dxf")
            self.assertEqual(res_dl_unauth.status_code, 401)

            res_afc = client.get(
                "/api/structural/projects/RS-STR-ROLLBACK-SUCCESS/deliverables/dxf?require_approved=true",
                headers=auth_headers
            )
            self.assertEqual(res_afc.status_code, 403)
            self.assertIn("strictly forbidden", res_afc.text)

    # -------------------------------------------------------------------------
    # WP-10: Historical Snapshot Hash Stability
    # -------------------------------------------------------------------------
    def test_wp10_historical_snapshot_hash_stability(self):
        """Verifies all 20 historical runs for Salem project maintain stable SHA-256 hashes."""
        real_db = StructuralDatabase()
        runs = real_db.list_calculation_runs("RS-STR-RENSUN-2026-0059")
        self.assertEqual(len(runs), 20)

        HISTORICAL_BASELINE = {
            "RUN-RS-STR-RENSUN-2026-0059-20261107104453-7bdd0d": ("f86d8a34e20265735239b61cb6ee4423654a9b7fa09414d8a37eb4c0db641ff7", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107104610-571183": ("d7eb175e150263ea22335e51995f1ae99eb52233093daaf19e5ba452b721ebe6", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111449-fce8fb": ("d7eb175e150263ea22335e51995f1ae99eb52233093daaf19e5ba452b721ebe6", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111528-324c57": ("da74bcb5e9508d0d8b930c85711b0ba6f384079ceb4c3821768202fbbb07608f", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111549-bdafe3": ("5af50b5d2628e7da1f05651fa88c80fb5e6c815a2d65dcb035d54e9016276049", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111551-d40abb": ("9659f34760784200ce5f5c5a2b89a0274e2e51dbd52fb0de8f5aa95a409f62be", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111552-da6119": ("bd8d9921c3f06ff890390d248a8ccd7ebd1f39cb3d37879f6ea9c3e3a58292f6", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107111559-034bf4": ("b98c6d286f24e90ca87c5daaeeff94c8bfac46a024f6b7a77bebd56b12a48d0d", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107112633-f94a52": ("c0c5d498afc0dd6647b2d66ba4bd60a33c545d680e4244a6a54b6209dcf61aa0", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107112635-d13ce2": ("ab2373018aadba204b83de7262d84bb1cb883d05284e4c9e640977e7958c78a0", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107112650-07f20a": ("52400371e8206a97fe567f0f7ba3db03b17b2c381e86978ca7bb4f795d89c628", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107112703-310bd3": ("8345d64a75cbbb54d2af439944b264002f18a51f3e4d54908f3b86571b116333", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107112707-f3fa52": ("1f77be0c85b9c410c136a5ebdc9917489e583dbfbd5d17d905627a371e5f70b1", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107115315-6c20eb": ("350bba022ea65086b2f6765afa9353f5e987287037cce4faf647825771b02e47", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107115432-f1944e": ("95cc7589c6aadf039c299311a7869b64217429b4b90577ccb8c13f746001dd38", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107115532-a0413a": ("f8e353721c16fc543e6875059fbe58fa2e1783a125e43927bf95d366e7c858f4", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107122140-47fef4": ("0c8233c84af87fe6cbab1213213781f07f9666c208366d03c0e13319da8165b9", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107122245-3d01ac": ("0c8233c84af87fe6cbab1213213781f07f9666c208366d03c0e13319da8165b9", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107130635-fe00ab": ("2eadfc7efe4b91ee30530c86ad80c60bf4bb1936cf6a0f04c50071558f8e0e4f", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
            "RUN-RS-STR-RENSUN-2026-0059-20261107130822-3acfa8": ("2eadfc7efe4b91ee30530c86ad80c60bf4bb1936cf6a0f04c50071558f8e0e4f", "8ce984bc4cba66c4d6638c7528ba70376e15bfbbfe4f18ad5c900f721745d8de"),
        }

        with real_db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT run_id, input_snapshot_json, report_summary_json FROM calculation_runs WHERE project_id = 'RS-STR-RENSUN-2026-0059' ORDER BY created_at ASC;"
            )
            db_rows = cur.fetchall()

        for row in db_rows:
            run_id = row["run_id"]
            self.assertIn(run_id, HISTORICAL_BASELINE)
            expected_snap_h, expected_rep_h = HISTORICAL_BASELINE[run_id]

            computed_snap_h = hashlib.sha256(row["input_snapshot_json"].encode("utf-8")).hexdigest()
            computed_rep_h = hashlib.sha256(row["report_summary_json"].encode("utf-8")).hexdigest()

            self.assertEqual(computed_snap_h, expected_snap_h, f"Snapshot hash mismatch for historical run {run_id}")
            self.assertEqual(computed_rep_h, expected_rep_h, f"Summary hash mismatch for historical run {run_id}")

        for r_summary in runs:
            r = real_db.get_calculation_run(r_summary["run_id"])
            self.assertEqual(r["status"], "FAIL")
            self.assertEqual(r["is_approved_for_construction"], 0)
            self.assertAlmostEqual(r["max_unity_ratio"], 1.727537, places=4)
            # Verify valid JSON
            self.assertIsInstance(r["input_snapshot"], dict)
            self.assertIsInstance(r["report_summary"], dict)

    # -------------------------------------------------------------------------
    # WP-11: Drawing & DXF Governance Notes
    # -------------------------------------------------------------------------
    def test_wp11_dxf_statutory_notes_and_schematic_label(self):
        """Verifies DXF notes block contains schematic indication caveats and watermark."""
        out_dxf = os.path.join(tempfile.gettempdir(), "test_phase1422_drawing.dxf")
        geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=4,
            rows=4,
            columns=1,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2800.0,
        )
        from structural.models import DrawingMetadata
        meta = DrawingMetadata(
            project_id="DWG-TEST",
            client_name="Test Client",
            site_location="Salem",
            system_type=MountingSystemType.SYSTEM_A_CANOPY,
            drawing_number="DWG-001",
            revision="A",
            date="2026-11-07",
            is_approved_for_construction=False,
        )
        engine = DXFDrawingEngine(geometry=geometry, metadata=meta)
        engine.generate_dxf(out_dxf, require_approved=False)

        with open(out_dxf, "r") as f:
            content = f.read()

        self.assertIn("PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", content)
        self.assertIn("FRAMING POSITIONS: SCHEMATIC INDICATIONS — NOT A SURVEYED LAYOUT", content)
        self.assertIn("ROOF CLASHES: PENETRATIONS, VENTS, AND PARAPET SHADOWS NOT SURVEYED", content)

        if os.path.exists(out_dxf):
            os.remove(out_dxf)

    # -------------------------------------------------------------------------
    # WP-12: SEC-01 & SEC-02 Complete API Security Endpoint Matrix
    # -------------------------------------------------------------------------
    def test_wp12_api_security_endpoint_matrix(self):
        """
        SEC-01 & SEC-02: Verifies authentication across all 7 structural read endpoints:
        - Missing token -> 401
        - Invalid token -> 403
        - Valid token -> 200
        - Query string token rejection (?token=... without header) -> 401
        - Unauthenticated responses contain no customer structural data
        """
        from starlette.testclient import TestClient
        from server import app
        from quotation.settings_manager import generate_owner_token, load_owner_settings
        from tests.test_isolation_helper import IsolatedTestEnvironment

        with IsolatedTestEnvironment() as iso:
            client = TestClient(app)
            pin = load_owner_settings().get("admin_pin", "admin123")
            valid_token = generate_owner_token(pin)
            auth_headers = {"X-Owner-Token": valid_token}
            bad_headers = {"X-Owner-Token": "invalid-token-test-123"}

            # Create test project in isolated DB
            pid = "RS-STR-SEC-TEST-01"
            iso.structural_db.create_project(pid, "Security Test Project", MountingSystemType.SYSTEM_A_CANOPY)
            iso.structural_db.set_site(pid, self.site)
            iso.structural_db.set_module(pid, self.module)
            geometry = ArrayGeometry(
                mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
                total_modules=4,
                rows=4,
                columns=1,
                module=self.module,
                purlin_spacing_mm=1150.0,
                rafter_spacing_mm=3000.0,
                ground_clearance_mm=2800.0,
            )
            iso.structural_db.set_geometry(pid, geometry)
            iso.structural_db.set_section(pid, "PURLIN", self.purlin_section)
            iso.structural_db.set_section(pid, "RAFTER", self.rafter_section)
            iso.structural_db.set_section(pid, "COLUMN", self.column_section)
            run = iso.structural_db.execute_and_record_run(pid)
            run_id = run["run_id"]

            # Also create quotation link
            from quotation.quotation_history import save_quotation
            qno = "RENSUN/2026/SEC01"
            save_quotation({
                "quotation_no": qno,
                "consumer_no": "044060072999",
                "customer_name": "Confidential Customer",
                "status": "Draft",
                "sizing": {"recommended_capacity_kw": 12.0},
                "pricing": {"net_customer_payable": 520000.0}
            })
            iso.structural_db.link_quotation_project(
                quotation_no=qno,
                project_id=pid,
                consumer_no="044060072999",
                mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
                assessment_requested=True
            )

            # All 7 structural read endpoints under SEC-01:
            read_endpoints = [
                f"/api/structural/projects",
                f"/api/structural/projects/{pid}",
                f"/api/structural/runs",
                f"/api/structural/projects/{pid}/runs",
                f"/api/structural/runs/{run_id}",
                f"/api/structural/holds",
                f"/api/quotations/{qno}/structural",
            ]

            for ep in read_endpoints:
                # 1. Missing token -> 401
                r_missing = client.get(ep)
                self.assertEqual(r_missing.status_code, 401, f"{ep} did not return 401 when missing token!")
                self.assertIn("Authentication required. Missing X-Owner-Token header.", r_missing.text)
                # Ensure no customer structural data is exposed
                self.assertNotIn("Confidential Customer", r_missing.text)
                self.assertNotIn("Salem Site", r_missing.text)

                # 2. Invalid token -> 403
                r_invalid = client.get(ep, headers=bad_headers)
                self.assertEqual(r_invalid.status_code, 403, f"{ep} did not return 403 when token invalid!")
                self.assertIn("Forbidden. Invalid or expired owner token.", r_invalid.text)

                # 3. Query string token rejection -> 401 (SEC-02: ?token= must NOT authenticate)
                r_qs = client.get(f"{ep}{'&' if '?' in ep else '?'}token={valid_token}")
                self.assertEqual(r_qs.status_code, 401, f"{ep} permitted query-string ?token= authentication!")

                # 4. Valid header token -> 200
                r_valid = client.get(ep, headers=auth_headers)
                self.assertEqual(r_valid.status_code, 200, f"{ep} failed with valid header token!")

    # -------------------------------------------------------------------------
    # WP-13: ISO-01 & ISO-02 Test Isolation & Production Non-Interference
    # -------------------------------------------------------------------------
    def test_wp13_filesystem_and_database_isolation(self):
        """
        ISO-01 & ISO-02: Verifies test isolation architecture and proves production non-interference:
        - Active quotation DB points to temporary path.
        - Active structural DB points to temporary path.
        - Active drawing output directory points to temporary path.
        - Active owner settings file points to temporary path.
        - Active quotation PDF directory points to temporary path.
        - Generated DXF drawings are written strictly to temporary output directory.
        - Production quotations.db and structural_runs.db hashes remain byte-identical before and after.
        """
        import os
        from starlette.testclient import TestClient
        from server import app
        from quotation.settings_manager import generate_owner_token, load_owner_settings
        from tests.test_isolation_helper import (
            IsolatedTestEnvironment,
            PROD_QUOTATIONS_DB,
            PROD_STRUCTURAL_DB,
            PROD_DRAWINGS_DIR,
            get_file_sha256,
        )

        pre_quotations_sha = get_file_sha256(PROD_QUOTATIONS_DB)
        pre_structural_sha = get_file_sha256(PROD_STRUCTURAL_DB)

        with IsolatedTestEnvironment() as iso:
            iso.assert_isolated_paths()
            client = TestClient(app)
            pin = load_owner_settings().get("admin_pin", "admin123")
            auth_headers = {"X-Owner-Token": generate_owner_token(pin)}

            # Create project and generate deliverable
            pid = "RS-STR-ISO-TEST-01"
            iso.structural_db.create_project(pid, "Isolation Test GA", MountingSystemType.SYSTEM_A_CANOPY)
            iso.structural_db.set_site(pid, self.site)
            iso.structural_db.set_module(pid, self.module)
            geometry = ArrayGeometry(
                mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
                total_modules=4,
                rows=4,
                columns=1,
                module=self.module,
                purlin_spacing_mm=1150.0,
                rafter_spacing_mm=3000.0,
                ground_clearance_mm=2800.0,
            )
            iso.structural_db.set_geometry(pid, geometry)

            res_dxf = client.get(f"/api/structural/projects/{pid}/deliverables/dxf", headers=auth_headers)
            self.assertEqual(res_dxf.status_code, 200)

            # Assert DXF was written to temp drawings dir
            temp_dxf_files = [f for f in os.listdir(iso.drawings_dir) if f.endswith(".dxf")]
            self.assertGreaterEqual(len(temp_dxf_files), 1)

            # Assert NO file named RS_STR_ISO_TEST_01 exists in production drawings dir
            prod_dxf_files = [f for f in os.listdir(PROD_DRAWINGS_DIR) if "RS_STR_ISO_TEST_01" in f]
            self.assertEqual(len(prod_dxf_files), 0, "Test DXF leaked into production generated_drawings/!")

        # After deactivation, verify production hashes are 100% byte-identical
        post_quotations_sha = get_file_sha256(PROD_QUOTATIONS_DB)
        post_structural_sha = get_file_sha256(PROD_STRUCTURAL_DB)
        self.assertEqual(pre_quotations_sha, post_quotations_sha, "Production quotations.db altered by test!")
        self.assertEqual(pre_structural_sha, post_structural_sha, "Production structural_runs.db altered by test!")


if __name__ == "__main__":
    unittest.main()
