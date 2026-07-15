# Codex Handoff Guide

**Status date:** 15 July 2026 (Australia/Melbourne)

The GitHub repository is the durable handoff boundary for Market Brief. Codex should not rely on chat summaries when the repository, generated data and workflow evidence can be inspected directly.

## Repository

- Repository: `TheDiamondDealer/market-brief`
- Default branch: `main`
- Current visibility: public
- Current deployment: `https://thediamonddealer.github.io/market-brief/`
- Architecture: static HTML, CSS and JavaScript deployed from `site/`
- Runtime backend: none
- Frontend bundler/framework: none

## Required reading order

Before substantial work, read:

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
12. Relevant files under `prompts/`
13. Every workflow under `.github/workflows/` that relates to the task

Also inspect the current generated caches rather than trusting documentation alone.

## Current implementation summary

The major static-dashboard remodel packages BR-01 through BR-19 are complete.

Subsequent work added:

- dormant private Twelve Data watchlist infrastructure;
- SEC, BLS, EIA, BEA, Census and USGS official-feed collectors;
- read-only Polymarket Crowd Expectations;
- Source Health integration;
- generated-data schemas and semantic validation;
- static accessibility and payload audits;
- expanded regression and workflow tests.

The July 2026 post-integration review corrected:

- a Source Health redispatch loop risk;
- Twelve Data stale-history false freshness;
- false BLS partial status;
- prediction-market validation false positives;
- missed resolution sources;
- provider-spread trust without bid/ask verification;
- broad asset contamination;
- event-family and category concentration in the Crowd list.

These fixes were merged through PRs #29, #30 and #31. Confirm the current implementation rather than assuming the PR description is sufficient evidence.

## Current operational states

### Working or current

- CFTC exact mapped contracts;
- FRED/rates pipeline;
- House and Senate political disclosures;
- BLS configured series;
- USGS annual release detection;
- read-only Crowd Expectations;
- static validation and deployment workflows.

### Explicitly unavailable or blocked

- SEC EDGAR from GitHub-hosted runners: HTTP 403;
- EIA: missing `EIA_API_KEY`;
- BEA: missing `BEA_API_KEY`;
- Census: missing `CENSUS_API_KEY`;
- Twelve Data prices: deliberately disabled while the repository and site are public.

An unavailable source is not automatically a defect. Determine whether it is:

- expected configuration state;
- provider access restriction;
- missing secret;
- stale documentation;
- collector bug;
- frontend hydration bug.

## Private-feed boundary

Do not activate Twelve Data while either the repository or deployed cache is public.

Activation requires:

- private repository;
- protected Cloudflare Pages deployment;
- Cloudflare Access on both the custom and `pages.dev` origins;
- public GitHub Pages origin removed or disabled;
- provider key stored only in GitHub Actions Secrets;
- explicit private-access and collection gates enabled only after independent verification;
- confirmation that the provider plan permits the intended internal use.

Do not commit, print, expose or request real credentials.

## Audit-first working method

The first Codex task should be audit-only.

Do not edit files during discovery. Produce a written report with file paths, line numbers, generated-output evidence and workflow evidence.

Separate findings into:

- confirmed defect;
- documentation drift;
- expected unavailable state;
- missing credential;
- provider restriction;
- security or licensing concern;
- technical debt;
- enhancement opportunity.

Only after that report should a separately scoped implementation task be authorised.

## Copy-and-paste Codex prompt

