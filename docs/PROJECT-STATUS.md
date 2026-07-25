# Market Brief Project Status

**Status date:** 25 July 2026 (Australia/Melbourne)

This file is the durable implementation handoff for the repository. It records what exists on `main`, what has been verified, what remains blocked, and the order in which the next work should be considered.

Do not treat chat history as the source of truth. Confirm every statement against the current repository, generated caches, workflow runs and provider documentation before changing code.

## Open branch pending review — Pressure Board PR-3: asset-first surfaces (25 July 2026)

`feat/pressure-board-pr3-surfaces` (open PR, **not merged to `main`**) is the flagship turn from a source catalogue into an asset-first brief (spec §5.2–§5.3). It consumes PR-1's engine and PR-2's tagger without touching either. Four tasks:

- **Dossiers (`#asset/<id>`).** The Asset Workspace leads with a net-pressure header (arrow + `up/down/mixed` counts from `collectDeterministicSignals`) over a three-tier **Observed / Verified / AI-tagged** evidence stack; the AI tier is fetched from `data/impact-tags.json` (guarded). The chip component (`site/core/impact-chips.js`) now defaults an empty `href` to `#asset/<id>` **for board assets only** — every board chip becomes navigation currency at once, while unknown (off-board) assets stay `<span>` so there are no dead links. `tests/test_asset_dossier.py` (6) + updated `tests/js/impact-chips.test.js`.
- **Home board (Today).** `home` now leads with the **Pressure Board** — 22 assets grouped by the six families (Energy, Metals, Softs/Ags, Rates/FX, Indices, Themes), each row a link to its dossier showing net state (↑/↓/CONTESTED/QUIET), `up/down/mixed` counts, an **honest `—` price dash** where no free feed exists (never invented), and the strongest observed driver. Inserted immediately after the existing regime verdict hero — nothing removed. Followed by **Top drivers** (the AI ledger ranked by tag-count then confidence) and **Watchpoints** (standing triggers + upcoming releases). Every block degrades to an explicit empty state; the board is guarded so a missing engine never crashes Today. Extended `tests/test_command_centre.py`.
- **Week view (`#week`).** A new lazy-loaded feature route (manifest entry in `site/core/feature-loader.js`) rendering the same board grammar **windowed to the trailing 7 days** via the engine's `since` option, plus a day-by-day AI digest, this week's COT shifts, crowd swings, and the week-ahead calendar. QUIET rows render dimmed, not hidden. `tests/test_week_view.py` (12).
- **Navigation.** The rail is regrouped into **Brief** (Today, This Week, Assets) / **Evidence** (Impact Feed, Calendar, COT, Political, Rates) / **System** (Regime, Trigger Zones, Research Library, Scenario Lab, Archive). All 13 routes preserved; the shell-contract accessibility + mobile-parity tests stay green.

Suite green apart from the one pre-existing date-fragile freshness test; `scripts/audit_static_site.py` exit 0; `node --check` clean on the changed scripts. Real-browser (headless Blink) smoke verified all three new surfaces render: the Today board, a `#asset/gold` dossier (Observed/Verified/AI-tagged stack + display-only TradingView context), and `#week`. The smoke confirmed the `since` windowing is real — Brent and WTI show **QUIET** on the trailing-7-day board while still carrying pressure on the all-time Today board. AI blocks currently show their honest "awaiting the next tagging run" empty state because the PR-2 tagger has not yet populated `impact-tags.json` on `main` (needs the `ANTHROPIC_API_KEY` secret + one workflow run). Deferred to a follow-up: the optional brief-archive step (spec §4.5 — the week digest already works from the 7-day ledger without it) and a raw magnitude field on crowd signals (the week crowd-swing sort currently re-parses magnitude from formatted detail text, which is fragile).

## Open branch pending review — Central-bank decision tracker (25 July 2026)

