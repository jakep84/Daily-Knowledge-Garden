import requests
from datetime import datetime, timezone

ALGOLIA_TOP = "https://hn.algolia.com/api/v1/search?tags=front_page"

def fetch_top():
    r = requests.get(ALGOLIA_TOP, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = []
    for hit in data.get("hits", []):
        items.append({
            "title": hit.get("title"),
            "url": hit.get("url"),
            "points": hit.get("points", 0),
            "author": hit.get("author"),
            "num_comments": hit.get("num_comments", 0),
            "created_at": hit.get("created_at"),
            "objectID": hit.get("objectID"),
        })
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": items
    }
