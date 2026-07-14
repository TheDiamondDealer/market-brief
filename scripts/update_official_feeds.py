#!/usr/bin/env python3
"""Collect free official economic, filing, energy and mineral-source observations.

The collector is deliberately defensive:
- one failed agency cannot erase another agency's data;
- missing free API keys produce explicit unavailable states;
- prior verified records are retained as stale on temporary failures;
- credentials never appear in generated data or diagnostics.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts" / "official_feeds_registry.json"
OUTPUT_PATH = ROOT / "site" / "data" / "official-feeds.json"
USER_AGENT = os.environ.get("OFFICIAL_FEEDS_USER_AGENT", "MarketBriefResearch/2.0 (+https://github.com/TheDiamondDealer/market-brief)")
STATUS_VALUES = {"current", "delayed", "stale", "failed", "unavailable", "partial", "unknown"}
SECRET_NAMES = ("EIA_API_KEY", "BEA_API_KEY", "CENSUS_API_KEY", "BLS_API_KEY")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def safe_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text or text.lower() in {"na", "n/a", "null", "none", "(d)", "(s)", "z"}:
        return None
    try:
        return round(float(text), 6)
    except ValueError:
        return None


def scrub(text: Any) -> str:
    rendered = str(text or "")
    for name in SECRET_NAMES:
        secret = os.environ.get(name)
        if secret:
            rendered = rendered.replace(secret, "[redacted]")
    rendered = re.sub(r"(?i)(api_key|apikey|userID|registrationkey)=([^&\s]+)", r"\1=[redacted]", rendered)
    rendered = re.sub(r"(?i)(api_key|apikey|userID|registrationkey)%3D[^&\s]+", r"\1%3D[redacted]", rendered)
    return rendered[:600]


def request_bytes(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 60) -> bytes:
    body = None
    merged = {"User-Agent": USER_AGENT, "Accept": "application/json,text/html;q=0.9,*/*;q=0.8"}
    if headers:
        merged.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=merged, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def request_json(*args: Any, **kwargs: Any) -> Any:
    return json.loads(request_bytes(*args, **kwargs).decode("utf-8-sig", errors="replace"))


def source_template(source_id: str, name: str, family: str, access: str, source_url: str, cadence: str, collected_at: str) -> dict[str, Any]:
    return {"id": source_id, "name": name, "family": family, "access": access, "status": "unknown", "observedAt": None, "collectedAt": collected_at, "lastSuccessfulAt": None, "expectedCadence": cadence, "sourceUrl": source_url, "detail": "", "error": None, "records": []}


def prior_source(previous: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    return next((row for row in previous.get("sources", []) if row.get("id") == source_id), None)


def finalise_success(source: dict[str, Any], *, status: str = "current", detail: str = "") -> dict[str, Any]:
    source["status"] = status if status in STATUS_VALUES else "unknown"
    source["detail"] = detail
    source["error"] = None
    source["lastSuccessfulAt"] = source["collectedAt"]
    observed = [str(row.get("observedAt") or row.get("filedAt") or "") for row in source["records"]]
    source["observedAt"] = max((value for value in observed if value), default=source["collectedAt"])
    return source


def finalise_failure(source: dict[str, Any], previous: dict[str, Any], error: Any, *, unavailable: bool = False) -> dict[str, Any]:
    prior = prior_source(previous, source["id"])
    message = scrub(error)
    if prior and prior.get("records"):
        source["records"] = prior["records"]
        source["observedAt"] = prior.get("observedAt")
        source["lastSuccessfulAt"] = prior.get("lastSuccessfulAt") or prior.get("collectedAt")
        source["status"] = "stale"
        source["detail"] = f"Retained {len(source['records'])} previously verified records."
    else:
        source["status"] = "unavailable" if unavailable else "failed"
        source["detail"] = "No verified records are currently available."
    source["error"] = message
    return source


def accession_compact(value: str) -> str:
    return re.sub(r"[^0-9]", "", value)


def sec_archives_url(cik: int, accession: str, primary_document: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_compact(accession)}/{primary_document}"


def collect_sec(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("sec-edgar", "SEC EDGAR company filings", "Company Filings", "No API key", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "Throughout each US business day", collected_at)
    try:
        ticker_payload = request_json("https://www.sec.gov/files/company_tickers.json")
        ticker_map: dict[str, dict[str, Any]] = {}
        entries = ticker_payload.values() if isinstance(ticker_payload, dict) else ticker_payload
        for entry in entries or []:
            if isinstance(entry, dict) and entry.get("ticker"):
                ticker_map[str(entry["ticker"]).upper()] = entry
        cutoff = (datetime.now(timezone.utc).date() - timedelta(days=int(config.get("lookbackDays", 180)))).isoformat()
        allowed_forms = set(config.get("forms", []))
        records: list[dict[str, Any]] = []
        missing: list[str] = []
        keys = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "act", "form", "fileNumber", "filmNumber", "items", "size", "isXBRL", "isInlineXBRL", "primaryDocument", "primaryDocDescription")
        for ticker in config.get("tickers", []):
            entry = ticker_map.get(str(ticker).upper())
            if not entry:
                missing.append(str(ticker))
                continue
            cik = int(entry["cik_str"])
            submissions = request_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
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
                accepted_raw = str(row.get("acceptanceDateTime") or "")
                accepted_at = accepted_raw
                if re.fullmatch(r"\d{14}", accepted_raw):
                    accepted_at = f"{accepted_raw[:4]}-{accepted_raw[4:6]}-{accepted_raw[6:8]}T{accepted_raw[8:10]}:{accepted_raw[10:12]}:{accepted_raw[12:14]}Z"
                records.append({"id": f"sec-{cik}-{accession_compact(accession)}", "kind": "filing", "name": row.get("primaryDocDescription") or f"{form} filing", "companyId": f"CIK{cik:010d}", "company": submissions.get("name") or entry.get("title") or ticker, "ticker": str(ticker).upper(), "form": form, "filedAt": filed_at, "acceptedAt": accepted_at or None, "observedAt": accepted_at or filed_at, "period": row.get("reportDate") or None, "accession": accession, "items": row.get("items") or None, "primaryDocument": primary_document, "title": row.get("primaryDocDescription") or f"{form} filing", "sourceUrl": sec_archives_url(cik, accession, primary_document)})
            time.sleep(0.11)
        records.sort(key=lambda item: (str(item.get("acceptedAt") or ""), str(item.get("filedAt") or "")), reverse=True)
        source["records"] = records[: int(config.get("maxRecords", 160))]
        status = "current" if source["records"] and not missing else "partial" if source["records"] else "failed"
        detail = f"{len(source['records'])} recent priority filings across {len(config.get('tickers', [])) - len(missing)} mapped companies."
        if missing:
            detail += f" Unmapped tickers: {', '.join(missing[:8])}."
        if not source["records"]:
            raise ValueError(detail)
        return finalise_success(source, status=status, detail=detail)
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def bls_period(year: str, period: str) -> str | None:
    if not re.fullmatch(r"M(0[1-9]|1[0-2])", period):
        return None
    return f"{year}-{period[1:]}"


def collect_bls(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("bls-public-data", "BLS labour and inflation series", "Macro", "No key required; free registration key optional", "https://www.bls.gov/developers/api_signature_v2.htm", "Monthly releases", collected_at)
    try:
        current_year = datetime.now(timezone.utc).year
        payload: dict[str, Any] = {"seriesid": [row["id"] for row in config.get("series", [])], "startyear": str(current_year - 2), "endyear": str(current_year), "calculations": True}
        registration_key = os.environ.get("BLS_API_KEY", "").strip()
        if registration_key:
            payload["registrationkey"] = registration_key
        response = request_json("https://api.bls.gov/publicAPI/v2/timeseries/data/", method="POST", payload=payload)
        if response.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError("; ".join(response.get("message", [])) or response.get("status"))
        config_map = {row["id"]: row for row in config.get("series", [])}
        records = []
        returned_ids = set()
        for series in response.get("Results", {}).get("series", []):
            series_id = str(series.get("seriesID") or "")
            meta = config_map.get(series_id)
            if not meta:
                continue
            observations = []
            for row in series.get("data", []):
                period = bls_period(str(row.get("year") or ""), str(row.get("period") or ""))
                value = safe_number(row.get("value"))
                if period and value is not None:
                    observations.append((period, value, row))
            observations.sort(key=lambda item: item[0])
            if not observations:
                continue
            returned_ids.add(series_id)
            latest = observations[-1]
            previous_value = observations[-2][1] if len(observations) > 1 else None
            footnotes = [note.get("text") for note in latest[2].get("footnotes", []) if isinstance(note, dict) and note.get("text")]
            records.append({"id": series_id, "kind": "series", "name": meta["name"], "group": meta["group"], "period": latest[0], "observedAt": f"{latest[0]}-01", "value": latest[1], "previous": previous_value, "change": round(latest[1] - previous_value, 6) if previous_value is not None else None, "unit": meta["unit"], "frequency": meta["frequency"], "preliminary": any("preliminary" in str(note).lower() for note in footnotes), "footnotes": footnotes, "sourceUrl": f"https://data.bls.gov/timeseries/{series_id}"})
        source["records"] = sorted(records, key=lambda row: (row["group"], row["name"]))
        missing = [item["id"] for item in config.get("series", []) if item["id"] not in returned_ids]
        if not records:
            raise ValueError("BLS returned no configured monthly observations")
        status = "partial" if missing or response.get("message") else "current"
        detail = f"{len(records)} configured BLS series; {len(missing)} missing."
        if response.get("message"):
            detail += f" API message: {'; '.join(response['message'])[:240]}"
        return finalise_success(source, status=status, detail=detail)
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def numeric_field(row: dict[str, Any]) -> tuple[str | None, float | None]:
    excluded = {"period", "series", "series-description", "seriesDescription", "name", "unit", "units", "product", "product-name", "area-name", "process-name", "duoarea", "area", "process"}
    for key, value in row.items():
        if key in excluded or key.endswith("-units"):
            continue
        number = safe_number(value)
        if number is not None:
            return key, number
    return None, None


def collect_eia(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("eia-energy", "EIA oil and natural-gas fundamentals", "Energy", "Free API key required", "https://www.eia.gov/opendata/", "Weekly and monthly, series dependent", collected_at)
    api_key = os.environ.get("EIA_API_KEY", "").strip()
    if not api_key:
        return finalise_failure(source, previous, "EIA_API_KEY is not configured", unavailable=True)
    try:
        records = []
        failures = []
        for meta in config.get("series", []):
            series_id = meta["id"]
            try:
                url = f"https://api.eia.gov/v2/seriesid/{urllib.parse.quote(series_id, safe='')}?" + urllib.parse.urlencode({"api_key": api_key, "length": "12"})
                payload = request_json(url)
                rows = payload.get("response", {}).get("data", [])
                parsed = []
                description = ""
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    description = str(row.get("series-description") or row.get("seriesDescription") or description)
                    field, value = numeric_field(row)
                    period = str(row.get("period") or "")
                    if period and value is not None:
                        parsed.append((period, value, field, row))
                parsed.sort(key=lambda item: item[0])
                if not parsed:
                    raise ValueError("no numeric observations")
                expected = [term.lower() for term in meta.get("expectedTerms", [])]
                identity_text = f"{description} {json.dumps(rows[0] if rows else {})}".lower()
                if expected and not all(term in identity_text for term in expected):
                    raise ValueError(f"series identity did not contain expected terms {expected}; description={description!r}")
                latest = parsed[-1]
                prior_value = parsed[-2][1] if len(parsed) > 1 else None
                unit = latest[3].get(f"{latest[2]}-units") or latest[3].get("units") or latest[3].get("unit") or meta.get("unit")
                records.append({"id": series_id, "kind": "series", "name": meta["name"], "group": meta["group"], "period": latest[0], "observedAt": latest[0], "value": latest[1], "previous": prior_value, "change": round(latest[1] - prior_value, 6) if prior_value is not None else None, "unit": unit, "frequency": meta["frequency"], "officialDescription": description or None, "sourceUrl": f"https://www.eia.gov/opendata/browser/#/series/{urllib.parse.quote(series_id, safe='')}"})
            except Exception as exc:
                failures.append(f"{series_id}: {scrub(exc)}")
            time.sleep(0.15)
        source["records"] = records
        if not records:
            raise ValueError("; ".join(failures) or "No EIA series succeeded")
        source = finalise_success(source, status="partial" if failures else "current", detail=f"{len(records)} verified EIA series; {len(failures)} failed.")
        source["error"] = "; ".join(failures)[:600] if failures else None
        return source
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def bea_data_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("BEAAPI", {}).get("Results", {})
    if isinstance(results, list):
        for result in results:
            if isinstance(result, dict) and isinstance(result.get("Data"), list):
                return result["Data"]
    if isinstance(results, dict) and isinstance(results.get("Data"), list):
        return results["Data"]
    errors = results.get("Error") if isinstance(results, dict) else None
    raise ValueError(errors or "BEA response contained no data rows")


def collect_bea(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("bea-nipa", "BEA national accounts", "Macro", "Free API key required", "https://apps.bea.gov/api/", "Monthly or quarterly, table dependent", collected_at)
    api_key = os.environ.get("BEA_API_KEY", "").strip()
    if not api_key:
        return finalise_failure(source, previous, "BEA_API_KEY is not configured", unavailable=True)
    try:
        current_year = datetime.now(timezone.utc).year
        records = []
        failures = []
        for table in config.get("tables", []):
            try:
                params = {"UserID": api_key, "method": "GetData", "datasetname": "NIPA", "TableName": table["table"], "Frequency": table["frequency"], "Year": f"{current_year-2},{current_year-1},{current_year}", "ResultFormat": "JSON"}
                rows = bea_data_rows(request_json("https://apps.bea.gov/api/data?" + urllib.parse.urlencode(params)))
                selected: dict[str, dict[str, Any]] = {}
                patterns = [pattern.lower() for pattern in table.get("patterns", [])]
                for row in rows:
                    description = html.unescape(str(row.get("LineDescription") or "")).strip()
                    if patterns and not any(pattern in description.lower() for pattern in patterns):
                        continue
                    value = safe_number(row.get("DataValue"))
                    period = str(row.get("TimePeriod") or "")
                    if value is None or not period:
                        continue
                    key = str(row.get("LineNumber") or description)
                    current = selected.get(key)
                    if not current or period > str(current.get("period")):
                        selected[key] = {"id": f"{table['table']}-{key}", "kind": "series", "name": description, "group": table["name"], "period": period, "observedAt": period, "value": value, "unit": row.get("UNIT_MULT") and f"10^{row.get('UNIT_MULT')} {row.get('CL_UNIT', '')}".strip() or row.get("CL_UNIT") or None, "frequency": table["frequency"], "table": table["table"], "lineNumber": row.get("LineNumber"), "sourceUrl": f"https://apps.bea.gov/iTable/?ReqID=19&step=3&isuri=1&nipa_table_list={table['table']}"}
                if not selected:
                    raise ValueError("no configured line descriptions matched")
                records.extend(selected.values())
            except Exception as exc:
                failures.append(f"{table['table']}: {scrub(exc)}")
            time.sleep(0.2)
        source["records"] = records
        if not records:
            raise ValueError("; ".join(failures) or "No BEA tables succeeded")
        source = finalise_success(source, status="partial" if failures else "current", detail=f"{len(records)} BEA table lines; {len(failures)} tables failed.")
        source["error"] = "; ".join(failures)[:600] if failures else None
        return source
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def collect_census(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("census-eits", "Census economic indicators", "Macro", "Free API key required", "https://www.census.gov/data/developers/data-sets/economic-indicators.html", "Monthly or quarterly, dataset dependent", collected_at)
    api_key = os.environ.get("CENSUS_API_KEY", "").strip()
    if not api_key:
        return finalise_failure(source, previous, "CENSUS_API_KEY is not configured", unavailable=True)
    try:
        start_year = datetime.now(timezone.utc).year - 1
        records = []
        failures = []
        for dataset in config.get("datasets", []):
            try:
                params = {"get": "cell_value,data_type_code,time_slot_id,category_code,seasonally_adj", "time": f"from {start_year}", "key": api_key}
                payload = request_json(f"https://api.census.gov/data/timeseries/eits/{dataset['id']}?" + urllib.parse.urlencode(params))
                if not isinstance(payload, list) or len(payload) < 2:
                    raise ValueError("no rows")
                headers = payload[0]
                candidates = []
                for values in payload[1:]:
                    if not isinstance(values, list):
                        continue
                    row = dict(zip(headers, values))
                    value = safe_number(row.get("cell_value"))
                    period = str(row.get("time") or "")
                    if value is None or not period:
                        continue
                    candidates.append({"id": f"{dataset['id']}-{row.get('data_type_code')}-{row.get('category_code')}-{row.get('seasonally_adj')}", "kind": "coded-series", "name": f"{dataset['name']} · {row.get('data_type_code')} / {row.get('category_code')}", "group": dataset["group"], "period": period, "observedAt": period, "value": value, "unit": "As defined by Census data dictionary", "frequency": dataset["frequency"], "dataTypeCode": row.get("data_type_code"), "categoryCode": row.get("category_code"), "seasonallyAdjusted": row.get("seasonally_adj"), "timeSlotId": row.get("time_slot_id"), "sourceUrl": f"https://api.census.gov/data/timeseries/eits/{dataset['id']}.html"})
                if not candidates:
                    raise ValueError("no numeric rows")
                candidates.sort(key=lambda item: str(item["period"]), reverse=True)
                latest_period = candidates[0]["period"]
                records.extend([row for row in candidates if row["period"] == latest_period][:12])
            except Exception as exc:
                failures.append(f"{dataset['id']}: {scrub(exc)}")
            time.sleep(0.15)
        source["records"] = records
        if not records:
            raise ValueError("; ".join(failures) or "No Census datasets succeeded")
        source = finalise_success(source, status="partial" if failures else "current", detail=f"{len(records)} latest coded Census observations; {len(failures)} datasets failed. Codes remain unexpanded until the official dictionary is joined.")
        source["error"] = "; ".join(failures)[:600] if failures else None
        return source
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def collect_usgs(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template("usgs-minerals", config.get("name", "USGS Mineral Commodity Summaries"), "Critical Minerals", "No API key", config["page"], config.get("frequency", "Annual"), collected_at)
    try:
        raw = request_bytes(config["page"], headers={"Accept": "text/html"}).decode("utf-8", errors="replace")
        text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
        text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"\s+", " ", text)
        years = [int(value) for value in re.findall(r"Mineral Commodity Summaries\s+(20\d{2})", text)]
        if not years:
            raise ValueError("current Mineral Commodity Summaries year not found")
        year = max(years)
        source["records"] = [{"id": f"usgs-mcs-{year}", "kind": "release", "name": f"Mineral Commodity Summaries {year}", "group": "Critical Minerals", "period": str(year), "observedAt": f"{year}-01-01", "value": None, "unit": None, "frequency": "Annual", "detail": "Annual government summary covering domestic industry, government programs, tariffs and five-year salient statistics for more than 90 minerals and materials.", "sourceUrl": config["page"]}]
        status = "current" if year >= datetime.now(timezone.utc).year - 1 else "stale"
        return finalise_success(source, status=status, detail=f"Latest official annual edition detected: {year}. Structured mineral values are not estimated from the PDF.")
    except Exception as exc:
        return finalise_failure(source, previous, exc)


def validate_output(data: dict[str, Any]) -> None:
    if data.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    sources = data.get("sources")
    if not isinstance(sources, list) or len(sources) != 6:
        raise ValueError("exactly six official sources are required")
    ids = [source.get("id") for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source ids")
    for source in sources:
        if source.get("status") not in STATUS_VALUES:
            raise ValueError(f"unknown status for {source.get('id')}")
        if not isinstance(source.get("records"), list):
            raise ValueError(f"records must be a list for {source.get('id')}")
        record_ids = [row.get("id") for row in source["records"] if isinstance(row, dict)]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"duplicate record ids for {source.get('id')}")
    rendered = json.dumps(data, ensure_ascii=False)
    for name in SECRET_NAMES:
        secret = os.environ.get(name)
        if secret and secret in rendered:
            raise ValueError(f"generated data contains {name}")
    if re.search(r"(?i)(api_key|apikey|userid|registrationkey)=[^&\s\[\]]+", rendered):
        raise ValueError("generated data appears to contain a credential query parameter")


def build_dataset(registry: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    collected_at = utc_now()
    collectors: list[tuple[str, Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]]]] = [("sec", collect_sec), ("bls", collect_bls), ("eia", collect_eia), ("bea", collect_bea), ("census", collect_census), ("usgs", collect_usgs)]
    sources = [collector(registry[key], previous, collected_at) for key, collector in collectors]
    successful = sum(1 for source in sources if source["status"] in {"current", "partial", "delayed"})
    unavailable = sum(1 for source in sources if source["status"] == "unavailable")
    failed = sum(1 for source in sources if source["status"] in {"failed", "stale"})
    if successful == len(sources):
        overall = "current" if all(source["status"] == "current" for source in sources) else "partial"
    elif successful:
        overall = "partial"
    elif unavailable == len(sources):
        overall = "unavailable"
    else:
        overall = "failed"
    last_successes = [source.get("lastSuccessfulAt") for source in sources if source.get("lastSuccessfulAt")]
    data = {"schemaVersion": 1, "generatedAtUtc": collected_at, "collection": {"status": overall, "successCount": successful, "failureCount": failed, "unavailableCount": unavailable, "lastSuccessfulAt": max(last_successes) if last_successes else None, "errors": [f"{source['name']}: {source['error']}" for source in sources if source.get("error")]}, "sources": sources, "methodology": {"observations": "Each agency keeps its own observation period, collection time, cadence and failure state.", "retention": "A temporary source failure retains previously verified records as stale; it never silently replaces populated history with an empty result.", "keys": "EIA, BEA and Census use free API keys stored only in GitHub Actions Secrets. BLS can run without a key; SEC and USGS require no key.", "consensus": "No market consensus estimates are created by these official feeds.", "censusCodes": "Census records preserve official data-type and category codes until a verified dictionary join is available.", "usgs": "USGS integration tracks the official annual release and does not OCR or estimate values from PDF tables."}}
    validate_output(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    args = parser.parse_args()
    registry = load_json(args.registry, {})
    if not registry:
        print(f"Unable to load registry: {args.registry}", file=sys.stderr)
        return 1
    previous = load_json(args.output, {})
    dataset = build_dataset(registry, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Official feeds status={dataset['collection']['status']}; successful={dataset['collection']['successCount']}; unavailable={dataset['collection']['unavailableCount']}; failed/stale={dataset['collection']['failureCount']}")
    for source in dataset["sources"]:
        print(f"- {source['id']}: {source['status']} ({len(source['records'])} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
