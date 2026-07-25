#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data" / "central-bank-decisions.json"
SCHEMA = ROOT / "schemas" / "central-bank-decisions.schema.json"

# Reuse the collector's semantic validator (probabilities, history, modal, markers).
sys.path.insert(0, str(ROOT / "scripts"))
import update_central_bank_decisions as cb  # noqa: E402


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: e.path)
    if errors:
        rendered = [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]
        raise SystemExit("Central-bank-decisions schema validation failed: " + "; ".join(rendered))
    try:
        cb.validate_output(data)
    except ValueError as exc:
        raise SystemExit(f"Central-bank-decisions semantic validation failed: {exc}") from exc
    covered = data["collection"]["banksCovered"]
    print(f"Central-bank-decisions OK: status={data['collection']['status']}; banksCovered={covered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
