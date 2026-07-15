# Data Sources and Trust Model

## Purpose

This document identifies the source classes used by Market Brief and the rules for accepting, displaying and interpreting them.

For the dated operational state of each source, see `docs/PROJECT-STATUS.md` and the generated Source Health data.

## Trust hierarchy

Use sources in this order:

1. Government, regulator, central bank, exchange or company primary release.
2. Original filing, dataset, policy document or company report.
3. High-quality financial wire or publication.
4. Specialist industry publication.
5. Third-party aggregator or parser.
6. Social media as an unverified discovery lead only.

A lower-tier source can help find an item, but should not overwrite a conflicting primary record.

## Official market data

### CFTC Commitments of Traders

Used for:

- managed-money positioning in commodities;
- leveraged-fund positioning in selected financial futures;
- long, short and net contracts;
- weekly and four-week changes;
- historical percentiles;
- 52-week positioning charts.

Rules:

- select the intended primary contract;
- reject micro, mini, ultra, index, financial and cross-rate variants when inappropriate;
- do not substitute a stale or similarly named contract;
- preserve report date and category;
- COT is weekly and delayed by design.

### FRED and official rate sources

Used for:

- Treasury yields;
- real yields;
- breakevens;
- high-yield spreads;
- effective federal funds rate;
- SOFR;
- trade-weighted US dollar;
- curve-spread calculations.

Rules:

- preserve each series’ own latest observation date;
- weekends and holidays create expected gaps;
- do not mark all rates current because one series updated;
- distinguish basis-point changes from index-point changes.

## Free official agency feeds

The repository includes independent collectors for SEC, BLS, EIA, BEA, Census and USGS.

### SEC EDGAR

Intended use:

- priority company filings;
- filing and acceptance dates;
- official accession and archive links;
- forms such as 8-K, 10-Q, 10-K, 6-K, 20-F, Form 4, offering documents and beneficial-ownership filings.

Rules:

- use pinned CIK identities;
- require the official submissions payload to confirm the expected ticker;
- reject identity mismatches;
- retain official accession and archive URLs;
- do not replace blocked official access with an unverified third-party filing parser.

Current known limitation: GitHub-hosted runners have received HTTP 403 from the official SEC submissions endpoints. This is a visible failed state, not permission to fabricate or substitute records.

### BLS

Used for configured labour and inflation series such as:

- CPI and core CPI;
- PPI;
- payrolls;
- unemployment and participation;
- average hourly earnings;
- job openings.

Rules:

- exclude annual-average period `M13` when a monthly observation is required;
- keep advisory messages separate from completeness status;
- complete configured observations remain current even when optional catalogue metadata is unavailable;
- never label `0 missing` as partial solely because of a benign API advisory.

### EIA

Intended use:

- crude and Cushing inventories;
- refined-product inventories;
- refinery runs and utilisation;
- production, imports and exports;
- natural-gas storage and production;
- LNG and power-sector fundamentals;
- uranium data where appropriate.

Rules:

- use exact configured series identities;
- verify returned descriptions against expected terms;
- store `EIA_API_KEY` only in GitHub Actions Secrets;
- missing key means unavailable, not failed;
- do not substitute a different region, benchmark or product.

### BEA

Intended use:

- GDP;
- income and spending;
- PCE prices;
- corporate profits;
- relevant NIPA table lines.

Rules:

- use official table names and line descriptions;
- reject unmatched tables rather than selecting arbitrary numeric rows;
- store `BEA_API_KEY` only in GitHub Actions Secrets;
- missing key means unavailable.

### Census

Intended use:

- trade;
- retail sales;
- manufacturing;
- inventories;
- housing and construction indicators.

Rules:

- preserve official data-type and category codes until a verified dictionary join exists;
- do not guess human-readable meanings for coded series;
- store `CENSUS_API_KEY` only in GitHub Actions Secrets;
- missing key means unavailable.

### USGS

Used for:

- official annual Mineral Commodity Summaries release detection;
- source document and edition identification;
- critical-mineral structural context.

Rules:

- do not OCR or estimate individual mineral values from PDF tables merely to populate the dashboard;
- label annual data with its own observation year and cadence;
- use a structured official join before publishing individual mineral statistics.

## Licensed private market data

### Twelve Data

The repository contains a server-side collector and disabled generated cache for a private internal equity watchlist.

The provider is not a public dashboard feed under the current architecture.

Rules:

- keep the pipeline disabled while the repository or deployed cache is public;
- never expose the API key to browser JavaScript;
- never commit licensed prices to a publicly accessible site;
- require a protected deployment and verified internal-use rights before activation;
- distinguish fresh quotes, fresh history and retained stale rows;
- advance `lastSuccessfulAt` only after a fresh accepted provider response;
- retain last verified rows as stale on temporary failure;
- do not mark retained history as proof of a current quote.

The disabled cache must contain no prices.

## Crowd Expectations

### Polymarket public market data

Used for read-only context on market-implied probabilities for relevant:

- monetary policy and macro;
- trade and industrial policy;
- geopolitics and security;
- energy and commodities;
- technology and AI;
- US policy and elections.

