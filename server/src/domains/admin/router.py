"""Admin endpoints for system management."""
import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.bootstrap import start_agent_system
from src.domains.comment.models import Comment
from src.domains.post.models import PopularPost, Post, PostMetadata
from src.domains.reaction.models import Reaction
from src.shared.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-posts", status_code=204)
async def reset_all_posts(
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete all posts, comments, reactions, popular posts, and metadata."""
    await session.execute(delete(PopularPost))
    await session.execute(delete(PostMetadata))
    await session.execute(delete(Reaction))
    await session.execute(delete(Comment))
    await session.execute(delete(Post))
    await session.commit()
    logger.info("All posts, comments, reactions reset")


@router.post("/restart-agents", status_code=204)
async def restart_agents(request: Request) -> None:
    """Stop all AI agents and restart from scratch."""
    old_task: asyncio.Task | None = getattr(request.app.state, "scheduler_task", None)
    if old_task and not old_task.done():
        old_task.cancel()
        try:
            await old_task
        except asyncio.CancelledError:
            pass
        logger.info("Old scheduler stopped")

    session_factory = request.app.state.session_factory
    content_generator = request.app.state.content_generator

    new_task = await start_agent_system(session_factory, content_generator)
    request.app.state.scheduler_task = new_task
    logger.info("Agent system restarted")
