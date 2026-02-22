from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import feedparser
from dateutil import parser as dt_parser
from sqlalchemy.orm import Session

from .models import Article, Source
from .summarizer import RuleBasedSummarizer


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, "", "", ""))


def parse_published(entry) -> datetime | None:
    value = entry.get("published") or entry.get("updated")
    if not value:
        return None
    try:
        dt = dt_parser.parse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def run_ingest(db: Session) -> dict:
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()
    summarizer = RuleBasedSummarizer()
    created, skipped = 0, 0

    for source in sources:
        feed = feedparser.parse(source.feed_url)
        for entry in feed.entries:
            url = entry.get("link")
            if not url:
                continue

            canonical = canonicalize_url(url)
            exists = db.query(Article).filter(Article.url_canonical == canonical).first()
            if exists:
                skipped += 1
                continue

            snippet = entry.get("summary") or entry.get("description") or ""
            content_text = snippet
            # TODO: Add full-text extraction from linked URL.
            summary_json = summarizer.summarize(content_text)

            article = Article(
                source_id=source.id,
                title=(entry.get("title") or "(no title)")[:500],
                url=url,
                url_canonical=canonical[:2000],
                published_at=parse_published(entry),
                snippet=snippet,
                content_text=content_text,
                summary_json=summary_json,
            )
            db.add(article)
            created += 1

    db.commit()
    return {
        "fetched_sources": len(sources),
        "created_articles": created,
        "skipped_duplicates": skipped,
    }
