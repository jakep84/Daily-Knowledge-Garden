"""RSS collection with observable per-feed status."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import feedparser
import requests

FEED_STATUS: list[dict[str, Any]] = []

def reset_status() -> None:
    FEED_STATUS.clear()

def fetch_rss(url: str, source: str, limit: int = 15) -> list[dict]:
    response = requests.get(
        url,
        headers={"User-Agent": "DailyKnowledgeGarden/1.1 (+https://github.com/jakep84/Daily-Knowledge-Garden)"},
        timeout=20,
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"Malformed feed: {parsed.bozo_exception}")

    items = [
        {"title": str(e.get("title", "")).strip(),
         "link": str(e.get("link", "")).strip(),
         "published": str(e.get("published", "")),
         "source": source}
        for e in parsed.entries[:limit]
        if e.get("title") and e.get("link")
    ]
    return items

def fetch_many(sources: list[tuple[str, str]]) -> list[dict]:
    articles: list[dict] = []
    for url, label in sources:
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            items = fetch_rss(url, label)
            status = "ok" if items else "empty"
            FEED_STATUS.append({"source": label, "url": url, "status": status,
                                "count": len(items), "checked_at_utc": checked_at})
            print(f"[FEED] {status.upper():5} {label}: {len(items)} articles", flush=True)
            articles.extend(items)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            FEED_STATUS.append({"source": label, "url": url, "status": "error",
                                "count": 0, "error": message, "checked_at_utc": checked_at})
            print(f"::warning title=Feed failed::{label}: {message}", flush=True)
    return articles
