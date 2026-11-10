"""
Data Provenance & Engineering Assumption Tracking Architecture
Package: structural.provenance

Enforces zero-uncertified-assumptions rule (DEC-016).
Every engineering input must carry an identifiable provenance tier.
Any provisional assumption automatically trips ASSUMED_DATA_CERTIFICATION_HOLD.
Durable persistence backed by SQLite database with snapshot versioning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import uuid


class ProvenanceLevel(str, Enum):
    LEVEL_1_MEASURED = "Level 1: Measured On-Site (Physical Inspection / NDT)"
    LEVEL_2_DRAWING_VERIFIED = "Level 2: Drawing Verified (As-Built Signed Structural Records)"
    LEVEL_3_CLIENT_CERTIFIED = "Level 3: Client Certified (Written Form from Host Building Owner)"
    LEVEL_4_STATUTORY_CODE = "Level 4: Statutory Code Value (Published IS Standard Reference)"
    LEVEL_5_ASSUMED_PROVISIONAL = "Level 5: Assumed Provisional (Requires Physical Verification)"


@dataclass
class ProvenanceRecord:
    parameter_key: str
    value: Any
    units: str
    level: ProvenanceLevel
    source_reference: str
    project_id: str = ""
    record_id: str = field(default_factory=lambda: f"PROV-{uuid.uuid4().hex[:8]}")
    certifier_name: Optional[str] = None
    date_certified: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    calculation_run_id: Optional[str] = None
    snapshot_version: int = 1

    def __post_init__(self):
        # Validate certification requirements upon creation
        self.validate_certification()

    def validate_certification(self) -> None:
        """
        Rejects invalid or incomplete certification records.
        A value must NOT be classified as measured or certified merely because
        a user supplied a value without verifiable evidence.
        """
        # Ensure level is an instance of ProvenanceLevel
        if isinstance(self.level, str):
            try:
                self.level = ProvenanceLevel(self.level)
            except ValueError:
                # Try finding matching enum
                matched = False
                for pl in ProvenanceLevel:
                    if pl.name == self.level or pl.value == self.level:
                        self.level = pl
                        matched = True
                        break
                if not matched:
                    raise ValueError(f"Unknown provenance level: {self.level}")

        if self.level == ProvenanceLevel.LEVEL_1_MEASURED:
            if not self.source_reference or not self.source_reference.strip():
                raise ValueError(
                    f"Level 1 (Measured On-Site) requires explicit physical test / inspection evidence for '{self.parameter_key}'."
                )
            if not self.certifier_name and not self.date_certified:
                raise ValueError(
                    f"Level 1 (Measured On-Site) requires certifier identity or inspection date for '{self.parameter_key}'."
                )

        elif self.level == ProvenanceLevel.LEVEL_2_DRAWING_VERIFIED:
            if not self.source_reference or not self.source_reference.strip():
                raise ValueError(
                    f"Level 2 (Drawing Verified) requires signed as-built drawing reference for '{self.parameter_key}'."
                )

        elif self.level == ProvenanceLevel.LEVEL_3_CLIENT_CERTIFIED:
            if not self.certifier_name or not self.certifier_name.strip():
                raise ValueError(
                    f"Level 3 (Client Certified) requires client/owner certifier name for '{self.parameter_key}'."
                )
            if not self.source_reference or not self.source_reference.strip():
                raise ValueError(
                    f"Level 3 (Client Certified) requires written authorization reference for '{self.parameter_key}'."
                )

        elif self.level == ProvenanceLevel.LEVEL_4_STATUTORY_CODE:
            if not self.source_reference or not self.source_reference.strip():
                raise ValueError(
                    f"Level 4 (Statutory Code Value) requires published codal standard and clause for '{self.parameter_key}'."
                )

    @property
    def is_certified(self) -> bool:
        return self.level != ProvenanceLevel.LEVEL_5_ASSUMED_PROVISIONAL


class ProvenanceTracker:
    """
    Tracks the evidence provenance for every design input parameter.
    Supports in-memory tracking as well as persistent SQLite database synchronization.
    """

    def __init__(self, db: Optional[Any] = None, project_id: Optional[str] = None):
        self._records: Dict[str, ProvenanceRecord] = {}
        self.db = db
        self.project_id = project_id
        if self.db and self.project_id:
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Loads existing provenance records from persistent SQLite database."""
        if not self.db or not self.project_id:
            return
        db_records = self.db.get_project_provenance(self.project_id)
        for r in db_records:
            try:
                rec = ProvenanceRecord(
                    record_id=r["record_id"],
                    project_id=r["project_id"],
                    parameter_key=r["parameter_key"],
                    value=r["value"],
                    units=r["units"],
                    level=ProvenanceLevel(r["level"]),
                    source_reference=r["source_reference"],
                    certifier_name=r.get("certifier_name"),
                    date_certified=r.get("date_certified"),
                    notes=r.get("notes", ""),
                    created_at=r.get("created_at", ""),
                    updated_at=r.get("updated_at", ""),
                    calculation_run_id=r.get("calculation_run_id"),
                    snapshot_version=r.get("snapshot_version", 1),
                )
                self._records[r["parameter_key"]] = rec
            except Exception:
                continue

    def record_parameter(
        self,
        parameter_key: str,
        value: Any,
        units: str,
        level: ProvenanceLevel,
        source_reference: str,
        certifier_name: Optional[str] = None,
        date_certified: Optional[str] = None,
        notes: str = "",
        calculation_run_id: Optional[str] = None,
        snapshot_version: int = 1,
    ) -> ProvenanceRecord:
        """
        Records a parameter with strict certification validation.
        Persists directly to SQLite database if db manager is attached.
        """
        rec = ProvenanceRecord(
            project_id=self.project_id or "",
            parameter_key=parameter_key,
            value=value,
            units=units,
            level=level,
            source_reference=source_reference,
            certifier_name=certifier_name,
            date_certified=date_certified,
            notes=notes,
            calculation_run_id=calculation_run_id,
            snapshot_version=snapshot_version,
        )
        self._records[parameter_key] = rec

        if self.db and self.project_id:
            self.db.record_parameter_provenance(
                project_id=self.project_id,
                parameter_key=parameter_key,
                value=str(value),
                units=units,
                level=rec.level.value,
                source_reference=source_reference,
                certifier_name=certifier_name,
                date_certified=date_certified,
                notes=notes,
                calculation_run_id=calculation_run_id,
                snapshot_version=snapshot_version,
            )

        if not rec.is_certified:
            self.enforce_assumed_data_hold()

        return rec

    def get_record(self, parameter_key: str) -> Optional[ProvenanceRecord]:
        return self._records.get(parameter_key)

    def get_all_records(self) -> List[ProvenanceRecord]:
        return list(self._records.values())

    def get_provisional_assumptions(self) -> List[ProvenanceRecord]:
        return [r for r in self._records.values() if not r.is_certified]

    def has_unverified_assumptions(self) -> bool:
        # If no records exist at all, it has unverified assumptions by definition
        if not self._records:
            return True
        return len(self.get_provisional_assumptions()) > 0

    def requires_certification_hold(self) -> bool:
        """Returns True if ASSUMED_DATA_CERTIFICATION_HOLD must remain active."""
        return self.has_unverified_assumptions()

    def enforce_assumed_data_hold(self) -> bool:
        """
        Activates and confirms enforcement of ASSUMED_DATA_CERTIFICATION_HOLD
        in MASTER_VERIFICATION_REGISTER and persists to SQLite project_holds
        whenever provisional assumptions are present.
        """
        from structural.holds import MASTER_VERIFICATION_REGISTER, HoldStatus
        if self.requires_certification_hold():
            hold = MASTER_VERIFICATION_REGISTER.get_hold("ASSUMED_DATA_CERTIFICATION_HOLD")
            if hold:
                hold.status = HoldStatus.ACTIVE_ENFORCED
            if self.db and self.project_id:
                provisional = self.get_provisional_assumptions()
                keys = [p.parameter_key for p in provisional]
                evidence = f"Unverified/provisional inputs: {', '.join(keys)}" if keys else "Missing parameter provenance records."
                self.db.set_project_hold(
                    project_id=self.project_id,
                    hold_id="ASSUMED_DATA_CERTIFICATION_HOLD",
                    status=HoldStatus.ACTIVE_ENFORCED.value,
                    reason="Mandatory SEOR assumption sign-off required for provisional inputs.",
                    evidence_notes=evidence,
                )
            return True
        return False
