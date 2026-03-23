import uuid
from datetime import UTC, datetime

from sqlalchemy import case, cast, delete, Float, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.post.models import PopularPost, Post, PostMetadata
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
        """Recalculate top posts and sync the popular_posts table (queue, max_slots)."""
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

        stmt = (
            select(Post.id, score.label("score"))
            .outerjoin(like_sub, Post.id == like_sub.c.target_id)
            .outerjoin(dislike_sub, Post.id == dislike_sub.c.target_id)
            .outerjoin(comment_sub, Post.id == comment_sub.c.post_id)
            .where((comment_col + like_col) >= min_engagement)
            .order_by(score.desc())
            .limit(max_slots)
        )
        result = await self._session.execute(stmt)
        top_rows = result.all()
        new_ids = {row.id: row.score for row in top_rows}

        # Get current popular entries
        current_result = await self._session.execute(
            select(PopularPost.post_id, PopularPost.promoted_at)
            .order_by(PopularPost.promoted_at.asc())
        )
        current_entries = {r.post_id: r.promoted_at for r in current_result.all()}

        # Update scores for existing entries
        now = datetime.now(UTC)
        for post_id, new_score in new_ids.items():
            if post_id in current_entries:
                await self._session.execute(
                    update(PopularPost)
                    .where(PopularPost.post_id == post_id)
                    .values(popularity_score=new_score)
                )

        # Remove entries that no longer qualify
        to_remove = set(current_entries.keys()) - set(new_ids.keys())
        if to_remove:
            await self._session.execute(
                delete(PopularPost).where(PopularPost.post_id.in_(to_remove))
            )

        # Add new entries
        new_to_add = set(new_ids.keys()) - set(current_entries.keys())
        for post_id in new_to_add:
            self._session.add(PopularPost(
                post_id=post_id,
                popularity_score=new_ids[post_id],
                promoted_at=now,
            ))
        await self._session.flush()

        # FIFO eviction: if over max_slots, remove oldest by promoted_at
        count_result = await self._session.execute(
            select(func.count()).select_from(PopularPost)
        )
        total = count_result.scalar_one()
        if total > max_slots:
            overflow = total - max_slots
            oldest = await self._session.execute(
                select(PopularPost.id)
                .order_by(PopularPost.promoted_at.asc())
                .limit(overflow)
            )
            oldest_ids = [r[0] for r in oldest.all()]
            if oldest_ids:
                await self._session.execute(
                    delete(PopularPost).where(PopularPost.id.in_(oldest_ids))
                )
            await self._session.flush()
