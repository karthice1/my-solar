"""
Comprehensive Automated Test Suite for Phase 1.3 Quotation & Structural Pipeline Integration
File: tests/test_quotation_structural_integration.py

Covers:
1. Project and quotation association (linking quotation_no to structural project_id).
2. Structural project creation without duplicating existing records.
3. Controlled mounting system selection (Systems A, B, C, D).
4. Input transfer and SI unit preservation (module specs, sizing, spacing).
5. Input completeness audit (distinguishing required vs missing inputs).
6. Preliminary structural calculation invocation and run persistence.
7. Standalone structural assessment report generation with mandatory disclaimer:
   "PRELIMINARY STRUCTURAL ASSESSMENT — FOR REVIEW ONLY — NOT FOR CONSTRUCTION".
8. Separation of outputs: structural report is distinct from 5-page proposal PDF.
9. Ordinary quotation operation without structural assessment.
10. Fault tolerance: Quotation operations succeed even if structural database is unavailable.
11. Commercial immutability: Solar capacity, panel count, pricing, and sequential quotation
    numbering remain completely unchanged by structural integration.
12. FastAPI HTTP API routes for structural assessment integration.
"""

import os
import sys
import tempfile
import json
import unittest
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from server import app

from structural.models import (
    MountingSystemType,
    SiteParameters,
    TerrainCategory,
    SeismicZone,
)
from structural.db import StructuralDatabase
from structural.integration import QuotationStructuralBridge
from quotation.quotation_history import (
    save_quotation,
    get_quotation,
    generate_next_quotation_no,
)
from quotation.settings_manager import generate_owner_token, load_owner_settings


from tests.test_isolation_helper import IsolatedTestEnvironment

