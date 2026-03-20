"""
Crawl Korean community content for RAG knowledge base.

Usage:
    python scripts/crawl_communities.py [--append]

Sources:
    - DCInside (디시인사이드) 인기글
    - 웃긴대학 베스트
    - Reddit 한국어 서브레딧
    - 클리앙 인기글
    - 루리웹 핫딜/유머
    - 에펨코리아 인기글

Output:
    data/community_content.json
"""
import argparse
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
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

MIN_CONTENT_LENGTH = 20
MAX_CONTENT_LENGTH = 500


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
    return text.strip()


def is_valid_korean(text: str) -> bool:
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    return korean_chars >= len(text) * 0.3 and len(text) >= MIN_CONTENT_LENGTH


# ──────────────────────────────────────────
# Source: DCInside 인기글
# ──────────────────────────────────────────

def crawl_dcinside() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    galleries = [
        ("hit", "인기"),
        ("domestic_travel", "여행"),
        ("cook", "요리"),
        ("movie", "영화"),
        ("music", "음악"),
        ("game", "게임"),
        ("sport", "스포츠"),
        ("cat", "동물"),
    ]

    for gallery_id, topic in galleries:
        try:
            url = f"https://gall.dcinside.com/board/lists/?id={gallery_id}&page=1"
            resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")

            rows = soup.select("tr.ub-content")
            for row in rows[:10]:
                title_el = row.select_one("td.gall_tit a")
                if not title_el:
                    continue
                title = clean_text(title_el.get_text())
                if not title or len(title) < 5:
                    continue

                # Get preview text from title
                subject = row.select_one("td.gall_subject")
                content = title  # Use title as content since list page

                if is_valid_korean(title):
                    posts.append(CrawledPost(title=title[:100], content=content[:MAX_CONTENT_LENGTH],
                                             source="dcinside", topic=topic))

            logger.info("DCInside [%s]: %d posts", gallery_id, len([p for p in posts if p.source == "dcinside"]))
            time.sleep(random.uniform(1, 2))
        except Exception:
            logger.exception("DCInside [%s] failed", gallery_id)

    return posts


# ──────────────────────────────────────────
# Source: Reddit 한국어 서브레딧
# ──────────────────────────────────────────

def crawl_reddit() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    subreddits = [
        ("korea", "한국"),
        ("hanguk", "일상"),
        ("korean", "언어"),
        ("kpop", "음악"),
        ("kdrama", "드라마"),
    ]

    for sub, topic in subreddits:
        try:
            url = f"https://old.reddit.com/r/{sub}/hot.json?limit=25"
            resp = httpx.get(url, headers={**HEADERS, "User-Agent": "DeadNetworkSociety/1.0"}, timeout=15.0)
            data = resp.json()

            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                title = clean_text(post_data.get("title", ""))
                selftext = clean_text(post_data.get("selftext", ""))
                content = selftext if selftext else title

                if is_valid_korean(title) or is_valid_korean(content):
                    posts.append(CrawledPost(
                        title=title[:100],
                        content=content[:MAX_CONTENT_LENGTH],
                        source="reddit",
                        topic=topic,
                    ))

            logger.info("Reddit r/%s: %d posts found", sub, len([p for p in posts if p.topic == topic]))
            time.sleep(random.uniform(1, 2))
        except Exception:
            logger.exception("Reddit r/%s failed", sub)

    return posts


# ──────────────────────────────────────────
# Source: 클리앙 인기글
# ──────────────────────────────────────────

def crawl_clien() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    boards = [
        ("park", "일상"),
        ("jirum", "쇼핑"),
        ("news", "뉴스"),
    ]

    for board, topic in boards:
        try:
            url = f"https://www.clien.net/service/board/{board}?type=recommend"
            resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select("div.list_item")
            for item in items[:15]:
                title_el = item.select_one("span.subject_fixed")
                if not title_el:
                    continue
                title = clean_text(title_el.get_text())
                if is_valid_korean(title):
                    posts.append(CrawledPost(title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                                             source="clien", topic=topic))

            logger.info("Clien [%s]: %d posts", board, len([p for p in posts if p.topic == topic]))
            time.sleep(random.uniform(1, 2))
        except Exception:
            logger.exception("Clien [%s] failed", board)

    return posts


