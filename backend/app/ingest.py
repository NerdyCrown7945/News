from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import feedparser
from dateutil import parser as dt_parser
from sqlalchemy.orm import Session

from .dedupe import canonicalize_url, normalize_title, similar_title
from .models import Article, Source
from .summarize import RuleBasedSummarizer, Summarizer

DEFAULT_SOURCES_PATH = Path(__file__).resolve().parents[1] / "sources.json"


def parse_published(entry) -> datetime | None:
    value = entry.get("published") or entry.get("updated") or entry.get("pubDate")
    if not value:
        return datetime.now(timezone.utc)
    try:
        dt = dt_parser.parse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def ensure_sources(db: Session, sources_path: Path = DEFAULT_SOURCES_PATH) -> int:
    if db.query(Source).count() > 0:
        return 0

    raw = json.loads(sources_path.read_text(encoding="utf-8"))
    created = 0
    for row in raw:
        db.add(
            Source(
                name=row["name"],
                feed_url=row["feed_url"],
                topic=row["topic"],
                enabled=row.get("enabled", True),
            )
        )
        created += 1

    db.commit()
    return created


def run_ingest(db: Session, summarizer: Summarizer | None = None) -> dict:
    summarizer = summarizer or RuleBasedSummarizer()
    ensure_sources(db)

    sources = db.query(Source).filter(Source.enabled.is_(True)).all()
    accepted_titles: list[str] = []
    created, skipped = 0, 0

    for source in sources:
        parsed = feedparser.parse(source.feed_url)
        for entry in parsed.entries:
            url = entry.get("link")
            if not url:
                continue

            canonical = canonicalize_url(url)
            exists = db.query(Article).filter(Article.url_canonical == canonical).first()
            if exists:
                skipped += 1
                continue

            title = (entry.get("title") or "(untitled)").strip()
            title_norm = normalize_title(title)
            if any(similar_title(title_norm, old) for old in accepted_titles):
                skipped += 1
                continue

            snippet = (entry.get("summary") or entry.get("description") or "").strip()
            summary_json = summarizer.summarize(snippet, title)

            db.add(
                Article(
                    source_id=source.id,
                    title=title[:500],
                    url=url,
                    url_canonical=canonical[:2000],
                    published_at=parse_published(entry),
                    snippet=snippet,
                    content_text=snippet,
                    summary_json=summary_json,
                )
            )
            accepted_titles.append(title_norm)
            created += 1

    db.commit()
    return {
        "fetched_sources": len(sources),
        "created_articles": created,
        "skipped_duplicates": skipped,
    }
