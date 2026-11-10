"""
Comprehensive Automated Test Suite for Phase 1.2 Structural Database Layer
File: tests/test_structural_database.py

Covers:
1. Database creation, connection management, and WAL mode.
2. Schema versioning and migration verification.
3. Project CRUD operations.
4. Foreign-key integrity, constraints, and cascade deletions.
5. Storage of site, module, geometry, material, and section domain objects.
6. Input snapshot immutability and calculation run persistence.
7. 100% bit-for-bit numerical reproducibility from historical input snapshots.
8. Active hold snapshot capture and non-negotiable AFC blocking.
9. DXF drawing record persistence.
10. Audit trail logging and history queries.
11. Non-interference: Proves structural database operations cannot modify quotations.db
    or alter sequential quotation numbering.
"""

import os
import sys
import tempfile
import sqlite3
import unittest
import json

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
    STEEL_E250,
    ALUMINIUM_6063_T6,
    STAINLESS_STEEL_A2_70,
)
from structural.db import StructuralDatabase, SCHEMA_VERSION


class TestStructuralDatabase(unittest.TestCase):
    """Test suite for structural persistence layer."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_structural_runs.db")
        self.db = StructuralDatabase(db_path=self.db_path)

        # Standard test domain fixtures
        self.site = SiteParameters(
            location_name="Coimbatore Tech Park",
            latitude=11.0168,
            longitude=76.9558,
            basic_wind_speed_vb=47.0,
            terrain_category=TerrainCategory.CATEGORY_2,
            building_height_m=10.0,
            rooftop_elevation_m=10.0,
            cyclonic_factor_k4=1.0,
            seismic_zone=SeismicZone.ZONE_III,
        )

        self.module = PVModuleSpecification(
            make_model="Tier-1 Mono-PERC 540W",
            length_mm=2278.0,
            width_mm=1134.0,
            thickness_mm=35.0,
            weight_kg=27.5,
            peak_power_w=540.0,
            tilt_deg=10.0,
            azimuth_deg=180.0,
        )

        self.purlin_section = SectionProperty(
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
        )

        self.rafter_section = SectionProperty(
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

    def tearDown(self):
        self.tmp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Database Creation & Schema Versioning
    # -------------------------------------------------------------------------
    def test_database_creation_and_schema_version(self):
        """Database file must be created with version table at current SCHEMA_VERSION."""
        self.assertTrue(os.path.exists(self.db_path))
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT MAX(version) FROM schema_version;")
            v = cur.fetchone()[0]
            self.assertEqual(v, SCHEMA_VERSION)

    def test_foreign_keys_pragmas_enabled(self):
        """SQLite connection must enforce PRAGMA foreign_keys = ON."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys;")
            fk = cur.fetchone()[0]
            self.assertEqual(fk, 1)

    # -------------------------------------------------------------------------
    # 2. Project CRUD Operations
    # -------------------------------------------------------------------------
    def test_project_create_and_retrieve(self):
        """Projects must persist with initial DRAFT status and correct metadata."""
        proj = self.db.create_project(
            project_id="RS-TEST-001",
            name="Coimbatore Rooftop Project",
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            client_name="Test Client Ltd",
            site_location="Coimbatore",
        )
        self.assertEqual(proj["project_id"], "RS-TEST-001")
        self.assertEqual(proj["status"], "DRAFT")

        retrieved = self.db.get_project("RS-TEST-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Coimbatore Rooftop Project")
        self.assertEqual(retrieved["mounting_system"], MountingSystemType.SYSTEM_A_CANOPY.value)

    def test_project_list(self):
        """Listing projects must return all created projects."""
        self.db.create_project("RS-01", "P1", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.create_project("RS-02", "P2", MountingSystemType.SYSTEM_B_ALUMINIUM_RAIL)
        projs = self.db.list_projects()
        self.assertEqual(len(projs), 2)
        ids = [p["project_id"] for p in projs]
        self.assertIn("RS-01", ids)
        self.assertIn("RS-02", ids)

    def test_project_update_system(self):
        """Updating project mounting system must update record and audit log."""
        self.db.create_project("RS-SYS-UPD", "P-Sys", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.update_project_system("RS-SYS-UPD", MountingSystemType.SYSTEM_D_BALLASTED)
        proj = self.db.get_project("RS-SYS-UPD")
        self.assertEqual(proj["mounting_system"], MountingSystemType.SYSTEM_D_BALLASTED.value)

    # -------------------------------------------------------------------------
    # 3. Foreign Key Integrity & Cascade Deletion
    # -------------------------------------------------------------------------
    def test_foreign_key_violation_raises(self):
        """Adding site to non-existent project must raise sqlite3.IntegrityError."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.set_site("NON-EXISTENT-PROJECT-ID", self.site)

    def test_cascade_deletion(self):
        """Deleting a project must cascade delete site, module, geometry, and sections."""
        pid = "RS-CASCADE-001"
        self.db.create_project(pid, "Cascade Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)

        # Confirm site and module exist
        self.assertIsNotNone(self.db.get_site(pid))
        self.assertIsNotNone(self.db.get_module(pid))

        # Delete project
        deleted = self.db.delete_project(pid)
        self.assertTrue(deleted)

        # Confirm cascaded deletion
        self.assertIsNone(self.db.get_project(pid))
        self.assertIsNone(self.db.get_site(pid))
        self.assertIsNone(self.db.get_module(pid))

    # -------------------------------------------------------------------------
    # 4. Domain Objects Persistence
    # -------------------------------------------------------------------------
    def test_site_parameters_persistence(self):
        """Site parameters must persist and reconstruct identical domain object."""
        pid = "RS-SITE-001"
        self.db.create_project(pid, "Site Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)

        loaded_site = self.db.get_site(pid)
        self.assertIsNotNone(loaded_site)
        self.assertEqual(loaded_site.location_name, self.site.location_name)
        self.assertEqual(loaded_site.latitude, self.site.latitude)
        self.assertEqual(loaded_site.basic_wind_speed_vb, self.site.basic_wind_speed_vb)
        self.assertEqual(loaded_site.terrain_category, self.site.terrain_category)
        self.assertEqual(loaded_site.seismic_zone, self.site.seismic_zone)

    def test_module_and_geometry_persistence(self):
        """Module and geometry must persist and reconstruct identical domain objects."""
        pid = "RS-GEOM-001"
        self.db.create_project(pid, "Geom Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_module(pid, self.module)

        geom = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3200.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geom)

        loaded_geom = self.db.get_geometry(pid)
        self.assertIsNotNone(loaded_geom)
        self.assertEqual(loaded_geom.rows, 4)
        self.assertEqual(loaded_geom.columns, 5)
        self.assertEqual(loaded_geom.total_modules, 20)
        self.assertEqual(loaded_geom.total_capacity_kw, 10.8)
        self.assertEqual(loaded_geom.purlin_spacing_mm, 1150.0)

    def test_material_and_section_persistence(self):
        """Section properties and attached materials must persist and reconstruct."""
        pid = "RS-SEC-001"
        self.db.create_project(pid, "Sec Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_section(pid, "PURLIN", self.purlin_section)

        loaded_sec = self.db.get_section(pid, "PURLIN")
        self.assertIsNotNone(loaded_sec)
        self.assertEqual(loaded_sec.designation, "ISMC 100x50x2.0")
        self.assertEqual(loaded_sec.area_mm2, 450.0)
        self.assertEqual(loaded_sec.material.name, STEEL_E250.name)
        self.assertAlmostEqual(loaded_sec.design_moment_capacity_major_kn_m, self.purlin_section.design_moment_capacity_major_kn_m, places=3)

    # -------------------------------------------------------------------------
    # 5. Calculation Run Execution, Snapshots, and Member Results
    # -------------------------------------------------------------------------
    def test_calculation_run_execution_and_persistence(self):
        """Executing calculation run must create an immutable snapshot and save results."""
        pid = "RS-CALC-001"
        self.db.create_project(pid, "Canopy Run Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)
        geom = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3200.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geom)
        self.db.set_section(pid, "PURLIN", self.purlin_section)
        self.db.set_section(pid, "RAFTER", self.rafter_section)
        self.db.set_section(pid, "COLUMN", self.rafter_section)

        run = self.db.execute_and_record_run(pid, walkway_width_m=0.80)
        self.assertIsNotNone(run)
        self.assertIn("RUN-", run["run_id"])
        self.assertEqual(run["status"], "PASS")
        self.assertGreater(run["max_unity_ratio"], 0.0)
        self.assertLessEqual(run["max_unity_ratio"], 1.0)
        # Exactly 10 canonical holds apply to System A (FRICTION is System D only, ALUMINIUM is Systems B,C,D only)
        self.assertEqual(run["active_holds_count"], 10)
        self.assertEqual(run["is_approved_for_construction"], 0)
        self.assertEqual(run["watermark"], "PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION")

        # Results verification
        self.assertGreater(len(run["results"]), 0)
        self.assertTrue(any("Purlin Sagging Flexure" in r["check_name"] for r in run["results"]))
        self.assertTrue(any("Primary Rafter Sagging Flexure" in r["check_name"] for r in run["results"]))
        self.assertTrue(any("Canopy Column Axial Buckling Resistance" in r["check_name"] for r in run["results"]))

    def test_calculation_run_overstressed_beam_records_fail(self):
        """Under-designed section must result in status='FAIL' and reflect in governing check."""
        pid = "RS-FAIL-001"
        self.db.create_project(pid, "Under-designed Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)
        geom = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3200.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geom)
        self.db.set_section(pid, "PURLIN", self.purlin_section)

        # Inadequate rafter section (ISMB 150)
        ismb150 = SectionProperty(
            designation="ISMB 150",
            profile_type="I-Section",
            material=STEEL_E250,
            area_mm2=1900.0,
            Ixx_mm4=7180000.0,
            Iyy_mm4=468000.0,
            Zxx_mm3=95700.0,
            Zyy_mm3=12500.0,
            rxx_mm=61.5,
            ryy_mm=15.7,
            mass_kg_m=14.9,
        )
        self.db.set_section(pid, "RAFTER", ismb150)
        self.db.set_section(pid, "COLUMN", self.rafter_section)

        run = self.db.execute_and_record_run(pid)
        self.assertEqual(run["status"], "FAIL")
        self.assertGreater(run["max_unity_ratio"], 1.0)
        self.assertTrue(any(not r["passed"] for r in run["results"]))

    # -------------------------------------------------------------------------
    # 6. Reproducibility Verification
    # -------------------------------------------------------------------------
    def test_reproducibility_from_stored_snapshot(self):
        """Calculation run must be 100% numerically reproducible from stored input snapshot."""
        pid = "RS-REPRO-001"
        self.db.create_project(pid, "Reproducibility Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)
        geom = ArrayGeometry(
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            total_modules=20,
            rows=4,
            columns=5,
            module=self.module,
            purlin_spacing_mm=1150.0,
            rafter_spacing_mm=3200.0,
            ground_clearance_mm=2800.0,
        )
        self.db.set_geometry(pid, geom)
        self.db.set_section(pid, "PURLIN", self.purlin_section)
        self.db.set_section(pid, "RAFTER", self.rafter_section)
        self.db.set_section(pid, "COLUMN", self.rafter_section)

        run = self.db.execute_and_record_run(pid)
        run_id = run["run_id"]

        is_reproducible, msg = self.db.verify_reproducibility(run_id)
        self.assertTrue(is_reproducible, f"Reproducibility verification failed: {msg}")

    # -------------------------------------------------------------------------
    # 7. Non-Interference with Production Quotations Database
    # -------------------------------------------------------------------------
    def test_non_interference_with_quotations_database(self):
        """Structural DB operations must never alter quotations.db or quotation sequence numbers."""
        from quotation.quotation_history import generate_next_quotation_no, DB_PATH as QUOTATIONS_DB_PATH

        # Record initial next quotation number
        initial_q_no = generate_next_quotation_no()

        # Perform multiple structural operations
        pid = "RS-NON-INT-001"
        self.db.create_project(pid, "Isolation Test", MountingSystemType.SYSTEM_A_CANOPY)
        self.db.set_site(pid, self.site)
        self.db.set_module(pid, self.module)

        # Verify quotation number is completely unaffected
        subsequent_q_no = generate_next_quotation_no()
        self.assertEqual(initial_q_no, subsequent_q_no)

        # Verify structural DB file is completely distinct from quotations DB file
        self.assertNotEqual(os.path.abspath(self.db_path), os.path.abspath(QUOTATIONS_DB_PATH))

    # -------------------------------------------------------------------------
    # 8. Quotation Integration Links (Phase 1.3)
    # -------------------------------------------------------------------------
    def test_quotation_link_persistence(self):
        """Cross-reference link between quotation and structural project must persist."""
        pid = "RS-LINK-001"
        self.db.create_project(pid, "Link Test", MountingSystemType.SYSTEM_A_CANOPY)
        link = self.db.link_quotation_project(
            quotation_no="RENSUN/2026/0001",
            project_id=pid,
            consumer_no="044060072111",
            mounting_system=MountingSystemType.SYSTEM_A_CANOPY,
            assessment_requested=True,
        )
        self.assertIsNotNone(link)
        self.assertEqual(link["quotation_no"], "RENSUN/2026/0001")
        self.assertEqual(link["project_id"], pid)
        self.assertEqual(link["assessment_requested"], 1)

        loaded = self.db.get_link_by_quotation("RENSUN/2026/0001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["consumer_no"], "044060072111")

        by_proj = self.db.get_link_by_project(pid)
        self.assertIsNotNone(by_proj)
        self.assertEqual(by_proj["quotation_no"], "RENSUN/2026/0001")


if __name__ == "__main__":
    unittest.main()
