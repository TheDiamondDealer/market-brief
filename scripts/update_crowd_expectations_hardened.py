#!/usr/bin/env python3
"""Harden the read-only Crowd Expectations collector.

This layer improves resolution-source extraction and validates the generated
structure without scanning legitimate market questions or resolution rules for
generic words such as "signature".
"""
from __future__ import annotations

import copy
import re
from typing import Any

import update_crowd_expectations as base

_ORIGINAL_QUALITY_SCORE = base.quality_score
_ORIGINAL_MARKET_RECORD = base.market_record
_URL_RE = re.compile(r"https?://[^\s<>\"']+")
_PROHIBITED_KEYS = {
    "private_key",
    "privatekey",
    "api_secret",
    "apisecret",
    "walletconnect",
    "signed_order",
    "signedorder",
    "order_payload",
}
_ORDER_ENDPOINT_RE = re.compile(r"https?://[^\s]+/(?:order|orders)(?:[/?#]|$)", re.I)


def resolution_source(market: dict[str, Any]) -> str | None:
    """Return the most specific resolution source supplied by the market."""
    direct = str(market.get("resolutionSource") or "").strip()
    if direct:
        return direct

    for event in market.get("events") or []:
        if not isinstance(event, dict):
            continue
        candidate = str(event.get("resolutionSource") or "").strip()
        if candidate:
            return candidate

    description = str(market.get("description") or "").strip()
    lowered = description.lower()
    if "resolution source" not in lowered and "will resolve" not in lowered:
        return None

    urls = [match.rstrip(".,);]") for match in _URL_RE.findall(description)]
    if urls:
        marker = lowered.find("resolution source")
        if marker >= 0:
            trailing = description[marker:]
            trailing_urls = [match.rstrip(".,);]") for match in _URL_RE.findall(trailing)]
            if trailing_urls:
                return trailing_urls[0]
        return urls[0]
    return "Resolution source described in the market rules"


def quality_score(
    market: dict[str, Any],
    relevance_score: int,
) -> tuple[int, str, list[str]]:
    enriched = copy.deepcopy(market)
    enriched["resolutionSource"] = resolution_source(market) or ""
    return _ORIGINAL_QUALITY_SCORE(enriched, relevance_score)


def market_record(
    raw: dict[str, Any],
    category: dict[str, Any],
    relevance_score: int,
    previous: dict[str, Any] | None,
    collected_at: str,
    history_days: int,
) -> dict[str, Any] | None:
    record = _ORIGINAL_MARKET_RECORD(
        raw,
        category,
        relevance_score,
        previous,
        collected_at,
        history_days,
    )
    if record is not None:
        record["resolutionSource"] = resolution_source(raw)
    return record


def iter_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).lower()
            yield from iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_keys(child)


def controlled_urls(data: dict[str, Any]):
    provider = data.get("provider", {})
    for key in ("marketEndpoint", "documentationUrl", "geoblockUrl"):
        value = provider.get(key)
        if value:
            yield str(value)
    for market in data.get("markets", []):
        value = market.get("sourceUrl")
        if value:
            yield str(value)
    for source in data.get("sourceStatus", []):
        value = source.get("url")
        if value:
            yield str(value)


def validate_output(data: dict[str, Any]) -> None:
    if data.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    provider = data.get("provider", {})
    if provider.get("id") != "polymarket" or provider.get("readOnly") is not True:
        raise ValueError("Provider must remain Polymarket read-only")
    if provider.get("marketEndpoint") != "https://gamma-api.polymarket.com/markets":
        raise ValueError("Unexpected Polymarket market-data endpoint")

    markets = data.get("markets")
    if not isinstance(markets, list):
        raise ValueError("markets must be a list")
    ids = [str(item.get("id") or "") for item in markets]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate crowd market ids")

    for item in markets:
        if item.get("readOnly") is not True:
            raise ValueError(f"Market is not read-only: {item.get('id')}")
        probability = base.number(item.get("probability"))
        if probability is None or not 0 <= probability <= 1:
            raise ValueError(f"Invalid probability: {item.get('id')}")
        history = item.get("history", [])
        dates = [
            str(point.get("date") or "")
            for point in history
            if isinstance(point, dict)
        ]
        if dates != sorted(dates) or len(dates) != len(set(dates)):
            raise ValueError(f"Invalid history dates: {item.get('id')}")
        if len(history) > 90:
            raise ValueError(f"History exceeds 90 days: {item.get('id')}")

    forbidden = sorted(set(iter_keys(data)).intersection(_PROHIBITED_KEYS))
    if forbidden:
        raise ValueError(f"Generated crowd data contains prohibited fields: {forbidden}")
    for url in controlled_urls(data):
        if _ORDER_ENDPOINT_RE.search(url):
            raise ValueError(f"Generated crowd data contains an order endpoint: {url}")


base.quality_score = quality_score
base.market_record = market_record
base.validate_output = validate_output


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
