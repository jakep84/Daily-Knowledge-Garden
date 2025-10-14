from __future__ import annotations
import os, json, datetime as dt
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
TO_EMAIL = os.getenv("TO_EMAIL", "priddyjacob84@gmail.com")  # safe default

def now_local():
    return dt.datetime.now(ZoneInfo(TZ))

def today_dir() -> Path | None:
    today = now_local().date().isoformat()
    d = DATA / today
    return d if d.exists() else None

def load_raw(d: Path) -> dict:
    p = d / "raw.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def build_email_payload(raw: dict) -> tuple[str, str]:
    date = raw.get("date") or now_local().date().isoformat()
    hn_items = (raw.get("hn") or {}).get("items", [])

    # De-dup by objectID, keep order
    seen = set()
    top = []
    for it in hn_items:
        k = it.get("objectID")
        if k in seen:
            continue
        seen.add(k)
        top.append(it)
        if len(top) >= 10:
            break

    titles_blob = ". ".join([t.get("title") or "" for t in hn_items])
    summary = summarize(titles_blob, max_sentences=4) or "Daily activity captured. See links below."

    lines = []
    lines.append(f"<h2>Daily Knowledge Garden — {date}</h2>")
    lines.append(f"<p><strong>Summary:</strong> {summary}</p>")

    if top:
        lines.append("<h3>Top Hacker News stories</h3><ol>")
        for it in top:
            title = it.get("title") or "(no title)"
            url = it.get("url") or f"https://news.ycombinator.com/item?id={it.get('objectID')}"
            pts = it.get("points", 0)
            c = it.get("num_comments", 0)
            lines.append(f'<li><a href="{url}">{title}</a> — {pts} points, {c} comments</li>')
        lines.append("</ol>")

    # Handy links
    lines.append(f'<p>Full report: <a href="https://github.com/jakep84/Daily-Knowledge-Garden/blob/master/data/{date}/report.md">report.md</a></p>')
    lines.append(f'<p>Live site: <a href="https://jakep84.github.io/Daily-Knowledge-Garden/{date}/">Daily Knowledge Garden — {date}</a></p>')

    subject = f"Daily wrap-up — {date} (Daily Knowledge Garden)"
    html = "\n".join(lines)
    return subject, html

def main():
    # Gate to 22:00 local (top of the hour, since workflow runs hourly)
    nl = now_local()
    should_send = (nl.hour == 22)

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