```text
You are reviewing the Market Brief repository after a major static-dashboard remodel, new official-data integrations, a dormant private-market-data pipeline and a full post-integration audit.

Repository:
- TheDiamondDealer/market-brief
- default branch: main
- current public site: https://thediamonddealer.github.io/market-brief/
- static site deployed from site/
- no frontend bundler, runtime backend or runtime database

WORKING MODE
This first pass is AUDIT ONLY. Do not modify files, create commits or open a pull request during discovery.

READ FIRST
1. AGENTS.md
2. README.md
3. docs/PROJECT-STATUS.md
4. docs/RESEARCH-GOVERNANCE.md
5. docs/ARCHITECTURE.md
6. docs/DATA-SOURCES.md
7. docs/RUNBOOK.md
8. docs/CODEX-HANDOFF.md
9. docs/OFFICIAL-FEEDS.md
10. docs/CROWD-EXPECTATIONS.md
11. operating-model.md
12. relevant prompts/
13. all .github/workflows/

Then inspect the actual source, tests, schemas, generated caches and current workflow configuration. Documentation is a claim to verify, not proof.

CONTEXT TO VERIFY
- BR-01 through BR-19 completed the major static remodel.
- Later work added dormant Twelve Data plumbing, free official agency feeds and read-only Polymarket Crowd Expectations.
- PRs #29, #30 and #31 corrected Source Health recursion risk, false freshness, false BLS partial state, crowd validation/scoring/spread/mapping issues and ranking concentration.
- The repo and GitHub Pages site remain public.
- Twelve Data must remain disabled and contain no prices while any generated cache is publicly accessible.
- SEC EDGAR has returned HTTP 403 from GitHub-hosted runners.
- EIA, BEA and Census require free API keys that may still be absent.
- BLS and USGS should be current in the latest generated official-feed cache.
- Crowd Expectations must remain read-only with no wallet, authentication, signing, deposit or order code.

NON-NEGOTIABLE RULES
- Never fabricate prices, filings, trades, consensus, observations, source URLs or catalyst dates.
- Preserve source attribution and observation timestamps.
- Keep observed data separate from model interpretation.
- Preserve previous verified data on temporary source failure and expose stale/partial/error status.
- Do not substitute a similar benchmark, contract, politician, company or dataset to hide missing data.
- Do not manually edit generated files as the primary fix.
- Do not add a framework, bundler, backend or production dependency during this audit.
- Do not expose or request credentials.
- Keep TradingView widget content outside internal calculations.
- Keep political traded and filed dates separate and preserve spouse/member attribution.
- Keep Brent and WTI separate and US Henry Hub and UK NBP separate.
- Do not claim branch protection, deployment success, source availability or privacy controls without direct evidence.

AUDIT SCOPE
1. Confirm the architecture and script/data loading model.
2. Identify all generated versus hand-maintained files.
3. Confirm every major hash route and feature manifest entry.
4. Review source-health extension behaviour for recursion, duplicate records and false freshness.
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
   - category/event balancing;
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

RUN THE FULL OFFLINE VALIDATION
python scripts/check_ci_pins.py
python -m pip install --disable-pip-version-check --requirement requirements/ci.txt
python -m pip check
python -m py_compile scripts/*.py tests/*.py
find site tests/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check
python scripts/validate_generated_data.py
python scripts/validate_crowd_expectations.py
python scripts/audit_static_site.py
python -m unittest discover -s tests -v

BROWSER REVIEW
Serve with:
python -m http.server 8000 --directory site

Use browser automation or Playwright where practical. Test desktop and mobile. Inspect console and network errors.

Verify at least:
- #home
- #today (legacy redirect to #home; there is no standalone Daily Brief menu item)
- #news
- #cot
- #rates
- #official-feeds
- #crowd-expectations
- #scenarios
- #trackers
- representative asset and product-detail routes

DELIVERABLE
Return an audit report containing:
1. Executive verdict.
2. Repository and deployment state confirmed as of the review date.
3. Architecture map.
4. Data-source status table.
5. Validation and browser-test results.
6. Confirmed defects ranked Critical/High/Medium/Low.
7. Documentation drift.
8. Expected limitations that are not defects.
9. Security, privacy and licensing risks.
10. Top five recommended next actions in dependency order.
11. Exact files likely to change for each proposed action.
12. Evidence: file paths, line numbers, workflow run references and generated-data samples.

Do not implement fixes in this first pass. Do not weaken unavailable or failed states merely to make the dashboard look complete.
```

## After Codex returns the audit

Review whether every finding is supported by evidence.

Before authorising implementation, ask:

- Is this a confirmed defect or expected unavailable state?
- Is the proposed target a generated file?
- Does the fix preserve source identity and retained history?
- Could it expose a private or licensed dataset?
- Does it change an existing route or data contract?
- Does it require owner-controlled repository or Cloudflare settings?
- Is the work small enough for one dedicated branch and pull request?

Then issue one narrowly scoped implementation task.

## Implementation prompt pattern

```text
Implement only [named work package or confirmed defect] from the approved audit.

Create a dedicated branch and pull request. Do not start unrelated work.

Preserve all AGENTS.md and research-governance rules. Fix the source of truth rather than manually maintaining generated output. Add regression coverage. Run the complete validation suite and browser smoke tests relevant to the change.

The pull request must state:
- files changed;
- behaviour fixed or added;
- generated outputs inspected;
- tests run and results;
- source, privacy or licensing limitations;
- whether deployment was triggered and whether the live site was independently verified.

Stop after this work package.
```

## Codex environment

Use Python 3.12 and a current Node.js release.

No frontend package install is required for ordinary work.

Install repository test dependencies with:

```bash
python -m pip install --disable-pip-version-check --requirement requirements/ci.txt
```

Allow internet access only when the task requires current official-source verification or controlled live endpoint tests.

## Ownership transfer rule

Important decisions belong in:

- `AGENTS.md` for standing engineering rules;
- `docs/PROJECT-STATUS.md` for current implementation and blockers;
- `docs/RESEARCH-GOVERNANCE.md` for research standards;
- `docs/ARCHITECTURE.md` for system design;
- `docs/DATA-SOURCES.md` for source trust and usage;
- `docs/RUNBOOK.md` for operations;
- `operating-model.md` for daily, weekly and monthly governance;
- GitHub issues for unfinished owner or implementation work;
- pull request descriptions for change-specific evidence.

Do not leave important project behaviour only in a conversation.
