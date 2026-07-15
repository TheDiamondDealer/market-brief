#!/usr/bin/env python3
"""Harden the read-only Crowd Expectations collector.

This layer improves resolution-source extraction, validates actual bid/ask
spreads, applies event-specific asset mappings and validates generated structure
without scanning legitimate market prose for generic words such as "signature".
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
            trailing_urls = [
                match.rstrip(".,);]") for match in _URL_RE.findall(trailing)
            ]
            if trailing_urls:
                return trailing_urls[0]
        return urls[0]
    return "Resolution source described in the market rules"


def computed_spread(market: dict[str, Any]) -> float | None:
    bid = base.number(market.get("bestBid"))
    ask = base.number(market.get("bestAsk"))
    if bid is None or ask is None or not 0 <= bid <= ask <= 1:
        return None
    return ask - bid


def selected_probability(
    market: dict[str, Any],
    outcome_probability: float | None,
) -> tuple[float | None, str]:
    bid = base.number(market.get("bestBid"))
    ask = base.number(market.get("bestAsk"))
    spread = computed_spread(market)
    if bid is not None and ask is not None and spread is not None and spread <= 0.10:
        return (bid + ask) / 2, "bid-ask midpoint"
    last = base.number(market.get("lastTradePrice"))
    if last is not None and 0 <= last <= 1:
        return last, "last trade"
    if outcome_probability is not None and 0 <= outcome_probability <= 1:
        return outcome_probability, "Gamma outcome price"
    return None, "unavailable"


def quality_score(
    market: dict[str, Any],
    relevance_score: int,
) -> tuple[int, str, list[str]]:
    enriched = copy.deepcopy(market)
    source = resolution_source(market)
    enriched["resolutionSource"] = source or ""
    spread = computed_spread(market)
    if spread is not None:
        enriched["spread"] = spread
    score, grade, reasons = _ORIGINAL_QUALITY_SCORE(enriched, relevance_score)
    if not source and score >= 80:
        score = 79
        grade = "B"
        reasons = [*reasons, "Grade capped below A until a resolution source is identifiable"]
    return score, grade, reasons


def asset_map(category: dict[str, Any], market: dict[str, Any]) -> list[str]:
    """Map only event-relevant assets rather than every asset in a category."""
    category_id = str(category.get("id") or "")
    text = base.normalized(
        f"{market.get('question', '')} {market.get('description', '')} "
        f"{base.event_title(market)}"
    )
    assets: set[str] = set()

    defaults = {
        "monetary-policy": {"rates", "us-dollar", "gold", "silver", "semiconductors"},
        "geopolitics-security": {"gold", "us-dollar"},
        "technology-ai": {"semiconductors"},
        "us-policy-elections": {"rates", "us-dollar"},
        "trade-industrial-policy": {"us-dollar"},
    }
    assets.update(defaults.get(category_id, set()))

    if "gold" in text:
        assets.add("gold")
    if "silver" in text:
        assets.add("silver")
    if "copper" in text:
        assets.add("copper")
    if "rare earth" in text or "critical mineral" in text:
        assets.add("rare-earths")

    if "wti" in text or "west texas intermediate" in text:
        assets.add("wti")
    elif "brent" in text:
        assets.add("brent")
    elif any(term in text for term in ("opec", "strait of hormuz", "crude oil", "oil production")):
        assets.update({"brent", "wti"})

    if "henry hub" in text or "us natural gas" in text:
        assets.add("gas-us")
    if any(term in text for term in ("uk gas", "european gas", "lng", "natural gas")):
        assets.add("gas-uk")

    if any(
        term in text
        for term in (
            "semiconductor",
            "chip",
            "nvidia",
            "amd",
            "intel",
            "tsmc",
            "asml",
            "taiwan",
            "data center",
            "data centre",
            "artificial intelligence",
        )
    ):
        assets.add("semiconductors")
    if any(term in text for term in ("taiwan", "south china sea", "china export control")):
        assets.add("rare-earths")

    if any(
        term in text
        for term in (
            "fed",
            "fomc",
            "interest rate",
            "inflation",
            "cpi",
            "pce",
            "recession",
            "unemployment",
            "payroll",
            "gdp",
        )
    ):
        assets.add("rates")
    if any(
        term in text
        for term in (
            "tariff",
            "sanction",
            "election",
            "debt ceiling",
            "government shutdown",
            "federal reserve",
            "fed",
        )
    ):
        assets.add("us-dollar")
    if "debt ceiling" in text or "government shutdown" in text:
        assets.add("gold")

    return sorted(assets)


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
        record["assets"] = asset_map(category, raw)
        spread = computed_spread(raw)
        if spread is not None:
            record["spread"] = round(spread, 6)
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


base.selected_probability = selected_probability
base.quality_score = quality_score
base.asset_map = asset_map
base.market_record = market_record
base.validate_output = validate_output


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
