# Trader Pressure Board — design spec

Date: 16 July 2026
Status: approved in brainstorm (Chris), pending spec review
Predecessor: `docs/superpowers/plans/2026-07-16-ui-revamp-mrktedge.md` (visual revamp, shipped as PR #42)

## 1. Goal

Remodel market-brief from a **source-organised data catalogue** into an **asset-first trading brief**. The product answers, at a glance: *what is pressuring each asset I trade, in which direction, on what evidence?* The directional impact chip (`Brent ↑`, `Risk assets ↓`) becomes the universal grammar of the app, applied to every signal type, with an aggregated net-pressure view per asset.

Reference product: mrktedge.ai. We match its legibility (chips, net arrows, asset pages) while keeping this repo's stricter honesty rules (trust tiers, visible failure states, no invented numbers).

### Operating profile (decided)

- **User rhythm:** morning brief, swing/position horizon (days–weeks). Daily pipeline cadence is sufficient; no real-time ambition.
- **Second rhythm:** a Sunday catch-up — "what happened this week" — for weeks with no daily check-ins.
- Conviction and evidence over speed. Contested evidence is itself signal.

## 2. Decisions locked during brainstorm

1. **Tagging engine:** Claude tags unstructured news in the existing scheduled pipelines (Haiku-class model, `ANTHROPIC_API_KEY` as a GitHub Actions secret). Structured data is chip-tagged deterministically in Python/JS — no model involved.
2. **Asset vocabulary:** closed board of 18 hard assets + 4 themes (below). Individual watchlist tickers are *not* first-class chip targets; they inherit via themes and get direct chips only from deterministic ticker-keyed sources (SEC filings, political disclosures).
3. **Remodel shape:** Approach A — "Pressure Board" pivot. Home becomes the board; asset dossiers aggregate evidence; existing source pages survive intact but demoted to an Evidence nav group.
4. **Views:** `Today` (24h window) and `This week` (trailing 7 days) as a toggle on the home view, deep-linkable (`#week`).
5. **News sources:** no new firehoses. Add GDELT topic queries for the broadened board, a USDA official-feed family, RBA media releases, and repair the failed `asx-announcements` source. No paid wires, no X/Twitter, no scraping.

## 3. Asset board (closed vocabulary)

New registry file shared by pipeline and site (single source of truth): `scripts/asset_board.json`, copied/emitted into `site/data/asset-board.json` by the pipeline so the browser never depends on `scripts/`.

| Family | Asset id | Label | Price join | CFTC COT |
|---|---|---|---|---|
| Energy | `brent` | Brent | if free feed exists | yes (ICE Brent via CFTC-published where available, else honest absent) |
| Energy | `wti` | WTI | yes | yes |
| Energy | `henry-hub` | US natural gas (Henry Hub) | if free feed exists | yes |
| Energy | `ttf` | EU gas (TTF) | likely none → honest state | no |
| Energy | `nbp` | UK gas (NBP) | likely none → honest state | no (ICE Europe, outside CFTC) |
| Metals | `gold` | Gold | yes | yes |
| Metals | `silver` | Silver | yes | yes |
| Metals | `copper` | Copper | yes | yes |
| Metals | `iron-ore` | Iron ore | likely none → honest state | no |
| Softs/Ags | `wheat` | Wheat | if free feed exists | yes |
| Softs/Ags | `cocoa` | Cocoa | if free feed exists | yes |
| Softs/Ags | `coffee` | Coffee | if free feed exists | yes |
| Rates/FX | `us10y` | US 10Y yield | yes (FRED) | no |
| Rates/FX | `dxy` | US dollar (DXY) | FRED broad-dollar index, labelled as such (true DXY is licensed) | no (USD index COT optional later) |
| Rates/FX | `aud` | AUD/USD | yes | yes |
| Indices | `spx` | S&P 500 | yes (SPY join) | yes (e-mini) |
| Indices | `ndx` | Nasdaq | yes (QQQ join) | yes (e-mini) |
| Indices | `asx200` | ASX 200 | if free feed exists | no |
| Theme | `inflation-risk` | Inflation risk | n/a | n/a |
| Theme | `risk-assets` | Risk assets | n/a | n/a |
| Theme | `semis` | Semiconductors | SMH/SOXX joins | n/a |
| Theme | `rare-earths` | Rare earths & critical minerals | REMX join | n/a |

Registry entry shape:

```json
{
  "id": "gold",
  "label": "Gold",
  "kind": "asset",            // or "theme"
  "family": "Metals",
  "priceJoin": {"source": "free-market-data", "key": "gold"},   // optional
  "cotMarket": "GOLD - COMMODITY EXCHANGE INC.",                 // optional, exact CFTC market name
  "memberTickers": []          // themes only: e.g. semis → ["nvda","amd","smh", ...]
}
```

"Price join" values marked *if free feed exists* are resolved during implementation against what `update_free_data.py` / Twelve Data can actually supply; any asset without a working join renders the explicit **"no price feed"** state. Never a fake or stale-unlabelled number.

## 4. Data architecture

### 4.1 Claude tagger (unstructured news → chips)

- New script `scripts/tag_impacts.py`, invoked as a step in the **existing** scheduled workflows after data fetch: GDELT radar (hourly cron) and conflict watch. v1 scope: GDELT articles + conflict-watch updates. Official-feed numeric records and SEC filings are **not** sent to the model (deterministic paths below).
- Only items whose id is not already in the ledger are tagged (append-only; tags never flap; re-runs are no-ops).
- Batched call, Haiku-class model (`claude-haiku-4-5`). Input per item: headline, source domain, topic id, seenAt. The prompt carries the closed vocabulary (ids + labels) from the registry.
- Output per item, strict JSON:

```json
{
  "itemId": "de8d8131fe4c9df45cac",
  "tags": [
    {"assetId": "brent", "direction": "up", "confidence": "medium",
     "mechanism": "Renewed Gulf blockade pressure raises seaborne supply risk."}
  ]
}
```

  An empty `tags` array is a valid, expected answer ("no clear asset impact") and is stored, so the item is never re-sent.
- **Validator** (`scripts/validate_impact_tags.py` + unit tests): drops any tag whose `assetId` is outside the registry, whose `direction` is not `up|down|mixed`, or whose `confidence` is not `high|medium|low`. Malformed model output for an item → item recorded as `tagFailed` (retried next run, max 3 attempts, then honest "tagging unavailable").
- **Ledger** `site/data/impact-tags.json`: self-contained — alongside tags it stores a compact copy of each item (headline, url, domain, seenAt, topic), because the GDELT snapshot file only retains the latest pull. Rolling **7-day** prune keeps the Sunday week view fully renderable from this one file. Size ≈ 60 items/day × 7d × ~350B ≈ 150 KB; gets its own byte-budget entry in `scripts/audit_static_site.py`.
- **Fail-open honesty:** if the API call fails, the workflow still succeeds; new items ship untagged and the UI shows "AI tagging unavailable" on affected items and a degraded-state note on the board.
- Cost envelope: ~50–60 new items/day → cents per day.

### 4.2 Deterministic chips (no model)

| Source | Rule | Tier |
|---|---|---|
| Price data (free-market-data, equity data) | sign of day/week change → observed direction on that asset | Observed |
| COT weekly | week-over-week managed-money net position change per mapped `cotMarket` → direction chip on the board asset | Observed |
| FRED/BLS prints | print vs prior → observed direction on the series; a small **visible rules table** (in methodology and in the registry repo file) maps selected series to theme chips, e.g. CPI hotter → `inflation-risk ↑` | Observed |
| Crowd expectations | week-over-week probability swing ≥ 5 percentage points → chip on mapped asset/theme | Observed |
| SEC filings (already ticker-keyed) | ticker → owning theme chip (e.g. NVDA 8-K → `semis`), direction-less "activity" chip unless numeric | Observed |
| Political disclosures | disclosed buy/sell → ticker → theme inheritance chip, low visual weight, existing delay warnings retained | Observed |
| Calendar | upcoming events → **watch-only chips** (no direction before the event exists) | n/a |

### 4.3 Trust tiers

Every chip carries a tier, visible in its styling:

1. **Observed** — it happened (price, positioning, prints). Solid fill.
2. **Verified** — the hand-curated daily brief (`intelligence-data.js`), human-tagged with mechanism + confirmation/invalidation. Outlined + check glyph.
3. **AI-tagged** — Claude-tagged news. Outlined + small "AI" badge; `low` confidence renders dimmed.

### 4.4 Aggregation (impact-engine)

New shared browser module `site/core/impact-engine.js` (classic script, `window.MarketBriefCore.impactEngine`), the only place aggregation logic lives — board, dossiers, and chip strips cannot disagree.

Net pressure per asset over a window (24h or 7d), from directional signals (`mixed` counts toward neither side but is displayed):

- `up > 0` and `up ≥ 2 × down` → net **↑**
- `down > 0` and `down ≥ 2 × up` → net **↓**
- no signals at all → **QUIET** (dimmed)
- otherwise → **CONTESTED**

No weighted magic score. Counts are always shown (`3↑ 1↓`); tier ranks the *ordering* of evidence, not a multiplier. These rules are contract-tested.

### 4.5 Curated-brief archive

A small step in an existing daily workflow snapshots the current `intelligence-data.js` newsFeed items into a rolling 7-day archive `site/data/brief-archive.json` (keyed by date + item id, deduped). Powers the week view's day-by-day digest and dossiers' Verified tier beyond today.

## 5. UX / IA

### 5.1 Navigation (three groups)

- **Brief:** Today (home), Assets (board index → dossiers)
- **Evidence:** News radar (GDELT), Official feeds, COT, Rates, Crowd consensus, Political flow, Conflict watch, Calendar — existing pages, layouts and contract tests intact, cards gain chip strips
- **System:** Source health, Data, Methodology

### 5.2 Today (home)

Top to bottom:

1. **Verdict line** — existing serif regime verdict + as-of + "N new signals since yesterday".
2. **Pressure board** — assets grouped by family. Each row: label · net arrow / CONTESTED / QUIET · signal counts (`3↑ 1↓`) · observed price move (or honest dash) · strongest driver headline. Row click → dossier.
3. **Top drivers** — 3–5 heaviest-tagged items of the last 24h, chips inline.
4. **Watchpoints today** — calendar releases due + standing confirmation/invalidation triggers from the curated brief.

Command Centre's regime verdict moves here; its remaining panels stay reachable under Evidence.

### 5.3 This week (`#week` toggle on home)

Same board grammar over the trailing 7 days, plus:

- **Day-by-day digest** — one strip per day: that day's curated brief items + heaviest AI-tagged headlines (ranked by tag count, then confidence; from the self-contained ledger + brief archive).
- **This week's COT shifts** — featured block (COT lands Friday night AEST; the Sunday review always has it fresh).
- **Crowd swings of the week** — largest probability moves.
- **Week ahead** — next 7 days of calendar releases + standing invalidation triggers.

Week price change shown where price history exists; honest dash otherwise.

### 5.4 Asset dossier (`#asset/<id>`)

The "should I still be in this trade" page. Header: label, family, net pressure + counts, price (chart where history exists), COT positioning snapshot, with explicit "no price feed" / "no COT coverage" states (e.g. NBP has neither — it renders news + curated evidence only, and says so).

Body: **evidence stack in tier order** — Observed (price move, COT shift, mapped prints) → Verified (curated items: mechanism, confirmation, invalidation) → AI-tagged (headline, domain, time, direction chip, confidence, one-line mechanism, outbound link). Default window 7 days with day dividers. Empty state: "No signals in the current window."

Theme dossiers additionally list member tickers with day moves (from equity data) — the Semis → NVDA inheritance made visible.

### 5.5 Chip component (universal)

One component everywhere: asset label + direction arrow. Arrow **and** colour encode direction (↑ positive / ↓ negative / ↔ mixed-grey) — survives colourblindness. Tier styling per §4.3. Every chip, on every page, links to its asset's dossier. Chips are the app's navigation currency.

## 6. News-source changes

1. **GDELT topic queries** (config in `scripts/update_gdelt_radar.py` / its registry): add `ags-softs` (wheat, cocoa, coffee, grain, harvest, drought, export ban…) and a gas-specific expansion (TTF, NBP, gas storage, LNG, pipeline); add *silver* to `strategic-materials`.
2. **USDA official-feed family** (WASDE + export sales) — scheduled mover for wheat; structured; deterministic chips like EIA.
3. **RBA media releases** — official coverage for `aud` / `asx200`.
4. **Repair `asx-announcements`** — currently `status: failed, 0 records`.

Explicitly out: paid wires, X/Twitter, paywalled scraping.

## 7. Honesty & failure states

The repo's existing rule (AGENTS.md: never hide unavailable/partial/stale states) applies to every new surface:

- Tagger down → untagged items say "AI tagging unavailable"; the board shows a degraded-data note.
- No price feed / no COT coverage → labelled dashes, never invented numbers.
- Zero signals → QUIET (dimmed), still rendered.
- Conflicting evidence → CONTESTED, never averaged away.
- AI-tagged chips always visually distinct from Observed/Verified; model name + tagged-at surfaced in item detail.
- Generated files (`site/free-data.js`, `political-data.js`, `equity-data.js`, `site/data/*`) remain pipeline-owned; the site never hand-edits them.

## 8. Testing

- **Pipeline:** unit tests for the tagger validator (closed vocabulary, enums, malformed output dropped, retry/`tagFailed` path, 7-day prune) and for the brief-archive step. Existing `validate_generated_data.py` pattern extended to the new files.
- **Site:** Python-unittest contract tests (same style as the existing 195) for: impact-engine aggregation rules (net-arrow ≥2:1, QUIET, CONTESTED, mixed handling), chip component markup (tier classes, arrow glyphs, dossier links), board/dossier/week renderers, honest failure strings.
- **Byte budget:** new entries in `scripts/audit_static_site.py` for `impact-tags.json`, `brief-archive.json`, `asset-board.json`, new JS/CSS.
- **Visual:** Playwright screenshot smoke via the existing harness (`market-brief-ui-shots/shoot.js`) for Today, Week, one asset dossier, one theme dossier.

## 9. Rollout (4 PRs, each independently shippable)

1. **PR-1 — grammar:** `asset_board.json` + `impact-engine.js` + chip component, applied to existing cards with **deterministic chips only** (price, COT, prints, crowd, SEC→theme, political→theme). App visibly improves with zero new infra.
2. **PR-2 — tagger:** `tag_impacts.py` + validator + ledger + workflow steps + `ANTHROPIC_API_KEY` secret + fail-open states. News cards light up.
3. **PR-3 — surfaces:** Today/Week home, asset dossiers, nav regroup, brief archive step.
4. **PR-4 — sources:** new GDELT topics, USDA + RBA families, `asx-announcements` repair.

Standard repo rules: work on feature branches, PR only, no merge without explicit approval; `site/**` on main auto-deploys the public Pages site.

## 10. Out of scope

- Real-time / intraday data or streaming.
- Paid data sources.
- Individual watchlist tickers as first-class chip targets (inherit via themes; revisit after v1).
- NBP COT coverage (no free CFTC-equivalent).
- Replacing the hand-curated daily brief (it stays the Verified tier; the tagger complements, not replaces).
