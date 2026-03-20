import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from src.shared.database import engine, async_session_factory
from src.shared.base_model import Base  # noqa: F401
from src.domains.user.router import router as user_router
from src.domains.post.router import router as post_router
from src.domains.comment.router import router as comment_router
from src.domains.reaction.router import router as reaction_router
from src.domains.agent.router import router as agent_router
from src.domains.agent.bootstrap import start_agent_system
from src.domains.agent.content_generator import ContentGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    content_generator = ContentGenerator(
        base_url=settings.ollama_base_url,
        default_model=settings.ollama_default_model,
    )

    scheduler_task = await start_agent_system(async_session_factory, content_generator)

    yield

    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        logger.info("Agent scheduler stopped")
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_router)
    app.include_router(post_router)
    app.include_router(comment_router)
    app.include_router(reaction_router)
    app.include_router(agent_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
