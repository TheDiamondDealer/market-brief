# Market Brief Project Status

**Status date:** 15 July 2026 (Australia/Melbourne)

This file is the durable implementation handoff for the repository. It records what exists on `main`, what has been verified, what remains blocked, and the order in which the next work should be considered.

Do not treat chat history as the source of truth. Confirm every statement against the current repository, generated caches, workflow runs and provider documentation before changing code.

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

### CFTC Commitments of Traders

Operational for exact mapped contracts including:

- gold;
- silver;
- copper;
- Japanese yen;
- US 10-year Treasury futures;
- US Dollar Index.

Unsafe or ambiguous contract mappings remain unavailable rather than being replaced with a similar contract. WTI, Brent, US Henry Hub and UK NBP positioning must not be described as operational unless exact contract mapping is verified in the generated output.

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
- `#today`
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
