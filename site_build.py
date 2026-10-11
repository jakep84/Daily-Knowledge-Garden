"""Build a readable, static, accessible Daily Knowledge Garden dashboard."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from html import escape
from urllib.parse import urlparse
import json
import re
import shutil
import markdown

from utils.summarize import top_headlines, summarize_news, _news_time

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"
DOCS = ROOT / "docs"
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CSS = """
<style>
:root{color-scheme:dark;--bg:#0b1118;--surface:#151f2b;--line:#304052;--ink:#f2f6fb;--muted:#a6b8ca;--accent:#98e3bc}
*{box-sizing:border-box}body{font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink);margin:0}
a{color:#b0d9ff;text-decoration:none}a:hover{text-decoration:underline}
.container{max-width:1170px;margin:auto;padding:24px}.nav{display:flex;gap:18px;justify-content:space-between;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line)}
.brand{color:var(--accent);font-size:1.15rem;font-weight:800}.meta,.sub,.time{color:var(--muted);font-size:.89rem}
.hero{padding:35px 0 18px}h1{font-size:clamp(2rem,4vw,3.2rem);line-height:1.1;letter-spacing:-.04em;margin:8px 0}
h2{font-size:1.42rem;margin:28px 0 14px}h3{font-size:1.06rem;line-height:1.35;margin:8px 0}
.lead{font-size:1.05rem;line-height:1.8;color:#d9e5f0;max-width:950px}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}
.tile,.card,.feature,.health{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}
.tile strong{display:block;font-size:1.8rem;color:var(--accent)}.tile span{color:var(--muted)}
.columns{display:grid;grid-template-columns:1.65fr 1fr;gap:26px}.cards{display:grid;gap:12px}
.card{overflow-wrap:anywhere}.card small,.tag{font-size:.78rem;letter-spacing:.04em;color:var(--accent);font-weight:700}
.card a{font-weight:650;color:var(--ink)}.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.pill{border:1px solid var(--line);border-radius:99px;padding:4px 10px;font-size:.78rem;color:var(--muted)}
.full{margin-top:24px}.feature{display:flex;gap:18px;align-items:center}.feature img{max-width:230px;width:35%;border-radius:10px}
.health summary{cursor:pointer;font-weight:700}.health-list{margin-top:14px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.good{color:var(--accent)}.warn{color:#ffcd86}.report{margin-top:36px;padding-top:20px;border-top:1px solid var(--line)}
.report details{padding:18px;background:var(--surface);border-radius:14px}.report summary{cursor:pointer}
.related{margin-top:12px;border-top:1px solid var(--line);padding-top:10px;font-size:.87rem}.related ul{padding-left:18px}.related li{margin:4px 0}.report img{max-width:100%}.report a{overflow-wrap:anywhere}footer{border-top:1px solid var(--line);color:var(--muted);padding:22px 0;margin-top:38px}
.topics{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}.topics button{cursor:pointer;border:1px solid var(--line);border-radius:25px;padding:8px 13px;background:var(--surface);color:var(--ink)}.topics button[aria-pressed=true]{background:var(--accent);color:#082018}.trend-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}.trend{background:var(--surface);border:1px solid var(--line);padding:14px;border-radius:12px}.trend strong,.trend span{display:block}.trend span{color:var(--muted);font-size:.85rem}[hidden]{display:none!important}
@media(max-width:760px){.columns{grid-template-columns:1fr}.tiles{grid-template-columns:1fr}.health-list{grid-template-columns:1fr}.feature{display:block}.feature img{width:100%;max-width:100%}}
</style>
"""

def e(value):
    return escape(str(value or ""), quote=True)

def link(url):
    value = str(url or "")
    return e(value) if urlparse(value).scheme in ("http", "https") else "#"

def day_dirs():
    return sorted((p for p in DATA.iterdir() if p.is_dir() and DAY.fullmatch(p.name))) if DATA.exists() else []


TOPICS = {
    "AI": ("artificial intelligence", " ai ", "openai", "llm", "machine learning", "model"),
    "Cybersecurity": ("cyber", "hack", "ransomware", "security", "breach", "malware"),
    "Technology": ("technology", "software", "startup", "chip", "comput", "robot", "tech"),
    "Space": ("space", "nasa", "rocket", "moon", "mars", "satellite", "astronom"),
    "Business": ("business", "market", "economy", "stock", "company", "trade", "finance"),
    "World": ("world", "war", "government", "election", "minister", "military", "international"),
    "Northern Virginia": ("virginia", "fairfax", "alexandria", "arlington", "loudoun", "prince william"),
}

def article_topics(item, local=False):
    value = " " + str(item.get("title", "")).lower() + " "
    found = [label for label, words in TOPICS.items() if any(word in value for word in words)]
    if local and "Northern Virginia" not in found:
        found.append("Northern Virginia")
    return found or ["World"]

def topic_controls():
    buttons = ''.join('<button type="button" data-filter="' + e(x) + '" aria-pressed="false">' + e(x) + '</button>' for x in TOPICS)
    return ('<div class="topics" aria-label="Filter news by topic"><button type="button" data-filter="All" aria-pressed="true">All topics</button>'
            + buttons + '</div>')

FILTER_SCRIPT = """
<script>
(function(){
 const buttons = document.querySelectorAll('[data-filter]');
 const cards = document.querySelectorAll('[data-topics]');
 const key = 'dkg-topic-v1';
 function apply(topic) {
   if (![...buttons].some(b=>b.dataset.filter===topic)) topic='All';
   buttons.forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.filter===topic)));
   cards.forEach(c=>{c.hidden=topic!=='All' && !(c.dataset.topics||'').split('|').includes(topic)});
   document.querySelectorAll('[data-filter-empty]').forEach(m=>{
     const section=m.closest('section');
     m.hidden=[...(section?.querySelectorAll('[data-topics]')||[])].some(c=>!c.hidden);
   });
   try {localStorage.setItem(key,topic)} catch(e){}
 }
 buttons.forEach(b=>b.addEventListener('click',()=>apply(b.dataset.filter)));
 let saved='All'; try{saved=localStorage.getItem(key)||'All'}catch(e){}
 apply(saved);
})();
</script>
"""

def linked_brief(news):
    global_items=top_headlines((news or {}).get("world", []), 2)
    local_items=top_headlines((news or {}).get("local", []), 2)
    blocks=[]
    for heading, items in (("Global watch",global_items),("Northern Virginia",local_items)):
        if items:
            links=', '.join('<a href="'+link(x.get("link"))+'" target="_blank" rel="noopener noreferrer">'+e(x.get("title"))+'</a>' for x in items)
            blocks.append('<p><strong>'+heading+':</strong> '+links+'.</p>')
    return ''.join(blocks) or '<p>No recent news coverage available.</p>'

def trend_counts(day_folders, max_days=7):
    """Counts only available archived daily data, not inferred trends."""
    recent=day_folders[-max_days:]
    result=[]
    for folder in recent:
        path=folder/"raw.json"
        if not path.exists():
            continue
        try:
            raw=json.loads(path.read_text(encoding="utf-8"))
            news=raw.get("news") or {}
            stories=(news.get("world") or [])+(news.get("local") or [])
            counts={topic:sum(topic in article_topics(article, article in (news.get("local") or [])) for article in stories) for topic in TOPICS}
            result.append((folder.name,counts))
        except (ValueError,OSError,TypeError):
            continue
    return result

def trend_panel(history):
    if len(history)<2:
        return '<p class="meta">Trends will appear when at least two days of reports have been collected.</p>'
    latest=history[-1][1]
    before=history[-2][1]
    cards=[]
    for topic in TOPICS:
        current=latest[topic]
        change=current-before[topic]
        cards.append('<div class="trend"><strong>'+e(topic)+'</strong><span>'+str(current)+' headlines · '+('+' if change>0 else '')+str(change)+' vs prior report</span></div>')
    return '<div class="trend-grid">'+''.join(cards)+'</div><p class="meta">Headline counts are based on keyword matches in available daily archives, not article importance or unique real-world events.</p>'

def render_cards(items, limit=6):
    return "\n".join(
        '<article class="card" data-topics="' + e('|'.join(article_topics(row, 'Northern Virginia' in str(row.get('source', ''))))) + '"><small>' + e(row.get("source", "News")) + '</small>'
        + '<h3><a href="' + link(row.get("link")) + '" target="_blank" rel="noopener noreferrer">'
        + e(row.get("title")) + '</a></h3>'
        + ('<span class="time">' + e(row.get("published")) + '</span>' if row.get("published") else '')
        + '</article>'
        for row in top_headlines(items, limit)
    ) or '<p class="meta">No recent stories available.</p>'


STOPWORDS = set("the and with from for after before into over says said that this about again amid are was were new news day its his her their have has".split())

def story_groups(items, limit=8):
    """Conservative title-keyword clustering. No semantic claims or fabricated text."""
    selected = top_headlines(items, 60)
    groups = []
    for item in selected:
        title = item.get("title", "")
        words = set(re.findall(r"[a-z0-9]{3,}", title.lower())) - STOPWORDS
        match = None
        for group in groups:
            common = len(words & group["words"])
            smaller = min(len(words), len(group["words"]))
            if smaller >= 4 and common >= 4 and common / smaller >= .70:
                match = group
                break
        if match is None:
            groups.append({"headline": item, "coverage": [item], "words": words})
        elif len(match["coverage"]) < 5:
            match["coverage"].append(item)
    return groups[:limit]

def render_stories(items, limit=8):
    html = []
    for group in story_groups(items, limit):
        row = group["headline"]
        sources = []
        for item in group["coverage"]:
            label = str(item.get("source") or "Publisher")
            if label not in sources:
                sources.append(label)
        multi = len(group["coverage"]) > 1
        coverage = ('<div class="pills"><span class="pill">' + str(len(group["coverage"]))
                    + ' related headlines</span>' + ''.join('<span class="pill">' + e(src) + '</span>' for src in sources)
                    + '</div>') if multi else '<div class="pills"><span class="pill">' + e(sources[0]) + '</span></div>'
        alternatives = ('<div class="related"><strong>More coverage</strong><ul>'
                        + ''.join('<li><a href="' + link(x.get("link")) + '" target="_blank" rel="noopener noreferrer">'
                                  + e(x.get("title")) + '</a></li>' for x in group["coverage"][1:])
                        + '</ul></div>') if multi else ''
        html.append('<article class="card" data-topics="' + e('|'.join(article_topics(row))) + '"><small>GLOBAL STORY</small><h3><a href="'
                    + link(row.get("link")) + '" target="_blank" rel="noopener noreferrer">'
                    + e(row.get("title")) + '</a></h3>' + coverage + alternatives + '</article>')
    return "\n".join(html) or '<p class="meta">No recent stories available.</p>'

def health_box(raw):
    statuses = raw.get("feed_status") or []
    passing = sum(s.get("status") == "ok" for s in statuses)
    issues = len(statuses)-passing
    items = "\n".join(
        '<div class="' + ('good' if s.get("status") == "ok" else 'warn') + '">'
        + e(s.get("source")) + ': ' + e(s.get("status"))
        + ' (' + e(s.get("count", 0)) + ')'
        + (' ' + e(s["error"]) if s.get("error") else '') + '</div>'
        for s in statuses
    )
    return ('<details class="health"><summary>Source health: '
            + f'{passing}/{len(statuses)} healthy'
            + (f' · {issues} need attention' if issues else '')
            + '</summary><div class="health-list">' + items + '</div></details>')

def build_day(folder, repo):
    day = folder.name
    out = DOCS / day
    out.mkdir(parents=True, exist_ok=True)
    for sub in ("plots", "images"):
        src = folder / sub
        dst = out / sub
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    report = folder / "report.md"
    if not report.exists():
        print(f"Skipping {day}: missing report.md")
        return
    raw_path = folder / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    news = raw.get("news") or {}
    world = news.get("world") or []
    local = news.get("local") or []
    hn = ((raw.get("hn") or {}).get("items") or [])
    apod = ((raw.get("apod") or {}).get("entry") or {})
    wiki = raw.get("wiki") or {}
    day_brief = linked_brief(news)
    updated = raw.get("last_updated_utc") or raw.get("collected_at_utc") or day
    entries = ((raw.get("feed_status") or []))
    healthy = sum(s.get("status") == "ok" for s in entries)

    hn_rows = [
        {"source": f"{h.get('points', 0)} points · Hacker News",
         "title": h.get("title"), "published": "",
         "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"}
        for h in hn[:15] if h.get("title")
    ]
    events = (wiki.get("today") or [])[:4]
    history = ''.join('<li><strong>' + e(x.get("year")) + '</strong> ' + e(x.get("text")) + '</li>' for x in events)
    preview = apod.get("image_url", "")
    picture = ('<img loading="lazy" alt="NASA Astronomy Picture of the Day preview" src="'
               + link(preview) + '">') if preview and link(preview) != "#" else ""
    apod_html = ('<div class="feature">' + picture
                 + '<div><span class="tag">NASA PICTURE OF THE DAY</span><h3><a href="'
                 + link(apod.get("link")) + '">' + e(apod.get("title")) + '</a></h3>'
                 + '<p class="meta">See the original image and explanation on NASA.</p></div></div>'
                 ) if apod.get("title") else '<p class="meta">NASA APOD unavailable.</p>'
    report_html = markdown.markdown(report.read_text(encoding="utf-8"), extensions=["extra", "tables", "sane_lists"])
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Daily Knowledge Garden | {e(day)}</title>{CSS}</head><body>
<div class="container"><nav class="nav"><a class="brand" href="../index.html">🌱 Daily Knowledge Garden</a>
<a href="../archive.html">View archive</a></nav>
<header class="hero"><p class="tag">YOUR DAILY INTELLIGENCE BRIEF · {e(day)}</p>
<h1>The world, in focus.</h1><div class="lead">{day_brief}</div>{topic_controls()}
<p class="meta">Last collected: {e(updated)} · Headlines are links to reporting, not verified full-article summaries.</p></header>
<div class="tiles"><div class="tile"><strong>{len(world)}</strong><span>Global headlines</span></div>
<div class="tile"><strong>{len(local)}</strong><span>Local headlines</span></div>
<div class="tile"><strong>{healthy}/{len(entries)}</strong><span>Sources reporting normally</span></div></div>
<div class="columns"><section><h2>🌍 Global coverage</h2><div class="cards">{render_stories(world, 8)}<p data-filter-empty hidden class="meta">No stories match this topic.</p></div></section>
<aside><section><h2>🏙️ Northern Virginia</h2><div class="cards">{render_cards(local, 6)}<p data-filter-empty hidden class="meta">No stories match this topic.</p></div></section>
<section><h2>🚀 Technology pulse</h2><div class="cards">{render_cards(hn_rows, 4)}<p data-filter-empty hidden class="meta">No stories match this topic.</p></div></section></aside></div>
<section class="full"><h2>🌌 Beyond Earth</h2>{apod_html}</section>
<section class="full"><h2>📜 On this day</h2><ul>{history or '<li>No historical events available.</li>'}</ul></section>
<section class="full"><h2>📈 Topic activity</h2>{trend_panel(trend_counts(day_dirs()))}</section>
<section class="full">{health_box(raw)}</section>
<section class="report"><details><summary>View original detailed report</summary>{report_html}</details></section>
<footer>Generated from public feeds · <a href="https://github.com/{e(repo)}">Source code</a> · {e(day)}</footer>
</div>{FILTER_SCRIPT}</body></html>"""
    (out / "index.html").write_text(html, encoding="utf-8")

def build_index(days):
    DOCS.mkdir(parents=True, exist_ok=True)
    nav = ''.join('<article class="card"><a href="./' + e(p.name) + '/">' + e(p.name) + '</a></article>' for p in reversed(days))
    archive = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Garden Archive</title>'
               + CSS + '</head><body><div class="container"><nav class="nav"><a class="brand" href="./index.html">🌱 Daily Knowledge Garden</a></nav>'
               '<h1>All daily reports</h1><div class="cards">' + (nav or '<p>No reports available.</p>') + '</div></div></body></html>')
    (DOCS / "archive.html").write_text(archive, encoding="utf-8")
    if days:
        # Static redirect rather than JS-only redirect; no script required.
        latest = days[-1].name
        html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Daily Knowledge Garden</title>'
                '<script>location.replace(new URLSearchParams(location.search).has("all") ? "./archive.html" : "./'
                + latest + '/");</script></head><body><a href="./' + latest
                + '/">Read the latest briefing</a> · <a href="./archive.html">All days</a></body></html>')
    else:
        html = archive
    (DOCS / "index.html").write_text(html, encoding="utf-8")

def main():
    DOCS.mkdir(exist_ok=True)
    days = day_dirs()
    for folder in days:
        build_day(folder, "jakep84/Daily-Knowledge-Garden")
    build_index(days)
    print(f"Built {len(days)} dashboard days into /docs")

if __name__ == "__main__":
    main()
