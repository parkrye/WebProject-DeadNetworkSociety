import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    nickname: str = Field(min_length=2, max_length=50)
    is_agent: bool = False


class UserLogin(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class UserUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=50)
    bio: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    is_agent: bool
    bio: str = ""
    avatar_url: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RankingEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    avatar_url: str = ""
    is_agent: bool
    total_popularity_score: float
    popular_post_count: int


class ActivityItem(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    view_count: int = 0
    created_at: datetime


class UserProfileStats(BaseModel):
    user_id: uuid.UUID
    nickname: str
    bio: str = ""
    avatar_url: str = ""
    is_agent: bool
    post_count: int
    comment_count: int
    likes_given: int
    likes_received: int
    dislikes_given: int
    dislikes_received: int
    followers_count: int = 0
    following_count: int = 0
    best_popular_rank: int | None = None
    total_popularity_score: float = 0.0
    recent_posts: list[ActivityItem]
    recent_comments: list[ActivityItem]
    liked_items: list[ActivityItem]
    disliked_items: list[ActivityItem]
