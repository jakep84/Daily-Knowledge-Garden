import requests
from datetime import datetime, timezone
WIKI_TODAY = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
WIKI_RANDOM = "https://en.wikipedia.org/api/rest_v1/page/random/summary"

def fetch_today_and_random(month: int, day: int):
    out = {"today": [], "random": {}, "fetched_at": datetime.now(timezone.utc).isoformat()}
    # On this day
    r = requests.get(WIKI_TODAY.format(month=month, day=day), timeout=20)
    if r.ok:
        out["today"] = [
            {
                "year": e.get("year"),
                "text": e.get("text"),
                "pages": [p.get("titles", {}).get("normalized") for p in e.get("pages", [])]
            } for e in r.json().get("events", [])[:10]
        ]
    # Random
    rr = requests.get(WIKI_RANDOM, timeout=20)
    if rr.ok:
        j = rr.json()
        out["random"] = {
            "title": j.get("title"),
            "description": j.get("description"),
            "extract": j.get("extract"),
            "content_urls": j.get("content_urls", {}).get("desktop", {}).get("page")
        }
    return out
