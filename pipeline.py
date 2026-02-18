import time, feedparser, re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from newspaper import Article
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import RSS_FEEDS, CATEGORIES, SUMMARY_SENTENCES, MAX_ITEMS_PER_FEED

# -------------- URL helpers --------------
def canonicalize_url(url: str) -> str:
    """Remove tracking params like utm_*, normalize."""
    try:
        u = urlparse(url)
        q = parse_qs(u.query)
        q = {k:v for k,v in q.items() if not k.lower().startswith("utm_")}
        new_query = urlencode(q, doseq=True)
        u = u._replace(query=new_query)
        return urlunparse(u)
    except Exception:
        return url

# -------------- Fetch RSS --------------
def fetch_rss_items(feeds):
    items = []
    for feed in feeds:
        d = feedparser.parse(feed)
        for e in d.entries[:MAX_ITEMS_PER_FEED]:
            items.append({
                "title": e.get("title", "").strip(),
                "link": canonicalize_url(e.get("link", "")),
                "published": time.mktime(e.published_parsed) if hasattr(e, "published_parsed") and e.published_parsed else time.time(),
                "summary_hint": e.get("summary", ""),
                "source": (e.get("link","").split("/")[2] if e.get("link") else "unknown")
            })
    return items

# -------------- Download full text --------------
def download_article_text(url: str):
    art = Article(url)
    art.download(); art.parse()
    return (art.title or "").strip(), (art.text or "").strip()

# -------------- Summarize --------------
def summarize_extractive(text: str, sentences: int = SUMMARY_SENTENCES) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summ = LsaSummarizer()
    sents = list(summ(parser.document, sentences))
    return " ".join(str(s) for s in sents)

# -------------- Simple keyword categorizer --------------
KEYWORDS = {
    "Sports": ["cricket","football","fifa","olympic","score","match","tournament","league","tennis","medal","run rate","wicket"],
    "Technology": ["ai","software","app","iphone","android","google","microsoft","startup","robot","cyber","chip","semiconductor","laptop","data"],
    "Politics": ["election","prime minister","president","parliament","minister","policy","bill","government","senate","diplomatic","treaty","vote"]
}

def categorize_simple(text: str):
    t = (text or "").lower()
    best_cat, best_hits = "Politics", 0
    for cat, words in KEYWORDS.items():
        hits = sum(1 for w in words if w in t)
        if hits > best_hits:
            best_cat, best_hits = cat, hits
    confidence = min(0.9, 0.3 + 0.1 * best_hits) if best_hits>0 else 0.3
    return best_cat, confidence

# -------------- Sentiment --------------
def sentiment_simple(text: str):
    p = TextBlob(text or "").sentiment.polarity
    if p > 0.15: return "Positive"
    if p < -0.15: return "Negative"
    return "Neutral"

# -------------- Dedup (optional) --------------
def near_duplicate_filter(records, threshold=0.9):
    kept = []
    corpus = []
    vec = TfidfVectorizer(max_features=4000, ngram_range=(1,2), stop_words="english")
    for rec in records:
        blob = ((rec.get("title","") + " " + rec.get("text","")).strip())
        if not blob:
            continue
        corpus_new = corpus + [blob]
        X = vec.fit_transform(corpus_new)
        if corpus:
            sim = cosine_similarity(X[-1], X[:-1]).max()
            if sim >= threshold:
                continue
        kept.append(rec)
        corpus.append(blob)
    return kept