`feat/central-bank-decision-tracker` (open branch, **not merged to `main`**) adds a read-only central-bank rate-decision tracker and its **"Rate decisions" view**. The collector (`scripts/update_central_bank_decisions.py`) performs targeted per-bank discovery against the same Polymarket public-search endpoint used by Crowd Expectations — reusing its tested helpers — for a fixed nine-bank registry (`scripts/central_bank_registry.json`: Fed, ECB, BoE, BoJ, RBA, BoC, BoK, Banxico, RBNZ), maps each event's outcomes to policy buckets (50+ bps cut, 25 bps cut, no change, 25 bps hike, 50+ bps hike) and writes `site/data/central-bank-decisions.json`. Output is schema- and semantically validated (`schemas/central-bank-decisions.schema.json` + `scripts/validate_central_bank_decisions.py`), covered by `tests/test_central_bank_decisions.py`, and fed into the impact engine (a directional signal plus Pressure Board wiring for banks with a mapped board asset). The read-only Polymarket protections carry over unchanged: no wallet, authentication, deposit, signing or order code; stale retention on source failure; one verified snapshot per UTC day for up to 90 days.

A dedicated refresh workflow (`.github/workflows/update-central-bank-decisions.yml`) runs the compile-guard + unit tests, collector and validator on `workflow_dispatch`, on pushes to the tracked files, and on a six-hourly schedule (`47 */6 * * *`, offset 30 minutes from Crowd Expectations' `:17`). It mirrors the Crowd Expectations workflow exactly — identical `permissions`, the shared `generated-data-writer` concurrency group, pinned checkout/setup actions, and the commit-generated-data → rebase → re-validate → push → deploy trigger — changing only the paths, schedule and CB-specific run/validate/commit-path lines.

## Merged to `main` — Pressure Board PR-1 (impact grammar) + PR-2 (AI news tagger)

Both PR-1 (`feat/pressure-board-pr1-grammar`) and PR-2 (`feat/pressure-board-pr2-tagger`) have since **merged to `main`** (PR-2 at merge commit `541e005`); PR-1 shipped live and PR-2's tagger workflow is wired. The detailed entries below were written while each was an open branch and describe the same delivered scope. **Operator prerequisite still outstanding:** add the `ANTHROPIC_API_KEY` GitHub Actions secret so the hourly GDELT workflow's tagger step populates `site/data/impact-tags.json`; until then everything ships fine and the AI tiers show "AI tagging pending".

## Delivered scope (PR-2 detail) — AI news tagger

`scripts/tag_impacts.py` adds the Claude news-impact tagger from the design spec §4.1. `scripts/tag_impacts.py` batches new GDELT-radar + conflict-watch items to `claude-haiku-4-5` (raw `urllib`, stdlib only) and records validated directional tags (`{assetId, direction, confidence, mechanism}`) in a self-contained 7-day ledger `site/data/impact-tags.json`. `scripts/validate_impact_tags.py` drops any tag outside the closed asset vocabulary or the `up|down|mixed` / `high|medium|low` enums; malformed model output → `tagFailed` (retried, capped at 3 attempts → `unavailable`). The GDELT News-radar cards render the tags as `tier-ai` chips (reusing PR-1's chip component; dashed + "AI" badge, `conf-low` dimming, `href:''` so no dead links) with honest `AI tagging pending` / `AI tagging unavailable` states. Wired as a step in the hourly GDELT workflow (`ANTHROPIC_API_KEY` from repo secrets); the tagger is **fail-open** — a missing key or model outage never breaks the build (news simply ships untagged). 27 tagger unit tests + a source-contract UI test + a workflow-contract test; the suite stays green apart from the one pre-existing date-fragile freshness test.

**Operator prerequisite:** add the `ANTHROPIC_API_KEY` GitHub Actions secret (Settings → Secrets → Actions) before the tagger will populate the ledger. Until then, everything ships fine and news cards show "AI tagging pending". Conscious single-writer choice: the tagger runs only in the GDELT hourly workflow but reads *both* news sources, so conflict-watch items are tagged there too (no cross-workflow commit race). Deferred to PR-3: the curated Verified-tier chips and the Today/Week board consuming these tags.

## Open branch pending review — UI revamp (16 July 2026)

Branch `feat/ui-mrktedge-revamp` (open PR, **not merged to `main`**) carries a presentation-only revamp toward an mrktedge.ai-style design language. It changes no data logic, no route contracts, and no generated files; the unittest suite (195 tests) and `scripts/audit_static_site.py` stay green.

- **Theme:** retired the legacy teal `:root` in `styles.css` and swept the remaining hardcoded teal literals in `command-centre.css`, `free-data.css`, `intelligence.css`, `scenario-lab.css` so the violet design tokens (`styles/tokens.css`) drive every view.
- **Bug fixes:** GDELT radar card was white-on-white (undefined light-theme fallback vars) → dark tokens; nav rail stuck expanded after a mouse click (`:focus-within` → `:has(:focus-visible)`); fake two-point FRED sparklines → delta chips.
- **Components:** data-first Command Centre hero (serif verdict + stat tiles, collapsible how-to); COT charts rebuilt as horizontal rows (no rotated labels); inline Lucide SVG icon sprite + favicon; quieter Impact Feed rows; unified status badges; de-chromed Official Feeds / Calendar / Rates metadata cells; probability-forward Crowd cards.
- **New:** a global search jump palette in the topbar (previously a dead end on 11 of 13 views) matching views, asset workspaces, dossiers and navigable political filers.
- **Structural:** correct "Asset Workspace" topbar context for `#asset/*`; removed a dead static `#view-home` skeleton and guarded two superseded legacy renderers (`command-centre.js`, `app.js` `openProduct`) so they cannot throw.
- **Reviewed:** a 6-dimension adversarial agent review (Fable xhigh) raised 6 findings; all were addressed (palette no longer lists the profile-less Trump tracker; combobox ARIA + focus restore on the palette; COT negative-value-label overlap fixed; teal sweep completed).

Real-browser Playwright smoke: zero new console errors (only pre-existing TradingView third-party CORS), all 18 views + mobile render, rail-collapse / palette-jump / COT row-select / asset↔product navigation verified.

## Delivered scope (PR-1 detail) — impact grammar

`feat/pressure-board-pr1-grammar` (since **merged to `main`**) adds the closed-vocabulary asset board (`scripts/asset_board.json` → generated `site/asset-board-data.js`), the deterministic impact engine (`site/core/impact-engine.js`), and the tiered chip component (`site/core/impact-chips.js` + `site/styles/chips.css`), applied to COT, Rates (+ a visible rules table), Crowd, Political (both tables, lag-excluded), Official-feeds (SEC filings + BLS prints) and Calendar (watch-only) cards. Pages delegate to the engine's single-row derivations — no duplicated signal logic. No model tagging yet (PR-2), no home board (PR-3), no new sources (PR-4). Spec + plan live on the `plan/trader-pressure-board` docs branch (`docs/superpowers/specs/2026-07-16-trader-pressure-board-design.md`), not on `main`, per the repo's docs-branch governance.

Suite green (`scripts/audit_static_site.py` + the unittest suite, aside from one pre-existing date-fragile freshness test unrelated to this PR); real-browser Playwright smoke verified chips render on all six pages with correct arrows/colours/glyphs, no dead links (all chips are `<span>` in PR-1), and no new console errors. Internal review fixes: calendar watch chips dedupe by board asset (alias collisions such as Bonds + US 10Y → us10y); the crowd derivation propagates `market.status`. External adversarial review (Codex) then drove: removal of the inverted `us10y` COT join (Treasury-note positioning mapped to the yield asset communicated the opposite direction; the correct DGS10 yield chip stays), exact-contract provenance in COT chip detail, source-status propagation for rate/SEC/BLS signals, and gating calendar watch chips to `upcoming` events (released events no longer claim to be scheduled). Deferred to PR-2/PR-3: ETF SMH+SOXX dedup, the trailing-window timestamp/date-granularity contract, and fail-closed handling of malformed model-tagged signals.

## Repository and deployment

- Repository: `TheDiamondDealer/market-brief`
- Default branch: `main`
- Current visibility: public
- Current deployment: static GitHub Pages
- Live URL: `https://thediamonddealer.github.io/market-brief/`
- Runtime backend: none
- Runtime database: none
- Frontend framework or bundler: none
- Deployment artifact: `site/`

The current public architecture means everything under `site/` is publicly downloadable. No licensed private feed may be activated while either the repository or deployed origin exposes its generated cache publicly.

## Governing documents

Read these before substantial work:

1. `AGENTS.md`
2. `README.md`
3. `docs/PROJECT-STATUS.md`
4. `docs/RESEARCH-GOVERNANCE.md`
5. `docs/ARCHITECTURE.md`
6. `docs/DATA-SOURCES.md`
7. `docs/RUNBOOK.md`
8. `docs/CODEX-HANDOFF.md`
9. `operating-model.md`
10. Relevant files under `prompts/`
11. All workflows touched by the proposed change

Specialised implementation documents include:

- `docs/OFFICIAL-FEEDS.md`
- `docs/CROWD-EXPECTATIONS.md`
- feature-specific documentation present under `docs/`

## Product state

The major static-dashboard remodel packages BR-01 through BR-19 are complete. The repository now includes:

- a modular static application shell;
- command-centre and research views;
- Impact Feed;
- Political Flow;
- COT Positioning;
- Rates and Liquidity;
- Asset Workspaces;
- Scenario Lab;
- Source Health;
- generated-data schemas and semantic validation;
- static accessibility and payload auditing;
- scheduled official-data collectors;
- read-only Crowd Expectations;
- dormant private-market-data plumbing.

The static architecture and existing hash routes must be preserved unless a separately approved migration plan replaces them.

## Current data sources

### Conflict and war trigger watch

Command Centre now leads with a four-step Decision Console guide and a recurring official conflict-publication watch. The watch checks United Nations Middle East and U.S. defence publications every three hours, shows the five latest relevant updates, links directly to each official source and separates those publications from conditional Market Brief transmission analysis. Temporary source failures retain previously verified items visibly.

### CFTC Commitments of Traders

The COT workspace tracks a 46-product reference catalogue spanning metals, energy, currencies, rates, equity indices, grains, softs and Bitcoin. Forty-five products have exact current CFTC identities. Oats remains visibly unavailable because its exact CBOT series has not published since 2 June 2026.

Exact derivative products such as NYMEX Brent Last Day, ICE WTI and NYMEX WTI Financial are labelled and tracked separately. They must not be represented as the unavailable intended ICE Brent or historical NYMEX WTI benchmark entries. The same non-substitution rule remains in force for intended US Henry Hub and UK NBP benchmarks.

Partial refresh failures retain previously verified rows with an explicit stale-retained state; missing products without a verified cache remain visible in registry coverage diagnostics.

### FRED and official rate series

Operational series include:

- 2-year, 5-year, 10-year and 30-year US Treasury yields;
- 10-year real yield;
- 10-year breakeven inflation;
- US high-yield spread;
- effective federal funds rate;
- SOFR;
- broad trade-weighted US dollar.

Each series keeps its own observation date. One updated series must not make the whole rates panel appear current.

### Political disclosures

Operational official-source collectors cover:

- US House Clerk annual indexes and PTR PDFs;
- US Senate eFD PTR records.

Non-negotiable rules:

- traded and filed dates remain separate;
- verified history is retained permanently;
- spouse/member/joint/dependent ownership is preserved;
- statutory values remain ranges;
- portfolio reconstructions are disclosure-derived estimates, not brokerage balances;
- official filings outrank third-party parsers.

### Free official agency feeds

Current generated status after the July 2026 audit:

- **BLS:** current; eight configured series and zero missing in the verified live refresh;
- **USGS:** current annual Mineral Commodity Summaries release detection;
- **SEC EDGAR:** failed from GitHub-hosted runners because official submissions endpoints returned HTTP 403;
- **EIA:** unavailable until `EIA_API_KEY` is configured;
- **BEA:** unavailable until `BEA_API_KEY` is configured;
- **Census:** unavailable until `CENSUS_API_KEY` is configured.

Missing keys must remain explicit `unavailable` states. They must not cause other agencies to fail and must never be placed in source files, browser JavaScript or logs.

### Crowd Expectations

The Polymarket integration is read-only public market data. It contains no wallet, authentication, deposit, signing or order code.

Verified protections include:

- binary YES/NO validation;
- sports, entertainment, celebrity and standalone crypto-price exclusions;
- calculated bid-minus-ask validation rather than blind trust in a provider spread field;
- resolution-source extraction from direct fields, event metadata and market rules;
- Grade A prohibited when no identifiable resolution source exists;
- event-specific asset mapping;
- category and event-family balancing after all quality filters;
- one daily UTC snapshot retained for up to 90 days;
- stale retention on source failure;
- structural checks for execution endpoints and secret-bearing fields.

The latest verified live selection contained 48 markets with category balancing. A zero category is acceptable when no qualifying contract passes the unchanged filters.

### TradingView

TradingView remains an external embedded display and discovery layer only.

Do not:

- scrape widget contents;
- represent widget values as internal API data;
- use widget data in the internal bias engine;
- claim that a personal TradingView subscription licences redistribution.

### Curated research

Daily, weekly and monthly interpretation is hand-curated or research-generated. It is not a live news wire. Observations, guidance, consensus, forecasts, inference and opinion must remain distinguishable.

## Private Twelve Data feed

The Twelve Data pipeline exists but is deliberately dormant.

Current state:

- provider status: unavailable;
- collection mode: disabled;
- prices published: none;
- configured watchlist: semiconductors, mining, critical minerals and benchmark ETFs;
- generated cache contains no licensed prices.

It must remain disabled while the repository or deployed site is public.

Activation requires all of the following:

1. private repository;
2. protected Cloudflare Pages deployment;
3. Cloudflare Access applied to both the custom domain and generated `pages.dev` hostname;
4. removal or disabling of the public GitHub Pages origin;
5. `TWELVE_DATA_API_KEY` stored only as a GitHub Actions secret;
6. explicit activation gates such as `PRIVATE_SITE_ACCESS_CONFIRMED` and `PRIVATE_MARKET_DATA_ENABLED` set only after access is independently verified;
7. confirmation that the selected Twelve Data plan permits the intended internal use.

A failed current quote must never be masked by retained history. Fresh quote responses, fresh history responses and stale retained rows are counted separately.

## July 2026 post-integration audit

The audit found and corrected material defects through PRs #29, #30 and #31.

### Fixed: Source Health recursion

Official Feeds and Crowd Expectations previously listened for and redispatched the same source-health event. This could create repeated asynchronous updates. Both bridges are now idempotent and write only when their own records are absent or changed.

### Fixed: Twelve Data false freshness

A failed quote could be obscured by retained daily history. The pipeline now advances `lastSuccessfulAt` only after a fresh accepted provider response and distinguishes retained stale values from current collection.

### Fixed: BLS false partial status

Unused optional calculations generated advisories that were being interpreted as incomplete data. Complete configured observations now remain current, advisory text remains visible, and the live workflow fails if `0 missing` is ever published as partial.

### Fixed: Crowd validation false positives

Legitimate resolution prose could contain generic words that resembled prohibited trading markers. Validation now checks controlled keys and URLs structurally rather than scanning ordinary market prose.

### Fixed: Crowd resolution-source scoring

Resolution sources embedded in event metadata or rules are now captured. Markets without identifiable resolution sources cannot receive Grade A.

### Fixed: Crowd spread validation

Midpoint eligibility and quality use calculated best-ask minus best-bid spread.

### Fixed: Crowd asset contamination

Broad category defaults previously attached asset-specific events to unrelated assets. Asset mapping now uses event wording.

### Fixed: Crowd ranking concentration

High-volume macro event families could monopolise the 48 retained positions. Selection now applies category reserves, a category cap and an event-family cap only after all original relevance, liquidity, volume and quality filters have passed.

## Known limitations and open work

### Owner-controlled repository settings

Branch protection remains an owner-controlled setting. Do not claim it is enabled unless repository settings prove it.

### SEC EDGAR runner block

SEC remains blocked by HTTP 403 from GitHub-hosted runners despite:

- descriptive user agents;
- pinned CIKs;
- ticker verification;
- direct submissions endpoints;
- throttling.

Do not replace SEC with an unverified third-party parser. The preferred next experiment is a controlled alternate outbound environment such as a self-hosted runner or Cloudflare Worker, with the official filing remaining the source of truth.

### Missing free API keys

Required secrets still absent unless repository settings show otherwise:

- `EIA_API_KEY`
- `BEA_API_KEY`
- `CENSUS_API_KEY`

Optional:

- `BLS_API_KEY`

### Public/private deployment decision

The largest architectural decision is whether to:

- retain the public free-data research dashboard; or
- create a separate private deployment for licensed data and private features.

Do not activate private feeds merely because the repository was changed to private. The deployed origins must also be access-controlled.

### Market Baseline Dossier

The research framework is documented, but the full current baseline dossier must be generated through fresh research and human approval. Monthly work may create drafts but must not overwrite approved live strategic files without explicit approval naming the month.

## Recommended next-work order

1. **Codex audit-only review** of current `main`, documentation, workflows, generated data and live routes.
2. **Owner privacy decision** for public versus private deployment.
3. **Configure free official keys** and verify each generated series against its official identity.
4. **Move SEC collection** to an environment accepted by SEC.
5. **Generate the July 2026 Market Baseline Dossier** under the research-governance rules and preserve the approval gate.
6. **Add browser automation** for high-value routes and data hydration without replacing existing offline validation.
7. **Consider a backend only when justified** by private accounts, alerts, large history, incremental ingestion or licensed real-time feeds.

## Full validation

Use the same commands as `.github/workflows/validate.yml`:

```bash
python scripts/check_ci_pins.py
python -m pip install --disable-pip-version-check --requirement requirements/ci.txt
python -m pip check
python -m py_compile scripts/*.py tests/*.py
find site tests/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/validate_generated_data.py
python scripts/validate_crowd_expectations.py
python scripts/audit_static_site.py
python -m unittest discover -s tests -v
```

For browser verification:

```bash
python -m http.server 8000 --directory site
```

Verify at least:

- `#home`
- `#today` (legacy redirect to `#home`; Daily Brief is merged into Command Centre)
- `#news`
- `#cot`
- `#rates`
- `#official-feeds`
- `#crowd-expectations`
- `#scenarios`
- `#trackers`
- representative asset and product-detail routes
- desktop and mobile navigation
- no console exceptions or missing generated modules

## Change discipline for the next reviewer

Start audit-only. Do not fix issues during the first discovery pass.

The first report should separate:

- confirmed defect;
- documentation drift;
- expected unavailable source;
- missing credential;
- provider restriction;
- architectural debt;
- enhancement opportunity.

For any later implementation:

- create a dedicated branch;
- fix only reproducible defects or an explicitly approved work package;
- update the source collector rather than manually editing generated data;
- run the full validation suite;
- inspect generated output samples;
- open a pull request with evidence and known limitations;
- merge only after CI passes.
