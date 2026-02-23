#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import feedparser
from dateutil import parser as dt_parser
from urllib.request import Request, urlopen

LOGGER = logging.getLogger("news-pipeline")
USER_AGENT = "NewsDigestBot/1.0 (+https://github.com/)"
TIMEOUT = 12
DEFAULT_MAX_ARTICLES = 150
TITLE_SIM_THRESHOLD = 0.9
TRACKING_QUERY_PREFIXES = (
    "utm_",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "spm",
    "igshid",
    "wt_",
)
HOMEPAGE_PATH_HINTS = {"blog", "blogs", "news", "updates", "stories", "research", "press"}


class Summarizer:
    def summarize(self, text: str, title: str) -> dict[str, Any]:
        raise NotImplementedError


class RuleBasedSummarizer(Summarizer):
    def summarize(self, text: str, title: str) -> dict[str, Any]:
        cleaned = clean_text(text)
        if not cleaned:
            return {
                "one_liner": title[:220],
                "summary_lines": [title[:220]],
                "key_points": [title[:220]],
            }

        paragraphs = [p.strip() for p in re.split(r"\n{2,}", cleaned) if p.strip()]
        first_paragraph = paragraphs[0] if paragraphs else cleaned

        sentences = split_sentences(cleaned)
        first_sentence = sentences[0] if sentences else first_paragraph
        key_sentence = max(sentences[:6], key=len) if sentences else first_sentence

        summary_lines = unique_keep_order([first_paragraph, key_sentence])[:3]
        key_points = unique_keep_order(sentences[:4] or [first_sentence])[:4]

        return {
            "one_liner": first_sentence[:220],
            "summary_lines": summary_lines,
            "key_points": key_points,
        }


@dataclass
class Source:
    id: str
    name: str
    topic: str
    feed_url: str
    site_url: str
    language_hint: str
    reliability: str
    tags: list[str]
    enabled: bool = True


@dataclass
class Article:
    id: str
    title: str
    source: str
    published_at: str
    topic: str
    one_liner: str
    tags: list[str]
    url: str
    cluster_id: str
    summary_lines: list[str]
    key_points: list[str]
    title_norm: str


def clean_text(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value or "")
    unescaped = html.unescape(no_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def unique_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


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
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            urlencode(clean_qs, doseq=True),
            "",
        )
    )


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


def extract_entry_url(entry: dict[str, Any]) -> str:
    candidates: list[str] = []

    link = (entry.get("link") or "").strip()
    if link:
        candidates.append(link)

    for link_item in entry.get("links", []) or []:
        href = (link_item.get("href") or "").strip()
        rel = (link_item.get("rel") or "").strip().lower()
        if href and rel in {"alternate", ""}:
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


def parse_published(entry: dict[str, Any]) -> datetime:
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


def normalize_title(title: str) -> str:
    lowered = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    return re.sub(r"\s+", " ", lowered).strip()


def similar_title(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(a=a, b=b).ratio() >= TITLE_SIM_THRESHOLD


def article_id(seed: str) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def fetch_feed(url: str) -> feedparser.FeedParserDict | None:
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT) as res:
            data = res.read()
        return feedparser.parse(data)
    except Exception as exc:
        LOGGER.warning("failed to fetch feed %s: %s", url, exc)
        return None


def load_sources(path: Path) -> list[Source]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    dedup: dict[tuple[str, str], Source] = {}
    for row in raw:
        source = Source(
            id=row.get("id") or row["name"].lower().replace(" ", "-"),
            name=row["name"],
            topic=row["topic"],
            feed_url=row["feed_url"],
            site_url=row.get("site_url", ""),
            language_hint=row.get("language_hint", "en"),
            reliability=row.get("reliability", "med"),
            tags=row.get("tags", []),
            enabled=row.get("enabled", True),
        )
        key = (source.topic.strip().lower(), source.feed_url.strip().lower())
        if key not in dedup:
            dedup[key] = source
    return list(dedup.values())


