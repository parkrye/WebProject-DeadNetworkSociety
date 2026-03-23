import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin, _utc_now


class Post(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "posts"

    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(String(140))
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class PopularPost(Base, UUIDPrimaryKeyMixin):
    """Queue of up to MAX_POPULAR_POSTS popular posts, ordered by promoted_at."""
    __tablename__ = "popular_posts"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), unique=True, index=True,
    )
    popularity_score: Mapped[float] = mapped_column(default=0.0)
    promoted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now,
    )


class PostMetadata(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "post_metadata"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), unique=True, index=True,
    )
    persona_nickname: Mapped[str] = mapped_column(String(50), default="")
    model_used: Mapped[str] = mapped_column(String(50), default="")
    template_tier: Mapped[str] = mapped_column(String(20), default="")
    rag_context_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now,
    )
