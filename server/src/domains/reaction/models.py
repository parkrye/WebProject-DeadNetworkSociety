import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, UUIDPrimaryKeyMixin
from src.shared.base_model import _utc_now

from datetime import datetime
from sqlalchemy import DateTime


class Reaction(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_reaction_user_target"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[uuid.UUID] = mapped_column()
    reaction_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
