#!/usr/bin/env python3
"""Validate the generated free official-feeds cache without network access."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data" / "official-feeds.json"
SCHEMA = ROOT / "schemas" / "official-feeds.schema.json"
EXPECTED_IDS = {"sec-edgar", "bls-public-data", "eia-energy", "bea-nipa", "census-eits", "usgs-minerals"}
STATUSES = {"current", "delayed", "stale", "failed", "unavailable", "partial", "unknown"}


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        rendered = []
        for error in errors[:12]:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise SystemExit("Official-feed schema validation failed: " + "; ".join(rendered))

    sources = data["sources"]
    ids = {source["id"] for source in sources}
    if ids != EXPECTED_IDS:
        raise SystemExit(f"Official-feed source set mismatch: {sorted(ids)}")
    if data["collection"]["successCount"] + data["collection"]["failureCount"] + data["collection"]["unavailableCount"] != len(sources):
        raise SystemExit("Official-feed collection counts do not match the source registry")

    all_record_ids: set[str] = set()
    for source in sources:
        if source["status"] not in STATUSES:
            raise SystemExit(f"Unknown source status: {source['id']}={source['status']}")
        record_ids = [str(record["id"]) for record in source["records"]]
        if len(record_ids) != len(set(record_ids)):
            raise SystemExit(f"Duplicate records inside {source['id']}")
        overlap = set(record_ids).intersection(all_record_ids)
        if overlap:
            raise SystemExit(f"Cross-source record id collision: {sorted(overlap)[:5]}")
        all_record_ids.update(record_ids)
        if source["status"] == "current" and not source["records"]:
            raise SystemExit(f"Current source has no records: {source['id']}")
        if source["status"] == "unavailable" and source["records"]:
            raise SystemExit(f"Unavailable source unexpectedly publishes records: {source['id']}")

    rendered = json.dumps(data, ensure_ascii=False)
    if re.search(r"(?i)(api_key|apikey|userid|registrationkey)=[^&\s\[\]]+", rendered):
        raise SystemExit("Official-feed cache appears to contain a credential query parameter")

    print(f"Validated six official sources and {len(all_record_ids)} retained records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
