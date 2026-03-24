"""Bootstrap knowledge graphs: parallel web search per persona to build initial knowledge."""
import asyncio
import json
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.agent.knowledge_graph import KnowledgeGraphRepository
from src.domains.agent.live_search import LiveSearchProvider
from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.user.repository import UserRepository

logger = logging.getLogger(__name__)

MAX_CONCURRENT_SEARCHES = 10
BOOTSTRAP_WEIGHT = 0.5  # Lighter than runtime edges — foundation knowledge

_KOREAN_WORD_RE = re.compile(r'[가-힣]{2,}')


def _extract_keywords_from_text(text: str, limit: int = 5) -> list[str]:
    """Extract meaningful Korean words from text."""
    stop = {"있는", "없는", "하는", "되는", "합니다", "입니다", "그리고", "하지만", "그래서", "때문에"}
    words = _KOREAN_WORD_RE.findall(text)
    seen: list[str] = []
    for w in words:
        if w not in stop and w not in seen and len(w) >= 2:
            seen.append(w)
            if len(seen) >= limit:
                break
    return seen


async def _bootstrap_single_persona(
    session: AsyncSession,
    persona: Persona,
    user_id: uuid.UUID,
    searcher: LiveSearchProvider,
) -> int:
    """Search the web for a persona's topics and build initial knowledge edges."""
    kg = KnowledgeGraphRepository(session)

    # Check if already bootstrapped (has any edges)
    edge_count = await kg.get_edge_count(user_id)
    if edge_count > 0:
        return 0

    all_keywords: list[str] = list(persona.topics)
    edges_created = 0

    # Search for each topic (max 3)
    for topic in persona.topics[:3]:
        try:
            results = await searcher.search([topic], max_total=3)
            for r in results:
                text = f"{r.title} {r.snippet}"
                extracted = _extract_keywords_from_text(text, limit=3)
                # Connect topic with extracted keywords
                topic_keywords = [topic] + extracted
                if len(topic_keywords) >= 2:
                    await kg.strengthen_edges(user_id, topic_keywords, weight_delta=BOOTSTRAP_WEIGHT, relation="related")
                    edges_created += len(topic_keywords) - 1

                # Collect for cross-topic connections
                all_keywords.extend(extracted)
        except Exception:
            continue

    # Connect persona's own topics together
    if len(persona.topics) >= 2:
        await kg.strengthen_edges(user_id, persona.topics, weight_delta=BOOTSTRAP_WEIGHT, relation="related")
        edges_created += len(persona.topics) - 1

    await session.flush()
    return edges_created


async def bootstrap_knowledge_graphs(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Bootstrap knowledge graphs for all personas via parallel web search."""
    personas = load_all_personas()
    if not personas:
        return

    searcher = LiveSearchProvider()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)

    total_edges = 0
    bootstrapped = 0

    async def process_persona(persona: Persona) -> int:
        async with semaphore:
            async with session_factory() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_nickname(persona.nickname)
                if not user:
                    return 0
                edges = await _bootstrap_single_persona(session, persona, user.id, searcher)
                await session.commit()
                return edges

    # Process all personas concurrently (bounded by semaphore)
    tasks = [process_persona(p) for p in personas]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, int) and r > 0:
            total_edges += r
            bootstrapped += 1

    logger.info(
        "Knowledge bootstrap complete: %d/%d personas, %d total edges created",
        bootstrapped, len(personas), total_edges,
    )
