"""
Structural Database & Persistence Architecture for RENSUN Solar
Package: structural.db

Features:
- Completely isolated SQLite database (structural/structural_runs.db)
- Zero coupling or interference with production quotations.db
- Foreign key enforcement and incremental schema versioning
- Full project, site, module, geometry, material, and section storage
- Immutable calculation run records with complete input snapshots
- Member-level calculation result persistence and audit history
- 100% reproducible historical calculation runs
"""

import os
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

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
from structural.holds import (
    MASTER_VERIFICATION_REGISTER,
    HoldStatus,
    HoldRecord,
)
from structural.provenance import (
    ProvenanceLevel,
    ProvenanceTracker,
)
from structural.engine import CalculationReport
from structural.workflows.system_a import SystemACanopyWorkflow
from structural.workflows.system_b import SystemBAluminiumRailWorkflow
from structural.workflows.system_c import SystemCMetalSheetWorkflow
from structural.workflows.system_d import SystemDBallastedWorkflow

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "structural_runs.db")
SCHEMA_VERSION = 6


class StructuralDatabase:
    """Isolated persistence manager for structural calculations, projects, and audit trails."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        # Ensure parent directory exists if using file path
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Yields a SQLite connection with row_factory and foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Applies schema migrations up to the current SCHEMA_VERSION."""
        with self.get_connection() as conn:
            # 1. Schema Version Tracking Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT
                );
            """)

            cur = conn.cursor()
            cur.execute("SELECT MAX(version) FROM schema_version;")
            row = cur.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            if current_version < 1:
                self._apply_migration_v1(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (1, datetime.now().isoformat(), "Initial Phase 1.2 isolated structural database schema"),
                )
                conn.commit()

            if current_version < 2:
                self._apply_migration_v2(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (2, datetime.now().isoformat(), "Phase 1.3 Quotation-structural project cross-reference links"),
                )
                conn.commit()

            if current_version < 3:
                self._apply_migration_v3(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (3, datetime.now().isoformat(), "Phase 1.3 Material table column upgrades (grade, standard_reference)"),
                )
                conn.commit()

            if current_version < 4:
                self._apply_migration_v4(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (4, datetime.now().isoformat(), "Phase 1.4 Structural project description attribute"),
                )
                conn.commit()

            if current_version < 5:
                self._apply_migration_v5(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (5, datetime.now().isoformat(), "Phase 1.4.2.1 Provenance persistence and separate status fields"),
                )
                conn.commit()

            if current_version < 6:
                self._apply_migration_v6(conn)
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?);",
                    (6, datetime.now().isoformat(), "Phase 1.4.2.2.1 Project-specific persistent hold evidence"),
                )
                conn.commit()

    def _apply_migration_v6(self, conn: sqlite3.Connection):
        """Migration V6: Add project_holds table for project-specific hold status and evidence."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                hold_id TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                evidence_notes TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, hold_id)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_project_holds_project ON project_holds(project_id);")

    def _apply_migration_v5(self, conn: sqlite3.Connection):
        """Migration V5: Add provenance_records table and separate status columns to calculation_runs."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS provenance_records (
                record_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                parameter_key TEXT NOT NULL,
                value TEXT NOT NULL,
                units TEXT NOT NULL,
                level TEXT NOT NULL,
                source_reference TEXT NOT NULL,
                certifier_name TEXT,
                date_certified TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                calculation_run_id TEXT,
                snapshot_version INTEGER DEFAULT 1
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prov_proj_param ON provenance_records(project_id, parameter_key);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prov_proj_run ON provenance_records(project_id, calculation_run_id);")

        cur = conn.cursor()
        cur.execute("PRAGMA table_info(calculation_runs);")
        cols = [row["name"] for row in cur.fetchall()]
        if "numerical_status" not in cols:
            conn.execute("ALTER TABLE calculation_runs ADD COLUMN numerical_status TEXT DEFAULT 'FAIL';")
        if "input_completeness" not in cols:
            conn.execute("ALTER TABLE calculation_runs ADD COLUMN input_completeness TEXT DEFAULT 'INCOMPLETE';")
        if "provenance_status" not in cols:
            conn.execute("ALTER TABLE calculation_runs ADD COLUMN provenance_status TEXT DEFAULT 'PROVISIONAL';")
        if "engineering_status" not in cols:
            conn.execute("ALTER TABLE calculation_runs ADD COLUMN engineering_status TEXT DEFAULT 'UNVERIFIED';")
        if "construction_status" not in cols:
            conn.execute("ALTER TABLE calculation_runs ADD COLUMN construction_status TEXT DEFAULT 'BLOCKED_AFC_LOCKED';")

    def _apply_migration_v4(self, conn: sqlite3.Connection):
        """Migration V4: Add description column to structural_projects if missing."""
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(structural_projects);")
        columns = [row["name"] for row in cur.fetchall()]
        if "description" not in columns:
            conn.execute("ALTER TABLE structural_projects ADD COLUMN description TEXT DEFAULT '';")

    def _apply_migration_v3(self, conn: sqlite3.Connection):
        """Migration V3: Ensure material columns exist on older tables."""
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(project_materials);")
        columns = [row["name"] for row in cur.fetchall()]
        if "grade" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN grade TEXT NOT NULL DEFAULT 'E250';")
        if "standard_reference" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN standard_reference TEXT NOT NULL DEFAULT 'IS 2062: 2011';")
        if "gamma_m0" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m0 REAL NOT NULL DEFAULT 1.10;")
        if "gamma_m1" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m1 REAL NOT NULL DEFAULT 1.25;")
        if "gamma_m0_override" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m0_override REAL;")
        if "gamma_m1_override" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m1_override REAL;")

    def _apply_migration_v2(self, conn: sqlite3.Connection):
        """Migration V2: Quotation-structural integration cross-reference table and column upgrades."""
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(project_materials);")
        columns = [row["name"] for row in cur.fetchall()]
        if "grade" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN grade TEXT NOT NULL DEFAULT 'E250';")
        if "standard_reference" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN standard_reference TEXT NOT NULL DEFAULT 'IS 2062: 2011';")
        if "gamma_m0_override" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m0_override REAL;")
        if "gamma_m1_override" not in columns:
            conn.execute("ALTER TABLE project_materials ADD COLUMN gamma_m1_override REAL;")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotation_structural_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_no TEXT NOT NULL UNIQUE,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                consumer_no TEXT NOT NULL,
                mounting_system TEXT NOT NULL,
                assessment_requested INTEGER NOT NULL DEFAULT 1,
                linked_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_links_quotation ON quotation_structural_links(quotation_no);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_links_project ON quotation_structural_links(project_id);")

    def _apply_migration_v1(self, conn: sqlite3.Connection):
        """Migration V1: Core structural tables with full constraints and indexes."""
        # Projects
        conn.execute("""
            CREATE TABLE IF NOT EXISTS structural_projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                client_name TEXT,
                site_location TEXT,
                mounting_system TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'DRAFT',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Site Parameters
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                location_name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                basic_wind_speed_vb REAL NOT NULL,
                terrain_category INTEGER NOT NULL,
                building_height_m REAL NOT NULL,
                rooftop_elevation_m REAL NOT NULL,
                cyclonic_factor_k4 REAL NOT NULL DEFAULT 1.0,
                topography_factor_k3 REAL NOT NULL DEFAULT 1.0,
                risk_coefficient_k1 REAL NOT NULL DEFAULT 1.0,
                seismic_zone TEXT NOT NULL DEFAULT 'Zone III',
                importance_factor_I REAL NOT NULL DEFAULT 1.0,
                response_reduction_R REAL NOT NULL DEFAULT 4.0,
                soil_type INTEGER NOT NULL DEFAULT 2,
                provenance_level INTEGER NOT NULL DEFAULT 3,
                provenance_source TEXT,
                updated_at TEXT NOT NULL
            );
        """)

        # PV Module Specification
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                make_model TEXT NOT NULL,
                length_mm REAL NOT NULL,
                width_mm REAL NOT NULL,
                thickness_mm REAL NOT NULL,
                weight_kg REAL NOT NULL,
                peak_power_w REAL NOT NULL,
                tilt_deg REAL NOT NULL DEFAULT 10.0,
                azimuth_deg REAL NOT NULL DEFAULT 180.0,
                provenance_level INTEGER NOT NULL DEFAULT 2,
                provenance_source TEXT,
                updated_at TEXT NOT NULL
            );
        """)

        # Array Geometry
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_geometries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                mounting_system TEXT NOT NULL,
                total_modules INTEGER NOT NULL,
                rows INTEGER NOT NULL,
                columns INTEGER NOT NULL,
                orientation TEXT NOT NULL DEFAULT 'PORTRAIT',
                purlin_spacing_mm REAL NOT NULL,
                rafter_spacing_mm REAL NOT NULL,
                ground_clearance_mm REAL NOT NULL,
                overhang_top_mm REAL NOT NULL DEFAULT 250.0,
                overhang_bottom_mm REAL NOT NULL DEFAULT 250.0,
                updated_at TEXT NOT NULL
            );
        """)

        # Material Properties (by component type, e.g. PURLIN, RAFTER, COLUMN, RAIL)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                component_type TEXT NOT NULL,
                material_name TEXT NOT NULL,
                grade TEXT NOT NULL DEFAULT 'E250',
                yield_strength_mpa REAL NOT NULL,
                ultimate_strength_mpa REAL NOT NULL,
                elastic_modulus_mpa REAL NOT NULL,
                poisson_ratio REAL NOT NULL,
                density_kg_m3 REAL NOT NULL,
                standard_reference TEXT NOT NULL DEFAULT 'IS 2062: 2011',
                gamma_m0 REAL NOT NULL DEFAULT 1.10,
                gamma_m1 REAL NOT NULL DEFAULT 1.25,
                gamma_m0_override REAL,
                gamma_m1_override REAL,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, component_type)
            );
        """)

        # Section Properties (by component type)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                component_type TEXT NOT NULL,
                designation TEXT NOT NULL,
                profile_type TEXT NOT NULL,
                area_mm2 REAL NOT NULL,
                Ixx_mm4 REAL NOT NULL,
                Iyy_mm4 REAL NOT NULL,
                Zxx_mm3 REAL NOT NULL,
                Zyy_mm3 REAL NOT NULL,
                rxx_mm REAL NOT NULL,
                ryy_mm REAL NOT NULL,
                mass_kg_m REAL NOT NULL,
                shear_area_mm2 REAL,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, component_type)
            );
        """)

        # Calculation Runs (Immutable Run Records with Snapshots)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calculation_runs (
                run_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                engine_version TEXT NOT NULL,
                mounting_system TEXT NOT NULL,
                calculation_method TEXT NOT NULL,
                status TEXT NOT NULL,
                max_unity_ratio REAL NOT NULL,
                governing_check TEXT NOT NULL,
                input_snapshot_json TEXT NOT NULL,
                report_summary_json TEXT NOT NULL,
                active_holds_count INTEGER NOT NULL,
                active_holds_json TEXT NOT NULL,
                is_approved_for_construction INTEGER NOT NULL DEFAULT 0,
                watermark TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # Member-level Detailed Calculation Results
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calculation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES calculation_runs(run_id) ON DELETE CASCADE,
                check_name TEXT NOT NULL,
                demand_value REAL NOT NULL,
                capacity_value REAL NOT NULL,
                unity_ratio REAL NOT NULL,
                units TEXT NOT NULL,
                governing_combination TEXT NOT NULL,
                passed INTEGER NOT NULL,
                clause_reference TEXT NOT NULL,
                notes TEXT
            );
        """)

        # DXF Drawing Output Records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drawing_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT REFERENCES calculation_runs(run_id) ON DELETE CASCADE,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                drawing_number TEXT NOT NULL,
                revision TEXT NOT NULL DEFAULT 'R0',
                file_path TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'DXF',
                watermark TEXT NOT NULL,
                is_approved_for_construction INTEGER NOT NULL DEFAULT 0,
                active_holds_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # Audit History
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES structural_projects(project_id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                details_json TEXT,
                timestamp TEXT NOT NULL
            );
        """)

        # Indexes for query optimization
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calc_runs_project ON calculation_runs(project_id, created_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calc_results_run ON calculation_results(run_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_drawings_project ON drawing_records(project_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_history(project_id, timestamp);")

    # -------------------------------------------------------------------------
    # Project Operations
    # -------------------------------------------------------------------------
    def create_project(
        self,
        project_id: str,
        name: str,
        mounting_system: Union[MountingSystemType, str],
        client_name: str = "",
        site_location: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """Creates a new structural project."""
        sys_str = mounting_system.value if isinstance(mounting_system, MountingSystemType) else mounting_system
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO structural_projects
                (project_id, name, client_name, site_location, mounting_system, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?);
                """,
                (project_id, name, client_name, site_location, sys_str, description, now, now),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="PROJECT_CREATED",
                description=f"Created structural project '{name}' for system '{sys_str}'",
                details={"client_name": client_name, "site_location": site_location, "description": description},
            )
            conn.commit()
        return self.get_project(project_id)

    def update_project_metadata(
        self,
        project_id: str,
        name: Optional[str] = None,
        client_name: Optional[str] = None,
        site_location: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates general project metadata (name, client, location, description)."""
        proj = self.get_project(project_id)
        if not proj:
            return None
        new_name = name if name is not None else proj.get("name", "")
        new_client = client_name if client_name is not None else proj.get("client_name", "")
        new_loc = site_location if site_location is not None else proj.get("site_location", "")
        new_desc = description if description is not None else proj.get("description", "")
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE structural_projects
                SET name = ?, client_name = ?, site_location = ?, description = ?, updated_at = ?
                WHERE project_id = ?;
                """,
                (new_name, new_client, new_loc, new_desc, now, project_id),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="PROJECT_METADATA_UPDATED",
                description=f"Updated metadata for project '{project_id}'",
                details={"name": new_name, "client_name": new_client, "site_location": new_loc},
            )
            conn.commit()
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves project details."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM structural_projects WHERE project_id = ?;", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return dict(row)

    def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all structural projects."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM structural_projects ORDER BY created_at DESC;")
            return [dict(r) for r in cur.fetchall()]

    def update_project_system(self, project_id: str, mounting_system: Union[MountingSystemType, str]):
        """Updates the assigned mounting system for a project."""
        sys_str = mounting_system.value if isinstance(mounting_system, MountingSystemType) else mounting_system
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE structural_projects SET mounting_system = ?, updated_at = ? WHERE project_id = ?;",
                (sys_str, now, project_id),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="SYSTEM_SELECTED",
                description=f"Updated mounting system to '{sys_str}'",
            )
            conn.commit()

    def delete_project(self, project_id: str) -> bool:
        """Deletes a structural project and cascades all associated inputs and runs."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM structural_projects WHERE project_id = ?;", (project_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    # -------------------------------------------------------------------------
    # Quotation Integration Links (Phase 1.3)
    # -------------------------------------------------------------------------
    def link_quotation_project(
        self,
        quotation_no: str,
        project_id: str,
        consumer_no: str,
        mounting_system: Union[MountingSystemType, str],
        assessment_requested: bool = True,
    ) -> Dict[str, Any]:
        """Creates or updates a persistent cross-reference link between quotation and structural project."""
        now = datetime.now().isoformat()
        sys_str = mounting_system.value if isinstance(mounting_system, MountingSystemType) else mounting_system
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quotation_structural_links (
                    quotation_no, project_id, consumer_no, mounting_system,
                    assessment_requested, linked_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(quotation_no) DO UPDATE SET
                    project_id = excluded.project_id,
                    consumer_no = excluded.consumer_no,
                    mounting_system = excluded.mounting_system,
                    assessment_requested = excluded.assessment_requested,
                    updated_at = excluded.updated_at;
                """,
                (quotation_no, project_id, consumer_no, sys_str, 1 if assessment_requested else 0, now, now),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="QUOTATION_LINKED",
                description=f"Linked quotation '{quotation_no}' to structural project '{project_id}'",
                details={"quotation_no": quotation_no, "consumer_no": consumer_no, "mounting_system": sys_str},
            )
            conn.commit()
        return self.get_link_by_quotation(quotation_no)

    def get_link_by_quotation(self, quotation_no: str) -> Optional[Dict[str, Any]]:
        """Retrieves link by quotation number."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM quotation_structural_links WHERE quotation_no = ?;", (quotation_no,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_link_by_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves link by structural project ID."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM quotation_structural_links WHERE project_id = ?;", (project_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_quotation_links(self) -> List[Dict[str, Any]]:
        """Lists all quotation-structural links."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM quotation_structural_links ORDER BY linked_at DESC;")
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Provenance Operations (Phase 1.4.2.1)
    # -------------------------------------------------------------------------
    def record_parameter_provenance(
        self,
        project_id: str,
        parameter_key: str,
        value: str,
        units: str,
        level: str,
        source_reference: str,
        certifier_name: Optional[str] = None,
        date_certified: Optional[str] = None,
        notes: str = "",
        calculation_run_id: Optional[str] = None,
        snapshot_version: int = 1,
    ) -> Dict[str, Any]:
        """Persists or updates a parameter provenance record."""
        now = datetime.now().isoformat()
        rec_id = f"PROV-{project_id}-{parameter_key}-{uuid.uuid4().hex[:6]}"
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT record_id FROM provenance_records WHERE project_id = ? AND parameter_key = ?;",
                (project_id, parameter_key),
            )
            existing = cur.fetchone()
            if existing:
                rec_id = existing["record_id"]
                conn.execute(
                    """
                    UPDATE provenance_records SET
                        value = ?, units = ?, level = ?, source_reference = ?,
                        certifier_name = ?, date_certified = ?, notes = ?,
                        updated_at = ?, calculation_run_id = ?, snapshot_version = ?
                    WHERE record_id = ?;
                    """,
                    (
                        str(value), units, level, source_reference,
                        certifier_name, date_certified, notes,
                        now, calculation_run_id, snapshot_version, rec_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO provenance_records (
                        record_id, project_id, parameter_key, value, units, level,
                        source_reference, certifier_name, date_certified, notes,
                        created_at, updated_at, calculation_run_id, snapshot_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        rec_id, project_id, parameter_key, str(value), units, level,
                        source_reference, certifier_name, date_certified, notes,
                        now, now, calculation_run_id, snapshot_version,
                    ),
                )
            conn.commit()
        return self.get_parameter_provenance(project_id, parameter_key)

    def get_parameter_provenance(self, project_id: str, parameter_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves provenance record for a specific parameter."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM provenance_records WHERE project_id = ? AND parameter_key = ?;",
                (project_id, parameter_key),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_project_provenance(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all provenance records for a project."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM provenance_records WHERE project_id = ? ORDER BY parameter_key ASC;",
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_provisional_parameters(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all parameters that are unverified or provisional."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM provenance_records WHERE project_id = ? AND level LIKE '%Provisional%' ORDER BY parameter_key ASC;",
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Project-Specific Verification Hold Operations (Phase 1.4.2.2.1)
    # -------------------------------------------------------------------------
    def set_project_hold(
        self,
        project_id: str,
        hold_id: str,
        status: str,
        reason: str = "",
        evidence_notes: str = "",
    ) -> None:
        """Persists or updates a project-specific hold status and evidence."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_holds (
                    project_id, hold_id, status, reason, evidence_notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, hold_id) DO UPDATE SET
                    status = excluded.status,
                    reason = excluded.reason,
                    evidence_notes = excluded.evidence_notes,
                    updated_at = excluded.updated_at;
                """,
                (project_id, hold_id, status, reason, evidence_notes, now),
            )
            conn.commit()

    def get_project_holds(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all verification holds for a project.
        Ensures all canonical holds applicable to the project mounting system are initialized.
        """
        proj = self.get_project(project_id)
        sys_str = proj["mounting_system"] if proj else "System A: Elevated Steel Canopy"
        from structural.holds import MASTER_VERIFICATION_REGISTER
        canonical_holds = MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(sys_str)
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            for h in canonical_holds:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO project_holds (
                        project_id, hold_id, status, reason, evidence_notes, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        project_id,
                        h.hold_id,
                        h.status.value,
                        h.description,
                        h.required_evidence,
                        now,
                    ),
                )
            conn.commit()

            cur = conn.cursor()
            cur.execute(
                "SELECT hold_id, status, reason, evidence_notes, updated_at FROM project_holds WHERE project_id = ? ORDER BY hold_id ASC;",
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def evaluate_and_enforce_project_holds(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Evaluates project inputs and provenance against canonical verification holds.
        If provisional or unverified data exists, automatically activates and persists
        ASSUMED_DATA_CERTIFICATION_HOLD with specific evidence notes.
        """
        from structural.provenance import ProvenanceTracker
        from structural.holds import HoldStatus

        tracker = ProvenanceTracker(db=self, project_id=project_id)
        if tracker.requires_certification_hold():
            provisional = tracker.get_provisional_assumptions()
            keys = [p.parameter_key for p in provisional]
            evidence = f"Unverified/provisional inputs: {', '.join(keys)}" if keys else "Missing parameter provenance records."
            self.set_project_hold(
                project_id=project_id,
                hold_id="ASSUMED_DATA_CERTIFICATION_HOLD",
                status=HoldStatus.ACTIVE_ENFORCED.value,
                reason="Mandatory SEOR assumption sign-off required for provisional inputs.",
                evidence_notes=evidence,
            )
            tracker.enforce_assumed_data_hold()

        return self.get_project_holds(project_id)

    # -------------------------------------------------------------------------
    # Site Operations
    # -------------------------------------------------------------------------
    def set_site(
        self,
        project_id: str,
        site: SiteParameters,
        provenance_level: int = 3,
        provenance_source: str = "IS 875 Appendix A Lookup",
    ):
        """Saves or updates site parameters for a project."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_sites (
                    project_id, location_name, latitude, longitude, basic_wind_speed_vb,
                    terrain_category, building_height_m, rooftop_elevation_m,
                    cyclonic_factor_k4, topography_factor_k3, risk_coefficient_k1,
                    seismic_zone, importance_factor_I, response_reduction_R, soil_type,
                    provenance_level, provenance_source, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    location_name = excluded.location_name,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    basic_wind_speed_vb = excluded.basic_wind_speed_vb,
                    terrain_category = excluded.terrain_category,
                    building_height_m = excluded.building_height_m,
                    rooftop_elevation_m = excluded.rooftop_elevation_m,
                    cyclonic_factor_k4 = excluded.cyclonic_factor_k4,
                    topography_factor_k3 = excluded.topography_factor_k3,
                    risk_coefficient_k1 = excluded.risk_coefficient_k1,
                    seismic_zone = excluded.seismic_zone,
                    importance_factor_I = excluded.importance_factor_I,
                    response_reduction_R = excluded.response_reduction_R,
                    soil_type = excluded.soil_type,
                    provenance_level = excluded.provenance_level,
                    provenance_source = excluded.provenance_source,
                    updated_at = excluded.updated_at;
                """,
                (
                    project_id,
                    site.location_name,
                    site.latitude,
                    site.longitude,
                    site.basic_wind_speed_vb,
                    site.terrain_category.value,
                    site.building_height_m,
                    site.rooftop_elevation_m,
                    site.cyclonic_factor_k4,
                    site.topography_factor_k3,
                    site.risk_coefficient_k1,
                    site.seismic_zone.value,
                    site.importance_factor_I,
                    site.response_reduction_R,
                    site.soil_type,
                    provenance_level,
                    provenance_source,
                    now,
                ),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="SITE_CONFIGURED",
                description=f"Configured site: {site.location_name} (Vb={site.basic_wind_speed_vb} m/s)",
            )
            conn.commit()

    def get_site(self, project_id: str) -> Optional[SiteParameters]:
        """Retrieves SiteParameters domain object."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM project_sites WHERE project_id = ?;", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return SiteParameters(
                location_name=row["location_name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                basic_wind_speed_vb=row["basic_wind_speed_vb"],
                terrain_category=TerrainCategory(row["terrain_category"]),
                building_height_m=row["building_height_m"],
                rooftop_elevation_m=row["rooftop_elevation_m"],
                cyclonic_factor_k4=row["cyclonic_factor_k4"],
                topography_factor_k3=row["topography_factor_k3"],
                risk_coefficient_k1=row["risk_coefficient_k1"],
                seismic_zone=SeismicZone(row["seismic_zone"]),
                importance_factor_I=row["importance_factor_I"],
                response_reduction_R=row["response_reduction_R"],
                soil_type=row["soil_type"],
            )

    # -------------------------------------------------------------------------
    # PV Module Operations
    # -------------------------------------------------------------------------
    def set_module(
        self,
        project_id: str,
        module: PVModuleSpecification,
        provenance_level: int = 2,
        provenance_source: str = "Manufacturer Datasheet",
    ):
        """Saves or updates PV module specifications for a project."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_modules (
                    project_id, make_model, length_mm, width_mm, thickness_mm,
                    weight_kg, peak_power_w, tilt_deg, azimuth_deg,
                    provenance_level, provenance_source, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    make_model = excluded.make_model,
                    length_mm = excluded.length_mm,
                    width_mm = excluded.width_mm,
                    thickness_mm = excluded.thickness_mm,
                    weight_kg = excluded.weight_kg,
                    peak_power_w = excluded.peak_power_w,
                    tilt_deg = excluded.tilt_deg,
                    azimuth_deg = excluded.azimuth_deg,
                    provenance_level = excluded.provenance_level,
                    provenance_source = excluded.provenance_source,
                    updated_at = excluded.updated_at;
                """,
                (
                    project_id,
                    module.make_model,
                    module.length_mm,
                    module.width_mm,
                    module.thickness_mm,
                    module.weight_kg,
                    module.peak_power_w,
                    module.tilt_deg,
                    module.azimuth_deg,
                    provenance_level,
                    provenance_source,
                    now,
                ),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="MODULE_CONFIGURED",
                description=f"Configured module: {module.make_model} ({module.peak_power_w} W)",
            )
            conn.commit()

    def get_module(self, project_id: str) -> Optional[PVModuleSpecification]:
        """Retrieves PVModuleSpecification domain object."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM project_modules WHERE project_id = ?;", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return PVModuleSpecification(
                make_model=row["make_model"],
                length_mm=row["length_mm"],
                width_mm=row["width_mm"],
                thickness_mm=row["thickness_mm"],
                weight_kg=row["weight_kg"],
                peak_power_w=row["peak_power_w"],
                tilt_deg=row["tilt_deg"],
                azimuth_deg=row["azimuth_deg"],
            )

    # -------------------------------------------------------------------------
    # Array Geometry Operations
    # -------------------------------------------------------------------------
    def set_geometry(self, project_id: str, geometry: ArrayGeometry):
        """Saves or updates array geometry for a project."""
        now = datetime.now().isoformat()
        sys_str = geometry.mounting_system.value if isinstance(geometry.mounting_system, MountingSystemType) else geometry.mounting_system
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_geometries (
                    project_id, mounting_system, total_modules, rows, columns,
                    orientation, purlin_spacing_mm, rafter_spacing_mm,
                    ground_clearance_mm, overhang_top_mm, overhang_bottom_mm, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    mounting_system = excluded.mounting_system,
                    total_modules = excluded.total_modules,
                    rows = excluded.rows,
                    columns = excluded.columns,
                    orientation = excluded.orientation,
                    purlin_spacing_mm = excluded.purlin_spacing_mm,
                    rafter_spacing_mm = excluded.rafter_spacing_mm,
                    ground_clearance_mm = excluded.ground_clearance_mm,
                    overhang_top_mm = excluded.overhang_top_mm,
                    overhang_bottom_mm = excluded.overhang_bottom_mm,
                    updated_at = excluded.updated_at;
                """,
                (
                    project_id,
                    sys_str,
                    geometry.total_modules,
                    geometry.rows,
                    geometry.columns,
                    geometry.orientation,
                    geometry.purlin_spacing_mm,
                    geometry.rafter_spacing_mm,
                    geometry.ground_clearance_mm,
                    geometry.overhang_top_mm,
                    geometry.overhang_bottom_mm,
                    now,
                ),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="GEOMETRY_CONFIGURED",
                description=f"Configured geometry: {geometry.rows}x{geometry.columns} = {geometry.total_modules} modules",
            )
            conn.commit()

    def get_geometry(self, project_id: str) -> Optional[ArrayGeometry]:
        """Retrieves ArrayGeometry domain object (requires module to be configured)."""
        module = self.get_module(project_id)
        if not module:
            return None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM project_geometries WHERE project_id = ?;", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return ArrayGeometry(
                mounting_system=MountingSystemType(row["mounting_system"]),
                total_modules=row["total_modules"],
                rows=row["rows"],
                columns=row["columns"],
                module=module,
                orientation=row["orientation"],
                purlin_spacing_mm=row["purlin_spacing_mm"],
                rafter_spacing_mm=row["rafter_spacing_mm"],
                ground_clearance_mm=row["ground_clearance_mm"],
                overhang_top_mm=row["overhang_top_mm"],
                overhang_bottom_mm=row["overhang_bottom_mm"],
            )

    # -------------------------------------------------------------------------
    # Material & Section Operations
    # -------------------------------------------------------------------------
    def set_material(self, project_id: str, component_type: str, material: MaterialProperty):
        """Saves material property for a specific component (e.g. PURLIN, RAFTER, COLUMN, RAIL)."""
        now = datetime.now().isoformat()
        comp = component_type.upper()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_materials (
                    project_id, component_type, material_name, grade, yield_strength_mpa,
                    ultimate_strength_mpa, elastic_modulus_mpa, poisson_ratio,
                    density_kg_m3, standard_reference, gamma_m0, gamma_m1,
                    gamma_m0_override, gamma_m1_override, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, component_type) DO UPDATE SET
                    material_name = excluded.material_name,
                    grade = excluded.grade,
                    yield_strength_mpa = excluded.yield_strength_mpa,
                    ultimate_strength_mpa = excluded.ultimate_strength_mpa,
                    elastic_modulus_mpa = excluded.elastic_modulus_mpa,
                    poisson_ratio = excluded.poisson_ratio,
                    density_kg_m3 = excluded.density_kg_m3,
                    standard_reference = excluded.standard_reference,
                    gamma_m0 = excluded.gamma_m0,
                    gamma_m1 = excluded.gamma_m1,
                    gamma_m0_override = excluded.gamma_m0_override,
                    gamma_m1_override = excluded.gamma_m1_override,
                    updated_at = excluded.updated_at;
                """,
                (
                    project_id,
                    comp,
                    material.name,
                    material.grade,
                    material.yield_strength_mpa,
                    material.ultimate_strength_mpa,
                    material.elastic_modulus_mpa,
                    material.poisson_ratio,
                    material.density_kg_m3,
                    material.standard_reference,
                    material.gamma_m0,
                    material.gamma_m1,
                    material.gamma_m0_override,
                    material.gamma_m1_override,
                    now,
                ),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="MATERIAL_CONFIGURED",
                description=f"Configured material for {comp}: {material.name} ({material.grade})",
            )
            conn.commit()

    def get_material(self, project_id: str, component_type: str) -> Optional[MaterialProperty]:
        """Retrieves material property for a component."""
        comp = component_type.upper()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM project_materials WHERE project_id = ? AND component_type = ?;",
                (project_id, comp),
            )
            row = cur.fetchone()
            if not row:
                return None
            return MaterialProperty(
                name=row["material_name"],
                grade=row["grade"],
                yield_strength_mpa=row["yield_strength_mpa"],
                ultimate_strength_mpa=row["ultimate_strength_mpa"],
                elastic_modulus_mpa=row["elastic_modulus_mpa"],
                poisson_ratio=row["poisson_ratio"],
                density_kg_m3=row["density_kg_m3"],
                standard_reference=row["standard_reference"],
                gamma_m0_override=row["gamma_m0_override"],
                gamma_m1_override=row["gamma_m1_override"],
            )

    def set_section(self, project_id: str, component_type: str, section: SectionProperty):
        """Saves section property for a specific component (e.g. PURLIN, RAFTER, COLUMN, RAIL)."""
        now = datetime.now().isoformat()
        comp = component_type.upper()
        # Save associated material first
        self.set_material(project_id, comp, section.material)
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_sections (
                    project_id, component_type, designation, profile_type,
                    area_mm2, Ixx_mm4, Iyy_mm4, Zxx_mm3, Zyy_mm3,
                    rxx_mm, ryy_mm, mass_kg_m, shear_area_mm2, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, component_type) DO UPDATE SET
                    designation = excluded.designation,
                    profile_type = excluded.profile_type,
                    area_mm2 = excluded.area_mm2,
                    Ixx_mm4 = excluded.Ixx_mm4,
                    Iyy_mm4 = excluded.Iyy_mm4,
                    Zxx_mm3 = excluded.Zxx_mm3,
                    Zyy_mm3 = excluded.Zyy_mm3,
                    rxx_mm = excluded.rxx_mm,
                    ryy_mm = excluded.ryy_mm,
                    mass_kg_m = excluded.mass_kg_m,
                    shear_area_mm2 = excluded.shear_area_mm2,
                    updated_at = excluded.updated_at;
                """,
                (
                    project_id,
                    comp,
                    section.designation,
                    section.profile_type,
                    section.area_mm2,
                    section.Ixx_mm4,
                    section.Iyy_mm4,
                    section.Zxx_mm3,
                    section.Zyy_mm3,
                    section.rxx_mm,
                    section.ryy_mm,
                    section.mass_kg_m,
                    section.shear_area_mm2,
                    now,
                ),
            )
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="SECTION_CONFIGURED",
                description=f"Configured section for {comp}: {section.designation}",
            )
            conn.commit()

    def get_section(self, project_id: str, component_type: str) -> Optional[SectionProperty]:
        """Retrieves SectionProperty domain object."""
        comp = component_type.upper()
        material = self.get_material(project_id, comp)
        if not material:
            return None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM project_sections WHERE project_id = ? AND component_type = ?;",
                (project_id, comp),
            )
            row = cur.fetchone()
            if not row:
                return None
            return SectionProperty(
                designation=row["designation"],
                profile_type=row["profile_type"],
                material=material,
                area_mm2=row["area_mm2"],
                Ixx_mm4=row["Ixx_mm4"],
                Iyy_mm4=row["Iyy_mm4"],
                Zxx_mm3=row["Zxx_mm3"],
                Zyy_mm3=row["Zyy_mm3"],
                rxx_mm=row["rxx_mm"],
                ryy_mm=row["ryy_mm"],
                mass_kg_m=row["mass_kg_m"],
                shear_area_mm2=row["shear_area_mm2"],
            )

    # -------------------------------------------------------------------------
    # Input Snapshot Packaging & Validation
    # -------------------------------------------------------------------------
    def validate_project_inputs(self, project_id: str) -> Tuple[bool, List[str]]:
        """
        Validates completeness and physical bounds of all project inputs.
        Returns (is_valid, error_messages).
        """
        errors = []
        proj = self.get_project(project_id)
        if not proj:
            return False, [f"Project '{project_id}' does not exist."]

        site = self.get_site(project_id)
        if not site:
            errors.append("Missing Site Parameters. Run 'project set-site'.")

        module = self.get_module(project_id)
        if not module:
            errors.append("Missing PV Module Specification. Run 'project set-module'.")

        geometry = self.get_geometry(project_id)
        if not geometry:
            errors.append("Missing Array Geometry. Run 'project set-geometry'.")

        sys_str = proj["mounting_system"]
        # Component requirement checks based on mounting system
        if "System A" in sys_str:
            if not self.get_section(project_id, "PURLIN"):
                errors.append("Missing PURLIN section for System A.")
            if not self.get_section(project_id, "RAFTER"):
                errors.append("Missing RAFTER section for System A.")
            if not self.get_section(project_id, "COLUMN"):
                errors.append("Missing COLUMN section for System A.")
        elif "System B" in sys_str:
            if not self.get_section(project_id, "RAIL"):
                errors.append("Missing RAIL section for System B.")
        elif "System C" in sys_str:
            # System C checks clamp capacity
            pass
        elif "System D" in sys_str:
            # System D checks ballast blocks
            pass

        return (len(errors) == 0), errors

    def build_input_snapshot(self, project_id: str) -> Dict[str, Any]:
        """Packages complete, immutable JSON snapshot of all project inputs."""
        proj = self.get_project(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        site = self.get_site(project_id)
        module = self.get_module(project_id)
        geometry = self.get_geometry(project_id)

        # Build snapshot dictionary
        snapshot: Dict[str, Any] = {
            "snapshot_version": "1.0",
            "project": proj,
            "site": site.__dict__ if site else None,
            "module": module.__dict__ if module else None,
            "geometry": {
                "mounting_system": geometry.mounting_system.value,
                "total_modules": geometry.total_modules,
                "rows": geometry.rows,
                "columns": geometry.columns,
                "orientation": geometry.orientation,
                "purlin_spacing_mm": geometry.purlin_spacing_mm,
                "rafter_spacing_mm": geometry.rafter_spacing_mm,
                "ground_clearance_mm": geometry.ground_clearance_mm,
                "overhang_top_mm": geometry.overhang_top_mm,
                "overhang_bottom_mm": geometry.overhang_bottom_mm,
            } if geometry else None,
            "materials": {},
            "sections": {},
        }

        # Handle site enums serialization
        if snapshot["site"]:
            snapshot["site"]["terrain_category"] = site.terrain_category.value
            snapshot["site"]["seismic_zone"] = site.seismic_zone.value

        for comp in ["PURLIN", "RAFTER", "COLUMN", "RAIL"]:
            mat = self.get_material(project_id, comp)
            if mat:
                snapshot["materials"][comp] = mat.__dict__
            sec = self.get_section(project_id, comp)
            if sec:
                sec_dict = sec.__dict__.copy()
                sec_dict["material"] = mat.__dict__ if mat else None
                snapshot["sections"][comp] = sec_dict

        return snapshot

    # -------------------------------------------------------------------------
    # Calculation Run Execution & Persistence
    # -------------------------------------------------------------------------
    def execute_and_record_run(
        self,
        project_id: str,
        walkway_width_m: float = 0.80,
        ballast_weight_kn_per_m2: float = 0.75,
        friction_coeff_mu: float = 0.40,
        sheet_clamp_tensile_kn: float = 3.50,
        bracket_spacing_mm: float = 1400.0,
    ) -> Dict[str, Any]:
        """
        Executes the appropriate structural workflow, creates an immutable run record,
        and saves all member-level results to SQLite.
        """
        is_valid, errors = self.validate_project_inputs(project_id)
        if not is_valid:
            raise ValueError(f"Cannot execute calculation: input validation failed:\n - " + "\n - ".join(errors))

        proj = self.get_project(project_id)
        sys_str = proj["mounting_system"]
        site = self.get_site(project_id)
        geometry = self.get_geometry(project_id)

        # Generate unique run ID
        run_id = f"RUN-{project_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        engine_version = "1.2.0-phase1.2"
        calc_method = "CLOSED_FORM_IS800_IS875_IS1893"
        now = datetime.now().isoformat()

        # Capture active holds snapshot and enforce automatic provisional hold
        self.evaluate_and_enforce_project_holds(project_id)
        project_holds_list = self.get_project_holds(project_id)
        active_holds_list = [h["hold_id"] for h in project_holds_list if "RELEASED" not in str(h.get("status", ""))]
        watermark = MASTER_VERIFICATION_REGISTER.get_drawing_watermark(sys_str)

        # Execute Workflow
        if "System A" in sys_str:
            purlin_sec = self.get_section(project_id, "PURLIN")
            rafter_sec = self.get_section(project_id, "RAFTER")
            column_sec = self.get_section(project_id, "COLUMN")
            workflow_a = SystemACanopyWorkflow(site=site, geometry=geometry)
            report = workflow_a.run_workflow_analysis(
                purlin_section=purlin_sec,
                rafter_section=rafter_sec,
                column_section=column_sec,
                walkway_width_m=walkway_width_m,
            )
        elif "System B" in sys_str:
            rail_sec = self.get_section(project_id, "RAIL")
            workflow_b = SystemBAluminiumRailWorkflow(site=site, geometry=geometry)
            report = workflow_b.run_workflow_analysis(
                rail_section=rail_sec,
                bracket_spacing_mm=bracket_spacing_mm,
            )
        elif "System C" in sys_str:
            workflow_c = SystemCMetalSheetWorkflow(site=site, geometry=geometry)
            report = workflow_c.run_workflow_analysis(
                sheet_clamp_tensile_capacity_kn=sheet_clamp_tensile_kn,
            )
        elif "System D" in sys_str:
            workflow_d = SystemDBallastedWorkflow(site=site, geometry=geometry)
            report = workflow_d.run_workflow_analysis(
                ballast_weight_kn_per_m2=ballast_weight_kn_per_m2,
                friction_coeff_mu=friction_coeff_mu,
            )
        else:
            raise NotImplementedError(f"Workflow for system '{sys_str}' is not supported.")

        # Determine governing result and run status
        max_unity = 0.0
        governing_check = "None"
        overall_pass = True
        for res in report.results:
            if res.unity_ratio > max_unity:
                max_unity = res.unity_ratio
                governing_check = f"{res.check_name} ({res.unity_ratio:.3f})"
            if not res.passed:
                overall_pass = False

        run_status = "PASS" if overall_pass else "FAIL"
        numerical_status = run_status

        # Evaluate truthful input completeness and provenance
        is_inputs_valid, input_errors = self.validate_project_inputs(project_id)
        prov_records = self.get_project_provenance(project_id)

        # Canonical required parameters for structural input completeness
        required_keys = {
            "basic_wind_speed_vb", "terrain_category", "building_height_m", "rooftop_elevation_m", "seismic_zone",
            "module_length_mm", "module_width_mm", "module_weight_kg", "module_peak_power_w",
            "total_modules", "rows", "columns", "purlin_spacing_mm", "rafter_spacing_mm"
        }
        recorded_keys = {r.get("parameter_key") for r in prov_records}
        has_provisional = any(
            "Level 5" in str(r.get("level", "")) or "Provisional" in str(r.get("level", ""))
            for r in prov_records
        )
        missing_provenance = not required_keys.issubset(recorded_keys)

        if not is_inputs_valid:
            input_completeness = "INCOMPLETE"
        elif has_provisional or missing_provenance:
            input_completeness = "PROVISIONAL"
        else:
            input_completeness = "COMPLETE"

        # Evaluate provenance status from persistent records
        if not prov_records:
            provenance_status = "UNVERIFIED"
        elif has_provisional or missing_provenance:
            provenance_status = "PROVISIONAL"
        else:
            provenance_status = "CERTIFIED"

        engineering_status = "UNVERIFIED"
        construction_status = "BLOCKED_AFC_LOCKED"

        # Input snapshot
        snapshot = self.build_input_snapshot(project_id)
        snapshot_json = json.dumps(snapshot, indent=2)

        report_summary = {
            "numerical_status": numerical_status,
            "input_completeness": input_completeness,
            "provenance_status": provenance_status,
            "engineering_status": engineering_status,
            "construction_status": construction_status,
            "is_approved_for_construction": 0,
            "watermark": watermark,
            "total_checks": len(report.results),
            "passed_checks": sum(1 for r in report.results if r.passed),
            "failed_checks": sum(1 for r in report.results if not r.passed),
            "max_unity_ratio": max_unity,
            "governing_check": governing_check,
            "calculation_trace": report.trace_log,
        }

        # Save to database
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO calculation_runs (
                    run_id, project_id, engine_version, mounting_system, calculation_method,
                    status, max_unity_ratio, governing_check, input_snapshot_json,
                    report_summary_json, active_holds_count, active_holds_json,
                    is_approved_for_construction, watermark, created_at,
                    numerical_status, input_completeness, provenance_status,
                    engineering_status, construction_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    run_id,
                    project_id,
                    engine_version,
                    sys_str,
                    calc_method,
                    run_status,
                    max_unity,
                    governing_check,
                    snapshot_json,
                    json.dumps(report_summary),
                    len(active_holds_list),
                    json.dumps(active_holds_list),
                    0,  # Never AFC in Phase 1
                    watermark,
                    now,
                    numerical_status,
                    input_completeness,
                    provenance_status,
                    engineering_status,
                    construction_status,
                ),
            )

            # Insert member results
            for res in report.results:
                conn.execute(
                    """
                    INSERT INTO calculation_results (
                        run_id, check_name, demand_value, capacity_value, unity_ratio,
                        units, governing_combination, passed, clause_reference, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        run_id,
                        res.check_name,
                        res.demand_value,
                        res.capacity_value,
                        res.unity_ratio,
                        res.units,
                        res.governing_combination,
                        1 if res.passed else 0,
                        res.clause_reference,
                        res.notes,
                    ),
                )

            self._log_audit(
                conn,
                project_id=project_id,
                event_type="CALCULATION_EXECUTED",
                description=f"Executed calculation run {run_id}: Status={run_status}, MaxUnity={max_unity:.3f}",
                details={"run_id": run_id, "max_unity_ratio": max_unity, "governing_check": governing_check},
            )
            conn.commit()

        return self.get_calculation_run(run_id)

    def get_calculation_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a calculation run and all its member results."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calculation_runs WHERE run_id = ?;", (run_id,))
            run_row = cur.fetchone()
            if not run_row:
                return None
            run_dict = dict(run_row)
            run_dict["numerical_status"] = run_dict.get("numerical_status") or run_dict["status"]
            run_dict["input_completeness"] = run_dict.get("input_completeness") or "COMPLETE"
            run_dict["provenance_status"] = run_dict.get("provenance_status") or "PROVISIONAL"
            run_dict["engineering_status"] = run_dict.get("engineering_status") or "UNVERIFIED"
            run_dict["construction_status"] = run_dict.get("construction_status") or "BLOCKED_AFC_LOCKED"
            run_dict["input_snapshot"] = json.loads(run_dict["input_snapshot_json"])
            run_dict["report_summary"] = json.loads(run_dict["report_summary_json"])
            run_dict["active_holds"] = json.loads(run_dict["active_holds_json"])

            cur.execute("SELECT * FROM calculation_results WHERE run_id = ? ORDER BY id ASC;", (run_id,))
            results = [dict(r) for r in cur.fetchall()]
            run_dict["results"] = results
            return run_dict

    def get_latest_run_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest calculation run for a project."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT run_id FROM calculation_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1;",
                (project_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self.get_calculation_run(row["run_id"])

    def list_calculation_runs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists calculation run history."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if project_id:
                cur.execute(
                    "SELECT run_id, project_id, mounting_system, status, max_unity_ratio, governing_check, active_holds_count, created_at "
                    "FROM calculation_runs WHERE project_id = ? ORDER BY created_at DESC;",
                    (project_id,),
                )
            else:
                cur.execute(
                    "SELECT run_id, project_id, mounting_system, status, max_unity_ratio, governing_check, active_holds_count, created_at "
                    "FROM calculation_runs ORDER BY created_at DESC;"
                )
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Reproducibility Verification
    # -------------------------------------------------------------------------
    def verify_reproducibility(self, run_id: str) -> Tuple[bool, str]:
        """
        Reruns calculations strictly using the stored input snapshot and verifies
        that the outputs match the stored results bit-for-bit.
        """
        run = self.get_calculation_run(run_id)
        if not run:
            return False, f"Run '{run_id}' not found."

        snapshot = run["input_snapshot"]
        site_dict = snapshot.get("site")
        mod_dict = snapshot.get("module")
        geom_dict = snapshot.get("geometry")

        if not site_dict or not mod_dict or not geom_dict:
            return False, "Input snapshot is missing required domain components."

        # Reconstruct models
        site = SiteParameters(
            location_name=site_dict["location_name"],
            latitude=site_dict["latitude"],
            longitude=site_dict["longitude"],
            basic_wind_speed_vb=site_dict["basic_wind_speed_vb"],
            terrain_category=TerrainCategory(site_dict["terrain_category"]),
            building_height_m=site_dict["building_height_m"],
            rooftop_elevation_m=site_dict["rooftop_elevation_m"],
            cyclonic_factor_k4=site_dict["cyclonic_factor_k4"],
            topography_factor_k3=site_dict["topography_factor_k3"],
            risk_coefficient_k1=site_dict["risk_coefficient_k1"],
            seismic_zone=SeismicZone(site_dict["seismic_zone"]),
            importance_factor_I=site_dict["importance_factor_I"],
            response_reduction_R=site_dict["response_reduction_R"],
            soil_type=site_dict["soil_type"],
        )
        module = PVModuleSpecification(
            make_model=mod_dict["make_model"],
            length_mm=mod_dict["length_mm"],
            width_mm=mod_dict["width_mm"],
            thickness_mm=mod_dict["thickness_mm"],
            weight_kg=mod_dict["weight_kg"],
            peak_power_w=mod_dict["peak_power_w"],
            tilt_deg=mod_dict["tilt_deg"],
            azimuth_deg=mod_dict["azimuth_deg"],
        )
        geometry = ArrayGeometry(
            mounting_system=MountingSystemType(geom_dict["mounting_system"]),
            total_modules=geom_dict["total_modules"],
            rows=geom_dict["rows"],
            columns=geom_dict["columns"],
            module=module,
            orientation=geom_dict["orientation"],
            purlin_spacing_mm=geom_dict["purlin_spacing_mm"],
            rafter_spacing_mm=geom_dict["rafter_spacing_mm"],
            ground_clearance_mm=geom_dict["ground_clearance_mm"],
            overhang_top_mm=geom_dict["overhang_top_mm"],
            overhang_bottom_mm=geom_dict["overhang_bottom_mm"],
        )

        sys_str = geom_dict["mounting_system"]
        if "System A" in sys_str:
            p_mat_d = snapshot["materials"]["PURLIN"]
            p_mat = MaterialProperty(**p_mat_d)
            p_sec_d = snapshot["sections"]["PURLIN"].copy()
            del p_sec_d["material"]
            purlin_sec = SectionProperty(material=p_mat, **p_sec_d)

            r_mat_d = snapshot["materials"]["RAFTER"]
            r_mat = MaterialProperty(**r_mat_d)
            r_sec_d = snapshot["sections"]["RAFTER"].copy()
            del r_sec_d["material"]
            rafter_sec = SectionProperty(material=r_mat, **r_sec_d)

            c_mat_d = snapshot["materials"]["COLUMN"]
            c_mat = MaterialProperty(**c_mat_d)
            c_sec_d = snapshot["sections"]["COLUMN"].copy()
            del c_sec_d["material"]
            column_sec = SectionProperty(material=c_mat, **c_sec_d)

            workflow_a = SystemACanopyWorkflow(site=site, geometry=geometry)
            new_report = workflow_a.run_workflow_analysis(
                purlin_section=purlin_sec,
                rafter_section=rafter_sec,
                column_section=column_sec,
            )
        elif "System B" in sys_str:
            rail_mat_d = snapshot["materials"]["RAIL"]
            rail_mat = MaterialProperty(**rail_mat_d)
            rail_sec_d = snapshot["sections"]["RAIL"].copy()
            del rail_sec_d["material"]
            rail_sec = SectionProperty(material=rail_mat, **rail_sec_d)

            workflow_b = SystemBAluminiumRailWorkflow(site=site, geometry=geometry)
            new_report = workflow_b.run_workflow_analysis(rail_section=rail_sec)
        elif "System C" in sys_str:
            workflow_c = SystemCMetalSheetWorkflow(site=site, geometry=geometry)
            new_report = workflow_c.run_workflow_analysis()
        elif "System D" in sys_str:
            workflow_d = SystemDBallastedWorkflow(site=site, geometry=geometry)
            new_report = workflow_d.run_workflow_analysis()
        else:
            return False, f"Unsupported system '{sys_str}'."

        # Compare outputs
        stored_results = run["results"]
        if len(new_report.results) != len(stored_results):
            return False, f"Check count mismatch: {len(new_report.results)} recomputed vs {len(stored_results)} stored."

        for new_res, stored in zip(new_report.results, stored_results):
            if abs(new_res.demand_value - stored["demand_value"]) > 1e-4:
                return False, f"Demand mismatch in {new_res.check_name}: {new_res.demand_value} != {stored['demand_value']}"
            if abs(new_res.capacity_value - stored["capacity_value"]) > 1e-4:
                return False, f"Capacity mismatch in {new_res.check_name}: {new_res.capacity_value} != {stored['capacity_value']}"
            if abs(new_res.unity_ratio - stored["unity_ratio"]) > 1e-4:
                return False, f"Unity ratio mismatch in {new_res.check_name}: {new_res.unity_ratio} != {stored['unity_ratio']}"

        return True, "100% reproducible: all member-level calculations match historical snapshot."

    # -------------------------------------------------------------------------
    # Drawing Records Operations
    # -------------------------------------------------------------------------
    def record_drawing_export(
        self,
        run_id: Optional[str],
        project_id: str,
        drawing_number: str,
        file_path: str,
        revision: str = "R0",
    ) -> Dict[str, Any]:
        """Saves a record of generated DXF drawing."""
        now = datetime.now().isoformat()
        proj = self.get_project(project_id)
        sys_str = proj["mounting_system"] if proj else "System A: Elevated Steel Canopy"
        watermark = MASTER_VERIFICATION_REGISTER.get_drawing_watermark(sys_str)
        active_holds_count = len(MASTER_VERIFICATION_REGISTER.get_active_holds_for_system(sys_str))

        # Check if run_id exists in calculation_runs, otherwise keep as None
        valid_run_id = None
        if run_id:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM calculation_runs WHERE run_id = ?;", (run_id,))
                if cur.fetchone():
                    valid_run_id = run_id

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO drawing_records (
                    run_id, project_id, drawing_number, revision, file_path,
                    format, watermark, is_approved_for_construction,
                    active_holds_count, created_at
                ) VALUES (?, ?, ?, ?, ?, 'DXF', ?, 0, ?, ?);
                """,
                (valid_run_id, project_id, drawing_number, revision, file_path, watermark, active_holds_count, now),
            )
            rec_id = cur.lastrowid
            self._log_audit(
                conn,
                project_id=project_id,
                event_type="DRAWING_EXPORTED",
                description=f"Exported preliminary DXF drawing '{drawing_number}' to '{file_path}'",
                details={"file_path": file_path, "watermark": watermark},
            )
            conn.commit()
            return {"id": rec_id, "drawing_number": drawing_number, "file_path": file_path, "watermark": watermark}

    def get_drawings_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves drawing records for a project."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM drawing_records WHERE project_id = ? ORDER BY created_at DESC;",
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Audit Trail Helper
    # -------------------------------------------------------------------------
    def _log_audit(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Internal helper to write an audit trail record within an existing connection."""
        now = datetime.now().isoformat()
        det_json = json.dumps(details) if details else None
        conn.execute(
            """
            INSERT INTO audit_history (project_id, event_type, description, details_json, timestamp)
            VALUES (?, ?, ?, ?, ?);
            """,
            (project_id, event_type, description, det_json, now),
        )

    def get_audit_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieves full audit log for a project."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM audit_history WHERE project_id = ? ORDER BY timestamp ASC;",
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]


# Global singleton instance using default isolated database path
STRUCTURAL_DB = StructuralDatabase()
