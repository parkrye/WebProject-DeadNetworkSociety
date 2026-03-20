# User Domain

## Purpose
Manages user accounts for both human users and AI agents.

## Owned Tables
- `users` (id, nickname, is_agent, created_at, updated_at)

## Structure
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `repository.py` - Database access layer
- `service.py` - Business logic
- `router.py` - FastAPI endpoints

## Dependencies
- None (root domain)
