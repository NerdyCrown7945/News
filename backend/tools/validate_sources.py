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
    parser = argparse.ArgumentParser(description="Validate RSS/Atom sources and save a separate validation report")
    parser.add_argument("--sources", default="backend/sources.json")
    parser.add_argument("--report", default="backend/validation_report.json", help="path for validation report JSON")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    path = Path(args.sources)
    rows = json.loads(path.read_text(encoding="utf-8"))
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    ok_count = 0
    fail_count = 0
    results: list[dict[str, Any]] = []

    for row in rows:
        source_id = row.get("id", row.get("name", "unknown"))
        feed_url = row.get("feed_url", "")

        if not feed_url:
            fail_count += 1
            results.append(
                {
                    "id": source_id,
                    "ok": False,
                    "status": None,
                    "error": "missing feed_url",
                    "entries": 0,
                    "feed_url": "",
                    "final_url": "",
                }
            )
            LOGGER.warning("FAIL %-28s missing feed_url", source_id)
            continue

        result = validate_feed_url(feed_url)
        if result["ok"]:
            ok_count += 1
            LOGGER.info("OK   %-28s status=%s entries=%s", source_id, result["status"], result["entries"])
        else:
            fail_count += 1
            LOGGER.warning("FAIL %-28s %s", source_id, result["reason"])

        results.append(
            {
                "id": source_id,
                "ok": result["ok"],
                "status": result["status"],
                "error": result["reason"],
                "entries": result["entries"],
                "feed_url": feed_url,
                "final_url": result["final_url"],
            }
        )

    LOGGER.info("validation done: ok=%s fail=%s total=%s", ok_count, fail_count, len(rows))

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "checked_at": checked_at,
        "summary": {"total": len(rows), "ok": ok_count, "failed": fail_count},
        "results": results,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("wrote validation report: %s", report_path)


if __name__ == "__main__":
    main()
