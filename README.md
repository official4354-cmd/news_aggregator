# Smart News Aggregator — Starter (Beginner Friendly)

This is a tiny project you can run **step by step**.
It fetches real news from a few RSS feeds, summarizes them to 3 lines, does a **very simple keyword-based category** (Sports/Tech/Politics),
adds a simple **sentiment** label, stores everything in **SQLite**, and shows them in a **Flask web page**.

> Keep it simple first. Later, you can upgrade categorization to HuggingFace zero-shot models.

---

## 0) Install Python + VS Code
- Windows: Install Python from https://www.python.org/downloads/ (tick "Add Python to PATH")
- Install VS Code from https://code.visualstudio.com/

## 1) Open a terminal here
Open VS Code → File → Open Folder → choose this folder → Terminal → New Terminal

## 2) Create a virtual environment (optional but recommended)
**Windows PowerShell**
```
python -m venv .venv
.\.venv\Scripts\activate
```
**Mac/Linux**
```
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install required packages
```
pip install -r requirements.txt
```
> If `newspaper3k` complains, run:
```
pip install lxml==5.2.1 Pillow==10.3.0
```
and then try again:
```
pip install newspaper3k
```

## 4) Fetch and process some news
```
python run_pipeline.py
```
This will create a local database file `news.db` and fill it with articles.

## 5) Start the mini website
```
python app.py
```
Open your browser: http://127.0.0.1:5000/

You should see a list of headlines. Click one to see the summary and details.

---

## Optional Upgrades
- **Better categorization** (no training): `pip install transformers torch` then switch to zero-shot in `pipeline.py`.
- **Deduplication**: enable TF-IDF dedup in `pipeline.py` (already stubbed).
- **More sources**: add RSS links in `config.py`.

## Troubleshooting
- If parsing fails for some sites, don't worry; the script skips them and continues.
- If `newspaper3k` fails often, stick to the sources in `config.py` or add others with clean RSS.
- If the page looks empty, re-run: `python run_pipeline.py` then refresh the browser.

