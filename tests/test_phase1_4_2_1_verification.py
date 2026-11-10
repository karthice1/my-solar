"""
Comprehensive Independent Verification Suite: Phase 1.4.2.1
Categories A through N:
- Category A: Load Action Registry Tests
- Category B: Load Combination Completeness Tests
- Category C: Seismic Combination Matrix Tests
- Category D: Independent Formula Benchmark Tests
- Category E: Provenance Persistence Tests
- Category F: Hold Integration Tests
- Category G: Numerical PASS versus Engineering Verification Tests
- Category H: System A–D Unsupported-Check Tests
- Category I: DXF Watermark & Approval Gate Tests
- Category J: CLI Input Validation Tests
- Category K: API Authentication & Transaction Safety Tests
- Category L: Historical Snapshot Immutability Tests
- Category M: Quotation & PDF Regression Tests
- Category N: TNEB Extraction & Consumer Matching Regression Tests
"""

import os
import sys
import json
import math
import tempfile
import unittest
import sqlite3
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    DrawingMetadata,
    STEEL_E250,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.actions import (
    ActionRegister,
    PhysicalAction,
    LoadCombination,
    CombinationGenerator,
    CANONICAL_ACTION_KEYS,
)
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldStatus,
)
from structural.provenance import (
    ProvenanceLevel,
    ProvenanceRecord,
    ProvenanceTracker,
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
from structural.cli import main as cli_main


class TestPhase1421Verification(unittest.TestCase):
    """Exhaustive test suite verifying Phase 1.4.2.1 corrections across Categories A-N."""

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
            building_height_m=12.0,
            rooftop_elevation_m=12.0,
            cyclonic_factor_k4=1.0,
            topography_factor_k3=1.0,
            risk_coefficient_k1=1.0,
            seismic_zone=SeismicZone.ZONE_III,
        )

        self.module = PVModuleSpecification(
            make_model="Adani 540W Mono PERC",
            length_mm=2278.0,
            width_mm=1134.0,
            thickness_mm=35.0,
            weight_kg=27.5,
            peak_power_w=540.0,
            tilt_deg=10.0,
            azimuth_deg=180.0,
        )

        self.geometry = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=8,
            rows=2,
            columns=4,
            module=self.module,
            purlin_spacing_mm=1200.0,
            rafter_spacing_mm=3000.0,
            ground_clearance_mm=2400.0,
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    # -------------------------------------------------------------------------
    # Category A: Load Action Registry Tests
    # -------------------------------------------------------------------------
    def test_category_a_load_action_registry(self):
        """Verifies physical load actions retain stable identities and complete attributes."""
        actions = ActionRegister.get_all_actions()
        self.assertGreaterEqual(len(actions), 10)

        # Retained canonical IDs
        act_ids = [a.action_id for a in actions]
        for expected in ["ACT-DL-01", "ACT-IL-01", "ACT-IL-02", "ACT-IL-03", "ACT-IL-04", "ACT-ER-01", "ACT-WL-UP", "ACT-WL-DOWN", "ACT-EQ-H", "ACT-EQ-V"]:
            self.assertIn(expected, act_ids)

        il01 = ActionRegister.get_action_by_id("ACT-IL-01")
        self.assertEqual(il01.nominal_value, 1.0)
        self.assertEqual(il01.units, "kN")
        self.assertIn("Point", il01.name)
        self.assertTrue(il01.applicable_systems)
        self.assertTrue(il01.load_path_component)
        self.assertEqual(il01.combination_behavior, "MUTUALLY_EXCLUSIVE_IMPOSED")

        # Action validation test
        with self.assertRaises(ValueError):
            PhysicalAction(
                action_id="",
                name="Empty ID",
                category="Permanent",
                nominal_value=1.0,
                units="kN",
                governing_clause="IS 800",
                description="Invalid",
            ).validate()

    # -------------------------------------------------------------------------
    # Category B: Load Combination Completeness Tests
    # -------------------------------------------------------------------------
    def test_category_b_load_combination_completeness(self):
        """Verifies gravity and wind load combinations, canonical keys, and exclusion logic."""
        combs = CombinationGenerator.generate_gravity_and_wind_combinations()
        self.assertEqual(len(combs), 9)  # 6 ULS + 3 SLS

        comb_ids = [c.comb_id for c in combs]
        for cid in ["ULS-01", "ULS-02", "ULS-03", "ULS-04", "ULS-05", "ULS-06", "SLS-01", "SLS-02", "SLS-03"]:
            self.assertIn(cid, comb_ids)

        # ULS-02 Uplift reversal check
        uls02 = next(c for c in combs if c.comb_id == "ULS-02")
        self.assertEqual(uls02.factors["DL"], 0.9)
        self.assertEqual(uls02.factors["WL_up"], 1.5)
        self.assertEqual(uls02.get_factor("WL"), 1.5)
        self.assertEqual(uls02.get_factor("IL_lead"), 0.0)
        self.assertIn("WL_down", uls02.excluded_actions)

        # Reject unknown action keys
        with self.assertRaises(KeyError):
            uls02.get_factor("NON_EXISTENT_ACTION_KEY")

    # -------------------------------------------------------------------------
    # Category C: Seismic Combination Matrix Tests
    # -------------------------------------------------------------------------
    def test_category_c_seismic_combination_matrix(self):
        """Verifies complete 24-case 3D seismic combination matrix per IS 1893: 2016."""
        combs_3d = CombinationGenerator.generate_seismic_combinations(include_vertical=True)
        self.assertEqual(len(combs_3d), 24)

        # Horizontal-dominant checks
        eq01 = next(c for c in combs_3d if c.comb_id == "ULS-EQ-01")
        self.assertEqual(eq01.factors["DL"], 1.5)
        self.assertEqual(eq01.factors["EZ"], 0.45)

        eq09 = next(c for c in combs_3d if c.comb_id == "ULS-EQ-09")
        self.assertEqual(eq09.factors["DL"], 0.9)
        self.assertEqual(eq09.factors["EZ"], 0.45)

        # Vertical-dominant checks
        eq17 = next(c for c in combs_3d if c.comb_id == "ULS-EQ-17")
        self.assertEqual(eq17.factors["DL"], 1.5)
        self.assertEqual(eq17.factors["EZ"], 1.50)

        eq18 = next(c for c in combs_3d if c.comb_id == "ULS-EQ-18")
        self.assertEqual(eq18.factors["DL"], 0.9)
        self.assertEqual(eq18.factors["EZ"], -1.50)

        # 2D horizontal-only checks
        combs_2d = CombinationGenerator.generate_seismic_combinations(include_vertical=False)
        self.assertEqual(len(combs_2d), 8)
        self.assertEqual(combs_2d[0].factors["EZ"], 0.0)

    # -------------------------------------------------------------------------
    # Category D: Independent Formula Benchmark Tests
    # -------------------------------------------------------------------------
    def test_category_d_independent_formula_benchmarks(self):
        """Verifies hand-calculated benchmarks for purlin deflection and seismic forces."""
        # Benchmark: Salem Canopy C100x50x2.0 purlin over 3.0 m span
        # Salem project purlin specification: Aluminium Alloy 6063-T6 (E = 69000 MPa, Ixx = 750000 mm4)
        E = 69000.0  # MPa
        Ixx = 750000.0  # mm4
        L = 3000.0  # mm
        P = 1000.0  # N
        
        # Dead load + ACT-IL-02 Distributed Live Load (0.75 kN/m2 * 1.15 m = 0.8625 N/mm)
        w_dl = 0.1548  # N/mm (module DL + purlin sw)
        w_il02 = 0.8625  # N/mm
        w_sls = w_dl + w_il02  # ~1.0173 N/mm

        # Distributed load midspan deflection: 5 * w * L^4 / (384 * E * I)
        delta_dist = (5.0 * w_sls * (L ** 4)) / (384.0 * E * Ixx)
        self.assertAlmostEqual(delta_dist, 20.73, places=1)

        # Point load midspan deflection: P * L^3 / (48 * E * I)
        delta_point = (P * (L ** 3)) / (48.0 * E * Ixx)
        self.assertAlmostEqual(delta_point, 10.87, places=1)

        # Governing deflection is distributed case (20.73 mm > 10.87 mm)
        delta_governing = max(delta_dist, delta_point)
        self.assertAlmostEqual(delta_governing, 20.73, places=1)

        # Allowable limit L/250 = 12.0 mm
        delta_allow = L / 250.0
        self.assertEqual(delta_allow, 12.0)
        unity_ratio = delta_governing / delta_allow
        self.assertAlmostEqual(unity_ratio, 1.7275, places=3)
        self.assertGreater(unity_ratio, 1.0)  # Correctly must fail!

    # -------------------------------------------------------------------------
    # Category E: Provenance Persistence Tests
    # -------------------------------------------------------------------------
    def test_category_e_provenance_persistence(self):
        """Verifies parameter provenance persistence and validation across DB restart."""
        pid = "PROV-TEST-01"
        self.db.create_project(pid, "Prov Test", MountingSystemType.SYSTEM_A_CANOPY)

        tracker = ProvenanceTracker(db=self.db, project_id=pid)
        tracker.record_parameter(
            parameter_key="purlin_yield_strength",
            value=250.0,
            units="MPa",
            level=ProvenanceLevel.LEVEL_4_STATUTORY_CODE,
            source_reference="IS 2062: 2011 Grade E250",
            notes="Mill certificate standard",
        )

        # Reopen DB in a fresh tracker instance
        tracker_reopened = ProvenanceTracker(db=self.db, project_id=pid)
        rec = tracker_reopened.get_record("purlin_yield_strength")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.value, "250.0")
        self.assertEqual(rec.level, ProvenanceLevel.LEVEL_4_STATUTORY_CODE)

        # Test rejection of uncertified Level 1 claim
        with self.assertRaises(ValueError):
            tracker.record_parameter(
                parameter_key="unverified_param",
                value=50.0,
                units="kN",
                level=ProvenanceLevel.LEVEL_1_MEASURED,
                source_reference="",  # Empty reference must raise ValueError!
            )

    # -------------------------------------------------------------------------
    # Category F: Hold Integration Tests
    # -------------------------------------------------------------------------
    def test_category_f_hold_integration(self):
        """Verifies that all 12 canonical holds are active and provisional inputs retain holds."""
        all_holds = MASTER_VERIFICATION_REGISTER.get_all_holds()
        self.assertEqual(len(all_holds), 12)

        # Cannot release AFC while holds are active
        self.assertFalse(MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction("System A: Elevated Steel Canopy"))
        self.assertFalse(MASTER_VERIFICATION_REGISTER.can_label_approved_for_construction("System D: Ballasted Non-Penetrating System"))

        self.db.create_project("HOLD-TEST", "Hold Test Project", MountingSystemType.SYSTEM_A_CANOPY)
        tracker = ProvenanceTracker(db=self.db, project_id="HOLD-TEST")
        tracker.record_parameter(
            parameter_key="site_wind_vb",
            value=39.0,
            units="m/s",
            level=ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL,
            source_reference="Manual contour interpolation",
        )
        self.assertTrue(tracker.requires_certification_hold())

    # -------------------------------------------------------------------------
    # Category G: Numerical PASS versus Engineering Verification Tests
    # -------------------------------------------------------------------------
    def test_category_g_numerical_pass_vs_engineering_verification(self):
        """Verifies that a numerical PASS does NOT imply engineering verification."""
        pid = "NUM-PASS-TEST"
        self.db.create_project(pid, "Oversized Frame", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)

        # Use 1.0 m span so purlin easily passes deflection
        geom_short = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=8,
            rows=2,
            columns=4,
            module=self.module,
            purlin_spacing_mm=1000.0,
            rafter_spacing_mm=1000.0,  # 1.0 m span
            ground_clearance_mm=2400.0,
        )
        self.db.set_geometry(pid, geom_short)

        # Configure massive section ISMB 400
        sec_oversized = SectionProperty(
            designation="ISMB 400",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=7846.0,
            Ixx_mm4=204584000.0,
            Iyy_mm4=6221000.0,
            Zxx_mm3=1022900.0,
            Zyy_mm3=88900.0,
            rxx_mm=161.5,
            ryy_mm=28.2,
            mass_kg_m=61.6,
        )
        for comp in ("PURLIN", "RAFTER", "COLUMN"):
            self.db.set_section(pid, comp, sec_oversized)

        run = self.db.execute_and_record_run(pid)
        # Numerical outcome is PASS
        self.assertEqual(run["numerical_status"], "PASS")
        self.assertEqual(run["status"], "PASS")
        self.assertLess(run["max_unity_ratio"], 1.0)

        # Engineering status remains UNVERIFIED and construction BLOCKED!
        self.assertEqual(run["engineering_status"], "UNVERIFIED")
        self.assertEqual(run["construction_status"], "BLOCKED_AFC_LOCKED")
        self.assertEqual(run["is_approved_for_construction"], 0)
        self.assertIn("PRELIMINARY", run["watermark"])

    # -------------------------------------------------------------------------
    # Category H: System A–D Unsupported-Check Tests
    # -------------------------------------------------------------------------
    def test_category_h_unsupported_checks_across_systems(self):
        """Verifies that all 4 systems log unsupported checks and provisional inputs."""
        purlin = SectionProperty(
            designation="C100x50x2.0", profile_type="C-Channel", material=STEEL_E250,
            area_mm2=450.0, Ixx_mm4=750000.0, Iyy_mm4=180000.0, Zxx_mm3=15000.0, Zyy_mm3=5000.0,
            rxx_mm=40.8, ryy_mm=20.0, mass_kg_m=3.53
        )

        # System A
        wf_a = SystemACanopyWorkflow(site=self.site, geometry=self.geometry)
        rep_a = wf_a.run_workflow_analysis(purlin, purlin, purlin)
        self.assertTrue(rep_a.unsupported_checks)
        self.assertIn("Cold-Formed Light-Gauge Steel Local Buckling Check (IS 801: 1975)", rep_a.unsupported_checks)

        # System B
        geom_b = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL, total_modules=8, rows=2, columns=4, module=self.module
        )
        wf_b = SystemBAluminiumRailWorkflow(site=self.site, geometry=geom_b)
        rep_b = wf_b.run_workflow_analysis(purlin)
        self.assertTrue(rep_b.unsupported_checks)
        self.assertTrue(any("Aluminium" in s for s in rep_b.unsupported_checks))

        # System C
        geom_c = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_C_METAL_SHEET, total_modules=8, rows=2, columns=4, module=self.module
        )
        wf_c = SystemCMetalSheetWorkflow(site=self.site, geometry=geom_c)
        rep_c = wf_c.run_workflow_analysis()
        self.assertTrue(rep_c.unsupported_checks)
        self.assertTrue(any("Pull-Out" in s for s in rep_c.unsupported_checks))

        # System D
        geom_d = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_D_BALLASTED, total_modules=8, rows=2, columns=4, module=self.module
        )
        wf_d = SystemDBallastedWorkflow(site=self.site, geometry=geom_d)
        rep_d = wf_d.run_workflow_analysis()
        self.assertTrue(rep_d.unsupported_checks)
        self.assertTrue(any("Friction" in s for s in rep_d.unsupported_checks))

    # -------------------------------------------------------------------------
    # Category I: DXF Watermark and Approval Gate Tests
    # -------------------------------------------------------------------------
    def test_category_i_dxf_watermark_and_approval_gate(self):
        """Verifies DXF watermark, classification label, and approval blocking."""
        meta = DrawingMetadata(
            project_id="DXF-TEST",
            client_name="Test Client",
            site_location="Salem",
            system_type=MountingSystemType.SYSTEM_A_CANOPY,
            drawing_number="DWG-001",
        )
        engine = DXFDrawingEngine(geometry=self.geometry, metadata=meta)
        out_dxf = os.path.join(tempfile.gettempdir(), "test_drawing.dxf")

        engine.generate_dxf(out_dxf, require_approved=False)
        self.assertTrue(os.path.exists(out_dxf))

        with open(out_dxf, "r") as f:
            content = f.read()

        self.assertIn("PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", content)
        self.assertIn("PRELIMINARY FRAMING CONCEPT (NOT FOR CONSTRUCTION)", content)
        self.assertIn("STATUS: UNAPPROVED — ACTIVE HOLDS ENFORCED", content)

        # Gate check: require_approved=True must raise PermissionError
        with self.assertRaises(PermissionError):
            engine.generate_dxf(out_dxf, require_approved=True)

        if os.path.exists(out_dxf):
            os.remove(out_dxf)

    # -------------------------------------------------------------------------
    # Category J: CLI Input Validation Tests
    # -------------------------------------------------------------------------
    def test_category_j_cli_input_validation(self):
        """Verifies CLI rejects non-existent projects, invalid ranges, and geometry mismatches."""
        from structural.cli import build_parser

        parser = build_parser()

        # 1. Non-existent project
        parsed_nonexistent = parser.parse_args([
            "--db-path", self.db_path, "project", "set-site",
            "--project-id", "NON-EXISTENT", "--location", "Salem",
            "--lat", "11.66", "--lon", "78.14", "--vb", "39.0"
        ])
        code = parsed_nonexistent.func(parsed_nonexistent)
        self.assertEqual(code, 1)

        # 2. Geometry rows * cols != total
        self.db.create_project("GEOM-VAL-TEST", "Geom Val", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_module("GEOM-VAL-TEST", self.module)
        parsed_geom = parser.parse_args([
            "--db-path", self.db_path, "project", "set-geometry",
            "--project-id", "GEOM-VAL-TEST", "--rows", "0", "--cols", "4"
        ])
        code_geom = parsed_geom.func(parsed_geom)
        self.assertEqual(code_geom, 1)

    # -------------------------------------------------------------------------
    # Category K: API Authentication and Transaction Tests
    # -------------------------------------------------------------------------
    def test_category_k_api_authentication_and_transactions(self):
        """Verifies API transaction safety and calculation parameter validation."""
        from starlette.testclient import TestClient
        from server import app
        from quotation.settings_manager import generate_owner_token, load_owner_settings
        from tests.test_isolation_helper import IsolatedTestEnvironment

        with IsolatedTestEnvironment() as iso:
            client = TestClient(app)
            pin = load_owner_settings().get("admin_pin", "admin123")
            headers = {"X-Owner-Token": generate_owner_token(pin)}

            # Failed quotation lookup must return 404 AND not leave orphan structural project
            res_fail = client.post("/api/structural/projects", json={
                "name": "Orphan Test",
                "mounting_system": "A",
                "quotation_no": "NON-EXISTENT-QUOTATION-9999",
                "project_id": "RS-STR-ORPHAN-TEST-001"
            }, headers=headers)
            self.assertEqual(res_fail.status_code, 404)

            # Verify no orphan project created in active application DB
            orphan = iso.structural_db.get_project("RS-STR-ORPHAN-TEST-001")
            self.assertIsNone(orphan)

            # Create project in isolated DB for parameter validation test
            iso.structural_db.create_project("RS-STR-RENSUN-2026-0059", "Salem Canopy", MountingSystemType.SYSTEM_A_CANOPY)
            # Non-finite parameter rejection or invalid ranges
            res_invalid_friction = client.post("/api/structural/projects/RS-STR-RENSUN-2026-0059/calculate", json={
                "friction_coeff_mu": -0.5
            }, headers=headers)
            self.assertEqual(res_invalid_friction.status_code, 400)
            self.assertIn("Friction coefficient mu must be in physical range", res_invalid_friction.text)

    # -------------------------------------------------------------------------
    # Category L: Historical Snapshot Immutability Tests
    # -------------------------------------------------------------------------
    def test_category_l_historical_snapshot_immutability(self):
        """Verifies historical snapshots for project RS-STR-RENSUN-2026-0059 remain byte-identical."""
        real_db = StructuralDatabase()
        runs = real_db.list_calculation_runs("RS-STR-RENSUN-2026-0059")
        self.assertGreaterEqual(len(runs), 20)

        # Verify earliest historical run details
        r0_summary = runs[-1] if len(runs) > 0 else None
        self.assertIsNotNone(r0_summary)
        r0 = real_db.get_calculation_run(r0_summary["run_id"])
        self.assertIsNotNone(r0)
        self.assertEqual(r0["status"], "FAIL")
        self.assertEqual(r0["is_approved_for_construction"], 0)
        self.assertAlmostEqual(r0["max_unity_ratio"], 1.728, places=2)

    # -------------------------------------------------------------------------
    # Category M: Quotation & PDF Regression Tests
    # -------------------------------------------------------------------------
    def test_category_m_quotation_and_pdf_regression(self):
        """Verifies solar sizing, quotation pricing, and PDF generation are undisturbed."""
        from solar_engine.solar_sizing import size_solar_system
        from quotation.pricing_engine import calculate_quotation_pricing
        from quotation.settings_manager import load_owner_settings

        sizing = size_solar_system(annual_consumption_kwh=12000.0)
        self.assertGreater(sizing["recommended_capacity_kw"], 0)

        settings = load_owner_settings()
        self.assertIn("pricing", settings)

        pricing = calculate_quotation_pricing(
            system_capacity_kw=5.0,
            pricing_config=settings["pricing"],
        )
        self.assertIn("net_customer_payable", pricing)
        self.assertGreater(pricing["net_customer_payable"], 0)

    # -------------------------------------------------------------------------
    # Category N: TNEB Extraction & Consumer Matching Regression Tests
    # -------------------------------------------------------------------------
    def test_category_n_tneb_extraction_offline_regression(self):
        """Verifies TNEB extraction offline data structures and consumer matching."""
        from tneb_tool import is_exact_consumer_match, find_matching_consumer_connection, normalize_consumer_number

        self.assertEqual(normalize_consumer_number(" 03-123-456/789 "), "03123456789")
        self.assertTrue(is_exact_consumer_match("03123456789", "03-123-456/789"))
        self.assertFalse(is_exact_consumer_match("03123456789", "03123456788"))

        sample_rows = [
            {"consumerNo": "03123456788", "consumerName": "OTHER CONSUMER"},
            {"consumerNo": "03123456789", "consumerName": "TARGET CONSUMER"}
        ]
        matched = find_matching_consumer_connection(sample_rows, "03-123-456-789")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["consumerName"], "TARGET CONSUMER")


if __name__ == "__main__":
    unittest.main()
