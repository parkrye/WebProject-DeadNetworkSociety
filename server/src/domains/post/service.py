import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.post.models import Post
from src.domains.post.repository import PostRepository
from src.domains.post.schemas import PostCreate, PostUpdate
from src.shared.event_bus import event_bus
from src.shared.events import PostCreated
from src.shared.pagination import PaginatedResult, PaginationParams


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = PostRepository(session)
        self._session = session

    async def create_post(self, data: PostCreate) -> Post:
        post = await self._repository.create(
            author_id=data.author_id,
            title=data.title,
            content=data.content,
        )
        await self._session.commit()
        await self._session.refresh(post)
        await event_bus.publish(PostCreated(post_id=post.id, author_id=post.author_id))
        return post

    async def get_post(self, post_id: uuid.UUID) -> Post:
        post = await self._repository.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return post

    async def get_posts(self, params: PaginationParams) -> PaginatedResult[Post]:
        return await self._repository.get_list(params)

    async def update_post(self, post_id: uuid.UUID, data: PostUpdate) -> Post:
        post = await self.get_post(post_id)
        post = await self._repository.update(post, title=data.title, content=data.content)
        await self._session.commit()
        await self._session.refresh(post)
        return post

    async def delete_post(self, post_id: uuid.UUID) -> None:
        post = await self.get_post(post_id)
        await self._repository.delete(post)
        await self._session.commit()
