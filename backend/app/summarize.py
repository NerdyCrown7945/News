from __future__ import annotations

import re
from typing import Protocol


class Summarizer(Protocol):
    def summarize(self, text: str, title: str) -> dict:
        ...


class RuleBasedSummarizer:
    """기본 더미 요약기(규칙 기반)."""

    def summarize(self, text: str, title: str) -> dict:
        clean = " ".join((text or "").split())
        if not clean:
            fallback = title[:220] if title else "No summary available."
            return {
                "one_liner": fallback,
                "summary_lines": [fallback],
                "key_points": [fallback],
            }

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        first = sentences[0] if sentences else clean
        summary_lines = sentences[:3] if sentences else [clean[:220]]
        key_points = sentences[:3] if sentences else [clean[:220]]
        return {
            "one_liner": first[:220],
            "summary_lines": summary_lines,
            "key_points": key_points,
        }


class LLMSummarizerStub:
    """향후 API 키 연동 시 대체할 LLM 요약 인터페이스."""

    def summarize(self, text: str, title: str) -> dict:
        raise NotImplementedError("Replace with external LLM provider integration.")
