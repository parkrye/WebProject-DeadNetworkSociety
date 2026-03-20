import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.shared.pagination import PaginatedResult, PaginationParams


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        post_id: uuid.UUID,
        author_id: uuid.UUID,
        content: str,
        parent_id: uuid.UUID | None = None,
        depth: int = 0,
    ) -> Comment:
        comment = Comment(
            post_id=post_id,
            author_id=author_id,
            content=content,
            parent_id=parent_id,
            depth=depth,
        )
        self._session.add(comment)
        await self._session.flush()
        return comment

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return await self._session.get(Comment, comment_id)

    async def get_by_post(self, post_id: uuid.UUID, params: PaginationParams) -> PaginatedResult[Comment]:
        count_stmt = select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
            .offset(params.offset)
            .limit(params.size)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=params.page, size=params.size)

    async def update(self, comment: Comment, content: str | None = None) -> Comment:
        if content is not None:
            comment.content = content
        await self._session.flush()
        return comment

    async def delete(self, comment: Comment) -> None:
        await self._session.delete(comment)
        await self._session.flush()
