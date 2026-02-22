from datetime import datetime
from pydantic import BaseModel


class Summary(BaseModel):
    one_liner: str
    summary_lines: list[str]
    key_points: list[str]


class FeedItem(BaseModel):
    id: int
    title: str
    url: str
    source_name: str
    topic: str
    published_at: datetime | None
    summary: Summary | None


class ArticleDetail(BaseModel):
    id: int
    title: str
    url: str
    source_name: str
    topic: str
    published_at: datetime | None
    snippet: str | None
    content_text: str | None
    summary: Summary | None


class IngestResult(BaseModel):
    fetched_sources: int
    created_articles: int
    skipped_duplicates: int
