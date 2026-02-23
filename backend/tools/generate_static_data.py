#!/usr/bin/env python3
"""Compatibility wrapper for static RSS data generation.

Some branches and workflow comments refer to `backend/tools/generate_static_data.py`.
The canonical implementation lives in `backend/scripts/generate_news_data.py`.
This wrapper keeps a stable entrypoint while reusing the same extraction/
canonicalization/home-section filtering logic.
"""

from __future__ import annotations

from backend.scripts.generate_news_data import main


if __name__ == "__main__":
    main()
