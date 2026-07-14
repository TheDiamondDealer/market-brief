#!/usr/bin/env python3
"""Retention, provider metadata and collection orchestration."""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from twelve_data_core import *  # noqa: F401,F403
from twelve_data_metrics import *  # noqa: F401,F403

def previous_by_id(previous: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in previous.get("watchlist", []) if isinstance(item, dict) and item.get("id")}


def stale_previous(item: dict[str, Any], previous: dict[str, Any] | None, *, now_iso: str, error: str) -> dict[str, Any]:
    if not previous or previous.get("price") is None:
        return blank_record(item, now_iso, "failed", error)
    retained = copy.deepcopy(previous)
    retained.update({"id":item["id"],"symbol":item["symbol"],"name":item["name"],"exchange":item["exchange"],"group":item["group"],"currency":item["currency"],"status":"stale","collectedAt":now_iso,"error":error})
    return retained


def provider_block(status: str) -> dict[str, Any]:
    return {"id":"twelve-data","name":"Twelve Data","sourceUrl":PROVIDER_URL,"access":"credentialed-server-side","licenseMode":"private-internal-use-only","status":status,"disclaimer":"Provider data is collected by GitHub Actions for an access-controlled internal dashboard. Do not enable while the repository or deployed site is publicly accessible."}


def disabled_payload(items: list[dict[str, Any]], *, now: datetime, reason: str) -> dict[str, Any]:
    now_iso = iso_utc(now)
    records = [blank_record(item, now_iso, "unavailable", None) for item in items]
    return {
        "schemaVersion":1,"generatedAtUtc":now_iso,"provider":provider_block("unavailable"),
        "collection":{"mode":"disabled","status":"unavailable","expectedCadence":"Intraday snapshots during the US session and one daily history refresh","lastSuccessfulAt":None,"successCount":0,"failureCount":len(records),"errors":[reason]},
        "watchlist":records,
        "sourceStatus":[{"id":"twelve-data-api","source":"Twelve Data private market feed","status":"unavailable","observationDate":None,"lastSuccessfulAt":None,"expectedCadence":"Intraday snapshots plus daily full history","detail":reason,"error":reason,"url":PROVIDER_URL}],
        "methodology":{"price":"Latest accepted quote close, otherwise latest accepted daily close.","returns":"Trading-session comparisons using 1, 5, 21, 63 and 252-session references where available.","trend":"Rule-based price and 20/50/200-session moving-average alignment; not a recommendation.","retention":"A failed symbol retains its last verified row with stale status rather than being erased."},
    }


def collect_payload(items: list[dict[str, Any]], *, client: TwelveDataClient, previous: dict[str, Any], mode: str, now: datetime) -> dict[str, Any]:
    if mode not in {"snapshot", "full"}:
        raise SourceError(f"Unsupported collection mode: {mode}")
    now_iso = iso_utc(now)
    previous_rows = previous_by_id(previous)
    output: list[dict[str, Any]] = []
    errors: list[str] = []
    success_count = 0
    for item in items:
        old = previous_rows.get(item["id"])
        quote: dict[str, Any] | None = None
        history = copy.deepcopy(old.get("history", [])) if isinstance(old, dict) else []
        item_errors: list[str] = []
        try:
            quote = client.get("quote", quote_params(item))
        except SourceError as exc:
            item_errors.append(f"quote: {sanitize_error(exc)}")
        if mode == "full":
            try:
                history = parse_history(client.get("time_series", time_series_params(item)))
            except SourceError as exc:
                item_errors.append(f"history: {sanitize_error(exc)}")
        if quote is not None or history:
            record = build_record(item, quote=quote, history=history, now_iso=now_iso, partial_error="; ".join(item_errors) if item_errors else None)
            if record["price"] is not None:
                success_count += 1
            else:
                item_errors.append("No accepted price was available")
                record = stale_previous(item, old, now_iso=now_iso, error="; ".join(item_errors))
        else:
            record = stale_previous(item, old, now_iso=now_iso, error="; ".join(item_errors) or "No provider response was accepted")
        output.append(record)
        if item_errors:
            errors.append(f"{item['symbol']}: {'; '.join(item_errors)}")
    failure_count = len(output) - success_count
    collection_status = "current" if success_count == len(output) else "partial" if success_count else "failed"
    observed = max((str(item.get("observedAt")) for item in output if item.get("observedAt")), default=None)
    previous_last_success = previous.get("collection", {}).get("lastSuccessfulAt")
    last_success = now_iso if success_count else previous_last_success
    return {
        "schemaVersion":1,"generatedAtUtc":now_iso,"provider":provider_block(collection_status),
        "collection":{"mode":mode,"status":collection_status,"expectedCadence":"Intraday snapshots during the US session and one daily history refresh","lastSuccessfulAt":last_success,"successCount":success_count,"failureCount":failure_count,"errors":errors},
        "watchlist":output,
        "sourceStatus":[{"id":"twelve-data-api","source":"Twelve Data private market feed","status":collection_status,"observationDate":observed,"lastSuccessfulAt":last_success,"expectedCadence":"Intraday snapshots plus daily full history","detail":f"{success_count} of {len(output)} configured instruments retained a usable price.","error":"; ".join(errors[:5]) if errors else None,"url":PROVIDER_URL}],
        "methodology":{"price":"Latest accepted quote close, otherwise latest accepted daily close.","returns":"Trading-session comparisons using 1, 5, 21, 63 and 252-session references where available.","trend":"Rule-based price and 20/50/200-session moving-average alignment; not a recommendation.","retention":"A failed symbol retains its last verified row with stale status rather than being erased."},
    }


def collection_exit_code(payload: dict[str, Any]) -> int:
    status = str(payload.get("collection", {}).get("status", "failed"))
    if status in {"current", "partial", "unavailable"}:
        return 0
    retained = any(row.get("price") is not None for row in payload.get("watchlist", []))
    return 0 if status == "failed" and retained else 1
