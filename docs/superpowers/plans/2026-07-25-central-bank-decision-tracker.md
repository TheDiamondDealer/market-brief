# Central-Bank Decision-Probability Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a provenance-clean, multi-central-bank rate-decision-probability tracker (our answer to MRKT EDGE's Interest Rate Tracker) as a new "Rate decisions" view, fed by the Polymarket data we already integrate, plus a conservative policy-lean Pressure-Board signal.

**Architecture:** A self-contained module mirroring the `crowd-expectations` / `official-feeds` patterns: a targeted per-bank Polymarket collector → normalized `central-bank-decisions.json` → an eager data global → a new `rate-decisions` view + a `deriveRateDecisionSignals` addition to the impact engine. Reuses the proven collector helpers (`request_json`, `selected_probability`, `binary_yes_probability`, `day_snapshot`) rather than duplicating them.

**Tech Stack:** Python 3 stdlib collector (+ `jsonschema` for validation, already a dep), vanilla classic-script browser JS setting `window.*` globals, Node `vm`-based JS unit tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-07-25-central-bank-decision-tracker-design.md`

## Global Constraints

Every task's requirements implicitly include these (verbatim from the spec + verified codebase facts):

- **Provider is Polymarket, read-only.** No wallet, authentication, signing, deposit or order code. The output JSON must contain none of the `update_crowd_expectations.TRADING_MARKERS` substrings.
- **The committed collector keeps TLS certificate verification.** The local `NODE_TLS_REJECT_UNAUTHORIZED=0` / unverified-SSL probe workaround is LOCAL-ONLY and must never appear in committed code.
- **Board asset ids are exact:** Fed → `dxy` (label "US dollar"), RBA → `aud` (label "AUD/USD"). No other bank has a board asset in v1 (`boardAssetId: null`).
- **Board signal gate:** emit a direction only when `modalProbability >= 0.55` AND `impliedDirection !== 'hold'`. Otherwise no signal (QUIET). Signal `source` is `'rate-decision-odds'`, kept distinct from the official-print `'rba'` signal so the two are never conflated.
- **History:** one snapshot per UTC day via `day_snapshot`, capped at 90 points, dates sorted + unique.
- **Outcome labels** come from Polymarket `groupItemTitle` verbatim; the bps value is derived via `BPS_BY_LABEL`.
- **Cadence:** every 6 hours (matches the sibling `crowd-expectations` Polymarket collector; the spec's "hourly" was based on a mis-recollection of crowd's cadence — corrected here).
- **DRY:** import shared helpers from `update_crowd_expectations`; do not re-implement them.

## File Structure

**Create:**
- `scripts/central_bank_registry.json` — bank list + provider block + discovery config
- `scripts/update_central_bank_decisions.py` — collector
- `scripts/validate_central_bank_decisions.py` — schema + semantic validator
- `schemas/central-bank-decisions.schema.json` — JSON schema
- `site/data/central-bank-decisions.json` — generated data (seeded by a real run)
- `site/features/rate-decisions/rate-decisions-data.js` — eager data global loader
- `site/features/rate-decisions/rate-decisions-page.js` — the view module
- `site/features/rate-decisions/rate-decisions-page.css` — view styles
- `.github/workflows/update-central-bank-decisions.yml` — hourly-class refresh workflow
- `tests/test_central_bank_decisions.py` — collector + validator tests

**Modify:**
- `site/core/impact-engine.js` — add `deriveRateDecisionSignals` + thread `cbSource`
- `site/features/command-centre/command-page.js` — pass `cbSource`, repaint on the CB event
- `site/features/week/week-page.js` — same board wiring
- `site/features/asset-workspace/asset-page.js` — same board wiring
- `site/core/feature-loader.js` — add the `rate-decisions` route entry
- `site/index.html` — eager data script, nav button, view container
- `tests/js/impact-engine.test.js` — policy-lean signal cases

---

## Task 1: Registry + collector parsing core

**Files:**
- Create: `scripts/central_bank_registry.json`
- Create: `scripts/update_central_bank_decisions.py`
- Test: `tests/test_central_bank_decisions.py`

**Interfaces:**
- Consumes: `update_crowd_expectations.{request_json, selected_probability, binary_yes_probability, day_snapshot, number, normalized, contains_term, utc_now, load_json, TRADING_MARKERS}`
- Produces:
  - `BPS_BY_LABEL: dict[str,int]`, `bps_for_label(label:str)->int|None`
  - `is_live_decision(event:dict, bank:dict, now:datetime)->bool`
  - `outcome_records(event:dict, previous_outcomes:dict, collected_at:str, history_days:int)->list[dict]`
  - `summarise(outcomes:list[dict])->tuple[str|None,float|None,float|None,str|None]` returning `(modalOutcome, modalProbability, expectedBps, impliedDirection)`

- [ ] **Step 1: Write the registry file**

`scripts/central_bank_registry.json`:
```json
{
  "schemaVersion": 1,
  "provider": {
    "id": "polymarket",
    "name": "Polymarket",
    "searchEndpoint": "https://gamma-api.polymarket.com/public-search",
    "documentationUrl": "https://docs.polymarket.com/market-data/overview",
    "readOnly": true,
    "jurisdictionNote": "Read-only public market data only. No wallet, authentication, deposits or order endpoints. Australia is close-only for Polymarket order placement."
  },
  "discovery": { "searchLimitPerType": 30, "historyDays": 90 },
  "banks": [
    { "id": "fed",     "name": "Federal Reserve",            "currency": "USD", "boardAssetId": "dxy", "flag": "🇺🇸", "searchTerms": ["Fed Decision"],                     "titleKeywords": ["fed decision"] },
    { "id": "ecb",     "name": "European Central Bank",       "currency": "EUR", "boardAssetId": null,  "flag": "🇪🇺", "searchTerms": ["ECB Interest Rates"],               "titleKeywords": ["ecb interest rates"] },
    { "id": "boe",     "name": "Bank of England",             "currency": "GBP", "boardAssetId": null,  "flag": "🇬🇧", "searchTerms": ["Bank of England decision"],         "titleKeywords": ["bank of england decision"] },
    { "id": "boj",     "name": "Bank of Japan",               "currency": "JPY", "boardAssetId": null,  "flag": "🇯🇵", "searchTerms": ["Bank of Japan Decision"],           "titleKeywords": ["bank of japan decision"] },
    { "id": "rba",     "name": "Reserve Bank of Australia",   "currency": "AUD", "boardAssetId": "aud", "flag": "🇦🇺", "searchTerms": ["Reserve Bank of Australia Decision"], "titleKeywords": ["reserve bank of australia decision"] },
    { "id": "boc",     "name": "Bank of Canada",              "currency": "CAD", "boardAssetId": null,  "flag": "🇨🇦", "searchTerms": ["Bank of Canada Decision"],          "titleKeywords": ["bank of canada decision"] },
    { "id": "bok",     "name": "Bank of Korea",               "currency": "KRW", "boardAssetId": null,  "flag": "🇰🇷", "searchTerms": ["Bank of Korea decision"],           "titleKeywords": ["bank of korea decision"] },
    { "id": "banxico", "name": "Bank of Mexico",              "currency": "MXN", "boardAssetId": null,  "flag": "🇲🇽", "searchTerms": ["Bank of Mexico Decision"],          "titleKeywords": ["bank of mexico decision"] },
    { "id": "rbnz",    "name": "Reserve Bank of New Zealand", "currency": "NZD", "boardAssetId": null,  "flag": "🇳🇿", "searchTerms": ["Reserve Bank of New Zealand decision"], "titleKeywords": ["reserve bank of new zealand decision"] }
  ]
}
```

- [ ] **Step 2: Write the failing test for label→bps + summarise**

Add to `tests/test_central_bank_decisions.py`:
```python
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_central_bank_decisions as cb  # noqa: E402


