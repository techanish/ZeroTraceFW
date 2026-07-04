from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .encryption import EncryptionEngine
from .utils import format_utc, parse_time, utcnow

EventCategory = Literal["auth", "access", "policy", "security", "system"]


@dataclass
class AuditEntry:
    timestamp: str
    event_type: str
    details: str
    filename: str | None = None
    event_category: EventCategory = "system"
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    viewing_duration_seconds: float | None = None
    pages_viewed: int | None = None
    copy_attempt: bool = False
    print_attempt: bool = False
    download_attempt: bool = False
    risk_score: int = 0
    geo_location: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        # Ignore extra fields that might not map to the dataclass
        valid_keys = {f for f in cls.__annotations__.keys()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


class AuditLogger:
    def __init__(self) -> None:
        self.log_entries: list[AuditEntry] = []

    def log_event(
        self,
        event_type: str,
        details: str,
        filename: str | None = None,
        event_category: EventCategory = "system",
        user_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        viewing_duration_seconds: float | None = None,
        pages_viewed: int | None = None,
        copy_attempt: bool = False,
        print_attempt: bool = False,
        download_attempt: bool = False,
        risk_score: int = 0,
        geo_location: str | None = None,
    ) -> dict:
        entry = AuditEntry(
            timestamp=format_utc(utcnow()) or "",
            event_type=str(event_type),
            details=str(details),
            filename=filename,
            event_category=event_category,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            viewing_duration_seconds=viewing_duration_seconds,
            pages_viewed=pages_viewed,
            copy_attempt=copy_attempt,
            print_attempt=print_attempt,
            download_attempt=download_attempt,
            risk_score=risk_score,
            geo_location=geo_location,
        )
        self.log_entries.append(entry)
        return entry.to_dict()

    def get_log(self) -> list[dict]:
        return [entry.to_dict() for entry in self.log_entries]

    def get_recent(self, n: int = 20) -> list[dict]:
        return self.get_log()[-int(n) :]

    def serialize(self) -> dict:
        return {"log_entries": self.get_log()}

    def deserialize(self, data: dict) -> "AuditLogger":
        entries = data.get("log_entries", []) if data else []
        self.log_entries = [AuditEntry.from_dict(e) for e in entries]
        return self

    def clear(self) -> None:
        self.log_entries = []

    def export_encrypted_log(self, output_path: str | Path, vault_key: bytes) -> Path:
        """Encrypts the full audit trail with the vault key for secure export."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        log_json = json.dumps(self.serialize()).encode("utf-8")
        encryption_engine = EncryptionEngine()
        sealed_data = encryption_engine.encrypt(log_json, vault_key)
        
        path.write_bytes(sealed_data)
        return path


class AuditDashboard:
    """Aggregates events, generates reports, and detects anomalies."""

    def __init__(self, logger: AuditLogger) -> None:
        self.logger = logger

    def generate_report(self) -> dict:
        entries = self.logger.log_entries
        total_events = len(entries)
        
        category_counts = {}
        high_risk_events = []
        copy_attempts = 0
        print_attempts = 0
        
        for entry in entries:
            category_counts[entry.event_category] = category_counts.get(entry.event_category, 0) + 1
            if entry.risk_score >= 70:
                high_risk_events.append(entry.to_dict())
            if entry.copy_attempt:
                copy_attempts += 1
            if entry.print_attempt:
                print_attempts += 1
                
        return {
            "total_events": total_events,
            "category_breakdown": category_counts,
            "high_risk_event_count": len(high_risk_events),
            "high_risk_events": high_risk_events,
            "copy_attempts": copy_attempts,
            "print_attempts": print_attempts,
        }

    def detect_anomalies(self) -> list[dict]:
        """Detect potential anomalous behavior based on audit logs."""
        anomalies = []
        entries = self.logger.log_entries
        
        # Example heuristic: multiple high-risk events in a short timeframe
        # Real implementation would use more sophisticated time-window logic
        high_risk_count = sum(1 for e in entries if e.risk_score >= 50)
        if high_risk_count >= 3:
            anomalies.append({
                "type": "multiple_high_risk",
                "severity": "high",
                "description": f"Detected {high_risk_count} high-risk events."
            })
            
        copy_print_count = sum(1 for e in entries if e.copy_attempt or e.print_attempt)
        if copy_print_count > 5:
             anomalies.append({
                "type": "excessive_data_extraction_attempts",
                "severity": "medium",
                "description": f"Detected {copy_print_count} attempts to copy or print protected data."
            })

        return anomalies
