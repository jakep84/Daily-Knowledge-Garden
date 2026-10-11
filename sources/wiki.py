"""Wikipedia history feed and random article with independent health reporting."""
from datetime import datetime, timezone
import requests

HEADERS = {"User-Agent": "DailyKnowledgeGarden/1.2 (https://github.com/jakep84/Daily-Knowledge-Garden)", "Accept": "application/json"}
EVENTS_URL = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{month:02d}/{day:02d}"
RANDOM_URL = "https://en.wikipedia.org/w/api.php"

def fetch_today_and_random(month: int, day: int):
    out = {"today": [], "random": {}, "fetched_at": datetime.now(timezone.utc).isoformat(), "status": []}
    url = EVENTS_URL.format(month=month, day=day)
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        events = response.json().get("events", [])
        out["today"] = [
            {"year": event.get("year"), "text": event.get("text"),
             "pages": [p.get("titles", {}).get("normalized") for p in event.get("pages", [])]}
            for event in events[:10] if event.get("text")
        ]
        out["status"].append({"source": "Wikipedia — On This Day", "status": "ok" if out["today"] else "empty",
                              "count": len(out["today"])})
    except Exception as exc:
        out["status"].append({"source": "Wikipedia — On This Day", "status": "error", "count": 0,
                              "error": f"{type(exc).__name__}: {exc}"})

    try:
        response = requests.get(RANDOM_URL, headers=HEADERS, timeout=20, params={
            "action": "query", "generator": "random", "grnnamespace": 0, "grnlimit": 1,
            "prop": "extracts|info", "exintro": 1, "explaintext": 1, "inprop": "url",
            "format": "json", "formatversion": 2,
        })
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
        page = pages[0] if pages else {}
        if page.get("title"):
            out["random"] = {"title": page["title"], "extract": page.get("extract", ""),
                             "content_urls": page.get("fullurl", "")}
        out["status"].append({"source": "Wikipedia — Random", "status": "ok" if out["random"] else "empty",
                              "count": int(bool(out["random"]))})
    except Exception as exc:
        out["status"].append({"source": "Wikipedia — Random", "status": "error", "count": 0,
                              "error": f"{type(exc).__name__}: {exc}"})
    for row in out["status"]:
        print(f"[SOURCE] {row['source']}: {row['status']} ({row['count']}) {row.get('error','')}", flush=True)
    return out
