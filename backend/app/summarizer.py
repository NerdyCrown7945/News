import re
from typing import Protocol


class Summarizer(Protocol):
    def summarize(self, text: str) -> dict:
        ...


class RuleBasedSummarizer:
    def summarize(self, text: str) -> dict:
        clean = " ".join((text or "").split())
        if not clean:
            return {
                "one_liner": "No summary available.",
                "summary_lines": [],
                "key_points": [],
            }

        parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        picked = parts[:5]
        return {
            "one_liner": picked[0][:220],
            "summary_lines": picked[:5],
            "key_points": picked[:3],
        }


class LLMSummarizerStub:
    """TODO: Replace with actual LLM integration."""

    def summarize(self, text: str) -> dict:
        raise NotImplementedError("LLM summarizer interface is not implemented yet.")
