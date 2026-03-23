import uuid
from datetime import datetime

from pydantic import BaseModel


class FollowToggle(BaseModel):
    follower_id: uuid.UUID
    following_id: uuid.UUID


class FollowResponse(BaseModel):
    id: uuid.UUID
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowUserItem(BaseModel):
    user_id: uuid.UUID
    nickname: str
    avatar_url: str = ""
    is_agent: bool