It is not:

- a wallet integration;
- an authentication flow;
- a deposit interface;
- an order router;
- a forecast of truth;
- a standalone trading signal.

Rules:

- accept binary YES/NO markets only;
- exclude sports, entertainment, celebrity and standalone cryptocurrency-price questions;
- calculate spread from best ask minus best bid;
- prefer midpoint only when the calculated book is valid and sufficiently narrow;
- fall back to last trade and then the provider outcome price;
- extract resolution sources from direct fields, event metadata and market rules;
- cap quality below Grade A when no identifiable resolution source exists;
- map assets from event wording rather than broad category defaults;
- apply category and event-family balancing only after original quality, volume and liquidity filters;
- retain one verified snapshot per UTC day for up to 90 days;
- preserve previous verified markets as stale on source failure;
- structurally reject secret-bearing fields or order endpoints;
- do not add wallet, signing, deposit or order code.

A probability is market-implied context, not a recommendation or factual prediction.

## Political disclosures

### House Clerk

Used for:

- Periodic Transaction Report discovery;
- official PTR PDFs;
- filing date;
- owner;
- asset;
- transaction type;
- trade date;
- statutory amount range.

The collector uses annual House disclosure indexes and official report PDFs.

### Senate eFD

Used for:

- Senate PTR discovery;
- official Senate report pages;
- the same normalized transaction fields as House records.

The statutory terms page must be accepted programmatically before search access.

### Political data rules

- official filing URL is retained for each transaction;
- actual trade date and public filing date remain separate;
- disclosure lag is calculated, not inferred;
- verified history is retained through temporary source failures;
- spouse/member/joint/dependent attribution is preserved;
- value ranges remain ranges;
- annual holdings baselines are required before a portfolio can claim broader completeness;
- current portfolios are labelled as transaction-derived estimates where appropriate.

## Curated research and interpretation

Examples:

- regime classification;
- risk gauge;
- asset bias scores;
- causal transmission chains;
- target-path scenarios;
- trigger conditions;
- news impact explanations.

These are project interpretations, not official source observations.

Every interpretation should be auditable through:

- dated inputs;
- visible component scores where used;
- driver;
- contradiction;
- confirmation;
- invalidation;
- source links for the underlying facts.

Research output must also follow `docs/RESEARCH-GOVERNANCE.md`.

## News

The internal news feed is a delayed, curated research product.

Preferred evidence:

- official announcement or original document;
- reputable wire/publication confirmation;
- direct company/regulator source where relevant.

Policy events should distinguish:

- threatened;
- proposed;
- announced;
- enacted;
- effective;
- exempted;
- delayed;
- reversed;
- retaliated against;
- de-escalated.

Do not treat a proposal as implementation.

## TradingView

TradingView is an external embedded display/discovery layer.

Used for:

- interactive charts;
- top stories;
- economic calendar context.

Not used for:

- internal price extraction;
- programmatic indicator values;
- internal news ingestion;
- bias-engine calculations;
- generated static market data.

The widget remains inside its iframe. The project must not scrape it or imply that its data has been imported.

## Third-party political tools

Examples such as Quiver may assist:

- discovering a filing;
- comparing parser results;
- identifying possible missing records;
- product-design inspiration.

They do not outrank official House or Senate records.

Do not use personal login credentials to scrape authenticated pages.

## Physical commodity evidence

Each commodity should use market-specific evidence rather than price alone.

### Oil

Keep separate:

- Brent global/seaborne balance;
- WTI US/Cushing balance;
- Brent-WTI spread;
- time spreads;
- inventories;
- refinery runs;
- product cracks;
- tanker/export flows;
- OPEC+ production and compliance.

### Natural gas

Keep separate:

- US Henry Hub;
- UK NBP;
- European TTF as a comparison, not a UK substitute;
- storage;
- production;
- LNG feedgas/arrivals;
- pipeline and interconnector flows;
- weather;
- gas-fired power demand.

### Gold and silver

Consider:

- real yields;
- nominal yields;
- dollar;
- ETF flows;
- central-bank demand;
- physical premiums;
- COT positioning;
- option/futures structure where available.

### Copper

Consider:

- LME/COMEX/Shanghai inventories;
- treatment charges;
- regional premiums;
- Chinese demand indicators;
- mine disruptions;
- scrap supply;
- COT positioning.

### Rare earths

Consider:

- individual oxide/metal prices;
- Chinese quotas and export controls;
- ex-China premiums;
- magnet demand;
- project construction and commissioning milestones;
- defence/industrial policy;
- company funding and permitting.

## Freshness labels

Where practical, expose:

- source;
- observation/report date;
- generated date;
- expected update cadence;
- current, delayed, partial, stale, failed or unavailable status.

A page should not use one generic updated timestamp to conceal mixed-frequency inputs.

## Missing data

When data is missing:

- show unavailable or pending;
- preserve the last verified value with a stale label when appropriate;
- explain the failed source or parser;
- do not estimate unless the methodology is explicit and the estimate is labelled;
- never use a superficially similar dataset to avoid an empty state.
