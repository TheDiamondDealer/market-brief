#!/usr/bin/env python3
"""Load and enforce the versioned exact CFTC contract registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

REGISTRY_PATH = Path(__file__).with_name("cot_contracts.json")
CODE_KEYS = ("cftc_contract_market_code", "CFTC_Contract_Market_Code")
NAME_KEYS = ("market_and_exchange_names", "Market_and_Exchange_Names")


class ContractRegistryError(ValueError):
    """Raised when the registry or a CFTC row violates the identity contract."""


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractRegistryError(f"Invalid COT registry {path}: {exc}") from exc
    validate_registry(registry)
    return registry


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schemaVersion") != 1:
        raise ContractRegistryError("Unsupported COT registry schemaVersion")
    contracts = registry.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        raise ContractRegistryError("COT registry contracts must be a non-empty list")

    ids: set[str] = set()
    codes: set[tuple[str, str]] = set()
    for contract in contracts:
        contract_id = _text(contract.get("id"))
        if not contract_id or contract_id in ids:
            raise ContractRegistryError(f"Duplicate or empty COT contract id: {contract_id!r}")
        ids.add(contract_id)
        if contract.get("status") not in {"verified", "unavailable"}:
            raise ContractRegistryError(f"Invalid status for {contract_id}")
        if contract.get("reportType") not in {"disaggregated", "traders-in-financial-futures"}:
            raise ContractRegistryError(f"Invalid reportType for {contract_id}")
        if not isinstance(contract.get("maximumAgeDays"), int) or contract["maximumAgeDays"] < 1:
            raise ContractRegistryError(f"Invalid maximumAgeDays for {contract_id}")

        if contract["status"] == "verified":
            code = _text(contract.get("cftcContractCode"))
            names = contract.get("acceptedNames")
            exchange = _text(contract.get("expectedExchange"))
            dataset_id = _text(contract.get("datasetId"))
            if len(code) != 6 or not code.isdigit() or not exchange or not dataset_id:
                raise ContractRegistryError(f"Incomplete verified identity for {contract_id}")
            if not isinstance(names, list) or not names or any(not _text(name) for name in names):
                raise ContractRegistryError(f"Verified contract {contract_id} needs acceptedNames")
            identity = (contract["reportType"], code)
            if identity in codes:
                raise ContractRegistryError(f"Duplicate CFTC identity {identity}")
            codes.add(identity)
        else:
            if contract.get("cftcContractCode") is not None or contract.get("acceptedNames") != []:
                raise ContractRegistryError(f"Unavailable contract {contract_id} cannot carry an accepted identity")
            if not _text(contract.get("unavailableReason")):
                raise ContractRegistryError(f"Unavailable contract {contract_id} needs a reason")


def contracts_by_id(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    current = registry or load_registry()
    return {contract["id"]: contract for contract in current["contracts"]}


def verified_contracts(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    current = registry or load_registry()
    return [contract for contract in current["contracts"] if contract["status"] == "verified"]


def unavailable_contracts(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    current = registry or load_registry()
    return [contract for contract in current["contracts"] if contract["status"] == "unavailable"]


def row_value(row: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        if row.get(key) not in (None, ""):
            return _text(row[key])
    return ""


def row_contract_code(row: dict[str, Any]) -> str:
    return row_value(row, CODE_KEYS)


def row_market_name(row: dict[str, Any]) -> str:
    return row_value(row, NAME_KEYS)


def contract_accepts_row(contract: dict[str, Any], row: dict[str, Any]) -> bool:
    if contract.get("status") != "verified":
        return False
    code = row_contract_code(row)
    name = row_market_name(row)
    if code != contract["cftcContractCode"]:
        return False
    if name not in {_text(value) for value in contract["acceptedNames"]}:
        return False
    if contract["expectedExchange"].upper() not in name.upper():
        return False
    return not any(_text(term).upper() in name.upper() for term in contract.get("rejectedTerms", []))


def contract_metadata(contract: dict[str, Any], market_name: str) -> dict[str, Any]:
    return {
        "registryVersion": 1,
        "identityStatus": "verified",
        "cftcContractCode": contract["cftcContractCode"],
        "reportType": contract["reportType"],
        "category": contract["category"],
        "exchange": contract["expectedExchange"],
        "marketName": market_name,
    }


def generated_row_is_verified(row: dict[str, Any], registry: dict[str, Any] | None = None) -> bool:
    contract = contracts_by_id(registry).get(str(row.get("id", "")))
    identity = row.get("contract")
    if not contract or contract.get("status") != "verified" or not isinstance(identity, dict):
        return False
    return (
        identity.get("identityStatus") == "verified"
        and identity.get("registryVersion") == 1
        and identity.get("cftcContractCode") == contract["cftcContractCode"]
        and identity.get("reportType") == contract["reportType"]
        and identity.get("category") == contract["category"]
        and identity.get("exchange") == contract["expectedExchange"]
        and identity.get("marketName") == row.get("market")
        and row.get("market") in contract["acceptedNames"]
    )
