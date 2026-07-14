#!/usr/bin/env python3
"""Validate committed generated data and the COT registry without network access."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cot_contracts import validate_registry  # noqa: E402
from validation_helpers import (  # noqa: E402
    ValidationFailure,
    read_json,
    validate_free_market_semantics,
    validate_political_semantics,
    validate_summary_consistency,
)

TARGETS = (
    (
        ROOT / "scripts" / "cot_contracts.json",
        ROOT / "schemas" / "cot-contract-registry.schema.json",
    ),
    (
        ROOT / "site" / "data" / "free-market-data.json",
        ROOT / "schemas" / "free-market-data.schema.json",
    ),
    (
        ROOT / "site" / "data" / "political-disclosures.json",
        ROOT / "schemas" / "political-disclosures.schema.json",
    ),
    (
        ROOT / "site" / "data" / "political-disclosures-summary.json",
        ROOT / "schemas" / "political-disclosures-summary.schema.json",
    ),
)


def validate_schema(data_path: Path, schema_path: Path) -> dict:
    data = read_json(data_path)
    schema = read_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        rendered = []
        for error in errors[:10]:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise ValidationFailure(f"{data_path}: schema validation failed: {'; '.join(rendered)}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args()

    loaded = {path.name: validate_schema(path, schema) for path, schema in TARGETS}
    registry = loaded["cot_contracts.json"]
    validate_registry(registry)
    if not args.schema_only:
        free_data = loaded["free-market-data.json"]
        political = loaded["political-disclosures.json"]
        summary = loaded["political-disclosures-summary.json"]
        validate_free_market_semantics(free_data, registry)
        validate_political_semantics(political)
        validate_summary_consistency(political, summary)

    total = loaded["political-disclosures-summary.json"]["totalTrades"]
    print(f"Validated COT registry plus 3 generated datasets; retained political trades={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
