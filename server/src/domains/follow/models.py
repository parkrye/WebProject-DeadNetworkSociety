import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, UUIDPrimaryKeyMixin, _utc_now


class Follow(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_pair"),
    )

    follower_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    following_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
