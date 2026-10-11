"""Reuters headlines via publisher-filtered Google News RSS (not an official Reuters feed)."""
from urllib.parse import quote_plus
from .news_common import fetch_many

def google_rss(query):
    return "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"

REUTERS_FEEDS = [
    (google_rss("site:reuters.com when:2d"), "Reuters — Headlines (Google News)"),
    (google_rss("site:reuters.com/world when:2d"), "Reuters — World (Google News)"),
    (google_rss("site:reuters.com/business when:2d"), "Reuters — Business (Google News)"),
]

def fetch() -> list[dict]:
    return fetch_many(REUTERS_FEEDS)