# ──────────────────────────────────────────
# Source: 루리웹
# ──────────────────────────────────────────

def crawl_ruliweb() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    boards = [
        ("best/humor", "유머"),
        ("best/game", "게임"),
        ("best/community", "일상"),
    ]

    for board, topic in boards:
        try:
            url = f"https://bbs.ruliweb.com/{board}"
            resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select("tr.table_body")
            for item in items[:15]:
                title_el = item.select_one("a.deco")
                if not title_el:
                    continue
                title = clean_text(title_el.get_text())
                if is_valid_korean(title):
                    posts.append(CrawledPost(title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                                             source="ruliweb", topic=topic))

            logger.info("Ruliweb [%s]: %d posts", board, len([p for p in posts if p.topic == topic]))
            time.sleep(random.uniform(1, 2))
        except Exception:
            logger.exception("Ruliweb [%s] failed", board)

    return posts


# ──────────────────────────────────────────
# Source: 에펨코리아
# ──────────────────────────────────────────

def crawl_fmkorea() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    try:
        url = "https://www.fmkorea.com/best"
        resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("li.li")
        for item in items[:20]:
            title_el = item.select_one("h3.title a")
            if not title_el:
                continue
            title = clean_text(title_el.get_text())
            if is_valid_korean(title):
                posts.append(CrawledPost(title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                                         source="fmkorea", topic="일상"))

        logger.info("FMKorea: %d posts", len(posts))
    except Exception:
        logger.exception("FMKorea failed")

    return posts


# ──────────────────────────────────────────
# Source: 웃긴대학
# ──────────────────────────────────────────

def crawl_humoruniv() -> list[CrawledPost]:
    posts: list[CrawledPost] = []
    try:
        url = "https://web.humoruniv.com/board/humor/list.html?table=pds&pg=0"
        resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("table.kboard-list tr")
        for item in items[:20]:
            title_el = item.select_one("td.kboard-list-title a")
            if not title_el:
                continue
            title = clean_text(title_el.get_text())
            if is_valid_korean(title):
                posts.append(CrawledPost(title=title[:100], content=title[:MAX_CONTENT_LENGTH],
                                         source="humoruniv", topic="유머"))

        logger.info("Humoruniv: %d posts", len(posts))
    except Exception:
        logger.exception("Humoruniv failed")

    return posts


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────

ALL_CRAWLERS = [
    ("DCInside", crawl_dcinside),
    ("Reddit", crawl_reddit),
    ("Clien", crawl_clien),
    ("Ruliweb", crawl_ruliweb),
    ("FMKorea", crawl_fmkorea),
    ("Humoruniv", crawl_humoruniv),
]


def main(append: bool = False) -> None:
    existing: dict[str, list[dict]] = {}
    if append and OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        logger.info("Loaded existing: %d topics, %d items",
                     len(existing), sum(len(v) for v in existing.values()))

    all_posts: list[CrawledPost] = []

    for name, crawler in ALL_CRAWLERS:
        logger.info("Crawling %s...", name)
        try:
            posts = crawler()
            all_posts.extend(posts)
            logger.info("%s: %d posts collected", name, len(posts))
        except Exception:
            logger.exception("%s crawler failed completely", name)

    # Group by topic
    by_topic: dict[str, list[dict]] = dict(existing)
    for post in all_posts:
        if post.topic not in by_topic:
            by_topic[post.topic] = []
        entry = {"title": post.title, "content": post.content, "source": post.source}
        # Deduplicate by title
        existing_titles = {item["title"] for item in by_topic[post.topic]}
        if post.title not in existing_titles:
            by_topic[post.topic].append(entry)

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_topic, f, ensure_ascii=False, indent=1)

    total = sum(len(v) for v in by_topic.values())
    logger.info("Done: %d items across %d topics -> %s (%.0f KB)",
                total, len(by_topic), OUTPUT_PATH, OUTPUT_PATH.stat().st_size / 1024)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append", action="store_true", help="Append to existing data")
    args = parser.parse_args()
    main(append=args.append)
