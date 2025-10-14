import datetime as dt
from pathlib import Path
from typing import List, Dict, Any

from config import DATA_DIR, IMG_DIRNAME, PLOTS_DIRNAME, RUN_DATE
from utils.files import write_json, write_text, replace_between_markers
from utils.summarize import summarize
from utils.plots import bar_plot

# Existing sources
from sources.hn import fetch_top
from sources.wiki import fetch_today_and_random
from sources.apod import fetch_apod

# Cross-source news
from sources import reuters as src_reuters
from sources import bbc as src_bbc
from sources import ap as src_ap
from sources import npr as src_npr
from sources import science as src_science
from sources import google_local as src_local

ROOT = Path(__file__).parent.resolve()


# -----------------------------------------------------------
# Helpers (Growth Mode)
# -----------------------------------------------------------
def _uniq(items: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
    """Stable de-duplication by one or more keys."""
    seen = set()
    out = []
    for it in items or []:
        key = tuple((it or {}).get(k) for k in keys)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _load_json(p: Path) -> Dict[str, Any]:
    if p.exists():
        try:
            return __import__("json").loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


# -----------------------------------------------------------
# Directory setup
# -----------------------------------------------------------
def today_dir() -> Path:
    d = DATA_DIR / str(RUN_DATE)
    d.mkdir(parents=True, exist_ok=True)
    (d / IMG_DIRNAME).mkdir(exist_ok=True)
    (d / PLOTS_DIRNAME).mkdir(exist_ok=True)
    (d / "runs").mkdir(parents=True, exist_ok=True)
    return d


# -----------------------------------------------------------
# Fetchers
# -----------------------------------------------------------
def fetch_all_sources() -> Dict[str, Any]:
    """Fetch a single-run snapshot from all sources."""
    hn = fetch_top()
    wiki = fetch_today_and_random(RUN_DATE.month, RUN_DATE.day)
    apod = fetch_apod()

    # World news (multiple feeds)
    world = []
    for src in [src_reuters, src_bbc, src_ap, src_npr, src_science]:
        try:
            world += src.fetch()
        except Exception as e:
            world.append({"title": f"(Error fetching {src.__name__})", "error": str(e)})

    # Local news
    local = []
    try:
        local = src_local.fetch()
    except Exception as e:
        local.append({"title": "(Error fetching local news)", "error": str(e)})

    news = {"world": world, "local": local}

    snapshot = {
        "date": str(RUN_DATE),
        "collected_at_utc": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hn": hn,
        "wiki": wiki,
        "apod": apod,
        "news": news,
    }
    return snapshot


def merge_day_payload(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a new snapshot into the day's combined payload."""
    out = {
        "date": new.get("date"),
        "last_updated_utc": new.get("collected_at_utc"),
        # These will be filled below
        "hn": {"items": []},
        "wiki": new.get("wiki") or {},
        "apod": new.get("apod") or {},
        "news": {"world": [], "local": []},
        "runs": (existing.get("runs") or []) + [new.get("collected_at_utc")],
    }

    # Merge HN items (dedupe by objectID)
    old_hn = (existing.get("hn") or {}).get("items") or []
    new_hn = (new.get("hn") or {}).get("items") or []
    merged_hn = _uniq(old_hn + new_hn, keys=["objectID"])
    out["hn"]["items"] = merged_hn[:200]  # cap for sanity

    # Merge news lists (dedupe by title+link)
    old_world = ((existing.get("news") or {}).get("world") or [])
    old_local = ((existing.get("news") or {}).get("local") or [])
    new_world = ((new.get("news") or {}).get("world") or [])
    new_local = ((new.get("news") or {}).get("local") or [])

    out["news"]["world"] = _uniq(old_world + new_world, keys=["title", "link"])[:300]
    out["news"]["local"] = _uniq(old_local + new_local, keys=["title", "link"])[:200]

    # Prefer the newest wiki/APOD if present; otherwise keep existing
    if not out["wiki"]:
        out["wiki"] = existing.get("wiki") or {}
    if not out["apod"]:
        out["apod"] = existing.get("apod") or {}

    return out


# -----------------------------------------------------------
# Charts
# -----------------------------------------------------------
def generate_charts(latest_snapshot: Dict[str, Any], out_dir: Path) -> Dict[str, str | None]:
    titles = [x.get("title") or "" for x in (latest_snapshot.get("hn") or {}).get("items", [])][:10]
    points = [int(x.get("points", 0)) for x in (latest_snapshot.get("hn") or {}).get("items", [])][:10]
    labels = [t[:18] + ("…" if len(t) > 18 else "") for t in titles]
    plot_path = out_dir / PLOTS_DIRNAME / "hn_top10_points.png"

    if titles:
        bar_plot("Hacker News: Top 10 stories (points)", labels, points, plot_path)
        return {"hn_top10_points": str(plot_path.relative_to(ROOT))}
    return {"hn_top10_points": None}


# -----------------------------------------------------------
# Markdown builder (combined payload)
# -----------------------------------------------------------
def make_markdown(payload: Dict[str, Any], charts: Dict[str, Any], out_dir: Path) -> Path:
    def _uniq_titles(items: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        return _uniq(items, keys=["title"])[:n]

    # Global & Local (from combined payload)
    world_items = _uniq_titles((payload.get("news", {}) or {}).get("world", []), 5)
    local_items = _uniq_titles((payload.get("news", {}) or {}).get("local", []), 5)

    def _lines(items):
        return (
            "\n".join([f"- [{it.get('title')}]({it.get('link')}) — {it.get('source')}" for it in items])
            if items
            else "_No data_"
        )

    world_block = _lines(world_items)
    local_block = _lines(local_items)

    # Synthesized daily summary from all titles (combined)
    try:
        all_titles = [w.get("title", "") for w in (payload.get("news") or {}).get("world", [])[:30]] + \
                     [l.get("title", "") for l in (payload.get("news") or {}).get("local", [])[:15]]
        blob = ". ".join([t for t in all_titles if t])
        summary_text = summarize(blob, max_sentences=3)
    except Exception:
        summary_text = "Summary unavailable."

    # Hacker News (Top 5 from combined list)
    hn_items = (payload.get("hn") or {}).get("items", [])[:5]
    hn_lines = []
    for it in hn_items:
        title = it.get("title") or "(no title)"
        object_id = it.get("objectID")
        url = it.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        points = it.get("points", 0)
        comments = it.get("num_comments", 0)
        hn_lines.append(f"- [{title}]({url}) — {points} points, {comments} comments")
    hn_block = "\n".join(hn_lines) if hn_lines else "_No data_"

    chart_md = f"![HN Points Chart]({charts['hn_top10_points']})" if charts.get("hn_top10_points") else ""

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
        f"\n<sub>Runs so far today: {len(payload.get('runs', []))}</sub>\n"
    )

    out_md = out_dir / "report.md"
    write_text(out_md, md)
    return out_md


# -----------------------------------------------------------
# README updater
# -----------------------------------------------------------
def update_readme(payload: Dict[str, Any], charts: Dict[str, Any], report_md_path: Path):
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    latest_run = f"{payload['date']} (UTC)"
    readme = replace_between_markers(readme, "<!--LATEST_RUN-->", "<!--/LATEST_RUN-->", latest_run)

    items = (payload.get("hn") or {}).get("items", [])
    top = items[0] if items else {}
    top_title = top.get("title", "N/A")
    object_id = top.get("objectID")
    top_url = top.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    apod = payload.get("apod", {}).get("entry")
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
# Main (Growth Mode)
# -----------------------------------------------------------
def main():
    out_dir = today_dir()

    # 1) Fetch a fresh snapshot
    snapshot = fetch_all_sources()

    # 2) Save this run under runs/<HHMMSS>/raw.json
    run_id = dt.datetime.utcnow().strftime("%H%M%S")
    run_dir = out_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "raw.json", snapshot)

    # 3) Load the day's combined payload (if any) and merge
    combined_path = out_dir / "raw.json"
    existing = _load_json(combined_path)
    combined = merge_day_payload(existing, snapshot)
    write_json(combined_path, combined)

    # 4) Charts from the latest snapshot (so the chart reflects the newest HN)
    charts = generate_charts(snapshot, out_dir)

    # 5) Build markdown (from combined payload so the page grows)
    report_md = make_markdown(combined, charts, out_dir)

    # 6) Update README highlights
    update_readme(combined, charts, report_md)

    print(
        f"✅ Growth mode run complete: runs={len(combined.get('runs', []))}, "
        f"date={combined.get('date')}, updated={combined.get('last_updated_utc')}"
    )


if __name__ == "__main__":
    main()
