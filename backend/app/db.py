from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "news.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  title_ko TEXT,
  url TEXT NOT NULL,
  url_canonical TEXT NOT NULL,
  source TEXT NOT NULL,
  topic TEXT NOT NULL CHECK (topic IN ('ai', 'scitech')),
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  snippet TEXT,
  content_text TEXT,
  summary_one_liner_ko TEXT,
  summary_lines_ko TEXT,
  key_points_ko TEXT,
  tags TEXT,
  lang TEXT,
  cluster_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url_canonical ON articles(url_canonical);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    with get_conn() as conn:
        conn.execute(query, params)
        conn.commit()
