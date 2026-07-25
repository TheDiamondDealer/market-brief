# Per-Headline AI "Why It Matters" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface a short, sourced AI "why it matters" read on each GDELT discovery-radar card — a per-headline synthesis note plus the previously-hidden per-asset mechanisms — via a tap-to-expand row, without disturbing the chips' dossier links or overclaiming.

**Architecture:** Extend the existing Haiku forced-tool tagger to emit one extra `note` string per item in the *same* API call; store it on the 7-day ledger (`site/data/impact-tags.json`, schema v2). On the client, [`gdelt-page.js`](../../../site/features/gdelt-radar/gdelt-page.js) renders one "Why it matters" `<button>`/panel per tagged card, reading the ledger `note` + `tags`. No new dependencies, no new data files, no router changes.

**Tech Stack:** Python 3.12 stdlib (raw `urllib`); vanilla-JS classic-script IIFE setting `window.*`; CSS custom-property tokens; **unittest** (not pytest); Playwright (session scratchpad) for browser smoke.

## Global Constraints

- **Tests are `unittest`, never pytest.** Run one method: `python -m unittest tests.test_impact_tagger.ClassName.test_name -v`. Run one file: `python -m unittest tests.test_impact_tagger -v`. Full suite: `python -m unittest discover -s tests`. Run all commands from the repo root (the worktree root).
- **Scripts are stdlib-only.** [`validate_impact_tags.py`](../../../scripts/validate_impact_tags.py) stays pure (no I/O, no network). [`tag_impacts.py`](../../../scripts/tag_impacts.py) uses raw `urllib` only.
- **Preserve the tagger's fail-open contract:** a whole-chunk outage burns no attempts; `validate_item_output` (tags) is unchanged; retry-cap / prune / batching behaviour is untouched.
- **`note` is OPTIONAL** in the forced-tool schema (never added to `required`); `clean_note` defaults every absent/blank/non-string value to `""`; hard cap **280 chars**.
- **`note` is grounded** to the assets the model tagged (prompt directive); empty tags ⇒ empty note. The note is rendered as prose only — it never becomes a chip or a board signal.
- **Rendering is additive.** Chips keep their `#asset/<id>` links, `tier: 'ai'`, and the `gdelt-ai-chips` wrapper. The existing degraded strings (`AI tagging unavailable`, `AI tagging pending`) and CSS rules (`.gdelt-tags span`, `.gdelt-ai-chips`, `.gdelt-ai-note`) must remain — contract tests assert them.
- **Honesty:** the provenance line ends `· unverified`; the string `real-time` must not appear. No "live" claims.
- **Accessibility:** a real `<button>` with `aria-expanded` + `aria-controls`; visible `:focus-visible`; caret transition gated behind `prefers-reduced-motion`.
- **Board ids:** US dollar = `dxy` (label "US dollar"); AUD = `aud`.
- Only confirmed design tokens are in play: `--bg-panel`, `--bg-elevated`, `--border-subtle`, `--text-primary`, `--text-muted`, `--accent`, `--positive`, `--negative`, `--warning`. Do not invent token names.

## File Structure

| File | Responsibility |
|------|----------------|
| `scripts/validate_impact_tags.py` | + pure `clean_note(raw_obj) -> str` |
| `scripts/tag_impacts.py` | prompt directive, `build_tool` `note` prop, `SCHEMA_VERSION=2`, `_ensure_entry` note init, store note in `tag_pending` |
| `site/features/gdelt-radar/gdelt-page.js` | "Why it matters" expander: markup builder, module `expandedNotes` Set, click handlers |
| `site/features/gdelt-radar/gdelt-page.css` | additive `.gdelt-why*` rules |
| `tests/test_impact_tagger.py` | `clean_note` + note-storage + tool-schema + schema-version tests |
| `tests/test_gdelt_impact_chips.py` | expander markup + accessibility + CSS assertions |

---

### Task 1: `clean_note` validator

**Files:**
- Modify: `scripts/validate_impact_tags.py`
- Test: `tests/test_impact_tagger.py` (add to `class ValidatorTests`)

**Interfaces:**
- Consumes: nothing (pure).
- Produces: `clean_note(raw_obj: Any) -> str` — reads `note` from one model result object; returns `""` for non-dict / missing / `None` / non-string; otherwise `str.strip()` hard-capped at 280 chars.

- [ ] **Step 1: Write the failing tests**

Add these methods inside `class ValidatorTests` in `tests/test_impact_tagger.py`:

