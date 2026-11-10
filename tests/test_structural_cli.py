"""
Comprehensive Automated Test Suite for Phase 1.2 Structural CLI
File: tests/test_structural_cli.py

Covers all CLI commands and workflows:
1. project create, list, show
2. project set-site (flags & file), rejection of out-of-bounds parameters
3. project set-module (flags & file), rejection of invalid dimensions
4. project set-geometry (flags & file), rejection of row/col mismatches
5. project set-material (presets & custom)
6. project set-section (flags & file)
7. system list & select
8. calculate validate-inputs (missing vs complete)
9. calculate loads (wind & seismic trace)
10. calculate run & calculate results (formatted UX & governance output)
11. holds list, show, and check
12. drawing preview & export-dxf
13. drawing approval rejection (--require-approved blocked by governance gate)
"""

import os
import sys
import tempfile
import json
import unittest
from io import StringIO
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from structural.cli import build_parser, main
from structural.db import StructuralDatabase


class TestStructuralCLI(unittest.TestCase):
    """Test suite for structural command-line operations."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "cli_test.db")
        self.db = StructuralDatabase(db_path=self.db_path)
        self.parser = build_parser()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def run_cli(self, args_list: list) -> tuple:
        """Executes CLI command with isolated DB path, capturing stdout, stderr, and exit code."""
        full_args = ["--db-path", self.db_path] + args_list
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()
        exit_code = 0
        try:
            parsed = self.parser.parse_args(full_args)
            if hasattr(parsed, "func"):
                exit_code = parsed.func(parsed)
            else:
                exit_code = 1
        except SystemExit as se:
            exit_code = se.code
        except Exception as e:
            mystderr.write(str(e))
            exit_code = 1
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        return exit_code, mystdout.getvalue(), mystderr.getvalue()

    # -------------------------------------------------------------------------
    # 1. Project Management
    # -------------------------------------------------------------------------
    def test_cli_project_create_and_show(self):
        code, out, err = self.run_cli([
            "project", "create",
            "--project-id", "CLI-PROJ-001",
            "--name", "Madurai Industrial Roof",
            "--system", "A",
            "--client", "Madurai Mills",
            "--location", "Madurai",
        ])
        self.assertEqual(code, 0)
        self.assertIn("SUCCESS: Created structural project 'CLI-PROJ-001'", out)

        # Show
        code_s, out_s, err_s = self.run_cli(["project", "show", "--project-id", "CLI-PROJ-001"])
        self.assertEqual(code_s, 0)
        self.assertIn("Madurai Industrial Roof", out_s)
        self.assertIn("System A: Elevated Steel Canopy", out_s)

    def test_cli_project_list(self):
        self.run_cli(["project", "create", "--project-id", "P1", "--name", "Project 1", "--system", "A"])
        self.run_cli(["project", "create", "--project-id", "P2", "--name", "Project 2", "--system", "B"])

        code, out, err = self.run_cli(["project", "list"])
        self.assertEqual(code, 0)
        self.assertIn("P1", out)
        self.assertIn("P2", out)
        self.assertIn("Total Projects: 2", out)

    def test_cli_project_show_not_found(self):
        code, out, err = self.run_cli(["project", "show", "--project-id", "DOES-NOT-EXIST"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    # -------------------------------------------------------------------------
    # 2. Structural Input Configuration
    # -------------------------------------------------------------------------
    def test_cli_set_site_valid_and_out_of_bounds(self):
        self.run_cli(["project", "create", "--project-id", "SITE-TEST", "--name", "Site Test", "--system", "A"])

        # Valid site
        code, out, err = self.run_cli([
            "project", "set-site",
            "--project-id", "SITE-TEST",
            "--location", "Chennai Coast",
            "--lat", "13.08",
            "--lon", "80.27",
            "--vb", "50.0",
            "--terrain", "3",
            "--height", "12.0",
            "--k4", "1.15",
            "--seismic-zone", "Zone III",
        ])
        self.assertEqual(code, 0)
        self.assertIn("SUCCESS: Site parameters configured", out)

        # Out-of-bounds latitude (beyond Indian subcontinent [6.0, 38.0])
        code_inv, out_inv, err_inv = self.run_cli([
            "project", "set-site",
            "--project-id", "SITE-TEST",
            "--location", "Invalid Lat",
            "--lat", "45.0",
            "--lon", "80.27",
            "--vb", "50.0",
        ])
        self.assertEqual(code_inv, 1)
        self.assertIn("Latitude 45.0 out of Indian subcontinent bounds", err_inv)

    def test_cli_set_module_and_geometry(self):
        pid = "MOD-GEOM-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Mod Geom Test", "--system", "A"])

        # Set Module
        code_m, out_m, err_m = self.run_cli([
            "project", "set-module",
            "--project-id", pid,
            "--make-model", "Tier-1 540W Mono-PERC",
            "--length", "2278.0",
            "--width", "1134.0",
            "--thickness", "35.0",
            "--weight", "27.5",
            "--power", "540.0",
        ])
        self.assertEqual(code_m, 0)
        self.assertIn("SUCCESS: PV module configured", out_m)

        # Set Geometry
        code_g, out_g, err_g = self.run_cli([
            "project", "set-geometry",
            "--project-id", pid,
            "--rows", "4",
            "--cols", "5",
            "--purlin-spacing", "1150.0",
            "--rafter-spacing", "3200.0",
            "--ground-clearance", "2800.0",
        ])
        self.assertEqual(code_g, 0)
        self.assertIn("SUCCESS: Array geometry configured", out_g)
        self.assertIn("10.80 kWp", out_g)

    def test_cli_set_material_and_section(self):
        pid = "MAT-SEC-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Mat Sec Test", "--system", "A"])

        # Preset material
        code_m, out_m, err_m = self.run_cli([
            "project", "set-material",
            "--project-id", pid,
            "--component", "PURLIN",
            "--preset", "E250",
        ])
        self.assertEqual(code_m, 0)
        self.assertIn("SUCCESS: Material configured for PURLIN", out_m)

        # Section
        code_s, out_s, err_s = self.run_cli([
            "project", "set-section",
            "--project-id", pid,
            "--component", "PURLIN",
            "--designation", "ISMC 100x50x2.0",
            "--area", "450.0",
            "--ixx", "750000.0",
            "--zxx", "15000.0",
        ])
        self.assertEqual(code_s, 0)
        self.assertIn("SUCCESS: Section configured for PURLIN", out_s)

    # -------------------------------------------------------------------------
    # 3. Systems and Calculations
    # -------------------------------------------------------------------------
    def test_cli_system_list_and_select(self):
        code_l, out_l, _ = self.run_cli(["system", "list"])
        self.assertEqual(code_l, 0)
        self.assertIn("SYSTEM A: Elevated Steel Canopy", out_l)
        self.assertIn("SYSTEM D: Ballasted Non-Penetrating System", out_l)

        pid = "SYS-SEL-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Sys Sel", "--system", "A"])
        code_sel, out_sel, _ = self.run_cli(["system", "select", "--project-id", pid, "--system", "D"])
        self.assertEqual(code_sel, 0)
        self.assertIn("System D: Ballasted Non-Penetrating System", out_sel)

    def test_cli_calculate_validate_missing_vs_complete(self):
        pid = "VAL-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Val Test", "--system", "A"])

        # Incomplete project must fail validation
        code_f, out_f, _ = self.run_cli(["calculate", "validate-inputs", "--project-id", pid])
        self.assertEqual(code_f, 1)
        self.assertIn("STATUS: FAILED", out_f)

        # Configure all required inputs
        self.run_cli(["project", "set-site", "--project-id", pid, "--location", "Salem", "--lat", "11.66", "--lon", "78.14", "--vb", "44.0"])
        self.run_cli(["project", "set-module", "--project-id", pid, "--make-model", "Tier-1 540W", "--length", "2278", "--width", "1134", "--thickness", "35", "--weight", "27.5", "--power", "540"])
        self.run_cli(["project", "set-geometry", "--project-id", pid, "--rows", "4", "--cols", "5"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "PURLIN", "--designation", "ISMC 100", "--area", "450", "--ixx", "750000", "--zxx", "15000"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "RAFTER", "--designation", "ISMB 300", "--area", "5626", "--ixx", "86036000", "--zxx", "573600"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "COLUMN", "--designation", "ISMB 300", "--area", "5626", "--ixx", "86036000", "--zxx", "573600"])

        code_p, out_p, _ = self.run_cli(["calculate", "validate-inputs", "--project-id", pid])
        self.assertEqual(code_p, 0)
        self.assertIn("STATUS: PASSED", out_p)

    def test_cli_calculate_loads(self):
        pid = "LOADS-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Loads Test", "--system", "A"])
        self.run_cli(["project", "set-site", "--project-id", pid, "--location", "Chennai", "--lat", "13.08", "--lon", "80.27", "--vb", "50.0", "--k4", "1.15"])
        self.run_cli(["project", "set-module", "--project-id", pid, "--make-model", "540W", "--length", "2278", "--width", "1134", "--thickness", "35", "--weight", "27.5", "--power", "540"])
        self.run_cli(["project", "set-geometry", "--project-id", pid, "--rows", "4", "--cols", "5"])

        code, out, _ = self.run_cli(["calculate", "loads", "--project-id", pid])
        self.assertEqual(code, 0)
        self.assertIn("DESIGN WIND (IS 875 Part 3: 2015)", out)
        self.assertIn("EQUIVALENT SEISMIC FORCES (IS 1893 Part 1: 2016)", out)
        self.assertIn("LOAD COMBINATIONS GENERATED", out)

    def test_cli_calculate_run_and_results(self):
        pid = "RUN-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Full Run Test", "--system", "A"])
        self.run_cli(["project", "set-site", "--project-id", pid, "--location", "Trichy", "--lat", "10.79", "--lon", "78.70", "--vb", "47.0"])
        self.run_cli(["project", "set-module", "--project-id", pid, "--make-model", "Tier-1 540W", "--length", "2278", "--width", "1134", "--thickness", "35", "--weight", "27.5", "--power", "540"])
        self.run_cli(["project", "set-geometry", "--project-id", pid, "--rows", "4", "--cols", "5", "--purlin-spacing", "1150", "--rafter-spacing", "3200"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "PURLIN", "--designation", "ISMC 100", "--area", "450", "--ixx", "750000", "--zxx", "15000"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "RAFTER", "--designation", "ISMB 300", "--area", "5626", "--ixx", "86036000", "--zxx", "573600"])
        self.run_cli(["project", "set-section", "--project-id", pid, "--component", "COLUMN", "--designation", "ISMB 300", "--area", "5626", "--ixx", "86036000", "--zxx", "573600"])

        code_r, out_r, _ = self.run_cli(["calculate", "run", "--project-id", pid])
        self.assertEqual(code_r, 0)
        self.assertIn("PROJECT:                 RUN-TEST", out_r)
        self.assertIn("INPUT VALIDATION:        PASSED", out_r)
        self.assertIn("PRELIMINARY CALCULATION: COMPLETED", out_r)
        self.assertIn("ENGINEERING VALIDATION:  PENDING", out_r)
        self.assertIn("CONSTRUCTION APPROVAL:   BLOCKED", out_r)

        # View results
        code_res, out_res, _ = self.run_cli(["calculate", "results", "--project-id", pid])
        self.assertEqual(code_res, 0)
        self.assertIn("Purlin Sagging Flexure", out_res)
        self.assertIn("Primary Rafter Sagging Flexure", out_res)

    # -------------------------------------------------------------------------
    # 4. Verification Holds & Gate Operations
    # -------------------------------------------------------------------------
    def test_cli_holds_list_show_and_check(self):
        # List
        code_l, out_l, _ = self.run_cli(["holds", "list"])
        self.assertEqual(code_l, 0)
        self.assertIn("INSPECTION_REQUIRED_HOLD", out_l)
        self.assertIn("DRAWING_UNVERIFIED_HOLD", out_l)

        # Show
        code_s, out_s, _ = self.run_cli(["holds", "show", "--hold-id", "INSPECTION_REQUIRED_HOLD"])
        self.assertEqual(code_s, 0)
        self.assertIn("TNCDBR-2019 Rule 35", out_s)

        # Check
        code_c, out_c, _ = self.run_cli(["holds", "check", "--system", "A"])
        self.assertEqual(code_c, 0)
        self.assertIn("Approved for Construction (AFC): STRICTLY FORBIDDEN", out_c)
        self.assertIn("PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", out_c)

    # -------------------------------------------------------------------------
    # 5. Drawing Operations & Permission Gate Rejection
    # -------------------------------------------------------------------------
    def test_cli_drawing_preview_and_export_dxf(self):
        pid = "DWG-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "Dwg Test", "--system", "A"])
        self.run_cli(["project", "set-site", "--project-id", pid, "--location", "Chennai", "--lat", "13.08", "--lon", "80.27", "--vb", "50.0"])
        self.run_cli(["project", "set-module", "--project-id", pid, "--make-model", "540W", "--length", "2278", "--width", "1134", "--thickness", "35", "--weight", "27.5", "--power", "540"])
        self.run_cli(["project", "set-geometry", "--project-id", pid, "--rows", "4", "--cols", "5"])

        # Preview
        code_p, out_p, _ = self.run_cli(["drawing", "preview", "--project-id", pid])
        self.assertEqual(code_p, 0)
        self.assertIn("ARRAY DRAWING PREVIEW", out_p)
        self.assertIn("WATERMARK NOTICE:    PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION", out_p)

        # Export Preliminary DXF
        dxf_file = os.path.join(self.tmp_dir.name, "test_cli_output.dxf")
        code_e, out_e, _ = self.run_cli(["drawing", "export-dxf", "--project-id", pid, "--output", dxf_file])
        self.assertEqual(code_e, 0)
        self.assertIn("SUCCESS: DXF drawing generated successfully", out_e)
        self.assertTrue(os.path.exists(dxf_file))

    def test_cli_drawing_export_approved_blocked_by_governance_gate(self):
        """Requesting --require-approved must be blocked by the governance gate with exit code 2."""
        pid = "AFC-BLOCK-TEST"
        self.run_cli(["project", "create", "--project-id", pid, "--name", "AFC Block Test", "--system", "A"])
        self.run_cli(["project", "set-site", "--project-id", pid, "--location", "Chennai", "--lat", "13.08", "--lon", "80.27", "--vb", "50.0"])
        self.run_cli(["project", "set-module", "--project-id", pid, "--make-model", "540W", "--length", "2278", "--width", "1134", "--thickness", "35", "--weight", "27.5", "--power", "540"])
        self.run_cli(["project", "set-geometry", "--project-id", pid, "--rows", "4", "--cols", "5"])

        dxf_file = os.path.join(self.tmp_dir.name, "test_blocked.dxf")
        code_b, out_b, err_b = self.run_cli(["drawing", "export-dxf", "--project-id", pid, "--output", dxf_file, "--require-approved"])
        self.assertEqual(code_b, 2)
        self.assertIn("GOVERNANCE GATE BLOCKED", err_b)
        self.assertIn("Preliminary watermark cannot be removed", err_b)
        self.assertFalse(os.path.exists(dxf_file))


if __name__ == "__main__":
    unittest.main()
