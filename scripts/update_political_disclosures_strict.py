#!/usr/bin/env python3
"""Harden the political disclosure collector for variable official PDF layouts.

This wrapper rejects page-header contamination, invalid statutory amount fields and
control characters. Any previously cached filing containing a malformed row is removed
from the in-memory baseline so that the complete filing is downloaded and parsed again.
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import pdfplumber

import update_political_disclosures as collector

_original_clean = collector.clean
_original_house_parser = collector.parse_house_pdf
_original_load_previous = collector.load_previous
SUMMARY_PATH = collector.ROOT / "site" / "data" / "political-disclosures-summary.json"

HEADER_MARKERS = (
    "name: hon.",
    "state/district:",
    "transaction date notification",
    "id owner asset",
    "cap. gains",
    "periodic transaction report",
)

ROW_PATTERN = re.compile(
    r"\b(?P<owner>SP|JT|DC|SELF|Self|Dependent Child|Not specified)\b\s+"
    r"(?P<asset>.+?)\s+"
    r"(?P<type>P|S(?:\s*\((?:partial|full)\))?|E)\s+"
    r"(?P<traded>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<notified>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<amount>(?:\$[\d,]+\s*(?:-|–|to)\s*\$[\d,]+|Over\s+\$[\d,]+))",
    re.IGNORECASE | re.DOTALL,
)

TABLE_HEADER_PATTERN = re.compile(
    r"(?:ID\s+)?Owner\s+Asset\s+Transaction\s+Date\s+Notification\s+Amount"
    r"(?:\s+Cap\.\s+Type)?(?:\s+Date)?(?:\s+Gains\s*>\s*\$?200\??)?",
    re.IGNORECASE,
)


def hardened_clean(value: Any) -> str:
    text = str(value or "").replace("\u00a0", " ")
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


collector.clean = hardened_clean


def valid_amount(value: Any) -> bool:
    text = hardened_clean(value).replace(" to ", " - ")
    return bool(
        re.fullmatch(r"\$[\d,]+(?:\.00)?\s*(?:-|–)\s*\$[\d,]+(?:\.00)?", text)
        or re.fullmatch(r"Over\s+\$[\d,]+(?:\.00)?", text, re.IGNORECASE)
    )


def valid_asset(value: Any) -> bool:
    text = hardened_clean(value)
    lower = text.lower()
    if not text or len(text) > 240 or not re.search(r"[A-Za-z]", text):
        return False
    if any(marker in lower for marker in HEADER_MARKERS):
        return False
    if re.match(r"^\d{4,}\s+[A-Z]?\s*Name:", text, re.IGNORECASE):
        return False
    return True


def valid_trade(trade: dict[str, Any]) -> bool:
    return (
        valid_asset(trade.get("asset"))
        and valid_amount(trade.get("amount"))
        and bool(collector.iso_date(trade.get("traded")))
        and collector.map_transaction_type(str(trade.get("type", ""))) != "Other"
    )


def clean_trade(trade: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(trade)
    for key in ("asset", "ticker", "type", "owner", "traded", "filed", "lag", "amount", "source", "sourceUrl"):
        if key in cleaned:
            cleaned[key] = hardened_clean(cleaned[key])
    return cleaned


def load_previous_hardened() -> dict[str, Any]:
    previous = _original_load_previous()
    for tracker in previous.get("trackers", {}).values():
        trades = [clean_trade(trade) for trade in tracker.get("trades", [])]
        malformed_filing_ids = {
            trade.get("filingId") for trade in trades if trade.get("filingId") and not valid_trade(trade)
        }
        tracker["trades"] = [
            trade for trade in trades
            if valid_trade(trade) and trade.get("filingId") not in malformed_filing_ids
        ]
    return previous


collector.load_previous = load_previous_hardened


def _fallback_house_text(content: bytes, filing: collector.Filing) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = hardened_clean(page.extract_text(x_tolerance=2, y_tolerance=3) or "")
            header = TABLE_HEADER_PATTERN.search(text)
            if header:
                text = text[header.end():]
            for index, match in enumerate(ROW_PATTERN.finditer(text), start=1):
                asset_raw = hardened_clean(match.group("asset"))
                traded = collector.iso_date(match.group("traded"))
                amount = hardened_clean(match.group("amount")).replace(" to ", " - ")
                tx_type = collector.map_transaction_type(match.group("type"))
                ticker = collector.extract_ticker(asset_raw)
                owner = hardened_clean(match.group("owner"))
                trade_id = collector.stable_id(
                    "house-text-v2", filing.filing_id, page_number, index, asset_raw, traded, amount
                )
                lag = collector.days_between(traded, filing.filed)
                trade = {
                    "id": trade_id,
                    "filingId": filing.filing_id,
                    "asset": collector.transaction_asset(asset_raw, ticker),
                    "ticker": ticker,
                    "type": tx_type,
                    "owner": owner,
                    "traded": traded,
                    "filed": filing.filed,
                    "lag": f"{lag} days" if lag is not None else "—",
                    "lagDays": lag,
                    "amount": amount,
                    "source": "Official House Periodic Transaction Report",
                    "sourceUrl": filing.report_url,
                    "page": page_number,
                }
                if valid_trade(trade):
                    trades.append(trade)
    return trades


def semantic_key(trade: dict[str, Any]) -> tuple[str, ...]:
    return (
        collector.norm(trade.get("asset")),
        collector.norm(trade.get("ticker")),
        collector.norm(trade.get("type")),
        collector.norm(trade.get("owner")),
        hardened_clean(trade.get("traded")),
        collector.norm(trade.get("amount")),
    )


def parse_house_pdf(content: bytes, filing: collector.Filing) -> list[dict[str, Any]]:
    table_rows = [clean_trade(trade) for trade in _original_house_parser(content, filing)]
    table_rows = [trade for trade in table_rows if valid_trade(trade)]
    fallback_rows = _fallback_house_text(content, filing)
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    for trade in table_rows + fallback_rows:
        merged.setdefault(semantic_key(trade), trade)
    return list(merged.values())


collector.parse_house_pdf = parse_house_pdf


def write_summary() -> None:
    if not collector.JSON_PATH.exists():
        return
    data = json.loads(collector.JSON_PATH.read_text(encoding="utf-8"))
    trackers = {}
    for tracker_id, tracker in data.get("trackers", {}).items():
        trades = tracker.get("trades", [])
        holdings = tracker.get("portfolio", {}).get("holdings", [])
        trackers[tracker_id] = {
            "name": tracker.get("name", tracker_id),
            "chamber": tracker.get("chamber"),
            "status": tracker.get("status"),
            "trades": len(trades),
            "holdings": len(holdings),
            "latestTrade": max((trade.get("traded", "") for trade in trades), default=None),
            "latestFiling": max((trade.get("filed", "") for trade in trades), default=None),
            "newTrades": tracker.get("sourceStatus", {}).get("newTrades", 0),
            "errors": tracker.get("sourceStatus", {}).get("errors", [])[:5],
        }
    summary = {
        "generatedAt": data.get("generatedAt"),
        "generatedAtHuman": data.get("generatedAtHuman"),
        "totalTrades": sum(item["trades"] for item in trackers.values()),
        "trackers": trackers,
        "sourceStatus": data.get("sourceStatus", {}),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    exit_code = collector.main()
    write_summary()
    raise SystemExit(exit_code)