def test_bps_for_label_maps_standard_ladder():
    assert cb.bps_for_label("No change") == 0
    assert cb.bps_for_label("25 bps increase") == 25
    assert cb.bps_for_label("50+ bps decrease") == -50
    assert cb.bps_for_label("garbage") is None


def test_summarise_picks_modal_and_direction():
    outcomes = [
        {"label": "No change", "bps": 0, "probability": 0.30},
        {"label": "25 bps increase", "bps": 25, "probability": 0.62},
        {"label": "50+ bps increase", "bps": 50, "probability": 0.08},
    ]
    modal, modal_prob, expected, direction = cb.summarise(outcomes)
    assert modal == "25 bps increase"
    assert modal_prob == 0.62
    assert direction == "hawkish"
    assert expected is not None and expected > 0
```

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_central_bank_decisions.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'update_central_bank_decisions'`.

- [ ] **Step 4: Write the collector's parsing core**

Create `scripts/update_central_bank_decisions.py`:
```python
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
    direction = "hold" if not modal_bps else ("hawkish" if modal_bps > 0 else "dovish")
    return modal["label"], round(modal["probability"], 6), expected, direction
```

- [ ] **Step 5: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_central_bank_decisions.py -q`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/central_bank_registry.json scripts/update_central_bank_decisions.py tests/test_central_bank_decisions.py
git commit -m "feat(rate-decisions): central-bank collector parsing core + registry"
```

---

## Task 2: Meeting/bank records, dataset build, resilience, CLI

**Files:**
- Modify: `scripts/update_central_bank_decisions.py`
- Test: `tests/test_central_bank_decisions.py`

**Interfaces:**
- Consumes: Task 1's `is_live_decision`, `outcome_records`, `summarise`
- Produces:
  - `meeting_record(event, previous_outcomes, collected_at, history_days)->dict|None`
  - `index_previous(previous:dict)->dict[tuple,dict]`
  - `build_dataset(registry:dict, previous:dict, *, fetcher=fetch_events)->dict`
  - `validate_output(data:dict)->None`
  - `main()->int`

- [ ] **Step 1: Write the failing test for build_dataset with a fake fetcher**

