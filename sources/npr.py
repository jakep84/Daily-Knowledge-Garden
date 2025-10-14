# sources/npr.py
from .news_common import fetch_many

NPR_FEEDS = [
    ("https://feeds.npr.org/1001/rss.xml", "NPR — Top Stories"),
    ("https://feeds.npr.org/1019/rss.xml", "NPR — Politics"),
    ("https://feeds.npr.org/1007/rss.xml", "NPR — Business"),
    ("https://feeds.npr.org/1008/rss.xml", "NPR — Science"),
    ("https://feeds.npr.org/1013/rss.xml", "NPR — Technology"),
]

def fetch() -> list[dict]:
    return fetch_many(NPR_FEEDS)
