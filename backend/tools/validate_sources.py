#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import feedparser

LOGGER = logging.getLogger("validate-sources")
USER_AGENT = "NewsDigestBot/1.0 (+https://github.com/)"
TIMEOUT = 12


def validate_feed_url(url: str) -> dict[str, Any]:
    result = {
        "ok": False,
        "status": None,
        "final_url": url,
        "content_type": "",
        "entries": 0,
        "reason": "",
    }
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
            status = getattr(resp, "status", 200)
            final_url = resp.geturl()
            content_type = (resp.headers.get("Content-Type") or "").lower()

        parsed = feedparser.parse(data)
        entries = len(getattr(parsed, "entries", []) or [])

        result.update(
            {
                "ok": bool(status == 200 and (entries > 0 or parsed.feed)),
                "status": status,
                "final_url": final_url,
                "content_type": content_type,
                "entries": entries,
            }
        )
        if not result["ok"]:
            result["reason"] = f"status={status}, entries={entries}"
        return result
    except Exception as exc:  # noqa: BLE001
        result["reason"] = str(exc)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RSS/Atom sources and optionally rewrite enabled/feed_url fields")
    parser.add_argument("--sources", default="backend/sources.json")
    parser.add_argument("--write", action="store_true", help="persist enabled/feed_url updates to sources.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    path = Path(args.sources)
    rows = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    ok_count = 0
    fail_count = 0

    for row in rows:
        feed_url = row.get("feed_url", "")
        if not feed_url:
            row["enabled"] = False
            row["validation_error"] = "missing feed_url"
            row["last_validated_at"] = now
            fail_count += 1
            continue

        result = validate_feed_url(feed_url)
        row["last_validated_at"] = now

        if result["ok"]:
            ok_count += 1
            row["enabled"] = True
            row["validation_error"] = ""
            if result["final_url"] and result["final_url"] != feed_url:
                row["feed_url"] = result["final_url"]
            LOGGER.info("OK   %-28s status=%s entries=%s", row.get("id", row.get("name", "unknown")), result["status"], result["entries"])
        else:
            fail_count += 1
            row["enabled"] = False
            row["validation_error"] = result["reason"]
            LOGGER.warning("FAIL %-28s %s", row.get("id", row.get("name", "unknown")), result["reason"])

    LOGGER.info("validation done: ok=%s fail=%s total=%s", ok_count, fail_count, len(rows))

    if args.write:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
