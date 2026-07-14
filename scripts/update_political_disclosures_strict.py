#!/usr/bin/env python3
"""Harden the political disclosure collector for variable official PDF layouts."""
from __future__ import annotations

import io
import re
import sys
from typing import Any

import pdfplumber

import update_political_disclosures as collector

_original_house_parser = collector.parse_house_pdf

ROW_PATTERN = re.compile(
    r"(?P<owner>SP|JT|DC|SELF|Self|Dependent Child|Not specified)\s+"
    r"(?P<asset>.+?)\s+"
    r"(?P<type>P|S(?:\s*\((?:partial|full)\))?|E)\s+"
    r"(?P<traded>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<notified>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<amount>(?:\$[\d,]+\s*(?:-|–|to)\s*\$[\d,]+|Over\s+\$[\d,]+))",
    re.IGNORECASE | re.DOTALL,
)


def _fallback_house_text(content: bytes, filing: collector.Filing) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            text = re.sub(r"\s+", " ", text)
            for index, match in enumerate(ROW_PATTERN.finditer(text), start=1):
                asset_raw = collector.clean(match.group("asset"))
                traded = collector.iso_date(match.group("traded"))
                amount = collector.clean(match.group("amount")).replace(" to ", " - ")
                tx_type = collector.map_transaction_type(match.group("type"))
                ticker = collector.extract_ticker(asset_raw)
                owner = collector.clean(match.group("owner"))
                trade_id = collector.stable_id(
                    "house-text", filing.filing_id, page_number, index, asset_raw, traded, amount
                )
                lag = collector.days_between(traded, filing.filed)
                trades.append({
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
                })
    return list({trade["id"]: trade for trade in trades if trade.get("traded")}.values())


def parse_house_pdf(content: bytes, filing: collector.Filing) -> list[dict[str, Any]]:
    table_rows = _original_house_parser(content, filing)
    if table_rows:
        return table_rows
    return _fallback_house_text(content, filing)


collector.parse_house_pdf = parse_house_pdf

if __name__ == "__main__":
    raise SystemExit(collector.main())
