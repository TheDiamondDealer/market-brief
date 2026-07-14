#!/usr/bin/env python3
"""Run official feeds with a CIK-pinned SEC collector.

SEC's public ticker-directory file can reject cloud runners even when the
submissions API remains available. This wrapper removes that directory as a
single point of failure. Every configured CIK response must independently
confirm the expected ticker before any filing is accepted.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import update_official_feeds as base


def accepted_at(value: Any) -> str | None:
    text = str(value or "")
    if re.fullmatch(r"\d{14}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}T{text[8:10]}:{text[10:12]}:{text[12:14]}Z"
    return text or None


def collect_sec_by_cik(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = base.source_template(
        "sec-edgar",
        "SEC EDGAR company filings",
        "Company Filings",
        "No API key",
        "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "Throughout each US business day",
        collected_at,
    )
    companies = config.get("companies", [])
    if not companies:
        return base.finalise_failure(source, previous, "No pinned SEC CIK registry is configured")

    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=int(config.get("lookbackDays", 180)))).isoformat()
    allowed_forms = set(config.get("forms", []))
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    verified_companies = 0
    keys = (
        "accessionNumber", "filingDate", "reportDate", "acceptanceDateTime",
        "act", "form", "fileNumber", "filmNumber", "items", "size",
        "isXBRL", "isInlineXBRL", "primaryDocument", "primaryDocDescription",
    )

    for company in companies:
        ticker = str(company.get("ticker") or "").upper()
        cik = int(company.get("cik") or 0)
        if not ticker or cik <= 0:
            failures.append(f"invalid registry entry: {company!r}")
            continue
        try:
            submissions = base.request_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
            returned_tickers = {str(value).upper() for value in submissions.get("tickers", [])}
            if ticker not in returned_tickers:
                raise ValueError(f"CIK {cik} did not confirm ticker {ticker}; returned={sorted(returned_tickers)}")
            verified_companies += 1
            recent = submissions.get("filings", {}).get("recent", {})
            length = max((len(recent.get(key, [])) for key in keys), default=0)
            for index in range(length):
                row = {key: (recent.get(key, [])[index] if index < len(recent.get(key, [])) else None) for key in keys}
                filed_at = str(row.get("filingDate") or "")
                form = str(row.get("form") or "")
                if not filed_at or filed_at < cutoff or form not in allowed_forms:
                    continue
                accession = str(row.get("accessionNumber") or "")
                primary_document = str(row.get("primaryDocument") or "")
                if not accession or not primary_document:
                    continue
                accepted = accepted_at(row.get("acceptanceDateTime"))
                records.append({
                    "id": f"sec-{cik}-{base.accession_compact(accession)}",
                    "kind": "filing",
                    "name": row.get("primaryDocDescription") or f"{form} filing",
                    "companyId": f"CIK{cik:010d}",
                    "company": submissions.get("name") or ticker,
                    "ticker": ticker,
                    "form": form,
                    "filedAt": filed_at,
                    "acceptedAt": accepted,
                    "observedAt": accepted or filed_at,
                    "period": row.get("reportDate") or None,
                    "accession": accession,
                    "items": row.get("items") or None,
                    "primaryDocument": primary_document,
                    "title": row.get("primaryDocDescription") or f"{form} filing",
                    "sourceUrl": base.sec_archives_url(cik, accession, primary_document),
                })
        except Exception as exc:
            failures.append(f"{ticker}/CIK{cik:010d}: {base.scrub(exc)}")
        time.sleep(0.12)

    records.sort(key=lambda item: (str(item.get("acceptedAt") or ""), str(item.get("filedAt") or "")), reverse=True)
    source["records"] = records[: int(config.get("maxRecords", 160))]
    if not source["records"]:
        return base.finalise_failure(source, previous, "; ".join(failures) or "SEC submissions returned no priority filings")

    source = base.finalise_success(
        source,
        status="partial" if failures else "current",
        detail=(
            f"{len(source['records'])} recent priority filings across "
            f"{verified_companies} CIK-verified companies; {len(failures)} company failures."
        ),
    )
    source["error"] = "; ".join(failures)[:600] if failures else None
    return source


base.collect_sec = collect_sec_by_cik

if __name__ == "__main__":
    raise SystemExit(base.main())
