# Crowd Expectations

## Purpose

Crowd Expectations adds a read-only event-probability layer to Market Brief. It is designed to show how prediction-market participants are pricing macro, policy, geopolitical, commodity and technology outcomes.

It is not:

- a betting interface;
- a wallet integration;
- an order router;
- a forecast of truth;
- a standalone trading signal.

## Provider and jurisdiction boundary

The initial provider is Polymarket public market data.

Public market-data endpoints require no API key, wallet or authentication. Australia is listed by Polymarket as close-only for order placement. The Market Brief integration therefore contains no wallet, deposit, signing, authentication or order code.

The dashboard displays source links for research context only.

## Data flow

```text
Polymarket Gamma public markets endpoint
        ↓
scripts/update_crowd_expectations.py
        ├── active-market discovery
        ├── binary YES/NO validation
        ├── sports/entertainment/crypto-price exclusion
        ├── market-relevance classification
        ├── probability-source selection
        ├── transparent quality score
        ├── asset mapping
        ├── one-snapshot-per-day history
        └── stale-data retention
        ↓
site/data/crowd-expectations.json
        ↓
#crowd-expectations
        ├── Command Centre probability shifts
        ├── Asset Workspace event probabilities
        └── Source Health
```

## Selection

The collector scans active, open markets ordered by 24-hour volume. It retains questions mapped to:

- monetary policy and macro;
- trade and industrial policy;
- geopolitics and security;
- energy and commodities;
- technology and AI;
- US policy and elections.

The registry excludes sports, entertainment, celebrity and standalone cryptocurrency-price questions.

The selection vocabulary is versioned in:

```text
scripts/crowd_expectations_registry.json
```

## Probability hierarchy

For the YES outcome:

1. bid-ask midpoint when bid and ask are valid and the spread is no wider than 10 probability points;
2. last traded price;
3. Gamma outcome price.

The UI always states which source was used.

## Quality score

The 0–100 quality score uses visible inputs:

- liquidity;
- 24-hour volume;
- bid-ask spread;
- resolution-source availability;
- description clarity;
- whether the market is active;
- time remaining;
- research relevance.

Grades:

- A: 80–100
- B: 65–79
- C: 50–64
- D: below 50

The default collector keeps markets with a score of at least 45, but Crowd Shock alerts require at least 65.

## Crowd Shock

A Crowd Shock is created when:

- the reported 24-hour probability move is at least five percentage points; and
- quality score is at least 65.

This is an attention flag, not a trade instruction.

## History

The workflow runs every six hours. The generated cache retains one verified snapshot per UTC calendar day for up to 90 days. A later run on the same day replaces that day’s prior snapshot.

## Failure behaviour

- A source failure does not replace populated data with an empty list.
- Previously verified markets are retained and marked stale.
- The source error remains visible.
- A successful empty result is rejected.
- Market IDs and daily history dates must be unique.
- Generated data must remain read-only.

## Workflow

```text
.github/workflows/update-crowd-expectations.yml
```

It runs:

- every six hours;
- manually;
- after collector, registry, schema, test or workflow changes.

The workflow validates the collector, generated JSON and browser modules before committing a refresh.

## Validation

```bash
python -m py_compile scripts/update_crowd_expectations.py scripts/validate_crowd_expectations.py
python -m unittest tests/test_crowd_expectations.py -v
python scripts/validate_crowd_expectations.py
node --check site/features/crowd-expectations/crowd-data.js
node --check site/features/crowd-expectations/crowd-health.js
node --check site/features/crowd-expectations/crowd-page.js
node --check site/features/crowd-expectations/crowd-command.js
node --check site/features/crowd-expectations/crowd-asset.js
```

## Future provider comparison

A second provider such as Kalshi may be added later. Probabilities must not be averaged unless the contract wording, cutoff date, resolution source and event definition are materially equivalent.
