# 🌱 Daily Knowledge Garden

👉 **Live site:** https://jakep84.github.io/Daily-Knowledge-Garden/

An autonomous, self-updating repository that publishes a daily bundle of insights from:

- **Hacker News** – Top front-page stories
- **Wikipedia** – “On this day” events + a random article
- **NASA Astronomy Picture of the Day (APOD)** – via RSS

Every day it:

1. Fetches public data (no API keys needed)
2. Summarizes and analyzes
3. Generates Markdown reports and charts
4. Commits results back to this repo

---

**Latest run:** <!--LATEST_RUN-->2025-10-14 (UTC)<!--/LATEST_RUN-->

## 📊 Highlights

<!--HIGHLIGHTS-->- **HN #1:** [NanoChat – The best ChatGPT that $100 can buy](https://github.com/karpathy/nanochat)
- **APOD:** [](https://apod.nasa.gov/apod/astropix.html)
- **Daily Report:** [2025-10-14/report.md](/data/2025-10-14/report.md)<!--/HIGHLIGHTS-->

---

## 📁 Archive

See `/data/YYYY-MM-DD/` for day-by-day JSON, Markdown, and generated images.

---

## ⚙️ How It Works

- **Scheduler:** Runs automatically every day at **09:00 UTC** via GitHub Actions
- **Sources:** Hacker News (Algolia API), Wikipedia APIs, NASA APOD RSS
- **Processing:** Lightweight frequency-based summarization (no AI keys needed)
- **Outputs:** Markdown report, JSON raw data, PNG charts, README “Highlights” auto-refresh

---

## 💡 Contributing Ideas

Want to help it grow?  
Open an issue suggesting a new public data source or visualization idea — this project is designed to evolve organically.

---

## 🪴 Vision

> A living, digital garden that grows knowledge automatically — no human hands required.

---

### License

MIT © 2025  
**Daily Knowledge Garden**
