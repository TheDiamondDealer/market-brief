#!/usr/bin/env python3
"""Shared offline validation helpers for generated Market Brief data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from cot_contracts import generated_row_is_verified

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

EQUITY_STATUSES = {
    "current",
    "delayed",
    "stale",
    "failed",
    "unavailable",
    "partial",
    "unknown",
}


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


def validate_free_market_semantics(data: dict[str, Any], registry: dict[str, Any] | None = None) -> None:
    rate_ids = [str(row.get("id", "")) for row in data.get("rates", [])]
    cot_ids = [str(row.get("id", "")) for row in data.get("cot", [])]
    for label, values in (("rate", rate_ids), ("COT", cot_ids)):
        duplicates = duplicate_values(value for value in values if value)
        if duplicates:
            raise ValidationFailure(f"Duplicate {label} ids: {', '.join(duplicates)}")

    registry_marker = data.get("cotContractRegistry")
    unavailable_ids = {
        str(item.get("id", ""))
        for item in (registry_marker or {}).get("unavailable", [])
        if isinstance(item, dict)
    }
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
        if registry_marker:
            if row.get("id") in unavailable_ids:
                raise ValidationFailure(f"Unavailable COT market was emitted: {row.get('id')}")
            if not generated_row_is_verified(row, registry):
                raise ValidationFailure(f"COT row lacks exact verified identity: {row.get('id', 'unknown')}")
            if row.get("dataState") not in {"current", "stale-retained"}:
                raise ValidationFailure(f"COT row has invalid dataState: {row.get('id', 'unknown')}")

    if registry_marker and registry:
        reference_ids = [str(value) for value in registry_marker.get("referenceProductIds", [])]
        if reference_ids != registry.get("referenceProductIds"):
            raise ValidationFailure("Generated COT referenceProductIds do not match the source registry")
        missing_ids = {
            str(item.get("id", ""))
            for item in registry_marker.get("missing", [])
            if isinstance(item, dict)
        }
        represented_ids = set(cot_ids) | unavailable_ids | missing_ids
        unrepresented = set(reference_ids) - represented_ids
        if unrepresented:
            raise ValidationFailure(f"COT reference products lack a rendered state: {', '.join(sorted(unrepresented))}")
        if set(cot_ids) & missing_ids:
            raise ValidationFailure("Generated COT rows also appear in cotContractRegistry.missing")


def validate_equity_market_semantics(data: dict[str, Any]) -> None:
    provider = data.get("provider", {})
    if provider.get("id") != "twelve-data":
        raise ValidationFailure("Equity market data provider must be Twelve Data")
    if provider.get("licenseMode") != "private-internal-use-only":
        raise ValidationFailure("Equity market data must retain the private internal-use boundary")

    rows = data.get("watchlist", [])
    if not isinstance(rows, list) or not rows:
        raise ValidationFailure("Equity market watchlist is empty")

    ids = [str(row.get("id", "")) for row in rows]
    identities = [
        f"{str(row.get('symbol', '')).upper()}::{str(row.get('exchange', '')).upper()}"
        for row in rows
    ]
    for label, values in (("equity id", ids), ("equity identity", identities)):
        duplicates = duplicate_values(value for value in values if value)
        if duplicates:
            raise ValidationFailure(f"Duplicate {label}s: {', '.join(duplicates[:10])}")

    collection = data.get("collection", {})
    success_count = collection.get("successCount")
    failure_count = collection.get("failureCount")
    if not isinstance(success_count, int) or not isinstance(failure_count, int):
        raise ValidationFailure("Equity collection counts must be integers")
    if success_count + failure_count != len(rows):
        raise ValidationFailure(
            f"Equity collection counts do not match watchlist: {success_count}+{failure_count}!={len(rows)}"
        )
    if collection.get("status") == "current" and success_count != len(rows):
        raise ValidationFailure("Current equity collection must have a usable price for every configured row")
    if collection.get("status") == "failed" and success_count != 0:
        raise ValidationFailure("Failed equity collection cannot report successful rows")

    disabled = collection.get("mode") == "disabled"
    for row in rows:
        row_id = row.get("id", "unknown")
        status = row.get("status")
        if status not in EQUITY_STATUSES:
            raise ValidationFailure(f"Unknown equity status for {row_id}: {status}")
        if status in {"current", "partial"} and row.get("price") is None:
            raise ValidationFailure(f"Usable equity row has no price: {row_id}")
        if disabled and (row.get("status") != "unavailable" or row.get("price") is not None):
            raise ValidationFailure(f"Disabled equity feed must not publish a price: {row_id}")

        history = row.get("history", [])
        dates = [str(item.get("date", "")) for item in history if isinstance(item, dict)]
        if dates != sorted(dates):
            raise ValidationFailure(f"Equity history is not sorted for {row_id}")
        duplicates = duplicate_values(date for date in dates if date)
        if duplicates:
            raise ValidationFailure(f"Duplicate equity history dates for {row_id}: {duplicates[:5]}")
        if len(history) > 260:
            raise ValidationFailure(f"Equity history exceeds 260 rows for {row_id}")

    rendered = json.dumps(data, ensure_ascii=False).lower()
    if "apikey=" in rendered or "twelve_data_api_key" in rendered:
        raise ValidationFailure("Generated equity data appears to contain an API credential")


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
