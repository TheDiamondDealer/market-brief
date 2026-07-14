#!/usr/bin/env python3
"""Collect COT data from the CFTC public reporting API.

Only explicitly recognised, recent benchmark contracts are accepted. Similar
micro, mini, index, basis, cross-rate and ultra contracts are rejected rather
than silently substituted. Missing or stale markets remain unavailable.
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

ZIP_FALLBACK = collector.fetch_cot
RECENT_CUTOFF_DAYS = 21

DATASETS = {
    "disagg": "72hh-3qpy",
    "tff": "gpe5-46if",
}

MARKETS = {
    "gold": {
        "label": "Gold", "report": "disagg", "query": "GOLD",
        "must": ["GOLD", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "silver": {
        "label": "Silver", "report": "disagg", "query": "SILVER",
        "must": ["SILVER", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "copper": {
        "label": "Copper", "report": "disagg", "query": "COPPER",
        "must": ["COPPER", "COMMODITY EXCHANGE"], "avoid": ["MICRO", "MINI"],
    },
    "oil-wti": {
        "label": "WTI crude oil", "report": "disagg", "query": "CRUDE OIL, LIGHT SWEET",
        "must": ["CRUDE OIL", "LIGHT SWEET"],
        "avoid": ["E-MINI", "MICRO", "FINANCIAL", "INDEX"],
    },
    "oil-brent": {
        "label": "Brent crude oil", "report": "disagg", "query": "BRENT",
        "must": ["BRENT"], "avoid": ["E-MINI", "MICRO", "INDEX", "BASIS", "SPREAD"],
    },
    "gas-us": {
        "label": "US Henry Hub natural gas", "report": "disagg", "query": "HENRY HUB",
        "must": ["HENRY HUB"], "avoid": ["E-MINI", "MICRO", "INDEX", "BASIS", "SWAP"],
    },
    "gas-uk": {
        "label": "UK NBP natural gas", "report": "disagg", "query": "NBP",
        "must": ["NBP"], "avoid": ["E-MINI", "MICRO", "INDEX", "BASIS", "SWAP"],
    },
    "yen": {
        "label": "Japanese yen", "report": "tff", "query": "JAPANESE YEN",
        "must": ["JAPANESE YEN", "CHICAGO MERCANTILE"], "avoid": ["EURO FX", "CROSS"],
    },
    "us10y-futures": {
        "label": "US 10-year Treasury futures", "report": "tff", "query": "10-YEAR",
        "must": ["10-YEAR", "TREASURY", "CHICAGO BOARD OF TRADE"], "avoid": ["ULTRA"],
    },
    "usd-index": {
        "label": "US Dollar Index", "report": "tff", "query": "USD INDEX",
        "must": ["USD INDEX", "ICE FUTURES U.S."], "avoid": [],
    },
}


def api_rows(dataset: str, search_text: str) -> list[dict[str, Any]]:
    start_date = (datetime.now(timezone.utc) - timedelta(days=366 * 6)).date().isoformat()
    escaped_search = search_text.replace("'", "''")
    where = (
        f"report_date_as_yyyy_mm_dd >= '{start_date}T00:00:00.000' "
        f"AND market_and_exchange_names like '%{escaped_search}%'"
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


def recognised_contract(name: str, config: dict[str, Any]) -> bool:
    upper = name.upper()
    if any(token.upper() in upper for token in config.get("avoid", [])):
        return False
    return all(token.upper() in upper for token in config.get("must", []))


def position_keys(report: str) -> tuple[str, str]:
    if report == "disagg":
        return "m_money_positions_long_all", "m_money_positions_short_all"
    return "lev_money_positions_long", "lev_money_positions_short"


def choose_candidate(rows: list[dict[str, Any]], config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]] | None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        name = str(row.get("market_and_exchange_names", "")).strip()
        if name and report_date(row) and recognised_contract(name, config):
            grouped[name].append(row)
    if not grouped:
        return None

    long_key, short_key = position_keys(config["report"])
    ranked = []
    for name, values in grouped.items():
        latest = max(report_date(row) or "" for row in values)
        latest_rows = [row for row in values if report_date(row) == latest]
        usable = any(
            (collector.safe_float(row.get(long_key)) or 0) != 0 or
            (collector.safe_float(row.get(short_key)) or 0) != 0
            for row in latest_rows
        )
        # Prefer the largest current open-interest contract where several
        # recognised versions share the same latest date.
        latest_open_interest = max((collector.safe_float(row.get("open_interest_all")) or 0) for row in latest_rows)
        ranked.append((latest, usable, latest_open_interest, name, values))
    ranked.sort(reverse=True)
    for _, usable, _, name, values in ranked:
        if usable:
            return name, values
    return None


def candidate_diagnostic(rows: list[dict[str, Any]]) -> str:
    grouped: dict[str, str] = {}
    for row in rows:
        name = str(row.get("market_and_exchange_names", "")).strip()
        date = report_date(row)
        if name and date and date > grouped.get(name, ""):
            grouped[name] = date
    candidates = sorted(((date, name) for name, date in grouped.items()), reverse=True)[:4]
    return f"nearest candidates={candidates}"


def observations_for(config: dict[str, Any]) -> list[collector.Observation]:
    rows = api_rows(DATASETS[config["report"]], config["query"])
    selected = choose_candidate(rows, config)
    if not selected:
        raise ValueError("no recognised current benchmark contract; " + candidate_diagnostic(rows))
    market_name, values = selected
    output: list[collector.Observation] = []
    long_key, short_key = position_keys(config["report"])
    category = "Managed money" if config["report"] == "disagg" else "Leveraged funds"
    for row in values:
        date = report_date(row)
        if not date:
            continue
        long_value = collector.safe_float(row.get(long_key))
        short_value = collector.safe_float(row.get(short_key))
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
    if not output:
        raise ValueError("recognised contract has no usable positioning fields")
    return output


def is_recent(report_date_value: str) -> bool:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RECENT_CUTOFF_DAYS)).date().isoformat()
    return bool(report_date_value and report_date_value >= cutoff)


def fetch_cot_api() -> tuple[list[dict[str, Any]], list[str]]:
    summaries: list[dict[str, Any]] = []
    errors: list[str] = []
    for market_id, config in MARKETS.items():
        try:
            observations = observations_for(config)
            summary = collector.summarise_market(market_id, config["label"], observations)
            if not summary:
                errors.append(f"{market_id}: no usable rows")
                continue
            if not is_recent(str(summary.get("reportDate", ""))):
                errors.append(f"{market_id}: latest recognised benchmark contract is stale ({summary.get('reportDate')}); excluded")
                continue
            summary["dataMethod"] = "CFTC public reporting API"
            summaries.append(summary)
        except Exception as exc:
            errors.append(f"{market_id}: {exc}")

    # Keep the legacy fallback only for non-energy IDs whose contract identity
    # remains unambiguous and whose report is current.
    fallback, fallback_errors = ZIP_FALLBACK()
    legacy_id_map = {"yen": "yen", "us10y-futures": "us10y-futures", "usd-index": "usd-index"}
    existing = {row["id"] for row in summaries}
    for row in fallback:
        mapped_id = legacy_id_map.get(row.get("id"))
        if mapped_id and mapped_id not in existing and is_recent(str(row.get("reportDate", ""))):
            row["id"] = mapped_id
            row["dataMethod"] = "CFTC annual ZIP fallback"
            summaries.append(row)
    errors.extend(f"ZIP fallback: {error}" for error in fallback_errors[:2])
    return summaries, errors


collector.fetch_cot = fetch_cot_api

if __name__ == "__main__":
    sys.exit(collector.main())