```python
    def test_clean_note_extracts_and_strips(self) -> None:
        self.assertEqual(validator.clean_note({"itemId": "x", "note": "  Hello world.  "}), "Hello world.")

    def test_clean_note_empty_when_missing_or_blank_or_none(self) -> None:
        self.assertEqual(validator.clean_note({"itemId": "x"}), "")
        self.assertEqual(validator.clean_note({"itemId": "x", "note": "   "}), "")
        self.assertEqual(validator.clean_note({"itemId": "x", "note": None}), "")

    def test_clean_note_empty_when_not_dict_or_not_string(self) -> None:
        self.assertEqual(validator.clean_note("nope"), "")
        self.assertEqual(validator.clean_note({"itemId": "x", "note": 123}), "")

    def test_clean_note_hard_caps_at_280_chars(self) -> None:
        out = validator.clean_note({"itemId": "x", "note": "y" * 400})
        self.assertEqual(out, "y" * 280)
        self.assertEqual(len(out), 280)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_impact_tagger.ValidatorTests -v`
Expected: FAIL — `AttributeError: module 'validate_impact_tags' has no attribute 'clean_note'`.

- [ ] **Step 3: Implement `clean_note`**

Append to `scripts/validate_impact_tags.py` (after `validate_item_output`):

```python
NOTE_MAX_CHARS = 280


def clean_note(raw_obj: Any) -> str:
    """Extract and sanitise the per-headline ``note`` from one model result object.

    Absent, blank, non-string, or non-dict input all collapse to ``""`` so the
    tagger can store a note unconditionally. Hard-capped at ``NOTE_MAX_CHARS`` to
    bound the ledger size budget.
    """
    if not isinstance(raw_obj, dict):
        return ""
    note = raw_obj.get("note")
    if not isinstance(note, str):
        return ""
    return note.strip()[:NOTE_MAX_CHARS]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_impact_tagger.ValidatorTests -v`
