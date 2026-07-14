#!/usr/bin/env python3
"""Verify mandatory remodel routes, aliases and generated-file ownership."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

ROUTE_CONTRACTS = {
    "home": ("features/command-centre/command-page.js", "router.register('home'"),
    "news": ("features/impact-feed/impact-page.js", "router.register('news'"),
    "news/<id>": ("features/impact-feed/impact-page.js", "registerPattern('impact-detail'"),
    "cot": ("features/cot/cot-page.js", "route.name === 'cot'"),
    "trackers": ("features/political-flow/political-page.js", "router.register('trackers'"),
    "trackers/<id>": ("features/political-flow/political-page.js", "registerPattern('political-profile'"),
    "asset/<id>": ("features/asset-workspace/asset-page.js", "registerPattern('asset-workspace'"),
    "product/<id>": ("features/asset-workspace/asset-page.js", "registerPattern('product-detail'"),
    "events": ("features/calendar/calendar-page.js", "router.register('events'"),
    "calendar": ("features/calendar/calendar-page.js", "router.register('calendar'"),
    "calendar/<id>": ("features/calendar/calendar-page.js", "registerPattern('calendar-detail'"),
    "rates": ("features/macro-monitor/macro-page.js", "router.register('rates'"),
    "macro": ("features/macro-monitor/macro-page.js", "router.register('macro'"),
    "sources": ("features/source-health/source-health-page.js", "router.register('sources'"),
    "source-health": ("features/source-health/source-health-page.js", "router.register('source-health'"),
}

GENERATED_OWNERS = {
    "site/free-data.js": "scripts/update_free_data_charts.py",
    "site/data/free-market-data.json": "scripts/update_free_data_charts.py",
    "site/political-data.js": "scripts/update_political_disclosures_ledger.py",
    "site/data/political-disclosures.json": "scripts/update_political_disclosures_ledger.py",
    "site/data/political-disclosures-summary.json": "scripts/update_political_disclosures_ledger.py",
    "site/data/political/manifest.json": "scripts/build_political_data_split.py",
    "site/data/political/summary.json": "scripts/build_political_data_split.py",
}


def verify_routes() -> list[str]:
    errors: list[str] = []
    for route, (relative, marker) in ROUTE_CONTRACTS.items():
        path = SITE / relative
        if not path.exists():
            errors.append(f"{route}: missing {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if marker not in text:
            errors.append(f"{route}: {relative} is missing marker {marker}")
    index = (SITE / "index.html").read_text(encoding="utf-8")
    for view in ("view-home", "view-news", "view-cot", "view-trackers", "view-product-detail", "view-events", "view-rates"):
        if f'id="{view}"' not in index:
            errors.append(f"Static route host is missing: {view}")
    source_page = (SITE / "features/source-health" / "source-health-page.js").read_text(encoding="utf-8")
    if "view-sources" not in source_page or "ensureHost" not in source_page:
        errors.append("Dynamic source-health host contract is missing")
    return errors


def verify_generated_ownership() -> list[str]:
    errors: list[str] = []
    for generated, owner in GENERATED_OWNERS.items():
        if not (ROOT / generated).exists():
            errors.append(f"Generated file missing: {generated}")
        if not (ROOT / owner).exists():
            errors.append(f"Generator missing for {generated}: {owner}")
    workflow = (ROOT / ".github" / "workflows" / "update-political-disclosures.yml").read_text(encoding="utf-8")
    if "site/data/political" not in workflow:
        errors.append("Political workflow does not commit split political files")
    return errors


def verify_retired_renderer() -> list[str]:
    text = (SITE / "command-centre.js").read_text(encoding="utf-8")
    errors: list[str] = []
    if "commandCentreRetired = true" not in text:
        errors.append("Legacy Command Centre path is not an explicit compatibility shim")
    for retired in ("risk score", "riskAngle", "bias.total", "renderRiskGauge"):
        if retired in text:
            errors.append(f"Retired composite-score implementation remains: {retired}")
    return errors


def verify_contract_files() -> list[str]:
    errors: list[str] = []
    for relative in (
        "schemas/news-impact.schema.json",
        "schemas/calendar-events.schema.json",
        "schemas/cot-contract-registry.schema.json",
        "site/core/freshness.js",
        "site/styles/hardening.css",
    ):
        path = ROOT / relative
        if not path.exists():
            errors.append(f"Mandatory contract missing: {relative}")
    registry = json.loads((ROOT / "scripts" / "cot_contracts.json").read_text(encoding="utf-8"))
    unavailable = {item["id"] for item in registry.get("contracts", []) if item.get("status") == "unavailable"}
    expected = {"oil-wti", "oil-brent", "gas-us", "gas-uk"}
    if unavailable != expected:
        errors.append(f"COT unavailable set changed: expected {sorted(expected)}, got {sorted(unavailable)}")
    return errors


def main() -> int:
    errors = [*verify_routes(), *verify_generated_ownership(), *verify_retired_renderer(), *verify_contract_files()]
    if errors:
        print("Release verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Release routes verified: {len(ROUTE_CONTRACTS)}")
    print(f"Generated ownership records verified: {len(GENERATED_OWNERS)}")
    print("Legacy composite-score renderer is retired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
