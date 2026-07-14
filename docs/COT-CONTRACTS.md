# COT contract identity registry

## Purpose

BR-06 replaces similar-name and open-interest ranking with a versioned exact-contract registry at `scripts/cot_contracts.json`.

A COT row is accepted only when all of these fields agree with a verified registry entry:

- CFTC report family and dataset;
- six-digit CFTC contract-market code;
- complete official market-and-exchange name;
- expected exchange;
- approved positioning category;
- contract-specific freshness limit.

Matching the name alone is not sufficient. Matching the code alone is not sufficient. The collector does not select the largest open-interest candidate from a group of similar names.

## Verified and unavailable states

`status: verified` entries contain the approved code and exact accepted names. Generated COT rows include a `contract` object that records the registry version, code, report type, category, exchange and exact market name.

`status: unavailable` entries deliberately contain no contract code and no accepted names. They document why a benchmark cannot be populated safely. The collector does not query or emit them.

At BR-06 completion:

- NYMEX Light Sweet Crude Oil is the approved WTI contract.
- NYMEX Natural Gas is the approved US Henry Hub contract.
- ICE Futures Europe WTI and Henry Hub Last Day Financial are rejected substitutes.
- NYMEX Brent Last Day is not treated as the ICE Brent benchmark.
- UK NBP remains unavailable until an exact official contract is approved.
- CBOT 10-Year U.S. Treasury Notes is approved; Ultra 10-Year is rejected.

## Source and fixtures

The registry uses the CFTC Public Reporting Environment datasets:

- Disaggregated Futures-Only: `72hh-3qpy`.
- Traders in Financial Futures Futures-Only: `gpe5-46if`.

Reduced official-response identity fixtures are committed under `tests/fixtures/cftc/`. They retain the fields used by the selector and are tested offline. Tests also mutate those fixtures to prove that a wrong code, wrong exchange name, financial variant or ultra Treasury variant is rejected.

## Failure and retention behaviour

- Exact current row available: publish it with verified identity metadata.
- Exact row stale: exclude it and report the stale contract code/date.
- Only a similar contract available: leave the market unavailable and report the returned identities.
- Total CFTC failure: retain only previous rows that already carry a registry-verified identity. Pre-BR-06 unverified rows are not retained as fallback.
- Partially successful run: publish the verified markets and expose errors for failed verified entries.

## Validation

The registry has its own JSON Schema. `scripts/validate_generated_data.py` validates both the registry and generated datasets. Once generated output carries the `cotContractRegistry` marker, every emitted COT row must have an exact verified `contract` identity and unavailable IDs are forbidden.

The scheduled free-market-data workflow runs the chart collector, which installs the exact API selector before adding 52-week history. It then validates generated JSON and browser JavaScript before any commit or Pages deployment.
