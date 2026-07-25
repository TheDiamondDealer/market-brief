#!/usr/bin/env python3
"""Collect read-only central-bank rate-decision probabilities from Polymarket.

Targeted per-bank discovery via the public-search endpoint. Read-only public
market data only: no wallet, authentication, signing, deposit or order code.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import update_crowd_expectations as crowd  # reuse proven, tested helpers

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts" / "central_bank_registry.json"
OUTPUT_PATH = ROOT / "site" / "data" / "central-bank-decisions.json"

BPS_BY_LABEL = {
    "50+ bps decrease": -50,
    "25 bps decrease": -25,
    "no change": 0,
    "25 bps increase": 25,
    "50+ bps increase": 50,
}


def bps_for_label(label: str) -> int | None:
    return BPS_BY_LABEL.get(crowd.normalized(label))


def fetch_events(endpoint: str, term: str, limit: int) -> list[dict[str, Any]]:
    params = {"q": term, "limit_per_type": str(limit)}
    payload = crowd.request_json(f"{endpoint}?{urllib.parse.urlencode(params)}")
    events = payload.get("events") if isinstance(payload, dict) else None
    return [e for e in events if isinstance(e, dict)] if isinstance(events, list) else []


def is_live_decision(event: dict[str, Any], bank: dict[str, Any], now: datetime) -> bool:
    if event.get("closed") or event.get("active") is False:
        return False
    title = crowd.normalized(event.get("title"))
    if not any(crowd.contains_term(title, kw) for kw in bank.get("titleKeywords", [])):
        return False
    try:
        end_dt = datetime.fromisoformat(str(event.get("endDate")).replace("Z", "+00:00"))
        return end_dt > now
    except (TypeError, ValueError):
        return False


def outcome_records(
    event: dict[str, Any],
    previous_outcomes: dict[str, Any],
    collected_at: str,
    history_days: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for market in event.get("markets", []) or []:
        if not isinstance(market, dict):
            continue
        label = str(market.get("groupItemTitle") or "").strip()
        if not label:
            continue
        yes_probability, _ = crowd.binary_yes_probability(market)
        probability, source = crowd.selected_probability(market, yes_probability)
        if probability is None:
            continue
        prev = previous_outcomes.get(crowd.normalized(label))
        history = crowd.day_snapshot(prev, collected_at, probability)[-history_days:]
        results.append({
            "label": label,
            "bps": bps_for_label(label),
            "probability": round(probability, 6),
            "probabilityPercent": round(probability * 100, 2),
            "probabilitySource": source,
            "history": history,
        })
    results.sort(key=lambda o: (o["bps"] is None, o["bps"] if o["bps"] is not None else 0))
    return results


def summarise(outcomes: list[dict[str, Any]]):
    if not outcomes:
        return None, None, None, None
    priced = [o for o in outcomes if o.get("bps") is not None]
    modal = max(outcomes, key=lambda o: o["probability"])
    total = sum(o["probability"] for o in priced)
    expected = round(sum(o["probability"] * o["bps"] for o in priced) / total, 2) if total else None
    modal_bps = modal.get("bps")
    # Unmapped modal labels (bps is None) only arise if Polymarket adds a rung outside the
    # standard 5-step ladder. We can't classify direction for those, so we treat them the
    # same as a genuine "no change" — 'hold' — which emits no board lean (conservative).
    # Deliberately stays within the {hawkish, dovish, hold} enum: a null would violate the
    # schema and be misread as a downward signal by the board.
    if modal_bps is None or modal_bps == 0:
        direction = "hold"
    elif modal_bps > 0:
        direction = "hawkish"
    else:
        direction = "dovish"
    return modal["label"], round(modal["probability"], 6), expected, direction


def meeting_record(event, previous_outcomes, collected_at, history_days):
    outcomes = outcome_records(event, previous_outcomes, collected_at, history_days)
    if not outcomes:
        return None
    modal_label, modal_prob, expected_bps, direction = summarise(outcomes)
    end = str(event.get("endDate") or "")
    return {
        "decisionDate": end[:10] or None,
        "decisionDateTime": event.get("endDate") or None,
        "outcomes": outcomes,
        "modalOutcome": modal_label,
        "modalProbability": modal_prob,
        "expectedBps": expected_bps,
        "impliedDirection": direction,
        "liquidityUsd": round(crowd.number(event.get("volume")) or 0, 2),
        "marketUrl": (f"https://polymarket.com/event/{event.get('slug')}"
                      if event.get("slug") else "https://polymarket.com/"),
    }


def index_previous(previous):
    idx: dict[tuple, dict] = {}
    for bank in previous.get("banks", []) or []:
        for meeting in bank.get("meetings", []) or []:
            for outcome in meeting.get("outcomes", []) or []:
                key = (bank.get("id"), meeting.get("decisionDate"), crowd.normalized(outcome.get("label")))
                idx[key] = outcome
    return idx


def build_dataset(registry, previous, *, fetcher=fetch_events):
    collected_at = crowd.utc_now()
    now = datetime.now(timezone.utc)
    discovery = registry.get("discovery", {})
    endpoint = registry["provider"]["searchEndpoint"]
    limit = int(discovery.get("searchLimitPerType", 30))
    history_days = int(discovery.get("historyDays", 90))
    prev_idx = index_previous(previous)

    error: str | None = None
    banks_out: list[dict[str, Any]] = []
    try:
        for bank in registry.get("banks", []):
            events: list[dict[str, Any]] = []
            seen: set[str] = set()
            for term in bank.get("searchTerms", []):
                for event in fetcher(endpoint, term, limit):
                    key = str(event.get("id") or event.get("slug") or event.get("title"))
                    if key in seen or not is_live_decision(event, bank, now):
                        continue
                    seen.add(key)
                    events.append(event)
            events.sort(key=lambda e: str(e.get("endDate") or ""))
            meetings = []
            for event in events:
                prev_outcomes = {
                    k[2]: v for k, v in prev_idx.items()
                    if k[0] == bank["id"] and k[1] == str(event.get("endDate") or "")[:10]
                }
                record = meeting_record(event, prev_outcomes, collected_at, history_days)
                if record:
                    meetings.append(record)
            banks_out.append({
                "id": bank["id"], "name": bank["name"], "currency": bank["currency"],
                "boardAssetId": bank.get("boardAssetId"), "flag": bank.get("flag", ""),
                "meetings": meetings,
            })
        if not any(bank["meetings"] for bank in banks_out):
            raise ValueError("No live central-bank decision meetings returned")
    except Exception as exc:  # noqa: BLE001 — resilience: retain prior verified data
        error = str(exc)[:600] or exc.__class__.__name__
        banks_out = [dict(bank) for bank in previous.get("banks", []) if isinstance(bank, dict)]

    covered = sum(1 for bank in banks_out if bank.get("meetings"))
    status = ("stale" if error else "current") if banks_out else ("failed" if error else "unavailable")
    last_success = collected_at if (covered and not error) else previous.get("collection", {}).get("lastSuccessfulAt")
    generated = {
        "schemaVersion": 1,
        "generatedAtUtc": collected_at,
        "provider": registry["provider"],
        "collection": {
            "status": status,
            "banksCovered": covered,
            "lastSuccessfulAt": last_success,
            "error": error,
        },
        "banks": banks_out,
        "methodology": {
            "interpretation": "Prices are crowd-implied probabilities of each central-bank rate outcome, not forecasts or trade recommendations.",
            "price": "YES bid-ask midpoint when the spread is <=10 points, else last trade, else the Gamma outcome price.",
            "history": "One snapshot per UTC day is retained for up to 90 days; new banks start with short histories that fill in daily.",
            "jurisdiction": "Read-only public market data. No wallet, authentication, deposits or order endpoints.",
        },
        "sourceStatus": [{
            "id": "polymarket-central-bank-decisions",
            "source": "Polymarket public market data",
            "status": status,
            "lastSuccessfulAt": last_success,
            "expectedCadence": "Every six hours",
            "detail": f"{covered} central banks with live decision markets.",
            "error": error,
            "url": registry["provider"]["documentationUrl"],
        }],
    }
    try:
        validate_output(generated)
    except ValueError as exc:
        # A secondary validation failure must not defeat the resilience path. On the SUCCESS
        # path (error is None) we still fail loud — never write freshly-built invalid data.
        # On the retention path, degrade to an explicit empty 'failed' payload rather than
        # crashing the collector (e.g. a corrupt prior file, or tightened validation rules).
        if error is None:
            raise
        generated["banks"] = []
        generated["collection"]["status"] = "failed"
        generated["collection"]["banksCovered"] = 0
        generated["collection"]["lastSuccessfulAt"] = None
        generated["collection"]["error"] = f"retained data failed validation: {exc}"[:600]
        generated["sourceStatus"][0]["status"] = "failed"
        generated["sourceStatus"][0]["detail"] = "Retained data failed validation; no banks emitted."
        generated["sourceStatus"][0]["lastSuccessfulAt"] = None
        generated["sourceStatus"][0]["error"] = generated["collection"]["error"]
        validate_output(generated)
    return generated


def validate_output(data):
    if data.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    provider = data.get("provider", {})
    if provider.get("id") != "polymarket" or provider.get("readOnly") is not True:
        raise ValueError("Provider must remain Polymarket read-only")
    for bank in data.get("banks", []):
        for meeting in bank.get("meetings", []):
            outcomes = meeting.get("outcomes", [])
            labels = [o.get("label") for o in outcomes]
            if len(labels) != len(set(labels)):
                raise ValueError(f"Duplicate outcome labels: {bank.get('id')} {meeting.get('decisionDate')}")
            for outcome in outcomes:
                probability = crowd.number(outcome.get("probability"))
                if probability is None or not 0 <= probability <= 1:
                    raise ValueError(f"Invalid probability: {bank.get('id')} {outcome.get('label')}")
                history = outcome.get("history", [])
                dates = [str(p.get("date") or "") for p in history if isinstance(p, dict)]
                if dates != sorted(dates) or len(dates) != len(set(dates)):
                    raise ValueError(f"Invalid history dates: {bank.get('id')} {outcome.get('label')}")
                if len(history) > 90:
                    raise ValueError(f"History exceeds 90 days: {bank.get('id')} {outcome.get('label')}")
            if meeting.get("modalOutcome") is not None and meeting["modalOutcome"] not in labels:
                raise ValueError(f"Modal outcome not among outcomes: {bank.get('id')}")
    rendered = json.dumps(data, ensure_ascii=False).lower()
    if any(marker in rendered for marker in crowd.TRADING_MARKERS):
        raise ValueError("Generated data contains a prohibited trading marker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    registry = crowd.load_json(args.registry, {})
    if not registry:
        print(f"Unable to load registry: {args.registry}", file=sys.stderr)
        return 1
    previous = crowd.load_json(args.output, {})
    dataset = build_dataset(registry, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Central-bank decisions status={dataset['collection']['status']}; "
          f"banksCovered={dataset['collection']['banksCovered']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
