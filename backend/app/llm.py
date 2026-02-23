from __future__ import annotations

import os
import re
from typing import Any


def _split_sentences(text: str) -> list[str]:
    clean = " ".join((text or "").split())
    if not clean:
        return []
    chunks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
    return chunks or [clean]


def summarize_and_translate(article: dict[str, Any]) -> tuple[str, str, list[str], list[str], list[str]]:
    """Return (title_ko, one_liner, lines, points, tags).

    기본 구현은 규칙 기반 더미입니다.
    TODO: OPENAI_API_KEY가 있으면 실제 LLM 호출로 교체.
    """
    title = (article.get("title") or "(untitled)").strip()
    text = (article.get("content_text") or article.get("snippet") or "").strip()

    if os.getenv("OPENAI_API_KEY"):
        # TODO: OpenAI API 연동 구현 지점.
        pass

    sents = _split_sentences(text)
    if not sents:
        sents = [title]

    title_ko = title  # TODO: 자연스러운 한국어 번역 제목 생성
    one_liner = sents[0][:180]
    lines = [s[:220] for s in sents[:5]]
    while len(lines) < 3:
        lines.append(one_liner)
    points = [s[:140] for s in sents[:3]]
    while len(points) < 3:
        points.append(one_liner)

    lowered = f"{title} {' '.join(sents[:2])}".lower()
    tags: list[str] = []
    mapping = {
        "llm": ["llm", "language model", "gpt"],
        "robotics": ["robot", "robotics"],
        "chip": ["chip", "gpu", "semiconductor"],
        "space": ["space", "nasa", "esa", "satellite"],
        "biology": ["biology", "genome", "medical"],
    }
    for tag, keywords in mapping.items():
        if any(k in lowered for k in keywords):
            tags.append(tag)

    return title_ko, one_liner, lines[:5], points[:3], tags[:5]
