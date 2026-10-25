import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.audit import AuditEvent


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AuditService:
    GENESIS_HASH = "0" * 64

    @staticmethod
    def _compute_event_hash(
        sequence_no: int,
        timestamp: datetime,
        actor_id: Optional[str],
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        previous_state: Optional[str],
        new_state: Optional[str],
        details_json: str,
        previous_hash: str
    ) -> str:
        ts = ensure_utc(timestamp)
        canonical = (
            f"{sequence_no}|"
            f"{ts.isoformat()}|"
            f"{actor_id or ''}|"
            f"{actor_role}|"
            f"{action}|"
            f"{entity_type}|"
            f"{entity_id}|"
            f"{previous_state or ''}|"
            f"{new_state or ''}|"
            f"{details_json}|"
            f"{previous_hash}"
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Appends an immutable audit event to the cryptographic hash chain.
        """
        # Fetch the latest audit event
        stmt = select(AuditEvent).order_by(AuditEvent.sequence_no.desc()).limit(1)
        latest = db.execute(stmt).scalar_one_or_none()

        if latest is None:
            sequence_no = 1
            previous_hash = cls.GENESIS_HASH
        else:
            sequence_no = latest.sequence_no + 1
            previous_hash = latest.current_hash

        now = datetime.now(timezone.utc)
        details_json = json.dumps(details or {}, sort_keys=True)

        current_hash = cls._compute_event_hash(
            sequence_no=sequence_no,
            timestamp=now,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_state=previous_state,
            new_state=new_state,
            details_json=details_json,
            previous_hash=previous_hash
        )

        event = AuditEvent(
            sequence_no=sequence_no,
            timestamp=now,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_state=previous_state,
            new_state=new_state,
            details_json=details_json,
            previous_hash=previous_hash,
            current_hash=current_hash
        )
        db.add(event)
        db.flush()
        return event

    @classmethod
    def verify_chain(cls, db: Session) -> Tuple[bool, int, Optional[int], str]:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Returns: (is_valid, total_checked, broken_sequence_no, message)
        """
        stmt = select(AuditEvent).order_by(AuditEvent.sequence_no.asc())
        events = db.execute(stmt).scalars().all()

        if not events:
            return True, 0, None, "Audit log is empty; chain is trivially intact."

        expected_previous_hash = cls.GENESIS_HASH

        for idx, event in enumerate(events, start=1):
            if event.sequence_no != idx:
                return False, len(events), event.sequence_no, f"Sequence gap or alteration detected at sequence {event.sequence_no}."

            if event.previous_hash != expected_previous_hash:
                return False, len(events), event.sequence_no, f"Previous hash mismatch at sequence {event.sequence_no}."

            recomputed_hash = cls._compute_event_hash(
                sequence_no=event.sequence_no,
                timestamp=event.timestamp,
                actor_id=event.actor_id,
                actor_role=event.actor_role,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                previous_state=event.previous_state,
                new_state=event.new_state,
                details_json=event.details_json,
                previous_hash=event.previous_hash
            )

            if event.current_hash != recomputed_hash:
                return False, len(events), event.sequence_no, f"Hash tamper detected at sequence {event.sequence_no}!"

            expected_previous_hash = event.current_hash

        return True, len(events), None, f"All {len(events)} events verified successfully. Hash chain intact."


audit_service = AuditService()
