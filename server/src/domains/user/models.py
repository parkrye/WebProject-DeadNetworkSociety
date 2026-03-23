from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    nickname: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[str] = mapped_column(String(200), default="", server_default="")
    avatar_url: Mapped[str] = mapped_column(String(500), default="", server_default="")
