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
    except (TypeError, ValueError):
        return False
    return end_dt > now


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
