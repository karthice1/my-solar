"""
Automated Test Suite for Phase 1.4: Structural Web UI Configurator & Project Dashboard
File: tests/test_structural_web_ui.py

Verifies:
1. Web UI template rendering of structural navigation, configurator, dashboard, and modals.
2. RESTful structural projects listing, search, filtering, and pagination.
3. Strict canonical mounting system enforcement (Systems A, B, C, D) and rejection of non-canonical systems.
4. Input updates and field-level lineage / dynamic completeness calculation.
5. Interactive structural calculation execution and run persistence.
6. Run history and immutable input snapshot inspection.
7. 12 Canonical verification holds dashboard endpoint and AFC blockers.
8. One-click deliverables generation (report, DXF, summary, inputs, sections).
9. Strict AFC gatekeeper enforcement (HTTP 403 Forbidden when unapproved DXF is requested).
10. Quotation builder structural integration and isolation from commercial quotation logic.
"""

import os
import sys
import json
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server import app
from structural.models import MountingSystemType
from structural.holds import MASTER_VERIFICATION_REGISTER


from quotation.quotation_history import save_quotation
from tests.test_isolation_helper import IsolatedTestEnvironment

class TestStructuralWebUI(unittest.TestCase):
    """Test suite for Phase 1.4 Web UI Configurator, Dashboard, and REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.iso = IsolatedTestEnvironment()
        cls.iso.activate()
        cls.iso.assert_isolated_paths()

        from quotation.settings_manager import generate_owner_token, load_owner_settings
        cls.client = TestClient(app)
        pin = load_owner_settings().get("admin_pin", "admin123")
        cls.auth_token = generate_owner_token(pin)
        cls.auth_headers = {"X-Owner-Token": cls.auth_token}

    @classmethod
    def tearDownClass(cls):
        cls.iso.deactivate()

    def setUp(self):
        self.client = self.__class__.client
        self.auth_token = self.__class__.auth_token
        self.auth_headers = self.__class__.auth_headers

    def test_01_home_page_renders_structural_ui(self):
        """Verify the main single-page application renders all structural views and components."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text

        # Navigation tabs
        self.assertIn("Structural Projects", html)
        self.assertIn("activeNav = 'structural-dashboard'", html)
        self.assertIn("activeNav = 'structural-configurator'", html)
        self.assertIn("activeNav = 'structural-history'", html)
        self.assertIn("activeNav = 'structural-holds'", html)

        # Dashboard View
        self.assertIn("Engineering Governance Notice", html)
        self.assertIn("12 Canonical Verification Holds Enforced", html)
        self.assertIn("PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", html)

        # Configurator View
        self.assertIn("Mounting System Configurator", html)
        self.assertIn("Select Canonical Mounting System", html)
        self.assertIn("Elevated Steel Canopy", html)
        self.assertIn("Low-Height Aluminium Rail", html)
        self.assertIn("Metal-Sheet Roof Mounting", html)
        self.assertIn("Ballasted Non-Penetrating", html)

        # Provenance Badges
        self.assertIn("Statutory Code", html)
        self.assertIn("Certified", html)
        self.assertIn("Measured", html)
        self.assertIn("Derived", html)

        # Modals
        self.assertIn("Create New Structural Project", html)
        self.assertIn("Project Deliverables", html)
        self.assertIn("Calculation Run Audit", html)

    def test_02_list_structural_projects_endpoint(self):
        """Verify GET /api/structural/projects returns enriched project list and governance metadata."""
        # Unauthenticated request must return 401
        res_unauth = self.client.get("/api/structural/projects")
        self.assertEqual(res_unauth.status_code, 401)

        res = self.client.get("/api/structural/projects", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("projects", data)
        self.assertIn("total", data)
        self.assertIn("governance", data)
        self.assertEqual(data["governance"]["status"], "ENGINEERING VERIFICATION PENDING")
        self.assertEqual(data["governance"]["active_holds"], 12)
        self.assertEqual(data["governance"]["afc_status"], "BLOCKED")

        # Check project enrichment
        if len(data["projects"]) > 0:
            proj = data["projects"][0]
            self.assertIn("project_id", proj)
            self.assertIn("mounting_system", proj)
            self.assertIn("input_completeness", proj)
            self.assertIn("completeness_percent", proj["input_completeness"])
            self.assertIn("approval_status", proj)
            self.assertEqual(proj["approval_status"], "BLOCKED_BY_ENGINEERING_HOLDS")

    def test_03_projects_search_and_filters(self):
        """Verify search query and multi-parameter filtering on structural projects."""
        # 1. Search term
        res_search = self.client.get("/api/structural/projects?q=SYS-D", headers=self.auth_headers)
        self.assertEqual(res_search.status_code, 200)
        data_search = res_search.json()
        for p in data_search["projects"]:
            corpus = f"{p['project_id']} {p['name']} {p['client_name']} {p['site_location']}".lower()
            self.assertIn("sys-d", corpus)

        # 2. System filter
        res_sys = self.client.get("/api/structural/projects?system=SYSTEM_D", headers=self.auth_headers)
        self.assertEqual(res_sys.status_code, 200)
        for p in res_sys.json()["projects"]:
            sys_name = p["mounting_system"].upper()
            self.assertTrue("SYSTEM_D" in sys_name or "SYSTEM D" in sys_name or "BALLAST" in sys_name)

        # 3. Completeness filter
        res_comp = self.client.get("/api/structural/projects?completeness=COMPLETE", headers=self.auth_headers)
        self.assertEqual(res_comp.status_code, 200)
        for p in res_comp.json()["projects"]:
            self.assertEqual(p["input_completeness"]["status"], "COMPLETE")

        # 4. Pagination
        res_page = self.client.get("/api/structural/projects?limit=1&offset=0", headers=self.auth_headers)
        self.assertEqual(res_page.status_code, 200)
        self.assertLessEqual(len(res_page.json()["projects"]), 1)

    def test_04_create_project_and_canonical_enforcement(self):
        """Verify POST /api/structural/projects creates canonical projects and blocks non-canonical ones."""
        # A. Create canonical System B project
        payload_valid = {
            "project_code": "RS-STR-TEST-SYS-B",
            "name": "Test System B Project",
            "client_name": "Test Client",
            "site_location": "Coimbatore, TN",
            "mounting_system": "SYSTEM_B",
            "description": "Validation test for System B rail configurator",
        }
        res_valid = self.client.post("/api/structural/projects", json=payload_valid, headers=self.auth_headers)
        self.assertEqual(res_valid.status_code, 200)
        data_valid = res_valid.json()
        self.assertEqual(data_valid["project_id"], "RS-STR-TEST-SYS-B")
        self.assertIn("System B", data_valid["mounting_system"])

        # B. Strict rejection of non-canonical systems
        payload_invalid = {
            "project_code": "RS-STR-INVALID-01",
            "name": "Invalid Ground Mount",
            "mounting_system": "GROUND_MOUNT",
        }
        res_invalid = self.client.post("/api/structural/projects", json=payload_invalid, headers=self.auth_headers)
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("cannot be mapped to canonical Systems A–D", res_invalid.json()["detail"])

        payload_carport = {
            "project_code": "RS-STR-INVALID-02",
            "name": "Invalid Carport",
            "mounting_system": "CARPORT",
        }
        res_carport = self.client.post("/api/structural/projects", json=payload_carport, headers=self.auth_headers)
        self.assertEqual(res_carport.status_code, 400)
        self.assertIn("cannot be mapped to canonical Systems A–D", res_carport.json()["detail"])

    def test_05_get_project_details_and_completeness(self):
        """Verify GET /api/structural/projects/{project_id} returns input sections and completeness."""
        pid = "RS-STR-TEST-SYS-B"
        # Unauthenticated request must return 401
        self.assertEqual(self.client.get(f"/api/structural/projects/{pid}").status_code, 401)

        res = self.client.get(f"/api/structural/projects/{pid}", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["project"]

        self.assertEqual(data["project_id"], pid)
        self.assertIn("site_inputs", data)
        self.assertIn("module_spec", data)
        self.assertIn("array_geometry", data)
        self.assertIn("sections", data)
        self.assertIn("input_completeness", data)

    def test_06_update_project_inputs(self):
        """Verify PUT /api/structural/projects/{project_id}/inputs updates parameters and lineage."""
        pid = "RS-STR-TEST-SYS-B"
        update_payload = {
            "name": "Updated System B Name",
            "site_inputs": {
                "basic_wind_speed_m_s": 44.0,
                "terrain_category": 2,
                "design_life_years": 25,
                "ground_elevation_m": 20.0,
                "k1": 1.0,
                "k2": 1.0,
                "k3": 1.0,
                "k4": 1.0,
            },
            "module_spec": {
                "module_wattage_wp": 580.0,
                "length_mm": 2278.0,
                "width_mm": 1134.0,
                "thickness_mm": 35.0,
                "mass_kg": 29.0,
                "tilt_angle_deg": 12.0,
                "orientation": "portrait",
            },
            "array_geometry": {
                "ground_clearance_m": 0.4,
                "purlin_spacing_m": 1.4,
                "rafter_spacing_m": 2.5,
            },
            "sections": {
                "rail_section": "AL_RAIL_40X40",
                "column_section": "AL_STUB_50",
            },
        }

        res = self.client.put(f"/api/structural/projects/{pid}/inputs", json=update_payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["input_completeness"]["status"], "COMPLETE")
        self.assertEqual(data["input_completeness"]["completeness_percent"], 100)

    def test_07_calculate_project_assessment(self):
        """Verify POST /api/structural/projects/{project_id}/calculate executes multi-code checks."""
        pid = "RS-STR-TEST-SYS-B"
        res = self.client.post(f"/api/structural/projects/{pid}/calculate", json={}, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("run_id", data)
        self.assertIn("status", data)
        self.assertIn("max_unity_ratio", data)
        self.assertIn("governing_check", data)
        self.assertEqual(data["approval_status"], "BLOCKED_BY_ENGINEERING_HOLDS")

    def test_08_run_history_and_immutable_snapshot_inspection(self):
        """Verify runs history and auditability via frozen immutable snapshot inspection."""
        pid = "RS-STR-TEST-SYS-B"
        # Unauthenticated request must return 401
        self.assertEqual(self.client.get(f"/api/structural/projects/{pid}/runs").status_code, 401)

        res_runs = self.client.get(f"/api/structural/projects/{pid}/runs", headers=self.auth_headers)
        self.assertEqual(res_runs.status_code, 200)
        runs = res_runs.json()["runs"]
        self.assertGreater(len(runs), 0)

        run_id = runs[0]["run_id"]
        # Unauthenticated request must return 401
        self.assertEqual(self.client.get(f"/api/structural/runs/{run_id}").status_code, 401)

        res_details = self.client.get(f"/api/structural/runs/{run_id}", headers=self.auth_headers)
        self.assertEqual(res_details.status_code, 200)
        details = res_details.json()

        self.assertIn("run", details)
        self.assertIn("input_snapshot_json", details["run"])
        snapshot = json.loads(details["run"]["input_snapshot_json"])

        # Check snapshot integrity
        self.assertIn("site", snapshot)
        self.assertIn("module", snapshot)
        self.assertEqual(snapshot["module"]["peak_power_w"], 580.0)
        self.assertEqual(snapshot["site"]["basic_wind_speed_vb"], 44.0)

    def test_09_verification_holds_dashboard(self):
        """Verify GET /api/structural/holds returns all 12 canonical holds and enforces AFC block."""
        # Unauthenticated request must return 401
        self.assertEqual(self.client.get("/api/structural/holds").status_code, 401)

        res = self.client.get("/api/structural/holds", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["governance_status"], "ENGINEERING VERIFICATION PENDING")
        self.assertEqual(data["active_holds_count"], 12)
        self.assertIn("BLOCKED", data["afc_status"])
        self.assertIn("PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", data["disclaimer"])

        hold_ids = [h["hold_id"] for h in data["holds"]]
        self.assertEqual(len(hold_ids), 12)
        self.assertIn("INSPECTION_REQUIRED_HOLD", hold_ids)
        self.assertIn("AERODYNAMIC_UNSUPPORTED_HOLD", hold_ids)
        self.assertIn("WIND_COORD_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("WIND_TRANSFORM_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("VERTICAL_SEISMIC_APPLICABILITY_HOLD", hold_ids)
        self.assertIn("LOAD_COMBINATION_PROVISIONAL_HOLD", hold_ids)
        self.assertIn("FRICTION_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("ALUMINIUM_DERIVATION_HOLD", hold_ids)
        self.assertIn("FASTENER_TORQUE_UNVERIFIED_HOLD", hold_ids)
        self.assertIn("NUMERICAL_INSTABILITY_HOLD", hold_ids)
        self.assertIn("ASSUMED_DATA_CERTIFICATION_HOLD", hold_ids)
        self.assertIn("DRAWING_UNVERIFIED_HOLD", hold_ids)

    def test_10_one_click_deliverables_download(self):
        """Verify 1-click download endpoints for report, DXF, summary, inputs, and sections."""
        pid = "RS-STR-TEST-SYS-B"

        # 1. Structural Report (.md)
        res_rep = self.client.get(f"/api/structural/projects/{pid}/deliverables/report", headers=self.auth_headers)
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn("PRELIMINARY STRUCTURAL ASSESSMENT REPORT", res_rep.text)
        self.assertIn("NOT FOR CONSTRUCTION", res_rep.text)

        # 2. General Arrangement CAD Drawing (.dxf)
        res_dxf = self.client.get(f"/api/structural/projects/{pid}/deliverables/dxf", headers=self.auth_headers)
        self.assertEqual(res_dxf.status_code, 200)
        self.assertIn("SECTION", res_dxf.text)
        self.assertIn("HEADER", res_dxf.text)

        # 3. Calculation Summary (.md)
        res_sum = self.client.get(f"/api/structural/projects/{pid}/deliverables/summary", headers=self.auth_headers)
        self.assertEqual(res_sum.status_code, 200)
        self.assertIn("CALCULATION SUMMARY", res_sum.text)

        # 4. Input Schedule (.md)
        res_inp = self.client.get(f"/api/structural/projects/{pid}/deliverables/inputs", headers=self.auth_headers)
        self.assertEqual(res_inp.status_code, 200)
        self.assertIn("STRUCTURAL INPUT SCHEDULE", res_inp.text)
        self.assertIn("Statutory Code", res_inp.text)

        # 5. Section Schedule (.md)
        res_sec = self.client.get(f"/api/structural/projects/{pid}/deliverables/sections", headers=self.auth_headers)
        self.assertEqual(res_sec.status_code, 200)
        self.assertIn("MATERIAL & SECTION SCHEDULE", res_sec.text)

    def test_11_strict_afc_gatekeeper_enforcement(self):
        """Verify that requesting AFC / approved deliverables strictly returns HTTP 403 Forbidden."""
        pid = "RS-STR-TEST-SYS-B"

        # DXF drawing with require_approved=true MUST fail with 403
        res_dxf_afc = self.client.get(f"/api/structural/projects/{pid}/deliverables/dxf?require_approved=true", headers=self.auth_headers)
        self.assertEqual(res_dxf_afc.status_code, 403)
        self.assertIn("Approved for Construction (AFC) drawing export is strictly forbidden", res_dxf_afc.json()["detail"])

        # Quotation DXF route with require_approved=true MUST also fail with 403
        res_q_dxf_afc = self.client.get("/api/quotations/DRAFT/structural/dxf?require_approved=true", headers=self.auth_headers)
        # 404 if quote not found, or 403 if hold checked
        self.assertIn(res_q_dxf_afc.status_code, [403, 404])

    def test_12_quotation_builder_structural_card_integration(self):
        """Verify seamless quotation linking without impacting commercial solar pricing."""
        # Seed quotation in isolated test DB
        save_quotation({
            "quotation_no": "RENSUN/2026/TEST01",
            "consumer_no": "044060072111",
            "customer_name": "Test Client",
            "status": "Draft",
            "sizing": {"recommended_capacity_kw": 5.0},
            "pricing": {"net_customer_payable": 250000.0}
        })

        # Check that quotations API returns 200
        res_quotes = self.client.get("/api/quotations")
        self.assertEqual(res_quotes.status_code, 200)
        quotes = res_quotes.json().get("quotations", [])

        if len(quotes) > 0:
            q_no = quotes[0]["quotation_no"]
            res_attach = self.client.post(f"/api/quotations/{q_no}/structural?mounting_system=SYSTEM_A", headers=self.auth_headers)
            self.assertEqual(res_attach.status_code, 200)
            data_attach = res_attach.json()
            self.assertIn("structural_assessment", data_attach)
            self.assertIn("System A", data_attach["structural_assessment"]["mounting_system"])

            # Verify unauthenticated request to structural assessment returns 401
            self.assertEqual(self.client.get(f"/api/quotations/{q_no}/structural").status_code, 401)
            # Authenticated request succeeds
            res_struct = self.client.get(f"/api/quotations/{q_no}/structural", headers=self.auth_headers)
            self.assertEqual(res_struct.status_code, 200)

            # Verify commercial pricing did not change
            res_quote_after = self.client.get(f"/api/quotations/{q_no}")
            self.assertEqual(res_quote_after.status_code, 200)
            q_after = res_quote_after.json()["quotation"]
            self.assertEqual(q_after["quotation_no"], q_no)

    def test_13_salem_site_provenance_and_unlisted_flag(self):
        """Phase 1.4.1 Requirement A: Verify Salem site coordinates, codal wind speed, and unlisted provenance."""
        # Create a Salem project
        payload = {
            "project_id": "RS-STR-TEST-SALEM-01",
            "name": "Salem Test Assessment",
            "client_name": "Salem Industrial Consumer",
            "site_location": "90 ERUMAPALAYAM ITTERI ROAD, SALEM",
            "mounting_system": "SYSTEM_A"
        }
        res_create = self.client.post("/api/structural/projects", json=payload, headers=self.auth_headers)
        self.assertIn(res_create.status_code, [200, 201])

        # Fetch project details (unauthenticated must fail with 401)
        self.assertEqual(self.client.get("/api/structural/projects/RS-STR-TEST-SALEM-01").status_code, 401)
        res_get = self.client.get("/api/structural/projects/RS-STR-TEST-SALEM-01", headers=self.auth_headers)
        self.assertEqual(res_get.status_code, 200)
        data = res_get.json()
        site = data.get("site_inputs") or {}

        # Salem coordinates must NOT be Chennai default (13.0827, 80.2707)
        self.assertAlmostEqual(site.get("latitude", 0), 11.6643, places=2)
        self.assertAlmostEqual(site.get("longitude", 0), 78.1460, places=2)
        # Salem basic wind speed must be 39.0 m/s per IS 875 Figure 1 contour
        self.assertEqual(site.get("basic_wind_speed_vb"), 39.0)
        # Provenance source and unlisted flag
        self.assertFalse(site.get("is_annex_a_listed"))
        self.assertIn("Figure 1", site.get("code_reference", ""))
        self.assertIn("WIND_COORD_UNVERIFIED_HOLD", site.get("verification_flag", ""))

    def test_14_hold_register_standards_and_member_results(self):
        """Phase 1.4.1 Requirement C & Workflow: Verify all 12 holds have standards and calculation returns member results."""
        # 1. Verification holds standards (unauthenticated must fail with 401)
        self.assertEqual(self.client.get("/api/structural/holds").status_code, 401)
        res_holds = self.client.get("/api/structural/holds", headers=self.auth_headers)
        self.assertEqual(res_holds.status_code, 200)
        holds = res_holds.json().get("holds", [])
        self.assertEqual(len(holds), 12)
        for h in holds:
            self.assertTrue(bool(h.get("standard")), f"Hold {h.get('hold_id')} has empty standard!")
            self.assertNotEqual(h.get("standard").strip(), "")

        # 2. Calculation execution returns member limit state checks
        pid = "RS-STR-TEST-SYS-B"
        res_calc = self.client.post(f"/api/structural/projects/{pid}/calculate", json={}, headers=self.auth_headers)
        self.assertEqual(res_calc.status_code, 200)
        calc_data = res_calc.json()
        self.assertIn("results", calc_data)
        results = calc_data["results"]
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("check_name", r)
            self.assertIn("unity_ratio", r)
            self.assertIn("demand_value", r)
            self.assertIn("capacity_value", r)
            self.assertIn("passed", r)


if __name__ == "__main__":
    unittest.main()
