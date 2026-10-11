# sources/news_common.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time
import feedparser

# Normalize RSS entries into a simple shape
@dataclass
class NewsItem:
    title: str
    link: str
    published: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def _safe(entry: dict, key: str, default: str = "") -> str:
    val = entry.get(key) or ""
    if isinstance(val, list) and val:
        val = val[0]
    return str(val)


def fetch_rss(url: str, source: str, limit: int = 15) -> list[dict]:
    import requests
    import feedparser

    response = requests.get(
        url,
        headers={"User-Agent": "DailyKnowledgeGarden/1.0"},
        timeout=20,
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise ValueError(
            f"Invalid feed: {feed.bozo_exception}"
        )

    if not feed.entries:
        print(f"[WARNING] {source}: zero articles")
        return []

    articles = [
        {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": source,
        }
        for entry in feed.entries[:limit]
        if entry.get("title") and entry.get("link")
    ]

    print(f"[OK] {source}: {len(articles)} articles")
    return articles


def fetch_many(sources: List[tuple]) -> List[Dict[str, Any]]:
    """sources = [(url, 'Label'), ...]"""
    out: List[Dict[str, Any]] = []
    for url, label in sources:
        try:
            out.extend(fetch_rss(url, label))
        except Exception as e:
            print(f"[ERROR] {label}: {type(e).__name__}: {e}")
        return out
