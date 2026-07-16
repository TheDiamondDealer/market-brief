# Market Brief UI Revamp (mrktedge-style) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Market Brief console to mrktedge.ai-level visual polish: fix four visual bugs, retire the legacy teal theme so the whole app renders in the violet/near-black token system, and upgrade the key views (Command Centre, COT, Rates, Impact Feed, Crowd Expectations) to a data-first, low-chrome design language — without touching any data rule, route contract, or generated file.

**Architecture:** The site is a static, bundler-free GitHub Pages app (`site/`). A design-token system ([site/styles/tokens.css](../../site/styles/tokens.css)) with violet accent `#a970ff` already exists and roughly half the views ("features/" modules) use it; the other half still read a legacy teal `:root` in [site/styles.css](../../site/styles.css) that loads later and overrides the token aliases. This plan finishes that migration and then restyles components in place. No framework, no build step, no new runtime dependency.

**Tech Stack:** Vanilla JS (browser globals, script-order-dependent), plain CSS, SVG for charts, Python unittest contract suite, GitHub Actions validate + Pages deploy.

## Global Constraints

Every task implicitly includes all of these. Read `AGENTS.md` at repo root before starting — it is binding.

- **Branch safety:** ALL work happens on branch `feat/ui-mrktedge-revamp` cut from `main`. NEVER commit to `main` and NEVER merge: any `site/**` change on `main` auto-deploys to the public GitHub Pages site via `.github/workflows/deploy-pages.yml`. Finish = push branch + open PR + STOP for Chris's review.
- **Never hide honest failure states.** Cards showing "Unavailable", "Partial", "stale-retained", retained-records warnings, or empty-state explanations must stay visible after every restyle. This is a non-negotiable AGENTS.md rule.
- **Never edit generated files:** `site/free-data.js`, `site/political-data.js`, `site/equity-data.js`, anything under `site/data/`. Renderers only.
- **Keep route contracts:** `#home #news #events #cot #trackers #rates #scenarios #products` etc.; view sections `id="view-*"` and nav `data-view` attributes must not be renamed.
- **Contract tests are the regression net.** Run `python -m unittest discover -s tests -v` after every task. Some tests assert on *source text* of JS/CSS files (exact strings listed per task below). If a test fails because the plan intentionally changed markup, adapt the implementation to keep the contract (preferred) — only change a test when the task explicitly says so.
- **Accessibility invariants:** keep `aria-label`s on icon-only buttons, `role="img"` + `<title>`/`<desc>` on chart SVGs, `tabindex="0"`/`role="button"` on interactive chart rows, focus-visible outlines from `styles/hardening.css`, 44px minimum touch targets.
- **File budgets** (enforced by `scripts/audit_static_site.py`): `index.html` ≤ 250 KB, each `features/**` file ≤ 140 KB.
- **Color semantics (design system):** violet `var(--accent)` = interactive/brand only; green `var(--positive)` = long/up/current; red `var(--negative)` = short/down/stale; amber `var(--warning)` = partial/warning. Never use teal.
- **Syntax gate after any JS edit:** `find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check` plus `node --check` on each edited `site/features/**/*.js` file.
- **Visual verification:** every task that changes rendering ends with a screenshot check against the live view (recipe in Task 0). Serve locally with `python -m http.server 8000 --directory site` — never test via `file://`.

## Design Reference (target language, distilled from mrktedge.ai screenshots)

The executor does not have the screenshots; these rules are the spec:

1. **Canvas:** near-black neutral (`--bg-canvas #050607` — already correct). Panels barely lighter, hairline `--border-subtle` borders, radius 10–14 px. Generous black space; never nested bordered boxes more than one level deep.
2. **Numbers first:** big values (22–30 px, `font-variant-numeric: tabular-nums`), each paired with a small pill "delta chip" — arrow + change, tinted green/red at ~12 % background opacity. Labels above values: 10 px, uppercase, letter-spaced, `--text-muted`.
3. **Section headers:** 15–16 px semibold white text + small muted count/date on the right. The violet ALL-CAPS eyebrow ("kicker") is reserved for one per page/panel, not on every card.
4. **News/timeline rows:** muted timestamp line, bold headline, 1–2 line muted interpretation, hairline separators between rows instead of heavy per-card borders.
5. **One display flourish:** the Command Centre regime verdict uses a serif display face (Georgia stack) like a newspaper headline. Nothing else is serif.
6. **Charts:** thin 2 px lines, subtle gradients, horizontal bars with readable left-aligned row labels (never rotated axis text), values at the end of each bar.

---

### Task 0: Branch + baseline screenshots

**Files:**
- Create: `..\market-brief-ui-shots\shoot.js` (OUTSIDE the repo — screenshots must not enter git)

**Interfaces:**
- Produces: `shoot.js` screenshot harness reused by every later task's verify step; baseline PNGs `baseline-<view>.png`.

- [ ] **Step 1: Cut the branch**

```bash
cd "c:/Users/Office/Desktop/Make Backup/market-brief"
git checkout -b feat/ui-mrktedge-revamp
```

- [ ] **Step 2: Start the local server (keep running in background for all tasks)**

Run: `python -m http.server 8000 --directory site`

- [ ] **Step 3: Create the screenshot harness**

Write `..\market-brief-ui-shots\shoot.js` (sibling folder next to the repo):

```js
// Usage: node shoot.js <prefix>   e.g. node shoot.js baseline
const { chromium } = require('C:/Users/Office/Desktop/Make Backup/amj-diamonds/node_modules/playwright');
const path = require('path');
const prefix = process.argv[2] || 'shot';
const VIEWS = ['home', 'news', 'events', 'cot', 'trackers', 'rates', 'assets', 'regime', 'products', 'scenarios'];
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:8000/', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(4000);
  for (const v of VIEWS) {
    try {
      await page.click(`.nav-item[data-view="${v}"]`, { timeout: 5000 });
      await page.evaluate(() => document.activeElement && document.activeElement.blur());
      await page.mouse.move(900, 500);
      await page.waitForTimeout(2200);
      await page.screenshot({ path: path.join(__dirname, `${prefix}-${v}.png`) });
      if (v === 'home') await page.screenshot({ path: path.join(__dirname, `${prefix}-${v}-full.png`), fullPage: true });
      console.log('ok', v);
    } catch (e) { console.log('fail', v, e.message); }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(__dirname, `${prefix}-mobile.png`) });
  await browser.close();
})();
```

(The playwright dependency is borrowed from the adjacent `amj-diamonds` project on this machine; do not add playwright to this repo.)

- [ ] **Step 4: Capture the baseline**

