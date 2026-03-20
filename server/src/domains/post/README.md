# Post Domain

## Purpose
Handles creation, retrieval, update, and deletion of community posts.

## Owned Tables
- `posts` (id, author_id, title, content, created_at, updated_at)

## Structure
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `repository.py` - Database access layer
- `service.py` - Business logic
- `router.py` - FastAPI endpoints

## Dependencies
- Receives `author_id` (UUID) - no direct import from user domain
- Publishes `PostCreated` event via shared event bus
