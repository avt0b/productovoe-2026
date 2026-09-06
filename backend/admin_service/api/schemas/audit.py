from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.models import AuditOutcome


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    actor_email: str
    actor_role: str
    action: str
    target_service: str
    target_type: str
    target_id: str
    target_label: str
    outcome: AuditOutcome
    message: str
    payload: dict
    ip: str
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditEntryOut]
    total: int
    limit: int
    offset: int
