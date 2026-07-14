#!/usr/bin/env python3
"""Metric and normalized-row helpers for the Twelve Data collector."""
from __future__ import annotations

from typing import Any

from twelve_data_core import *  # noqa: F401,F403

def quote_observed_at(payload: dict[str, Any]) -> str | None:
    timestamp = safe_float(payload.get("timestamp"))
    if timestamp is not None:
        try:
            return iso_utc(datetime.fromtimestamp(timestamp, tz=timezone.utc))
        except (OSError, OverflowError, ValueError):
            pass
    value = str(payload.get("datetime") or payload.get("last_quote_at") or "").strip()
    if not value:
        return None
    return value.replace(" ", "T")


def parse_fifty_two_week(payload: dict[str, Any]) -> tuple[float | None, float | None]:
    section = payload.get("fifty_two_week")
    if not isinstance(section, dict):
        return None, None
    return safe_float(section.get("low")), safe_float(section.get("high"))


def previous_reference(history: list[dict[str, Any]], sessions_back: int) -> float | None:
    if not history:
        return None
    index = len(history) - 1 - sessions_back
    if index < 0:
        return None
    return safe_float(history[index].get("close"))


def moving_average(history: list[dict[str, Any]], sessions: int) -> float | None:
    if len(history) < sessions:
        return None
    return average(safe_float(item.get("close")) for item in history[-sessions:])


def derive_trend(
    price: float | None,
    ma20: float | None,
    ma50: float | None,
    ma200: float | None,
) -> dict[str, str]:
    if price is None or ma20 is None or ma50 is None:
        return {"state": "insufficient", "detail": "Insufficient verified history for a trend classification."}
    if price > ma20 > ma50 and (ma200 is None or ma50 > ma200):
        return {"state": "bullish", "detail": "Price is above the 20- and 50-session averages with aligned trend structure."}
    if price < ma20 < ma50 and (ma200 is None or ma50 < ma200):
        return {"state": "bearish", "detail": "Price is below the 20- and 50-session averages with aligned downside structure."}
    return {"state": "mixed", "detail": "Moving averages and price are not aligned in one direction."}


def blank_record(item: dict[str, Any], now_iso: str, status: str, error: str | None) -> dict[str, Any]:
    return {
        "id": item["id"],
        "symbol": item["symbol"],
        "name": item["name"],
        "exchange": item["exchange"],
        "group": item["group"],
        "currency": item["currency"],
        "status": status,
        "observedAt": None,
        "collectedAt": now_iso,
        "price": None,
        "sourceUrl": PROVIDER_URL,
        "error": error,
    }


def build_record(
    item: dict[str, Any],
    *,
    quote: dict[str, Any] | None,
    history: list[dict[str, Any]],
    now_iso: str,
    partial_error: str | None = None,
) -> dict[str, Any]:
    latest_history = history[-1] if history else {}
    price = safe_float((quote or {}).get("close"))
    if price is None:
        price = safe_float(latest_history.get("close"))
    previous_close = safe_float((quote or {}).get("previous_close"))
    if previous_close is None:
        previous_close = previous_reference(history, 1)
    change = safe_float((quote or {}).get("change"))
    if change is None and price is not None and previous_close is not None:
        change = price - previous_close
    percent_change = safe_float((quote or {}).get("percent_change"))
    if percent_change is None:
        percent_change = pct_change(price, previous_close)
    volume = safe_int((quote or {}).get("volume"))
    if volume is None:
        volume = safe_int(latest_history.get("volume"))
    ma20 = moving_average(history, 20)
    ma50 = moving_average(history, 50)
    ma200 = moving_average(history, 200)
    average_volume20 = average(safe_float(row.get("volume")) for row in history[-20:])
    low52, high52 = parse_fifty_two_week(quote or {})
    recent = history[-252:]
    history_lows = [safe_float(row.get("low")) for row in recent]
    history_highs = [safe_float(row.get("high")) for row in recent]
    if low52 is None:
        cleaned_lows = [value for value in history_lows if value is not None]
        low52 = min(cleaned_lows) if cleaned_lows else None
    if high52 is None:
        cleaned_highs = [value for value in history_highs if value is not None]
        high52 = max(cleaned_highs) if cleaned_highs else None
    range_position = None
    if price is not None and low52 is not None and high52 is not None and high52 > low52:
        range_position = rounded((price - low52) / (high52 - low52) * 100, 1)
    observed_at = quote_observed_at(quote or {}) or str(latest_history.get("date") or "") or None
    status = "partial" if partial_error else ("current" if price is not None else "failed")
    return {
        "id": item["id"],
        "symbol": item["symbol"],
        "name": str((quote or {}).get("name") or item["name"]),
        "exchange": str((quote or {}).get("exchange") or item["exchange"]),
        "group": item["group"],
        "currency": str((quote or {}).get("currency") or item["currency"]),
        "status": status,
        "observedAt": observed_at,
        "collectedAt": now_iso,
        "price": rounded(price),
        "previousClose": rounded(previous_close),
        "change": rounded(change),
        "percentChange": rounded(percent_change, 2),
        "volume": volume,
        "averageVolume20": safe_int(average_volume20),
        "volumeRatio20": rounded(volume / average_volume20, 2) if volume is not None and average_volume20 not in (None, 0) else None,
        "returns": {
            "day": rounded(percent_change, 2),
            "week": pct_change(price, previous_reference(history, 5)),
            "month": pct_change(price, previous_reference(history, 21)),
            "threeMonth": pct_change(price, previous_reference(history, 63)),
            "year": pct_change(price, previous_reference(history, 252)),
        },
        "movingAverages": {"day20": rounded(ma20), "day50": rounded(ma50), "day200": rounded(ma200)},
        "distanceFromMovingAverages": {
            "day20": pct_change(price, ma20),
            "day50": pct_change(price, ma50),
            "day200": pct_change(price, ma200),
        },
        "range52Week": {"low": rounded(low52), "high": rounded(high52), "positionPercent": range_position},
        "trend": derive_trend(price, ma20, ma50, ma200),
        "history": history[-260:],
        "sourceUrl": PROVIDER_URL,
        "error": partial_error,
    }
