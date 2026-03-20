import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.post.models import Post
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

    async def update(self, post: Post, title: str | None = None, content: str | None = None) -> Post:
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        await self._session.flush()
        return post

    async def delete(self, post: Post) -> None:
        await self._session.delete(post)
        await self._session.flush()