Run: `node "..\market-brief-ui-shots\shoot.js" baseline` (from repo root)
Expected: `ok <view>` for all 10 views; PNGs in `..\market-brief-ui-shots\`.

- [ ] **Step 5: Verify the test suite is green before touching anything**

Run: `python -m unittest discover -s tests -v`
Expected: OK (all pass). If anything fails on a clean checkout, STOP and report before proceeding.

---

### Task 1: Retire the legacy teal theme in `styles.css`

The single highest-impact change. [site/styles/tokens.css](../../site/styles/tokens.css) already defines every legacy alias (`--bg --panel --panel2 --line --text --muted --teal --teal2 --amber --red --green --blue --shadow --radius`) pointing at the violet/neutral system, but `styles.css` loads after it and stomps them with teal literals.

**Files:**
- Modify: `site/styles.css:1-6` (delete the `:root` block), `site/styles.css:8` (body gradient), plus every remaining literal teal occurrence in that file.

**Interfaces:**
- Produces: all legacy-styled views (Assets, Regime, Research Library, Scenario Lab, Week Ahead, Trigger Zones, Archive, news sidebar) inherit the token palette. Later tasks assume no teal remains anywhere.

- [ ] **Step 1: Delete the legacy `:root` block**

Remove exactly these lines from the top of `site/styles.css`:

```css
:root {
      --bg:#071014; --panel:#0d181e; --panel2:#111f26; --line:#21343d;
      --text:#e9f0f2; --muted:#94a7af; --teal:#2dd4bf; --teal2:#14b8a6;
      --amber:#f5b942; --red:#ff6b6b; --green:#63d392; --blue:#6cb6ff;
      --shadow:0 20px 60px rgba(0,0,0,.28); --radius:18px;
    }
