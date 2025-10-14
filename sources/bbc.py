# sources/bbc.py
from .news_common import fetch_many

BBC_FEEDS = [
    ("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC — World"),
    ("http://feeds.bbci.co.uk/news/technology/rss.xml", "BBC — Tech"),
    ("http://feeds.bbci.co.uk/news/business/rss.xml", "BBC — Business"),
    ("http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC — Science"),
]

def fetch() -> list[dict]:
    return fetch_many(BBC_FEEDS)
