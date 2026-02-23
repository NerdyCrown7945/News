from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .db import fetch_all, fetch_one, init_db
from .ingest import run_ingest

app = FastAPI(title="News MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest/run")
def ingest_run() -> dict[str, int]:
    return run_ingest()


def _cutoff(range_value: str) -> str | None:
    now = datetime.now(timezone.utc)
    if range_value == "24h":
        return (now - timedelta(hours=24)).isoformat()
    if range_value == "7d":
        return (now - timedelta(days=7)).isoformat()
    if range_value == "30d":
        return (now - timedelta(days=30)).isoformat()
    return None


@app.get("/feed")
def feed(
    topic: str = Query("all", pattern="^(ai|scitech|all)$"),
    range: str = Query("24h", pattern="^(24h|7d|30d)$"),
    query: str = "",
    tags: str = "",
    sort: str = Query("new", pattern="^(new|date)$"),
):
    where = []
    params: list[str] = []

    if topic != "all":
        where.append("topic = ?")
        params.append(topic)

    cutoff = _cutoff(range)
    if cutoff:
        where.append("published_at >= ?")
        params.append(cutoff)

    q = query.strip().lower()
    if q:
        where.append("(lower(title) LIKE ? OR lower(title_ko) LIKE ? OR lower(summary_one_liner_ko) LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    for t in tag_list:
        where.append("lower(tags) LIKE ?")
        params.append(f"%{t}%")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    if sort == "date":
        order_sql = "ORDER BY published_at ASC, fetched_at ASC"
    else:
        order_sql = "ORDER BY published_at DESC, fetched_at DESC"

    rows = fetch_all(f"SELECT * FROM articles {where_sql} {order_sql} LIMIT 300", tuple(params))

    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "title": r["title"],
                "title_ko": r["title_ko"],
                "url": r["url"],
                "source": r["source"],
                "topic": r["topic"],
                "published_at": r["published_at"],
                "one_liner": r["summary_one_liner_ko"],
                "tags": json.loads(r["tags"] or "[]"),
            }
        )
    return result


@app.get("/article/{article_id}")
def article(article_id: str):
    row = fetch_one("SELECT * FROM articles WHERE id = ?", (article_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")
    return {
        "id": row["id"],
        "title": row["title"],
        "title_ko": row["title_ko"],
        "url": row["url"],
        "source": row["source"],
        "topic": row["topic"],
        "published_at": row["published_at"],
        "snippet": row["snippet"],
        "content_text": row["content_text"],
        "summary_one_liner_ko": row["summary_one_liner_ko"],
        "summary_lines_ko": json.loads(row["summary_lines_ko"] or "[]"),
        "key_points_ko": json.loads(row["key_points_ko"] or "[]"),
        "tags": json.loads(row["tags"] or "[]"),
        "lang": row["lang"],
        "cluster_id": row["cluster_id"],
    }


@app.get("/search")
def search(query: str, from_date: str | None = Query(None, alias="from"), to: str | None = None, topic: str = "all"):
    where = ["(lower(title) LIKE ? OR lower(title_ko) LIKE ? OR lower(content_text) LIKE ?)"]
    q = f"%{query.lower()}%"
    params: list[str] = [q, q, q]
    if from_date:
        where.append("published_at >= ?")
        params.append(f"{from_date}T00:00:00+00:00")
    if to:
        where.append("published_at <= ?")
        params.append(f"{to}T23:59:59+00:00")
    if topic != "all":
        where.append("topic = ?")
        params.append(topic)

    rows = fetch_all(
        f"SELECT id, title, title_ko, source, topic, published_at, summary_one_liner_ko, tags FROM articles WHERE {' AND '.join(where)} ORDER BY published_at DESC LIMIT 200",
        tuple(params),
    )
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "title_ko": r["title_ko"],
            "source": r["source"],
            "topic": r["topic"],
            "published_at": r["published_at"],
            "one_liner": r["summary_one_liner_ko"],
            "tags": json.loads(r["tags"] or "[]"),
        }
        for r in rows
    ]
