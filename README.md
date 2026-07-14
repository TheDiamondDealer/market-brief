# Market Brief Intelligence Console

A static, research-led market intelligence dashboard focused on commodities, macro, rates, positioning, causal news interpretation and delayed public political disclosures.

**Live dashboard:** https://thediamonddealer.github.io/market-brief/

> Research and system testing only. Not financial advice. Political transaction data is delayed public disclosure, not real-time execution data. The Impact Feed is delayed curated research, not a live news wire.

## Completed mandatory remodel

BR-01 through BR-19 are implemented. The current product includes:

- **Command Centre** — up to three priority events, active contradictions, asset flip conditions, exact COT changes, political filings and source failures. No hidden composite risk score.
- **Impact Feed** — versioned directional interpretations with magnitude, horizon, confidence, mechanism, confirmation, invalidation and sources.
- **COT Positioning** — category filters, contract search, net/long-short/weekly-change modes, history and exact CFTC identity disclosure.
- **Political Flow** — recent filings, politician profiles, ticker reverse search, disclosed owner/account, statutory ranges, lazy annual history and filing-ledger health.
- **Asset Workspaces** — display-only external chart, supporting/contradicting evidence, flip rules, impact events, calendar catalysts, exact COT and physical checks.
- **Calendar & Reactions** — Melbourne release times, independent previous/consensus/actual source states and immediate/close/+1/+5 reaction lifecycle.
- **Macro Monitor** — official rates, liquidity, real yields, breakevens, credit and broad US dollar series with individual observation dates.
- **Source Health** — independent observation, collection, generation, cadence, last-success and error records.
- **Production hardening** — recursive syntax checks, generated-data validation, static accessibility/performance audit, payload budgets and release-route verification.

BR-20 is optional and has not been started. It covers licensed/live feeds, consensus data, accounts, alerts and backend services.

## Architecture

The site is plain HTML, CSS and JavaScript deployed to GitHub Pages. There is no application server, database, secret-bearing browser request, framework or bundler.

Core runtime:

- `site/index.html`
- `site/core/store.js`
- `site/core/format.js`
- `site/core/adapters.js`
- `site/core/router.js`
- `site/core/feature-loader.js`
- `site/core/freshness.js`

Feature routes are loaded through one ordered manifest under `site/features/`.

## Main routes

- `#home`
- `#news` and `#news/<id>`
- `#cot`
- `#trackers` and `#trackers/<id>`
- `#asset/<id>` and legacy `#product/<id>`
- `#events`, `#calendar`, `#calendar/<id>`
- `#rates`, `#macro`
- `#sources`, `#source-health`

## Data and trust boundaries

Official automated data currently includes:

- CFTC exact-contract COT records;
- selected FRED macro and rates series;
- official House and Senate political disclosure filings.

Repository-maintained delayed research supplies regime, asset bias, physical checklists, event scenarios and curated impact records.

Unavailable data remains unavailable rather than being replaced with a similar contract, estimate or unsourced value.

See:

- `docs/DATA-SOURCES.md`
- `docs/ARCHITECTURE.md`
- `docs/RUNBOOK.md`

## Local development

```bash
python -m http.server 8000 --directory site
```

Open `http://localhost:8000`.

## Full validation

```bash
python scripts/check_ci_pins.py
python -m py_compile scripts/*.py tests/*.py
find site tests/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/validate_generated_data.py
python scripts/audit_static_site.py
python scripts/verify_release_routes.py
python -m unittest discover -s tests -v
```

The `Validate Market Brief` workflow enforces the same gates before merge.

## Generated files

Do not manually edit generated market or political data. Change the owning collector/schema/fixture and let the workflow regenerate the output. The ownership table is in `docs/DATA-SOURCES.md`.

## Deployment

`site/` is deployed by `.github/workflows/deploy-pages.yml`. Successful collector runs invoke deployment, and relevant site/workflow pushes to `main` trigger deployment after BR-19.

A deployment run and an independently verified public revision are different facts. Follow `docs/RUNBOOK.md` for live verification.

## Repository controls

Owner-only activation of the `main` protection ruleset remains tracked in GitHub issue #4 until it is enabled and tested.
