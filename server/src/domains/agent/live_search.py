"""Live search provider: fetches recent information from public sources.

Shared tool that personas use to get current trending info.
Uses RSS feeds and public JSON APIs — no API keys needed.

Sources:
- Google News RSS (Korean)
- Naver News search RSS
- Reddit search JSON
"""
import asyncio
import logging
import time
import urllib.parse
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

SEARCH_TIMEOUT = 10.0
CACHE_TTL_SECONDS = 600  # 10 minutes
MAX_RESULTS_PER_SOURCE = 3


@dataclass
class SearchResult:
    title: str
    snippet: str
    source: str


@dataclass
class _CacheEntry:
    results: list[SearchResult]
    timestamp: float


class LiveSearchProvider:
    """Fetches recent web info for keywords. Results are cached."""

    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}

    async def search(self, keywords: list[str], max_total: int = 5) -> list[SearchResult]:
        """Search multiple sources for the given keywords."""
        query = " ".join(keywords[:3])
        cache_key = query.lower().strip()

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry.timestamp < CACHE_TTL_SECONDS:
                return entry.results

        # Search all sources concurrently
        results: list[SearchResult] = []
        tasks = [
            self._search_google_news(query),
            self._search_naver_news(query),
            self._search_reddit(query),
        ]
        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        for sr in source_results:
            if isinstance(sr, list):
                results.extend(sr)

        # Deduplicate by title similarity
        seen_titles: set[str] = set()
        unique: list[SearchResult] = []
        for r in results:
            title_key = r.title[:20]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(r)

        final = unique[:max_total]
        self._cache[cache_key] = _CacheEntry(results=final, timestamp=time.time())

        # Evict old cache entries
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v.timestamp > CACHE_TTL_SECONDS * 3]
        for k in expired:
            del self._cache[k]

        return final

    def format_as_context(self, results: list[SearchResult]) -> str:
        if not results:
            return ""
        lines = ["[최신 정보]"]
        for r in results:
            lines.append(f"- [{r.source}] {r.title}: {r.snippet}")
        return "\n".join(lines)

    async def _search_google_news(self, query: str) -> list[SearchResult]:
        """Google News RSS search (Korean)."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
            async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code != 200:
                    return []

            import feedparser
            feed = feedparser.parse(resp.text)
            results = []
            for entry in feed.entries[:MAX_RESULTS_PER_SOURCE]:
                title = entry.get("title", "")
                snippet = entry.get("summary", "")
                # Strip HTML
                if "<" in snippet:
                    from bs4 import BeautifulSoup
                    snippet = BeautifulSoup(snippet, "html.parser").get_text()
                results.append(SearchResult(
                    title=title[:80],
                    snippet=snippet[:120],
                    source="구글뉴스",
                ))
            return results
        except Exception:
            logger.debug("Google News search failed for: %s", query)
            return []

    async def _search_naver_news(self, query: str) -> list[SearchResult]:
        """Naver News search RSS."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://search.naver.com/search.naver?where=rss&query={encoded}"
            async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code != 200:
                    return []

            import feedparser
            feed = feedparser.parse(resp.text)
            results = []
            for entry in feed.entries[:MAX_RESULTS_PER_SOURCE]:
                title = entry.get("title", "")
                snippet = entry.get("description", "")
                if "<" in snippet:
                    from bs4 import BeautifulSoup
                    snippet = BeautifulSoup(snippet, "html.parser").get_text()
                results.append(SearchResult(
                    title=title[:80],
                    snippet=snippet[:120],
                    source="네이버",
                ))
            return results
        except Exception:
            logger.debug("Naver search failed for: %s", query)
            return []

    async def _search_reddit(self, query: str) -> list[SearchResult]:
        """Reddit search via public JSON API."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://www.reddit.com/search.json?q={encoded}&sort=new&limit={MAX_RESULTS_PER_SOURCE}"
            headers = {"User-Agent": "DeadNetworkSociety/1.0"}
            async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code != 200:
                    return []

            data = resp.json()
            results = []
            for child in data.get("data", {}).get("children", [])[:MAX_RESULTS_PER_SOURCE]:
                post = child.get("data", {})
                title = post.get("title", "")
                snippet = post.get("selftext", "")[:120]
                if not snippet:
                    snippet = post.get("subreddit_name_prefixed", "")
                results.append(SearchResult(
                    title=title[:80],
                    snippet=snippet,
                    source="Reddit",
                ))
            return results
        except Exception:
            logger.debug("Reddit search failed for: %s", query)
            return []


# Module-level singleton
_live_search = LiveSearchProvider()


def get_live_search() -> LiveSearchProvider:
    return _live_search
