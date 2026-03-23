"""Repository for dynamic PersonaState — mutable runtime state persisted to DB."""
import json
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.models import PersonaState


class PersonaStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: uuid.UUID, default_interests: list[str] | None = None) -> PersonaState:
        stmt = select(PersonaState).where(PersonaState.user_id == user_id)
        result = await self._session.execute(stmt)
        state = result.scalar_one_or_none()
        if state:
            return state
        state = PersonaState(
            user_id=user_id,
            active_interests=json.dumps(default_interests or [], ensure_ascii=False),
        )
        self._session.add(state)
        await self._session.flush()
        return state

    def get_interests(self, state: PersonaState) -> list[str]:
        try:
            return json.loads(state.active_interests)
        except (json.JSONDecodeError, TypeError):
            return []

    async def set_interests(self, state: PersonaState, interests: list[str]) -> None:
        state.active_interests = json.dumps(interests, ensure_ascii=False)
        await self._session.flush()

    async def update_mood(self, user_id: uuid.UUID, delta: float) -> None:
        """Adjust mood, clamped to [-1.0, +1.0]."""
        state = await self.get_or_create(user_id)
        new_mood = max(-1.0, min(1.0, state.mood + delta))
        state.mood = new_mood
        await self._session.flush()

    async def decay_mood(self, user_id: uuid.UUID, rate: float = 0.1) -> None:
        """Decay mood toward 0 (neutral)."""
        state = await self.get_or_create(user_id)
        if state.mood > 0:
            state.mood = max(0.0, state.mood - rate)
        elif state.mood < 0:
            state.mood = min(0.0, state.mood + rate)
        await self._session.flush()
