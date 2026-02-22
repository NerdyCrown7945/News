from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .ingest import run_ingest
from .models import Article, Source
from .schemas import ArticleDetail, FeedItem, IngestResult, Summary
from .store import get_db

router = APIRouter()


def parse_range(range_value: str) -> timedelta:
    mapping = {"24h": timedelta(hours=24), "7d": timedelta(days=7)}
    if range_value not in mapping:
        raise HTTPException(status_code=400, detail="range must be one of: 24h, 7d")
    return mapping[range_value]


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ingest/run", response_model=IngestResult)
def ingest_endpoint(db: Session = Depends(get_db)):
    return run_ingest(db)


@router.get("/feed", response_model=list[FeedItem])
def feed(
    topic: str = Query(..., pattern="^(ai|scitech)$"),
    range: str = Query("24h", alias="range"),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - parse_range(range)
    rows = (
        db.query(Article, Source)
        .join(Source, Source.id == Article.source_id)
        .filter(Source.topic == topic)
        .filter((Article.published_at.is_(None)) | (Article.published_at >= cutoff))
        .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        FeedItem(
            id=article.id,
            title=article.title,
            url=article.url,
            source_name=source.name,
            topic=source.topic,
            published_at=article.published_at,
            summary=Summary(**article.summary_json) if article.summary_json else None,
        )
        for article, source in rows
    ]


@router.get("/article/{article_id}", response_model=ArticleDetail)
def article_detail(article_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Article, Source)
        .join(Source, Source.id == Article.source_id)
        .filter(Article.id == article_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    article, source = row
    return ArticleDetail(
        id=article.id,
        title=article.title,
        url=article.url,
        source_name=source.name,
        topic=source.topic,
        published_at=article.published_at,
        snippet=article.snippet,
        content_text=article.content_text,
        summary=Summary(**article.summary_json) if article.summary_json else None,
    )
