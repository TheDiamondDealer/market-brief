#!/usr/bin/env python3
"""Validate the generated crowd-expectations cache without network access."""

from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data" / "crowd-expectations.json"
SCHEMA = ROOT / "schemas" / "crowd-expectations.schema.json"
PROHIBITED_CODE_MARKERS = (
    "post_order",
    "create_order",
    "private_key",
    "api_secret",
    "walletconnect",
)


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        rendered = []
        for error in errors[:12]:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise SystemExit("Crowd-expectations schema validation failed: " + "; ".join(rendered))

    if data["provider"]["id"] != "polymarket" or data["provider"]["readOnly"] is not True:
        raise SystemExit("Crowd feed must remain Polymarket read-only")

    markets = data["markets"]
    if data["collection"]["selectedMarketCount"] != len(markets):
        raise SystemExit("selectedMarketCount does not match markets length")
    if sum(category["count"] for category in data["categories"]) != len(markets):
        raise SystemExit("Category counts do not match markets length")

    ids = [market["id"] for market in markets]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate crowd market ids")

    for market in markets:
        if market["readOnly"] is not True:
            raise SystemExit(f"Market is not read-only: {market['id']}")
        if market["probabilityPercent"] != round(market["probability"] * 100, 2):
            raise SystemExit(f"Probability-percent mismatch: {market['id']}")
        dates = [point["date"] for point in market["history"]]
        if dates != sorted(dates) or len(dates) != len(set(dates)):
            raise SystemExit(f"Invalid history sequence: {market['id']}")
        if len(market["history"]) > 90:
            raise SystemExit(f"History exceeds retention: {market['id']}")
        if market["qualityGrade"] == "A" and market["qualityScore"] < 80:
            raise SystemExit(f"Grade A below threshold: {market['id']}")
        if market["qualityGrade"] == "B" and not 65 <= market["qualityScore"] < 80:
            raise SystemExit(f"Grade B outside threshold: {market['id']}")
        if market["qualityGrade"] == "C" and not 50 <= market["qualityScore"] < 65:
            raise SystemExit(f"Grade C outside threshold: {market['id']}")
        if market["qualityGrade"] == "D" and market["qualityScore"] >= 50:
            raise SystemExit(f"Grade D above threshold: {market['id']}")

    market_ids = set(ids)
    for shock in data["shocks"]:
        if shock["marketId"] not in market_ids:
            raise SystemExit(f"Shock references unknown market: {shock['marketId']}")
        if abs(shock["change24hPoints"]) < 5:
            raise SystemExit(f"Shock below five-point threshold: {shock['marketId']}")

    rendered = json.dumps(data, ensure_ascii=False).lower()
    for marker in PROHIBITED_CODE_MARKERS:
        if marker in rendered:
            raise SystemExit(f"Prohibited trading marker in generated data: {marker}")
    if re.search(r"https?://[^\"\s]+/(order|orders)(?:[/?#]|$)", rendered):
        raise SystemExit("Generated data contains an order endpoint")

    print(f"Validated {len(markets)} read-only crowd markets and {len(data['shocks'])} crowd shocks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
