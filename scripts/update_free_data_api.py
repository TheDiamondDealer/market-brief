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


def fetch_cot_api() -> tuple[list[dict[str, Any]], list[str]]:
    summaries: list[dict[str, Any]] = []
    errors: list[str] = []
    for contract in verified_contracts(REGISTRY):
        try:
            observations = observations_for(contract)
            summary = collector.summarise_market(contract["id"], contract["label"], observations)
            if not summary:
                errors.append(f"{contract['id']}: no usable rows")
                continue
            if not is_recent(str(summary.get("reportDate", "")), contract["maximumAgeDays"]):
                errors.append(
                    f"{contract['id']}: exact contract {contract['cftcContractCode']} is stale "
                    f"({summary.get('reportDate')}); excluded"
                )
                continue
            summary["contract"] = contract_metadata(contract, summary["market"])
            summary["dataMethod"] = "CFTC public reporting API exact contract registry"
            summary["sourceUrl"] = f"https://publicreporting.cftc.gov/resource/{contract['datasetId']}.json"
            summaries.append(summary)
        except Exception as exc:
            errors.append(f"{contract['id']}: {exc}")
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
    unavailable = unavailable_contracts(REGISTRY)
    dataset["cotContractRegistry"] = {
        "schemaVersion": REGISTRY["schemaVersion"],
        "verifiedIds": [contract["id"] for contract in verified_contracts(REGISTRY)],
        "unavailable": [
            {"id": contract["id"], "label": contract["label"], "reason": contract["unavailableReason"]}
            for contract in unavailable
        ],
    }
    dataset.setdefault("methodology", {})["cotRegistry"] = (
        "Rows require an exact CFTC contract-market code and exact approved market/exchange name. "
        "Unapproved benchmarks remain unavailable; no open-interest ranking or similar-name substitution is used."
    )
    return dataset


collector.load_previous = load_previous_verified
collector.fetch_cot = fetch_cot_api
collector.build_dataset = build_dataset_with_registry

if __name__ == "__main__":
    sys.exit(collector.main())
