import re
from collections import Counter

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+")
_SENT = re.compile(r"(?<=[.!?])\s+")

def tokenize(text):
    return _WORD.findall(text or "")

def sentence_split(text):
    # keep sentence separators minimal assumptions
    return [s.strip() for s in _SENT.split(text or "") if s.strip()]

def summarize(text, max_sentences=3):
    """Simple frequency-based extractive summary (no external models)."""
    if not text:
        return ""
    sentences = sentence_split(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    words = [w.lower() for w in tokenize(text)]
    freq = Counter(words)
    # ignore very common short words
    for stop in ["the","a","an","and","or","of","to","in","on","for","with","is","are","was","were","by","from","as","at","that","this","it","be"]:
        freq.pop(stop, None)

    scores = []
    for s in sentences:
        sw = [w.lower() for w in tokenize(s)]
        score = sum(freq.get(w, 0) for w in sw) / (len(sw) + 1e-9)
        scores.append((score, s))

    best = [s for _, s in sorted(scores, key=lambda x: x[0], reverse=True)[:max_sentences]]
    # preserve original order
    ordered = [s for s in sentences if s in best]
    return " ".join(ordered)

from datetime import datetime
from email.utils import parsedate_to_datetime

def _news_time(item):
    published = item.get("published", "")
    try:
        return parsedate_to_datetime(published).timestamp()
    except (ValueError, TypeError, IndexError, OverflowError):
        try:
            return datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError, OverflowError):
            return 0

def _headline_key(row):
    """Prefer stable article identity, then normalize headline punctuation."""
    from urllib.parse import urlsplit, urlunsplit
    link = row.get("link", "")
    if link:
        url = urlsplit(link)
        if url.netloc and "news.google.com" not in url.netloc:
            return "url:" + url.netloc.lower() + url.path.rstrip("/").lower()
    title = row.get("title", "")
    title = re.sub(r"\s+-\s+[^-]{2,60}$", "", title)
    title = re.sub(r"\b(the|a|an)\b", "", title.lower())
    return "title:" + re.sub(r"[^a-z0-9]+", "", title)

def top_headlines(items, limit=5, max_age_hours=72):
    """Fresh, diverse, deduplicated headlines; unknown dates retained as fallback."""
    from datetime import timezone
    now = datetime.now(timezone.utc).timestamp()
    rows = sorted((r for r in items or [] if r.get("title") and r.get("link")),
                  key=_news_time, reverse=True)
    fresh = [r for r in rows if not _news_time(r) or 0 <= now - _news_time(r) <= max_age_hours * 3600]
    seen, primary, backup, counts = set(), [], [], {}
    for row in fresh:
        key = _headline_key(row)
        if key in seen:
            continue
        seen.add(key)
        src = row.get("source", "").split(" — ")[0]
        if counts.get(src, 0) < 2 and len(primary) < limit:
            primary.append(row)
            counts[src] = counts.get(src, 0) + 1
        else:
            backup.append(row)
    return (primary + backup)[:limit]

def summarize_news(news):
    """Headline-only daily overview; does not invent details from full articles."""
    global_items = top_headlines((news or {}).get("world", []), 3)
    local_items = top_headlines((news or {}).get("local", []), 2)
    parts = []
    if global_items:
        parts.append("Global coverage includes " + "; ".join(row["title"] for row in global_items) + ".")
    if local_items:
        parts.append("Local coverage includes " + "; ".join(row["title"] for row in local_items) + ".")
    return " ".join(parts) or "No current news headlines were collected."
