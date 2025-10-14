# sources/reuters.py
from .news_common import fetch_many

REUTERS_FEEDS = [
    ("https://feeds.reuters.com/reuters/worldNews", "Reuters — World"),
    ("https://feeds.reuters.com/reuters/businessNews", "Reuters — Business"),
    ("https://feeds.reuters.com/reuters/technologyNews", "Reuters — Tech"),
    ("https://feeds.reuters.com/reuters/scienceNews", "Reuters — Science"),
]

def fetch() -> list[dict]:
    return fetch_many(REUTERS_FEEDS)
