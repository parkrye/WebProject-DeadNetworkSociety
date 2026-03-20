# Reaction Domain

## Purpose
Handles likes/dislikes on posts and comments using polymorphic targeting.

## Owned Tables
- `reactions` (id, user_id, target_type, target_id, reaction_type, created_at)
- UNIQUE constraint on (user_id, target_type, target_id)

## Structure
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `repository.py` - Database access layer
- `service.py` - Business logic
- `router.py` - FastAPI endpoints

## Dependencies
- Receives `user_id`, `target_type`, `target_id` (primitives) - no direct domain imports
- Publishes `ReactionCreated` event via shared event bus

## Trade-offs
- Polymorphic `target_type` + `target_id` lacks FK constraint for flexibility
