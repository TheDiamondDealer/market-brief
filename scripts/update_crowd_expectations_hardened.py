#!/usr/bin/env python3
"""Harden the read-only Crowd Expectations collector."""
from __future__ import annotations

import copy
import re
from typing import Any

import update_crowd_expectations as base

_ORIGINAL_BUILD_DATASET = base.build_dataset
_ORIGINAL_QUALITY_SCORE = base.quality_score
_ORIGINAL_MARKET_RECORD = base.market_record
_URL_RE = re.compile(r"https?://[^\s<>\"']+")
_PROHIBITED_KEYS = {
    "private_key", "privatekey", "api_secret", "apisecret",
    "walletconnect", "signed_order", "signedorder", "order_payload",
}
_ORDER_ENDPOINT_RE = re.compile(r"https?://[^\s]+/(?:order|orders)(?:[/?#]|$)", re.I)


def resolution_source(market: dict[str, Any]) -> str | None:
    direct = str(market.get("resolutionSource") or "").strip()
    if direct:
        return direct
    for event in market.get("events") or []:
        if isinstance(event, dict):
            candidate = str(event.get("resolutionSource") or "").strip()
            if candidate:
                return candidate
    description = str(market.get("description") or "").strip()
    lowered = description.lower()
    if "resolution source" not in lowered and "will resolve" not in lowered:
        return None
    urls = [match.rstrip(".,);]") for match in _URL_RE.findall(description)]
    if not urls:
        return None
    marker = lowered.find("resolution source")
    if marker >= 0:
        trailing_urls = [
            match.rstrip(".,);]")
            for match in _URL_RE.findall(description[marker:])
        ]
        if trailing_urls:
            return trailing_urls[0]
    return urls[0]


def computed_spread(market: dict[str, Any]) -> float | None:
    bid = base.number(market.get("bestBid"))
    ask = base.number(market.get("bestAsk"))
    if bid is None or ask is None or not 0 <= bid <= ask <= 1:
        return None
    return ask - bid


def selected_probability(
    market: dict[str, Any], outcome_probability: float | None
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
    market: dict[str, Any], relevance_score: int
) -> tuple[int, str, list[str]]:
    enriched = copy.deepcopy(market)
    source = resolution_source(market)
    enriched["resolutionSource"] = source or ""
    spread = computed_spread(market)
    if spread is not None:
        enriched["spread"] = spread
    score, grade, reasons = _ORIGINAL_QUALITY_SCORE(enriched, relevance_score)
    if not source and score >= 80:
        score, grade = 79, "B"
        reasons = [
            *reasons,
            "Grade capped below A until a resolution source is identifiable",
        ]
    return score, grade, reasons


def asset_map(category: dict[str, Any], market: dict[str, Any]) -> list[str]:
    """Map event-relevant assets without broad category-wide contamination."""
    category_id = str(category.get("id") or "")
    text = base.normalized(
        f"{market.get('question', '')} {market.get('description', '')} "
        f"{base.event_title(market)}"
    )
    defaults = {
        "monetary-policy": {"rates", "us-dollar", "gold", "silver", "semiconductors"},
        "geopolitics-security": {"gold", "us-dollar"},
        "technology-ai": {"semiconductors"},
        "us-policy-elections": {"rates", "us-dollar"},
        "trade-industrial-policy": {"us-dollar"},
    }
    assets: set[str] = set(defaults.get(category_id, set()))

    for token, asset in (
        ("gold", "gold"), ("silver", "silver"), ("copper", "copper"),
    ):
        if token in text:
            assets.add(asset)
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

    if any(term in text for term in (
        "semiconductor", "chip", "nvidia", "amd", "intel", "tsmc", "asml",
        "taiwan", "data center", "data centre", "artificial intelligence",
    )):
        assets.add("semiconductors")
    if any(term in text for term in ("taiwan", "south china sea", "china export control")):
        assets.add("rare-earths")
    if "debt ceiling" in text or "government shutdown" in text:
        assets.add("gold")
    return sorted(assets)


def market_record(
    raw: dict[str, Any], category: dict[str, Any], relevance_score: int,
    previous: dict[str, Any] | None, collected_at: str, history_days: int,
) -> dict[str, Any] | None:
    record = _ORIGINAL_MARKET_RECORD(
        raw, category, relevance_score, previous, collected_at, history_days
    )
    if record is not None:
        record["resolutionSource"] = resolution_source(raw)
        record["assets"] = asset_map(category, raw)
        spread = computed_spread(raw)
        if spread is not None:
            record["spread"] = round(spread, 6)
    return record


def event_family(record: dict[str, Any]) -> str:
    """Stable family key used to prevent one multi-outcome event dominating."""
    return base.normalized(
        record.get("sourceUrl")
        or record.get("eventTitle")
        or record.get("slug")
        or record.get("id")
    )


