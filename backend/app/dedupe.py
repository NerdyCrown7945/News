from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TITLE_SIM_THRESHOLD = 0.9


def canonicalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    clean_qs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
    ]
    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", urlencode(clean_qs), "")
    )


def normalize_title(title: str) -> str:
    lowered = re.sub(r"[^a-z0-9\s]", " ", (title or "").lower())
    return re.sub(r"\s+", " ", lowered).strip()


def similar_title(a: str, b: str, threshold: float = TITLE_SIM_THRESHOLD) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(a=a, b=b).ratio() >= threshold
