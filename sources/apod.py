"""NASA Astronomy Picture of the Day, using NASA's current public WordPress API."""
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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
        image_url = ""
        try:
            page = requests.get(link, timeout=15, headers={"User-Agent": "DailyKnowledgeGarden/1.2"})
            page.raise_for_status()
            soup = BeautifulSoup(page.text, "html.parser")
            og = soup.find("meta", attrs={"property": "og:image"})
            candidate = (og.get("content") or "") if og else ""
            parsed = urlparse(candidate)
            if parsed.scheme == "https" and (parsed.hostname or "").endswith(".nasa.gov"):
                image_url = candidate
        except requests.RequestException as exc:
            print(f"::warning title=NASA preview::Image lookup failed: {exc}")
        out["entry"] = {"title": title, "link": link, "image_url": image_url, "summary": data.get("explanation", ""),
                        "published": data.get("date", ""), "media_type": data.get("media_type", "")}
        out["status"] = [{"source": "NASA — APOD", "status": "ok", "count": 1}]
    except Exception as exc:
        out["status"] = [{"source": "NASA — APOD", "status": "error", "count": 0,
                          "error": f"{type(exc).__name__}: {exc}"}]
    for row in out["status"]:
        print(f"[SOURCE] {row['source']}: {row['status']} {row.get('error','')}", flush=True)
    return out
