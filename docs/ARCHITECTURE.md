# Architecture

## Purpose

Market Brief is a static GitHub Pages application backed by scheduled research and public-data collectors. It aims to provide an auditable market-intelligence workspace without requiring a paid market-data API or an always-on application server.

The system has three distinct layers:

1. **Source collection** — official datasets, filings and research inputs.
2. **Normalization and interpretation** — Python collectors and curated JavaScript research objects.
3. **Static presentation** — browser-rendered dashboard deployed from `site/`.

## High-level data flow

```text
Official public sources                    Research process
(CFTC, FRED, House, Senate, etc.)          (daily / weekly / monthly)
             │                                      │
             ▼                                      ▼
      Python collectors                     curated research state
             │                                      │
             ├── validation                         ├── regime
             ├── deduplication                      ├── news interpretation
             ├── freshness/status                   ├── triggers
             └── historical retention               └── product dossiers
             │                                      │
             └──────────────┬───────────────────────┘
                            ▼
                    static JS / JSON caches
                            │
                            ▼
                     `site/index.html`
                            │
                            ▼
                     GitHub Pages deploy
```

## Runtime model

The frontend is deliberately simple:

- no Node package install;
- no bundler;
- no application server;
- no database at runtime;
- no client-side secret;
- no paid API required for the current version.

The browser receives static HTML, CSS and JavaScript. JavaScript modules currently share global objects, so **load order is part of the architecture**.

## Frontend loading model

### Data-first principle

Data-defining scripts must execute before rendering scripts that consume them.

Typical categories:

1. Core and product data.
2. Command-centre and intelligence data.
3. Political tracker definitions.
4. Generated official-data caches.
5. Base application router/renderers.
6. Feature-specific enhancement modules.

When adding a new generated file, confirm all three conditions:

- the collector writes the file;
- `site/index.html` or a documented loader loads the file;
- the consumer rerenders when the data becomes available.

A generated file existing in GitHub does not mean the live application uses it.

### Routing

The application uses URL hashes for views and selected detail pages. Examples:

- `#home`
- `#today`
- `#news`
- `#cot`
- `#rates`
- `#events`
- `#scenarios`
- `#trackers`
- product-detail routes handled by the application router

New modules must not intercept or overwrite unrelated routes.

## Data domains

## 1. Curated research state

Primary examples:

- `site/data.js`
- `site/command-centre-data.js`
- `site/intelligence-data.js`
- `site/research-data.js`
- `site/products-a.js`
- `site/products-b.js`
- `site/energy-expansion.js`

These objects drive:

- regime and sign-flip interpretation;
- command-centre bias scores;
- news transmission logic;
- trigger zones;
- weekly events;
- product research;
- Scenario Lab explanations.

These are not automatically market truth. They must carry appropriate dates, sources and conditional language.

## 2. Free official market data

The free-data pipeline collects public observations for areas such as:

- CFTC Commitments of Traders;
- Treasury yields and curve spreads;
- real yields and inflation breakevens;
- credit spreads;
- policy rates;
- broad dollar measures.

The collector should output both:

- a browser-ready JavaScript cache; and
- machine-readable JSON or compact diagnostics where useful.

COT market selection must reject misleading alternatives such as micro, mini, financial, index, cross-rate or ultra contracts when the intended primary contract cannot be mapped safely.

Unavailable data must remain unavailable. Do not substitute another benchmark merely to populate a card.

## 3. Political disclosures

Primary collector:

- `scripts/update_political_disclosures.py`

Hardening layer:

- `scripts/update_political_disclosures_strict.py`

Generated outputs:

- `site/political-data.js`
- `site/data/political-disclosures.json`
- `site/data/political-disclosures-summary.json`

Primary sources:

- House Clerk annual indexes and official Periodic Transaction Report PDFs.
- Senate eFD search and official PTR report pages.

### Political import flow

