# Market Brief Architecture

Last reviewed: 14 July 2026

## Runtime model

Market Brief is a static GitHub Pages application. There is no application server, database, secret-bearing browser request or bundler.

The page starts from `site/index.html` and loads ordered global scripts. Core modules attach to `window.MarketBriefCore`:

- `site/core/store.js` — immutable slice store and subscriptions.
- `site/core/format.js` — shared formatting and HTML escaping.
- `site/core/adapters.js` — access to official, research, evidence and scenario globals.
- `site/core/router.js` — hash router, aliases and pattern routes.
- `site/core/feature-loader.js` — ordered feature manifest.
- `site/core/freshness.js` — unified per-source and per-series health registry.

`feature-loader.js` first loads global hardening CSS and the freshness registry. It then loads each route package in manifest order. This keeps `index.html` stable while allowing individual remodel packages to own their presentation.

## Route packages

| Route | Feature package | Primary host |
| --- | --- | --- |
| `#home` | `features/command-centre` | `view-home` |
| `#news` and `#news/<id>` | `features/impact-feed` | `view-news` |
| `#cot` | `features/cot` | `view-cot` |
| `#trackers` and `#trackers/<id>` | `features/political-flow` | `view-trackers` |
| `#asset/<id>` and `#product/<id>` | `features/asset-workspace` | `view-product-detail` |
| `#events`, `#calendar`, `#calendar/<id>` | `features/calendar` | `view-events` |
| `#rates`, `#macro` | `features/macro-monitor` | `view-rates` |
| `#sources`, `#source-health` | `features/source-health` | dynamically created `view-sources` |

Legacy route names are retained where users or bookmarks may still rely on them.

## Data layers

### Official market layer

Generated outputs:

- `site/free-data.js`
- `site/data/free-market-data.json`

The free official-data collector produces FRED series, derived Treasury curve spreads, exact-registry CFTC positioning and source metadata. The JSON file is canonical; the JavaScript file is the browser bootstrap.

### COT contract integrity

The exact registry lives in `scripts/cot_contracts.json`, `scripts/cot_contracts.py` and `schemas/cot-contract-registry.schema.json`.

A row is emitted only when contract code, accepted market name, exchange, report family and report category all match. Unavailable intended benchmarks remain unavailable.

### Political disclosure layer

Canonical retained history:

- `site/data/political-disclosures.json`
- `site/data/political-disclosures-summary.json`
- `site/data/political/filing-ledger.json`

Lazy browser layout:

- `site/data/political/manifest.json`
- `site/data/political/summary.json`
- `site/data/political/<politician>/summary.json`
- `site/data/political/<politician>/<year>.json`
- `site/data/political/indexes/politicians.json`
- `site/data/political/indexes/tickers.json`
- compact `site/political-data.js` bootstrap.

`site/features/political-flow/political-data.js` fetches profile, annual and search-index files only when requested.

### Research layer

Repository-maintained research globals provide strategic baseline text, asset-bias records, physical checklists, event/reaction records, scenarios and delayed curated news.

Adapters convert legacy structures into versioned contracts without changing editorial meaning:

- `schemas/news-impact.schema.json`
- `schemas/calendar-events.schema.json`
- `features/impact-feed/impact-data.js`
- `features/calendar/calendar-data.js`

Unknown fields remain explicitly unknown rather than inferred.

### External display layer

TradingView is embedded inside asset workspaces as a display-only iframe. Prices and indicators are not copied into internal datasets.

## Source health

`site/core/freshness.js` normalises records into source observation time, collection time, generation time, expected cadence, last successful run, status, detail, error and URL.

Statuses are `current`, `delayed`, `stale`, `failed`, `unavailable`, `partial` and `unknown`.

Macro series and COT contracts are evaluated independently. A current FRED or CFTC pipeline cannot conceal a stale individual observation.

## Generated-file ownership

Generated outputs are never manually edited. Collector workflows regenerate, validate, commit only passing changes, rebase on current `main` and invoke Pages deployment after success. See `docs/DATA-SOURCES.md` for the ownership table.

## Validation architecture

`Validate Market Brief` runs:

1. immutable GitHub Action pin validation;
2. Python compilation;
3. recursive JavaScript syntax validation under `site/` and `tests/js/`;
4. generated schema and semantic validation;
5. static performance, accessibility and payload audit;
6. release route and generated-ownership verification;
7. offline unit, fixture, workflow and route tests.

`scripts/audit_static_site.py` checks duplicate IDs/assets, local references, accessible names, iframe/link safety, viewport contracts and payload budgets.

`scripts/verify_release_routes.py` verifies required routes, aliases, exact COT unavailable set and generated ownership.

## Performance and accessibility

`site/styles/hardening.css` is loaded before route packages. It provides visible keyboard focus, 44-pixel interactive targets, overflow-safe tables and text, reduced-motion support, forced-colour support and explicit 1440, 1024, 768 and 390-pixel viewport contracts.

Political history is excluded from the initial browser payload. Route packages are loaded through one auditable manifest, and external charts use lazy iframes.

## Compatibility boundaries

Legacy files remain where the static shell or older routes may still reference them. Do not delete a module until search and route tests prove no remaining consumer.

`site/command-centre.js` is an explicit compatibility shim. The composite-score renderer is retired; the actual home route is `features/command-centre/command-page.js`.

## Optional future architecture

BR-20 is outside the completed mandatory remodel. Live news, licensed prices, consensus data, user accounts, alerts, queues or secret-bearing APIs require separate source, licensing and architecture approval.
