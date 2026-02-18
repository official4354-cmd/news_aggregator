import time
from db import get_conn, upsert_article
from pipeline import fetch_rss_items, download_article_text, summarize_extractive, categorize_simple, sentiment_simple, near_duplicate_filter
from config import RSS_FEEDS

def run_once():
    raw = fetch_rss_items(RSS_FEEDS)
    records = []
    for r in raw:
        try:
            title, text = download_article_text(r["link"])
            if not text:
                # fallback: use summary_hint if available
                text = r.get("summary_hint","")
            if not (title or text):
                continue
            records.append({
                "url": r["link"],
                "title": title or r["title"],
                "text": text,
                "published_ts": r["published"],
                "source": r.get("source","unknown")
            })
        except Exception:
            continue

    records = near_duplicate_filter(records, threshold=0.9)

    conn = get_conn()
    added = 0
    for rec in records:
        summary = summarize_extractive(rec["text"])
        cat, conf = categorize_simple((rec["title"] or "") + ". " + summary)
        senti = sentiment_simple(summary or rec["text"])
        upsert_article(conn, {
            "url": rec["url"],
            "title": rec["title"],
            "content": rec["text"],
            "summary": summary,
            "category": cat,
            "category_conf": conf,
            "sentiment": senti,
            "published_ts": rec["published_ts"],
            "source": rec["source"]
        })
        added += 1
    conn.close()
    print(f"Processed {len(records)} items. Inserted (or skipped if existing): {added}")

if __name__ == "__main__":
    run_once()
