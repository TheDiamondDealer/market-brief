#!/usr/bin/env python3
"""Run official feeds with hardened SEC and BLS collectors.

SEC's public ticker-directory file can reject cloud runners even when the
submissions API remains available. This wrapper removes that directory as a
single point of failure. Every configured CIK response must independently
confirm the expected ticker before any filing is accepted.

BLS calculations are not requested because the dashboard does not consume them.
Advisory API messages therefore do not downgrade a complete configured series
set to partial.
"""
from __future__ import annotations

import os
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


def collect_sec_by_cik(
    config: dict[str, Any],
    previous: dict[str, Any],
    collected_at: str,
) -> dict[str, Any]:
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

    cutoff = (
        datetime.now(timezone.utc).date()
        - timedelta(days=int(config.get("lookbackDays", 180)))
    ).isoformat()
    allowed_forms = set(config.get("forms", []))
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    verified_companies = 0
    keys = (
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "act",
        "form",
        "fileNumber",
        "filmNumber",
        "items",
        "size",
        "isXBRL",
        "isInlineXBRL",
        "primaryDocument",
        "primaryDocDescription",
    )

    for company in companies:
        ticker = str(company.get("ticker") or "").upper()
        cik = int(company.get("cik") or 0)
        if not ticker or cik <= 0:
            failures.append(f"invalid registry entry: {company!r}")
            continue
        try:
            submissions = base.request_json(
                f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
            )
            returned_tickers = {
                str(value).upper() for value in submissions.get("tickers", [])
            }
            if ticker not in returned_tickers:
                raise ValueError(
                    f"CIK {cik} did not confirm ticker {ticker}; "
                    f"returned={sorted(returned_tickers)}"
                )
            verified_companies += 1
            recent = submissions.get("filings", {}).get("recent", {})
            length = max((len(recent.get(key, [])) for key in keys), default=0)
            for index in range(length):
                row = {
                    key: (
                        recent.get(key, [])[index]
                        if index < len(recent.get(key, []))
                        else None
                    )
                    for key in keys
                }
                filed_at = str(row.get("filingDate") or "")
                form = str(row.get("form") or "")
                if not filed_at or filed_at < cutoff or form not in allowed_forms:
                    continue
                accession = str(row.get("accessionNumber") or "")
                primary_document = str(row.get("primaryDocument") or "")
                if not accession or not primary_document:
                    continue
                accepted = accepted_at(row.get("acceptanceDateTime"))
                records.append(
                    {
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
                        "sourceUrl": base.sec_archives_url(
                            cik, accession, primary_document
                        ),
                    }
                )
        except Exception as exc:
            failures.append(f"{ticker}/CIK{cik:010d}: {base.scrub(exc)}")
        time.sleep(0.12)

    records.sort(
        key=lambda item: (
            str(item.get("acceptedAt") or ""),
            str(item.get("filedAt") or ""),
        ),
        reverse=True,
    )
    source["records"] = records[: int(config.get("maxRecords", 160))]
    if not source["records"]:
        return base.finalise_failure(
            source,
            previous,
            "; ".join(failures) or "SEC submissions returned no priority filings",
        )

    source = base.finalise_success(
        source,
        status="partial" if failures else "current",
        detail=(
            f"{len(source['records'])} recent priority filings across "
            f"{verified_companies} CIK-verified companies; "
            f"{len(failures)} company failures."
        ),
    )
    source["error"] = "; ".join(failures)[:600] if failures else None
    return source


def collect_bls_without_unused_calculations(
    config: dict[str, Any],
    previous: dict[str, Any],
    collected_at: str,
) -> dict[str, Any]:
    source = base.source_template(
        "bls-public-data",
        "BLS labour and inflation series",
        "Macro",
        "No key required; free registration key optional",
        "https://www.bls.gov/developers/api_signature_v2.htm",
        "Monthly releases",
        collected_at,
    )
    try:
        current_year = datetime.now(timezone.utc).year
        payload: dict[str, Any] = {
            "seriesid": [row["id"] for row in config.get("series", [])],
            "startyear": str(current_year - 2),
            "endyear": str(current_year),
        }
        registration_key = os.environ.get("BLS_API_KEY", "").strip()
        if registration_key:
            payload["registrationkey"] = registration_key

        response = base.request_json(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            method="POST",
            payload=payload,
        )
        if response.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError(
                "; ".join(response.get("message", [])) or response.get("status")
            )

        config_map = {row["id"]: row for row in config.get("series", [])}
        records: list[dict[str, Any]] = []
        returned_ids: set[str] = set()
        for series in response.get("Results", {}).get("series", []):
            series_id = str(series.get("seriesID") or "")
            meta = config_map.get(series_id)
            if not meta:
                continue
            observations = []
            for row in series.get("data", []):
                period = base.bls_period(
                    str(row.get("year") or ""),
                    str(row.get("period") or ""),
                )
                value = base.safe_number(row.get("value"))
                if period and value is not None:
                    observations.append((period, value, row))
            observations.sort(key=lambda item: item[0])
            if not observations:
                continue

            returned_ids.add(series_id)
            latest = observations[-1]
            previous_value = observations[-2][1] if len(observations) > 1 else None
            footnotes = [
                note.get("text")
                for note in latest[2].get("footnotes", [])
                if isinstance(note, dict) and note.get("text")
            ]
            records.append(
                {
                    "id": series_id,
                    "kind": "series",
                    "name": meta["name"],
                    "group": meta["group"],
                    "period": latest[0],
                    "observedAt": f"{latest[0]}-01",
                    "value": latest[1],
                    "previous": previous_value,
                    "change": (
                        round(latest[1] - previous_value, 6)
                        if previous_value is not None
                        else None
                    ),
                    "unit": meta["unit"],
                    "frequency": meta["frequency"],
                    "preliminary": any(
                        "preliminary" in str(note).lower() for note in footnotes
                    ),
                    "footnotes": footnotes,
                    "sourceUrl": f"https://data.bls.gov/timeseries/{series_id}",
                }
            )

        source["records"] = sorted(records, key=lambda row: (row["group"], row["name"]))
        missing = [
            item["id"]
            for item in config.get("series", [])
            if item["id"] not in returned_ids
        ]
        if not records:
            raise ValueError("BLS returned no configured monthly observations")

        messages = [str(message) for message in response.get("message", []) if message]
        status = "partial" if missing else "current"
        detail = f"{len(records)} configured BLS series; {len(missing)} missing."
        if messages:
            detail += f" API advisory: {'; '.join(messages)[:240]}"
        return base.finalise_success(source, status=status, detail=detail)
    except Exception as exc:
        return base.finalise_failure(source, previous, exc)


base.collect_sec = collect_sec_by_cik
base.collect_bls = collect_bls_without_unused_calculations

if __name__ == "__main__":
    raise SystemExit(base.main())