def assign_cluster_id(title_norm: str, existing_titles: dict[str, str]) -> str:
    for known_title, cid in existing_titles.items():
        if similar_title(title_norm, known_title):
            return cid
    seed = hashlib.md5(title_norm.encode("utf-8")).hexdigest()[:10]
    return f"c-{seed}"


def generate_data(sources: list[Source], summarizer: Summarizer, max_articles: int = DEFAULT_MAX_ARTICLES) -> list[Article]:
    seen_keys: set[str] = set()
    accepted_titles: list[str] = []
    cluster_by_title: dict[str, str] = {}
    articles: list[Article] = []

    for source in sources:
        if not source.enabled:
            continue
        parsed = fetch_feed(source.feed_url)
        if not parsed:
            continue

        for entry in parsed.entries:
            canonical = extract_entry_url(entry)

            title = (entry.get("title") or "(untitled)").strip()
            title_norm = normalize_title(title)
            dedupe_key = canonical or f"{source.name.lower()}::{title_norm}"
            if dedupe_key in seen_keys:
                continue

            if any(similar_title(title_norm, t) for t in accepted_titles):
                continue

            snippet = clean_text(entry.get("summary") or entry.get("description") or "")
            summary = summarizer.summarize(snippet or title, title)
            published = parse_published(entry).isoformat().replace("+00:00", "Z")
            cluster_id = assign_cluster_id(title_norm, cluster_by_title)
            aid = article_id(canonical or f"{source.name}|{title}|{published}")

            item = Article(
                id=aid,
                title=title,
                source=source.name,
                published_at=published,
                topic=source.topic,
                one_liner=summary["one_liner"],
                tags=source.tags,
                url=canonical,
                cluster_id=cluster_id,
                summary_lines=summary["summary_lines"],
                key_points=summary["key_points"],
                title_norm=title_norm,
            )
            articles.append(item)
            seen_keys.add(dedupe_key)
            accepted_titles.append(title_norm)
            cluster_by_title[title_norm] = cluster_id

            if len(articles) >= max_articles:
                break
        if len(articles) >= max_articles:
            break

    articles.sort(key=lambda a: a.published_at, reverse=True)
    return articles


def write_output(articles: list[Article], output_root: Path) -> None:
    data_dir = output_root / "data"
    articles_dir = data_dir / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)

    if not articles and (data_dir / "feed.json").exists():
        LOGGER.warning("no articles generated; preserving existing frontend/public/data output")
        return

    for file in articles_dir.glob("*.json"):
        file.unlink()

    by_cluster: dict[str, list[Article]] = {}
    for article in articles:
        by_cluster.setdefault(article.cluster_id, []).append(article)

    feed = []
    for article in articles:
        feed.append(
            {
                "id": article.id,
                "title": article.title,
                "source": article.source,
                "published_at": article.published_at,
                "topic": article.topic,
                "one_liner": article.one_liner,
                "tags": article.tags,
                "url": article.url,
                "cluster_id": article.cluster_id,
            }
        )

        related = [
            {
                "id": other.id,
                "title": other.title,
                "source": other.source,
                "published_at": other.published_at,
            }
            for other in by_cluster.get(article.cluster_id, [])
            if other.id != article.id
        ][:5]

        detail = {
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "published_at": article.published_at,
            "summary_lines": article.summary_lines,
            "key_points": article.key_points,
            "summary_lines_ko": article.summary_lines,
            "key_points_ko": article.key_points,
            "url": article.url,
            "related": related,
        }
        (articles_dir / f"{article.id}.json").write_text(
            json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    (data_dir / "feed.json").write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static RSS news data for frontend/public/data")
    parser.add_argument("--sources", default="backend/sources.json", help="path to sources JSON")
    parser.add_argument("--output", default="frontend/public", help="frontend public directory")
    parser.add_argument("--max-articles", type=int, default=DEFAULT_MAX_ARTICLES, help="maximum number of items to generate")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sources = load_sources(Path(args.sources))
    articles = generate_data(sources=sources, summarizer=RuleBasedSummarizer(), max_articles=max(10, args.max_articles))
    write_output(articles, Path(args.output))
    LOGGER.info("generated %s articles from %s sources", len(articles), len(sources))


if __name__ == "__main__":
    main()
