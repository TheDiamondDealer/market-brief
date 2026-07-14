#!/usr/bin/env python3
"""Collect COT data from the CFTC public reporting API.

The Socrata datasets are the CFTC's official public reporting environment. This
wrapper selects the most recently reported contract candidate first, then uses
contract-name scoring to prefer the main contract over micro, mini, cross-rate,
ICE or ultra variants. The annual ZIP collector remains the fallback.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import update_free_data as collector
import update_free_data_strict as strict_collector  # applies strict fallback config

DATASETS = {
    "disagg": "72hh-3qpy",
    "tff": "gpe5-46if",
}

MARKETS = {
    "gold": {
        "label": "Gold", "report": "disagg", "query": "GOLD",
        "prefer": ["GOLD -", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "silver": {
        "label": "Silver", "report": "disagg", "query": "SILVER",
        "prefer": ["SILVER -", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "copper": {
        "label": "Copper", "report": "disagg", "query": "COPPER",
        "prefer": ["COPPER", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "oil": {
        "label": "WTI crude oil", "report": "disagg", "query": "CRUDE OIL",
        "prefer": ["LIGHT SWEET", "NEW YORK MERCANTILE"], "avoid": ["E-MINI", "MICRO", "ICE FUTURES"],
    },
    "natural-gas": {
        "label": "Natural gas", "report": "disagg", "query": "NATURAL GAS",
        "prefer": ["NATURAL GAS -", "NEW YORK MERCANTILE"], "avoid": ["E-MINI", "MICRO"],
    },
    "yen": {
        "label": "Japanese yen", "report": "tff", "query": "JAPANESE YEN",
        "prefer": ["JAPANESE YEN -", "CHICAGO MERCANTILE"], "avoid": ["EURO FX", "CROSS"],
    },
    "us10y-futures": {
        "label": "US 10-year Treasury futures", "report": "tff", "query": "10-YEAR",
        "prefer": ["TREASURY NOTES", "CHICAGO BOARD OF TRADE"], "avoid": ["ULTRA"],
    },
    "usd-index": {
        "label": "US Dollar Index", "report": "tff", "query": "USD INDEX",
        "prefer": ["USD INDEX", "ICE FUTURES U.S."], "avoid": [],
    },
}


def api_rows(dataset: str, search_text: str) -> list[dict[str, Any]]:
    start_date = (datetime.now(timezone.utc) - timedelta(days=366 * 6)).date().isoformat()
    where = (
        f"report_date_as_yyyy_mm_dd >= '{start_date}T00:00:00.000' "
        f"AND market_and_exchange_names like '%{search_text.replace("'", "''")}%'"
    )
    params = urllib.parse.urlencode({
        "$limit": "5000",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$where": where,
    })
    url = f"https://publicreporting.cftc.gov/resource/{dataset}.json?{params}"
    payload = collector.fetch_bytes(url, timeout=90)
    rows = json.loads(payload.decode("utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected API response for {search_text}")
    return rows


def report_date(row: dict[str, Any]) -> str | None:
    for key in ("report_date_as_yyyy_mm_dd", "as_of_date_in_form_yyyy_mm_dd", "as_of_date_form_yyyy_mm_dd"):
        value = row.get(key)
        if value:
            return str(value)[:10]
    return None


def candidate_score(name: str, config: dict[str, Any]) -> int:
    upper = name.upper()
    score = 0
    for token in config.get("prefer", []):
        token_upper = token.upper()
        if token_upper in upper:
            score += 8
        if upper.startswith(token_upper):
            score += 6
    for token in config.get("avoid", []):
        if token.upper() in upper:
            score -= 25
    return score


def choose_candidate(rows: list[dict[str, Any]], config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]] | None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        name = str(row.get("market_and_exchange_names", "")).strip()
        if name and report_date(row):
            grouped[name].append(row)
    if not grouped:
        return None

    ranked = []
    for name, values in grouped.items():
        latest = max(report_date(row) or "" for row in values)
        ranked.append((latest, candidate_score(name, config), name, values))
    ranked.sort(reverse=True)

    newest_date = ranked[0][0]
    current_candidates = [entry for entry in ranked if entry[0] == newest_date]
    current_candidates.sort(key=lambda entry: entry[1], reverse=True)
    _, _, name, values = current_candidates[0]
    return name, values


def observations_for(market_id: str, config: dict[str, Any]) -> list[collector.Observation]:
    rows = api_rows(DATASETS[config["report"]], config["query"])
    selected = choose_candidate(rows, config)
    if not selected:
        return []
    market_name, values = selected
    output: list[collector.Observation] = []
    for row in values:
        date = report_date(row)
        if not date:
            continue
        if config["report"] == "disagg":
            long_value = collector.safe_float(row.get("m_money_positions_long_all"))
            short_value = collector.safe_float(row.get("m_money_positions_short_all"))
            category = "Managed money"
        else:
            long_value = collector.safe_float(row.get("lev_money_positions_long_all"))
            short_value = collector.safe_float(row.get("lev_money_positions_short_all"))
            category = "Leveraged funds"
        if long_value is None or short_value is None:
            continue
        output.append(collector.Observation(
            date=date,
            long=long_value,
            short=short_value,
            open_interest=collector.safe_float(row.get("open_interest_all")),
            market_name=market_name,
            category=category,
        ))
    return output


def fetch_cot_api() -> tuple[list[dict[str, Any]], list[str]]:
    summaries: list[dict[str, Any]] = []
    errors: list[str] = []
    for market_id, config in MARKETS.items():
        try:
            observations = observations_for(market_id, config)
            summary = collector.summarise_market(market_id, config["label"], observations)
            if summary:
                summary["dataMethod"] = "CFTC public reporting API"
                summaries.append(summary)
            else:
                errors.append(f"{market_id}: no usable rows")
        except Exception as exc:
            errors.append(f"{market_id}: {exc}")

    if len(summaries) < 5:
        fallback, fallback_errors = strict_collector.collector.fetch_cot()
        existing = {row["id"] for row in summaries}
        summaries.extend(row for row in fallback if row["id"] not in existing)
        errors.extend(f"ZIP fallback: {error}" for error in fallback_errors[:3])
    return summaries, errors


collector.fetch_cot = fetch_cot_api

if __name__ == "__main__":
    sys.exit(collector.main())
