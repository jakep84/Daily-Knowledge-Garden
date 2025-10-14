import datetime as dt
from pathlib import Path

from config import DATA_DIR, IMG_DIRNAME, PLOTS_DIRNAME, RUN_DATE
from utils.files import write_json, write_text, replace_between_markers
from utils.summarize import summarize
from utils.plots import bar_plot

# Existing data sources
from sources.hn import fetch_top
from sources.wiki import fetch_today_and_random
from sources.apod import fetch_apod

# New multi-source news modules
from sources import reuters as src_reuters
from sources import bbc as src_bbc
from sources import ap as src_ap
from sources import npr as src_npr
from sources import science as src_science
from sources import google_local as src_local

ROOT = Path(__file__).parent.resolve()

# -----------------------------------------------------------
# Directory setup
# -----------------------------------------------------------
def today_dir():
    d = DATA_DIR / str(RUN_DATE)
    d.mkdir(parents=True, exist_ok=True)
    (d / IMG_DIRNAME).mkdir(exist_ok=True)
    (d / PLOTS_DIRNAME).mkdir(exist_ok=True)
    return d


# -----------------------------------------------------------
# Aggregate all feeds into one payload
# -----------------------------------------------------------
def build_report_payload():
    hn = fetch_top()
    wiki = fetch_today_and_random(RUN_DATE.month, RUN_DATE.day)
    apod = fetch_apod()

    # --- World news feeds ---
    world = []
    for src in [src_reuters, src_bbc, src_ap, src_npr, src_science]:
        try:
            world += src.fetch()
        except Exception as e:
            world.append({"title": f"(Error fetching {src.__name__})", "error": str(e)})

    # --- Local feeds ---
    local = []
    try:
        local = src_local.fetch()
    except Exception as e:
        local.append({"title": f"(Error fetching local news)", "error": str(e)})

    news = {"world": world[:60], "local": local[:30]}  # keep it light

    return {"date": str(RUN_DATE), "hn": hn, "wiki": wiki, "apod": apod, "news": news}


# -----------------------------------------------------------
# Generate visual charts
# -----------------------------------------------------------
def generate_charts(payload, out_dir: Path):
    titles = [x.get("title") or "" for x in payload["hn"].get("items", [])][:10]
    points = [int(x.get("points", 0)) for x in payload["hn"].get("items", [])][:10]
    labels = [t[:18] + ("…" if len(t) > 18 else "") for t in titles]
    plot_path = out_dir / PLOTS_DIRNAME / "hn_top10_points.png"

    if titles:
        bar_plot("Hacker News: Top 10 stories (points)", labels, points, plot_path)
        return {"hn_top10_points": str(plot_path.relative_to(ROOT))}
    return {"hn_top10_points": None}


