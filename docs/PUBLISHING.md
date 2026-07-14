# Generated-data publishing

## Purpose

This document describes the BR-02 collector-to-Pages publishing contract.

Generated-data commits made with the repository `GITHUB_TOKEN` do not rely on a second push-triggered workflow to publish the site. Each successful collector workflow explicitly calls the reusable Pages workflow and requests deployment of current `main`.

## Successful collector path

```text
latest main checkout
        │
        ▼
collector runs
        │
        ▼
syntax + schema + semantic validation
        │
        ├── failure → stop; no commit; no deployment
        │
        ▼
commit generated files when changed
        │
        ▼
rebase onto latest main
        │
        ▼
validation runs again
        │
        ├── failure/conflict → stop; no push; no deployment
        │
        ▼
push validated commit to main
        │
        ▼
call reusable Pages workflow
        │
        ▼
Pages workflow checks out current main and deploys site/
```

A successful collector run also deploys when there is no generated-data change. This deliberately republishes current `main` and makes manual collector runs a reliable recovery mechanism for a stale Pages deployment.

## Workflows

- `.github/workflows/update-free-market-data.yml`
- `.github/workflows/update-political-disclosures.yml`
- `.github/workflows/deploy-pages.yml`

The two collector workflows use the shared `generated-data-writer` concurrency group so their commits cannot race each other.

The reusable deployment workflow uses the `pages` concurrency group and deploys the requested ref. Collector callers always pass `main`.

## Validation boundary

Before a collector can commit, it must pass:

- Python compilation for the relevant collectors and validators;
- JSON schema validation;
- semantic generated-data validation;
- browser JavaScript syntax checks;
- collector-specific output inspection.

After rebasing onto current `main`, schema/semantic and browser JavaScript validation run again before push.

Political validation includes retained non-empty history, Pelosi-history retention, malformed-row rejection, unique transaction IDs and summary/count consistency.

Free-market validation includes unique rate/COT IDs and COT long-minus-short arithmetic.

## Failure behaviour

- Collector failure: no commit and no deployment.
- Schema or semantic failure: no commit and no deployment.
- Rebase conflict: no push and no deployment.
- Post-rebase validation failure: no push and no deployment.
- Pages failure after a successful collector: generated data remains committed, but the collector workflow is marked failed because deployment did not complete.

## Manual recovery

Run either collector with `workflow_dispatch`. A successful run deploys current `main`, even when the collector finds no data changes.

The Pages workflow can also be dispatched directly with `ref=main` when collection should not run.

## Independent verification

A workflow success is not sufficient proof that the live site changed. Verify at least one relevant live artifact:

- `site/data/free-market-data.json` equivalent on the Pages URL for market-data timestamps;
- `site/data/political-disclosures-summary.json` equivalent for political counts and timestamps;
- the affected live hash route in a private window.

Record the deployed commit SHA from the Pages workflow log when diagnosing cache or stale-deployment issues.