Add to `tests/test_central_bank_decisions.py`:
```python
def _fake_event(slug, title, end, ladder):
    return {
        "slug": slug, "title": title, "endDate": end, "active": True, "closed": False,
        "volume": 50000,
        "markets": [
            {"groupItemTitle": label, "outcomes": "[\"Yes\", \"No\"]",
             "outcomePrices": f"[\"{p}\", \"{round(1-p,4)}\"]"}
            for label, p in ladder
        ],
    }


def test_build_dataset_normalizes_a_bank_meeting():
    registry = {
        "schemaVersion": 1,
        "provider": {"id": "polymarket", "readOnly": True, "documentationUrl": "https://x"},
        "discovery": {"searchLimitPerType": 30, "historyDays": 90},
        "banks": [{"id": "rba", "name": "Reserve Bank of Australia", "currency": "AUD",
                   "boardAssetId": "aud", "flag": "AU",
                   "searchTerms": ["Reserve Bank of Australia Decision"],
                   "titleKeywords": ["reserve bank of australia decision"]}],
    }
    events = {"Reserve Bank of Australia Decision": [
        _fake_event("rba-aug", "Reserve Bank of Australia Decision in August",
                    "2099-08-11T11:59:00Z",
                    [("No change", 0.62), ("25 bps increase", 0.30), ("25 bps decrease", 0.08)])
    ]}
    data = cb.build_dataset(registry, {}, fetcher=lambda ep, term, lim: events.get(term, []))
    assert data["collection"]["status"] == "current"
    bank = data["banks"][0]
    assert bank["id"] == "rba" and bank["boardAssetId"] == "aud"
    meeting = bank["meetings"][0]
    assert meeting["decisionDate"] == "2099-08-11"
    assert meeting["modalOutcome"] == "No change"
    assert meeting["impliedDirection"] == "hold"
    # outcomes are bps-ordered and each carries a one-point history
    assert [o["label"] for o in meeting["outcomes"]] == ["25 bps decrease", "No change", "25 bps increase"]
    assert len(meeting["outcomes"][0]["history"]) == 1
    cb.validate_output(data)  # must not raise


def test_build_dataset_retains_previous_on_total_failure():
    registry = {"schemaVersion": 1, "provider": {"id": "polymarket", "readOnly": True,
                "documentationUrl": "https://x"}, "discovery": {"historyDays": 90},
                "banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                           "boardAssetId": "dxy", "flag": "US", "searchTerms": ["Fed Decision"],
                           "titleKeywords": ["fed decision"]}]}
    previous = {"banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                "boardAssetId": "dxy", "meetings": [{"decisionDate": "2099-07-29",
                "outcomes": [{"label": "No change", "bps": 0, "probability": 0.7,
                "probabilityPercent": 70.0, "probabilitySource": "last trade", "history": []}],
                "modalOutcome": "No change", "modalProbability": 0.7, "expectedBps": 0.0,
                "impliedDirection": "hold", "liquidityUsd": 0, "marketUrl": "https://x"}]}],
                "collection": {"lastSuccessfulAt": "2026-07-25T00:00:00Z"}}

    def boom(ep, term, lim):
        raise RuntimeError("network down")

    data = cb.build_dataset(registry, previous, fetcher=boom)
    assert data["collection"]["status"] == "stale"
    assert data["collection"]["error"]
    assert data["banks"][0]["meetings"][0]["decisionDate"] == "2099-07-29"
```

- [ ] **Step 2: Run to confirm failure**

Run: `python -m pytest tests/test_central_bank_decisions.py -q`
Expected: FAIL — `AttributeError: module ... has no attribute 'build_dataset'`.

- [ ] **Step 3: Implement records, dataset build, resilience, validation, CLI**

Append to `scripts/update_central_bank_decisions.py`:
```python
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
        error = str(exc)[:600]
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
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_central_bank_decisions.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/update_central_bank_decisions.py tests/test_central_bank_decisions.py
git commit -m "feat(rate-decisions): dataset build, resilience + CLI for CB collector"
```

---

## Task 3: JSON schema, validator, committed-cache test, seed the data

**Files:**
- Create: `schemas/central-bank-decisions.schema.json`
- Create: `scripts/validate_central_bank_decisions.py`
- Create: `site/data/central-bank-decisions.json` (real run)
- Test: `tests/test_central_bank_decisions.py`

**Interfaces:**
- Consumes: `central-bank-decisions.json`, the schema
- Produces: `validate_central_bank_decisions.main()->int` (raises `SystemExit` on failure), a committed valid data file

- [ ] **Step 1: Write the schema**

