# Architecture

## Purpose

Market Brief is a static research-led market-intelligence application backed by scheduled collectors and curated research state. It provides an auditable workspace for macro, commodities, positioning, political disclosures and event probabilities without requiring an always-on application server.

The dated implementation and blocker state is maintained in `docs/PROJECT-STATUS.md`.

## Core layers

The system has four distinct layers:

1. **Source collection** — official datasets, filings, public market data and research inputs.
2. **Normalization and validation** — Python collectors, schemas, semantic tests and retained-history rules.
3. **Interpretation** — curated JavaScript research objects for regime, news impact, triggers, scenarios and dossiers.
4. **Static presentation** — browser-rendered dashboard deployed from `site/`.

## High-level data flow

```text
Official/public sources                   Research process
(CFTC, FRED, agencies,                    (daily / weekly / monthly)
House, Senate, Polymarket)                         │
          │                                         │
          ▼                                         ▼
   Python collectors                         curated research state
          │                                         │
          ├── identity checks                       ├── regime
          ├── validation                            ├── news interpretation
          ├── deduplication                         ├── triggers
          ├── freshness/status                      ├── scenarios
          └── retained history                      └── product dossiers
          │                                         │
          └─────────────────┬───────────────────────┘
                            ▼
                    static JS / JSON caches
                            │
                            ▼
                     feature loader/router
                            │
                            ▼
                      `site/index.html`
                            │
                            ▼
                    GitHub Pages artifact
```

A separate dormant path exists for licensed private data:

```text
Twelve Data API
      │
      ▼
GitHub Actions collector
      │
      ├── only after private-access verification
      ├── secret never sent to browser
      ├── fresh/stale distinction
      └── internal-use licence boundary
      │
      ▼
protected static cache
      │
      ▼
Cloudflare Access protected deployment
```

That path is intentionally disabled in the current public repository and public deployment.

## Runtime model

The public frontend is deliberately simple:

- no Node package installation at runtime;
- no bundler;
- no application server;
- no runtime database;
- no browser-side secret;
- no user account system;
- no runtime API proxy.

The browser receives static HTML, CSS, JavaScript and generated JSON.

JavaScript modules share browser globals and a small core/feature-loader contract. Script and feature order remain part of the architecture.

## Frontend loading model

### Data-first principle

Data-defining modules must become available before rendering modules consume them.

Typical order:

1. core and product data;
2. command-centre and intelligence data;
3. generated official-data caches or asynchronous data loaders;
4. base application router and shared renderers;
5. feature manifest modules;
6. feature-specific page, command, asset and Source Health extensions.

When adding a generated source, confirm:

- collector writes the file;
- schema validates it;
- browser loader requests or loads it;
- consumer rerenders when data arrives;
- Source Health receives exactly one stable record set;
- deployment includes the generated path.

A generated file existing in Git does not prove the live application uses it.

### Shared core

`window.MarketBriefCore` provides shared contracts such as:

- routing;
- state/store access;
- formatting and escaping;
- source freshness normalization;
- feature registration.

Feature extensions must remain idempotent. An extension that listens for a shared event and then redispatches it must prove that it returns without writing when its expected records already exist.

### Routing

The application uses URL hashes.

Important routes include:

- `#home`
- `#today`
- `#news`
- `#cot`
- `#rates`
- `#official-feeds`
- `#crowd-expectations`
- `#events`
- `#week`
- `#regime`
- `#triggers`
- `#assets`
- `#products`
- `#scenarios`
- `#trackers`
- `#archive`
- asset and product-detail hashes.

New modules must not intercept or overwrite unrelated routes.

## Data domains

## 1. Curated research state

Primary examples include:

- `site/data.js`
- `site/command-centre-data.js`
- `site/intelligence-data.js`
- `site/research-data.js`
- `site/products-*.js`
- other curated product and expansion modules.

These drive:

