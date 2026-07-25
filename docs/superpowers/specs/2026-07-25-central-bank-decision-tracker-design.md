# Central-Bank Decision-Probability Tracker — Design Spec

- **Date:** 2026-07-25
- **Author:** Chris Ozkoch (with Claude)
- **Status:** Draft for review
- **Arc:** MRKT-EDGE parity upgrades — **Slice 1 of 5**. Confirmed order: (1) CB decision
  tracker → (2) live-ish per-headline AI analysis + tap-to-expand impact chips → (3)
  chart-anchored home (our own chart + our deterministic levels overlaid, not a bare embed)
  → (4) surface supports/flip on the home board → (5) tame the 7,000px wall.
- **Repo:** `TheDiamondDealer/market-brief`

## 1. Goal

Ship a **central-bank decision-probability tracker** — our provenance-clean answer to
MRKT EDGE's marquee "Interest Rate Tracker". For each central bank we show, per upcoming
meeting, the market-implied probability of each rate outcome (No change / ±25 / ±50+ bps),
a sparkline of how those odds evolved, and — where we hold it — the **last actual decision
from official data** next to the market's expectation. Selected decisions also feed the
Pressure Board as a slow-moving "policy-lean" pressure.

**Success = ** a new **Rate decisions** view that matches or exceeds MRKT's bank coverage,
sourced entirely from data with auditable provenance, updating hourly, with the Fed board
numbers tracking MRKT's within normal market drift (verified: our Fed-July no-change 73.0%
vs MRKT 74.0% on 2026-07-25).

## 2. Motivation

MRKT markets the Interest Rate Tracker as a headline paid feature. We already collect the
same *class* of data (Polymarket monetary-policy markets, hourly, with self-accumulating
history) and already render prediction-market probabilities in `crowd-expectations`. The
gap is purely **presentation + coverage**, not data access. Doing it with explicit
per-market provenance (and pairing implied odds with the last *actual* decision) is a
genuine "better than the black box" differentiator, not a copy.

## 3. Scope

**In scope (v1):**
- Full multi-bank coverage matching/exceeding MRKT: **Fed, ECB, BoE, BoJ, RBA, BoC, BoK,
  Banxico, RBNZ** (every bank Polymarket lists with a live decision event).
- A dedicated collector, registry, data file, JSON schema, validator, and hourly workflow.
- A new additive **Rate decisions** nav view.
- Pressure-Board wiring for the banks whose currency we already track as a board asset
  (**Fed → US dollar; RBA → AUD/USD**).

**Out of scope (later slices / follow-ups):**
- Adding new board assets so more banks can feed it: FX assets (EUR/GBP/JPY/CAD/KRW/MXN/NZD)
  for the other six banks, and a **front-end/2Y yield** asset so Fed/RBA policy-lean can drive
  rates (not just the currency). Tracker displays all banks; board wiring waits for the assets.
- OIS/futures-implied odds or non-Polymarket providers.
- Merging or restructuring the existing FRED-yield `rates` view (stays untouched).

## 4. Data source & provenance

**Provider:** Polymarket Gamma API — the same read-only public-market-data provider we
already integrate for `crowd-expectations`. No wallet, auth, or order code. Jurisdiction
note carried over verbatim.

- **Discovery endpoint:** `https://gamma-api.polymarket.com/public-search?q=<bank>` returns
  decision **events**, each with a nested `markets[]` array carrying `groupItemTitle`
  (clean outcome label), `outcomePrices` / `lastTradePrice` / `bestBid` / `bestAsk`
  (probability), `endDate` (meeting date), and liquidity/volume.
- **Outcome labels come from `groupItemTitle`** — no fragile question-text parsing.
- **History self-accumulates** via the existing `day_snapshot` pattern (one point per UTC
  day, capped at 90). New banks start with short sparklines that fill in daily — identical
  to how the Fed history reached 12 points.

**Verified coverage (2026-07-25):**

