import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Comment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "comments"

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id"), index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("comments.id"), default=None)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer, default=0)
