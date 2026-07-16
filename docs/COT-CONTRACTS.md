# COT contract identity registry

## Purpose

BR-06 replaces similar-name and open-interest ranking with a versioned exact-contract registry at `scripts/cot_contracts.json`.

A COT row is accepted only when all of these fields agree with a verified registry entry:

- CFTC report family and dataset;
- six-character CFTC contract-market code, including official alphanumeric codes;
- complete official market-and-exchange name;
- expected exchange;
- approved positioning category;
- contract-specific freshness limit.

Matching the name alone is not sufficient. Matching the code alone is not sufficient. The collector does not select the largest open-interest candidate from a group of similar names.

## Verified and unavailable states

`status: verified` entries contain the approved code and exact accepted names. Generated COT rows include a `contract` object that records the registry version, code, report type, category, exchange and exact market name.

`status: unavailable` entries deliberately contain no contract code and no accepted names. They document why a benchmark cannot be populated safely. The collector does not query or emit them.

At BR-06 completion:

- WTI remains unavailable. The historical NYMEX Light Sweet identity stops in 2022 in the current Disaggregated Futures-Only dataset; current ICE WTI and NYMEX WTI Financial rows are not substituted.
- US Henry Hub natural gas remains unavailable. The historical standard NYMEX Natural Gas identity stops in 2022; current Last Day Financial, basis, index, penultimate and different contract-size rows are not substituted.
- NYMEX Brent Last Day is not treated as the ICE Brent benchmark.
- UK NBP remains unavailable until an exact official contract is approved.
- CFTC code `043602` is approved for the CBOT 10-year note. The current official name `UST 10Y NOTE - CHICAGO BOARD OF TRADE` and its historical official name are accepted; Ultra UST 10Y is rejected.

The July 2026 reference expansion records 46 requested products in `referenceProductIds`. Forty-five have current exact identities across the Disaggregated Futures-Only and Traders in Financial Futures Futures-Only datasets. This includes explicitly named derivative products such as NYMEX Brent Last Day, ICE WTI, NYMEX WTI Financial, Micro E-mini indices and Ultra Treasury contracts. They are distinct products, not replacements for the unavailable intended WTI, ICE Brent, Henry Hub or UK NBP benchmark entries.

Oats is the one unavailable reference product. Its exact CBOT series, historical code `004603`, last published on 2 June 2026. It remains visible in coverage diagnostics but is not graphed as current.

## Source and fixtures

The registry uses the CFTC Public Reporting Environment datasets:

- Disaggregated Futures-Only: `72hh-3qpy`.
- Traders in Financial Futures Futures-Only: `gpe5-46if`.

Current official identities were captured through a branch-only GitHub Actions diagnostic against those datasets. The temporary diagnostic workflow is not part of the production branch. Reduced official-response fixtures are committed under `tests/fixtures/cftc/`; they retain the identity, position, open-interest and contract-unit fields required to distinguish the intended Treasury contract from Ultra Treasury and to prove why current energy alternatives are unsafe.

## Failure and retention behaviour

- Exact current row available: publish it with verified identity metadata.
- Exact row stale: exclude it and report the stale contract code/date.
- Only a similar contract available: leave the market unavailable; do not promote a candidate by name, exchange or open interest.
- Total CFTC failure: retain only previous rows that already carry a registry-verified identity. Pre-BR-06 unverified rows are not retained as fallback.
- Partially successful run: publish current verified markets, retain previously verified rows for failed contracts with `dataState: stale-retained`, and expose the errors. A failed contract with no verified retained row appears in `cotContractRegistry.missing`.

## Validation

The registry has its own JSON Schema. `scripts/validate_generated_data.py` validates both the registry and generated datasets. Once generated output carries the `cotContractRegistry` marker, every emitted COT row must have an exact verified `contract` identity and unavailable IDs are forbidden.

The scheduled free-market-data workflow runs the chart collector, which installs the exact API selector before adding 52-week history. It then validates generated JSON and browser JavaScript before any commit or Pages deployment.