| Bank | Currency | Live meetings | Outcomes |
|------|----------|---------------|----------|
| Federal Reserve | USD | Jul, Sep, Oct | 5 |
| ECB | EUR | Sep, Oct | 5 |
| Bank of England | GBP | Jul, Sep | 5 |
| Bank of Japan | JPY | Jul, Sep | 5 |
| Reserve Bank of Australia | AUD | Aug | 5 |
| Bank of Canada | CAD | Sep, Oct | 5 |
| Bank of Korea | KRW | Aug | 5 |
| Banxico (Mexico) | MXN | Aug, Sep | 5 |
| Reserve Bank of New Zealand | NZD | Sep | 3 |

Standard 5-outcome ladder: `50+ bps decrease`, `25 bps decrease`, `No change`,
`25 bps increase`, `50+ bps increase`. Thinner banks (e.g. RBNZ) may list a subset; the
model stores whatever outcomes the provider exposes rather than forcing all five.

**Security invariant:** the committed collector keeps TLS certificate verification ON. The
local `NODE_TLS_REJECT_UNAUTHORIZED=0` / `ssl._create_unverified_context()` bypass used for
probing behind the TLS-inspection proxy is LOCAL-ONLY and never ships.

## 5. Architecture

Four well-bounded units, mirroring the existing `crowd-expectations` and `official-feeds`
patterns:

```
central_bank_registry.json ──▶ update_central_bank_decisions.py ──▶ central-bank-decisions.json
   (bank list + mapping)          (targeted per-bank fetch,             (normalized model)
                                   normalize, accumulate history)             │
                                          │                                   ├─▶ rate-decisions view (new)
                                   validate_central_bank_decisions.py         │
                                   + schema                                   └─▶ impact-engine policy-lean signal
                                                                                   ──▶ Pressure Board
```

### 5.1 Collector — `scripts/update_central_bank_decisions.py`
- Iterate the registry's banks; for each, `public-search` for its decision events, keep
  those that are `active && !closed && endDate > now`, and keep all such meetings nearest-first
  (typically 1–3 per bank).
- For each meeting, read the event's `markets[]`; extract probability per outcome via the
  existing `selected_probability` helper (prefer bid/ask midpoint, fall back to
  `lastTradePrice`/`outcomePrices[0]`). Label from `groupItemTitle`.
- Accumulate `history` per outcome with `day_snapshot` (reuse from base collector).
- ~9 search calls per run (one per bank) → low request volume; apply the same request
  spacing/backoff discipline used by the GDELT/crowd collectors.
- Emit provider + `collection.status` (current/stale/unavailable) blocks. On failure,
  retain prior file as `stale` (same resilience contract as official-feeds).

### 5.2 Data model — `site/data/central-bank-decisions.json`
```jsonc
{
  "schemaVersion": 1,
  "generatedAtUtc": "2026-07-25T…Z",
  "provider": { "id": "polymarket", … , "readOnly": true },
  "collection": { "status": "current", "lastSuccessfulAt": "…", "error": null },
  "banks": [
    {
      "id": "rba", "name": "Reserve Bank of Australia", "currency": "AUD",
      "boardAssetId": "aud",                       // null when we track no asset yet
      "lastActual": {                              // from official-feeds when available
        "change": 0.25, "unit": "%", "observedAt": "2026-05-06", "source": "rba-cash-rate"
      },
      "meetings": [
        {
          "decisionDate": "2026-08-11",
          "outcomes": [
            { "label": "No change",       "bps": 0,   "probability": 0.62, "history": [{ "date": "…", "probability": 0.6 }] },
            { "label": "25 bps increase", "bps": 25,  "probability": 0.30, "history": [ … ] }
            /* …full 5-ladder… */
          ],
          "modalOutcome": "No change", "modalProbability": 0.62,
          "expectedBps": 6.5,                       // probability-weighted, display only
          "impliedDirection": "hold",               // hawkish | dovish | hold
          "marketUrl": "https://polymarket.com/event/…"
        }
      ]
    }
  ]
}
```

