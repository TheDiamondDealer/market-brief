# Per-Headline AI "Why It Matters" — Design Spec

**Status:** approved (brainstorm) · 2026-07-26
**Arc:** MRKT-EDGE parity, slice 2 of 5 (see `project_marketbrief_mrkt_parity_arc`)
**Repo:** TheDiamondDealer/market-brief · branch `feat/per-headline-ai-notes`

## Problem

MRKT EDGE ($49.99/mo) markets "live per-headline AI analysis." market-brief already
runs an AI tagger over its GDELT discovery radar, but the analysis it produces is
**buried and fragmentary**:

- [`scripts/tag_impacts.py`](../../../scripts/tag_impacts.py) already returns, per headline, a
  set of `{assetId, direction, confidence, mechanism}` tags via one forced-tool Haiku
  call. Each `mechanism` is a one-sentence "why it matters" — but **per asset**, never a
  single per-headline read.
- [`site/core/impact-chips.js`](../../../site/core/impact-chips.js) renders those tags as
  chips but drops the `mechanism` into a hover `title=` tooltip — **invisible on tap /
  mobile**, and there is no headline-level synthesis anywhere.

So the raw material exists; it is neither synthesized nor surfaced.

## Goal

On each GDELT discovery-radar card, add a **tap-to-expand "Why it matters"** row that
reveals a short, sourced AI reading of the headline — a per-headline synthesis note plus
the per-asset mechanisms that were previously hidden — without overclaiming and without
disturbing the chips' existing dossier navigation.

## Non-goals / scope

- **Only** the GDELT discovery-radar cards ([`gdelt-page.js`](../../../site/features/gdelt-radar/gdelt-page.js)).
  The curated Impact Feed already has its own deep "Show causal detail" expander; the
  week and asset dossiers consume tags differently — all out of scope.
- No persistent watchlist / "monitor" state. MRKT's "tap-to-monitor" is descoped to
  tap-to-expand (progressive disclosure), which also seeds slice 4 (taming the wall).
- No new board FX assets. No change to the curated feed, the chip component's public API,
  or the router.

## Design

### 1. Data contract — the ledger gains a per-item `note`

The append-only 7-day ledger at `site/data/impact-tags.json` gets one new **optional**
field per item:

```
{
  "id": "...", "source": "gdelt", "headline": "...", "url": "...", "domain": "...",
  "seenAt": "...", "topic": "...",
  "tagState": "tagged", "attempts": 0, "taggedAtUtc": "...",
  "note": "A hawkish Fed lifts real yields — supportive for the US dollar and a headwind for gold and rate-sensitive tech.",
  "tags": [ { "assetId": "dxy", "direction": "up", "confidence": "high", "mechanism": "..." }, ... ]
}
```

- `note` is a plain string, `""` when there is no clear read (e.g. empty `tags`).
- **`SCHEMA_VERSION` bumps 1 → 2.** No consumer asserts the ledger's version, and every
  reader must already tolerate mixed item shapes inside the rolling window, so this is a
  documentation signal, not a breaking change. `run()` already stamps `SCHEMA_VERSION`
  on every write, so the first post-deploy cron run re-stamps the whole ledger to v2.

### 2. Tagger — emit the note in the same forced-tool call

No extra API round-trip, still `claude-haiku-4-5`, still fail-open.

- **Tool schema** ([`build_tool`](../../../scripts/tag_impacts.py)): add a `note` property
  (`{"type": "string"}`) to each result object. Keep it **out of `required`** so a model
  that omits it never produces a schema violation — `clean_note` defaults absence to `""`.
- **Prompt** (`SYSTEM_INSTRUCTION`): add one directive — *"For each item also return a
  `note`: one or two plain sentences on how the headline transmits to the assets you
  tagged. Ground it only in those assets; never mention an asset you did not tag. If you
  return no tags, return an empty note."* This keeps the note and the chips consistent and
  blocks invented calls.
- **Validator** ([`validate_impact_tags.py`](../../../scripts/validate_impact_tags.py)):
  add a pure `clean_note(raw_obj) -> str`:
  - non-dict input, missing/`None`/non-string `note` → `""`
  - otherwise `str.strip()`, then hard-cap at **280 chars** (protects the 400 KB ledger
    size budget in `audit_static_site.py` and keeps the UI tidy).
  `validate_item_output` (tags) is **unchanged**, so all 12 existing validator/tagger
  tests stay green.
- **State machine** ([`tag_pending`](../../../scripts/tag_impacts.py)): when an item's
  result validates as `tagged`, also set `entry["note"] = clean_note(raw)`. New entries
  from `_ensure_entry` initialise `note: ""`. `tagFailed` / `unavailable` paths leave the
  existing note untouched. Fail-open, retry-cap, prune, and batching invariants are all
  unchanged.

### 3. Rendering — the "Why it matters" row (interaction model A)

In [`gdelt-page.js`](../../../site/features/gdelt-radar/gdelt-page.js), chips are left
exactly as they are (board assets keep their one-tap `#asset/<id>` dossier links). Each
card additionally renders **one** expander.

**When shown:** the item is `tagState === 'tagged'` **and** has a non-empty `note` **or**
at least one tag. This lights up the ~100 already-tagged items immediately (surfacing
their previously-hidden mechanisms) and adds the synthesis note as the ledger refreshes.
Degrades to nothing when the chip guard (`core.impactChips` + `window.marketAssetBoard`)
is unmet, exactly like the chips do today.

