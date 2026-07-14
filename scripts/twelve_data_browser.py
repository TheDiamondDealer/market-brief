#!/usr/bin/env python3
"""Browser cache loader for the private equity JSON dataset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_js(path: Path, payload: dict[str, Any]) -> None:
    """Write a stable loader; generated JSON remains the browser data source."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fallback = {
        "schemaVersion": 1,
        "generatedAtUtc": payload.get("generatedAtUtc"),
        "provider": payload.get("provider", {}),
        "collection": {"mode": "disabled", "status": "unknown", "successCount": 0, "failureCount": 0, "errors": []},
        "watchlist": [],
        "sourceStatus": [],
        "methodology": {},
    }
    fallback_json = json.dumps(fallback, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    path.write_text(
        "(() => {\n"
        f"  window.equityMarketData = {fallback_json};\n"
        "  const publish = (data) => { window.equityMarketData = data; window.dispatchEvent(new CustomEvent('marketbrief:equity-data', { detail: data })); };\n"
        "  fetch('data/equity-market-data.json', { cache: 'no-store', credentials: 'same-origin' })\n"
        "    .then((response) => { if (!response.ok) throw new Error(`Equity cache HTTP ${response.status}`); return response.json(); })\n"
        "    .then(publish)\n"
        "    .catch((error) => { window.equityMarketData.collection.status = 'failed'; window.equityMarketData.collection.errors = [String(error.message || error)]; publish(window.equityMarketData); });\n"
        "})();\n",
        encoding="utf-8",
    )
