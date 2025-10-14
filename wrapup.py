from __future__ import annotations
import os, sys, json, datetime as dt
from pathlib import Path

# --- Load .env locally; harmless in Actions where vars come from secrets/vars
try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present
except Exception:
    pass

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:
    from backports.zoneinfo import ZoneInfo  # unlikely on Actions

from utils.summarize import summarize

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

TZ = os.getenv("TIMEZONE", "America/New_York")
TO_EMAIL = os.getenv("TO_EMAIL", "priddyjacob84@gmail.com")  # default for convenience


# ---------------------------
# Helpers
# ---------------------------
def now_local():
    return dt.datetime.now(ZoneInfo(TZ))

def today_dir() -> Path | None:
    today = now_local().date().isoformat()
    d = DATA / today
    return d if d.exists() else None

def load_raw(d: Path) -> dict:
    p = d / "raw.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def _uniq(items, key="title"):
    seen, out = set(), []
    for it in items or []:
        k = (it or {}).get(key) or ""
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out

def _fmt_list(items, take=5, with_source=True):
    items = _uniq(items)[:take]
    if not items:
        return "<p><em>No data</em></p>"
    lis = []
    for it in items:
        title = (it or {}).get("title") or "(no title)"
        link = (it or {}).get("link") or "#"
        src  = (it or {}).get("source") or ""
        suffix = f" — {src}" if (with_source and src) else ""
        lis.append(f'<li><a href="{link}">{title}</a>{suffix}</li>')
    return "<ol>\n" + "\n".join(lis) + "\n</ol>"

def synthesize_day(raw: dict) -> str:
    """
    Create a short, neutral daily brief (2–3 sentences) from
    global + local news headlines, with HN titles as context.
    """
    news = (raw.get("news") or {})
    world = news.get("world") or []
    local = news.get("local") or []
    hn_items = (raw.get("hn") or {}).get("items", []) or []

    titles = []
    # Prioritize world + local for the day’s brief
    titles += [ (it or {}).get("title") or "" for it in world[:40] ]
    titles += [ (it or {}).get("title") or "" for it in local[:20] ]
    # Add a bit of HN context (tech/industry pulse)
    titles += [ (it or {}).get("title") or "" for it in hn_items[:15] ]

    blob = ". ".join([t for t in titles if t]).strip()
    if not blob:
        return "Today’s coverage was light. See the links below for details."

    # Produce a crisp 2–3 sentence neutral brief
    brief = summarize(blob, max_sentences=3)
    return brief or "A cross-section of global, local, and technology headlines shaped today’s coverage."

def build_email_payload(raw: dict) -> tuple[str, str]:
    date = raw.get("date") or now_local().date().isoformat()

    # Sections: Global, Local, Hacker News
    news = (raw.get("news") or {})
    world = news.get("world") or []
    local = news.get("local") or []
    hn_items = (raw.get("hn") or {}).get("items", []) or []

    # Dedup + take N
    world_block = _fmt_list(world, take=5, with_source=True)
    local_block = _fmt_list(local, take=5, with_source=True)

    # HN Top 10 (dedup by objectID)
    seen_ids, hn_top = set(), []
    for it in hn_items:
        oid = (it or {}).get("objectID")
        if oid in seen_ids:
            continue
        seen_ids.add(oid)
        hn_top.append(it)
        if len(hn_top) >= 10:
            break

    if hn_top:
        lis = []
        for it in hn_top:
            title = it.get("title") or "(no title)"
            url = it.get("url") or f"https://news.ycombinator.com/item?id={it.get('objectID')}"
            pts = it.get("points", 0)
            c = it.get("num_comments", 0)
            lis.append(f'<li><a href="{url}">{title}</a> — {pts} points, {c} comments</li>')
        hn_block = "<ol>\n" + "\n".join(lis) + "\n</ol>"
    else:
        hn_block = "<p><em>No data</em></p>"

    # Daily brief
    daily_brief = synthesize_day(raw)

    # Links to artifacts
    report_link = f"https://github.com/jakep84/Daily-Knowledge-Garden/blob/master/data/{date}/report.md"
    site_link = f"https://jakep84.github.io/Daily-Knowledge-Garden/{date}/"

    # Build HTML
    lines = []
    lines.append(f"<h2>Daily Knowledge Garden — {date}</h2>")
    lines.append(f"<p><strong>Daily Brief:</strong> {daily_brief}</p>")

    lines.append("<h3>🌍 Global — Top 5</h3>")
    lines.append(world_block)

    lines.append("<h3>🏙️ Local — Top 5</h3>")
    lines.append(local_block)

    lines.append("<h3>🚀 Hacker News — Top 10</h3>")
    lines.append(hn_block)

    lines.append(f'<p>Full report: <a href="{report_link}">report.md</a></p>')
    lines.append(f'<p>Live site: <a href="{site_link}">Daily Knowledge Garden — {date}</a></p>')

    subject = f"Daily wrap-up — {date} (Daily Knowledge Garden)"
    html = "\n".join(lines)
    return subject, html


# ---------------------------
# Main
# ---------------------------
def main():
    # Allow local testing anytime with --test
    force_test = ("--test" in sys.argv)

    # Gate to 22:00 local (top of the hour), unless --test provided
    nl = now_local()
    should_send = force_test or (nl.hour == 22)

    # Expose to GitHub Actions as an output
    gh_out = os.getenv("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"should_send={'true' if should_send else 'false'}\n")

    if not should_send:
        print(f"[wrapup] Not 22:00 in {TZ} (now {nl}). Skipping.")
        return

    d = today_dir()
    if not d:
        print("[wrapup] No data folder for today; skipping email.")
        return

    raw = load_raw(d)
    subject, html = build_email_payload(raw)

    (OUT / "email_subject.txt").write_text(subject, encoding="utf-8")
    (OUT / "email.html").write_text(html, encoding="utf-8")
    print("[wrapup] Email prepared at out/email.html")

if __name__ == "__main__":
    main()