### 5.3 View — `site/features/rate-decisions/`
- New nav item **"Rate decisions"** in the System/Evidence group, next to `Rates`. Purely
  additive; the FRED-yield `rates` view is untouched.
- Grouped by bank (flag + name + currency). One card per meeting:
  outcome bars (label + %, modal highlighted), the evolution **sparkline**, decision date,
  and a "view market" provenance link.
- **Do-better-than-MRKT:** each bank card shows `lastActual` (the last *actual* decision
  from our official prints, e.g. the RBA cash-rate we already ingest) beside the implied
  odds — "market expects vs last actual," fully sourced. Banks with no official print omit
  the row honestly.
- Reuse `crowd-page.css` patterns; eager-load the data global like `official-feeds-data.js`.

### 5.4 Pressure-Board wiring — `site/core/impact-engine.js`
- New signal family: **policy-lean**, derived from each bank's nearest meeting, for banks
  with a `boardAssetId` (v1: Fed→`us-dollar`, RBA→`aud`).
- Rule (conservative, honest): emit a direction only when the **modal outcome ≥ 55% and is
  not "No change"**. Hike-lean → currency **up**; cut-lean → currency **down**. Otherwise
  **QUIET** (or CONTESTED if two outcomes are near-tied) — never a fabricated direction on a
  coin-flip meeting. (Front-end/2Y yield mapping waits for a rates asset — see §3.)
- Sourced distinctly (`source: 'rate-decision-odds'`, implied/crowd tier) so it is
  transparent and **not conflated** with the official-print signal (the RBA *actual*
  cash-rate stays its own separate evidence — forward expectation vs backward actual).
- Generalizes the `officialSeriesRules` `sign-of-change` pattern shipped for RBA→AUD.
- **Honesty caveat (documented in UI):** an *expected* decision is largely priced in, so
  this is a slow-moving policy *lean*, not an event-day trade signal — consistent with our
  "pressure," not "signal," language.

## 6. Testing

- **Collector unit tests** (`tests/test_central_bank_decisions.py`): event filtering
  (live/upcoming only), outcome extraction from `groupItemTitle` + prices, history
  accumulation/cap, modal/expected/direction computation, stale-retention on failure.
- **Schema + validator** (`schemas/central-bank-decisions.schema.json`,
  `validate_central_bank_decisions.py`): committed-cache validates in CI, mirroring
  `test_official_feeds.py::test_committed_cache_validates`.
- **Impact-engine tests** (`tests/js/impact-engine.test.js`): policy-lean rule — hike-lean
  ≥55% → currency up; no-change/ <55% → QUIET; near-tie → CONTESTED; distinct source; only
  fires for banks with `boardAssetId`.
- **View smoke:** eager-load global present; renders without the data (empty/stale states).

## 7. Rollout

- New GH Actions workflow `update-central-bank-decisions.yml` (hourly + `workflow_dispatch`),
  cloned from `update-crowd-expectations.yml`: py_compile guard, run collector, run
  validator, commit generated `central-bank-decisions.json` (generated-data-on-main pattern),
  chained deploy.
- Ship one feature PR (collector + data + view + wiring + tests). Seed the data file with a
  first successful run so the view is populated on merge; sparklines thicken over the
  following days.

## 8. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Polymarket event titles/slugs drift per meeting cycle | Match by bank search term + `groupItemTitle`, not hard-coded slugs; validator flags empty banks. |
| Thin/illiquid banks (BoK, RBNZ) give noisy odds | Show liquidity; board rule needs ≥55% modal so thin coin-flips read QUIET. |
| Short initial sparklines look empty | Same as Fed's history ramp; render "history building" state < ~5 points. |
| Board double-counts RBA (actual print + implied odds) | Distinct sources/tiers; UI labels forward-expectation vs backward-actual explicitly. |
| Fed markets duplicated with crowd-expectations | Intentional — different lens (biggest shifts vs decision board); no dedup. |

## 9. Open questions

None blocking. Assumed defaults (approved in brainstorming): hourly cadence; keep Fed in
crowd-expectations; conservative ≥55% board mapping; additive "Rate decisions" view.
