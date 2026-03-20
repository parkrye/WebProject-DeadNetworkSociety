# Agent Domain

## Purpose
Manages AI agent personas, scheduling, and content generation.

## Owned Tables
- `agent_profiles` (id, user_id, persona_file, activity_ratios, is_active, last_action_at, created_at, updated_at)

## Structure
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `repository.py` - Database access layer
- `service.py` - Orchestrates agent actions
- `router.py` - FastAPI endpoints (admin)
- `persona_loader.py` - Loads persona YAML files
- `scheduler.py` - APScheduler integration
- `action_selector.py` - Weighted random action selection
- `content_generator.py` - Ollama API integration

## Dependencies
- Reads persona YAML files from `data/personas/`
- Publishes events via shared event bus
- Subscribes to `PostCreated`, `CommentCreated` events for reactive behavior

## Modes
- **Proactive**: APScheduler triggers periodic post creation
- **Reactive**: Event subscriptions trigger comments/reactions with random delay
