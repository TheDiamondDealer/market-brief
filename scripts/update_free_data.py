#!/usr/bin/env python3
"""Collect free official rates and COT data for the static dashboard.

Sources:
- Federal Reserve Bank of St. Louis downloadable CSV series (no paid key).
- CFTC annual compressed COT files (Disaggregated and TFF futures-only).

The script is deliberately defensive: one failed source does not erase the last
successful dataset. It writes both JSON and a browser-loadable JavaScript file.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "site" / "data" / "free-market-data.json"
JS_PATH = ROOT / "site" / "free-data.js"
USER_AGENT = "MarketBriefResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)"

FRED_SERIES = {
    "DGS2": {"name": "US 2-year Treasury", "unit": "%", "kind": "yield"},
    "DGS5": {"name": "US 5-year Treasury", "unit": "%", "kind": "yield"},
    "DGS10": {"name": "US 10-year Treasury", "unit": "%", "kind": "yield"},
    "DGS30": {"name": "US 30-year Treasury", "unit": "%", "kind": "yield"},
    "DFII10": {"name": "US 10-year real yield", "unit": "%", "kind": "yield"},
    "T10YIE": {"name": "US 10-year breakeven", "unit": "%", "kind": "yield"},
    "BAMLH0A0HYM2": {"name": "US high-yield spread", "unit": "%", "kind": "spread"},
    "DFF": {"name": "Effective federal funds rate", "unit": "%", "kind": "policy"},
    "SOFR": {"name": "SOFR", "unit": "%", "kind": "policy"},
    "DTWEXBGS": {"name": "Trade-weighted US dollar", "unit": "index", "kind": "index"},
}

DISAGG_MARKETS = {
    "gold": {"label": "Gold", "patterns": ["GOLD", "COMMODITY EXCHANGE"]},
    "silver": {"label": "Silver", "patterns": ["SILVER", "COMMODITY EXCHANGE"]},
    "copper": {"label": "Copper", "patterns": ["COPPER-GRADE #1"]},
    "oil": {"label": "WTI crude oil", "patterns": ["CRUDE OIL, LIGHT SWEET"]},
    "natural-gas": {"label": "Natural gas", "patterns": ["NATURAL GAS", "NEW YORK MERCANTILE"]},
}

TFF_MARKETS = {
    "yen": {"label": "Japanese yen", "patterns": ["JAPANESE YEN"]},
    "us10y-futures": {"label": "US 10-year Treasury futures", "patterns_any": ["10-YEAR U.S. TREASURY", "UST 10Y", "10 YEAR U.S. TREASURY"]},
    "usd-index": {"label": "US Dollar Index", "patterns_any": ["U.S. DOLLAR INDEX", "USD INDEX"]},
}


@dataclass
class Observation:
    date: str
    long: float
    short: float
    open_interest: float | None
    market_name: str
    category: str

    @property
    def net(self) -> float:
        return self.long - self.short


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {".", "NA", "N/A", "null", "None"}:
        return None
    try:
        number = float(text)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def load_previous() -> dict[str, Any]:
    if not JSON_PATH.exists():
        return {}
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def fetch_fred_series(series_id: str) -> dict[str, Any]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    raw = fetch_bytes(url).decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(raw)))
    observations: list[tuple[str, float]] = []
    for row in rows:
        date = row.get("observation_date") or row.get("DATE") or row.get("date")
        value = safe_float(row.get(series_id))
        if date and value is not None:
            observations.append((date, value))
    if not observations:
        raise ValueError(f"No usable observations for {series_id}")
    latest_date, latest = observations[-1]
    previous = observations[-2][1] if len(observations) > 1 else None
    change = latest - previous if previous is not None else None
    meta = FRED_SERIES[series_id]
    return {
        "id": series_id,
        "name": meta["name"],
        "unit": meta["unit"],
        "kind": meta["kind"],
        "date": latest_date,
        "value": round(latest, 4),
        "previous": round(previous, 4) if previous is not None else None,
        "change": round(change, 4) if change is not None else None,
        "changeBps": round(change * 100, 1) if change is not None and meta["kind"] in {"yield", "spread", "policy"} else None,
        "sourceUrl": url,
    }


def normalise_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip().replace("\ufeff", ""): str(value).strip() for key, value in row.items() if key is not None}


def read_cot_zip(url: str) -> list[dict[str, str]]:
    payload = fetch_bytes(url, timeout=90)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if not names:
            raise ValueError(f"No files in {url}")
        preferred = next((name for name in names if name.lower().endswith((".txt", ".csv"))), names[0])
        raw = archive.read(preferred)
    text = raw.decode("utf-8-sig", errors="replace").replace("\x00", "")
    return [normalise_row(row) for row in csv.DictReader(io.StringIO(text))]


def market_matches(name: str, config: dict[str, Any]) -> bool:
    upper = name.upper()
    all_patterns = config.get("patterns", [])
    any_patterns = config.get("patterns_any", [])
    return (not all_patterns or all(pattern.upper() in upper for pattern in all_patterns)) and (not any_patterns or any(pattern.upper() in upper for pattern in any_patterns))


def parse_date(row: dict[str, str]) -> str | None:
    candidates = [
        row.get("As_of_Date_Form_YYYY-MM-DD"),
        row.get("Report_Date_as_YYYY-MM-DD"),
        row.get("Report_Date_as_MM_DD_YYYY"),
        row.get("As_of_Date_In_Form_YYMMDD"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        value = candidate.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m_%d_%Y", "%y%m%d"):
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                pass
    return None


def row_value(row: dict[str, str], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = safe_float(row.get(key))
        if value is not None:
            return value
    return None


def extract_observations(rows: list[dict[str, str]], markets: dict[str, dict[str, Any]], report_type: str) -> dict[str, list[Observation]]:
    output: dict[str, list[Observation]] = defaultdict(list)
    for row in rows:
        market_name = row.get("Market_and_Exchange_Names", "")
        date = parse_date(row)
        if not market_name or not date:
            continue
        for market_id, config in markets.items():
            if not market_matches(market_name, config):
                continue
            if report_type == "disagg":
                long_value = row_value(row, ["M_Money_Positions_Long_All"])
                short_value = row_value(row, ["M_Money_Positions_Short_All"])
                category = "Managed money"
            else:
                long_value = row_value(row, ["Lev_Money_Positions_Long_All"])
                short_value = row_value(row, ["Lev_Money_Positions_Short_All"])
                category = "Leveraged funds"
            if long_value is None or short_value is None:
                continue
            output[market_id].append(Observation(
                date=date,
                long=long_value,
                short=short_value,
                open_interest=row_value(row, ["Open_Interest_All"]),
                market_name=market_name,
                category=category,
            ))
    return output


def percentile_rank(values: list[float], current: float) -> float | None:
    if len(values) < 5:
        return None
    below_or_equal = sum(1 for value in values if value <= current)
    return round(100 * below_or_equal / len(values), 1)


def crowding_label(percentile: float | None) -> str:
    if percentile is None:
        return "Insufficient history"
    if percentile >= 90:
        return "Crowded long"
    if percentile >= 75:
        return "Elevated long"
    if percentile <= 10:
        return "Crowded short"
    if percentile <= 25:
        return "Elevated short"
    return "Mid-range"


def summarise_market(market_id: str, label: str, observations: list[Observation]) -> dict[str, Any] | None:
    deduped: dict[str, Observation] = {}
    for observation in observations:
        deduped[observation.date] = observation
    ordered = sorted(deduped.values(), key=lambda item: item.date)
    if not ordered:
        return None
    latest = ordered[-1]
    previous = ordered[-2] if len(ordered) > 1 else None
    four_weeks = ordered[-5] if len(ordered) > 4 else None
    history = ordered[-260:]  # roughly five years of weekly reports
    history_52 = ordered[-52:]
    percentile = percentile_rank([item.net for item in history], latest.net)
    return {
        "id": market_id,
        "name": label,
        "market": latest.market_name,
        "category": latest.category,
        "reportDate": latest.date,
        "long": round(latest.long),
        "short": round(latest.short),
        "net": round(latest.net),
        "weekChange": round(latest.net - previous.net) if previous else None,
        "fourWeekChange": round(latest.net - four_weeks.net) if four_weeks else None,
        "openInterest": round(latest.open_interest) if latest.open_interest is not None else None,
        "netPercentile5y": percentile,
        "crowding": crowding_label(percentile),
        "historyCount": len(history),
        "history52": [
            {
                "date": item.date,
                "long": round(item.long),
                "short": round(item.short),
                "net": round(item.net),
            }
            for item in history_52
        ],
        "source": "CFTC Commitments of Traders",
        "sourceUrl": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
    }


def fetch_cot() -> tuple[list[dict[str, Any]], list[str]]:
    current_year = datetime.now(timezone.utc).year
    years = list(range(current_year - 5, current_year + 1))
    all_disagg: list[dict[str, str]] = []
    all_tff: list[dict[str, str]] = []
    errors: list[str] = []
    for year in years:
        for report_type, template, target in (
            ("disaggregated", "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip", all_disagg),
            ("financial", "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip", all_tff),
        ):
            url = template.format(year=year)
            try:
                target.extend(read_cot_zip(url))
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, zipfile.BadZipFile, ValueError) as exc:
                errors.append(f"{report_type} {year}: {exc}")

    combined: dict[str, list[Observation]] = defaultdict(list)
    for market_id, values in extract_observations(all_disagg, DISAGG_MARKETS, "disagg").items():
        combined[market_id].extend(values)
    for market_id, values in extract_observations(all_tff, TFF_MARKETS, "tff").items():
        combined[market_id].extend(values)

    configs = {**DISAGG_MARKETS, **TFF_MARKETS}
    summaries = []
    for market_id, config in configs.items():
        summary = summarise_market(market_id, config["label"], combined.get(market_id, []))
        if summary:
            summaries.append(summary)
    return summaries, errors


def build_dataset(previous: dict[str, Any]) -> dict[str, Any]:
    melbourne = datetime.now(ZoneInfo("Australia/Melbourne"))
    utc_now = datetime.now(timezone.utc)
    source_status: list[dict[str, Any]] = []

    rates: list[dict[str, Any]] = []
    rate_errors: list[str] = []
    for series_id in FRED_SERIES:
        try:
            rates.append(fetch_fred_series(series_id))
        except Exception as exc:  # retain partial success and report precisely
            rate_errors.append(f"{series_id}: {exc}")

    if not rates and previous.get("rates"):
        rates = previous["rates"]
        rate_state = "stale fallback"
    elif rate_errors:
        rate_state = "partial"
    else:
        rate_state = "current"
    source_status.append({
        "source": "FRED / Federal Reserve data",
        "status": rate_state,
        "detail": "; ".join(rate_errors[:4]) if rate_errors else "Latest non-missing observation loaded for each series.",
        "url": "https://fred.stlouisfed.org/docs/api/fred/",
    })

    try:
        cot, cot_errors = fetch_cot()
    except Exception as exc:
        cot, cot_errors = [], [str(exc)]
    if not cot and previous.get("cot"):
        cot = previous["cot"]
        cot_state = "stale fallback"
    elif cot_errors:
        cot_state = "partial"
    else:
        cot_state = "current"
    source_status.append({
        "source": "CFTC Commitments of Traders",
        "status": cot_state,
        "detail": "; ".join(cot_errors[:4]) if cot_errors else "Six years of annual compressed files loaded for percentile calculations.",
        "url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
    })

    rate_by_id = {row["id"]: row for row in rates}
    def value(series_id: str) -> float | None:
        row = rate_by_id.get(series_id)
        return row.get("value") if row else None

    dgs2, dgs5, dgs10, dgs30 = value("DGS2"), value("DGS5"), value("DGS10"), value("DGS30")
    spreads = []
    if dgs2 is not None and dgs10 is not None:
        spreads.append({"name": "2s10s", "value": round((dgs10 - dgs2) * 100, 1), "unit": "bp", "interpretation": "Positive means the 10-year yield is above the 2-year yield."})
    if dgs5 is not None and dgs30 is not None:
        spreads.append({"name": "5s30s", "value": round((dgs30 - dgs5) * 100, 1), "unit": "bp", "interpretation": "A steeper long end can reflect growth, inflation or supply pressure."})

    return {
        "generatedAt": f"{melbourne.day} {melbourne.strftime('%B %Y')}, {melbourne.strftime('%I:%M %p %Z').lstrip('0')}",
        "generatedAtUtc": utc_now.isoformat(timespec="seconds"),
        "rates": rates,
        "curveSpreads": spreads,
        "cot": cot,
        "sourceStatus": source_status,
        "methodology": {
            "rates": "Latest non-missing public FRED observations. Basis-point changes compare with the previous available observation.",
            "cot": "CFTC futures-only reports. Commodities use Managed Money; currencies and Treasury futures use Leveraged Funds. Percentiles use up to 260 weekly observations.",
            "warning": "COT reflects Tuesday positions normally released Friday. It is positioning context, not a real-time signal or proof of trader intent.",
        },
    }


def write_dataset(dataset: dict[str, Any], dry_run: bool) -> None:
    payload = json.dumps(dataset, indent=2, ensure_ascii=False, sort_keys=False)
    if dry_run:
        print(payload)
        return
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(payload + "\n", encoding="utf-8")
    JS_PATH.write_text("window.freeMarketData = " + json.dumps(dataset, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print the generated JSON instead of writing files.")
    args = parser.parse_args()
    previous = load_previous()
    dataset = build_dataset(previous)
    write_dataset(dataset, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
