# sources/google_local.py
import os
from urllib.parse import quote_plus
from .news_common import fetch_many

# Set your area once (repo variable or .env): LOCAL_QUERY="Austin, TX" (examples: "Northern Virginia", "San Francisco CA")
LOCAL_QUERY = os.getenv("LOCAL_QUERY", "Northern Virginia")

def _google_news_search(q: str):
    # Google News RSS search; region US English
    base = "https://news.google.com/rss/search"
    url = f"{base}?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"
    return url

def fetch() -> list[dict]:
    feeds = [
        (_google_news_search(LOCAL_QUERY), f"Google News — {LOCAL_QUERY}"),
        (_google_news_search(f"{LOCAL_QUERY} traffic OR transit"), f"Google News — {LOCAL_QUERY} traffic"),
        (_google_news_search(f"{LOCAL_QUERY} weather warning OR advisory"), f"Google News — {LOCAL_QUERY} weather"),
    ]
    return fetch_many(feeds)