- regime and sign-flip interpretation;
- command-centre priorities;
- news transmission logic;
- trigger zones;
- weekly events;
- product research;
- scenario explanations.

They are interpretations rather than automatic market truth. They must follow `docs/RESEARCH-GOVERNANCE.md` and carry dates, sources, uncertainty and conditional language.

## 2. CFTC and FRED official market data

The free-data pipeline collects:

- CFTC Commitments of Traders;
- Treasury yields and curve spreads;
- real yields and breakevens;
- credit spreads;
- policy rates;
- broad dollar measures.

COT contract selection must reject misleading alternatives such as micro, mini, ultra, index, financial or cross-rate contracts when the intended primary contract cannot be mapped safely.

Unavailable data stays unavailable.

## 3. Free official agency feeds

Primary collector family:

- `scripts/update_official_feeds.py`
- `scripts/update_official_feeds_resilient.py`
- `scripts/validate_official_feeds.py`
- `scripts/official_feeds_registry.json`

Generated output:

- `site/data/official-feeds.json`
- browser data and Source Health modules under `site/features/official-feeds/`.

Agencies:

- SEC EDGAR;
- BLS;
- EIA;
- BEA;
- Census;
- USGS.

Each agency is independent.

Expected behaviour:

- one agency failure does not block successful agencies;
- missing keys become unavailable;
- previous verified records become stale on temporary failure;
- identity mismatches are rejected;
- source observation and collection times remain separate;
- generated output validates before commit;
- BLS completeness is not downgraded by benign advisory metadata.

Current exact operational state belongs in `docs/PROJECT-STATUS.md` and the generated cache.

## 4. Political disclosures

Primary collector:

- `scripts/update_political_disclosures.py`

Hardening layer:

- `scripts/update_political_disclosures_strict.py`

Generated outputs:

- `site/political-data.js`
- `site/data/political-disclosures.json`
- `site/data/political-disclosures-summary.json`

Primary sources:

- House Clerk annual indexes and official PTR PDFs;
- Senate eFD search and official PTR pages.

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

Until complete annual holdings baselines are incorporated, the portfolio is PTR-derived.

Consequences:

- pre-existing positions may be unknown;
- partial sales may not reveal the remaining position;
- options may not map cleanly to share exposure;
- statutory ranges are not current market values;
- zero reconstruction does not always prove absence.

The UI must preserve these limitations.

## 5. Crowd Expectations

Collector family:

- `scripts/update_crowd_expectations.py`
- `scripts/update_crowd_expectations_hardened.py`
- `scripts/validate_crowd_expectations.py`
- `scripts/crowd_expectations_registry.json`

Generated output:

- `site/data/crowd-expectations.json`
- feature modules under `site/features/crowd-expectations/`.

The provider path is public read-only market data.

Architecture guarantees:

- no wallet or user authentication;
- no signing or deposits;
- no order endpoint;
- binary market validation;
- relevance and exclusion vocabulary;
- computed bid/ask spread;
- resolution-source extraction;
- transparent quality score;
- event-specific asset mapping;
- category and event-family balancing after qualification;
- daily retained history;
- stale fallback;
- structural validation of controlled URLs and fields.

Crowd probabilities are context rather than forecasts or recommendations.

## 6. Dormant private market data

Collector family includes Twelve Data watchlist and pipeline modules under `scripts/`, with generated disabled caches under `site/`.

The public architecture must expose only a disabled state with no prices.

The collector is gated by:

- repository privacy;
- protected deployment;
- explicit access confirmation;
- explicit collection enablement;
- server-side secret;
- provider-use rights.

A private repository alone does not protect a public deployment. Both the custom origin and generated Cloudflare origin must be protected before activation, and the public GitHub Pages origin must be retired.

Freshness rules distinguish:

- fresh quote;
- fresh daily history;
- retained stale row;
- failed empty run.

Retained history must not make a failed quote current.

## 7. TradingView integration

TradingView is an external layer for:

