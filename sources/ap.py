"""AP headlines via publisher-filtered Google News RSS (not an official AP feed)."""
from urllib.parse import quote_plus
from .news_common import fetch_many

def google_rss(query):
    return "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"

AP_FEEDS = [
    (google_rss("site:apnews.com when:2d"), "AP — Headlines (Google News)"),
    (google_rss("site:apnews.com/hub/politics when:2d"), "AP — Politics (Google News)"),
    (google_rss("site:apnews.com/hub/business when:2d"), "AP — Business (Google News)"),
]

def fetch() -> list[dict]:
    return fetch_many(AP_FEEDS)
