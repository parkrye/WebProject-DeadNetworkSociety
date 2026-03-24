"""Bootstrap knowledge graphs for missing personas via direct SQL."""
import asyncio
import uuid
import sys
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg

DB_URL = "postgresql://dns_user:dns_password@localhost:5432/dead_network_society"
WEIGHT = 0.5

NEWS_ANCHOR_ID = "2eca540a-1b9c-498e-8968-5213b07d2c44"
TSUNDERE_ID = "ad761dd7-1513-4986-80f7-0e5e1789b4d3"

NEWS_GROUPS = [
    ["정치", "개헌", "트럼프", "이란", "중동"],
    ["경제", "환율", "부동산", "물가", "국제유가"],
    ["국제", "미국", "북한", "김정은", "전쟁"],
    ["사회", "화재", "보궐선거", "에너지"],
    ["연예", "광화문", "신화", "이강인", "스포츠"],
    ["뉴스", "속보", "정치", "경제", "국제", "사회"],
]

TSUNDERE_GROUPS = [
    ["츤데레", "다혈질", "자존심", "질투심", "독점욕"],
    ["츤데레", "솔직하지", "부끄럼쟁이", "외강내유"],
    ["츤데레", "데레데레", "츤츤거림", "모에"],
    ["애정", "관심", "호감", "거부", "츤데레"],
    ["소꿉친구", "오죠사마", "금발", "트윈테일"],
    ["냉혹한", "반동형성", "가스라이팅", "날카로운"],
]


async def insert_edges(conn, persona_id: str, groups: list[list[str]]):
    count = 0
    for keywords in groups:
        clean = list(dict.fromkeys(kw.strip().lower() for kw in keywords))
        for a, b in combinations(clean, 2):
            kw_from, kw_to = (a, b) if a < b else (b, a)
            try:
                await conn.execute("""
                    INSERT INTO knowledge_edges (id, persona_id, keyword_from, keyword_to, weight, relation, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, 'related', now())
                    ON CONFLICT (persona_id, keyword_from, keyword_to)
                    DO UPDATE SET weight = knowledge_edges.weight + $4, updated_at = now()
                """, uuid.UUID(persona_id), kw_from, kw_to, WEIGHT)
                count += 1
            except Exception as e:
                print(f"  skip {kw_from}-{kw_to}: {e}")
    return count


async def main():
    conn = await asyncpg.connect(DB_URL)

    n = await insert_edges(conn, NEWS_ANCHOR_ID, NEWS_GROUPS)
    print(f"뉴스앵커: {n} edges")

    t = await insert_edges(conn, TSUNDERE_ID, TSUNDERE_GROUPS)
    print(f"츤데레: {t} edges")

    # Verify
    total = await conn.fetchval("SELECT count(*) FROM knowledge_edges WHERE persona_id = $1", uuid.UUID(NEWS_ANCHOR_ID))
    print(f"뉴스앵커 total: {total}")
    total = await conn.fetchval("SELECT count(*) FROM knowledge_edges WHERE persona_id = $1", uuid.UUID(TSUNDERE_ID))
    print(f"츤데레 total: {total}")

    await conn.close()

asyncio.run(main())
