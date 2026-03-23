import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    post_id: uuid.UUID
    author_id: uuid.UUID
    content: str = Field(min_length=1, max_length=2000)
    parent_id: uuid.UUID | None = None


class CommentUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    parent_id: uuid.UUID | None
    author_id: uuid.UUID
    content: str
    depth: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentEnrichedResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    parent_id: uuid.UUID | None
    author_id: uuid.UUID
    author_nickname: str
    author_avatar_url: str = ""
    content: str
    depth: int
    created_at: datetime
    updated_at: datetime
