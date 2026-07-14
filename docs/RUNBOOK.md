# Market Brief Operations Runbook

Last reviewed: 14 July 2026

## Local development

From the repository root:

```bash
python -m http.server 8000 --directory site
```

Open `http://localhost:8000` and test hash routes directly.

Do not open `site/index.html` with a `file://` URL. Lazy political files and route assets require an HTTP origin.

## Required local validation

Run before opening a pull request:

```bash
python scripts/check_ci_pins.py
python -m py_compile scripts/*.py tests/*.py
find site tests/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/validate_generated_data.py
python scripts/audit_static_site.py
python scripts/verify_release_routes.py
python -m unittest discover -s tests -v
```

The GitHub `Validate Market Brief` workflow runs the same production gates.

## Branch and merge procedure

1. Create one branch for one remodel or maintenance package.
2. Do not mix generated data with presentation changes unless the collector owns the output.
3. Open a pull request against `main`.
4. Wait for `Validate Market Brief / offline-validation` to pass.
5. Review the final diff and confirm unrelated routes or generated files were not changed.
6. Squash-merge only after all required checks pass.
7. Confirm the resulting main commit and any triggered collector/deployment run separately.

Owner-only repository protection remains tracked in GitHub issue #4 until the ruleset is activated and tested.

## Official market-data refresh

Workflow: `.github/workflows/update-free-market-data.yml`

Collector entry point: `scripts/update_free_data_charts.py`

The workflow:

1. checks out current `main`;
2. validates immutable Action pins;
3. installs pinned dependencies;
4. compiles collectors;
5. collects official data;
6. validates generated schemas and semantics;
7. commits only if output changed;
8. rebases against current `main`;
9. revalidates;
10. pushes the generated commit;
11. invokes Pages deployment after success.

### COT incident rule

Never fix an unavailable COT row by selecting a similarly named contract. Update `scripts/cot_contracts.json` only after confirming exact code, accepted market name, exchange, report family and category from the official CFTC dataset. Add or update fixtures and tests in the same pull request.

## Political disclosure refresh

Workflow: `.github/workflows/update-political-disclosures.yml`

Entry point: `scripts/update_political_disclosures_ledger.py`

The collector:

- discovers official House and Senate filings;
- records discovery/download/parser state in `site/data/political/filing-ledger.json`;
- records parser version and SHA-256 content hash;
- retains verified history through temporary failures;
- retries partial and failed filings;
- builds compact summary, annual profile files and search indexes;
- validates annual totals against retained canonical history before commit.

### Political failure triage

1. Open `#sources` and inspect the filing-ledger status.
2. Open `site/data/political/filing-ledger.json` for filing-specific error and next-retry metadata.
3. Confirm the official filing still exists.
4. Reproduce with the existing parser fixture or add a new fixture.
5. Increment parser version when previously parsed filings require reprocessing.
6. Never delete prior verified transactions merely because the current source request failed.

## Curated research updates

Research globals remain repository-maintained delayed inputs. When editing them:

- preserve source and event dates;
- separate fact from interpretation;
- include mechanism, confirmation and invalidation where known;
- leave horizon or confidence `unclear` when not supplied;
- keep consensus `Not sourced` until an approved provider exists;
- do not insert live-price claims into static research records.

## Generated-file ownership

See `docs/DATA-SOURCES.md`.

Do not manually edit:

- `site/free-data.js`;
- `site/data/free-market-data.json`;
- `site/political-data.js`;
- `site/data/political-disclosures*.json`;
- `site/data/political/**` generated manifests, annual files, indexes or ledger.

Change the owning generator, fixture or schema, then let the workflow regenerate output.

## Pages deployment

Workflow: `.github/workflows/deploy-pages.yml`

The workflow can be:

- invoked by successful collector workflows;
- run manually with `workflow_dispatch`;
- triggered by a relevant push to `main` after BR-19.

Deployment steps:

1. validate Action pins;
2. compile Python and recursively syntax-check JavaScript;
3. validate generated data;
4. run static production audit and release route verification;
5. run offline tests;
6. upload `site/` as the Pages artifact;
7. deploy through `actions/deploy-pages`.

A successful deployment workflow proves that GitHub accepted and deployed an artifact. It does not by itself prove that the public URL is serving the new revision. Perform the independent checks below.

## Independent live verification

Public site: `https://thediamonddealer.github.io/market-brief/`

After deployment:

1. open the root URL and confirm HTTP success;
2. open `data/free-market-data.json` and compare `generatedAt` with the repository;
3. open `data/political/manifest.json` and confirm tracker and trade counts;
4. test direct hashes:
   - `#home`
   - `#news`
   - `#cot`
   - `#trackers`
   - `#asset/gold`
   - `#calendar`
   - `#macro`
   - `#sources`
5. confirm the browser console has no route-asset load error;
6. distinguish a deployment trigger from an independently observed live revision in release notes.

GitHub Pages and edge caches may temporarily serve an older artifact. Record the exact time and evidence if live verification is inconclusive.

## Source-health triage

Use `#sources` to inspect independent records. Do not rely only on the page-level generation timestamp.

- `current` — within expected cadence.
- `delayed` — outside normal cadence but potentially usable.
- `stale` — materially old.
- `partial` — mixed success and retryable failures.
- `failed` — latest run error.
- `unavailable` — no approved source or mapping.
- `unknown` — timestamp cannot be interpreted safely.

Check source observation, collection, generation and last successful run separately.

## Common failure modes

### Validation passes but a route is blank

- confirm the route package is listed in `site/core/feature-loader.js`;
- confirm its JavaScript and CSS paths exist;
- run `node --check` on the nested feature file;
- run `python scripts/verify_release_routes.py`;
- inspect the browser console for feature-loader errors.

### Browser shows old Political Flow data

- compare `site/data/political/manifest.json` and the deployed file;
- hard refresh or use a cache-busting query for diagnosis;
- confirm the update workflow pushed a generated commit before deployment;
- verify the browser bootstrap is compact and not the retained full-history JSON.

### Macro panel says current but a series is old

- inspect the individual observation date in `#macro` or `#sources`;
- do not use the FRED pipeline status as the series status;
- confirm expected cadence and holiday gaps before changing thresholds.

### Static audit fails a payload budget

- identify whether full retained data entered the browser bootstrap;
- split by route/year or move to a lazy file;
- remove duplicate route assets;
- increase a budget only with a documented reason and review.

### A legacy file appears unused

- search the repository for imports and script tags;
- run route verification and the complete offline suite;
- remove or retire it in an isolated pull request;
- preserve a compatibility shim when a stable path may still be loaded by the shell.

## Optional BR-20 boundary

Do not add live news, licensed prices, consensus feeds, user accounts, alerts, a database or secret-bearing APIs as part of routine maintenance. Those require explicit BR-20 approval and separate licensing/security design.
