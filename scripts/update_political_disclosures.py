#!/usr/bin/env python3
"""Collect and retain public congressional transaction disclosures.

Primary sources:
- House Clerk annual disclosure indexes and PTR PDFs.
- Senate eFD search and PTR report pages after accepting the statutory terms.

The output is a static JSON cache plus a browser-ready JavaScript hydrator. Existing
verified trades are retained if a source is temporarily unavailable. The portfolio is
explicitly transaction-derived until an annual holdings baseline is available.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pdfplumber
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "site" / "data" / "political-disclosures.json"
JS_PATH = ROOT / "site" / "political-data.js"
START_YEAR = int(os.getenv("POLITICAL_DISCLOSURE_START_YEAR", "2012"))
REQUEST_TIMEOUT = int(os.getenv("POLITICAL_DISCLOSURE_TIMEOUT", "45"))
REQUIRE_TRADES = os.getenv("POLITICAL_REQUIRE_TRADES", "0") == "1"
USER_AGENT = "MarketBriefResearch/1.0 (+https://thediamonddealer.github.io/market-brief/)"
HOUSE_INDEX = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.txt"
HOUSE_PTR_URLS = (
    "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf",
    "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{doc_id}.pdf",
)
SENATE_BASE = "https://efdsearch.senate.gov"

TRACKERS: dict[str, dict[str, Any]] = {
    "pelosi": {"name": "Nancy Pelosi", "chamber": "House", "last": "Pelosi", "first": ["Nancy"]},
    "tim-moore": {"name": "Tim Moore", "chamber": "House", "last": "Moore", "first": ["Tim", "Timothy"]},
    "dan-meuser": {"name": "Dan Meuser", "chamber": "House", "last": "Meuser", "first": ["Dan", "Daniel"]},
    "cleo-fields": {"name": "Cleo Fields", "chamber": "House", "last": "Fields", "first": ["Cleo"]},
    "rob-bresnahan": {"name": "Rob Bresnahan", "chamber": "House", "last": "Bresnahan", "first": ["Rob", "Robert"]},
    "donald-beyer": {"name": "Donald Beyer", "chamber": "House", "last": "Beyer", "first": ["Donald", "Don"]},
    "josh-gottheimer": {"name": "Josh Gottheimer", "chamber": "House", "last": "Gottheimer", "first": ["Josh", "Joshua"]},
    "sheldon-whitehouse": {"name": "Sheldon Whitehouse", "chamber": "Senate", "last": "Whitehouse", "first": ["Sheldon"]},
}

AMOUNT_BUCKETS = {
    "$1,001 - $15,000": (1001, 15000),
    "$15,001 - $50,000": (15001, 50000),
    "$50,001 - $100,000": (50001, 100000),
    "$100,001 - $250,000": (100001, 250000),
    "$250,001 - $500,000": (250001, 500000),
    "$500,001 - $1,000,000": (500001, 1000000),
    "$1,000,001 - $5,000,000": (1000001, 5000000),
    "$5,000,001 - $25,000,000": (5000001, 25000000),
    "$25,000,001 - $50,000,000": (25000001, 50000000),
    "Over $50,000,000": (50000001, None),
}


class CollectionError(RuntimeError):
    pass


@dataclass
class Filing:
    tracker_id: str
    chamber: str
    filing_id: str
    filed: str
    report_url: str
    year: int


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u00a0", " ")).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", clean(value).lower())


def iso_date(value: Any) -> str | None:
    text = clean(value)
    if not text:
        return None
    text = re.sub(r"\s+00:00:00$", "", text)
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if match:
        year = int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return date(year, int(match.group(1)), int(match.group(2))).isoformat()
        except ValueError:
            return None
    return None


def days_between(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return None


def fetch(session: requests.Session, url: str, *, method: str = "GET", **kwargs: Any) -> requests.Response:
    response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    response.raise_for_status()
    return response


def flexible_get(row: dict[str, Any], *keys: str) -> str:
    mapped = {norm(key): value for key, value in row.items()}
    for key in keys:
        value = mapped.get(norm(key))
        if clean(value):
            return clean(value)
    return ""


def person_matches(first: str, last: str, config: dict[str, Any]) -> bool:
    if norm(last) != norm(config["last"]):
        return False
    normalized_first = norm(first)
    return any(normalized_first.startswith(norm(alias)) for alias in config["first"])


def read_house_index(session: requests.Session, year: int) -> list[dict[str, str]]:
    response = fetch(session, HOUSE_INDEX.format(year=year))
    text = response.content.decode("utf-8-sig", errors="replace").replace("\x00", "")
    sample = text[:4096]
    delimiter = "\t" if sample.count("\t") >= sample.count("|") else "|"
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return [{clean(k): clean(v) for k, v in row.items() if k is not None} for row in reader]


def discover_house_filings(session: requests.Session) -> tuple[list[Filing], list[str]]:
    filings: list[Filing] = []
    errors: list[str] = []
    current_year = datetime.now(timezone.utc).year
    house_trackers = {key: value for key, value in TRACKERS.items() if value["chamber"] == "House"}
    for year in range(START_YEAR, current_year + 1):
        try:
            rows = read_house_index(session, year)
        except Exception as exc:
            errors.append(f"House index {year}: {exc}")
            continue
        for row in rows:
            filing_type = flexible_get(row, "FilingType", "Filing Type", "ReportType", "Report Type")
            if filing_type and filing_type.upper() not in {"P", "PTR", "PERIODIC TRANSACTION REPORT"}:
                continue
            first = flexible_get(row, "First", "FirstName", "First Name")
            last = flexible_get(row, "Last", "LastName", "Last Name")
            doc_id = flexible_get(row, "DocID", "DocumentID", "Document Id", "Document")
            filed = iso_date(flexible_get(row, "FilingDate", "Filing Date", "Date"))
            if not doc_id or not filed:
                continue
            for tracker_id, config in house_trackers.items():
                if person_matches(first, last, config):
                    url = HOUSE_PTR_URLS[0].format(year=year, doc_id=doc_id)
                    filings.append(Filing(tracker_id, "House", doc_id, filed, url, year))
                    break
    unique = {(item.tracker_id, item.filing_id): item for item in filings}
    return sorted(unique.values(), key=lambda item: (item.filed, item.filing_id)), errors


def map_transaction_type(value: str) -> str:
    text = clean(value)
    upper = text.upper()
    if upper.startswith("P") or "PURCHASE" in upper:
        return "Purchase"
    if upper.startswith("S") or "SALE" in upper:
        if "PARTIAL" in upper:
            return "Sale (partial)"
        if "FULL" in upper:
            return "Sale (full)"
        return "Sale"
    if upper.startswith("E") or "EXCHANGE" in upper:
        return "Exchange"
    return text or "Other"


def extract_ticker(asset: str, explicit: str = "") -> str:
    explicit = clean(explicit).upper()
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,7}", explicit) and explicit not in {"N/A", "NA", "--"}:
        return explicit
    for pattern in (r"\(([A-Z][A-Z0-9.\-]{0,7})\)", r"^([A-Z][A-Z0-9.\-]{0,7})\s+-\s+"):
        match = re.search(pattern, asset)
        if match and match.group(1) not in {"IRA", "LLC", "ETF"}:
            return match.group(1)
    return ""


def transaction_asset(asset: str, ticker: str) -> str:
    asset = clean(asset)
    ticker = clean(ticker).upper()
    if ticker and ticker not in asset.upper():
        return f"{ticker} — {asset}"
    return asset or ticker or "Unspecified asset"


def stable_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(clean(part) for part in parts).encode("utf-8")).hexdigest()[:24]


def table_header_map(row: Iterable[Any]) -> dict[str, int]:
    aliases = {
        "id": {"id", "transactionid"},
        "owner": {"owner"},
        "asset": {"asset", "assetdescription", "assetname"},
        "ticker": {"ticker"},
        "type": {"transactiontype", "type"},
        "date": {"date", "transactiondate"},
        "notification": {"notificationdate", "notified"},
        "amount": {"amount", "amountrange"},
    }
    result: dict[str, int] = {}
    for index, cell in enumerate(row):
        key = norm(cell)
        for canonical, values in aliases.items():
            if key in values or any(value and value in key for value in values if len(value) > 4):
                result.setdefault(canonical, index)
    return result


def parse_house_pdf(content: bytes, filing: Filing) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for table in tables:
                header: dict[str, int] | None = None
                for raw_row in table:
                    row = [clean(cell) for cell in (raw_row or [])]
                    candidate = table_header_map(row)
                    if "asset" in candidate and "type" in candidate and "date" in candidate:
                        header = candidate
                        continue
                    if not header:
                        continue

                    def cell(name: str) -> str:
                        index = header.get(name)
                        return row[index] if index is not None and index < len(row) else ""

                    asset_raw = cell("asset")
                    traded = iso_date(cell("date"))
                    tx_type = map_transaction_type(cell("type"))
                    amount = cell("amount")
                    if not asset_raw or not traded or tx_type == "Other" or not amount:
                        continue
                    ticker = extract_ticker(asset_raw, cell("ticker"))
                    owner = cell("owner") or "Not specified"
                    transaction_id = cell("id") or str(len(trades) + 1)
                    trade_id = stable_id("house", filing.filing_id, transaction_id, asset_raw, traded, amount)
                    lag = days_between(traded, filing.filed)
                    trades.append({
                        "id": trade_id,
                        "filingId": filing.filing_id,
                        "asset": transaction_asset(asset_raw, ticker),
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
    return list({trade["id"]: trade for trade in trades}.values())


def download_house_pdf(session: requests.Session, filing: Filing) -> tuple[bytes, str]:
    errors: list[str] = []
    for template in HOUSE_PTR_URLS:
        url = template.format(year=filing.year, doc_id=filing.filing_id)
        try:
            response = fetch(session, url)
            if not response.content.startswith(b"%PDF"):
                raise CollectionError("response is not a PDF")
            filing.report_url = url
            return response.content, url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise CollectionError("; ".join(errors))


def csrf_token(session: requests.Session, html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    field = soup.select_one('input[name="csrfmiddlewaretoken"]')
    return clean(field.get("value")) if field else clean(session.cookies.get("csrftoken"))


def senate_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/json"})
    home_url = f"{SENATE_BASE}/search/home/"
    home = fetch(session, home_url)
    token = csrf_token(session, home.text)
    if not token:
        raise CollectionError("Senate eFD CSRF token not found")
    payload = {"csrfmiddlewaretoken": token, "prohibition_agreement": "1"}
    response = fetch(session, home_url, method="POST", data=payload, headers={"Referer": home_url, "X-CSRFToken": token})
    if "prohibition_agreement" in response.text and "/search/report/" not in response.url:
        raise CollectionError("Senate eFD terms agreement was not accepted")
    return session


def discover_senate_filings(session: requests.Session, tracker_id: str, config: dict[str, Any]) -> list[Filing]:
    token = clean(session.cookies.get("csrftoken"))
    current_year = datetime.now(timezone.utc).year
    endpoint = f"{SENATE_BASE}/search/report/data/"
    filings: list[Filing] = []
    start = 0
    while True:
        payload = {
            "start": str(start), "length": "100", "report_types": "[11]", "filer_types": "[]",
            "submitted_start_date": f"01/01/{START_YEAR} 00:00:00",
            "submitted_end_date": f"12/31/{current_year} 23:59:59",
            "candidate_state": "", "senator_state": "", "office_id": "",
            "first_name": config["first"][0], "last_name": config["last"],
        }
        response = fetch(session, endpoint, method="POST", data=payload,
                         headers={"Referer": f"{SENATE_BASE}/search/report/", "X-CSRFToken": token})
        body = response.json()
        records = body.get("data", []) if isinstance(body, dict) else []
        for record in records:
            if isinstance(record, list):
                text = " ".join(clean(value) for value in record)
                soup = BeautifulSoup(text, "html.parser")
                link = soup.find("a", href=True)
                report_url = requests.compat.urljoin(SENATE_BASE, link["href"]) if link else ""
                filed = next((iso_date(value) for value in record if iso_date(value)), None)
                filing_id = report_url.rstrip("/").split("/")[-1] if report_url else stable_id(text)
            elif isinstance(record, dict):
                link_value = flexible_get(record, "link", "url", "report_url", "report").replace("&amp;", "&")
                soup = BeautifulSoup(link_value, "html.parser")
                link = soup.find("a", href=True)
                href = link["href"] if link else link_value
                report_url = requests.compat.urljoin(SENATE_BASE, href)
                filed = iso_date(flexible_get(record, "date_received", "filed", "filing_date", "date"))
                filing_id = flexible_get(record, "id", "report_id") or report_url.rstrip("/").split("/")[-1]
            else:
                continue
            if report_url and filed and "/ptr/" in report_url.lower():
                filings.append(Filing(tracker_id, "Senate", filing_id, filed, report_url, int(filed[:4])))
        total = int(body.get("recordsFiltered", len(records))) if isinstance(body, dict) else len(records)
        start += len(records)
        if not records or start >= total:
            break
    unique = {(item.tracker_id, item.filing_id): item for item in filings}
    return list(unique.values())


def parse_senate_report(session: requests.Session, filing: Filing) -> list[dict[str, Any]]:
    response = fetch(session, filing.report_url, headers={"Referer": f"{SENATE_BASE}/search/report/"})
    soup = BeautifulSoup(response.text, "html.parser")
    trades: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        headers = [clean(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        mapping = table_header_map(headers)
        if "asset" not in mapping and "ticker" not in mapping:
            continue
        if "date" not in mapping or "type" not in mapping:
            continue
        for index, row_node in enumerate(table.select("tbody tr"), start=1):
            cells = [clean(cell.get_text(" ", strip=True)) for cell in row_node.find_all(["td", "th"])]

            def cell(name: str) -> str:
                position = mapping.get(name)
                return cells[position] if position is not None and position < len(cells) else ""

            asset_raw = cell("asset")
            ticker = extract_ticker(asset_raw, cell("ticker"))
            traded = iso_date(cell("date"))
            tx_type = map_transaction_type(cell("type"))
            amount = cell("amount")
            if not (asset_raw or ticker) or not traded or tx_type == "Other" or not amount:
                continue
            owner = cell("owner") or "Not specified"
            trade_id = stable_id("senate", filing.filing_id, index, asset_raw, ticker, traded, amount)
            lag = days_between(traded, filing.filed)
            trades.append({
                "id": trade_id,
                "filingId": filing.filing_id,
                "asset": transaction_asset(asset_raw, ticker),
                "ticker": ticker,
                "type": tx_type,
                "owner": owner,
                "traded": traded,
                "filed": filing.filed,
                "lag": f"{lag} days" if lag is not None else "—",
                "lagDays": lag,
                "amount": amount,
                "source": "Official Senate Periodic Transaction Report",
                "sourceUrl": filing.report_url,
            })
    return list({trade["id"]: trade for trade in trades}.values())


def amount_bounds(text: str) -> tuple[int | None, int | None]:
    cleaned = clean(text).replace("–", "-")
    for label, bounds in AMOUNT_BUCKETS.items():
        if norm(label) == norm(cleaned):
            return bounds
    numbers = [int(value.replace(",", "")) for value in re.findall(r"\$?([0-9][0-9,]*)", cleaned)]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return None, None


def money(value: int | None) -> str:
    if value is None:
        return "open-ended"
    return f"${value:,.0f}"


def build_portfolio(trades: list[dict[str, Any]], generated_human: str) -> dict[str, Any]:
    ledger: dict[tuple[str, str], dict[str, Any]] = {}
    for trade in sorted(trades, key=lambda item: (item.get("traded", ""), item.get("filed", ""), item.get("id", ""))):
        key = (trade.get("ticker") or norm(trade.get("asset")), trade.get("owner") or "Not specified")
        entry = ledger.setdefault(key, {
            "asset": trade.get("asset") or "Unspecified asset", "owner": trade.get("owner") or "Not specified",
            "minimum": 0, "maximum": 0, "unknown": False, "status": "Transaction-derived open",
            "lastActivity": trade.get("traded"), "sourceUrl": trade.get("sourceUrl"),
        })
        low, high = amount_bounds(trade.get("amount", ""))
        tx_type = str(trade.get("type", "")).lower()
        if "purchase" in tx_type or "exchange" in tx_type:
            if low is None:
                entry["unknown"] = True
            else:
                entry["minimum"] += low
                if high is None:
                    entry["unknown"] = True
                else:
                    entry["maximum"] += high
            entry["status"] = "Transaction-derived open"
        elif "sale" in tx_type:
            if "full" in tx_type:
                entry["minimum"] = 0
                entry["maximum"] = 0
                entry["status"] = "Closed by reported full sale"
            elif low is not None:
                entry["minimum"] = max(0, entry["minimum"] - (high or low))
                entry["maximum"] = max(0, entry["maximum"] - low)
                entry["status"] = "Reduced / baseline uncertain" if entry["maximum"] else "Potentially closed"
            else:
                entry["unknown"] = True
                entry["status"] = "Sale reported / baseline unresolved"
        entry["lastActivity"] = trade.get("traded")
        entry["sourceUrl"] = trade.get("sourceUrl")
        entry["asset"] = trade.get("asset") or entry["asset"]

    holdings: list[dict[str, Any]] = []
    for entry in ledger.values():
        if entry["minimum"] == 0 and entry["maximum"] == 0 and not entry["unknown"] and "closed" in entry["status"].lower():
            continue
        if entry["unknown"] and entry["minimum"] == 0 and entry["maximum"] == 0:
            amount = "Range unresolved without annual baseline"
        elif entry["unknown"]:
            amount = f"At least {money(entry['minimum'])}; upper bound unresolved"
        else:
            amount = f"{money(entry['minimum'])}–{money(entry['maximum'])} disclosed activity"
        holdings.append({
            "asset": entry["asset"], "owner": entry["owner"], "amount": amount,
            "status": entry["status"], "lastActivity": entry["lastActivity"],
            "confidence": "Low — PTR-derived only", "sourceUrl": entry["sourceUrl"],
        })
    holdings.sort(key=lambda item: item.get("lastActivity", ""), reverse=True)
    return {
        "updated": generated_human,
        "status": "Transaction-derived estimate",
        "basis": "Built from verified Periodic Transaction Reports. It does not yet include a complete annual holdings baseline, so sales and pre-existing positions may be unresolved.",
        "valuation": "Amounts are statutory disclosure ranges, not share counts or current market values.",
        "holdings": holdings,
    }


def load_previous() -> dict[str, Any]:
    if not JSON_PATH.exists():
        return {"trackers": {}}
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"trackers": {}}


def merge_trades(previous: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {trade.get("id") or stable_id(json.dumps(trade, sort_keys=True)): trade for trade in previous}
    for trade in incoming:
        merged[trade["id"]] = trade
    return sorted(merged.values(), key=lambda item: (item.get("traded", ""), item.get("filed", ""), item.get("id", "")), reverse=True)


def browser_js(dataset: dict[str, Any]) -> str:
    payload = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"))
    return f"""window.politicalDisclosureData={payload};
