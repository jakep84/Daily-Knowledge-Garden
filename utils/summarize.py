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
