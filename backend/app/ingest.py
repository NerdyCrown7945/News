from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

import feedparser
from dateutil import parser as dt_parser

from .db import execute, fetch_all, fetch_one, get_conn, init_db
from .llm import summarize_and_translate

SOURCES_PATH = Path(__file__).resolve().parents[1] / "sources.json"
TITLE_SIM_THRESHOLD = 0.9
TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "spm", "igshid", "wt_")
HOMEPAGE_PATH_HINTS = {"blog", "blogs", "news", "updates", "stories", "research", "press"}


def _is_http_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def canonicalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return ""

    clean_qs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
    ]
    path = parsed.path or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(clean_qs, doseq=True), ""))


def is_home_or_section_url(url: str) -> bool:
    if not _is_http_url(url):
        return True
    parsed = urlparse(url)
    path = (parsed.path or "").strip("/").lower()
    if not path:
        return True

    segments = [seg for seg in path.split("/") if seg]
    if len(segments) == 1 and segments[0] in HOMEPAGE_PATH_HINTS:
        return True
    if len(segments) <= 2:
        joined = "/".join(segments)
        if joined == "discover/blog":
            return True
        if segments and segments[0] in HOMEPAGE_PATH_HINTS:
            return True
    return False


def extract_entry_url(entry: Any) -> str:
    candidates: list[str] = []

    link = (entry.get("link") or "").strip()
    if link:
        candidates.append(link)

    for link_item in entry.get("links", []) or []:
        href = (link_item.get("href") or "").strip()
        rel = (link_item.get("rel") or "").strip().lower()
        if href and rel in {"", "alternate"}:
            candidates.append(href)

    guid = (entry.get("guid") or entry.get("id") or "").strip()
    if guid:
        candidates.append(guid)

    for candidate in candidates:
        if not _is_http_url(candidate):
            continue
        canonical = canonicalize_url(candidate)
        if canonical and not is_home_or_section_url(canonical):
            return canonical

    return ""


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", (title or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def title_similarity(a: str, b: str) -> float:
    aw = set(a.split())
    bw = set(b.split())
    if not aw or not bw:
        return 0.0
    inter = len(aw & bw)
    union = len(aw | bw)
    return inter / union if union else 0.0


def parse_published(entry: Any) -> str:
    value = entry.get("published") or entry.get("updated") or entry.get("pubDate")
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = dt_parser.parse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def extract_content(url: str, fallback: str) -> str:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=8) as resp:
            html = resp.read(300000).decode("utf-8", errors="ignore")
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 200:
            return text[:20000]
    except Exception:
        pass
    return fallback.strip()


def ensure_sources() -> int:
    init_db()
    sources_row = fetch_one("SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type='table' AND name='sources'")
    execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          topic TEXT NOT NULL,
          feed_url TEXT NOT NULL UNIQUE,
          enabled INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    count = fetch_one("SELECT COUNT(*) AS cnt FROM sources")
    if count and count["cnt"] > 0:
        return 0

    rows = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    inserted = 0
    with get_conn() as conn:
        for row in rows:
            conn.execute(
                "INSERT OR IGNORE INTO sources(name, topic, feed_url, enabled) VALUES (?, ?, ?, ?)",
                (row["name"], row["topic"], row["feed_url"], 1 if row.get("enabled", True) else 0),
            )
            inserted += 1
        conn.commit()
    return inserted


def run_ingest() -> dict[str, int]:
    init_db()
    ensure_sources()
    created = 0
    skipped = 0
    with get_conn() as conn:
        sources = conn.execute("SELECT name, topic, feed_url FROM sources WHERE enabled = 1").fetchall()
        recent_titles = [r["title"] for r in conn.execute("SELECT title FROM articles ORDER BY fetched_at DESC LIMIT 500").fetchall()]

        for source in sources:
            parsed = feedparser.parse(source["feed_url"])
            entries = list(parsed.entries)
            if not entries:
                continue
            for entry in entries:
                url = extract_entry_url(entry)
                canonical = canonicalize_url(url) if url else ""
                if canonical and conn.execute("SELECT 1 FROM articles WHERE url_canonical = ?", (canonical,)).fetchone():
                    skipped += 1
                    continue

                title = (entry.get("title") or "(untitled)").strip()
                title_norm = normalize_title(title)
                if any(title_similarity(title_norm, normalize_title(old)) >= TITLE_SIM_THRESHOLD for old in recent_titles[-100:]):
                    skipped += 1
                    continue

                snippet = (entry.get("summary") or entry.get("description") or "").strip()
                content = extract_content(url, snippet)
                lang = (entry.get("language") or parsed.feed.get("language") or "unknown")[:20]
                published_at = parse_published(entry)
                fetched_at = datetime.now(timezone.utc).isoformat()
                aid_seed = canonical or f"{source['name']}|{title}|{published_at}"
                aid = hashlib.sha1(aid_seed.encode("utf-8")).hexdigest()[:20]

                article = {
                    "title": title,
                    "snippet": snippet,
                    "content_text": content,
                }
                title_ko, one_liner, lines, points, tags = summarize_and_translate(article)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO articles (
                        id, title, title_ko, url, url_canonical, source, topic,
                        published_at, fetched_at, snippet, content_text,
                        summary_one_liner_ko, summary_lines_ko, key_points_ko,
                        tags, lang, cluster_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        aid,
                        title,
                        title_ko,
                        url,
                        canonical or f"urn:news:{aid}",
                        source["name"],
                        source["topic"],
                        published_at,
                        fetched_at,
                        snippet,
                        content,
                        one_liner,
                        json.dumps(lines, ensure_ascii=False),
                        json.dumps(points, ensure_ascii=False),
                        json.dumps(tags, ensure_ascii=False),
                        lang,
                        None,
                    ),
                )
                recent_titles.append(title)
                created += 1
        conn.commit()

    return {"fetched_sources": len(sources), "created_articles": created, "skipped_duplicates": skipped}
