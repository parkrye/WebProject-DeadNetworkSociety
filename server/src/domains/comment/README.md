# Comment Domain

## Purpose
Manages comments and threaded replies on posts.

## Owned Tables
- `comments` (id, post_id, parent_id, author_id, content, depth, created_at, updated_at)

## Structure
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `repository.py` - Database access layer
- `service.py` - Business logic
- `router.py` - FastAPI endpoints

## Dependencies
- Receives `post_id`, `author_id` (UUIDs) - no direct domain imports
- Publishes `CommentCreated` event via shared event bus