Expected: PASS (existing validator tests + 4 new).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_impact_tags.py tests/test_impact_tagger.py
git commit -m "feat(impact-tags): add clean_note validator for per-headline notes"
```

---

### Task 2: Tagger emits + stores the note (schema v2)

**Files:**
- Modify: `scripts/tag_impacts.py`
- Test: `tests/test_impact_tagger.py` (add to `class TaggerTests` and `class TaggerToolContractTests`)

**Interfaces:**
- Consumes: `validate_impact_tags.clean_note` (Task 1).
- Produces: every ledger item carries a `note` string; `build_tool` result schema has an **optional** `note` property; `SCHEMA_VERSION == 2`.

- [ ] **Step 1: Write the failing tests**

Add to `class TaggerTests`:

```python
    def test_tagged_item_stores_the_note(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": [_good_tag("gold")], "note": "  Sanctions lift crude.  "}]
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagged")
        self.assertEqual(entry["note"], "Sanctions lift crude.")

    def test_tagged_item_without_note_stores_empty_string(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": []}]  # empty tags, no note key
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagged")
        self.assertEqual(entry["note"], "")

    def test_new_entry_initialises_note_key(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": "nope"}]  # malformed -> tagFailed
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        self.assertEqual(ledger["items"][0]["note"], "")
```

Add to `class TaggerToolContractTests`:

```python
    def test_build_tool_includes_optional_note(self) -> None:
        tool = tagger.build_tool({"gold", "wti"})
        result_items = tool["input_schema"]["properties"]["results"]["items"]
        self.assertIn("note", result_items["properties"])
        self.assertEqual(result_items["properties"]["note"]["type"], "string")
        # optional: an omitted note must never be a schema violation
        self.assertNotIn("note", result_items["required"])

    def test_schema_version_is_two(self) -> None:
        self.assertEqual(tagger.SCHEMA_VERSION, 2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_impact_tagger.TaggerTests tests.test_impact_tagger.TaggerToolContractTests -v`
Expected: FAIL — `KeyError: 'note'` (storage tests) and the schema/version assertions fail.

- [ ] **Step 3: Implement the tagger changes** in `scripts/tag_impacts.py`

(a) Bump the constant:

```python
SCHEMA_VERSION = 2
```

(b) Extend the import:

```python
from validate_impact_tags import CONFIDENCES, DIRECTIONS, clean_note, valid_asset_ids, validate_item_output
```

(c) Append the note directive to `SYSTEM_INSTRUCTION` (keep the existing text, add the final two sentences):

```python
SYSTEM_INSTRUCTION = (
    "You tag financial-news headlines for their directional impact on a CLOSED list "
    "of assets. Use ONLY the asset ids allowed by the tool schema — never invent one. "
    "For every supplied itemId return exactly one result object; an empty tags array "
    "is a valid, expected answer when the headline has no clear asset impact. "
    "Also return a `note`: one or two plain-English sentences on how the headline "
    "transmits to the assets you tagged — the net 'why it matters'. Ground the note "
    "ONLY in the assets you tagged; never mention an asset you did not tag. If you "
    "return no tags, return an empty note."
)
```

(d) In `build_tool`, add a `note` property to each result object, alongside `itemId` and `tags` (leave `"required": ["itemId", "tags"]` unchanged):

```python
                    "items": {
                        "type": "object",
                        "properties": {
                            "itemId": {"type": "string"},
                            "note": {
                                "type": "string",
                                "description": "One or two plain sentences on why this headline matters for the assets you tagged; empty string when there are no tags.",
                            },
                            "tags": {
```

(e) In `_ensure_entry`, initialise the note key (add the line just before `"tags": [],`):

```python
        "taggedAtUtc": None,
        "note": "",
        "tags": [],
```

(f) In `tag_pending`, store the note on the tagged branch (add the one `entry["note"]` line):

```python
            else:
                entry["tagState"] = "tagged"
                entry["tags"] = result
                entry["note"] = clean_note(raw)
                entry["taggedAtUtc"] = _iso(now)
                tagged_n += 1
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_impact_tagger -v`
Expected: PASS (all existing tagger tests + 5 new).

- [ ] **Step 5: Commit**

```bash
git add scripts/tag_impacts.py tests/test_impact_tagger.py
git commit -m "feat(impact-tags): tagger emits + stores per-headline note (schema v2)"
```

---

### Task 3: GDELT "Why it matters" expander (render + CSS)

**Files:**
- Modify: `site/features/gdelt-radar/gdelt-page.js`
- Modify: `site/features/gdelt-radar/gdelt-page.css`
- Test: `tests/test_gdelt_impact_chips.py` (add to `class GdeltImpactChipsTests`)

**Interfaces:**
- Consumes: ledger items' `note`, `tags`, and the ledger's top-level `model` (already loaded into `impactTags`). `window.marketAssetBoard.assets` for labels; `core.impactChips` presence as the render guard (mirrors `aiChipsMarkup`).
- Produces: per-card DOM — `<button class="gdelt-why" data-gdelt-why aria-expanded aria-controls>` + `<div class="gdelt-why-panel" hidden?>` containing `.gdelt-why-note?`, `.gdelt-why-mechs`, `.gdelt-why-prov`.

- [ ] **Step 1: Write the failing contract tests**

Add to `class GdeltImpactChipsTests` in `tests/test_gdelt_impact_chips.py`:

```python
    def test_why_it_matters_expander_present(self) -> None:
        self.assertIn("gdelt-why", self.page)
        self.assertIn("data-gdelt-why", self.page)
        self.assertIn("gdelt-why-panel", self.page)
        self.assertIn("Why it matters", self.page)

    def test_expander_is_accessible_and_honest(self) -> None:
        self.assertIn("aria-expanded", self.page)
        self.assertIn("aria-controls", self.page)
        self.assertIn("· unverified", self.page)  # honesty framing preserved
        self.assertNotIn("real-time", self.page)        # never overclaim liveness

    def test_expander_reads_note_and_tracks_expanded_state(self) -> None:
        self.assertIn("expandedNotes", self.page)        # module-level open-state set
        self.assertIn("whyItMattersMarkup", self.page)   # dedicated builder
        self.assertIn("gdelt-why-prov", self.page)       # provenance line

    def test_why_panel_css_present(self) -> None:
        self.assertIn(".gdelt-why", self.styles)
        self.assertIn(".gdelt-why-panel", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_gdelt_impact_chips -v`
Expected: FAIL — the four new assertions (`gdelt-why*`, `expandedNotes`, CSS) are absent.

- [ ] **Step 3: Implement the expander in `site/features/gdelt-radar/gdelt-page.js`**

(a) Add module state + a direction map next to the existing `let impactTags = ...` declarations near the top of the IIFE:

```js
  const expandedNotes = new Set();
  const DIR_ARROW = { up: '↑', down: '↓', mixed: '↔' };
```

(b) Add two functions immediately after `aiChipsMarkup`:

```js
  function whyAssetLabel(assetId) {
    const asset = (window.marketAssetBoard?.assets || []).find((entry) => entry.id === assetId);
    return asset ? asset.label : String(assetId || 'Unknown asset');
  }

  function whyItMattersMarkup(item) {
    const entry = impactTagsById().get(item.id);
    if (!entry || entry.tagState !== 'tagged') return '';
    if (!core.impactChips || !window.marketAssetBoard?.assets) return '';
    const tags = Array.isArray(entry.tags) ? entry.tags : [];
    const note = typeof entry.note === 'string' ? entry.note.trim() : '';
    // Shown only when there is something to say: a synthesis note or >=1 mechanism.
    if (!note && !tags.length) return '';

    const id = String(item.id);
    const panelId = `gdelt-why-${id}`;
    const open = expandedNotes.has(id);
    const model = (impactTags && typeof impactTags.model === 'string' && impactTags.model) || 'AI';
    const domain = item.domain || 'source';

    const noteHtml = note ? `<p class="gdelt-why-note">${escapeHtml(note)}</p>` : '';
    const mechs = tags.map((tag) => {
      const dir = ['up', 'down', 'mixed'].includes(tag.direction) ? tag.direction : 'mixed';
      return `<li><span class="gdelt-why-asset ${dir}">${escapeHtml(whyAssetLabel(tag.assetId))} ${DIR_ARROW[dir]}</span> — ${escapeHtml(tag.mechanism || 'Mechanism not specified.')}</li>`;
    }).join('');
    const mechsHtml = mechs ? `<ul class="gdelt-why-mechs">${mechs}</ul>` : '';
    const prov = `<p class="gdelt-why-prov">AI reading · ${escapeHtml(model)} · ${escapeHtml(domain)} · unverified</p>`;

    return `<button type="button" class="gdelt-why" data-gdelt-why="${escapeHtml(id)}" aria-expanded="${open}" aria-controls="${escapeHtml(panelId)}"><span class="gdelt-why-caret" aria-hidden="true">▸</span> Why it matters</button>
      <div class="gdelt-why-panel" id="${escapeHtml(panelId)}"${open ? '' : ' hidden'}>${noteHtml}${mechsHtml}${prov}</div>`;
  }
```

(c) In `cards()`, render the expander right after the chips. Change the line:

```js
      ${aiChipsMarkup(item)}
```

to:

```js
      ${aiChipsMarkup(item)}
      ${whyItMattersMarkup(item)}
```

(d) In `render()`, wire the toggle handlers. Immediately after the existing
`mount.querySelectorAll('[data-gdelt-topic]')...` block, add:

```js
    mount.querySelectorAll('[data-gdelt-why]').forEach((button) => button.addEventListener('click', () => {
      const id = button.dataset.gdeltWhy;
      const panel = document.getElementById(`gdelt-why-${id}`);
      const open = !expandedNotes.has(id);
      if (open) { expandedNotes.add(id); } else { expandedNotes.delete(id); }
      if (panel) { panel.toggleAttribute('hidden', !open); }
      button.setAttribute('aria-expanded', String(open));
    }));
```

- [ ] **Step 4: Implement the CSS in `site/features/gdelt-radar/gdelt-page.css`**

Append (additive — do not edit existing rules):

```css
.gdelt-why { display: inline-flex; align-items: center; gap: 7px; margin-top: 10px; padding: 6px 11px 6px 9px; border: 1px solid var(--border-subtle); border-radius: 9px; background: var(--bg-panel); color: var(--text-primary); font: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
.gdelt-why:hover { border-color: var(--accent); }
.gdelt-why:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.gdelt-why-caret { color: var(--accent); font-size: 10px; display: inline-block; }
.gdelt-why[aria-expanded="true"] .gdelt-why-caret { transform: rotate(90deg); }
.gdelt-why-panel { margin-top: 9px; border: 1px solid var(--border-subtle); border-left: 2px solid var(--accent); border-radius: 10px; background: var(--bg-panel); padding: 12px 13px; }
.gdelt-why-panel[hidden] { display: none; }
.gdelt-why-note { margin: 0 0 10px; font-size: 13px; line-height: 1.5; color: var(--text-primary); }
.gdelt-why-mechs { list-style: none; margin: 0 0 10px; padding: 0; display: grid; gap: 6px; }
.gdelt-why-mechs li { font-size: 12px; line-height: 1.45; color: var(--text-muted); }
.gdelt-why-asset { font-weight: 600; }
.gdelt-why-asset.up { color: var(--positive); }
.gdelt-why-asset.down { color: var(--negative); }
.gdelt-why-asset.mixed { color: var(--warning); }
.gdelt-why-prov { margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; color: var(--text-muted); letter-spacing: .03em; border-top: 1px dashed var(--border-subtle); padding-top: 9px; }
@media (prefers-reduced-motion: no-preference) { .gdelt-why-caret { transition: transform 160ms ease; } }
```

- [ ] **Step 5: Run the contract tests + JS syntax check**

Run: `python -m unittest tests.test_gdelt_impact_chips -v`
Expected: PASS — including the pre-existing `test_nested_javascript_is_syntax_valid` (`node --check`) and `test_additive_css_does_not_disturb_existing_gdelt_tags_rule`.

- [ ] **Step 6: Run the full suite**

Run: `python -m unittest discover -s tests`
Expected: only the known pre-existing flake `test_source_health.test_runtime_registry_keeps_source_failures_independent` fails; everything else passes.

- [ ] **Step 7: Commit**

```bash
git add site/features/gdelt-radar/gdelt-page.js site/features/gdelt-radar/gdelt-page.css tests/test_gdelt_impact_chips.py
git commit -m "feat(gdelt-radar): tap-to-expand 'Why it matters' AI note on radar cards"
```

---

## Whole-branch verification (controller)

Committed tests are contract + syntax level; real interaction is proven with a browser
smoke over a **fixture ledger** (proves note rendering without any API key). Run from the
worktree root after Task 3.

- [ ] **Playwright smoke.** Assemble a temp served copy of `site/` whose
  `data/impact-tags.json` is a v2 fixture: one item whose `id`, `domain`, and `seenAt` are
  copied from the first article in `site/data/gdelt-radar.json`, `tagState: "tagged"`, a
  real `note`, and two tags (`dxy` up, `gold` down). Serve it on `127.0.0.1` and drive it:

```js
// scratchpad smoke — asserts note renders, chips still navigate, aria toggles, no new errors
const { chromium } = require('playwright');
const BASE = process.env.SMOKE_BASE || 'http://127.0.0.1:8137';
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message.split('\n')[0].slice(0, 140)));
  await page.goto(`${BASE}/#news`, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(4500);
  // open the GDELT radar <details> if collapsed, then expand the first card's note
  await page.evaluate(() => document.querySelector('#gdeltRadarMount details')?.setAttribute('open', ''));
  await page.waitForTimeout(300);
  const btn = await page.$('#gdeltRadarMount [data-gdelt-why]');
  const chipHref = await page.$eval('#gdeltRadarMount .gdelt-ai-chips a.impact-chip', (a) => a.getAttribute('href')).catch(() => null);
  await btn.click();
  await page.waitForTimeout(300);
  const state = await page.evaluate(() => {
    const b = document.querySelector('#gdeltRadarMount [data-gdelt-why]');
    const panel = document.getElementById(b.getAttribute('aria-controls'));
    return {
      expanded: b.getAttribute('aria-expanded'),
      panelVisible: panel && !panel.hasAttribute('hidden'),
      noteText: (panel?.querySelector('.gdelt-why-note')?.textContent || '').slice(0, 80),
      prov: (panel?.querySelector('.gdelt-why-prov')?.textContent || ''),
    };
  });
  console.log('CHIP HREF:', chipHref, '| STATE:', JSON.stringify(state), '| ERRORS:', errors.length);
  errors.slice(0, 6).forEach((e) => console.log('  *', e));
  await browser.close();
})().catch((e) => { console.error('FATAL', e); process.exit(1); });
```

  Pass criteria: `expanded === "true"`, `panelVisible === true`, a non-empty `noteText`, a
  `prov` ending `· unverified`, `CHIP HREF` starting `#asset/` (dossier nav intact), and
  **no new** `pageerror`s versus an `origin/main` baseline run of the same navigation (the
  3 known pre-existing `kind/kind/map` errors are baseline, not regressions).

- [ ] **Ledger size guard.** Confirm `site/data/impact-tags.json` stays well under the
  400 KB budget enforced by `scripts/audit_static_site.py` (the committed ledger is
  untouched by this PR; the note field lands via the cron post-merge).

- [ ] **Finish:** superpowers:finishing-a-development-branch → push + open PR against
  `main`, then **STOP** (per-change approval required before merge).

## Self-Review

- **Spec coverage:** note field (T1+T2), grounded prompt (T2), schema v2 (T2), expander +
  when-shown gate + a11y + honesty (T3), no-backfill transition (verification note), tests
  without a key (all tasks + smoke). All spec sections map to a task.
- **Placeholder scan:** none — every step carries real code and an exact command.
- **Type/name consistency:** `clean_note` (T1) is imported and called in T2; `note` key,
  `expandedNotes`, `whyItMattersMarkup`, `gdelt-why*` names match across T3 impl and tests;
  `SCHEMA_VERSION` bumped once (T2) and asserted once (T2).
