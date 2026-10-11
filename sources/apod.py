"""NASA Astronomy Picture of the Day, using NASA's current public WordPress API."""
from datetime import datetime, timezone
import requests

APOD_API = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"

def fetch_apod():
    out = {"fetched_at": datetime.now(timezone.utc).isoformat(), "entry": None}
    try:
        response = requests.get(APOD_API, timeout=25, headers={
            "User-Agent": "DailyKnowledgeGarden/1.2 (https://github.com/jakep84/Daily-Knowledge-Garden)",
            "Accept": "application/json",
        })
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            data = data[0] if data else {}
        title = data.get("title")
        if isinstance(title, dict):
            title = title.get("rendered")
        link = data.get("permalink") or data.get("url")
        if not title or not link:
            raise ValueError("APOD response missing title or link")
        out["entry"] = {"title": title, "link": link, "summary": data.get("explanation", ""),
                        "published": data.get("date", ""), "media_type": data.get("media_type", "")}
        out["status"] = [{"source": "NASA — APOD", "status": "ok", "count": 1}]
    except Exception as exc:
        out["status"] = [{"source": "NASA — APOD", "status": "error", "count": 0,
                          "error": f"{type(exc).__name__}: {exc}"}]
    for row in out["status"]:
        print(f"[SOURCE] {row['source']}: {row['status']} {row.get('error','')}", flush=True)
    return out