(() => {{
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;
  const source = window.politicalDisclosureData || {{trackers:{{}}}};
  Object.entries(source.trackers || {{}}).forEach(([id, imported]) => {{
    const tracker = fallback.trackers[id];
    if (!tracker) return;
    tracker.trades = Array.isArray(imported.trades) ? imported.trades : [];
    tracker.updated = imported.updated || source.generatedAtHuman || tracker.updated;
    tracker.importStatus = imported.status;
    tracker.emptyMessage = imported.emptyMessage || tracker.emptyMessage;
    tracker.portfolio = Object.assign({{}}, tracker.portfolio || {{}}, imported.portfolio || {{}});
    const latest = tracker.trades.map((trade) => trade.filed).filter(Boolean).sort().reverse()[0] || 'No verified filing imported';
    tracker.stats = [
      ['Source', imported.chamber === 'Senate' ? 'Senate eFD' : 'House Clerk'],
      ['Trades retained', String(tracker.trades.length)],
      ['Latest filing', latest],
      ['Import status', imported.status || 'Unknown']
    ];
  }});
}})();
"""


def main() -> int:
    previous = load_previous()
    generated = datetime.now(ZoneInfo("Australia/Melbourne"))
    generated_iso = generated.isoformat(timespec="seconds")
    generated_human = generated.strftime("%d %B %Y, %H:%M %Z")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/plain,text/html,application/pdf,application/json"})

    house_filings, house_errors = discover_house_filings(session)
    previous_trackers = previous.get("trackers", {})
    incoming_by_tracker: dict[str, list[dict[str, Any]]] = {key: [] for key in TRACKERS}
    known_filing_ids = {
        tracker_id: {trade.get("filingId") for trade in previous_trackers.get(tracker_id, {}).get("trades", [])}
        for tracker_id in TRACKERS
    }
    parse_errors: list[str] = []

    for filing in house_filings:
        if filing.filing_id in known_filing_ids.get(filing.tracker_id, set()):
            continue
        try:
            content, _ = download_house_pdf(session, filing)
            trades = parse_house_pdf(content, filing)
            if not trades:
                raise CollectionError("no transaction rows parsed")
            incoming_by_tracker[filing.tracker_id].extend(trades)
            time.sleep(0.08)
        except Exception as exc:
            parse_errors.append(f"House {filing.tracker_id} {filing.filing_id}: {exc}")

    senate_errors: list[str] = []
    try:
        senate = senate_session()
        for tracker_id, config in TRACKERS.items():
            if config["chamber"] != "Senate":
                continue
            try:
                filings = discover_senate_filings(senate, tracker_id, config)
                for filing in filings:
                    if filing.filing_id in known_filing_ids.get(tracker_id, set()):
                        continue
                    trades = parse_senate_report(senate, filing)
                    if not trades:
                        raise CollectionError(f"no transaction rows parsed from {filing.report_url}")
                    incoming_by_tracker[tracker_id].extend(trades)
                    time.sleep(0.08)
            except Exception as exc:
                senate_errors.append(f"Senate {tracker_id}: {exc}")
    except Exception as exc:
        senate_errors.append(f"Senate session: {exc}")

    trackers_output: dict[str, Any] = {}
    for tracker_id, config in TRACKERS.items():
        old = previous_trackers.get(tracker_id, {})
        trades = merge_trades(old.get("trades", []), incoming_by_tracker.get(tracker_id, []))
        chamber_errors = senate_errors if config["chamber"] == "Senate" else house_errors + parse_errors
        relevant_errors = [error for error in chamber_errors if tracker_id in error or "index" in error or "session" in error]
        if trades:
            status = "Current" if not relevant_errors else "Partial — previous verified records retained"
            empty_message = ""
        else:
            status = "Unavailable — no verified transactions parsed"
            empty_message = "No verified transactions were parsed. Check the source-status message and workflow logs; existing data is never fabricated."
        trackers_output[tracker_id] = {
            "name": config["name"], "chamber": config["chamber"], "updated": generated_human,
            "status": status, "trades": trades, "portfolio": build_portfolio(trades, generated_human),
            "emptyMessage": empty_message,
            "sourceStatus": {"errors": relevant_errors[:12], "newTrades": len(incoming_by_tracker.get(tracker_id, []))},
        }

    dataset = {
        "generatedAt": generated_iso,
        "generatedAtHuman": generated_human,
        "methodology": "Official House PTR PDFs and Senate eFD PTR pages. Existing verified trades are retained during source failures. Portfolio estimates are PTR-derived until annual holdings baselines are added.",
        "trackers": trackers_output,
        "sourceStatus": {
            "house": {"filingsDiscovered": len(house_filings), "errors": house_errors[:20]},
            "senate": {"errors": senate_errors[:20]},
            "parsing": {"errors": parse_errors[:30]},
        },
    }

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JS_PATH.write_text(browser_js(dataset), encoding="utf-8")
    total = sum(len(item["trades"]) for item in trackers_output.values())
    print(f"Political disclosure cache written: {total} retained trades; {sum(len(v) for v in incoming_by_tracker.values())} new")
    if total == 0:
        print("Warning: no trades were imported; inspect sourceStatus and workflow logs.", file=sys.stderr)
        if REQUIRE_TRADES:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
