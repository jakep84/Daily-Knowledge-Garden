import feedparser
from datetime import datetime, timezone

APOD_RSS = "https://apod.nasa.gov/apod.rss"

def fetch_apod():
    feed = feedparser.parse(APOD_RSS)
    best = feed.entries[0] if feed.entries else None
    if not best:
        return {"fetched_at": datetime.now(timezone.utc).isoformat(), "entry": None}
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "entry": {
            "title": best.get("title"),
            "link": best.get("link"),
            "summary": best.get("summary"),
            "published": best.get("published"),
        }
    }