`schemas/central-bank-decisions.schema.json` (Draft 2020-12), mirroring `schemas/crowd-expectations.schema.json` structure:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["schemaVersion", "provider", "collection", "banks"],
  "properties": {
    "schemaVersion": { "const": 1 },
    "provider": {
      "type": "object",
      "required": ["id", "readOnly"],
      "properties": { "id": { "const": "polymarket" }, "readOnly": { "const": true } }
    },
    "collection": {
      "type": "object",
      "required": ["status", "banksCovered"],
      "properties": {
        "status": { "enum": ["current", "stale", "partial", "failed", "unavailable"] },
        "banksCovered": { "type": "integer", "minimum": 0 }
      }
    },
    "banks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "currency", "boardAssetId", "meetings"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "currency": { "type": "string" },
          "boardAssetId": { "type": ["string", "null"] },
          "meetings": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["decisionDate", "outcomes", "impliedDirection"],
              "properties": {
                "decisionDate": { "type": ["string", "null"] },
                "impliedDirection": { "enum": ["hawkish", "dovish", "hold"] },
                "modalProbability": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
                "outcomes": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["label", "probability", "history"],
                    "properties": {
                      "label": { "type": "string" },
                      "bps": { "type": ["integer", "null"] },
                      "probability": { "type": "number", "minimum": 0, "maximum": 1 },
                      "history": {
                        "type": "array",
                        "maxItems": 90,
                        "items": {
                          "type": "object",
                          "required": ["date", "probability"],
                          "properties": {
                            "date": { "type": "string" },
                            "probability": { "type": "number", "minimum": 0, "maximum": 1 }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Write the validator**

`scripts/validate_central_bank_decisions.py` (mirror `scripts/validate_crowd_expectations.py`):
```python
#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data" / "central-bank-decisions.json"
SCHEMA = ROOT / "schemas" / "central-bank-decisions.schema.json"

# Reuse the collector's semantic validator (probabilities, history, modal, markers).
sys.path.insert(0, str(ROOT / "scripts"))
import update_central_bank_decisions as cb  # noqa: E402


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: e.path)
    if errors:
        rendered = [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]
        raise SystemExit("Central-bank-decisions schema validation failed: " + "; ".join(rendered))
    try:
        cb.validate_output(data)
    except ValueError as exc:
        raise SystemExit(f"Central-bank-decisions semantic validation failed: {exc}") from exc
    covered = data["collection"]["banksCovered"]
    print(f"Central-bank-decisions OK: status={data['collection']['status']}; banksCovered={covered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Seed the real data file**

Run the collector against live Polymarket (network required):
```bash
python scripts/update_central_bank_decisions.py
```
Expected stdout: `status=current; banksCovered=9` (or close — thin banks occasionally have no live market). Confirm `site/data/central-bank-decisions.json` now exists with a `banks` array.

- [ ] **Step 4: Write the committed-cache validation test**

Add to `tests/test_central_bank_decisions.py`:
```python
import subprocess


def test_committed_cache_validates():
    subprocess.run(["python", "scripts/validate_central_bank_decisions.py"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
```

- [ ] **Step 5: Run validator + tests**

Run: `python scripts/validate_central_bank_decisions.py && python -m pytest tests/test_central_bank_decisions.py -q`
Expected: validator prints OK; all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add schemas/central-bank-decisions.schema.json scripts/validate_central_bank_decisions.py site/data/central-bank-decisions.json tests/test_central_bank_decisions.py
git commit -m "feat(rate-decisions): schema, validator + seed CB decisions data"
```

---

## Task 4: Impact-engine policy-lean signal

**Files:**
- Modify: `site/core/impact-engine.js`
- Test: `tests/js/impact-engine.test.js`

**Interfaces:**
- Consumes: `assetById`, `netPressure` (existing in impact-engine)
- Produces: `deriveRateDecisionSignals(cbSource)->signal[]`; `collectDeterministicSignals` now accepts a `cbSource` key; both exported on `core.impactEngine`.

- [ ] **Step 1: Write the failing JS test cases**

In `tests/js/impact-engine.test.js`, after the existing BLS block (around line 158), add a `cbSource` fixture + assertions. Note the shared `sandbox.window.marketAssetBoard` fixture already defines `dxy` (label "US dollar") and `aud` — reuse them:
```javascript
// --- rate-decision policy-lean signals ---
const cbSource = {
  generatedAtUtc: '2026-07-25T00:00:00Z',
  collection: { status: 'current' },
  banks: [
    { id: 'rba', name: 'Reserve Bank of Australia', boardAssetId: 'aud',
      meetings: [{ decisionDate: '2026-08-11', modalOutcome: '25 bps increase',
        modalProbability: 0.62, impliedDirection: 'hawkish' }] },
    { id: 'fed', name: 'Federal Reserve', boardAssetId: 'dxy',
      meetings: [{ decisionDate: '2026-07-29', modalOutcome: 'No change',
        modalProbability: 0.74, impliedDirection: 'hold' }] },          // hold -> no signal
    { id: 'boe', name: 'Bank of England', boardAssetId: null,
      meetings: [{ decisionDate: '2026-08-01', modalOutcome: '25 bps increase',
        modalProbability: 0.80, impliedDirection: 'hawkish' }] },       // no board asset -> no signal
    { id: 'boc', name: 'Bank of Canada', boardAssetId: 'cad-not-a-real-asset',
      meetings: [{ decisionDate: '2026-09-02', modalOutcome: '25 bps decrease',
        modalProbability: 0.52, impliedDirection: 'dovish' }] },        // <55% AND unknown asset
  ],
};
const cbSignals = engine.deriveRateDecisionSignals(cbSource);
assert.strictEqual(cbSignals.length, 1, 'only RBA clears the gate with a mapped asset');
assert.strictEqual(cbSignals[0].assetId, 'aud');
assert.strictEqual(cbSignals[0].direction, 'up');            // hawkish -> up
assert.strictEqual(cbSignals[0].source, 'rate-decision-odds');
assert.strictEqual(engine.deriveRateDecisionSignals({}).length, 0);   // empty-safe

// folds into collect under aud
const cbCollected = engine.collectDeterministicSignals({
  freeData: { cot: [], rates: [] }, crowdData: { markets: [] },
  equityData: { watchlist: [] }, cbSource,
});
assert.strictEqual(cbCollected.aud.counts.up, 1);
assert.strictEqual(cbCollected.aud.net, 'up');
```

- [ ] **Step 2: Run to confirm failure**

Run: `node tests/js/impact-engine.test.js`
Expected: FAIL — `engine.deriveRateDecisionSignals is not a function`.

- [ ] **Step 3: Implement the derive function + thread cbSource**

In `site/core/impact-engine.js`, add after `deriveBlsPrintSignals` (before `collectDeterministicSignals`):
```javascript
  // Market-implied central-bank policy lean. Conservative + honest: only banks whose
  // currency we track as a board asset, only when the modal outcome is a decisive
  // (>=55%) non-"no change" call. A priced-in expectation is a slow policy lean, not an
  // event-day trade — kept as its own source so it never conflates with the official
  // print signal (e.g. the RBA cash-rate 'rba' source).
  function deriveRateDecisionSignals(cbSource = {}) {
    const banks = Array.isArray(cbSource.banks) ? cbSource.banks : [];
    const at = typeof cbSource.generatedAtUtc === 'string' ? cbSource.generatedAtUtc.slice(0, 10) : null;
    const status = cbSource.collection?.status || 'current';
    const signals = [];
    banks.forEach((bank) => {
      if (!bank.boardAssetId) return;
      const asset = assetById(bank.boardAssetId);
      if (!asset) return;
      const meeting = (bank.meetings || [])[0];
      if (!meeting) return;
      const modalProb = Number(meeting.modalProbability);
      const direction = meeting.impliedDirection;
      if (!Number.isFinite(modalProb) || modalProb < 0.55 || direction === 'hold') return;
      signals.push({
        assetId: asset.id,
        direction: direction === 'hawkish' ? 'up' : 'down',
        tier: 'observed',
        source: 'rate-decision-odds',
        label: `${bank.name} policy lean`,
        detail: `Market-implied ${bank.name} decision (${meeting.decisionDate || 'date unavailable'}): ${meeting.modalOutcome} at ${Math.round(modalProb * 100)}% — a ${direction} lean for ${asset.label}. This is a priced-in expectation, not an event-day move.`,
        at,
        status,
        href: '',
      });
    });
    return signals;
  }
```
Then update `collectDeterministicSignals`'s destructure and array:
```javascript
  function collectDeterministicSignals({ freeData, crowdData, equityData, blsSource, cbSource } = {}, options = {}) {
    const all = [
      ...deriveCotSignals(freeData),
      ...deriveRateSignals(freeData),
      ...deriveCrowdSignals(crowdData),
      ...deriveEtfSignals(equityData),
      ...deriveBlsPrintSignals(blsSource),
      ...deriveRateDecisionSignals(cbSource),
    ];
```
Add `deriveRateDecisionSignals,` to the `Object.freeze({ ... })` export block.

- [ ] **Step 4: Run to confirm pass**

Run: `node tests/js/impact-engine.test.js`
Expected: `impact-engine tests passed`.

- [ ] **Step 5: Commit**

```bash
git add site/core/impact-engine.js tests/js/impact-engine.test.js
git commit -m "feat(rate-decisions): policy-lean signal in the impact engine"
```

---

## Task 5: Board wiring (home + week + asset views)

**Files:**
- Modify: `site/features/command-centre/command-page.js`
- Modify: `site/features/week/week-page.js`
- Modify: `site/features/asset-workspace/asset-page.js`

**Interfaces:**
- Consumes: `window.centralBankDecisionsData` (set by Task 6's loader), `engine.collectDeterministicSignals` (Task 4)
- Produces: board renders fold the policy-lean signal; repaint on `marketbrief:central-bank-decisions`

- [ ] **Step 1: Wire the home board**

In `site/features/command-centre/command-page.js`, add a slice helper next to `officialSlice` (after line 196):
```javascript
  function cbDecisionsSlice() {
    // Eager loader sets window.centralBankDecisionsData; the board repaints via
    // patchPressureBoard() on 'marketbrief:central-bank-decisions'.
    return window.centralBankDecisionsData || {};
  }
```
In `pressureBoardInner`, add `cbSource` to the collect call (inside the object passed to `collectDeterministicSignals`, alongside `blsSource: officialSlice(),`):
```javascript
        blsSource: officialSlice(),
        cbSource: cbDecisionsSlice(),
```
At the bottom, next to the official-feeds listener (line 384), add:
```javascript
  window.addEventListener('marketbrief:central-bank-decisions', patchPressureBoard);
```

- [ ] **Step 2: Verify the home board still renders (manual smoke)**

Run: `python -m http.server 8099 --directory site` then open `http://localhost:8099/#home`.
Expected: the Pressure Board renders; the AUD/USD row shows an extra `↑` when the seeded RBA market has a decisive hike lean (or is unchanged when it's "no change" — both are correct). No console errors.

- [ ] **Step 3: Wire the week + asset views**

In `site/features/week/week-page.js` and `site/features/asset-workspace/asset-page.js`, find each existing `collectDeterministicSignals({ ... blsSource: ... })` call and add `cbSource: window.centralBankDecisionsData || {},` to the object. Add a repaint listener mirroring each file's existing `marketbrief:official-feeds` handler — locate the line `window.addEventListener('marketbrief:official-feeds', <handler>)` in each file and add directly beneath it:
```javascript
  window.addEventListener('marketbrief:central-bank-decisions', <sameHandler>);
```
(Use the exact handler name each file already registers for the official-feeds event.)

- [ ] **Step 4: Smoke week + a dossier**

Reload `http://localhost:8099/#week` and `http://localhost:8099/#asset/aud`.
Expected: both render without console errors; AUD pressure reflects the policy lean consistently with `#home`.

- [ ] **Step 5: Commit**

```bash
git add site/features/command-centre/command-page.js site/features/week/week-page.js site/features/asset-workspace/asset-page.js
git commit -m "feat(rate-decisions): fold CB policy-lean into the pressure board (home/week/asset)"
```

---

## Task 6: Eager data global + view scaffold (nav, container, manifest, loader)

**Files:**
- Create: `site/features/rate-decisions/rate-decisions-data.js`
- Modify: `site/index.html`
- Modify: `site/core/feature-loader.js`
- Test: `tests/test_central_bank_decisions.py` (structural assertions)

**Interfaces:**
- Produces: `window.centralBankDecisionsData` global + `marketbrief:central-bank-decisions` event; a `#view-rate-decisions` container; nav item `data-view="rate-decisions"`; manifest route `rate-decisions`.

- [ ] **Step 1: Write the eager loader** (clone `official-feeds-data.js`)

`site/features/rate-decisions/rate-decisions-data.js`:
```javascript
(() => {
  'use strict';
  const EMPTY = Object.freeze({ schemaVersion: 1, generatedAtUtc: null,
    provider: { id: 'polymarket', name: 'Polymarket', readOnly: true },
    collection: { status: 'unavailable', banksCovered: 0, lastSuccessfulAt: null, error: 'Central-bank decisions have not loaded.' },
    banks: [], methodology: {}, sourceStatus: [] });
  async function load() {
    try {
      const response = await fetch('data/central-bank-decisions.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      window.centralBankDecisionsData = data;
      window.dispatchEvent(new CustomEvent('marketbrief:central-bank-decisions', { detail: data }));
    } catch (error) {
      window.centralBankDecisionsData = { ...EMPTY, collection: { ...EMPTY.collection, error: `Unable to load central-bank decisions: ${error.message}` } };
      window.dispatchEvent(new CustomEvent('marketbrief:central-bank-decisions', { detail: window.centralBankDecisionsData }));
    }
  }
  window.centralBankDecisionsData = window.centralBankDecisionsData || EMPTY;
  load();
})();
```

- [ ] **Step 2: Add the eager script tag** in `site/index.html` immediately after line 238 (`official-feeds-data.js`):
```html
<script src="features/rate-decisions/rate-decisions-data.js"></script>
```

- [ ] **Step 3: Add the nav button** in `site/index.html` immediately after the Rates button (line 59), still under the "Evidence" section:
```html
      <button type="button" class="nav-item" data-view="rate-decisions" aria-label="Rate decisions" title="Rate decisions — central-bank probabilities" data-tooltip="Rate decisions"><span class="nav-icon" aria-hidden="true"><svg><use href="#i-activity"/></svg></span><span class="nav-label">Rate decisions</span></button>
```

- [ ] **Step 4: Add the view container** in `site/index.html` immediately after the `view-rates` section (after line 114):
```html
      <section class="view" id="view-rate-decisions">
        <div class="hero"><div><div class="eyebrow">Market-implied central-bank probabilities</div><h2>Rate decisions</h2><p class="data-hero-note">Per-bank, per-meeting odds of each rate outcome with how the odds evolved — read-only Polymarket data, shown beside the last actual decision where we hold it.</p></div><span class="badge" id="rateDecisionsUpdated">Awaiting data</span></div>
        <div id="rateDecisionsMount"><div class="command-empty">Loading rate decisions…</div></div>
      </section>
```

- [ ] **Step 5: Register the route allow-list.** Grep for every place the `cot` route is enumerated as a known/supported view and add `rate-decisions` alongside it:

Run: `grep -rn "'cot'" site/app.js site/free-data-ui.js site/core/router.js`
For each allow-list array that contains `'cot'` (e.g. a `supported`/known-views list in `site/app.js` / `site/free-data-ui.js`), add `'rate-decisions'`. If no allow-list gates it (route driven purely by `core.router`), no change is needed — Step 8's smoke confirms navigation works.

- [ ] **Step 6: Add the manifest route** in `site/core/feature-loader.js`, inside the `manifest` array (after the `crowd-expectations` entry, line 53):
```javascript
    Object.freeze({ route: 'rate-decisions', styles: ['features/rate-decisions/rate-decisions-page.css'], scripts: ['features/rate-decisions/rate-decisions-page.js'] }),
```

- [ ] **Step 7: Write structural tests**

Add to `tests/test_central_bank_decisions.py`:
```python
def test_eager_loader_and_nav_are_wired():
    index_html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert "features/rate-decisions/rate-decisions-data.js" in index_html
    assert 'data-view="rate-decisions"' in index_html
    assert 'id="view-rate-decisions"' in index_html
    loader = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
    assert "route: 'rate-decisions'" in loader
    engine = (ROOT / "site" / "core" / "impact-engine.js").read_text(encoding="utf-8")
    assert "deriveRateDecisionSignals" in engine and "rate-decision-odds" in engine
```

- [ ] **Step 8: Run tests + smoke navigation**

Run: `python -m pytest tests/test_central_bank_decisions.py -q` (all PASS).
Then `python -m http.server 8099 --directory site`, click the "Rate decisions" nav item.
Expected: URL becomes `#rate-decisions`, the `#view-rate-decisions` section becomes active (shows the "Loading…" placeholder — the page module lands in Task 7). No console errors.

- [ ] **Step 9: Commit**

```bash
git add site/features/rate-decisions/rate-decisions-data.js site/index.html site/core/feature-loader.js tests/test_central_bank_decisions.py
git commit -m "feat(rate-decisions): eager data global + nav/view scaffold + route"
```

---

## Task 7: The Rate decisions view (render + styles)

**Files:**
- Create: `site/features/rate-decisions/rate-decisions-page.js`
- Create: `site/features/rate-decisions/rate-decisions-page.css`

**Interfaces:**
- Consumes: `window.centralBankDecisionsData`, `window.officialFeedsData` (for the "last actual" merge), `core.router`
- Produces: renders bank cards into `#rateDecisionsMount`; self-registers route `rate-decisions`

- [ ] **Step 1: Write the view module**

`site/features/rate-decisions/rate-decisions-page.js` (mirrors `cot-page.js`'s `core.router.subscribe` + `#view-*` render pattern):
```javascript
(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  const escapeHtml = core.format?.escapeHtml || ((v = '') => String(v)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  // Only the RBA has an official "last actual" print today (the rba-cash-rate series).
  const OFFICIAL_SERIES_BY_BANK = { rba: 'rba-cash-rate' };

  function data() { return window.centralBankDecisionsData || { banks: [], collection: {} }; }

  function lastActual(bankId) {
    const seriesId = OFFICIAL_SERIES_BY_BANK[bankId];
    if (!seriesId) return null;
    const sources = Array.isArray(window.officialFeedsData?.sources) ? window.officialFeedsData.sources : [];
    for (const source of sources) {
      const record = (source.records || []).find((r) => r.id === seriesId);
      if (record) return record;
    }
    return null;
  }

  function sparkline(history = []) {
    const points = history.filter((p) => Number.isFinite(Number(p.probability)));
    if (points.length < 2) return '<span class="rd-spark-empty">history building…</span>';
    const w = 96, h = 24;
    const xs = (i) => (points.length === 1 ? 0 : (i / (points.length - 1)) * w);
    const ys = (p) => h - Number(p) * h;
    const d = points.map((p, i) => `${xs(i).toFixed(1)},${ys(p.probability).toFixed(1)}`).join(' ');
    return `<svg class="rd-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${d}" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>`;
  }

  function outcomeRow(outcome, modalLabel) {
    const pct = Number(outcome.probabilityPercent) || 0;
    const isModal = outcome.label === modalLabel;
    return `<div class="rd-outcome ${isModal ? 'is-modal' : ''}">
      <span class="rd-outcome-label">${escapeHtml(outcome.label)}</span>
      <span class="rd-outcome-bar"><span style="width:${Math.max(2, Math.min(100, pct))}%"></span></span>
      <span class="rd-outcome-pct">${pct.toFixed(1)}%</span>
      ${sparkline(outcome.history)}
    </div>`;
  }

  function meetingCard(meeting) {
    const dir = meeting.impliedDirection || 'hold';
    return `<article class="rd-meeting">
      <header><h4>${escapeHtml(meeting.decisionDate || 'Date unavailable')}</h4>
        <span class="rd-lean rd-lean-${escapeHtml(dir)}">${escapeHtml(dir)}</span></header>
      <div class="rd-outcomes">${(meeting.outcomes || []).map((o) => outcomeRow(o, meeting.modalOutcome)).join('')}</div>
      <footer><a href="${escapeHtml(meeting.marketUrl || 'https://polymarket.com/')}" target="_blank" rel="noopener noreferrer">View market ↗</a></footer>
    </article>`;
  }

  function bankCard(bank) {
    const actual = lastActual(bank.id);
    const actualRow = actual
      ? `<p class="rd-actual">Last actual: ${escapeHtml(String(actual.change))} ${escapeHtml(actual.unit || '')} on ${escapeHtml(actual.observedAt || '—')} <span>(official print)</span></p>`
      : '';
    const meetings = (bank.meetings || []);
    return `<section class="rd-bank">
      <div class="rd-bank-head"><span class="rd-flag" aria-hidden="true">${escapeHtml(bank.flag || '')}</span>
        <div><h3>${escapeHtml(bank.name)}</h3><span class="rd-ccy">${escapeHtml(bank.currency || '')}</span></div></div>
      ${actualRow}
      <div class="rd-meetings">${meetings.length ? meetings.map(meetingCard).join('') : '<div class="command-empty">No live decision market.</div>'}</div>
    </section>`;
  }

  function render() {
    const mount = document.getElementById('rateDecisionsMount');
    if (!mount) return;
    const feed = data();
    const banks = (feed.banks || []).filter((b) => (b.meetings || []).length);
    const badge = document.getElementById('rateDecisionsUpdated');
    if (badge) badge.textContent = feed.collection?.status === 'current'
      ? `${feed.collection.banksCovered} central banks`
      : (feed.collection?.status || 'Unavailable');
    mount.innerHTML = banks.length
      ? `<div class="rd-grid">${banks.map(bankCard).join('')}</div>
         <p class="rd-methodology">Read-only Polymarket market-implied probabilities. A probability is crowd expectation, not a forecast or trade recommendation.</p>`
      : '<div class="command-empty">No central-bank decision markets are currently available.</div>';
  }

  if (document.getElementById('view-rate-decisions')) render();
  core.router?.subscribe?.((route) => { if (route.name === 'rate-decisions') render(); });
  window.addEventListener('marketbrief:central-bank-decisions', render);
  window.addEventListener('marketbrief:official-feeds', render);
})();
```

- [ ] **Step 2: Write the styles**

`site/features/rate-decisions/rate-decisions-page.css` — grid of bank cards, outcome bars, modal highlight, sparkline color, lean chips. Follow `crowd-page.css` visual tokens (dark theme, `var(--...)` where the project defines them). Minimum viable, theme-consistent:
```css
.rd-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.rd-bank { border: 1px solid rgba(255,255,255,.08); border-radius: 12px; padding: 14px; background: rgba(255,255,255,.02); }
.rd-bank-head { display: flex; gap: 10px; align-items: center; margin-bottom: 6px; }
.rd-flag { font-size: 20px; }
.rd-ccy { font-size: 12px; opacity: .6; }
.rd-actual { font-size: 12px; opacity: .75; margin: 4px 0 10px; }
.rd-actual span { opacity: .6; }
.rd-meeting { border-top: 1px solid rgba(255,255,255,.06); padding-top: 10px; margin-top: 10px; }
.rd-meeting header { display: flex; justify-content: space-between; align-items: center; }
.rd-meeting h4 { margin: 0; font-size: 13px; }
.rd-lean { font-size: 11px; text-transform: uppercase; padding: 2px 6px; border-radius: 999px; }
.rd-lean-hawkish { background: rgba(34,197,94,.15); color: #22c55e; }
.rd-lean-dovish { background: rgba(239,68,68,.15); color: #ef4444; }
.rd-lean-hold { background: rgba(148,163,184,.15); color: #94a3b8; }
.rd-outcome { display: grid; grid-template-columns: 92px 1fr 46px 96px; gap: 8px; align-items: center; padding: 3px 0; font-size: 12px; }
.rd-outcome.is-modal { font-weight: 600; }
.rd-outcome-bar { background: rgba(255,255,255,.06); border-radius: 4px; height: 8px; overflow: hidden; }
.rd-outcome-bar span { display: block; height: 100%; background: currentColor; opacity: .55; }
.rd-outcome.is-modal .rd-outcome-bar span { opacity: .9; }
.rd-spark { width: 96px; height: 24px; opacity: .7; }
.rd-spark-empty { font-size: 10px; opacity: .5; }
.rd-methodology { font-size: 11px; opacity: .6; margin-top: 14px; }
```

- [ ] **Step 3: Smoke the full view**

Run `python -m http.server 8099 --directory site`, open `http://localhost:8099/#rate-decisions`.
Expected: bank cards render (Fed/ECB/BoE/BoJ/RBA/BoC/BoK/Banxico/RBNZ where markets exist), each meeting shows the 5-outcome ladder with the modal highlighted, sparklines show "history building…" on first load, RBA shows a "Last actual" line from the official cash-rate print. No console errors.

- [ ] **Step 4: Commit**

```bash
git add site/features/rate-decisions/rate-decisions-page.js site/features/rate-decisions/rate-decisions-page.css
git commit -m "feat(rate-decisions): render the Rate decisions view + styles"
```

---

## Task 8: Refresh workflow + docs

**Files:**
- Create: `.github/workflows/update-central-bank-decisions.yml`
- Modify: `docs/DATA-SOURCES.md` (add the new source), `docs/PROJECT-STATUS.md` (note the feature)

**Interfaces:** none (CI/ops)

- [ ] **Step 1: Write the workflow** (clone `.github/workflows/update-crowd-expectations.yml`; keep the identical permissions, `concurrency.group: generated-data-writer`, checkout, Python setup, and commit-generated-data steps). Change: name, the `paths:` trigger list to the new files, the schedule, and the run/validate commands:
```yaml
name: Update central bank decisions

on:
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - 'scripts/update_central_bank_decisions.py'
      - 'scripts/validate_central_bank_decisions.py'
      - 'scripts/central_bank_registry.json'
      - 'schemas/central-bank-decisions.schema.json'
      - 'tests/test_central_bank_decisions.py'
      - '.github/workflows/update-central-bank-decisions.yml'
      - '.github/workflows/deploy-pages.yml'
  schedule:
    - cron: '47 */6 * * *'   # every 6h, offset 30min from crowd-expectations (:17)

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: generated-data-writer
  cancel-in-progress: false
```
For the job body, copy the `update` job from `update-crowd-expectations.yml` verbatim and replace only the run + validate + commit-path lines:
```yaml
      - name: Compile guard
        run: python -m py_compile scripts/update_central_bank_decisions.py scripts/validate_central_bank_decisions.py tests/test_central_bank_decisions.py
      - name: Collect central bank decisions
        run: python scripts/update_central_bank_decisions.py
      - name: Validate
        run: python scripts/validate_central_bank_decisions.py
```
And the commit step must `git add site/data/central-bank-decisions.json` (mirror crowd's generated-data commit + push + deploy trigger exactly).

- [ ] **Step 2: Validate the workflow YAML parses**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/update-central-bank-decisions.yml')); print('yaml ok')"`
Expected: `yaml ok`.

- [ ] **Step 3: Add docs**

In `docs/DATA-SOURCES.md`, add a row/section for "Central-bank decisions — Polymarket public-search, read-only, every 6h → `site/data/central-bank-decisions.json`". In `docs/PROJECT-STATUS.md`, note the "Rate decisions" view shipped.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/update-central-bank-decisions.yml docs/DATA-SOURCES.md docs/PROJECT-STATUS.md
git commit -m "ci(rate-decisions): 6-hourly refresh workflow + docs"
```

---

## Task 9: Full-suite verification + PR

**Files:** none (verification)

- [ ] **Step 1: Run the whole test suite**

Run: `python -m pytest tests/ -q` and `node tests/js/impact-engine.test.js`
Expected: all green except the pre-existing, unrelated `test_runtime_registry_keeps_source_failures_independent` freshness-registry flake (date-fragile; red on every PR — confirm it's the same known failure and nothing new).

- [ ] **Step 2: Final board + view smoke**

Serve `site/`, verify `#home`, `#week`, `#asset/aud`, and `#rate-decisions` all render without console errors, and the AUD row's pressure is consistent across home/week/dossier.

- [ ] **Step 3: Push + open PR (STOP before merge)**

```bash
git push -u origin feat/central-bank-decision-tracker
gh pr create --base main --title "feat(rate-decisions): central-bank decision-probability tracker" --body "Slice 1 of the MRKT-EDGE parity arc. New 'Rate decisions' view + policy-lean board signal, from the Polymarket feed we already integrate. See docs/superpowers/specs/2026-07-25-central-bank-decision-tracker-design.md. 🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```
**STOP.** Per the standing hard rule, do not merge — push + PR only, then hand back for review.

---

## Self-Review

**1. Spec coverage:**
- §3 full multi-bank (9 banks) → registry (Task 1) + collector (Task 2). ✓
- §4 provider/provenance/history/security invariant → registry provider block, `validate_output` TRADING_MARKERS, committed TLS (no bypass in code), `day_snapshot` history. ✓
- §5.1 collector → Tasks 1–2. §5.2 data model → Task 2 shape + Task 3 schema. §5.3 view (nav additive, per-bank cards, sparklines, provenance link, last-actual) → Tasks 6–7. §5.4 board wiring (Fed→dxy, RBA→aud, ≥55% gate, distinct source) → Tasks 4–5. ✓
- §6 testing (collector, schema/validator, impact-engine, view smoke) → Tasks 1–7. ✓
- §7 rollout (workflow, seed) → Task 3 Step 3 (seed) + Task 8 (workflow). ✓

**2. Placeholder scan:** No "TBD/TODO"; all code blocks are concrete. Task 5 Step 3 references "the exact handler name each file already registers" — this is a deliberate instruction to read two specific existing lines, not a placeholder (the pattern is shown).

**3. Type consistency:** `cbSource` shape `{generatedAtUtc, collection:{status}, banks:[{boardAssetId, meetings:[{decisionDate, modalOutcome, modalProbability, impliedDirection}]}]}` is identical across the collector output (Task 2), the schema (Task 3), the derive function + tests (Task 4), and the view (Task 7). Signal object keys (`assetId, direction, tier, source, label, detail, at, status, href`) match the existing signal shape in impact-engine. `deriveRateDecisionSignals` name identical in impl, export, and test.

**Correction vs spec:** cadence is **every 6 hours** (spec said "hourly" based on a wrong recollection of the crowd collector's cadence). Fed board asset id is **`dxy`** (the spec prose said "US dollar", which is the label). Both reconciled in Global Constraints.
