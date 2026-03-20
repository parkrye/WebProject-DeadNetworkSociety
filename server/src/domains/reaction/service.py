import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.reaction.models import Reaction
from src.domains.reaction.repository import ReactionRepository
from src.domains.reaction.schemas import ReactionCountResponse, ReactionCreate
from src.shared.event_bus import event_bus
from src.shared.events import ReactionCreated


class ReactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = ReactionRepository(session)
        self._session = session

    async def toggle_reaction(self, data: ReactionCreate) -> Reaction | None:
        existing = await self._repository.get_by_user_and_target(
            user_id=data.user_id,
            target_type=data.target_type,
            target_id=data.target_id,
        )

        if existing:
            if existing.reaction_type == data.reaction_type:
                await self._repository.delete(existing)
                await self._session.commit()
                return None
            else:
                await self._repository.delete(existing)

        reaction = await self._repository.create(
            user_id=data.user_id,
            target_type=data.target_type,
            target_id=data.target_id,
            reaction_type=data.reaction_type,
        )
        await self._session.commit()
        await self._session.refresh(reaction)
        await event_bus.publish(
            ReactionCreated(
                user_id=reaction.user_id,
                target_type=reaction.target_type,
                target_id=reaction.target_id,
                reaction_type=reaction.reaction_type,
            )
        )
        return reaction

    async def get_counts(self, target_type: str, target_id: uuid.UUID) -> ReactionCountResponse:
        if target_type not in ("post", "comment"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target_type")
        counts = await self._repository.count_by_target(target_type, target_id)
        return ReactionCountResponse(
            target_type=target_type,
            target_id=target_id,
            like=counts.get("like", 0),
            dislike=counts.get("dislike", 0),
        )
