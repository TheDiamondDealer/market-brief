#!/usr/bin/env python3
"""Shared offline validation helpers for generated Market Brief data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

FORBIDDEN_COT_TERMS = (
    "MICRO",
    "E-MINI",
    "MINI ",
    "ULTRA",
    "FINANCIAL",
    "INDEX",
    "CROSS RATE",
)

MALFORMED_POLITICAL_MARKERS = (
    "\x00",
    "Name: Hon.",
    "State/District:",
    "Transaction Date Notification",
    "ID Owner Asset",
)


class ValidationFailure(ValueError):
    """Raised when generated data fails a trust or consistency rule."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationFailure(f"{path}: root must be an object")
    return value


def duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def cot_name_is_safe(name: str, rejected_terms: Iterable[str] = FORBIDDEN_COT_TERMS) -> bool:
    upper = re.sub(r"\s+", " ", str(name or "")).upper()
    return bool(upper.strip()) and not any(term.upper() in upper for term in rejected_terms)


def assert_safe_cot_name(name: str, rejected_terms: Iterable[str] = FORBIDDEN_COT_TERMS) -> None:
    if not cot_name_is_safe(name, rejected_terms):
        raise ValidationFailure(f"Unsafe COT contract name: {name!r}")


def validate_free_market_semantics(data: dict[str, Any]) -> None:
    rate_ids = [str(row.get("id", "")) for row in data.get("rates", [])]
    cot_ids = [str(row.get("id", "")) for row in data.get("cot", [])]
    for label, values in (("rate", rate_ids), ("COT", cot_ids)):
        duplicates = duplicate_values(value for value in values if value)
        if duplicates:
            raise ValidationFailure(f"Duplicate {label} ids: {', '.join(duplicates)}")

    for row in data.get("cot", []):
        try:
            expected = round(float(row["long"]) - float(row["short"]))
            actual = round(float(row["net"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationFailure(f"Invalid COT numeric row for {row.get('id', 'unknown')}") from exc
        if expected != actual:
            raise ValidationFailure(
                f"COT net mismatch for {row.get('id', 'unknown')}: expected {expected}, got {actual}"
            )


def political_trade_count(data: dict[str, Any]) -> int:
    return sum(
        len(tracker.get("trades", []))
        for tracker in data.get("trackers", {}).values()
        if isinstance(tracker, dict)
    )


def validate_political_semantics(data: dict[str, Any]) -> None:
    trackers = data.get("trackers", {})
    if not isinstance(trackers, dict) or not trackers:
        raise ValidationFailure("Political tracker history is empty")

    pelosi = trackers.get("pelosi", {})
    if not isinstance(pelosi, dict) or not pelosi.get("trades"):
        raise ValidationFailure("Pelosi retained history is unexpectedly empty")

    ids: list[str] = []
    malformed: list[str] = []
    for tracker_id, tracker in trackers.items():
        for trade in tracker.get("trades", []):
            trade_id = str(trade.get("id", ""))
            if trade_id:
                ids.append(trade_id)
            asset = str(trade.get("asset", ""))
            if not asset or any(marker in asset for marker in MALFORMED_POLITICAL_MARKERS):
                malformed.append(f"{tracker_id}:{trade.get('filingId', 'unknown')}:{asset[:80]}")
            if trade.get("traded") == trade.get("filed") and trade.get("lagDays") not in (0, None):
                malformed.append(f"{tracker_id}:{trade.get('filingId', 'unknown')}:lag mismatch")

    duplicates = duplicate_values(ids)
    if duplicates:
        raise ValidationFailure(f"Duplicate political trade ids: {', '.join(duplicates[:10])}")
    if malformed:
        raise ValidationFailure(f"Malformed political rows: {malformed[:5]}")


def validate_summary_consistency(data: dict[str, Any], summary: dict[str, Any]) -> None:
    expected_total = political_trade_count(data)
    actual_total = summary.get("totalTrades")
    if actual_total != expected_total:
        raise ValidationFailure(
            f"Political summary total mismatch: expected {expected_total}, got {actual_total}"
        )
    for tracker_id, tracker in data.get("trackers", {}).items():
        expected = len(tracker.get("trades", []))
        actual = summary.get("trackers", {}).get(tracker_id, {}).get("trades")
        if actual != expected:
            raise ValidationFailure(
                f"Political summary mismatch for {tracker_id}: expected {expected}, got {actual}"
            )
