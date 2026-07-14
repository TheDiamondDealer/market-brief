# Data Sources and Trust Model

## Purpose

This document identifies the source classes used by Market Brief and the rules for accepting, displaying and interpreting them.

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

## CFTC Commitments of Traders

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

## FRED and official rate sources

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

## Political disclosures

## House Clerk

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

## Senate eFD

Used for:

- Senate PTR discovery;
- official Senate report pages;
- the same normalized transaction fields as House records.

The statutory terms page must be accepted programmatically before search access.

## Political data rules

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
- current, delayed, partial, stale or unavailable status.

A page should not use one generic updated timestamp to conceal mixed-frequency inputs.

## Missing data

When data is missing:

- show unavailable or pending;
- preserve the last verified value with a stale label when appropriate;
- explain the failed source or parser;
- do not estimate unless the methodology is explicit and the estimate is labelled;
- never use a superficially similar dataset to avoid an empty state.
