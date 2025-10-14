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

def fetch_rss(url: str, source: str, limit: int = 15) -> List[Dict[str, Any]]:
    # User-Agent helps some feeds
    d = feedparser.parse(url, request_headers={"User-Agent": "DailyKnowledgeGarden/1.0 (+github)"})
    items: List[NewsItem] = []
    for e in d.entries[:limit]:
        items.append(
            NewsItem(
                title=_safe(e, "title"),
                link=_safe(e, "link"),
                published=_safe(e, "published", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
                source=source,
            )
        )
    return [i.to_dict() for i in items]

def fetch_many(sources: List[tuple]) -> List[Dict[str, Any]]:
    """sources = [(url, 'Label'), ...]"""
    out: List[Dict[str, Any]] = []
    for url, label in sources:
        try:
            out.extend(fetch_rss(url, label))
        except Exception as e:
            out.append({"title": f"(feed error from {label})", "link": "", "published": "", "source": label, "error": str(e)})
    return out