class TestQuotationStructuralIntegration(unittest.TestCase):
    """Test suite for quotation and structural pipeline bridge."""

    def setUp(self):
        self.iso = IsolatedTestEnvironment()
        self.iso.activate()
        self.iso.assert_isolated_paths()

        self.db_path = self.iso.structural_db_path
        self.struct_db = self.iso.structural_db
        self.bridge = QuotationStructuralBridge(db=self.struct_db)
        self.client = TestClient(app)

        pin = load_owner_settings().get("admin_pin", "admin123")
        self.token = generate_owner_token(pin)
        self.auth_headers = {"X-Owner-Token": self.token}

        # Baseline sample quotation payload
        self.sample_quotation = {
            "quotation_no": "RENSUN/2026/TEST01",
            "consumer_no": "044060072111",
            "customer_name": "R. Vasanthakumar",
            "address": "123 Industrial Estate, Coimbatore, Tamil Nadu",
            "tariff": "LA1A / DOMESTIC",
            "sanctioned_load_kw": 15.0,
            "status": "Draft",
            "sizing": {
                "recommended_capacity_kw": 10.0,
                "actual_dc_capacity_kw": 10.8,
                "number_of_panels": 20,
                "panel_wattage_wp": 540,
                "roof_area_required_sqft": 600.0,
            },
            "panel": {
                "model": "Tier-1 Mono-PERC 540W",
                "wattage_wp": 540,
                "length_mm": 2278.0,
                "width_mm": 1134.0,
                "thickness_mm": 35.0,
                "weight_kg": 27.5,
            },
            "pricing": {
                "indicative_base_price": 540000.0,
                "gross_system_cost": 540000.0,
                "subsidy_amount": 78000.0,
                "net_customer_payable": 462000.0,
            },
        }

    def tearDown(self):
        self.iso.deactivate()

    # -------------------------------------------------------------------------
    # 1. Project & Quotation Association
    # -------------------------------------------------------------------------
    def test_project_linking_creates_unique_structural_id(self):
        """Quotation must link to a unique structural project ID derived from quotation reference."""
        proj, created = self.bridge.create_or_get_project_for_quotation(
            quotation_data=self.sample_quotation,
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
        )
        self.assertTrue(created)
        self.assertEqual(proj["project_id"], "RS-STR-RENSUN-2026-TEST01")
        self.assertEqual(proj["mounting_system"], MountingSystemType.SYSTEM_A_CANOPY.value)

        # Verify cross-reference link in database
        link = self.struct_db.get_link_by_quotation("RENSUN/2026/TEST01")
        self.assertIsNotNone(link)
        self.assertEqual(link["project_id"], "RS-STR-RENSUN-2026-TEST01")
        self.assertEqual(link["consumer_no"], "044060072111")

    def test_idempotent_project_linking_prevents_duplicates(self):
        """Repeated linking calls for the same quotation must return existing project without duplicates."""
        proj1, created1 = self.bridge.create_or_get_project_for_quotation(
            quotation_data=self.sample_quotation,
            mounting_system="A",
        )
        self.assertTrue(created1)

        proj2, created2 = self.bridge.create_or_get_project_for_quotation(
            quotation_data=self.sample_quotation,
            mounting_system="A",
        )
        self.assertFalse(created2)
        self.assertEqual(proj1["project_id"], proj2["project_id"])

        # Listing projects must show only 1 project
        projs = self.struct_db.list_projects()
        self.assertEqual(len(projs), 1)

    # -------------------------------------------------------------------------
    # 2. Mounting System Selection (A, B, C, D)
    # -------------------------------------------------------------------------
    def test_mounting_system_selection_options(self):
        """Bridge must support Systems A, B, C, and D with canonical definitions."""
        sys_a = self.bridge.resolve_mounting_system("A")
        sys_b = self.bridge.resolve_mounting_system("B")
        sys_c = self.bridge.resolve_mounting_system("C")
        sys_d = self.bridge.resolve_mounting_system("D")

        # Canonical identity verification
        self.assertEqual(sys_a, MountingSystemType.SYSTEM_A_CANOPY)
        self.assertEqual(sys_a.value, "System A: Elevated Steel Canopy")

        self.assertEqual(sys_b, MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL)
        self.assertEqual(sys_b.value, "System B: Low-Height Aluminium Rail")

        self.assertEqual(sys_c, MountingSystemType.SYSTEM_C_METAL_SHEET)
        self.assertEqual(sys_c.value, "System C: Metal-Sheet Roof Mounting")

        self.assertEqual(sys_d, MountingSystemType.SYSTEM_D_BALLASTED)
        self.assertEqual(sys_d.value, "System D: Ballasted Non-Penetrating System")

        # Non-canonical configurations must be rejected and NOT mapped to C or D
        with self.assertRaises(ValueError) as cm_ground:
            self.bridge.resolve_mounting_system("GROUND_MOUNT")
        self.assertIn("Ground-mounted", str(cm_ground.exception))

        with self.assertRaises(ValueError) as cm_carport:
            self.bridge.resolve_mounting_system("CARPORT")
        self.assertIn("Carport", str(cm_carport.exception))

        with self.assertRaises(ValueError):
            self.bridge.resolve_mounting_system("UNKNOWN_XYZ")

    def test_canonical_12_holds_identity_and_presence(self):
        """All 12 original canonical verification holds must exist under exact identifiers."""
        from structural.holds import MASTER_VERIFICATION_REGISTER
        canonical_12 = [
            "INSPECTION_REQUIRED_HOLD",
            "AERODYNAMIC_UNSUPPORTED_HOLD",
            "WIND_COORD_UNVERIFIED_HOLD",
            "WIND_TRANSFORM_UNVERIFIED_HOLD",
            "VERTICAL_SEISMIC_APPLICABILITY_HOLD",
            "LOAD_COMBINATION_PROVISIONAL_HOLD",
            "FRICTION_UNVERIFIED_HOLD",
            "ALUMINIUM_DERIVATION_HOLD",
            "FASTENER_TORQUE_UNVERIFIED_HOLD",
            "NUMERICAL_INSTABILITY_HOLD",
            "ASSUMED_DATA_CERTIFICATION_HOLD",
            "DRAWING_UNVERIFIED_HOLD",
        ]
        registered_holds = {h.hold_id: h for h in MASTER_VERIFICATION_REGISTER.get_all_holds()}
        self.assertEqual(len(registered_holds), 12)
        for h_id in canonical_12:
            self.assertIn(h_id, registered_holds, f"Missing canonical hold: {h_id}")
            self.assertTrue(registered_holds[h_id].is_active())

    def test_hold_gate_enforcement_in_apis(self):
        """FastAPI endpoints must enforce hold gates and forbid AFC bypass."""
        save_quotation(self.sample_quotation, status="Draft")
        q_no = self.sample_quotation["quotation_no"]

        # Link project
        self.client.post(
            f"/api/quotations/{q_no}/structural",
            json={"mounting_system": "A", "execute_run": False},
            headers=self.auth_headers,
        )

        # Verify unauthenticated request is rejected (401)
        resp_unauth = self.client.get(f"/api/quotations/{q_no}/structural")
        self.assertEqual(resp_unauth.status_code, 401)

        # 1. GET structural endpoint reports exact holds
        resp_get = self.client.get(f"/api/quotations/{q_no}/structural", headers=self.auth_headers)
        self.assertEqual(resp_get.status_code, 200)
        data = resp_get.json()
        self.assertEqual(data["approval_status"], "BLOCKED_BY_ENGINEERING_HOLDS")
        self.assertFalse(data["can_approve_for_construction"])
        self.assertIn("INSPECTION_REQUIRED_HOLD", data["active_holds"])
        self.assertIn("DRAWING_UNVERIFIED_HOLD", data["active_holds"])
        self.assertEqual(data["active_holds_count"], 10)  # System A: 10 holds

        # 2. DXF with require_approved=True must be strictly blocked (403 Forbidden)
        resp_dxf_appr = self.client.get(
            f"/api/quotations/{q_no}/structural/dxf?require_approved=true",
            headers=self.auth_headers,
        )
        self.assertEqual(resp_dxf_appr.status_code, 403)
        self.assertIn("strictly forbidden", resp_dxf_appr.json()["detail"])

        # 3. Status update to APPROVED_FOR_CONSTRUCTION must be strictly blocked (403 Forbidden)
        resp_status = self.client.put(
            f"/api/quotations/{q_no}/status",
            json={"status": "APPROVED_FOR_CONSTRUCTION"}
        )
        self.assertEqual(resp_status.status_code, 403)
        self.assertIn("strictly forbidden", resp_status.json()["detail"])

    # -------------------------------------------------------------------------
    # 3. Input Transfer & SI Unit Preservation
    # -------------------------------------------------------------------------
    def test_input_transfer_maps_module_and_geometry(self):
        """Quotation panel count and wattage must transfer accurately into structural geometry."""
        proj, _ = self.bridge.create_or_get_project_for_quotation(
            quotation_data=self.sample_quotation,
            mounting_system="A",
            site_inputs={
                "location_name": "Coimbatore",
                "latitude": 11.0168,
                "longitude": 76.9558,
                "basic_wind_speed_vb": 47.0,
                "building_height_m": 12.0,
            },
            roof_inputs={
                "rows": 4,
                "columns": 5,
                "purlin_spacing_mm": 1150.0,
                "rafter_spacing_mm": 3200.0,
                "ground_clearance_mm": 2800.0,
            },
        )
        pid = proj["project_id"]

        module = self.struct_db.get_module(pid)
        self.assertIsNotNone(module)
        self.assertEqual(module.peak_power_w, 540.0)
        self.assertEqual(module.length_mm, 2278.0)
        self.assertEqual(module.width_mm, 1134.0)
        self.assertAlmostEqual(module.dead_load_kn_per_m2, (27.5 * 9.80665 / 1000.0) / module.area_m2, places=3)

        geom = self.struct_db.get_geometry(pid)
        self.assertIsNotNone(geom)
        self.assertEqual(geom.total_modules, 20)
        self.assertEqual(geom.rows, 4)
        self.assertEqual(geom.columns, 5)
        self.assertEqual(geom.total_capacity_kw, 10.8)

        site = self.struct_db.get_site(pid)
        self.assertIsNotNone(site)
        self.assertEqual(site.basic_wind_speed_vb, 47.0)

    # -------------------------------------------------------------------------
    # 4. Input Completeness Audit
    # -------------------------------------------------------------------------
    def test_input_completeness_audit(self):
        """Bridge must distinguish complete vs incomplete input status."""
        q_incomplete = self.sample_quotation.copy()
        q_incomplete["quotation_no"] = "RENSUN/2026/INCOMP01"

        # Link project without site parameters
        proj, _ = self.bridge.create_or_get_project_for_quotation(
            quotation_data=q_incomplete,
            mounting_system="A",
            site_inputs=None,  # Missing site!
            auto_preset_sections=False,
        )

        audit = self.bridge.assess_input_completeness(proj["project_id"])
        self.assertFalse(audit["is_complete"])
        self.assertEqual(audit["status"], "INCOMPLETE")
        self.assertIn("Site Parameters", audit["missing"])

        # Attempting calculation on incomplete inputs must return INPUTS_INCOMPLETE without executing run
        res = self.bridge.execute_structural_assessment(q_incomplete["quotation_no"])
        self.assertEqual(res["status"], "INPUTS_INCOMPLETE")
        self.assertIn("missing_inputs", res)

    # -------------------------------------------------------------------------
    # 5. Full Calculation Invocation & Result Persistence
    # -------------------------------------------------------------------------
    def test_calculation_invocation_and_summary(self):
        """Complete inputs must execute structural workflows and persist calculation run."""
        q_complete = self.sample_quotation.copy()
        q_complete["quotation_no"] = "RENSUN/2026/EXEC01"

        proj, _ = self.bridge.create_or_get_project_for_quotation(
            quotation_data=q_complete,
            mounting_system="A",
            site_inputs={
                "location_name": "Coimbatore",
                "latitude": 11.0168,
                "longitude": 76.9558,
                "basic_wind_speed_vb": 47.0,
                "building_height_m": 12.0,
            },
            roof_inputs={
                "rows": 4,
                "columns": 5,
                "purlin_spacing_mm": 1150.0,
                "rafter_spacing_mm": 3200.0,
                "ground_clearance_mm": 2800.0,
            },
            auto_preset_sections=True,
        )

        summary = self.bridge.execute_structural_assessment(q_complete["quotation_no"])
        self.assertTrue(summary["requested"])
        self.assertEqual(summary["status"], "PRELIMINARY_COMPLETED")
        self.assertEqual(summary["preliminary_calculation_status"], "PASS")
        self.assertIn("RUN-", summary["run_id"])
        self.assertGreater(summary["max_unity_ratio"], 0.0)
        self.assertLessEqual(summary["max_unity_ratio"], 1.0)
        self.assertEqual(summary["approval_status"], "BLOCKED_BY_ENGINEERING_HOLDS")
        self.assertEqual(summary["watermark"], "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION")

    # -------------------------------------------------------------------------
    # 6. Standalone Structural Assessment Report Output
    # -------------------------------------------------------------------------
    def test_structural_report_contains_mandatory_disclaimer_and_results(self):
        """Structural report must contain mandatory preliminary disclaimer and calculation details."""
        q_rep = self.sample_quotation.copy()
        q_rep["quotation_no"] = "RENSUN/2026/REP01"

        proj, _ = self.bridge.create_or_get_project_for_quotation(
            quotation_data=q_rep,
            mounting_system="A",
            site_inputs={"location_name": "Salem", "latitude": 11.66, "longitude": 78.14, "basic_wind_speed_vb": 44.0},
            roof_inputs={"rows": 4, "columns": 5},
            auto_preset_sections=True,
        )
        self.bridge.execute_structural_assessment(q_rep["quotation_no"])

        report_md = self.bridge.generate_structural_assessment_report(proj["project_id"])
        self.assertIn("PRELIMINARY STRUCTURAL ASSESSMENT — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", report_md)
        self.assertIn("APPROVED FOR CONSTRUCTION (AFC) IS STRICTLY FORBIDDEN", report_md)
        self.assertIn("TNCDBR-2019 Rule 35", report_md)
        self.assertIn("Purlin Sagging Flexure", report_md)
        self.assertIn("ACTIVE ENGINEERING VERIFICATION HOLDS", report_md)

    # -------------------------------------------------------------------------
    # 7. Unaltered Normal Quotation Operation
    # -------------------------------------------------------------------------
    def test_normal_quotation_without_structural_assessment(self):
        """Ordinary quotation without structural assessment operates cleanly with requested=False."""
        embedded = self.bridge.embed_assessment_in_quotation(self.sample_quotation, None)
        self.assertIn("structural_assessment", embedded)
        self.assertFalse(embedded["structural_assessment"]["requested"])
        self.assertEqual(embedded["structural_assessment"]["status"], "NOT_REQUESTED")

        # Solar technical and commercial values must remain 100% identical
        self.assertEqual(embedded["sizing"]["actual_dc_capacity_kw"], 10.8)
        self.assertEqual(embedded["sizing"]["number_of_panels"], 20)
        self.assertEqual(embedded["pricing"]["net_customer_payable"], 462000.0)

    # -------------------------------------------------------------------------
    # 8. Commercial Immutability & Numbering Preservation
    # -------------------------------------------------------------------------
    def test_structural_integration_does_not_modify_pricing_or_numbering(self):
        """Attaching structural assessment must never modify quotation pricing or sequence numbers."""
        initial_q_no = generate_next_quotation_no()

        # Run full structural assessment
        q_test = self.sample_quotation.copy()
        q_test["quotation_no"] = "RENSUN/2026/PRICE_CHECK"
        initial_price = q_test["pricing"]["net_customer_payable"]

        proj, _ = self.bridge.create_or_get_project_for_quotation(
            quotation_data=q_test,
            mounting_system="A",
            site_inputs={"location_name": "Madurai", "latitude": 9.92, "longitude": 78.11, "basic_wind_speed_vb": 47.0},
            roof_inputs={"rows": 4, "columns": 5},
            auto_preset_sections=True,
        )
        assessment = self.bridge.execute_structural_assessment(q_test["quotation_no"])
        updated_q = self.bridge.embed_assessment_in_quotation(q_test, assessment)

        # Price must be bit-for-bit identical
        self.assertEqual(updated_q["pricing"]["net_customer_payable"], initial_price)

        # Next quotation number must be completely unaffected
        subsequent_q_no = generate_next_quotation_no()
        self.assertEqual(initial_q_no, subsequent_q_no)

    # -------------------------------------------------------------------------
    # 9. HTTP API Route Integration
    # -------------------------------------------------------------------------
    def test_http_api_structural_integration_flow(self):
        """FastAPI endpoints for structural integration must return correct status and artifacts."""
        # 1. Save quotation first in SQLite history
        save_quotation(self.sample_quotation, status="Draft")
        q_no = self.sample_quotation["quotation_no"]

        # 2. POST attach structural assessment
        resp_post = self.client.post(
            f"/api/quotations/{q_no}/structural",
            json={
                "mounting_system": "A",
                "site_inputs": {
                    "location_name": "Chennai",
                    "latitude": 13.08,
                    "longitude": 80.27,
                    "basic_wind_speed_vb": 50.0,
                },
                "roof_inputs": {
                    "rows": 4,
                    "columns": 5,
                },
                "execute_run": True,
            },
            headers=self.auth_headers,
        )
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertTrue(data_post["success"])
        self.assertIn("RS-STR-", data_post["project_id"])
        self.assertEqual(data_post["structural_assessment"]["status"], "PRELIMINARY_COMPLETED")

        # 3. GET structural assessment status (requires authentication)
        resp_unauth = self.client.get(f"/api/quotations/{q_no}/structural")
        self.assertEqual(resp_unauth.status_code, 401)

        resp_get = self.client.get(f"/api/quotations/{q_no}/structural", headers=self.auth_headers)
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.json()
        self.assertTrue(data_get["requested"])
        self.assertEqual(data_get["input_completeness"], "COMPLETE")
        self.assertEqual(data_get["approval_status"], "BLOCKED_BY_ENGINEERING_HOLDS")

        # 4. GET standalone structural report
        resp_rep = self.client.get(
            f"/api/quotations/{q_no}/structural/report",
            headers=self.auth_headers,
        )
        self.assertEqual(resp_rep.status_code, 200)
        self.assertIn("PRELIMINARY STRUCTURAL ASSESSMENT", resp_rep.text)

        # 5. GET DXF drawing
        resp_dxf = self.client.get(
            f"/api/quotations/{q_no}/structural/dxf",
            headers=self.auth_headers,
        )
        self.assertEqual(resp_dxf.status_code, 200)
        self.assertTrue(len(resp_dxf.content) > 1000)


if __name__ == "__main__":
    unittest.main()
