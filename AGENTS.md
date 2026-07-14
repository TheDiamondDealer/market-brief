# AGENTS.md

## Mission

Maintain and extend the Market Brief Intelligence Console as a trustworthy, research-led market dashboard. Prefer correct, sourceable, auditable behaviour over visual novelty or unsupported certainty.

Read these files before substantial work:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/RUNBOOK.md`
4. `operating-model.md`
5. The relevant file under `prompts/`

## Non-negotiable data rules

- Never invent prices, economic consensus estimates, filings, trades, holdings, news events or source URLs.
- Preserve source attribution and timestamps.
- Official sources outrank third-party summaries and parsers.
- When sources fail, retain previously verified data and expose a partial/stale/error status.
- Do not replace missing data with a superficially similar contract, benchmark, politician or asset.
- A model interpretation must be distinguishable from an official observation.

## Political disclosure rules

- Keep `traded` and `filed` dates separate.
- Retain verified historical transactions permanently, including filings disclosed more than 45 days after execution.
- Preserve owner/account labels exactly: member, spouse, joint or dependent.
- Do not describe Paul Pelosi’s disclosed transactions as Nancy Pelosi personally trading.
- Treat statutory amount ranges as ranges, not exact transaction values.
- Portfolio estimates are disclosure-derived and must not be presented as brokerage balances.
- House Clerk and Senate eFD records are primary. Third-party sources may assist discovery but cannot override an official filing.
- Trump policy tracking and Trump financial-disclosure tracking are separate concerns.

## Market research rules

- Bias is conditional analysis, not a price promise or trade recommendation.
- Show the driver, contradiction, confirmation and invalidation conditions where possible.
- Separate first-order, second-order and cross-asset effects.
- Do not infer physical tightness solely from a futures price move.
- Keep Brent and WTI separate.
- Keep US Henry Hub and UK NBP separate.
- Keep external TradingView widgets separate from internal data and calculations.
- TradingView chart/news widget data must not be scraped or represented as an internal API feed.

## Approved research hierarchy

Prefer sources in this order:

1. Government, regulator, central bank, exchange or company primary release.
2. Original filing, dataset or legal/policy document.
3. High-quality wire or financial publication.
4. Specialist industry publication.
5. Social media only as an unverified discovery lead.

Major policy or geopolitical claims should normally have an official source or two independent reputable reports.

## Repository boundaries

### Hand-maintained source files

Examples:

- `site/index.html`
- `site/*.css`
- `site/*-app.js`
- `site/*-ui.js`
- `site/products-*.js`
- `site/intelligence-data.js`
- `site/command-centre-data.js`
- `scripts/*.py`
- `prompts/*.md`
- `operating-model.md`

### Generated files

Do not edit these as the primary fix:

- `site/political-data.js`
- `site/data/political-disclosures.json`
- `site/data/political-disclosures-summary.json`
- generated official market-data JavaScript/JSON caches under `site/`

Change the collector or source model, regenerate, validate, then commit the output.

## Static frontend constraints

- The application is a static GitHub Pages site without a bundler.
- Script order in `site/index.html` matters because modules share browser globals.
- Data modules must load before the rendering modules that consume them.
- When adding a generated data module, verify it is actually loaded by the page.
- Preserve direct routes such as `#trackers`, `#cot`, `#rates`, `#scenarios`, `#news` and product-detail hashes.
- Avoid adding a framework or production dependency without explaining the migration cost and receiving approval.

## Required checks

Run the checks relevant to the change. For broad changes, run all of them.

```bash
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check
python -m py_compile scripts/*.py
python -m json.tool site/data/political-disclosures.json >/dev/null
python -m json.tool site/data/political-disclosures-summary.json >/dev/null
node --check site/political-data.js
```

Serve the site locally for visual testing:

```bash
python -m http.server 8000 --directory site
```

Minimum smoke test:

- no browser-console exceptions;
- command centre renders;
- `#trackers` shows imported counts rather than seeded zeros;
- `#cot` renders current data and history when available;
- `#rates` renders freshness and source status;
- `#scenarios` works on desktop and mobile;
- direct links and sidebar navigation work;
- generated data failure states remain visible.

## Collector expectations

- Set a descriptive user agent.
- Use timeouts and explicit failure handling.
- Validate content type and schema before accepting data.
- Deduplicate using stable identifiers.
- Preserve previous verified records on temporary source failure.
- Commit concise diagnostics or summaries when practical.
- Never let a successful workflow silently replace populated data with an empty dataset.
- Avoid repeatedly downloading known unchanged historical filings.

## GitHub Actions expectations

- Scheduled jobs must be safe to rerun.
- Generated-data commits must avoid triggering infinite workflow loops.
- Use least-privilege permissions.
- Do not place secrets in workflow files, logs or generated site data.
- Pages deployment uses `site/` as the artifact.
- A changed `site/**` file should trigger deployment through `.github/workflows/deploy-pages.yml`.

## Research approval boundary

The monthly strategic task may create drafts, but must not overwrite live approved dossier, regime-state or threshold files without an explicit user approval identifying the month. Show a concise diff before promotion. Stop and ask when approval is ambiguous.

## Change discipline

Before editing:

1. Identify the source of truth.
2. Check whether the target file is generated.
3. Find all consumers of the changed field or module.
4. Confirm script/load order if frontend globals are involved.

Before finishing:

1. Run syntax and data validation.
2. Inspect the actual generated output, not only the collector exit code.
3. State what was verified and what remains partial.
4. Update documentation when behaviour, workflows, data contracts or operational steps change.

## Security

- Never use or preserve credentials pasted into chat.
- Never commit passwords, session cookies, API tokens or private account exports.
- Use GitHub Actions secrets only when a future integration genuinely requires credentials.
- Prefer free public official endpoints for the current architecture.

## Communication style for completed work

Report:

- files changed;
- behaviour added or fixed;
- checks run and their outcome;
- data-source limitations;
- whether deployment was merely triggered or independently confirmed live.

Do not claim a collector, deployment or page is working until evidence supports the claim.
