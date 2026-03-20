import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    nickname: str = Field(min_length=2, max_length=50)
    is_agent: bool = False


class UserUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=50)


class UserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    is_agent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