**Markup:**

```
<button class="gdelt-why" data-gdelt-why="<id>" aria-expanded="false" aria-controls="gdelt-why-<id>">
  <span class="gdelt-why-caret" aria-hidden="true">▸</span> Why it matters
</button>
<div class="gdelt-why-panel" id="gdelt-why-<id>" hidden>
  <p class="gdelt-why-note">…note…</p>                     <!-- omitted when note is "" -->
  <ul class="gdelt-why-mechs">
    <li><span class="m-asset up">US dollar ↑</span> — …mechanism…</li> …
  </ul>
  <p class="gdelt-why-prov">AI reading · <model> · <domain> · unverified</p>
</div>
```

- Model name comes from `impactTags.model`; domain from `item.domain`. Asset labels via
  `window.marketAssetBoard`; direction arrow from a small local `{up:'↑',down:'↓',mixed:'↔'}`.
- **Expanded state** lives in a module-level `Set` of item ids (mirrors
  [`impact-page.js`](../../../site/features/impact-feed/impact-page.js)'s `expandedId`).
  The markup reads the Set to set each panel's initial `hidden` + `aria-expanded`, so an
  expanded card survives a data-driven re-render. The click handler toggles the Set and
  mutates that panel's `hidden` + the button's `aria-expanded` in place (no full re-render;
  expansion does not change the render fingerprint). Handlers are (re)bound each render,
  like the existing topic-filter buttons.
- **Accessibility:** real `<button>`, `aria-expanded` + `aria-controls`, visible
  `:focus-visible` ring, caret rotation gated behind `prefers-reduced-motion`.

**CSS** ([`gdelt-page.css`](../../../site/features/gdelt-radar/gdelt-page.css)): new
`.gdelt-why*` rules only, built from existing design tokens (`--border-subtle`,
`--bg-inset`, `--accent`, `--positive`, `--negative`, `--text-muted`). Purely additive —
the existing `.gdelt-tags span`, `.gdelt-ai-chips`, `.gdelt-ai-note` rules are untouched
(asserted by `test_gdelt_impact_chips.py`).

### 4. Honesty & transition

- The panel keeps the radar's existing framing: the provenance line ends `· unverified`,
  and the surrounding "Discovery only" warning is unchanged. **No "live" / "real-time"
  language.** The note is an AI reading of a discovery lead, not a verified call.
- **No backfill.** Already-tagged items show chips + mechanisms now and gain notes as the
  6-hourly cron churns the 7-day window; new items get notes at once. The committed ledger
  stays at v1 until the first post-merge cron run rewrites it to v2 — readers handle both.

## Testing

All automated tests run **without an API key** (the model is never contacted).

- **unittest** (`tests/test_impact_tagger.py`): `clean_note` (strip, 280-cap, non-string →
  `""`, missing → `""`); `tag_pending` stores the note on a tagged item and `""` on
  empty-tags / note-absent; `_ensure_entry` seeds `note: ""`; `build_tool` result schema
  includes a `note` string property.
- **gdelt contract** (`tests/test_gdelt_impact_chips.py`): `gdelt-page.js` contains the
  `gdelt-why` toggle, `data-gdelt-why`, `gdelt-why-panel`, `aria-expanded`, and the
  `unverified` provenance fragment; CSS contains `.gdelt-why` / `.gdelt-why-panel`; the
  existing `node --check` syntax gate still passes.
- **Browser smoke** (Playwright, session scratchpad — not committed): serve the site over
  a **fixture ledger** carrying one note + tags → open `#news`, expand a card, assert the
  note text renders, assert a board-asset chip still has `href^="#asset/"`, assert
  `aria-expanded` toggles, and assert **0 new console errors** vs. an `origin/main`
  baseline. The fixture proves rendering with no model dependency.

## Files

| File | Change |
|------|--------|
| `scripts/tag_impacts.py` | prompt directive, `build_tool` `note` prop, `SCHEMA_VERSION=2`, `_ensure_entry` note init, store note in `tag_pending` |
| `scripts/validate_impact_tags.py` | add pure `clean_note` |
| `site/features/gdelt-radar/gdelt-page.js` | "Why it matters" expander: markup, expanded-state Set, handlers |
| `site/features/gdelt-radar/gdelt-page.css` | additive `.gdelt-why*` rules |
| `tests/test_impact_tagger.py` | note validator + state-machine + tool-schema tests |
| `tests/test_gdelt_impact_chips.py` | expander markup + CSS assertions |

One small PR. Push + open PR, then STOP before merge (per-change approval required).

## Risks

- **Model ignores the grounding directive and cites an untagged asset.** Mitigation: the
  note is displayed as prose, not parsed into signals — it can never create a chip or a
  board signal. Worst case is an imperfect sentence, and the prompt + empty-note rule keep
  it tight.
- **Ledger size growth.** ~150 chars × items over 7 days ≪ the 400 KB budget; the 280-cap
  bounds the tail. Verified in the plan.
- **Expanded state lost on data refresh.** Bounded to the ~6-hourly cron cadence and only
  for cards left open across a refresh; the Set restores it on the same-session renders in
  between.
