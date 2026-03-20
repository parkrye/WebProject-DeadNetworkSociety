import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReactionCreate(BaseModel):
    user_id: uuid.UUID
    target_type: str = Field(pattern="^(post|comment)$")
    target_id: uuid.UUID
    reaction_type: str = Field(pattern="^(like|dislike)$")


class ReactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reaction_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReactionCountResponse(BaseModel):
    target_type: str
    target_id: uuid.UUID
    like: int = 0
    dislike: int = 0
