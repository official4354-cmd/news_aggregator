from flask import Flask, render_template, abort
from db import get_conn, latest, get_article

app = Flask(__name__)

@app.route("/")
def home():
    conn = get_conn()
    rows = latest(conn, limit=24)
    conn.close()
    if not rows:
        msg = "No articles yet. Open a terminal and run: python run_pipeline.py"
        return f"<h1>Smart News Aggregator</h1><p>{msg}</p>"
    return render_template("index.html", news=rows)

@app.route("/article/<int:aid>")
def article(aid):
    conn = get_conn()
    row = get_article(conn, aid)
    conn.close()
    if not row: abort(404)
    return render_template("article.html", a=row)

if __name__ == "__main__":
    app.run(debug=True)