# -----------------------------------------------------------
# Markdown builder with concise global + local digest
# -----------------------------------------------------------
def make_markdown(payload, charts, out_dir: Path):
    # Helper for deduplication
    def _uniq(items, key="title"):
        seen, out = set(), []
        for it in items:
            t = (it or {}).get(key)
            if not t or t in seen:
                continue
            seen.add(t)
            out.append(it)
        return out

    # Hacker News section
    hn_items = payload["hn"].get("items", [])
    hn_top = hn_items[:5]
    hn_lines = []
    for it in hn_top:
        title = it.get("title") or "(no title)"
        object_id = it.get("objectID")
        url = it.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        points = it.get("points", 0)
        comments = it.get("num_comments", 0)
        hn_lines.append(f"- [{title}]({url}) — {points} points, {comments} comments")

    hn_block = "\n".join(hn_lines) if hn_lines else "_No data_"

    # Chart
    chart_md = f"![HN Points Chart]({charts['hn_top10_points']})" if charts.get("hn_top10_points") else ""

    # --- Global + Local News ---
    world_items = _uniq((payload.get("news", {}) or {}).get("world", []))[:5]
    local_items = _uniq((payload.get("news", {}) or {}).get("local", []))[:5]

    def _lines(items):
        return (
            "\n".join(
                [f"- [{it.get('title')}]({it.get('link')}) — {it.get('source')}" for it in items]
            )
            if items
            else "_No data_"
        )

    world_block = _lines(world_items)
    local_block = _lines(local_items)

    # Quick synthesized daily summary from all sources
    try:
        all_titles = [w.get("title", "") for w in payload["news"]["world"][:30]] + [
            l.get("title", "") for l in payload["news"]["local"][:15]
        ]
        blob = ". ".join([t for t in all_titles if t])
        summary_text = summarize(blob, max_sentences=3)
    except Exception:
        summary_text = "Summary unavailable."

    # Wikipedia — On This Day
    today_events = (payload.get("wiki", {}) or {}).get("today", [])[:5]
    today_block = (
        "\n".join([f"- **{e.get('year')}** — {e.get('text')}" for e in today_events])
        if today_events
        else "_No data_"
    )

    # Wikipedia Random
    random = (payload.get("wiki", {}) or {}).get("random") or {}
    random_title = random.get("title", "N/A")
    random_blurb = summarize((random.get("extract") or "")[:2000], max_sentences=2)
    random_url = random.get("content_urls") or ""

    # APOD
    apod_entry = (payload.get("apod", {}) or {}).get("entry")
    apod_line = f"[{apod_entry['title']}]({apod_entry['link']})" if apod_entry else "Unavailable"

    md = (
        f"# Daily Knowledge Garden — {payload['date']}\n\n"
        f"## 🧭 Daily Summary\n{summary_text}\n\n"
        f"## 🌍 Global News (cross-source)\n{world_block}\n\n"
        f"## 🏙️ Local News\n{local_block}\n\n"
        f"## 🚀 Hacker News (Top 5)\n{hn_block}\n\n"
        f"{chart_md}\n\n"
        f"## 🌍 Wikipedia — On This Day (selected)\n{today_block}\n\n"
        f"## 🎲 Wikipedia — Random Article\n"
        f"**{random_title}**  \n{random_blurb}\n{random_url}\n\n"
        f"## 🌌 NASA APOD\n{apod_line}\n"
    )

    out_md = out_dir / "report.md"
    write_text(out_md, md)
    return out_md


# -----------------------------------------------------------
# README highlights updater
# -----------------------------------------------------------
def update_readme(payload, charts, report_md_path: Path):
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    latest_run = f"{payload['date']} (UTC)"
    readme = replace_between_markers(readme, "<!--LATEST_RUN-->", "<!--/LATEST_RUN-->", latest_run)

    items = payload["hn"].get("items", [])
    top = items[0] if items else {}
    top_title = top.get("title", "N/A")
    object_id = top.get("objectID")
    top_url = top.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    apod = payload["apod"].get("entry")
    apod_title = apod.get("title") if apod else "N/A"
    apod_link = apod.get("link") if apod else ""

    highlights_md = (
        f"- **HN #1:** [{top_title}]({top_url})\n"
        f"- **APOD:** [{apod_title}]({apod_link})\n"
        f"- **Daily Report:** [{payload['date']}/report.md](/data/{payload['date']}/report.md)\n"
    )

    readme = replace_between_markers(readme, "<!--HIGHLIGHTS-->", "<!--/HIGHLIGHTS-->", highlights_md.strip())
    readme_path.write_text(readme, encoding="utf-8")


# -----------------------------------------------------------
# Main entrypoint
# -----------------------------------------------------------
def main():
    out_dir = today_dir()
    payload = build_report_payload()
    write_json(out_dir / "raw.json", payload)
    charts = generate_charts(payload, out_dir)
    report_md = make_markdown(payload, charts, out_dir)
    update_readme(payload, charts, report_md)
    print("✅ Daily Knowledge Garden updated successfully.")


if __name__ == "__main__":
    main()
