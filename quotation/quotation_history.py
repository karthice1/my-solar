"""Quotation History & Version Control: Persistent SQLite Store for Solar Quotations.

Maintains unique quotation IDs (e.g. RENSUN/2026/0001), version trees,
and immutable historical snapshots.
"""

import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quotations.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_no TEXT UNIQUE NOT NULL,
                consumer_no TEXT NOT NULL,
                customer_name TEXT,
                system_capacity_kw REAL,
                net_payable_amount REAL,
                status TEXT NOT NULL DEFAULT 'Draft',
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                pdf_path TEXT,
                data_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotation_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_no TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                pdf_path TEXT,
                data_json TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

def generate_next_quotation_no(prefix: str = "RENSUN") -> str:
    """Generates sequential quotation reference: RENSUN/YYYY/0001."""
    year = datetime.now().year
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE quotation_no LIKE ?", (f"{prefix}/{year}/%",))
        count = cursor.fetchone()[0]
        next_seq = count + 1
        return f"{prefix}/{year}/{next_seq:04d}"

def save_quotation(quotation_data: Dict[str, Any], status: str = "Draft") -> Dict[str, Any]:
    """Saves or updates a quotation in the SQLite database."""
    q_no = quotation_data.get("quotation_no")
    if not q_no:
        q_no = generate_next_quotation_no()
        quotation_data["quotation_no"] = q_no

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quotation_data["updated_at"] = now_iso
    quotation_data["status"] = status

    c_no = str(quotation_data.get("consumer_no") or "")
    c_name = str(quotation_data.get("customer_name") or "")
    cap = float(quotation_data.get("system_capacity_kw") or 0.0)
    net_pay = float(quotation_data.get("pricing", {}).get("net_customer_payable") or 0.0)
    pdf_path = quotation_data.get("pdf_path", "")
    version = int(quotation_data.get("version", 1))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, version, status FROM quotations WHERE quotation_no = ?", (q_no,))
        existing = cursor.fetchone()

        if existing:
            # Updating existing quotation
            curr_version = existing["version"]
            # If current was already finalized or presented, increment version on revision
            if existing["status"] in ("Finalized", "Accepted") and status != existing["status"]:
                curr_version += 1
                quotation_data["version"] = curr_version

            cursor.execute("""
                UPDATE quotations
                SET customer_name = ?, system_capacity_kw = ?, net_payable_amount = ?,
                    status = ?, version = ?, updated_at = ?, pdf_path = ?, data_json = ?
                WHERE quotation_no = ?
            """, (c_name, cap, net_pay, status, curr_version, now_iso, pdf_path, json.dumps(quotation_data), q_no))

            # Record in versions history table
            cursor.execute("""
                INSERT INTO quotation_versions (quotation_no, version, status, created_at, pdf_path, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (q_no, curr_version, status, now_iso, pdf_path, json.dumps(quotation_data)))

        else:
            # Inserting brand new quotation
            quotation_data["created_at"] = now_iso
            quotation_data["version"] = 1
            cursor.execute("""
                INSERT INTO quotations (quotation_no, consumer_no, customer_name, system_capacity_kw,
                                        net_payable_amount, status, version, created_at, updated_at, pdf_path, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (q_no, c_no, c_name, cap, net_pay, status, 1, now_iso, now_iso, pdf_path, json.dumps(quotation_data)))

            cursor.execute("""
                INSERT INTO quotation_versions (quotation_no, version, status, created_at, pdf_path, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (q_no, 1, status, now_iso, pdf_path, json.dumps(quotation_data)))

        conn.commit()

    return quotation_data

def get_quotation(quotation_no: str) -> Optional[Dict[str, Any]]:
    """Retrieves full JSON details for a quotation by its reference number."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM quotations WHERE quotation_no = ?", (quotation_no,))
        row = cursor.fetchone()
        if row:
            return json.loads(row["data_json"])
    return None

def list_quotations(consumer_no: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns list of quotations ordered by last updated descending."""
    with get_db() as conn:
        cursor = conn.cursor()
        if consumer_no:
            cursor.execute("""
                SELECT quotation_no, consumer_no, customer_name, system_capacity_kw,
                       net_payable_amount, status, version, created_at, updated_at, pdf_path
                FROM quotations
                WHERE consumer_no = ?
                ORDER BY updated_at DESC
            """, (consumer_no,))
        else:
            cursor.execute("""
                SELECT quotation_no, consumer_no, customer_name, system_capacity_kw,
                       net_payable_amount, status, version, created_at, updated_at, pdf_path
                FROM quotations
                ORDER BY updated_at DESC
            """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_quotation_versions(quotation_no: str) -> List[Dict[str, Any]]:
    """Returns all historical versions of a quotation."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, quotation_no, version, status, created_at, pdf_path
            FROM quotation_versions
            WHERE quotation_no = ?
            ORDER BY version DESC
        """, (quotation_no,))
        return [dict(r) for r in cursor.fetchall()]

def update_status(quotation_no: str, new_status: str):
    """Updates quotation lifecycle status (e.g. Draft -> Finalized -> Accepted)."""
    valid = ("Draft", "Presented", "Revised", "Finalized", "Accepted", "Rejected", "Expired")
    if new_status not in valid:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid}")
    with get_db() as conn:
        conn.execute("UPDATE quotations SET status = ?, updated_at = ? WHERE quotation_no = ?",
                     (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quotation_no))
        conn.commit()
