# Market Brief Data Sources and Trust Model

Last reviewed: 14 July 2026

This document lists sources that are actually connected to the static site. Planned providers are not described as live.

## Trust hierarchy

Use sources in this order:

1. Government, regulator, central bank, exchange or company primary release.
2. Original filing, dataset, policy document or company report.
3. High-quality financial wire or publication.
4. Specialist industry publication.
5. Third-party aggregator or parser.
6. Social media as an unverified discovery lead only.

A lower-tier source can help locate evidence but cannot overwrite a conflicting primary record.

## Connected source classes

| Product surface | Connected source | Mode | Important boundary |
| --- | --- | --- | --- |
| COT Positioning | CFTC Public Reporting Environment datasets `72hh-3qpy` and `gpe5-46if` | Official weekly cache | Only exact registry-approved code, name, exchange, report family and category are emitted. |
| Macro Monitor | Federal Reserve Economic Data public series | Official delayed observations | Every series keeps its own observation date; cache recency does not override it. |
| Political Flow — House | US House Clerk Financial Disclosure portal | Official filing discovery and PDF parsing | Public disclosure is delayed and range-based; disclosed owner/account is preserved. |
| Political Flow — Senate | US Senate electronic Financial Disclosure portal | Official filing discovery and HTML parsing | Failed and partial filings remain visible and retryable. |
| Impact Feed | Repository-maintained curated research records | Delayed editorial interpretation | This is not a live news wire; unknown decision fields remain unknown. |
| Calendar & Reactions | Repository-maintained event research using named official release agencies | Research workflow | Consensus stays `Not sourced` until an approved provider is connected. |
| Asset charts | Embedded TradingView widgets | Display-only external widget | Chart data remains with TradingView and is not copied into internal datasets. |
| Physical and macro checklists | Repository-maintained research records with source and cadence labels | Research workflow | A checklist is not called automated unless a pipeline exists. |

## Exact COT registry

The source of truth is `scripts/cot_contracts.json`.

Verified contracts:

- Gold — `088691`, Managed Money, Disaggregated Futures Only.
- Silver — `084691`, Managed Money, Disaggregated Futures Only.
- Copper — `085692`, Managed Money, Disaggregated Futures Only.
- Japanese yen — `097741`, Leveraged Funds, Traders in Financial Futures.
- US 10-year Treasury note — `043602`, Leveraged Funds, Traders in Financial Futures.
- US Dollar Index — `098662`, Leveraged Funds, Traders in Financial Futures.

Explicitly unavailable and never substituted:

- WTI crude oil.
- Brent crude oil.
- US Henry Hub natural gas.
- UK NBP natural gas.

Each unavailable reason is stored in the registry and exposed in the interface.

## Official macro series currently connected

- `DFF` — Effective Federal Funds Rate.
- `SOFR` — Secured Overnight Financing Rate.
- `DGS2`, `DGS5`, `DGS10`, `DGS30` — nominal Treasury yields.
- `DFII10` — 10-year real Treasury yield.
- `T10YIE` — 10-year breakeven inflation rate.
- `BAMLH0A0HYM2` — US high-yield option-adjusted spread.
- `DTWEXBGS` — broad trade-weighted US dollar index.

Employment and growth panels remain unavailable until approved automated series are added.

## Political disclosure rules

- Official filing URL is retained for each transaction.
- Actual trade date and public filing date remain separate.
- Disclosure lag is calculated, not inferred.
- Spouse, member, joint and dependent attribution is preserved.
- Statutory value ranges remain ranges.
- Verified history survives temporary source failures.
- The filing ledger records parser version, content hash, attempts, error and retry state.
- Portfolio reconstruction is labelled as transaction-derived and cannot claim brokerage-account completeness.

## Generated-file ownership

Generated files must not be edited by hand.

| Generated output | Owning generator/workflow |
| --- | --- |
| `site/free-data.js` | `scripts/update_free_data_charts.py` through `update-free-market-data.yml` |
| `site/data/free-market-data.json` | `scripts/update_free_data_charts.py` through `update-free-market-data.yml` |
| `site/political-data.js` | `scripts/update_political_disclosures_ledger.py` through `update-political-disclosures.yml` |
| `site/data/political-disclosures.json` | `scripts/update_political_disclosures_ledger.py` |
| `site/data/political-disclosures-summary.json` | `scripts/update_political_disclosures_ledger.py` |
| `site/data/political/filing-ledger.json` | `scripts/political_filing_ledger.py` through the ledger-backed collector |
| `site/data/political/manifest.json` | `scripts/build_political_data_split.py` |
| `site/data/political/summary.json` | `scripts/build_political_data_split.py` |
| `site/data/political/<politician>/<year>.json` | `scripts/build_political_data_split.py` |
| `site/data/political/indexes/*.json` | `scripts/build_political_data_split.py` |

## Freshness vocabulary

`site/core/freshness.js` standardises:

- `current` — inside the expected cadence window.
- `delayed` — outside the normal window but potentially usable.
- `stale` — materially older than expected.
- `partial` — some records succeeded while others require retry.
- `failed` — the latest run reported an error.
- `unavailable` — no approved source or verified mapping is connected.
- `unknown` — the timestamp cannot be interpreted safely.

Each source-health record stores source observation time, collection time, generation time, expected cadence and last successful run separately.

## Research interpretation rules

A research interpretation must expose, when applicable:

- affected asset;
- direction and magnitude;
- horizon and confidence;
- causal mechanism;
- confirmation;
- invalidation;
- source and event timestamp.

No hidden composite risk score is used by the remodelled Command Centre. The retired renderer remains only as a compatibility shim.

## Sources not connected

The mandatory remodel does not claim access to:

- a licensed live news wire;
- live or exchange-delayed price redistribution;
- an approved consensus forecast feed;
- interest-rate probability data;
- earnings-estimate data;
- capital-flow data;
- authenticated user accounts, watchlists or alerts.

Those items belong to optional BR-20 and require explicit approval, licensing and architecture decisions.
