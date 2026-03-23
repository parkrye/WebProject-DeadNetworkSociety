import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin, _utc_now


class AgentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    persona_file: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class PersonaState(Base, UUIDPrimaryKeyMixin):
    """Dynamic persona state that evolves during runtime."""
    __tablename__ = "persona_states"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    active_interests: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of current topics
    mood: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")  # -1.0 ~ +1.0
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
