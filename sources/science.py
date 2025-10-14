# sources/science.py
from .news_common import fetch_many

SCI_FEEDS = [
    ("https://www.sciencenews.org/feed", "ScienceNews"),
    ("https://www.sciencedaily.com/rss/top/science.xml", "ScienceDaily — Top"),
    ("https://www.nature.com/subjects/technology.rss", "Nature — Technology"),
]

def fetch() -> list[dict]:
    return fetch_many(SCI_FEEDS)