```

(tokens.css's compatibility aliases take over; card radius drops 18→14 px which is intended.)

- [ ] **Step 2: Neutralise the teal body gradient**

In the `body{...}` rule on the following line, replace

```css
background:radial-gradient(circle at 20% -10%,#12333a 0,transparent 36%),var(--bg);
```

with

```css
background:radial-gradient(circle at 20% -10%,rgba(169,112,255,.06) 0,transparent 36%),var(--bg);
```

- [ ] **Step 3: Sweep remaining teal literals in styles.css**

Run: `grep -nE "2dd4bf|14b8a6|0f766e|12333a|rgba\(45,212,191|rgba\(20,184,166" site/styles.css`
For each hit, replace with the violet equivalent:
- `rgba(45,212,191,.22)` → `rgba(169,112,255,.22)`
- `rgba(20,184,166,.12)` → `rgba(169,112,255,.14)`
- any bare `#2dd4bf`/`#14b8a6` → `var(--accent)` / `var(--accent-strong)`
- `#0f766e` (gradient stop in the legacy `.mark`) → `#5b2ca1`

Expected after sweep: the grep returns nothing.

- [ ] **Step 4: Tame the oversized legacy page titles**

The legacy views (Assets, Regime, Research Library, Scenario Lab…) open with 32–55 px display titles that duplicate the topbar's page title. In `site/styles.css`:

- In the rule `.hero h2{font-size:clamp(28px,4vw,48px);letter-spacing:-.045em;...}` (~line 18) change the size to `font-size:22px;letter-spacing:-.02em`.
- In the `*-hero h2` rule (~line 42, `font-size:clamp(32px,5vw,55px)`) change to `font-size:24px;letter-spacing:-.02em`.

(The teal gradient on that same `*-hero` rule — `rgba(20,184,166,.12)` — is already replaced by Step 3's sweep.)

- [ ] **Step 5: Visual + contract verification**

Run: `python -m unittest discover -s tests -v` → OK.
Run: `node "..\market-brief-ui-shots\shoot.js" task1`
Compare `task1-assets/regime/products/scenarios.png` against baseline: pages must now be violet-accented on neutral dark panels, with no green-tinted panel backgrounds, page titles at sane sizes, and every text still readable (spot-check filter pills, badges, table text). The already-remodeled views (home, news, cot, rates, trackers, events) must look unchanged.

- [ ] **Step 6: Commit**

```bash
git add site/styles.css
git commit -m "style: retire legacy teal :root so token aliases drive all views"
```

---

### Task 2: COT chart colors → semantic tokens

**Files:**
- Modify: `site/cot-chart.css` (literals `#2dd4bf` long / `#ff6b6b` short), `site/cot-chart.js:111` (gradient stops), `site/features/cot/cot-page.js` (gradient defs `#27e58b/#087b4b/#ff6672/#8e2932` — these get fully replaced again in Task 9; here just make colors consistent in case Task 9 is deferred).

**Interfaces:**
- Produces: long = `#20c979` (`--positive`), short = `#f45b69` (`--negative`) everywhere in COT visuals.

- [ ] **Step 1: Replace literals in cot-chart.css**

In `site/cot-chart.css` replace every `#2dd4bf` with `var(--positive)` and every `#ff6b6b` with `var(--negative)` (occurrences: `.cot-chart-legend .long i`, `.cot-chart-legend .short i`, `.cot-long-line`, `.cot-short-line`, `.cot-latest-dot.long`, `.cot-latest-dot.short`, `.cot-balance-bar .long`, `.cot-balance-bar .short`). Also replace `border-color:var(--teal2);background:rgba(20,184,166,.12)` in `.cot-chart-tabs button.active` with `border-color:var(--accent-strong);background:rgba(169,112,255,.14)`.

- [ ] **Step 2: Replace SVG gradient stops (attributes cannot use CSS vars)**

In `site/cot-chart.js` (~line 111) change both `stop-color="#2dd4bf"` to `stop-color="#20c979"`. In the adjacent short gradient change `#ff6b6b` stops to `#f45b69`.
In `site/features/cot/cot-page.js` `chartBalance` defs: `#27e58b`→`#20c979`, `#087b4b`→`#0e7a49`, `#ff6672`→`#f45b69`, `#8e2932`→`#8a3038`.

- [ ] **Step 3: Verify**

Run: `node --check site/cot-chart.js && node --check site/features/cot/cot-page.js` → no output.
Run: `python -m unittest tests.test_cot_interface tests.test_cot_contracts -v` → OK.
Screenshot: `node "..\market-brief-ui-shots\shoot.js" task2`, check `task2-cot.png`: bar/line greens and reds match the rest of the app (same green as "CURRENT" badges).

- [ ] **Step 4: Commit**

```bash
git add site/cot-chart.css site/cot-chart.js site/features/cot/cot-page.js
git commit -m "style: COT chart colors use semantic token palette"
```

---

### Task 3: Fix the GDELT Discovery Radar light-theme card

`site/features/gdelt-radar/gdelt-page.css` was authored against a token vocabulary this app never defines (`--surface`, `--border`, `--surface-raised`, `--surface-muted`), so its fallbacks render a white card with pale text inside the dark Impact Feed.

**Files:**
- Modify: `site/features/gdelt-radar/gdelt-page.css` (whole file, 33 lines)

**Interfaces:**
- Produces: dark-theme GDELT panel; class names unchanged (`gdelt-page.js` markup untouched).

- [ ] **Step 1: Remap every token/fallback to this app's dark tokens**

Apply these substitutions across the whole file (every occurrence):

| Old | New |
|---|---|
| `var(--surface, #fff)` | `var(--bg-panel)` |
| `var(--surface-raised, #fff)` | `var(--bg-elevated)` |
| `var(--surface-muted, #f1f4f8)` | `var(--bg-elevated)` |
| `var(--border, #d8dee8)` | `var(--border-subtle)` |
| `var(--muted, #667085)` | `var(--text-muted)` |
| `var(--text, #172033)` | `var(--text-primary)` |
| `var(--accent, #136c7a)` | `var(--accent)` |
| `#a33a2b` (`.gdelt-error` color) | `var(--negative)` |
| `#f59e0b` (warning color-mix) | `var(--warning)` |

Additionally, in `.gdelt-toolbar button[aria-pressed="true"]` change `color: #fff` to `color: #09040f` (dark text on the violet accent, matching the brand mark).

- [ ] **Step 2: Verify**

Run: `python -m unittest tests.test_gdelt_radar -v` → OK.
Screenshot: `node "..\market-brief-ui-shots\shoot.js" task3`, check `task3-news.png`: the "GDELT Discovery Radar" panel is now a dark card; the "PARTIAL" badge, "48 leads" and description are all legible; expand-state (`<details>`) still toggles.

- [ ] **Step 3: Commit**

```bash
git add site/features/gdelt-radar/gdelt-page.css
git commit -m "fix: GDELT radar panel renders dark theme instead of white fallback"
```

---

### Task 4: Stop the nav rail sticking open after click

`.sidebar:focus-within` in [site/styles/shell.css](../../site/styles/shell.css) keeps the 252 px rail expanded over ~200 px of content after every mouse click on a nav item (the button retains focus). Scope the expansion to keyboard focus only.

**Files:**
- Modify: `site/styles/shell.css` (all `:focus-within` occurrences on `.sidebar` selectors — lines ~23-28, ~63-80, and the tooltip guards at ~156-179)

**Interfaces:**
- Produces: rail expands on hover and on keyboard (`:focus-visible`) focus; collapses immediately after a mouse click navigates.

- [ ] **Step 1: Replace the pseudo-class**

Run: `grep -n ":focus-within" site/styles/shell.css` (expect ~9 hits).
Replace every `.sidebar:focus-within` with `.sidebar:has(:focus-visible)` and every `.sidebar:not(:hover):not(:focus-within)` with `.sidebar:not(:hover):not(:has(:focus-visible))`. No other selector part changes.

- [ ] **Step 2: Verify interactively**

With the local server running, in a real browser (or via a quick playwright eval): click "COT Positioning" in the rail, move the mouse into the page body — the rail must collapse to 54 px (content fully visible). Then Tab into the rail from the page — it must expand while keyboard focus is inside. Check `python -m unittest tests.test_shell_contract -v` → OK.

- [ ] **Step 3: Commit**

```bash
git add site/styles/shell.css
git commit -m "fix: nav rail no longer sticks expanded after mouse click (focus-visible scoping)"
```

---

### Task 5: Rates/Macro cards — honest delta chip + de-chromed meta rows

The two-point "sparkline" (a line between exactly two dots — FRED cache only stores `value` + `previous`) reads as a broken chart, and each card nests four bordered boxes. Replace with the mrktedge stat-card pattern.

**Files:**
- Modify: `site/features/macro-monitor/macro-page.js` (replace `sparkline()`, edit `seriesCard()`)
- Modify: `site/features/macro-monitor/macro-page.css` (replace `dl` box styles + `.macro-spark` rules, add `.macro-delta` + `.macro-meta`)

**Interfaces:**
- Consumes: `row = {id,name,unit,kind,date,value,previous,change,changeBps,sourceUrl}` from `official.rates` (unchanged).
- Produces: `deltaChip(row)` returning a pill `<span class="macro-delta up|down|flat">`; `seriesCard(row, status)` markup with `.macro-meta` list. The honesty string `No previous observation` must remain in the source (check `grep -n "spark\|previous observation" tests/test_macro_monitor.py` first and keep any asserted strings).

- [ ] **Step 1: Replace `sparkline()` with `deltaChip()` in macro-page.js**

Delete the whole `function sparkline(row) {...}` and add:

```js
function deltaChip(row) {
  const change = row.change === null || row.change === undefined ? null : Number(row.change);
  if (change === null) return '<span class="macro-delta flat">No previous observation</span>';
  const cls = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';
  const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '·';
  return `<span class="macro-delta ${cls}"><span aria-hidden="true">${arrow}</span> ${escapeHtml(trendLabel(row))}</span>`;
}
```

- [ ] **Step 2: Rewrite `seriesCard()`**

```js
function seriesCard(row, status) {
  return `<article class="macro-series-card">
    <header><div><span>${escapeHtml(row.kind || 'series')}</span><h4>${escapeHtml(row.name)}</h4></div><span class="data-state ${statusClass(status.status)}">${escapeHtml(status.status || 'Unavailable')}</span></header>
    <div class="macro-reading"><strong>${number(row.value, row.unit === 'index' ? 4 : 2)}${row.unit === '%' ? '%' : ''}</strong>${deltaChip(row)}</div>
    <dl class="macro-meta"><div><dt>Observed</dt><dd>${escapeHtml(row.date || 'Unavailable')}</dd></div><div><dt>Previous</dt><dd>${number(row.previous, row.unit === 'index' ? 4 : 2)}${row.unit === '%' ? '%' : ''}</dd></div><div><dt>Cadence</dt><dd>${escapeHtml(cadence(row))}</dd></div><div><dt>Series</dt><dd>${escapeHtml(row.id)}</dd></div></dl>
    <a href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener noreferrer">Official FRED series ↗</a>
  </article>`;
}
```

Note: the old `${sparkline(row)}` call disappears; the `trendLabel` text moves inside the chip so the standalone trend `<span>` in `.macro-reading` is removed.

- [ ] **Step 3: Update macro-page.css**

Remove the `.macro-spark` and `.macro-no-spark` rules and the boxed `.macro-series-card dl div{padding:9px;border:...;background:...}` styling. Add:

```css
.macro-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 14px;margin:0;padding-top:10px;border-top:1px solid var(--border-subtle)}
.macro-meta div{display:flex;justify-content:space-between;gap:10px;padding:3px 0;border:0;background:transparent}
.macro-meta dt{font-size:10px;text-transform:uppercase;color:var(--text-muted)}
.macro-meta dd{margin:0;font-size:12px;font-variant-numeric:tabular-nums}
.macro-delta{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:650}
.macro-delta.up{color:var(--positive);background:rgba(32,201,121,.12)}
.macro-delta.down{color:var(--negative);background:rgba(244,91,105,.12)}
.macro-delta.flat{color:var(--text-muted);background:var(--bg-elevated)}
```

Keep `.macro-reading strong{font-size:26px;font-variant-numeric:tabular-nums}` and change `.macro-reading` to `align-items:center` with the chip right-aligned.

- [ ] **Step 4: Verify**

Run: `node --check site/features/macro-monitor/macro-page.js` → clean.
Run: `python -m unittest tests.test_macro_monitor -v` → OK (if it asserted `macro-spark`, adapt the *implementation* to keep an equivalent honesty string — the "No previous observation" text is preserved in `deltaChip`).
Screenshot `task5-rates.png`: cards show big value + colored delta chip + four plain label/value rows, no empty two-dot chart, no nested boxes.

- [ ] **Step 5: Commit**

```bash
git add site/features/macro-monitor/macro-page.js site/features/macro-monitor/macro-page.css
git commit -m "style: macro series cards use delta chips and borderless meta rows"
```

---

### Task 6: Unify the status-badge component

`.data-state` (defined in `site/free-data.css`, used app-wide) hardcodes pale Tailwind-ish colors and 8 px text. Retint with tokens and make it legible.

**Files:**
- Modify: `site/free-data.css` (the `.data-state` block near the top)

**Interfaces:**
- Produces: one badge look for `current | partial | stale | pending` used by every feature (`grep -rn "data-state" site/features/ | wc -l` shows the consumers; classes don't change).

- [ ] **Step 1: Replace the badge palette**

Replace the existing `.data-state{...}` and its three state rules with:

```css
.data-state{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.06em;border:1px solid var(--border-subtle)}
.data-state.current,.evidence-status.automatic{color:var(--positive);background:rgba(32,201,121,.1);border-color:rgba(32,201,121,.28)}
.data-state.partial,.evidence-status.partial{color:var(--warning);background:rgba(224,184,79,.1);border-color:rgba(224,184,79,.28)}
.data-state.stale,.data-state.pending,.evidence-status.pending{color:var(--negative);background:rgba(244,91,105,.09);border-color:rgba(244,91,105,.25)}
```

- [ ] **Step 2: Verify**

Run: `python -m unittest discover -s tests -v` → OK.
Screenshots `task6-home.png`, `task6-trackers.png`, `task6-events.png`: badges ("CURRENT", "PARTIAL", "2 SOURCE WARNINGS", "REACTION COMPLETE", "SOURCED") are consistent in size/tone across views and readable at a glance.

- [ ] **Step 3: Commit**

```bash
git add site/free-data.css
git commit -m "style: status badges share one token-based palette and legible sizing"
```

---

### Task 7: Real SVG nav icons + favicon

Unicode glyphs (⌂ ⚡ ◷ ⇄ ◎ …) have inconsistent optical weight and read as placeholders. Inline a Lucide SVG sprite. Also add a favicon (currently none).

**Files:**
- Modify: `site/index.html` (sprite after `<body>` opens, favicon `<link>` in `<head>`, all `.nav-icon` spans in the sidebar + mobile bottom nav + rail toggle)
- Modify: `site/styles/shell.css` (`.nav-icon` sizing rule)

**Interfaces:**
- Produces: `<svg class="ico"><use href="#i-<name>"/></svg>` icons; symbol ids `i-home i-zap i-calendar i-arrows i-landmark i-activity i-rss i-users i-week i-compass i-flag i-gem i-library i-trend i-archive i-rail`.

- [ ] **Step 1: Fetch Lucide outline path data**

For each mapping below, fetch `https://unpkg.com/lucide-static@latest/icons/<lucide-name>.svg` and copy the inner path/shape elements (24×24 viewBox, stroke-based):

| symbol id | lucide name | used by |
|---|---|---|
| `i-home` | `house` | Command Centre |
| `i-zap` | `zap` | Impact Feed |
| `i-calendar` | `calendar-clock` | Calendar |
| `i-arrows` | `arrow-right-left` | COT Positioning |
| `i-landmark` | `landmark` | Political Flow |
| `i-activity` | `activity` | Rates & Liquidity |
| `i-rss` | `rss` | Official Feeds |
| `i-users` | `users` | Crowd Expectations |
| `i-week` | `calendar-range` | Week Ahead |
| `i-compass` | `compass` | Regime |
| `i-flag` | `flag` | Trigger Zones |
| `i-gem` | `gem` | Assets |
| `i-library` | `library` | Research Library |
| `i-trend` | `trending-up` | Scenario Lab |
| `i-archive` | `archive` | Archive |
| `i-rail` | `panel-left-open` | rail toggle |

Build one sprite immediately after `<body>`:

```html
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
  <symbol id="i-home" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><!-- paths from lucide house --></symbol>
  <!-- ...one symbol per row of the table... -->
</svg>
```

- [ ] **Step 2: Swap the glyphs**

For each sidebar nav button replace `<span class="nav-icon" aria-hidden="true">⌂</span>` with `<span class="nav-icon" aria-hidden="true"><svg><use href="#i-home"/></svg></span>` (matching icon per row above; the `aria-label`/`title`/`data-tooltip` attributes stay). Do the same for the rail toggle (`⇥` → `i-rail`) and the mobile bottom-nav buttons if they carry glyph spans (check `grep -n "nav-icon" site/index.html site/shell.js`).

- [ ] **Step 3: Size the icons and add the favicon**

In `site/styles/shell.css` extend the `.nav-icon` rule with:

```css
.nav-icon svg{width:17px;height:17px;display:block;margin:0 auto}
```

In `<head>` add:

```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23a970ff'/%3E%3Ctext x='32' y='44' font-family='Georgia,serif' font-size='36' font-weight='700' text-anchor='middle' fill='%2309040f'%3EM%3C/text%3E%3C/svg%3E" />
```

- [ ] **Step 4: Verify**

Run: `python scripts/audit_static_site.py` → passes (index.html stays under 250 KB).
Run: `python -m unittest tests.test_frontend_contract tests.test_shell_contract -v` → OK.
Screenshot `task7-home.png` + mobile: icons render crisp at both rail widths and in the bottom nav; browser tab shows the violet "M" favicon.

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/styles/shell.css
git commit -m "feat: inline Lucide icon sprite for navigation and add favicon"
```

---

### Task 8: Command Centre — data-first hero

Lead with numbers, not prose: add a stat-tile strip from the daily observed moves, give the regime verdict a serif display treatment, and demote the "How to use this console" documentation card to a collapsible placed at the bottom.

**Files:**
- Modify: `site/features/command-centre/command-page.js` (`decisionGuide()`, `dailyBrief()`, `render()`, new `heroStats()`)
- Modify: `site/features/command-centre/command-page.css` (new `.command-stat-*` rules, hero h2 serif)

**Interfaces:**
- Consumes: `research.daily.stats = [{label, value, move, dir}]` (already used by `dailyBrief()`); `directionGlyph/directionLabel` helpers already in the module.
- Produces: `heroStats()` returning `<section class="command-stat-strip">…`; `decisionGuide()` now returns a `<details class="command-decision-guide">`.
- Contract strings that MUST remain in the source: `Expected market pressure` (directionStrip default arg), `expected directional pressure under the current regime`, `market-direction-chip`, `root.dataset.commandCentreRemodel = 'br-14'` (checked by `tests/test_command_centre.py`).

- [ ] **Step 1: Add `heroStats()` after `decisionGuide()`**

```js
function heroStats() {
  const stats = (research.daily?.stats || []).slice(0, 6);
  if (!stats.length) return '';
  return `<section class="command-stat-strip" aria-label="Today's observed market moves">${stats.map((stat) => {
    const dir = directionLabel(stat.dir);
    return `<article class="command-stat ${escapeHtml(dir)}"><span class="command-stat-label">${escapeHtml(stat.label)}</span><strong>${escapeHtml(stat.value || '—')}</strong><span class="command-stat-move"><span aria-hidden="true">${directionGlyph(stat.dir)}</span> ${escapeHtml(stat.move || 'No move recorded')}</span></article>`;
  }).join('')}</section>`;
}
```

- [ ] **Step 2: Convert `decisionGuide()` to a collapsible**

```js
function decisionGuide() {
  return `<details class="command-decision-guide">
    <summary><span class="command-kicker">How to use this console</span><h3 id="commandGuideTitle">From trigger to decision</h3></summary>
    <div class="command-decision-guide-body"><p>Start with the dominant driver, then require confirmation across prices and physical data. Use the asset pressure as a conditional map, and the flip condition as the point where the interpretation must change.</p>
    <ol><li><span>1</span><div><strong>Trigger</strong><small>What changed in policy, conflict, data or physical flows?</small></div></li><li><span>2</span><div><strong>Confirmation</strong><small>Do oil, yields, the dollar, volatility and exposed assets agree?</small></div></li><li><span>3</span><div><strong>Transmission</strong><small>Which assets face upward, downward or mixed pressure under this regime?</small></div></li><li><span>4</span><div><strong>Flip condition</strong><small>What observable evidence would weaken or reverse the view?</small></div></li></ol></div>
  </details>`;
}
```

- [ ] **Step 3: Rearrange `render()` and slim `dailyBrief()`**

In `render()`'s template: insert `${heroStats()}` immediately after the `</header>` of `.command-hero`; move `${decisionGuide()}` from its position after the header down to just before the final `<section class="command-source-panel">`. In `dailyBrief()` delete the line `${stats.length ? directionStrip(stats, 'Today’s observed moves') : ''}` (the hero tiles replace it; the `stats` mapping constant can stay or be removed with it — remove both to avoid dead code, BUT first confirm `Expected market pressure` still appears in the file via the `directionStrip` default parameter).

- [ ] **Step 4: CSS**

Append to `site/features/command-centre/command-page.css`:

```css
.command-stat-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.command-stat{display:grid;gap:6px;padding:14px 16px;border:1px solid var(--border-subtle);border-radius:var(--radius-md);background:var(--bg-panel)}
.command-stat-label{color:var(--text-muted);font-size:10px;letter-spacing:.08em;text-transform:uppercase}
.command-stat strong{font-size:22px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.command-stat-move{font-size:11px;color:var(--text-secondary)}
.command-stat.up .command-stat-move{color:var(--positive)}
.command-stat.down .command-stat-move{color:var(--negative)}
.command-stat.mixed .command-stat-move{color:var(--warning)}
.command-hero h2{font-family:Georgia,'Times New Roman',serif;font-size:30px;letter-spacing:-.005em}
.command-decision-guide summary{display:flex;flex-direction:column;gap:2px;cursor:pointer;list-style:none}
.command-decision-guide summary::-webkit-details-marker{display:none}
.command-decision-guide summary h3{margin:0}
.command-decision-guide-body{margin-top:14px}
```

Check the existing `.command-decision-guide` grid rule — since the element is now a `<details>` containing summary + body, change its `display:grid;grid-template-columns:...` to `display:block` and move the two-column layout onto `.command-decision-guide-body` (`display:grid;grid-template-columns:minmax(260px,.8fr) minmax(0,1.7fr);gap:22px`).

- [ ] **Step 5: Verify**

Run: `node --check site/features/command-centre/command-page.js` → clean.
Run: `python -m unittest tests.test_command_centre -v` → OK.
Screenshot `task8-home.png`: order is now serif regime verdict → stat tiles with colored moves → conflict watch → daily brief; "How to use this console" is a closed collapsible near the bottom that opens on click.

- [ ] **Step 6: Commit**

```bash
git add site/features/command-centre/command-page.js site/features/command-centre/command-page.css
git commit -m "feat: data-first command centre hero with stat tiles and collapsible guide"
```

---

### Task 9: COT positioning charts — horizontal rows (kill rotated labels)

Replace the vertical stacked columns (rotated 45° labels, cartoon gradients) with horizontal per-market rows: readable left-aligned names, a long/short split bar, values at the end. **Must remain SVG** with `role="img"`, `<title>`, `<desc>`, and per-row `data-cot-chart-select` + `tabindex="0"` + `role="button"` + `aria-label` — `tests/test_cot_interface.py` asserts `role="img"` and `<desc` exist in the source, and row click/keyboard selection is wired to `[data-cot-chart-select]`.

**Files:**
- Modify: `site/features/cot/cot-page.js` (`chartBalance()`, `chartDirectional()`; check the event wiring uses `closest('[data-cot-chart-select]')` — `grep -n "cot-chart-select" site/features/cot/cot-page.js`)
- Modify: `site/features/cot/cot-page.css` (new row-label/value classes, drop rotated-label rules)

**Interfaces:**
- Consumes: `shares(row)` → `{available, long, short}`; `signed()`, `number()`, `compact()`, `escapeHtml()` — all already in the module.
- Produces: same function names/signatures (`chartBalance(rowsToShow)`, `chartDirectional(rowsToShow, key, description)`) returning SVG strings; `positioningChart()` dispatch untouched.

- [ ] **Step 1: Replace `chartBalance()`**

```js
function chartBalance(rowsToShow) {
  const rowHeight = 34;
  const margin = { top: 30, right: 64, bottom: 12, left: 200 };
  const width = 980;
  const plotWidth = width - margin.left - margin.right;
  const height = margin.top + rowsToShow.length * rowHeight + margin.bottom;
  const axis = [0, 25, 50, 75, 100].map((tick) => {
    const x = margin.left + (tick / 100) * plotWidth;
    return `<line class="cot-chart-gridline ${tick === 50 ? 'zero' : ''}" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${margin.top - 6}" y2="${height - margin.bottom}"></line><text class="cot-chart-axis" x="${x.toFixed(1)}" y="${margin.top - 12}" text-anchor="middle">${tick}%</text>`;
  }).join('');
  const bars = rowsToShow.map((row, index) => {
    const split = shares(row);
    const y = margin.top + index * rowHeight;
    const barY = y + (rowHeight - 14) / 2;
    const name = `<text class="cot-chart-row-label" x="${margin.left - 12}" y="${y + rowHeight / 2 + 4}" text-anchor="end">${escapeHtml(row.name)}</text>`;
    if (!split.available) {
      return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: no reported long or short positions">
        ${name}<rect class="cot-chart-empty-bar" x="${margin.left}" y="${barY}" width="${plotWidth}" height="14" rx="7"></rect>
        <text class="cot-chart-value muted" x="${margin.left + plotWidth + 10}" y="${y + rowHeight / 2 + 4}" text-anchor="start">n/a</text>
      </g>`;
    }
    const longWidth = (split.long / 100) * plotWidth;
    return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: ${number(split.long, 1)} percent long and ${number(split.short, 1)} percent short">
      ${name}
      <rect class="cot-chart-long" x="${margin.left}" y="${barY}" width="${longWidth.toFixed(1)}" height="14"></rect>
      <rect class="cot-chart-short" x="${(margin.left + longWidth).toFixed(1)}" y="${barY}" width="${(plotWidth - longWidth).toFixed(1)}" height="14"></rect>
      <text class="cot-chart-value" x="${margin.left + plotWidth + 10}" y="${y + rowHeight / 2 + 4}" text-anchor="start">${number(split.long, 0)}%</text>
    </g>`;
  }).join('');
  return `<div class="cot-positioning-chart-scroll"><svg class="cot-positioning-svg" style="min-width:720px" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotPositioningTitle cotPositioningDesc">
    <title id="cotPositioningTitle">Long and short positioning by verified CFTC contract</title>
    <desc id="cotPositioningDesc">Each row totals 100 percent of reported long plus short positions. Green is long share, red is short share, and the right-hand value is the long percentage.</desc>
    ${axis}${bars}
  </svg></div>`;
}
```

(The old gradient `<defs>` disappear; solid token colors come from Task 2's CSS classes.)

- [ ] **Step 2: Replace `chartDirectional()`**

```js
function chartDirectional(rowsToShow, key, description) {
  const rowHeight = 34;
  const margin = { top: 30, right: 84, bottom: 12, left: 200 };
  const width = 980;
  const plotWidth = width - margin.left - margin.right;
  const height = margin.top + rowsToShow.length * rowHeight + margin.bottom;
  const maxAbsolute = Math.max(...rowsToShow.map((row) => Math.abs(Number(row[key] || 0))), 1);
  const zeroX = margin.left + plotWidth / 2;
  const axis = [-1, -0.5, 0, 0.5, 1].map((fraction) => {
    const x = zeroX + fraction * (plotWidth / 2);
    return `<line class="cot-chart-gridline ${fraction === 0 ? 'zero' : ''}" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${margin.top - 6}" y2="${height - margin.bottom}"></line><text class="cot-chart-axis" x="${x.toFixed(1)}" y="${margin.top - 12}" text-anchor="middle">${escapeHtml(compact(fraction * maxAbsolute))}</text>`;
  }).join('');
  const bars = rowsToShow.map((row, index) => {
    const value = Number(row[key] || 0);
    const barLength = (Math.abs(value) / maxAbsolute) * (plotWidth / 2);
    const y = margin.top + index * rowHeight;
    const barY = y + (rowHeight - 14) / 2;
    const x = value >= 0 ? zeroX : zeroX - barLength;
    const valueX = value >= 0 ? zeroX + barLength + 8 : zeroX - barLength - 8;
    return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: ${escapeHtml(signed(value))} contracts">
      <text class="cot-chart-row-label" x="${margin.left - 12}" y="${y + rowHeight / 2 + 4}" text-anchor="end">${escapeHtml(row.name)}</text>
      <rect class="${value >= 0 ? 'cot-chart-positive' : 'cot-chart-negative'}" x="${x.toFixed(1)}" y="${barY}" width="${Math.max(barLength, 2).toFixed(1)}" height="14"></rect>
      <text class="cot-chart-value" x="${valueX.toFixed(1)}" y="${y + rowHeight / 2 + 4}" text-anchor="${value >= 0 ? 'start' : 'end'}">${escapeHtml(compact(value))}</text>
    </g>`;
  }).join('');
  return `<div class="cot-positioning-chart-scroll"><svg class="cot-positioning-svg" style="min-width:720px" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotPositioningTitle cotPositioningDesc">
    <title id="cotPositioningTitle">${escapeHtml(description)} by verified CFTC contract</title>
    <desc id="cotPositioningDesc">Bars extend right for positive (green) and left for negative (red) values. Values are contract counts and are not comparable across differently sized futures markets.</desc>
    ${axis}${bars}
  </svg></div>`;
}
```

- [ ] **Step 3: CSS for the new row elements**

In `site/features/cot/cot-page.css`, remove the now-unused rotated-label styling on `.cot-chart-label` and add:

```css
.cot-chart-row-label{fill:var(--text-secondary);font-size:12px}
.cot-chart-value{fill:var(--text-primary);font-size:11px;font-variant-numeric:tabular-nums}
.cot-chart-value.muted{fill:var(--text-muted)}
.cot-chart-long{fill:var(--positive)}
.cot-chart-short{fill:var(--negative)}
.cot-chart-positive{fill:var(--positive)}
.cot-chart-negative{fill:var(--negative)}
.cot-chart-empty-bar{fill:var(--bg-elevated);stroke:var(--border-strong);stroke-dasharray:4 4}
.cot-chart-market{cursor:pointer}
.cot-chart-market:focus-visible rect{stroke:var(--focus-ring);stroke-width:2}
.cot-chart-gridline{stroke:rgba(160,166,178,.12)}
.cot-chart-gridline.zero{stroke:rgba(160,166,178,.35)}
.cot-chart-axis{fill:var(--text-muted);font-size:10px}
```

- [ ] **Step 4: Verify row selection still works**

`grep -n "data-cot-chart-select" site/features/cot/cot-page.js` — confirm the click/keydown delegation resolves via `closest('[data-cot-chart-select]')` (it targets the `<g>`, which is preserved). Manually click and keyboard-Enter a row in the browser: the per-market detail below must update.

- [ ] **Step 5: Verify**

Run: `node --check site/features/cot/cot-page.js` → clean.
Run: `python -m unittest tests.test_cot_interface tests.test_cot_contracts -v` → OK.
Screenshot `task9-cot.png`: horizontal rows, market names readable on the left, no rotated text, both long % visible; toggling LONG/SHORT ↔ NET POSITION ↔ WEEKLY CHANGE renders the diverging variant.

- [ ] **Step 6: Commit**

```bash
git add site/features/cot/cot-page.js site/features/cot/cot-page.css
git commit -m "feat: COT charts use horizontal rows with readable labels"
```

---

### Task 10: Impact Feed timeline — quieter, denser news rows

Match the reference news-feed feel: muted timestamp, strong headline, muted interpretation, hairline separators instead of heavy per-item card borders.

**Files:**
- Modify: `site/intelligence.css` (the `.impact-timeline*` / `.impact-*` rules — locate with `grep -n "impact-timeline\|impact-headline\|impact-summary" site/intelligence.css site/features/impact-feed/*.css 2>/dev/null`)

**Interfaces:**
- Consumes: existing markup from `site/features/impact-feed/impact-page.js` `timelineItem()` (`.impact-timeline-item`, `.impact-timeline-marker`, headline/summary/chips) — markup unchanged.

- [ ] **Step 1: Restyle the timeline items**

Adjust the located rules to these target values (keep selectors, replace declarations where they conflict):

```css
.impact-timeline-item{border:0;border-bottom:1px solid var(--border-subtle);border-radius:0;background:transparent;padding:18px 4px}
.impact-timeline-item:last-child{border-bottom:0}
.impact-timeline-item h4, .impact-timeline-item h3{font-size:15px;line-height:1.4;margin:6px 0 4px}
.impact-timeline-item p{color:var(--text-secondary);font-size:12.5px;line-height:1.55}
.impact-timeline-marker{background:var(--accent);width:7px;height:7px}
```

If a heavy inner card background (`background:var(--bg-panel)` or similar) exists on the item, remove it — the page canvas is the background. Keep the expanded causal-detail panel (`.impact-expanded`) as a bordered card so the expansion is visually distinct. Keep all status/`data-state` chips.

- [ ] **Step 2: Verify**

Run: `python -m unittest tests.test_impact_feed_interface tests.test_news_impact_contract -v` → OK.
Screenshot `task10-news.png`: the timeline reads as a clean news list with separators; "Show causal detail" still expands into a bordered panel.

- [ ] **Step 3: Commit**

```bash
git add site/intelligence.css
git commit -m "style: impact feed timeline uses hairline separators and quieter rows"
```

---

### Task 11: Crowd Expectations — probability-card polish

Style the market cards like rate-tracker probability cards: dominant % readout, muted source line, violet history sparkline.

**Files:**
- Modify: `site/features/crowd-expectations/crowd-page.css`

**Interfaces:**
- Consumes: existing markup from `crowd-page.js` (`.crowd-market-card`, `.crowd-probability strong/span`, `.crowd-sparkline`) — markup unchanged.

- [ ] **Step 1: Restyle**

Locate the matching rules in `crowd-page.css` and set:

```css
.crowd-probability strong{font-size:30px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.crowd-probability span{color:var(--text-muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}
.crowd-sparkline polyline, .crowd-sparkline path{stroke:var(--accent);stroke-width:2;fill:none}
.crowd-sparkline circle{fill:var(--accent)}
.crowd-market-card{background:var(--bg-panel);border:1px solid var(--border-subtle)}
```

(Adapt selector details to what actually exists in the file — the intent is: big tabular %, muted meta, violet thin history line, flat card.)

- [ ] **Step 2: Verify**

Run: `python -m unittest tests.test_crowd_expectations tests.test_crowd_selection_balance -v` → OK.
Open `#crowd` (Crowd Expectations nav item) in the browser and screenshot manually via the harness page (`node "..\market-brief-ui-shots\shoot.js" task11` covers the standard views; navigate + capture the crowd view with an added entry in VIEWS if its `data-view` differs — check `grep -n "data-view" site/index.html` for the exact route name).

- [ ] **Step 3: Commit**

```bash
git add site/features/crowd-expectations/crowd-page.css
git commit -m "style: crowd expectation cards emphasise probability readout"
```

---

### Task 12: Make the global search real (jump palette)

The topbar search is prominent, centred, and ⌘K-hinted — but typing does **nothing visible on 11 of 13 views** (it only filters cards on Assets and Research Library, wired in `site/app.js:183-235`). Give it a results dropdown that always works: matching views, asset workspaces, product dossiers and tracked filers, Enter/click to jump.

**Files:**
- Modify: `site/index.html` (add results host inside `.search`)
- Modify: `site/shell.js` (palette index + render + handlers, after the `routeMeta` block)
- Modify: `site/styles/shell.css` (dropdown styles)

**Interfaces:**
- Consumes: `routeMeta` and `goToRoute(route)` already in `shell.js`; research state via `window.MarketBriefCore.adapters.research()` → `{assetBiases: [{name, productId|id}], products: [{name, id}], trackers: {<id>:{name}}, trackerOrder: []}` (defaults defined in `core/adapters.js`, so every field is safe to read).
- Produces: `#searchResults` listbox; existing per-view filtering in `app.js` keeps working unchanged (the palette is additive).

- [ ] **Step 1: Add the results host in index.html**

Inside `<div class="search" role="search">…</div>` in the topbar, after the `<span class="kbd">` element, add:

```html
<div id="searchResults" class="search-results" role="listbox" aria-label="Search results" hidden></div>
```

- [ ] **Step 2: Check the existing Enter handler**

Run: `sed -n 225,240p site/app.js` — read what Enter currently does in the `#search` keydown listener. If it navigates somewhere, the palette's Enter behaviour (Step 3) must run first and stop propagation so the two don't fight; note what you found in the commit message.

- [ ] **Step 3: Add the palette to shell.js (after the `routeMeta` definition)**

```js
const paletteEsc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
function searchIndex() {
  const research = window.MarketBriefCore?.adapters?.research?.() || {};
  const entries = Object.entries(routeMeta)
    .filter(([route]) => !['today', 'official', 'crowd', 'equities', 'product-detail', 'asset'].includes(route))
    .map(([route, [title]]) => ({ label: title, hint: 'View', hash: route }));
  (research.assetBiases || []).forEach((bias) => entries.push({ label: bias.name, hint: 'Asset workspace', hash: `asset/${bias.productId || bias.id}` }));
  (research.products || []).forEach((product) => entries.push({ label: product.name, hint: 'Research dossier', hash: `product/${product.id}` }));
  const trackers = research.trackers || {};
  (research.trackerOrder || Object.keys(trackers)).forEach((id) => { const filer = trackers[id]; if (filer?.name) entries.push({ label: filer.name, hint: 'Political profile', hash: `trackers/${id}` }); });
  return entries;
}
function renderSearchResults(query) {
  const box = $('searchResults');
  if (!box) return;
  const term = String(query || '').trim().toLowerCase();
  if (term.length < 2) { box.hidden = true; box.innerHTML = ''; return; }
  const matches = searchIndex().filter((entry) => entry.label.toLowerCase().includes(term)).slice(0, 8);
  box.innerHTML = matches.length
    ? matches.map((entry) => `<button type="button" role="option" data-palette-hash="${paletteEsc(entry.hash)}"><strong>${paletteEsc(entry.label)}</strong><span>${paletteEsc(entry.hint)}</span></button>`).join('')
    : '<div class="search-empty">No local match across views, assets, dossiers and tracked filers.</div>';
  box.hidden = false;
}
function closeSearchResults() { const box = $('searchResults'); if (box) { box.hidden = true; box.innerHTML = ''; } }
const searchInput = $('search');
if (searchInput) {
  searchInput.addEventListener('input', () => renderSearchResults(searchInput.value));
  searchInput.addEventListener('keydown', (event) => {
    const box = $('searchResults');
    if (event.key === 'Escape') { closeSearchResults(); return; }
    if (event.key === 'ArrowDown' && box && !box.hidden) { event.preventDefault(); box.querySelector('button')?.focus(); return; }
    if (event.key === 'Enter' && box && !box.hidden) {
      const first = box.querySelector('button[data-palette-hash]');
      if (first) { event.preventDefault(); event.stopImmediatePropagation(); window.location.hash = first.dataset.paletteHash; closeSearchResults(); }
    }
  });
}
document.addEventListener('click', (event) => {
  const option = event.target.closest?.('[data-palette-hash]');
  if (option) { window.location.hash = option.dataset.paletteHash; closeSearchResults(); if (searchInput) searchInput.value = ''; return; }
  if (!event.target.closest?.('.search')) closeSearchResults();
});
```

Also add keyboard support inside the box (arrow between options, Enter activates — buttons get this for free; add `Escape` on the box to return focus):

```js
$('searchResults')?.addEventListener('keydown', (event) => {
  const options = [...event.currentTarget.querySelectorAll('button')];
  const index = options.indexOf(document.activeElement);
  if (event.key === 'ArrowDown') { event.preventDefault(); options[Math.min(index + 1, options.length - 1)]?.focus(); }
  if (event.key === 'ArrowUp') { event.preventDefault(); if (index <= 0) searchInput?.focus(); else options[index - 1]?.focus(); }
  if (event.key === 'Escape') { closeSearchResults(); searchInput?.focus(); }
});
```

- [ ] **Step 4: Dropdown CSS in styles/shell.css**

```css
.search-results{position:absolute;top:calc(100% + 6px);left:0;right:0;z-index:50;display:grid;max-height:340px;overflow-y:auto;padding:6px;border:1px solid var(--border-strong);border-radius:var(--radius-md);background:var(--bg-elevated);box-shadow:0 24px 60px rgba(0,0,0,.5)}
.search-results button{display:flex;justify-content:space-between;align-items:center;gap:12px;width:100%;padding:10px 12px;border:0;border-radius:var(--radius-sm);background:transparent;color:var(--text-primary);text-align:left;cursor:pointer}
.search-results button:hover,.search-results button:focus-visible{background:var(--bg-selected)}
.search-results button span{color:var(--text-muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}
.search-empty{padding:12px;color:var(--text-muted);font-size:12px}
```

- [ ] **Step 5: Verify**

Run: `node --check site/shell.js` → clean. `python scripts/audit_static_site.py` → passes. `python -m unittest tests.test_shell_contract tests.test_frontend_contract -v` → OK.
In the browser: type "gol" on the Command Centre → dropdown shows Gold asset workspace + Gold dossier; Enter jumps to the first; Escape closes; clicking outside closes; on the Assets view the existing card filtering still works while the dropdown shows.

- [ ] **Step 6: Commit**

```bash
git add site/index.html site/shell.js site/styles/shell.css
git commit -m "feat: global search palette jumps to views, assets, dossiers and filers"
```

---

### Task 13: De-chrome Official Feeds and Calendar nested cells

Official Feeds cards nest bordered OBSERVED/COLLECTED/LAST SUCCESS/CADENCE cells (and FILED/ACCEPTED cells per filing); Calendar event cards nest bordered PREVIOUS/CONSENSUS/ACTUAL cells. Same disease Task 5 cured on the macro cards — apply the same label:value row pattern.

**Files:**
- Modify: `site/features/official-feeds/official-feeds-page.css`
- Modify: `site/features/calendar/calendar-page.css`

**Interfaces:**
- Consumes: existing markup (unchanged); Task 5's visual pattern is the reference.

- [ ] **Step 1: Locate the boxed-cell rules**

Run: `grep -noE "[a-z-]+ (div|>div|dl div)\{[^}]*border[^}]*\}" site/features/official-feeds/official-feeds-page.css site/features/calendar/calendar-page.css | head -20`
Identify each rule that gives inner metadata cells their own `border` + `background` + `padding` box (in Official Feeds: the source-status meta grid and the per-filing date cells; in Calendar: the previous/consensus/actual triplet).

- [ ] **Step 2: Flatten them**

For each located rule, replace the boxed declarations with the Task 5 row pattern (keep the selectors):

```css
/* target look, adapt selector names to the file */
border: 0;
background: transparent;
padding: 3px 0;
```

and give the *containing* group a single hairline top border (`border-top:1px solid var(--border-subtle);padding-top:10px`) so the metadata region is still visually separated. Labels stay 10px uppercase `var(--text-muted)`, values 12px `tabular-nums` — add those declarations if the existing rules lack them. Keep the `data-state`/`SOURCED` badges untouched; keep "No approved source attached" and similar honesty strings visible.

- [ ] **Step 3: Verify**

Run: `python -m unittest tests.test_official_feeds tests.test_calendar_reactions -v` → OK (adjust module names to actual test files: `ls tests/ | grep -iE "official|calendar"`).
Screenshots of `#official-feeds` and `#events`: metadata reads as clean label:value rows; each card has at most one level of inner border.

- [ ] **Step 4: Commit**

```bash
git add site/features/official-feeds/official-feeds-page.css site/features/calendar/calendar-page.css
git commit -m "style: flatten nested metadata cells on official feeds and calendar"
```

---

### Task 14: Asset-route topbar fix + strip dead Command Centre skeleton

Two small structural bugs. (a) The asset workspace (`#asset/gold`) reuses the `view-product-detail` section (see `features/asset-workspace/asset-page.js:18-21`), so the topbar wrongly shows "Product Dossier / Detailed commodity research workspace" on asset pages. (b) `index.html` ships a full static Command Centre layout inside `<section id="view-home">` that `command-page.js` `render()` unconditionally replaces via `root.innerHTML` — dead bytes plus a flash of stale layout on load.

**Files:**
- Modify: `site/shell.js` (`routeMeta` + `updatePageContext`)
- Modify: `site/index.html` (`view-home` section contents)

- [ ] **Step 1: Add an asset meta entry and resolve it from the hash**

In `shell.js` add to `routeMeta`:

```js
asset: ['Asset Workspace', 'Evidence, flip conditions, catalysts and positioning for one asset.'],
```

and change `updatePageContext` to prefer the hash for asset routes:

```js
function updatePageContext(view = activeView()) {
  const hash = String(window.location.hash || '').replace(/^#/, '');
  const key = hash.startsWith('asset/') ? 'asset' : view;
  const [title, subtitle] = routeMeta[key] || routeMeta.home;
  if ($('pageTitle')) $('pageTitle').textContent = title;
  if ($('pageSubtitle')) $('pageSubtitle').textContent = subtitle;
  document.title = `${title} · Market Brief`;
}
```

- [ ] **Step 2: Check nothing asserts on the static home markup, then strip it**

Run: `grep -rn "commandRegime\|commandRisk\|biasTable\|command-intro" tests/ scripts/audit_static_site.py`
If no test/audit references them, replace the entire *contents* of `<section class="view active" id="view-home">…</section>` in `index.html` (the static `.command-hero`, `.command-grid`, bias table markup) with:

```html
<div class="command-empty">Loading command centre…</div>
```

The `<section>` tag itself, its `id`, and its classes must stay (route contract). If any test DOES reference one of those ids, keep a minimal `<div id="<that-id>"></div>` placeholder for each referenced id instead and note it in the commit.

- [ ] **Step 3: Verify**

Run: `node --check site/shell.js` → clean. `python scripts/audit_static_site.py` + `python -m unittest tests.test_frontend_contract tests.test_command_centre tests.test_shell_contract -v` → OK.
Browser: `#asset/gold` topbar shows "Asset Workspace"; `#product/gold` still shows "Product Dossier"; hard-reload on `#home` shows the loading hint briefly, then the rendered console, with no layout jump from stale markup.

- [ ] **Step 4: Commit**

```bash
git add site/shell.js site/index.html
git commit -m "fix: asset workspace topbar context + remove dead command centre skeleton"
```

---

### Task 15: Full verification sweep + PR

**Files:**
- Modify: `docs/PROJECT-STATUS.md` (dated entry describing the UI revamp, per AGENTS.md change discipline)

- [ ] **Step 1: Run the complete gate**

```bash
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check
find site/features -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/audit_static_site.py
python -m unittest discover -s tests -v
```

Expected: all clean/OK.

- [ ] **Step 2: AGENTS.md smoke checklist against localhost:8000**

- no browser-console exceptions on load (check via playwright `page.on('console')` or devtools);
- command centre renders (stat strip + serif verdict + collapsible guide);
- `#trackers` shows imported counts; `#cot` renders charts + history; `#rates` shows freshness/source status; `#scenarios` works desktop + mobile widths;
- direct hash links and sidebar navigation work; rail collapses after mouse click;
- generated-data failure states (source warnings, PARTIAL badges, retained-records notes) are all still visible.

- [ ] **Step 3: Final screenshot set + comparison**

Run: `node "..\market-brief-ui-shots\shoot.js" final`
Compare every `final-*.png` against `baseline-*.png`: consistent violet/neutral palette everywhere, no white GDELT card, no teal views, no rotated chart labels, no two-dot sparklines.

- [ ] **Step 4: Update PROJECT-STATUS.md**

Add a dated section summarising: theme unification, the four bug fixes, per-view restyles, and that no data contracts, routes, or generated files changed.

- [ ] **Step 5: Push branch and open PR — then STOP**

```bash
git push -u origin feat/ui-mrktedge-revamp
gh pr create --title "UI revamp: unify violet theme + mrktedge-style component polish" --body "<summary of tasks 1-14, before/after notes, checks run>"
```

Do NOT merge. Merging to `main` deploys to the public site; Chris reviews first.

---

## Deferred (explicitly out of scope for this plan)

- **Real FRED history sparklines:** needs a collector change (`scripts/update_free_data.py` + regeneration), mirroring how `update_free_data_charts.py` added `history52` for COT. Worth doing later; renderer should then use history when present and fall back to the delta chip.
- **Home-page length reduction** beyond Task 8 (tabbing/summarising the lower sections) — separate design decision.
- **Probability-history charts for Crowd Expectations** beyond the existing day-history sparkline.
- **Scenario Lab / Research Library deeper remodels** — they inherit the Task 1 palette flip; full component redesign is a later pass.
