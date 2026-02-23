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

# 홈/섹션 판정은 path가 비어있는 경우를 별도 처리하므로 ""는 포함하지 않는다.
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
    """개별 기사 URL이 아니라 홈/섹션(목록) URL이면 True."""
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
    """
    RSS entry에서 '개별 기사' 링크를 최대한 정확히 추출한다.
    추측으로 URL을 만들지 않고, entry가 제공하는 근거(link/alternate/guid)만 사용한다.
    홈/섹션 링크로 판정되면 빈 문자열을 반환한다.
    """
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