import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentProfileCreate(BaseModel):
    persona_file: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class AgentProfileUpdate(BaseModel):
    is_active: bool | None = None


class AgentProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    persona_file: str
    is_active: bool
    last_action_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
