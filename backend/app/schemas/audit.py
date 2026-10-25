from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


class AuditEventResponse(BaseModel):
    id: str
    sequence_no: int
    timestamp: datetime
    actor_id: Optional[str] = None
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    details_json: str
    previous_hash: str
    current_hash: str

    model_config = ConfigDict(from_attributes=True)


class AuditChainVerificationResult(BaseModel):
    is_valid: bool
    total_events_checked: int
    genesis_hash_valid: bool
    broken_sequence_no: Optional[int] = None
    verification_message: str
    checked_at: datetime
