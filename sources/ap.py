# sources/ap.py
from .news_common import fetch_many

AP_FEEDS = [
    ("https://apnews.com/hub/apf-topnews?utm_source=apnews.com&utm_medium=referral&utm_campaign=aprss", "AP — Top"),
    ("https://apnews.com/hub/politics?utm_source=apnews.com&utm_medium=referral&utm_campaign=aprss", "AP — Politics"),
    ("https://apnews.com/hub/business?utm_source=apnews.com&utm_medium=referral&utm_campaign=aprss", "AP — Business"),
]

def fetch() -> list[dict]:
    return fetch_many(AP_FEEDS)
