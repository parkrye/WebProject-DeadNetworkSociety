"""
Crawl Korean community content for RAG knowledge base.

Usage:
    python scripts/crawl_communities.py [--append] [--pages N]

Output:
    data/community_content.json
"""
import argparse
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("crawler")

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "community_content.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

MIN_CONTENT_LENGTH = 15
MAX_CONTENT_LENGTH = 500
DEFAULT_PAGES = 5


@dataclass
class CrawledPost:
    title: str
    content: str
    source: str
    topic: str


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[#@]\S+", "", text)
    return text.strip()


def is_valid_korean(text: str) -> bool:
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    return korean_chars >= len(text) * 0.25 and len(text) >= MIN_CONTENT_LENGTH


def _sleep():
    time.sleep(random.uniform(1.0, 2.5))


# ──────────────────────────────────────────
# DCInside - 멀티페이지, 갤러리 확대
# ──────────────────────────────────────────

def crawl_dcinside(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    galleries = [
        ("hit", "인기"), ("humor_new2", "유머"), ("cook", "요리"),
        ("movie", "영화"), ("music_new1", "음악"), ("game", "게임"),
        ("baseball_new11", "스포츠"), ("cat", "동물"), ("travel", "여행"),
        ("car", "자동차"), ("stock", "경제"), ("programming", "기술"),
        ("diet", "건강"), ("fashion", "패션"), ("photo", "사진"),
    ]

    for gallery_id, topic in galleries:
        for page in range(1, pages + 1):
            try:
                url = f"https://gall.dcinside.com/board/lists/?id={gallery_id}&page={page}"
                resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("tr.ub-content")
                if not rows:
                    break

                for row in rows:
                    title_el = row.select_one("td.gall_tit a")
                    if not title_el:
                        continue
                    title = clean_text(title_el.get_text())
                    if title and is_valid_korean(title):
                        posts.append(CrawledPost(
                            title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                            source="dcinside", topic=topic,
                        ))
                _sleep()
            except Exception:
                logger.warning("DCInside [%s] page %d failed", gallery_id, page)

        logger.info("DCInside [%s]: done", gallery_id)

    logger.info("DCInside total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# Reddit - 멀티페이지(after 파라미터), 서브레딧 확대
# ──────────────────────────────────────────

def crawl_reddit(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    subreddits = [
        ("hanguk", "일상"), ("korea", "한국"), ("korean", "언어"),
        ("kpop", "음악"), ("kdrama", "드라마"), ("koreatravel", "여행"),
    ]
    reddit_headers = {**HEADERS, "User-Agent": "DeadNetworkSociety/1.0"}

    for sub, topic in subreddits:
        after = None
        for page in range(pages):
            try:
                url = f"https://old.reddit.com/r/{sub}/hot.json?limit=100"
                if after:
                    url += f"&after={after}"
                resp = httpx.get(url, headers=reddit_headers, timeout=15.0)
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                after = data.get("data", {}).get("after")

                for child in children:
                    pd = child.get("data", {})
                    title = clean_text(pd.get("title", ""))
                    selftext = clean_text(pd.get("selftext", ""))
                    content = selftext if selftext else title
                    if is_valid_korean(title) or is_valid_korean(content):
                        posts.append(CrawledPost(
                            title=title[:100], content=content[:MAX_CONTENT_LENGTH],
                            source="reddit", topic=topic,
                        ))

                if not after:
                    break
                _sleep()
            except Exception:
                logger.warning("Reddit r/%s page %d failed", sub, page)

        logger.info("Reddit r/%s: done", sub)

    logger.info("Reddit total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# X (Twitter) - nitter 인스턴스 활용
# ──────────────────────────────────────────

def crawl_x(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    # nitter 인스턴스들 (public)
    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.cz",
    ]
    # 한국어 검색어
    searches = [
        ("한국", "한국"), ("일상", "일상"), ("맛집", "요리"),
        ("게임", "게임"), ("영화", "영화"), ("음악추천", "음악"),
        ("운동", "건강"), ("여행", "여행"), ("코딩", "기술"),
    ]

    for search_term, topic in searches:
        found = False
        for base_url in nitter_instances:
            if found:
                break
            try:
                url = f"{base_url}/search?q={search_term}&f=tweets&lang=ko"
                resp = httpx.get(url, headers=HEADERS, timeout=10.0, follow_redirects=True)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                tweets = soup.select("div.tweet-content")

                for tweet in tweets[:30]:
                    text = clean_text(tweet.get_text())
                    if is_valid_korean(text):
                        # 첫 문장을 제목으로, 전체를 본문으로
                        title = text[:50].split(".")[0].split("?")[0].split("!")[0]
                        posts.append(CrawledPost(
                            title=title[:100], content=text[:MAX_CONTENT_LENGTH],
                            source="x", topic=topic,
                        ))

                if tweets:
                    found = True
                    logger.info("X [%s] via %s: %d tweets", search_term, base_url.split("//")[1], len(tweets))
                _sleep()
            except Exception:
                continue

        if not found:
            logger.warning("X [%s]: all nitter instances failed", search_term)

    logger.info("X total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# 클리앙 - 멀티페이지
# ──────────────────────────────────────────

def crawl_clien(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    boards = [
        ("park", "일상"), ("jirum", "쇼핑"), ("news", "뉴스"),
        ("food", "요리"), ("use", "기술"),
    ]

    for board, topic in boards:
        for page in range(pages):
            try:
                url = f"https://www.clien.net/service/board/{board}?&od=T31&po={page}"
                resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select("div.list_item")
                if not items:
                    break

                for item in items:
                    title_el = item.select_one("span.subject_fixed")
                    if not title_el:
                        continue
                    title = clean_text(title_el.get_text())
                    if is_valid_korean(title):
                        posts.append(CrawledPost(
                            title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                            source="clien", topic=topic,
                        ))
                _sleep()
            except Exception:
                logger.warning("Clien [%s] page %d failed", board, page)

        logger.info("Clien [%s]: done", board)

    logger.info("Clien total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# 루리웹 - 멀티페이지
# ──────────────────────────────────────────

def crawl_ruliweb(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    boards = [
        ("best/humor", "유머"), ("best/game", "게임"),
        ("best/community", "일상"), ("best/hobby", "취미"),
    ]

    for board, topic in boards:
        for page in range(1, pages + 1):
            try:
                url = f"https://bbs.ruliweb.com/{board}?page={page}"
                resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select("tr.table_body")
                if not items:
                    break

                for item in items:
                    title_el = item.select_one("a.deco")
                    if not title_el:
                        continue
                    title = clean_text(title_el.get_text())
                    if is_valid_korean(title):
                        posts.append(CrawledPost(
                            title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                            source="ruliweb", topic=topic,
                        ))
                _sleep()
            except Exception:
                logger.warning("Ruliweb [%s] page %d failed", board, page)

        logger.info("Ruliweb [%s]: done", board)

    logger.info("Ruliweb total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# 에펨코리아 - 멀티페이지
# ──────────────────────────────────────────

def crawl_fmkorea(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    boards = [("best", "인기"), ("humor", "유머"), ("issue", "이슈")]

    for board, topic in boards:
        for page in range(1, pages + 1):
            try:
                url = f"https://www.fmkorea.com/{board}?page={page}"
                resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select("li.li")
                if not items:
                    break

                for item in items:
                    title_el = item.select_one("h3.title a")
                    if not title_el:
                        continue
                    title = clean_text(title_el.get_text())
                    if is_valid_korean(title):
                        posts.append(CrawledPost(
                            title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                            source="fmkorea", topic=topic,
                        ))
                _sleep()
            except Exception:
                logger.warning("FMKorea [%s] page %d failed", board, page)

        logger.info("FMKorea [%s]: done", board)

    logger.info("FMKorea total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# 웃긴대학 - 멀티페이지
# ──────────────────────────────────────────

def crawl_humoruniv(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    for page in range(pages):
        try:
            url = f"https://web.humoruniv.com/board/humor/list.html?table=pds&pg={page}"
            resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")

            for a_tag in soup.select("a"):
                title = clean_text(a_tag.get_text())
                if is_valid_korean(title) and len(title) > 10:
                    posts.append(CrawledPost(
                        title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                        source="humoruniv", topic="유머",
                    ))
            _sleep()
        except Exception:
            logger.warning("Humoruniv page %d failed", page)

    logger.info("Humoruniv total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# 더쿠 (TheQoo)
# ──────────────────────────────────────────

def crawl_theqoo(pages: int = DEFAULT_PAGES) -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    for page in range(1, pages + 1):
        try:
            url = f"https://theqoo.net/hot?page={page}"
            resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("a.document_title")

            for item in items:
                title = clean_text(item.get_text())
                if is_valid_korean(title):
                    posts.append(CrawledPost(
                        title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                        source="theqoo", topic="연예",
                    ))
            _sleep()
        except Exception:
            logger.warning("TheQoo page %d failed", page)

    logger.info("TheQoo total: %d posts", len(posts))
    return posts


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────

ALL_CRAWLERS = [
    ("DCInside", crawl_dcinside),
    ("Reddit", crawl_reddit),
    ("X", crawl_x),
    ("Clien", crawl_clien),
    ("Ruliweb", crawl_ruliweb),
    ("FMKorea", crawl_fmkorea),
    ("Humoruniv", crawl_humoruniv),
    ("TheQoo", crawl_theqoo),
]


def main(append: bool = False, pages: int = DEFAULT_PAGES) -> None:
    existing: dict[str, list[dict]] = {}
    if append and OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        logger.info("Loaded existing: %d topics, %d items",
                     len(existing), sum(len(v) for v in existing.values()))

    all_posts: list[CrawledPost] = []

    for name, crawler in ALL_CRAWLERS:
        logger.info("=== Crawling %s (%d pages) ===", name, pages)
        try:
            posts = crawler(pages)
            all_posts.extend(posts)
        except Exception:
            logger.exception("%s crawler failed", name)

    # Group by topic, deduplicate
    by_topic: dict[str, list[dict]] = dict(existing)
    for post in all_posts:
        if post.topic not in by_topic:
            by_topic[post.topic] = []
        entry = {"title": post.title, "content": post.content, "source": post.source}
        existing_titles = {item["title"] for item in by_topic[post.topic]}
        if post.title not in existing_titles:
            by_topic[post.topic].append(entry)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_topic, f, ensure_ascii=False, indent=1)

    total = sum(len(v) for v in by_topic.values())
    logger.info("\n=== Summary ===")
    for topic, items in sorted(by_topic.items(), key=lambda x: -len(x[1])):
        sources = {}
        for item in items:
            s = item.get("source", "?")
            sources[s] = sources.get(s, 0) + 1
        logger.info("  %s: %d items %s", topic, len(items), dict(sources))
    logger.info("Total: %d items, %d topics -> %s (%.0f KB)",
                total, len(by_topic), OUTPUT_PATH, OUTPUT_PATH.stat().st_size / 1024)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append", action="store_true", help="Append to existing data")
    parser.add_argument("--pages", type=int, default=DEFAULT_PAGES, help="Pages per source")
    args = parser.parse_args()
    main(append=args.append, pages=args.pages)
