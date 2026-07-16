#!/usr/bin/env python3
"""Collect COT data using the exact, versioned CFTC contract registry.

A row is accepted only when its official CFTC contract-market code, complete
market/exchange name, report family and exchange all match the registry. Similar
contracts are never ranked or substituted. Registry entries without an approved
identity remain explicitly unavailable.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any

import update_free_data as collector
from cot_contracts import (
    contract_accepts_row,
    contract_metadata,
    generated_row_is_verified,
    load_registry,
    row_contract_code,
    row_market_name,
    unavailable_contracts,
    verified_contracts,
)

REGISTRY = load_registry()


def api_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    start_date = (datetime.now(timezone.utc) - timedelta(days=366 * 6)).date().isoformat()
    code = contract["cftcContractCode"].replace("'", "''")
    where = (
        f"report_date_as_yyyy_mm_dd >= '{start_date}T00:00:00.000' "
        f"AND cftc_contract_market_code = '{code}'"
    )
    params = urllib.parse.urlencode({
        "$limit": "5000",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$where": where,
    })
    url = f"https://publicreporting.cftc.gov/resource/{contract['datasetId']}.json?{params}"
    payload = collector.fetch_bytes(url, timeout=90)
    rows = json.loads(payload.decode("utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected API response for {contract['id']}")
    return rows


def report_date(row: dict[str, Any]) -> str | None:
    for key in ("report_date_as_yyyy_mm_dd", "as_of_date_in_form_yyyy_mm_dd", "as_of_date_form_yyyy_mm_dd"):
        value = row.get(key)
        if value:
            return str(value)[:10]
    return None


def position_keys(report_type: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if report_type == "disaggregated":
        return ("m_money_positions_long_all",), ("m_money_positions_short_all",)
    return ("lev_money_positions_long", "lev_money_positions_long_all"), ("lev_money_positions_short", "lev_money_positions_short_all")


def candidate_diagnostic(rows: list[dict[str, Any]]) -> str:
    candidates: dict[tuple[str, str], str] = {}
    for row in rows:
        date = report_date(row)
        code = row_contract_code(row)
        name = row_market_name(row)
        if date and (code or name):
            candidates[(code, name)] = max(date, candidates.get((code, name), ""))
    nearest = sorted(((date, code, name) for (code, name), date in candidates.items()), reverse=True)[:4]
    return f"returned identities={nearest}"


def observations_from_rows(contract: dict[str, Any], rows: list[dict[str, Any]]) -> list[collector.Observation]:
    accepted = [row for row in rows if report_date(row) and contract_accepts_row(contract, row)]
    if not accepted:
        raise ValueError("no exact registered contract rows; " + candidate_diagnostic(rows))

    long_keys, short_keys = position_keys(contract["reportType"])
    output: list[collector.Observation] = []
    for row in accepted:
        date = report_date(row)
        long_value = collector.row_value(row, long_keys)
        short_value = collector.row_value(row, short_keys)
        if not date or long_value is None or short_value is None:
            continue
        output.append(collector.Observation(
            date=date,
            long=long_value,
            short=short_value,
            open_interest=collector.safe_float(row.get("open_interest_all")),
            market_name=row_market_name(row),
            category=contract["category"],
        ))
    if not output:
        raise ValueError("exact registered contract has no usable positioning fields")
    return output


def observations_for(contract: dict[str, Any]) -> list[collector.Observation]:
    return observations_from_rows(contract, api_rows(contract))


def is_recent(report_date_value: str, maximum_age_days: int, *, as_of: datetime | None = None) -> bool:
    now = as_of or datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=maximum_age_days)).date().isoformat()
    return bool(report_date_value and report_date_value >= cutoff)


def fetch_registered_contract(contract: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        observations = observations_for(contract)
        summary = collector.summarise_market(contract["id"], contract["label"], observations)
        if not summary:
            return None, f"{contract['id']}: no usable rows"
        if not is_recent(str(summary.get("reportDate", "")), contract["maximumAgeDays"]):
            return None, (
                f"{contract['id']}: exact contract {contract['cftcContractCode']} is stale "
                f"({summary.get('reportDate')}); excluded"
            )
        summary["contract"] = contract_metadata(contract, summary["market"])
        summary["dataState"] = "current"
        summary["dataMethod"] = "CFTC public reporting API exact contract registry"
        summary["sourceUrl"] = f"https://publicreporting.cftc.gov/resource/{contract['datasetId']}.json"
        return summary, None
    except Exception as exc:
        return None, f"{contract['id']}: {exc}"


def fetch_cot_api() -> tuple[list[dict[str, Any]], list[str]]:
    contracts = verified_contracts(REGISTRY)
    with ThreadPoolExecutor(max_workers=min(6, len(contracts))) as executor:
        results = list(executor.map(fetch_registered_contract, contracts))
    summaries = [summary for summary, _ in results if summary]
    errors = [error for _, error in results if error]
    return summaries, errors


_original_load_previous = collector.load_previous


def load_previous_verified() -> dict[str, Any]:
    previous = _original_load_previous()
    if previous.get("cot"):
        previous["cot"] = [row for row in previous["cot"] if generated_row_is_verified(row, REGISTRY)]
    return previous


_original_build_dataset = collector.build_dataset


def build_dataset_with_registry(previous: dict[str, Any]) -> dict[str, Any]:
    dataset = _original_build_dataset(previous)
    verified = verified_contracts(REGISTRY)
    unavailable = unavailable_contracts(REGISTRY)
    current_rows = {
        str(row.get("id")): row
        for row in dataset.get("cot", [])
        if isinstance(row, dict) and row.get("id")
    }
    previous_rows = {
        str(row.get("id")): row
        for row in previous.get("cot", [])
        if isinstance(row, dict) and row.get("id")
    }
    cftc_status = next(
        (
            item
            for item in dataset.get("sourceStatus", [])
            if "cftc" in str(item.get("source", "")).lower()
        ),
        None,
    )
    if cftc_status and cftc_status.get("status") == "stale fallback":
        for row in current_rows.values():
            row["dataState"] = "stale-retained"

    retained_ids: list[str] = []
    for contract in verified:
        contract_id = contract["id"]
        if contract_id in current_rows or contract_id not in previous_rows:
            continue
        retained = dict(previous_rows[contract_id])
        retained["dataState"] = "stale-retained"
        current_rows[contract_id] = retained
        retained_ids.append(contract_id)

    display_order = {contract_id: index for index, contract_id in enumerate(REGISTRY["referenceProductIds"])}
    dataset["cot"] = sorted(
        current_rows.values(),
        key=lambda row: (display_order.get(str(row.get("id")), len(display_order)), str(row.get("name", ""))),
    )
    missing = [
        {"id": contract["id"], "label": contract["label"], "reason": "No current or retained verified observation is available."}
        for contract in verified
        if contract["id"] not in current_rows
    ]
    if retained_ids and cftc_status:
        retained_detail = "Retained previously verified rows for: " + ", ".join(retained_ids) + "."
        cftc_status["detail"] = " ".join(filter(None, [str(cftc_status.get("detail", "")).strip(), retained_detail]))
    elif cftc_status and cftc_status.get("status") == "current":
        cftc_status["detail"] = (
            f"Loaded {len(current_rows)} current exact-contract series from the CFTC Public Reporting Environment."
        )
    dataset["cotContractRegistry"] = {
        "schemaVersion": REGISTRY["schemaVersion"],
        "referenceProductIds": REGISTRY["referenceProductIds"],
        "verifiedIds": [contract["id"] for contract in verified],
        "missing": missing,
        "unavailable": [
            {
                "id": contract["id"],
                "label": contract["label"],
                "reason": contract["unavailableReason"],
                **({"lastObservationDate": contract["lastObservationDate"]} if contract.get("lastObservationDate") else {}),
                **({"historicalCftcContractCode": contract["historicalCftcContractCode"]} if contract.get("historicalCftcContractCode") else {}),
            }
            for contract in unavailable
        ],
    }
    dataset.setdefault("methodology", {})["cotRegistry"] = (
        "Rows require an exact CFTC contract-market code and exact approved market/exchange name. "
        "Unapproved benchmarks remain unavailable; no open-interest ranking or similar-name substitution is used."
    )
    dataset["methodology"]["cot"] = (
        "CFTC Public Reporting Environment futures-only data. Commodities use Managed Money; financial futures use "
        "Leveraged Funds. Every row must match an approved exact code, complete market/exchange identity and freshness limit; "
        "history includes the latest 52 weekly observations."
    )
    return dataset


collector.load_previous = load_previous_verified
collector.fetch_cot = fetch_cot_api
collector.build_dataset = build_dataset_with_registry

if __name__ == "__main__":
    sys.exit(collector.main())
