import uuid
from datetime import UTC, datetime

from sqlalchemy import case, cast, delete, Float, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
import re
import yaml
from pathlib import Path

from src.domains.post.models import PopularPost, Post, PostMetadata, TrendingKeyword

_AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"
from src.domains.reaction.models import Reaction
from src.shared.pagination import PaginatedResult, PaginationParams


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, author_id: uuid.UUID, title: str, content: str) -> Post:
        post = Post(author_id=author_id, title=title, content=content)
        self._session.add(post)
        await self._session.flush()
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        return await self._session.get(Post, post_id)

    async def get_list(self, params: PaginationParams) -> PaginatedResult[Post]:
        count_stmt = select(func.count()).select_from(Post)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Post)
            .order_by(Post.created_at.desc())
            .offset(params.offset)
            .limit(params.size)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=params.page, size=params.size)

    async def get_recent_by_author(self, author_id: uuid.UUID, limit: int = 10) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, post: Post, title: str | None = None, content: str | None = None) -> Post:
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        await self._session.flush()
        return post

    async def increment_view_count(self, post_id: uuid.UUID, amount: int = 1) -> None:
        stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(view_count=Post.view_count + amount)
        )
        await self._session.execute(stmt)

    async def delete(self, post: Post) -> None:
        await self._session.delete(post)
        await self._session.flush()


class PostMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        post_id: uuid.UUID,
        persona_nickname: str = "",
        model_used: str = "",
        template_tier: str = "",
        rag_context_summary: str = "",
    ) -> PostMetadata:
        meta = PostMetadata(
            post_id=post_id,
            persona_nickname=persona_nickname,
            model_used=model_used,
            template_tier=template_tier,
            rag_context_summary=rag_context_summary,
        )
        self._session.add(meta)
        await self._session.flush()
        return meta

    async def get_by_post_id(self, post_id: uuid.UUID) -> PostMetadata | None:
        stmt = select(PostMetadata).where(PostMetadata.post_id == post_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PopularPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[PopularPost]:
        stmt = select(PopularPost).order_by(PopularPost.popularity_score.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_post_ids(self) -> list[uuid.UUID]:
        stmt = select(PopularPost.post_id).order_by(PopularPost.popularity_score.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def refresh(
        self,
        comment_weight: float = 3.0,
        like_weight: float = 2.0,
        like_ratio_weight: float = 1.0,
        min_engagement: int = 2,
        max_slots: int = 10,
    ) -> None:
        """Refresh popular posts queue.

        Logic:
        1. Score ALL qualifying posts
        2. Update scores for posts already in the queue
        3. Find new qualifying posts NOT yet in the queue
        4. Add new posts, evicting oldest (FIFO by promoted_at) if over max_slots
        5. Remove posts that no longer meet min_engagement
        """
        like_sub = (
            select(Reaction.target_id, func.count().label("cnt"))
            .where(Reaction.target_type == "post", Reaction.reaction_type == "like")
            .group_by(Reaction.target_id)
            .subquery()
        )
        dislike_sub = (
            select(Reaction.target_id, func.count().label("cnt"))
            .where(Reaction.target_type == "post", Reaction.reaction_type == "dislike")
            .group_by(Reaction.target_id)
            .subquery()
        )
        comment_sub = (
            select(Comment.post_id, func.count().label("cnt"))
            .group_by(Comment.post_id)
            .subquery()
        )

        like_col = func.coalesce(like_sub.c.cnt, 0)
        dislike_col = func.coalesce(dislike_sub.c.cnt, 0)
        comment_col = func.coalesce(comment_sub.c.cnt, 0)
        total_reactions = like_col + dislike_col

        like_ratio = case(
            (total_reactions > 0, cast(like_col, Float) / cast(total_reactions, Float)),
            else_=0.0,
        )
        score = (
            comment_col * comment_weight
            + like_col * like_weight
            + like_ratio * like_ratio_weight
        )

        # All qualifying posts with scores
        all_qualified = await self._session.execute(
            select(Post.id, score.label("score"))
            .outerjoin(like_sub, Post.id == like_sub.c.target_id)
            .outerjoin(dislike_sub, Post.id == dislike_sub.c.target_id)
            .outerjoin(comment_sub, Post.id == comment_sub.c.post_id)
            .where((comment_col + like_col) >= min_engagement)
            .order_by(score.desc())
        )
        qualified = {row.id: row.score for row in all_qualified.all()}

        # Current queue
        current_result = await self._session.execute(
            select(PopularPost.post_id, PopularPost.promoted_at)
            .order_by(PopularPost.promoted_at.asc())
        )
        current_entries = {r.post_id: r.promoted_at for r in current_result.all()}

        # 1. Update scores for existing entries
        for post_id in current_entries:
            if post_id in qualified:
                await self._session.execute(
                    update(PopularPost)
                    .where(PopularPost.post_id == post_id)
                    .values(popularity_score=qualified[post_id])
                )

        # 2. Remove entries that no longer qualify
        disqualified = set(current_entries.keys()) - set(qualified.keys())
        if disqualified:
            await self._session.execute(
                delete(PopularPost).where(PopularPost.post_id.in_(disqualified))
            )
            for pid in disqualified:
                del current_entries[pid]

        # 3. Find the best new candidate not yet in queue
        best_new = None
        for pid, sc in sorted(qualified.items(), key=lambda x: x[1], reverse=True):
            if pid not in current_entries:
                best_new = (pid, sc)
                break

        # 4. Add the best new candidate if it exists
        if best_new:
            now = datetime.now(UTC)
            post_id, new_score = best_new

            if len(current_entries) >= max_slots:
                # FIFO eviction: remove the oldest by promoted_at
                oldest_pid = min(current_entries, key=current_entries.get)
                await self._session.execute(
                    delete(PopularPost).where(PopularPost.post_id == oldest_pid)
                )

            self._session.add(PopularPost(
                post_id=post_id,
                popularity_score=new_score,
                promoted_at=now,
            ))

        await self._session.flush()


class TrendingKeywordRepository:
    _KOREAN_WORD_RE = re.compile(r'[가-힣]{2,}')

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _load_config() -> dict:
        with open(_AI_DEFAULTS_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f).get("trending_keywords", {})

    def _extract_keywords(self, text: str, stop_words: set[str]) -> list[str]:
        words = self._KOREAN_WORD_RE.findall(text)
        return [w for w in words if w not in stop_words and len(w) >= 2]

    async def get_all(self) -> list[TrendingKeyword]:
        stmt = select(TrendingKeyword).order_by(TrendingKeyword.count.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def refresh(self) -> None:
        """Count keywords from all posts, update trending queue (FIFO, max 20)."""
        config = self._load_config()
        max_slots = config.get("max_slots", 20)
        min_count = config.get("min_count", 3)
        stop_words = set(config.get("stop_words", []))

        # Count keywords from all posts
        result = await self._session.execute(select(Post.title, Post.content))
        word_counts: dict[str, int] = {}
        for row in result.all():
            text = f"{row.title} {row.content}"
            for word in self._extract_keywords(text, stop_words):
                word_counts[word] = word_counts.get(word, 0) + 1

        # Filter by min_count, sort by count desc
        qualified = {w: c for w, c in word_counts.items() if c >= min_count}
        sorted_words = sorted(qualified.items(), key=lambda x: x[1], reverse=True)

        # Current trending
        current_result = await self._session.execute(
            select(TrendingKeyword.keyword, TrendingKeyword.promoted_at)
        )
        current = {r.keyword: r.promoted_at for r in current_result.all()}

        # Update counts for existing
        for keyword, count in sorted_words:
            if keyword in current:
                await self._session.execute(
                    update(TrendingKeyword)
                    .where(TrendingKeyword.keyword == keyword)
                    .values(count=count)
                )

        # Remove disqualified
        disqualified = set(current.keys()) - set(qualified.keys())
        if disqualified:
            await self._session.execute(
                delete(TrendingKeyword).where(TrendingKeyword.keyword.in_(disqualified))
            )
            for kw in disqualified:
                del current[kw]

        # Add best new keyword (1 per refresh, FIFO like popular posts)
        now = datetime.now(UTC)
        for keyword, count in sorted_words:
            if keyword not in current:
                if len(current) >= max_slots:
                    oldest_kw = min(current, key=current.get)
                    await self._session.execute(
                        delete(TrendingKeyword).where(TrendingKeyword.keyword == oldest_kw)
                    )
                    del current[oldest_kw]

                self._session.add(TrendingKeyword(keyword=keyword, count=count, promoted_at=now))
                current[keyword] = now
                break  # 1 per refresh

        await self._session.flush()
