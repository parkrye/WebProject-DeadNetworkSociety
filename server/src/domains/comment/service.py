import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.comment.repository import CommentRepository
from src.domains.comment.schemas import CommentCreate, CommentUpdate
from src.shared.event_bus import event_bus
from src.shared.events import CommentCreated
from src.shared.pagination import PaginatedResult, PaginationParams


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = CommentRepository(session)
        self._session = session

    async def create_comment(self, data: CommentCreate) -> Comment:
        depth = 0
        if data.parent_id:
            parent = await self._repository.get_by_id(data.parent_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
            depth = parent.depth + 1

        comment = await self._repository.create(
            post_id=data.post_id,
            author_id=data.author_id,
            content=data.content,
            parent_id=data.parent_id,
            depth=depth,
        )
        await self._session.commit()
        await self._session.refresh(comment)
        await event_bus.publish(
            CommentCreated(comment_id=comment.id, post_id=comment.post_id, author_id=comment.author_id)
        )
        return comment

    async def get_comment(self, comment_id: uuid.UUID) -> Comment:
        comment = await self._repository.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return comment

    async def get_comments_by_post(self, post_id: uuid.UUID, params: PaginationParams) -> PaginatedResult[Comment]:
        return await self._repository.get_by_post(post_id, params)

    async def update_comment(self, comment_id: uuid.UUID, data: CommentUpdate) -> Comment:
        comment = await self.get_comment(comment_id)
        comment = await self._repository.update(comment, content=data.content)
        await self._session.commit()
        await self._session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: uuid.UUID) -> None:
        comment = await self.get_comment(comment_id)
        await self._repository.delete(comment)
        await self._session.commit()
