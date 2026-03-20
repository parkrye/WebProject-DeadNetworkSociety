import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class PostCreated(DomainEvent):
    post_id: uuid.UUID = field(default_factory=uuid.uuid4)
    author_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class CommentCreated(DomainEvent):
    comment_id: uuid.UUID = field(default_factory=uuid.uuid4)
    post_id: uuid.UUID = field(default_factory=uuid.uuid4)
    author_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True)
class ReactionCreated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_type: str = ""
    target_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reaction_type: str = ""
