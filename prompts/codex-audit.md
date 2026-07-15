# Codex Audit Prompt — Market Brief

**Status date:** 15 July 2026 (Australia/Melbourne)

Copy everything below into Codex as the first review task.

---

You are reviewing the Market Brief repository after a major static-dashboard remodel, new official-data integrations, a dormant private-market-data pipeline and a full post-integration audit.

Repository:

- `TheDiamondDealer/market-brief`
- default branch: `main`
- current public site: `https://thediamonddealer.github.io/market-brief/`
- static site deployed from `site/`
- no frontend bundler, runtime backend or runtime database

## Working mode

This first pass is **AUDIT ONLY**.

Do not modify files, create commits or open a pull request during discovery.

## Read first

1. `AGENTS.md`
2. `README.md`
3. `docs/PROJECT-STATUS.md`
4. `docs/RESEARCH-GOVERNANCE.md`
5. `docs/ARCHITECTURE.md`
6. `docs/DATA-SOURCES.md`
7. `docs/RUNBOOK.md`
8. `docs/CODEX-HANDOFF.md`
9. `docs/OFFICIAL-FEEDS.md`
10. `docs/CROWD-EXPECTATIONS.md`
11. `operating-model.md`
12. relevant files under `prompts/`
13. all workflows under `.github/workflows/`

Then inspect the actual source, tests, schemas, generated caches and current workflow configuration. Documentation is a claim to verify, not proof.

## Context to verify

- BR-01 through BR-19 completed the major static remodel.
- Later work added dormant Twelve Data plumbing, free official agency feeds and read-only Polymarket Crowd Expectations.
- PRs #29, #30 and #31 corrected Source Health recursion risk, false freshness, false BLS partial state, crowd validation/scoring/spread/mapping issues and ranking concentration.
- The repository and GitHub Pages site remain public.
- Twelve Data must remain disabled and contain no prices while any generated cache is publicly accessible.
- SEC EDGAR has returned HTTP 403 from GitHub-hosted runners.
- EIA, BEA and Census require free API keys that may still be absent.
- BLS and USGS should be current in the latest generated official-feed cache.
- Crowd Expectations must remain read-only with no wallet, authentication, signing, deposit or order code.

## Non-negotiable rules

- Never fabricate prices, filings, trades, consensus, observations, source URLs or catalyst dates.
- Preserve source attribution and observation timestamps.
- Keep observed data separate from model interpretation.
- Preserve previous verified data on temporary source failure and expose stale, partial, failed or unavailable status.
- Do not substitute a similar benchmark, contract, politician, company or dataset to hide missing data.
- Do not manually edit generated files as the primary fix.
- Do not add a framework, bundler, backend or production dependency during this audit.
- Do not expose or request credentials.
- Keep TradingView widget content outside internal calculations.
- Keep political traded and filed dates separate and preserve spouse/member attribution.
- Keep Brent and WTI separate and US Henry Hub and UK NBP separate.
- Do not claim branch protection, deployment success, source availability or privacy controls without direct evidence.

## Audit scope

1. Confirm the architecture and script/data loading model.
2. Identify all generated versus hand-maintained files.
3. Confirm every major hash route and feature-manifest entry.
4. Review Source Health extension behaviour for recursion, duplicate records and false freshness.
5. Review Twelve Data privacy gates, disabled output, secret handling, stale retention and provider-data exposure risk.
6. Review official feeds:
   - SEC identity verification and current failure mode;
   - BLS completeness and advisory handling;
   - EIA, BEA and Census missing-key states;
   - USGS release detection and no-OCR boundary.
7. Review Crowd Expectations:
   - read-only boundary;
   - exclusions;
   - resolution-source extraction;
   - calculated bid/ask spread;
   - quality grading;
   - asset mapping;
   - category and event balancing;
   - history retention;
   - shock generation.
8. Review CFTC, FRED and political-disclosure collectors for regression or documentation drift.
9. Review GitHub Actions for:
   - immutable action pins;
   - least privilege;
   - generated-data writer concurrency;
   - infinite-loop risk;
   - meaningful-change commits;
   - validation before push;
   - deployment triggers.
10. Compare generated data with documentation and current source status.
11. Review the research governance and monthly approval boundary.
12. Identify security, licensing, deployment and maintainability risks.

## Run the full offline validation

```bash
python scripts/check_ci_pins.py
python -m pip install --disable-pip-version-check --requirement requirements/ci.txt
python -m pip check
python -m py_compile scripts/*.py tests/*.py
find site tests/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/validate_generated_data.py
python scripts/validate_crowd_expectations.py
python scripts/audit_static_site.py
python -m unittest discover -s tests -v
```

## Browser review

Serve with:

```bash
python -m http.server 8000 --directory site
```

Use browser automation or Playwright where practical. Test desktop and mobile. Inspect console and network errors.

Verify at least:

- `#home`
- `#today`
- `#news`
- `#cot`
- `#rates`
- `#official-feeds`
- `#crowd-expectations`
- `#scenarios`
- `#trackers`
- representative asset and product-detail routes

## Deliverable

Return an audit report containing:

1. Executive verdict.
2. Repository and deployment state confirmed as of the review date.
3. Architecture map.
4. Data-source status table.
5. Validation and browser-test results.
6. Confirmed defects ranked Critical, High, Medium or Low.
7. Documentation drift.
8. Expected limitations that are not defects.
9. Security, privacy and licensing risks.
10. Top five recommended next actions in dependency order.
11. Exact files likely to change for each proposed action.
12. Evidence: file paths, line numbers, workflow run references and generated-data samples.

Do not implement fixes in this first pass. Do not weaken unavailable or failed states merely to make the dashboard look complete.