def balanced_selection(
    ranked: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    reserve_per_category: int = 3,
    max_per_category: int = 16,
    max_per_event: int = 4,
) -> list[dict[str, Any]]:
    """Preserve quality rank while reserving category breadth and event diversity."""
    limit = int(registry.get("discovery", {}).get("maxMarkets", 48))
    category_order = [
        str(category.get("id") or "")
        for category in registry.get("categories", [])
        if category.get("id")
    ]
    buckets = {
        category_id: [
            item for item in ranked if str(item.get("categoryId") or "") == category_id
        ]
        for category_id in category_order
    }
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    category_counts: dict[str, int] = {}
    event_counts: dict[str, int] = {}

    def add(item: dict[str, Any]) -> bool:
        item_id = str(item.get("id") or "")
        category_id = str(item.get("categoryId") or "")
        family = event_family(item)
        if not item_id or item_id in selected_ids:
            return False
        if category_counts.get(category_id, 0) >= max_per_category:
            return False
        if event_counts.get(family, 0) >= max_per_event:
            return False
        selected.append(item)
        selected_ids.add(item_id)
        category_counts[category_id] = category_counts.get(category_id, 0) + 1
        event_counts[family] = event_counts.get(family, 0) + 1
        return True

    # Round-robin reserves keep every qualifying category visible without
    # promoting any market that failed the normal quality/liquidity filters.
    for round_index in range(max(0, reserve_per_category)):
        for category_id in category_order:
            bucket = buckets.get(category_id, [])
            accepted = category_counts.get(category_id, 0)
            if accepted > round_index:
                continue
            for item in bucket:
                if add(item):
                    break
            if len(selected) >= limit:
                return selected

    for item in ranked:
        add(item)
        if len(selected) >= limit:
            break
    return selected


def build_dataset(registry: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    """Collect a larger qualified pool, then apply balanced final selection."""
    expanded_registry = copy.deepcopy(registry)
    discovery = expanded_registry.setdefault("discovery", {})
    final_limit = int(registry.get("discovery", {}).get("maxMarkets", 48))
    discovery["maxMarkets"] = max(final_limit * 4, final_limit + 96)

    generated = _ORIGINAL_BUILD_DATASET(expanded_registry, previous)
    if generated.get("collection", {}).get("error"):
        return generated

    markets = balanced_selection(generated.get("markets", []), registry)
    generated["markets"] = markets
    generated["collection"]["selectedMarketCount"] = len(markets)

    category_counts: dict[str, int] = {}
    for item in markets:
        category_id = str(item.get("categoryId") or "")
        category_counts[category_id] = category_counts.get(category_id, 0) + 1
    generated["categories"] = [
        {
            "id": category["id"],
            "name": category["name"],
            "count": category_counts.get(category["id"], 0),
        }
        for category in registry.get("categories", [])
    ]

    discovery_rules = registry.get("discovery", {})
    shocks = [
        {
            "marketId": item["id"],
            "question": item["question"],
            "probabilityPercent": item["probabilityPercent"],
            "change24hPoints": item["change24hPoints"],
            "qualityGrade": item["qualityGrade"],
            "qualityScore": item["qualityScore"],
            "assets": item["assets"],
            "sourceUrl": item["sourceUrl"],
        }
        for item in markets
        if item.get("change24hPoints") is not None
        and abs(float(item["change24hPoints"]))
        >= float(discovery_rules.get("shockPoints24h", 5))
        and int(item["qualityScore"])
        >= int(discovery_rules.get("shockMinQualityScore", 65))
    ]
    shocks.sort(key=lambda item: abs(float(item["change24hPoints"])), reverse=True)
    generated["shocks"] = shocks[:12]

    generated["methodology"]["selection"] = (
        "Markets first pass the normal relevance, liquidity, volume and quality filters. "
        "Final selection then reserves up to three markets per qualifying category, caps "
        "any category at 16 markets and any event family at four outcomes before filling "
        "remaining slots in quality rank order."
    )
    if generated.get("sourceStatus"):
        generated["sourceStatus"][0]["detail"] = (
            f"{len(markets)} balanced relevant markets retained from "
            f"{generated['collection'].get('rawMarketCount', 0)} active markets."
        )
    validate_output(generated)
    return generated


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
        if provider.get(key):
            yield str(provider[key])
    for market in data.get("markets", []):
        if market.get("sourceUrl"):
            yield str(market["sourceUrl"])
    for source in data.get("sourceStatus", []):
        if source.get("url"):
            yield str(source["url"])


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
        dates = [str(point.get("date") or "") for point in history if isinstance(point, dict)]
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
base.build_dataset = build_dataset
base.validate_output = validate_output


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
