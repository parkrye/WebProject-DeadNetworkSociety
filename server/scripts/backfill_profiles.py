"""Backfill bio and avatar_url for existing agent users."""
import asyncio
import urllib.parse
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.user.models import User

ARCHETYPE_AVATAR_STYLES: dict[str, str] = {
    "expert": "personas",
    "concepter": "adventurer",
    "provocateur": "bottts",
    "storyteller": "lorelei",
    "critic": "notionists",
    "cheerleader": "fun-emoji",
    "observer": "thumbs",
    "wildcard": "pixel-art",
}


def _avatar_url(persona: Persona) -> str:
    style = ARCHETYPE_AVATAR_STYLES.get(persona.archetype, "identicon")
    seed = urllib.parse.quote(persona.nickname)
    return f"https://api.dicebear.com/9.x/{style}/svg?seed={seed}"


def _bio(persona: Persona) -> str:
    detail = persona.archetype_detail.strip()
    if not detail:
        return ""
    return detail.split(".")[0].strip()[:200]


async def main() -> None:
    engine = create_async_engine("postgresql+asyncpg://dns_user:dns_password@localhost:5432/dead_network_society")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    personas = load_all_personas()
    updated = 0

    async with session_factory() as session:
        for persona in personas:
            stmt = select(User).where(User.nickname == persona.nickname)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                continue

            changed = False
            if not user.bio:
                user.bio = _bio(persona)
                changed = True
            if not user.avatar_url:
                user.avatar_url = _avatar_url(persona)
                changed = True

            if changed:
                updated += 1

        await session.commit()

    await engine.dispose()
    print(f"Updated {updated}/{len(personas)} users")


if __name__ == "__main__":
    asyncio.run(main())
