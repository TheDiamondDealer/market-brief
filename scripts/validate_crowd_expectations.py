#!/usr/bin/env python3
"""Validate the generated crowd-expectations cache without network access."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_crowd_expectations import classify_market  # noqa: E402
from update_crowd_expectations_hardened import validate_output  # noqa: E402

DATA = ROOT / "site" / "data" / "crowd-expectations.json"
SCHEMA = ROOT / "schemas" / "crowd-expectations.schema.json"
REGISTRY = ROOT / "scripts" / "crowd_expectations_registry.json"


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda item: list(item.path),
    )
    if errors:
        rendered = []
        for error in errors[:12]:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise SystemExit(
            "Crowd-expectations schema validation failed: " + "; ".join(rendered)
        )

    try:
        validate_output(data)
    except ValueError as exc:
        raise SystemExit(f"Crowd-expectations semantic validation failed: {exc}") from exc

    markets = data["markets"]
    if data["collection"]["selectedMarketCount"] != len(markets):
        raise SystemExit("selectedMarketCount does not match markets length")
    if sum(category["count"] for category in data["categories"]) != len(markets):
        raise SystemExit("Category counts do not match markets length")

    for market in markets:
        classified, _ = classify_market(
            {
                "question": market.get("question"),
                "description": market.get("description"),
                "events": [{"title": market.get("eventTitle") or ""}],
            },
            registry,
        )
        if classified is None or classified.get("id") != market.get("categoryId"):
            expected = classified.get("id") if classified else "excluded"
            raise SystemExit(
                f"Category classification mismatch: {market['id']} is "
                f"{market.get('categoryId')}, expected {expected}"
            )
        if market["probabilityPercent"] != round(market["probability"] * 100, 2):
            raise SystemExit(f"Probability-percent mismatch: {market['id']}")
        if market["qualityGrade"] == "A" and market["qualityScore"] < 80:
            raise SystemExit(f"Grade A below threshold: {market['id']}")
        if market["qualityGrade"] == "B" and not 65 <= market["qualityScore"] < 80:
            raise SystemExit(f"Grade B outside threshold: {market['id']}")
        if market["qualityGrade"] == "C" and not 50 <= market["qualityScore"] < 65:
            raise SystemExit(f"Grade C outside threshold: {market['id']}")
        if market["qualityGrade"] == "D" and market["qualityScore"] >= 50:
            raise SystemExit(f"Grade D above threshold: {market['id']}")

    market_ids = {market["id"] for market in markets}
    for shock in data["shocks"]:
        if shock["marketId"] not in market_ids:
            raise SystemExit(f"Shock references unknown market: {shock['marketId']}")
        if abs(shock["change24hPoints"]) < 5:
            raise SystemExit(f"Shock below five-point threshold: {shock['marketId']}")

    print(
        f"Validated {len(markets)} read-only crowd markets and "
        f"{len(data['shocks'])} crowd shocks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
