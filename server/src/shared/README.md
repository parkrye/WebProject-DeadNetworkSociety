# Shared

도메인 간 공유 인프라. 도메인 로직 포함 금지.

## 모듈

| 파일 | 역할 |
|------|------|
| `database.py` | async SQLAlchemy 엔진 + 세션 팩토리 |
| `base_model.py` | Base, TimestampMixin, UUIDPrimaryKeyMixin |
| `event_bus.py` | In-process async pub/sub 이벤트 디스패처 |
| `events.py` | PostCreated, CommentCreated, ReactionCreated |
| `pagination.py` | PaginationParams, PaginatedResult |
