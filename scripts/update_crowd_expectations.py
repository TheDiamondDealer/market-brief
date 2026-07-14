#!/usr/bin/env python3
"""Collect read-only crowd-implied event probabilities from Polymarket.

The collector intentionally uses only public market-data endpoints. It contains
no wallet, authentication, signing, deposit or order-placement functionality.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts" / "crowd_expectations_registry.json"
OUTPUT_PATH = ROOT / "site" / "data" / "crowd-expectations.json"
USER_AGENT = os.environ.get(
    "CROWD_EXPECTATIONS_USER_AGENT",
    "MarketBriefResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)",
)
TRADING_MARKERS = (
    "/order",
    "post_order",
    "create_order",
    "private_key",
    "signature",
    "api_secret",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def request_json(url: str, timeout: int = 45) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            raise ValueError(f"Unexpected content type: {content_type}")
        return json.loads(response.read().decode("utf-8-sig", errors="replace"))


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def json_array(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def source_url(market: dict[str, Any]) -> str:
    events = market.get("events") or []
    if events and isinstance(events[0], dict) and events[0].get("slug"):
        return f"https://polymarket.com/event/{events[0]['slug']}"
    slug = market.get("slug")
    return f"https://polymarket.com/market/{slug}" if slug else "https://polymarket.com/"


def event_title(market: dict[str, Any]) -> str:
    events = market.get("events") or []
    if events and isinstance(events[0], dict):
        return str(events[0].get("title") or "")
    return ""


def binary_yes_probability(market: dict[str, Any]) -> tuple[float | None, int | None]:
    outcomes = [normalized(item) for item in json_array(market.get("outcomes"))]
    prices = json_array(market.get("outcomePrices"))
    if len(outcomes) != len(prices) or "yes" not in outcomes or "no" not in outcomes:
        return None, None
    yes_index = outcomes.index("yes")
    return number(prices[yes_index]), yes_index


def classify_market(market: dict[str, Any], registry: dict[str, Any]) -> tuple[dict[str, Any] | None, int]:
    text = normalized(
        " ".join(
            [
                str(market.get("question") or ""),
                str(market.get("description") or ""),
                str(market.get("category") or ""),
                event_title(market),
            ]
        )
    )
    if not text:
        return None, 0
    if market.get("sportsMarketType") or any(term in text for term in registry.get("excludeTerms", [])):
        return None, 0

    best: dict[str, Any] | None = None
    best_score = 0
    for category in registry.get("categories", []):
        matches = [term for term in category.get("keywords", []) if term in text]
        score = len(matches)
        if score > best_score:
            best = category
            best_score = score
    return best, best_score


def liquidity_points(value: float) -> int:
    if value >= 250_000:
        return 25
    if value >= 100_000:
        return 22
    if value >= 25_000:
        return 18
    if value >= 10_000:
        return 14
    if value >= 2_500:
        return 9
    return 3


def volume_points(value: float) -> int:
    if value >= 500_000:
        return 20
    if value >= 100_000:
        return 17
    if value >= 25_000:
        return 13
    if value >= 5_000:
        return 9
    if value >= 500:
        return 5
    return 1


def spread_points(value: float | None) -> int:
    if value is None:
        return 3
    if value <= 0.01:
        return 25
    if value <= 0.025:
        return 22
    if value <= 0.05:
        return 17
    if value <= 0.10:
        return 10
    return 2


def quality_score(market: dict[str, Any], relevance_score: int) -> tuple[int, str, list[str]]:
    liquidity = number(market.get("liquidityNum") or market.get("liquidity")) or 0
    volume24h = number(market.get("volume24hr")) or 0
    spread = number(market.get("spread"))
    resolution = bool(str(market.get("resolutionSource") or "").strip())
    description = len(str(market.get("description") or "").strip()) >= 80
    accepting = bool(market.get("acceptingOrders", market.get("active", False)))
    end_date = market.get("endDate")
    time_points = 0
    if end_date:
        try:
            remaining = datetime.fromisoformat(str(end_date).replace("Z", "+00:00")) - datetime.now(timezone.utc)
            time_points = 5 if remaining >= timedelta(days=2) else 2 if remaining.total_seconds() > 0 else 0
        except ValueError:
            time_points = 1

    score = (
        liquidity_points(liquidity)
        + volume_points(volume24h)
        + spread_points(spread)
        + (8 if resolution else 2)
        + (5 if description else 1)
        + (5 if accepting else 0)
        + time_points
        + min(7, relevance_score * 2)
    )
    score = max(0, min(100, score))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    reasons = [
        f"Liquidity ${liquidity:,.0f}",
        f"24h volume ${volume24h:,.0f}",
        f"Spread {spread * 100:.2f} points" if spread is not None else "Spread unavailable",
        "Resolution source supplied" if resolution else "Resolution source not supplied",
    ]
    return score, grade, reasons


def selected_probability(market: dict[str, Any], outcome_probability: float | None) -> tuple[float | None, str]:
    bid = number(market.get("bestBid"))
    ask = number(market.get("bestAsk"))
    spread = number(market.get("spread"))
    if bid is not None and ask is not None and 0 <= bid <= ask <= 1 and (spread is None or spread <= 0.10):
        return (bid + ask) / 2, "bid-ask midpoint"
    last = number(market.get("lastTradePrice"))
    if last is not None and 0 <= last <= 1:
        return last, "last trade"
    if outcome_probability is not None and 0 <= outcome_probability <= 1:
        return outcome_probability, "Gamma outcome price"
    return None, "unavailable"


def asset_map(category: dict[str, Any], market: dict[str, Any]) -> list[str]:
    assets = list(category.get("assets", []))
    text = normalized(f"{market.get('question', '')} {market.get('description', '')}")
    additions = {
        "gold": ("gold",),
        "silver": ("silver",),
        "copper": ("copper",),
        "brent": ("brent", "opec", "middle east", "strait of hormuz"),
        "wti": ("wti", "crude oil", "opec"),
        "gas-us": ("henry hub", "us natural gas"),
        "gas-uk": ("lng", "european gas", "uk gas"),
        "semiconductors": ("semiconductor", "chip", "nvidia", "amd", "intel", "tsmc", "asml"),
        "rare-earths": ("rare earth", "critical mineral"),
        "rates": ("fed", "interest rate", "inflation", "cpi", "pce", "recession"),
        "us-dollar": ("fed", "tariff", "election", "sanction", "debt ceiling"),
    }
    for asset, terms in additions.items():
        if any(term in text for term in terms):
            assets.append(asset)
    return sorted(set(assets))


def day_snapshot(previous: dict[str, Any] | None, timestamp: str, probability: float) -> list[dict[str, Any]]:
    today = timestamp[:10]
    history = []
    if previous:
        history = [item for item in previous.get("history", []) if isinstance(item, dict)]
    snapshot = {"date": today, "observedAt": timestamp, "probability": round(probability, 6)}
    if history and history[-1].get("date") == today:
        history[-1] = snapshot
    else:
        history.append(snapshot)
    return history


def market_record(
    raw: dict[str, Any],
    category: dict[str, Any],
    relevance_score: int,
    previous: dict[str, Any] | None,
    collected_at: str,
    history_days: int,
) -> dict[str, Any] | None:
    outcome_probability, _ = binary_yes_probability(raw)
    probability, probability_source = selected_probability(raw, outcome_probability)
    if probability is None:
        return None

    score, grade, reasons = quality_score(raw, relevance_score)
    market_id = str(raw.get("id") or raw.get("conditionId") or raw.get("slug") or "")
    if not market_id:
        return None
    history = day_snapshot(previous, collected_at, probability)
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=history_days)).isoformat()
    history = [item for item in history if str(item.get("date", "")) >= cutoff][-history_days:]

    delta24 = number(raw.get("oneDayPriceChange"))
    delta7d = number(raw.get("oneWeekPriceChange"))
    return {
        "id": market_id,
        "slug": raw.get("slug") or None,
        "question": str(raw.get("question") or "").strip(),
        "eventTitle": event_title(raw) or None,
        "categoryId": category["id"],
        "category": category["name"],
        "probability": round(probability, 6),
        "probabilityPercent": round(probability * 100, 2),
        "probabilitySource": probability_source,
        "change24hPoints": round(delta24 * 100, 2) if delta24 is not None else None,
        "change7dPoints": round(delta7d * 100, 2) if delta7d is not None else None,
        "bestBid": number(raw.get("bestBid")),
        "bestAsk": number(raw.get("bestAsk")),
        "spread": number(raw.get("spread")),
        "liquidity": round(number(raw.get("liquidityNum") or raw.get("liquidity")) or 0, 2),
        "volume24h": round(number(raw.get("volume24hr")) or 0, 2),
        "volumeTotal": round(number(raw.get("volumeNum") or raw.get("volume")) or 0, 2),
        "openInterest": round(number((raw.get("events") or [{}])[0].get("openInterest")) or 0, 2),
        "qualityScore": score,
        "qualityGrade": grade,
        "qualityReasons": reasons,
        "relevanceScore": relevance_score,
        "assets": asset_map(category, raw),
        "resolutionSource": str(raw.get("resolutionSource") or "").strip() or None,
        "description": str(raw.get("description") or "").strip()[:1800],
        "endDate": raw.get("endDate") or None,
        "updatedAt": raw.get("updatedAt") or collected_at,
        "collectedAt": collected_at,
        "sourceUrl": source_url(raw),
        "restricted": bool(raw.get("restricted")),
        "acceptingOrders": bool(raw.get("acceptingOrders", False)),
        "readOnly": True,
        "history": history,
    }


def discover_markets(registry: dict[str, Any]) -> list[dict[str, Any]]:
    provider = registry["provider"]
    discovery = registry["discovery"]
    endpoint = provider["marketEndpoint"]
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(int(discovery.get("maxPages", 10))):
        params = {
            "active": "true",
            "closed": "false",
            "limit": str(discovery.get("pageSize", 100)),
            "offset": str(page * int(discovery.get("pageSize", 100))),
            "order": "volume24hr",
            "ascending": "false",
        }
        payload = request_json(endpoint + "?" + urllib.parse.urlencode(params))
        if not isinstance(payload, list):
            raise ValueError("Polymarket markets endpoint did not return a list")
        if not payload:
            break
        for item in payload:
            if not isinstance(item, dict):
                continue
            market_id = str(item.get("id") or item.get("conditionId") or item.get("slug") or "")
            if market_id and market_id not in seen:
                seen.add(market_id)
                records.append(item)
        if len(payload) < int(discovery.get("pageSize", 100)):
            break
    return records


def collection_status(markets: list[dict[str, Any]], error: str | None = None) -> str:
    if markets:
        return "partial" if error else "current"
    return "failed" if error else "unavailable"


def build_dataset(registry: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    collected_at = utc_now()
    discovery = registry["discovery"]
    previous_by_id = {
        str(item.get("id")): item
        for item in previous.get("markets", [])
        if isinstance(item, dict) and item.get("id")
    }
    error: str | None = None
    raw_count = 0
    try:
        raw_markets = discover_markets(registry)
        raw_count = len(raw_markets)
        ranked: list[dict[str, Any]] = []
        for raw in raw_markets:
            category, relevance = classify_market(raw, registry)
            if not category:
                continue
            record = market_record(
                raw,
                category,
                relevance,
                previous_by_id.get(str(raw.get("id") or raw.get("conditionId") or raw.get("slug") or "")),
                collected_at,
                int(discovery.get("historyDays", 90)),
            )
            if not record:
                continue
            if record["liquidity"] < float(discovery.get("minLiquidity", 0)):
                continue
            if record["volume24h"] < float(discovery.get("minVolume24h", 0)):
                continue
            if record["qualityScore"] < int(discovery.get("minQualityScore", 0)):
                continue
            ranked.append(record)
        ranked.sort(
            key=lambda item: (
                item["qualityScore"],
                item["relevanceScore"],
                math.log10(item["volume24h"] + 10),
                math.log10(item["liquidity"] + 10),
            ),
            reverse=True,
        )
        markets = ranked[: int(discovery.get("maxMarkets", 48))]
        if not markets:
            raise ValueError(f"No relevant markets passed filters from {raw_count} active markets")
    except Exception as exc:
        error = str(exc)[:600]
        prior_markets = [item for item in previous.get("markets", []) if isinstance(item, dict)]
        markets = []
        for item in prior_markets:
            retained = dict(item)
            retained["status"] = "stale"
            retained["readOnly"] = True
            markets.append(retained)

    for item in markets:
        item.setdefault("status", "current" if not error else "stale")

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
        and abs(float(item["change24hPoints"])) >= float(discovery.get("shockPoints24h", 5))
        and int(item["qualityScore"]) >= int(discovery.get("shockMinQualityScore", 65))
    ]
    shocks.sort(key=lambda item: abs(float(item["change24hPoints"])), reverse=True)

    category_counts: dict[str, int] = {}
    for item in markets:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

    status = collection_status(markets, error)
    generated = {
        "schemaVersion": 1,
        "generatedAtUtc": collected_at,
        "provider": registry["provider"],
        "collection": {
            "status": status,
            "rawMarketCount": raw_count,
            "selectedMarketCount": len(markets),
            "lastSuccessfulAt": collected_at if markets and not error else previous.get("collection", {}).get("lastSuccessfulAt"),
            "error": error,
        },
        "categories": [
            {"id": category["id"], "name": category["name"], "count": category_counts.get(category["name"], 0)}
            for category in registry.get("categories", [])
        ],
        "markets": markets,
        "shocks": shocks[:12],
        "methodology": {
            "interpretation": "Prices are crowd-implied event probabilities, not forecasts, truth estimates or trade recommendations.",
            "price": "Use the YES bid-ask midpoint when available and the spread is no wider than 10 probability points; otherwise use the last trade, then the Gamma outcome price.",
            "quality": "Quality combines liquidity, 24-hour volume, spread, resolution-source clarity, market activity, time remaining and relevance.",
            "history": "One verified snapshot per UTC day is retained for up to 90 days.",
            "selection": "Sports, entertainment, celebrity and standalone cryptocurrency-price markets are excluded. Only market-relevant macro, policy, geopolitical, energy, commodity and technology questions are retained.",
            "jurisdiction": "Read-only public market data. No wallet, authentication, deposits or order endpoints are implemented. Australia is close-only for Polymarket order placement.",
        },
        "sourceStatus": [
            {
                "id": "polymarket-public-market-data",
                "source": "Polymarket public market data",
                "status": status,
                "observationDate": max((str(item.get("updatedAt") or "") for item in markets), default=None),
                "lastSuccessfulAt": None,
                "expectedCadence": "Every six hours",
                "detail": f"{len(markets)} relevant markets retained from {raw_count} active markets.",
                "error": error,
                "url": registry["provider"]["documentationUrl"],
            }
        ],
    }
    generated["sourceStatus"][0]["lastSuccessfulAt"] = generated["collection"]["lastSuccessfulAt"]
    validate_output(generated)
    return generated


def validate_output(data: dict[str, Any]) -> None:
    if data.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    provider = data.get("provider", {})
    if provider.get("id") != "polymarket" or provider.get("readOnly") is not True:
        raise ValueError("Provider must remain Polymarket read-only")
    markets = data.get("markets")
    if not isinstance(markets, list):
        raise ValueError("markets must be a list")
    ids = [str(item.get("id") or "") for item in markets]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate crowd market ids")
    for item in markets:
        if item.get("readOnly") is not True:
            raise ValueError(f"Market is not read-only: {item.get('id')}")
        probability = number(item.get("probability"))
        if probability is None or not 0 <= probability <= 1:
            raise ValueError(f"Invalid probability: {item.get('id')}")
        history = item.get("history", [])
        dates = [str(point.get("date") or "") for point in history if isinstance(point, dict)]
        if dates != sorted(dates) or len(dates) != len(set(dates)):
            raise ValueError(f"Invalid history dates: {item.get('id')}")
        if len(history) > 90:
            raise ValueError(f"History exceeds 90 days: {item.get('id')}")
    rendered = json.dumps(data, ensure_ascii=False).lower()
    if any(marker in rendered for marker in TRADING_MARKERS):
        raise ValueError("Generated crowd data contains a prohibited trading marker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    registry = load_json(args.registry, {})
    if not registry:
        print(f"Unable to load registry: {args.registry}", file=sys.stderr)
        return 1
    previous = load_json(args.output, {})
    dataset = build_dataset(registry, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Crowd expectations status={dataset['collection']['status']}; "
        f"selected={dataset['collection']['selectedMarketCount']}; "
        f"shocks={len(dataset['shocks'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
