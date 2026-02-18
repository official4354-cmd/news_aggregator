import sqlite3

def get_conn():
    conn = sqlite3.connect("news.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT,
        summary TEXT,
        category TEXT,
        category_conf REAL,
        sentiment TEXT,
        published_ts REAL,
        source TEXT
    )""")
    return conn

def upsert_article(conn, a):
    conn.execute("""INSERT OR IGNORE INTO articles
        (url,title,content,summary,category,category_conf,sentiment,published_ts,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (a.get("url"), a.get("title"), a.get("content"), a.get("summary"),
         a.get("category"), a.get("category_conf"), a.get("sentiment"),
         a.get("published_ts"), a.get("source"))
    )
    conn.commit()

def latest(conn, limit=30):
    cur = conn.execute("SELECT id,title,summary,category,sentiment,source FROM articles ORDER BY id DESC LIMIT ?", (limit,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def get_article(conn, id_):
    cur = conn.execute("SELECT * FROM articles WHERE id=?", (id_,))
    row = cur.fetchone()
    if not row: return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))
