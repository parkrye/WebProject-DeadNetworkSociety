import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TrendingKeywordResponse(BaseModel):
    keyword: str
    count: int

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    author_id: uuid.UUID
    title: str = Field(min_length=1, max_length=30)
    content: str = Field(min_length=1, max_length=140)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=30)
    content: str | None = Field(default=None, min_length=1, max_length=140)


class PostResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostEnrichedResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_nickname: str
    author_avatar_url: str = ""
    title: str
    content: str
    like_count: int
    dislike_count: int
    comment_count: int
    view_count: int = 0
    popularity_score: float | None = None
    created_at: datetime
    updated_at: datetime
