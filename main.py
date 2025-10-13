import datetime as dt
from pathlib import Path
import json

from config import DATA_DIR, IMG_DIRNAME, PLOTS_DIRNAME, RUN_DATE
from utils.files import write_json, write_text, replace_between_markers
from utils.summarize import summarize
from utils.plots import bar_plot

from sources.hn import fetch_top
from sources.wiki import fetch_today_and_random
from sources.apod import fetch_apod

ROOT = Path(__file__).parent.resolve()

def today_dir():
    d = DATA_DIR / str(RUN_DATE)
    d.mkdir(parents=True, exist_ok=True)
    (d / IMG_DIRNAME).mkdir(exist_ok=True)
    (d / PLOTS_DIRNAME).mkdir(exist_ok=True)
    return d

def build_report_payload():
    hn = fetch_top()
    wiki = fetch_today_and_random(RUN_DATE.month, RUN_DATE.day)
    apod = fetch_apod()
    return {"date": str(RUN_DATE), "hn": hn, "wiki": wiki, "apod": apod}

def generate_charts(payload, out_dir: Path):
    # simple HN points vs. title length
    titles = [x["title"] or "" for x in payload["hn"]["items"]][:10]
    points = [x.get("points", 0) for x in payload["hn"]["items"]][:10]
    labels = [t[:18] + ("…" if len(t) > 18 else "") for t in titles]
    plot_path = out_dir / PLOTS_DIRNAME / "hn_top10_points.png"
    if titles:
        bar_plot("Hacker News: Top 10 stories (points)", labels, points, plot_path)
    return {"hn_top10_points": str(plot_path.relative_to(ROOT)) if titles else None}

def make_markdown(payload, charts, out_dir: Path):
    hn_top = payload["hn"]["items"][:5]
    hn_lines = []
    for it in hn_top:
        t = it.get("title") or "(no title)"
        url = it.get("url") or f"https://news.ycombinator.com/item?id={it.get('objectID')}"
        hn_lines.append(f"- [{t}]({url}) — {it.get('points',0)} points, {it.get('num_comments',0)} comments")

    random = payload["wiki"]["random"]
    random_blurb = summarize((random.get("extract") or "")[:2000], max_sentences=2) if random else ""

    apod = payload["apod"]["entry"]
    apod_line = f"[{apod['title']}]({apod['link']})" if apod else "Unavailable"

    md = f"""# Daily Knowledge Garden — {payload['date']}

## 🚀 Hacker News (Top 5)
{chr(10).join(hn_lines) if hn_lines else "_No data_"}

{"![HN Points Chart](" + charts["hn_top10_points"] + ")" if charts.get("hn_top10_points") else ""}

## 🌍 Wikipedia — On This Day (selected)
{"".join([f"- **{e['year']}** — {e['text']}\\n" for e in (payload['wiki'].get('today') or [])[:5]]) or "_No data_"}

## 🎲 Wikipedia — Random Article
**{random.get('title') if random else 'N/A'}**  
{random_blurb}
{(random.get('content_urls') or '') if random else ''}

## 🌌 NASA APOD
{apod_line}
"""
    out_md = out_dir / "report.md"
    write_text(out_md, md)
    return out_md

def update_readme(payload, charts, report_md_path: Path):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    latest_run = f"{payload['date']} (UTC)"
    readme = replace_between_markers(readme, "<!--LATEST_RUN-->", "<!--/LATEST_RUN-->", latest_run)

    # highlight: show top HN title + APOD title
    top = payload["hn"]["items"][0] if payload["hn"]["items"] else {}
    top_title = top.get("title", "N/A")
    top_url = top.get("url") or (f"https://news.ycombinator.com/item?id={top.get('objectID')}" if top else "")
    apod = payload["apod"]["entry"]
    apod_title = apod.get("title") if apod else "N/A"
    apod_link = apod.get("link") if apod else ""

    highlights_md = f"""
- **HN #1:** [{top_title}]({top_url})
- **APOD:** [{apod_title}]({apod_link})
- **Daily Report:** [{payload['date']}/report.md](/data/{payload['date']}/report.md)
"""
    readme = replace_between_markers(readme, "<!--HIGHLIGHTS-->", "<!--/HIGHLIGHTS-->", highlights_md.strip())
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

def main():
    out_dir = today_dir()
    payload = build_report_payload()
    write_json(out_dir / "raw.json", payload)
    charts = generate_charts(payload, out_dir)
    report_md = make_markdown(payload, charts, out_dir)
    update_readme(payload, charts, report_md)

if __name__ == "__main__":
    main()
