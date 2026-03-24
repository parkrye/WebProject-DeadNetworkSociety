"""Persona knowledge graph: persistent keyword-keyword semantic network.

Each persona builds their own graph as they interact with content.
Edges connect co-occurring keywords with weights that strengthen over time.
"""
import logging
import uuid
from itertools import combinations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.models import KnowledgeEdge

logger = logging.getLogger(__name__)

# Edge weight increments per action type
WEIGHT_POST_AUTHOR = 1.0      # Writing about these topics together
WEIGHT_COMMENT = 0.5           # Commenting on content with these topics
WEIGHT_REACTION_LIKE = 0.3     # Liking content → weaker but positive association
WEIGHT_REACTION_DISLIKE = -0.2  # Disliking → weakens association


class KnowledgeGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def strengthen_edges(
        self,
        persona_id: uuid.UUID,
        keywords: list[str],
        weight_delta: float = 1.0,
        relation: str = "related",
    ) -> None:
        """Connect all keyword pairs in the persona's graph. Strengthens existing edges."""
        if len(keywords) < 2:
            return

        # Normalize and deduplicate
        clean = list(dict.fromkeys(kw.strip().lower() for kw in keywords if kw.strip()))
        if len(clean) < 2:
            return

        for kw_a, kw_b in combinations(clean, 2):
            # Ensure consistent ordering
            kw_from, kw_to = (kw_a, kw_b) if kw_a < kw_b else (kw_b, kw_a)

            existing = await self._session.execute(
                select(KnowledgeEdge).where(
                    KnowledgeEdge.persona_id == persona_id,
                    KnowledgeEdge.keyword_from == kw_from,
                    KnowledgeEdge.keyword_to == kw_to,
                )
            )
            edge = existing.scalar_one_or_none()

            if edge:
                edge.weight = max(0.0, edge.weight + weight_delta)
                if relation != "related" and edge.relation == "related":
                    edge.relation = relation
            else:
                self._session.add(KnowledgeEdge(
                    persona_id=persona_id,
                    keyword_from=kw_from,
                    keyword_to=kw_to,
                    weight=max(0.0, weight_delta),
                    relation=relation,
                ))

        await self._session.flush()

    async def get_related_keywords(
        self, persona_id: uuid.UUID, keyword: str, limit: int = 5,
    ) -> list[tuple[str, float, str]]:
        """Find keywords most strongly connected to the given keyword.
        Returns [(keyword, weight, relation), ...]"""
        kw = keyword.strip().lower()
        stmt = (
            select(KnowledgeEdge.keyword_from, KnowledgeEdge.keyword_to,
                   KnowledgeEdge.weight, KnowledgeEdge.relation)
            .where(
                KnowledgeEdge.persona_id == persona_id,
                (KnowledgeEdge.keyword_from == kw) | (KnowledgeEdge.keyword_to == kw),
                KnowledgeEdge.weight > 0,
            )
            .order_by(KnowledgeEdge.weight.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        related = []
        for row in result.all():
            other = row.keyword_to if row.keyword_from == kw else row.keyword_from
            related.append((other, row.weight, row.relation))
        return related

    async def get_strongest_edges(
        self, persona_id: uuid.UUID, limit: int = 10,
    ) -> list[tuple[str, str, float, str]]:
        """Get the persona's strongest knowledge connections.
        Returns [(keyword_from, keyword_to, weight, relation), ...]"""
        stmt = (
            select(KnowledgeEdge.keyword_from, KnowledgeEdge.keyword_to,
                   KnowledgeEdge.weight, KnowledgeEdge.relation)
            .where(KnowledgeEdge.persona_id == persona_id, KnowledgeEdge.weight > 0)
            .order_by(KnowledgeEdge.weight.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(r.keyword_from, r.keyword_to, r.weight, r.relation) for r in result.all()]

    async def format_for_prompt(self, persona_id: uuid.UUID, seed_keywords: list[str]) -> str:
        """Build a prompt-friendly representation of knowledge around seed keywords."""
        if not seed_keywords:
            return ""

        all_related: dict[str, float] = {}
        for kw in seed_keywords[:3]:
            related = await self.get_related_keywords(persona_id, kw, limit=3)
            for word, weight, _ in related:
                if word not in seed_keywords:
                    all_related[word] = all_related.get(word, 0) + weight

        if not all_related:
            return ""

        sorted_related = sorted(all_related.items(), key=lambda x: x[1], reverse=True)[:5]
        connections = ", ".join(f"{w}({v:.1f})" for w, v in sorted_related)
        return f"[당신의 지식 연결] 관련 주제: {connections}"

    async def get_edge_count(self, persona_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(KnowledgeEdge)
            .where(KnowledgeEdge.persona_id == persona_id, KnowledgeEdge.weight > 0)
        )
        return (await self._session.execute(stmt)).scalar_one()
