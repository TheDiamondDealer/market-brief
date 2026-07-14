#!/usr/bin/env python3
"""Split retained political disclosure history into lazy, searchable static files."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "site" / "data" / "political-disclosures.json"
OUTPUT_ROOT = ROOT / "site" / "data" / "political"
BOOTSTRAP_PATH = ROOT / "site" / "political-data.js"
RECENT_PER_TRACKER = 30
RECENT_GLOBAL = 100


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _year(trade: dict[str, Any]) -> int | None:
    value = str(trade.get("traded") or trade.get("filed") or "")
    match = re.match(r"^(\d{4})", value)
    return int(match.group(1)) if match else None


def _trade_sort(trade: dict[str, Any]) -> tuple[str, str, str]:
    return (str(trade.get("traded") or ""), str(trade.get("filed") or ""), str(trade.get("id") or ""))


def build_split(dataset: dict[str, Any], output_root: Path = OUTPUT_ROOT) -> dict[str, Any]:
    trackers = dataset.get("trackers", {}) if isinstance(dataset.get("trackers"), dict) else {}
    manifest_trackers: dict[str, Any] = {}
    summary_trackers: dict[str, Any] = {}
    politician_index: list[dict[str, Any]] = []
    ticker_index: dict[str, dict[str, Any]] = {}
    recent_global: list[dict[str, Any]] = []

    for tracker_id, tracker in trackers.items():
        trades = sorted(list(tracker.get("trades") or []), key=_trade_sort, reverse=True)
        by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for trade in trades:
            year = _year(trade)
            if year is not None:
                by_year[year].append(trade)
            recent_global.append({"politicianId": tracker_id, "politician": tracker.get("name", tracker_id), "chamber": tracker.get("chamber"), **trade})

        years = sorted(by_year, reverse=True)
        for year in years:
            annual = {
                "schemaVersion": 1,
                "generatedAt": dataset.get("generatedAt"),
                "politicianId": tracker_id,
                "politician": tracker.get("name", tracker_id),
                "chamber": tracker.get("chamber"),
                "year": year,
                "tradeCount": len(by_year[year]),
                "trades": by_year[year],
            }
            _write(output_root / tracker_id / f"{year}.json", annual)

        tracker_summary = {
            "schemaVersion": 1,
            "generatedAt": dataset.get("generatedAt"),
            "politicianId": tracker_id,
            "name": tracker.get("name", tracker_id),
            "chamber": tracker.get("chamber"),
            "status": tracker.get("status"),
            "updated": tracker.get("updated"),
            "tradeCount": len(trades),
            "years": years,
            "latestTrade": trades[0].get("traded") if trades else None,
            "latestFiling": max((str(item.get("filed") or "") for item in trades), default=None),
            "recentTrades": trades[:RECENT_PER_TRACKER],
            "portfolio": tracker.get("portfolio", {}),
            "emptyMessage": tracker.get("emptyMessage", ""),
            "sourceStatus": tracker.get("sourceStatus", {}),
        }
        _write(output_root / tracker_id / "summary.json", tracker_summary)

        manifest_trackers[tracker_id] = {
            "id": tracker_id,
            "name": tracker_summary["name"],
            "chamber": tracker_summary["chamber"],
            "status": tracker_summary["status"],
            "tradeCount": tracker_summary["tradeCount"],
            "latestTrade": tracker_summary["latestTrade"],
            "latestFiling": tracker_summary["latestFiling"],
            "years": years,
            "summaryUrl": f"data/political/{tracker_id}/summary.json",
            "annualUrls": {str(year): f"data/political/{tracker_id}/{year}.json" for year in years},
        }
        summary_trackers[tracker_id] = {
            key: tracker_summary[key]
            for key in ("politicianId", "name", "chamber", "status", "tradeCount", "latestTrade", "latestFiling", "years", "recentTrades", "sourceStatus")
        }
        politician_index.append({
            "id": tracker_id,
            "name": tracker_summary["name"],
            "chamber": tracker_summary["chamber"],
            "tradeCount": tracker_summary["tradeCount"],
            "latestFiling": tracker_summary["latestFiling"],
            "keywords": f"{tracker_id} {tracker_summary['name']} {tracker_summary['chamber']}".lower(),
        })

        for trade in trades:
            ticker = str(trade.get("ticker") or "").strip().upper()
            if not ticker:
                continue
            entry = ticker_index.setdefault(ticker, {"ticker": ticker, "tradeCount": 0, "politicians": {}, "assets": set(), "latestTrade": None, "latestFiling": None})
            entry["tradeCount"] += 1
            entry["politicians"][tracker_id] = tracker_summary["name"]
            if trade.get("asset"):
                entry["assets"].add(str(trade["asset"]))
            entry["latestTrade"] = max(filter(None, [entry["latestTrade"], trade.get("traded")]), default=None)
            entry["latestFiling"] = max(filter(None, [entry["latestFiling"], trade.get("filed")]), default=None)

    recent_global.sort(key=lambda item: _trade_sort(item), reverse=True)
    ticker_rows = []
    for entry in ticker_index.values():
        ticker_rows.append({
            "ticker": entry["ticker"],
            "tradeCount": entry["tradeCount"],
            "politicians": [{"id": key, "name": value} for key, value in sorted(entry["politicians"].items())],
            "assets": sorted(entry["assets"])[:12],
            "latestTrade": entry["latestTrade"],
            "latestFiling": entry["latestFiling"],
        })
    ticker_rows.sort(key=lambda item: (-item["tradeCount"], item["ticker"]))
    politician_index.sort(key=lambda item: item["name"])

    manifest = {
        "schemaVersion": 1,
        "generatedAt": dataset.get("generatedAt"),
        "generatedAtHuman": dataset.get("generatedAtHuman"),
        "methodology": dataset.get("methodology"),
        "trackerCount": len(manifest_trackers),
        "totalTrades": sum(item["tradeCount"] for item in manifest_trackers.values()),
        "trackers": manifest_trackers,
        "summaryUrl": "data/political/summary.json",
        "politicianIndexUrl": "data/political/indexes/politicians.json",
        "tickerIndexUrl": "data/political/indexes/tickers.json",
    }
    summary = {
        "schemaVersion": 1,
        "generatedAt": dataset.get("generatedAt"),
        "generatedAtHuman": dataset.get("generatedAtHuman"),
        "methodology": dataset.get("methodology"),
        "totalTrades": manifest["totalTrades"],
        "trackers": summary_trackers,
        "recentFilings": recent_global[:RECENT_GLOBAL],
        "sourceStatus": dataset.get("sourceStatus", {}),
    }
    _write(output_root / "manifest.json", manifest)
    _write(output_root / "summary.json", summary)
    _write(output_root / "indexes" / "politicians.json", {"schemaVersion": 1, "generatedAt": dataset.get("generatedAt"), "politicians": politician_index})
    _write(output_root / "indexes" / "tickers.json", {"schemaVersion": 1, "generatedAt": dataset.get("generatedAt"), "tickers": ticker_rows})
    return {"manifest": manifest, "summary": summary}


def browser_bootstrap(split: dict[str, Any]) -> str:
    manifest = split["manifest"]
    summary = split["summary"]
    trackers = {}
    for tracker_id, item in summary.get("trackers", {}).items():
        trackers[tracker_id] = {
            "name": item.get("name"),
            "chamber": item.get("chamber"),
            "status": item.get("status"),
            "updated": summary.get("generatedAtHuman"),
            "trades": item.get("recentTrades", []),
            "totalTrades": item.get("tradeCount", 0),
            "availableYears": item.get("years", []),
            "lazySummaryUrl": manifest.get("trackers", {}).get(tracker_id, {}).get("summaryUrl"),
            "sourceStatus": item.get("sourceStatus", {}),
            "portfolio": {"status": "Load profile for disclosure-derived holdings", "holdings": []},
        }
    bootstrap = {
        "generatedAt": summary.get("generatedAt"),
        "generatedAtHuman": summary.get("generatedAtHuman"),
        "methodology": summary.get("methodology"),
        "trackers": trackers,
        "sourceStatus": summary.get("sourceStatus", {}),
        "lazy": True,
    }
    return "\n".join([
        f"window.politicalDisclosureManifest={json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))};",
        f"window.politicalDisclosureSummary={json.dumps(summary, ensure_ascii=False, separators=(',', ':'))};",
        f"window.politicalDisclosureData={json.dumps(bootstrap, ensure_ascii=False, separators=(',', ':'))};",
        """(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;
  const source = window.politicalDisclosureData || {trackers:{}};
  Object.entries(source.trackers || {}).forEach(([id, imported]) => {
    const tracker = fallback.trackers[id];
    if (!tracker) return;
    tracker.trades = Array.isArray(imported.trades) ? imported.trades : [];
    tracker.totalTrades = imported.totalTrades || tracker.trades.length;
    tracker.availableYears = imported.availableYears || [];
    tracker.lazySummaryUrl = imported.lazySummaryUrl;
    tracker.updated = imported.updated || source.generatedAtHuman || tracker.updated;
    tracker.importStatus = imported.status;
    tracker.portfolio = Object.assign({}, tracker.portfolio || {}, imported.portfolio || {});
  });
})();
""",
    ])


def build_from_disk() -> dict[str, Any]:
    dataset = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    split = build_split(dataset)
    BOOTSTRAP_PATH.write_text(browser_bootstrap(split), encoding="utf-8")
    return split


if __name__ == "__main__":
    built = build_from_disk()
    print(f"Political lazy data written: {built['manifest']['trackerCount']} trackers; {built['manifest']['totalTrades']} retained trades")
