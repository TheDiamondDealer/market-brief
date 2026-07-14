#!/usr/bin/env python3
"""Run the hardened political collector with a durable filing ledger."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import update_political_disclosures_strict as strict
from political_filing_ledger import FilingIdentity, FilingLedger, content_hash, identity_from_filing

collector = strict.collector
LEDGER_PATH = collector.ROOT / "site" / "data" / "political" / "filing-ledger.json"
ledger = FilingLedger(LEDGER_PATH)
_pending_hashes: dict[str, str] = {}
_response_hashes: dict[str, str] = {}

_original_load_previous = collector.load_previous
_original_discover_house = collector.discover_house_filings
_original_download_house = collector.download_house_pdf
_original_parse_house = collector.parse_house_pdf
_original_discover_senate = collector.discover_senate_filings
_original_parse_senate = collector.parse_senate_report
_original_fetch = collector.fetch


def _identity_from_trade(tracker_id: str, chamber: str, trade: dict[str, Any]) -> FilingIdentity | None:
    filing_id = str(trade.get("filingId") or "").strip()
    filed = str(trade.get("filed") or "").strip()
    if not filing_id or not filed:
        return None
    return FilingIdentity(
        tracker_id=tracker_id,
        chamber=chamber,
        filing_id=filing_id,
        filed=filed,
        report_url=str(trade.get("sourceUrl") or ""),
        year=int(filed[:4]),
    )


def load_previous_with_ledger() -> dict[str, Any]:
    previous = _original_load_previous()
    for tracker_id, tracker in previous.get("trackers", {}).items():
        chamber = str(tracker.get("chamber") or collector.TRACKERS.get(tracker_id, {}).get("chamber") or "House")
        by_filing: dict[str, list[dict[str, Any]]] = {}
        for trade in tracker.get("trades", []):
            filing_id = str(trade.get("filingId") or "")
            if filing_id:
                by_filing.setdefault(filing_id, []).append(trade)
        retry_ids: set[str] = set()
        for filing_trades in by_filing.values():
            identity = _identity_from_trade(tracker_id, chamber, filing_trades[0])
            if not identity:
                continue
            ledger.bootstrap_success(identity, trade_count=len(filing_trades))
            if ledger.should_process(identity, known_success=True):
                retry_ids.add(identity.filing_id)
        if retry_ids:
            tracker["trades"] = [trade for trade in tracker.get("trades", []) if str(trade.get("filingId")) not in retry_ids]
    return previous


def discover_house_with_ledger(session):
    filings, errors = _original_discover_house(session)
    for filing in filings:
        ledger.discover(identity_from_filing(filing))
    return filings, errors


def download_house_with_ledger(session, filing):
    identity = identity_from_filing(filing)
    ledger.begin(identity)
    try:
        content, url = _original_download_house(session, filing)
        digest = content_hash(content)
        _pending_hashes[identity.key] = digest
        identity = FilingIdentity(identity.tracker_id, identity.chamber, identity.filing_id, identity.filed, url, identity.year)
        ledger.discover(identity)
        return content, url
    except Exception as exc:
        ledger.failure(identity, exc)
        raise


def parse_house_with_ledger(content: bytes, filing):
    identity = identity_from_filing(filing)
    digest = _pending_hashes.get(identity.key) or content_hash(content)
    try:
        trades = _original_parse_house(content, filing)
        if not trades:
            raise collector.CollectionError("no transaction rows parsed")
        for trade in trades:
            trade["filingContentHash"] = digest
            trade["parserVersion"] = ledger.parser_version
        ledger.success(identity, digest=digest, trade_count=len(trades))
        return trades
    except Exception as exc:
        ledger.failure(identity, exc)
        raise


def tracked_fetch(session, url: str, *, method: str = "GET", **kwargs):
    response = _original_fetch(session, url, method=method, **kwargs)
    if "/ptr/" in str(url).lower() or "periodic" in str(url).lower():
        _response_hashes[str(response.url)] = content_hash(response.content)
        _response_hashes[str(url)] = content_hash(response.content)
    return response


def discover_senate_with_ledger(session, tracker_id, config):
    filings = _original_discover_senate(session, tracker_id, config)
    for filing in filings:
        ledger.discover(identity_from_filing(filing))
    return filings


def parse_senate_with_ledger(session, filing):
    identity = identity_from_filing(filing)
    ledger.begin(identity)
    try:
        trades = _original_parse_senate(session, filing)
        if not trades:
            raise collector.CollectionError("no transaction rows parsed")
        digest = _response_hashes.get(filing.report_url)
        if not digest:
            normalized = json.dumps(trades, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            digest = content_hash(normalized)
        for trade in trades:
            trade["filingContentHash"] = digest
            trade["parserVersion"] = ledger.parser_version
        ledger.success(identity, digest=digest, trade_count=len(trades))
        return trades
    except Exception as exc:
        ledger.failure(identity, exc)
        raise


def attach_ledger_status() -> None:
    if not collector.JSON_PATH.exists():
        return
    dataset = json.loads(collector.JSON_PATH.read_text(encoding="utf-8"))
    dataset.setdefault("sourceStatus", {})["filingLedger"] = ledger.summary()
    collector.JSON_PATH.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    collector.JS_PATH.write_text(collector.browser_js(dataset), encoding="utf-8")


collector.load_previous = load_previous_with_ledger
collector.discover_house_filings = discover_house_with_ledger
collector.download_house_pdf = download_house_with_ledger
collector.parse_house_pdf = parse_house_with_ledger
collector.fetch = tracked_fetch
collector.discover_senate_filings = discover_senate_with_ledger
collector.parse_senate_report = parse_senate_with_ledger


if __name__ == "__main__":
    exit_code = 1
    try:
        exit_code = collector.main()
        ledger.write()
        attach_ledger_status()
        strict.write_summary()
    finally:
        ledger.write()
    raise SystemExit(exit_code)