- interactive charts;
- top stories;
- economic calendar context.

It is not an internal feed.

The application must not:

- scrape widget contents;
- read indicator values from the iframe;
- claim a personal subscription upgrades website data;
- feed widget values into internal bias calculations.

Scenario analysis belongs to the project’s own research model and verified/user-entered references.

## Source Health architecture

Source Health merges base records with feature-specific extensions.

Each record should preserve:

- stable ID;
- source family;
- observed date;
- collection/generated date;
- expected cadence;
- last successful date;
- normalized status;
- detail;
- error;
- source URL.

Extensions must:

1. remove only their own family from the base set;
2. construct the expected records;
3. compare existing and expected records;
4. return without writing when equal;
5. dispatch a shared update only after a genuine change.

This prevents event recursion and duplicate source records.

## Schemas and validation

Generated datasets are protected by:

- JSON schemas;
- semantic validators;
- source-specific validators;
- unit tests;
- workflow tests;
- route and frontend contract tests;
- static accessibility and payload audit.

The primary CI workflow is `.github/workflows/validate.yml`.

It runs:

- immutable action-pin validation;
- Python compilation;
- recursive JavaScript syntax checks;
- generated schema and semantic validation;
- Crowd Expectations validation;
- static-site audit;
- complete offline unit-test discovery.

## Scheduled workflows

### Pages deployment

`.github/workflows/deploy-pages.yml`

- uploads `site/` as the Pages artifact;
- deploys using GitHub Pages actions;
- uses Pages and OIDC permissions;
- does not make documentation-only changes visible on the dashboard unless `site/` also changes.

### Generated-data writers

Generated-data workflows share a serialization strategy so concurrent collectors do not race to push generated commits.

Expected sequence:

1. checkout latest `main`;
2. validate pinned dependencies;
3. compile and test collector;
4. collect;
5. validate generated output;
6. inspect and print source counts;
7. commit only changed generated paths;
8. pull/rebase latest `main`;
9. revalidate;
10. push;
11. trigger or call deployment.

Scheduled jobs must be safe to rerun and must not trigger infinite generated-data loops.

## Research operating model

`operating-model.md` defines:

- daily tactical research;
- weekly operational synthesis;
- monthly strategic refresh.

Monthly work can create drafts but cannot overwrite approved dossier, regime or threshold state without explicit approval naming the month.

## Failure design

The project prefers visible partial operation over false completeness.

Expected failure behaviour:

- source unavailable → preserve last verified data where appropriate;
- missing key → unavailable;
- parser fails for one item → retain other valid history and report the item;
- unsafe benchmark mapping → unavailable;
- unexpectedly empty successful dataset → fail validation;
- stale source → stale or partial status;
- provider runner block → failed with diagnostic;
- TradingView unavailable → internal research remains usable;
- one feature fails → unrelated routes continue where possible;
- private-access condition not met → licensed feed remains disabled with no prices.

## Security model

The current deployed architecture is public and static.

Therefore:

- anything under `site/` is public;
- browser JavaScript cannot safely contain secrets;
- Actions logs must not reveal credentials;
- credentialed collectors use GitHub Secrets;
- licensed/private datasets require a protected deployment before collection;
- website passwords or authenticated personal accounts must never be used as scraping credentials;
- official public endpoints are preferred.

## Scaling path

The static design remains suitable while:

- updates are periodic rather than tick-level;
- datasets remain manageable as static JSON/JavaScript;
- no user authentication is required;
- no private licensed data is publicly deployed;
- no large queryable history or per-user alerts are required.

A backend becomes justified when the project needs:

- private user accounts;
- server-side watchlists and alerts;
- large incremental history;
- licensed real-time or delayed feeds;
- complex cross-dataset joins;
- secret-bearing runtime APIs;
- reliable notification infrastructure.

Until those requirements are approved, preserve the low-cost static design and improve validation, modularity, browser coverage and documentation first.