```text
House/Senate source
       │
       ▼
filing discovery
       │
       ▼
PDF/HTML parsing
       │
       ├── normalize dates
       ├── normalize transaction type
       ├── preserve owner
       ├── preserve statutory amount range
       ├── calculate disclosure lag
       └── attach official filing URL
       │
       ▼
stable-ID deduplication
       │
       ▼
merge with previous verified history
       │
       ├── retain history on source failure
       └── expose partial/error status
       │
       ▼
transaction-derived portfolio estimate
       │
       ▼
static JSON + browser JS
```

### Portfolio limitations

Until full annual holdings baselines are incorporated, the portfolio is **PTR-derived only**.

Consequences:

- pre-existing positions may be unknown;
- a partial sale may not reveal the remaining position;
- options may not map cleanly to share exposure;
- value ranges are not current market values;
- a zero reconstruction does not always prove the asset is absent.

The UI must preserve this limitation.

## 4. TradingView integration

TradingView is used as an embedded external layer for:

- interactive charts;
- top stories;
- an economic calendar.

TradingView is not the internal market-data source.

The application must not:

- scrape widget contents;
- read indicator values out of the iframe;
- claim that a paid personal TradingView subscription upgrades website data;
- feed widget data into internal bias calculations.

Scenario analysis belongs to the project’s own research model and user-entered/verified reference prices.

## Scheduled workflows

## Pages deployment

`.github/workflows/deploy-pages.yml`

- triggers when `site/**` changes;
- uploads `site/` as the Pages artifact;
- deploys using GitHub Pages actions;
- uses Pages and OIDC permissions only.

## Political disclosure refresh

`.github/workflows/update-political-disclosures.yml`

- supports manual dispatch;
- runs on a Melbourne-oriented weekday schedule;
- installs parser dependencies;
- compiles collectors;
- runs the strict collector;
- validates JSON and JavaScript;
- commits data or diagnostics;
- verifies Pelosi history is not silently empty;
- rejects malformed asset rows;
- ignores generated-data-only commits to avoid loops.

## Other official-data refreshes

Free official-data workflows should follow the same pattern:

1. collect;
2. validate;
3. preserve prior verified data on temporary failure;
4. write freshness and diagnostics;
5. commit only meaningful changes;
6. allow Pages deployment to publish the result.

## Research operating model

`operating-model.md` defines three altitudes:

- **Daily tactical** — overnight moves, immediate catalysts and dashboard updates.
- **Weekly operational** — synthesis, regime test and week-ahead calendar.
- **Monthly strategic** — deeper structural refresh and draft strategic state.

The monthly process has an approval boundary: it can create drafts, but cannot overwrite approved live dossier, regime or threshold state without explicit approval.

## Failure design

The project prefers visible partial operation over false completeness.

Expected failure behaviour:

- source unavailable → keep previous verified data;
- parser fails for one filing → log the filing ID and retain other history;
- benchmark mapping unsafe → show unavailable;
- generated data empty unexpectedly → fail validation;
- stale source → display stale/partial status;
- TradingView unavailable → internal dashboard remains usable;
- one feature script fails → other views should continue where possible.

## Security model

The current architecture is public and static.

Therefore:

- anything under `site/` is public;
- browser JavaScript cannot safely contain secrets;
- GitHub Actions logs must not reveal credentials;
- future credentialed APIs must use GitHub Secrets and server-side collection;
- login passwords must never be used as scraping credentials;
- official public endpoints are preferred.

## Scaling path

The static architecture is suitable while:

- updates are daily/weekly rather than tick-level;
- datasets remain manageable as compressed JS/JSON;
- no user authentication is required;
- portfolio calculations are disclosure-based rather than per-user accounts.

A backend becomes justified when the project needs:

- large queryable history;
- user accounts and server-side watchlists;
- real-time licensed feeds;
- secret-bearing APIs;
- complex cross-dataset joins;
- reliable incremental ingestion and alerting.

Until then, preserve the low-cost static design and improve modularity, validation and documentation before introducing infrastructure.
