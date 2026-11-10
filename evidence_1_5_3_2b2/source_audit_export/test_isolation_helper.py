"""
Test Isolation Architecture and Environment Manager
Package: tests.test_isolation_helper

Enforces complete isolation for test execution:
- Temporary SQLite quotation database with verified schema
- Temporary SQLite structural database with verified schema and migrations
- Temporary owner settings file
- Temporary generated drawings directory
- Temporary generated quotations PDF directory
- Safe redirection and cleanup of global singletons and paths
- Explicit assertions guarding production files from any test mutation
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import sqlite3
from typing import Optional, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import quotation.quotation_history as qh
import quotation.settings_manager as sm
import quotation.pdf_generator as pg
from structural.db import StructuralDatabase, DEFAULT_DB_PATH
from structural.integration import STRUCTURAL_BRIDGE

# Production canonical paths to guard
PROD_QUOTATIONS_DB = os.path.abspath(os.path.join(PROJECT_ROOT, "quotations.db"))
PROD_STRUCTURAL_DB = os.path.abspath(DEFAULT_DB_PATH)
PROD_SETTINGS_FILE = os.path.abspath(os.path.join(PROJECT_ROOT, "quotation_settings.json"))
PROD_DRAWINGS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "generated_drawings"))
PROD_PDF_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "generated_quotations"))


def get_file_sha256(path: str) -> Optional[str]:
    """Calculates SHA-256 checksum of a file if it exists."""
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ConnectionAuditor:
    """
    Test-only instrumentation that intercepts sqlite3.connect calls during
    isolated test execution, tracking all connection targets and strictly
    blocking any attempt to open production databases.
    """

    def __init__(self, allowed_tmp_dir: str, blocked_production_paths: list):
        self.allowed_tmp_dir = os.path.abspath(allowed_tmp_dir)
        self.blocked_production_paths = [os.path.abspath(p) for p in blocked_production_paths]
        self.connection_attempts = []
        self.rejected_attempts = []
        self._orig_connect = sqlite3.connect

    def intercept_connect(self, database, *args, **kwargs):
        # Allow special in-memory databases
        if database != ":memory:" and not (isinstance(database, str) and database.startswith("file::memory:")):
            try:
                abs_db_path = os.path.abspath(database)
            except Exception:
                abs_db_path = str(database)

            self.connection_attempts.append(abs_db_path)

            # Reject if matches any blocked production path
            for blocked in self.blocked_production_paths:
                if abs_db_path == blocked:
                    self.rejected_attempts.append(abs_db_path)
                    raise RuntimeError(
                        f"CRITICAL TEST ISOLATION VIOLATION: Intercepted and blocked direct connection to production database: {abs_db_path}"
                    )
        return self._orig_connect(database, *args, **kwargs)


class IsolatedTestEnvironment:
    """
    Context manager providing a completely hermetic filesystem and database
    sandbox for integration, API, and unit tests.
    """

    def __init__(self, copy_production_settings: bool = True):
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="rensun_test_iso_")
        self.tmp_path = self.tmp_dir.name

        # 1. Isolated temporary quotations database
        self.quotations_db_path = os.path.join(self.tmp_path, "quotations.db")

        # 2. Isolated temporary structural database
        self.structural_db_path = os.path.join(self.tmp_path, "structural_runs.db")
        self.structural_db = StructuralDatabase(db_path=self.structural_db_path)

        # 3. Isolated temporary owner settings
        self.settings_path = os.path.join(self.tmp_path, "quotation_settings.json")
        self.copy_settings = copy_production_settings

        # 4. Isolated temporary drawings output directory
        self.drawings_dir = os.path.join(self.tmp_path, "generated_drawings")
        os.makedirs(self.drawings_dir, exist_ok=True)

        # 5. Isolated temporary quotation PDF output directory
        self.pdf_dir = os.path.join(self.tmp_path, "generated_quotations")
        os.makedirs(self.pdf_dir, exist_ok=True)

        # Store pre-test production checksums & directory states
        self.pre_prod_quotations_sha = get_file_sha256(PROD_QUOTATIONS_DB)
        self.pre_prod_structural_sha = get_file_sha256(PROD_STRUCTURAL_DB)
        self.pre_prod_settings_sha = get_file_sha256(PROD_SETTINGS_FILE)
        self.pre_prod_drawings_files = set(os.listdir(PROD_DRAWINGS_DIR)) if os.path.exists(PROD_DRAWINGS_DIR) else set()
        self.pre_prod_pdf_files = set(os.listdir(PROD_PDF_DIR)) if os.path.exists(PROD_PDF_DIR) else set()

        # Instrumentation for sqlite3.connect interception
        self.auditor = ConnectionAuditor(
            allowed_tmp_dir=self.tmp_path,
            blocked_production_paths=[PROD_QUOTATIONS_DB, PROD_STRUCTURAL_DB],
        )

        # Save original runtime bindings
        self._orig_qh_db_path = qh.DB_PATH
        self._orig_sm_settings_file = sm.SETTINGS_FILE
        self._orig_pg_output_pdf_dir = pg.OUTPUT_PDF_DIR
        self._orig_bridge_db = STRUCTURAL_BRIDGE.db
        self._orig_bridge_drawings_dir = getattr(STRUCTURAL_BRIDGE, "drawing_output_dir", None)

    def activate(self):
        """Activates path and singleton redirection and connection interception."""
        # Enable connection interception
        sqlite3.connect = self.auditor.intercept_connect

        # Setup quotations schema
        qh.DB_PATH = self.quotations_db_path
        qh.init_db()

        # Setup structural schema
        self.structural_db.init_db()
        STRUCTURAL_BRIDGE.set_db(self.structural_db)
        STRUCTURAL_BRIDGE.set_drawing_output_dir(self.drawings_dir)

        # Setup settings
        if self.copy_settings and os.path.exists(PROD_SETTINGS_FILE):
            shutil.copy2(PROD_SETTINGS_FILE, self.settings_path)
        else:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump({"admin_pin": "admin123", "company_name": "RENSUN SOLAR TEST"}, f)
        sm.SETTINGS_FILE = self.settings_path

        # Setup PDF directory
        pg.OUTPUT_PDF_DIR = self.pdf_dir

    def deactivate(self, verify_production_non_interference: bool = True):
        """Restores original runtime bindings and verifies production files were untouched."""
        # Restore original connection handler first
        sqlite3.connect = self.auditor._orig_connect

        # Restore original bindings
        qh.DB_PATH = self._orig_qh_db_path
        sm.SETTINGS_FILE = self._orig_sm_settings_file
        pg.OUTPUT_PDF_DIR = self._orig_pg_output_pdf_dir
        STRUCTURAL_BRIDGE.set_db(self._orig_bridge_db)
        STRUCTURAL_BRIDGE.set_drawing_output_dir(self._orig_bridge_drawings_dir)

        # Verify production non-interference
        if verify_production_non_interference:
            post_prod_quotations_sha = get_file_sha256(PROD_QUOTATIONS_DB)
            post_prod_structural_sha = get_file_sha256(PROD_STRUCTURAL_DB)
            post_prod_settings_sha = get_file_sha256(PROD_SETTINGS_FILE)

            if self.pre_prod_quotations_sha != post_prod_quotations_sha:
                raise RuntimeError(
                    f"TEST ISOLATION VIOLATION: Production quotations.db modified during test execution! "
                    f"Pre: {self.pre_prod_quotations_sha}, Post: {post_prod_quotations_sha}"
                )
            if self.pre_prod_structural_sha != post_prod_structural_sha:
                raise RuntimeError(
                    f"TEST ISOLATION VIOLATION: Production structural_runs.db modified during test execution! "
                    f"Pre: {self.pre_prod_structural_sha}, Post: {post_prod_structural_sha}"
                )
            if self.pre_prod_settings_sha != post_prod_settings_sha:
                raise RuntimeError(
                    f"TEST ISOLATION VIOLATION: Production quotation_settings.json modified during test execution! "
                    f"Pre: {self.pre_prod_settings_sha}, Post: {post_prod_settings_sha}"
                )

            # Verify no files added to production drawings/PDF directories
            if os.path.exists(PROD_DRAWINGS_DIR):
                post_drawings_files = set(os.listdir(PROD_DRAWINGS_DIR))
                if post_drawings_files != self.pre_prod_drawings_files:
                    diff = post_drawings_files - self.pre_prod_drawings_files
                    raise RuntimeError(f"TEST ISOLATION VIOLATION: Files created in production drawings directory: {diff}")
            if os.path.exists(PROD_PDF_DIR):
                post_pdf_files = set(os.listdir(PROD_PDF_DIR))
                if post_pdf_files != self.pre_prod_pdf_files:
                    diff = post_pdf_files - self.pre_prod_pdf_files
                    raise RuntimeError(f"TEST ISOLATION VIOLATION: Files created in production PDF directory: {diff}")

        # Cleanup temporary files
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate()

    def assert_isolated_paths(self):
        """Explicit assertions proving active runtime paths differ from production."""
        assert os.path.abspath(qh.DB_PATH) != PROD_QUOTATIONS_DB, "Active quotations DB is pointing to production!"
        assert os.path.abspath(self.structural_db.db_path) != PROD_STRUCTURAL_DB, "Active structural DB is pointing to production!"
        assert os.path.abspath(STRUCTURAL_BRIDGE.db.db_path) != PROD_STRUCTURAL_DB, "Active bridge DB is pointing to production!"
        assert os.path.abspath(sm.SETTINGS_FILE) != PROD_SETTINGS_FILE, "Active settings file is pointing to production!"
        assert os.path.abspath(STRUCTURAL_BRIDGE.drawing_output_dir) != PROD_DRAWINGS_DIR, "Active drawings dir is pointing to production!"
        assert os.path.abspath(pg.OUTPUT_PDF_DIR) != PROD_PDF_DIR, "Active PDF dir is pointing to production!"
        assert len(self.auditor.rejected_attempts) == 0, f"Production database connection was attempted and rejected: {self.auditor.rejected_attempts}"
