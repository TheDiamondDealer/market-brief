# Market Brief Intelligence Console

A static, research-led market intelligence dashboard focused on commodities, macro, rates, positioning, cross-asset transmission and delayed public political disclosures.

**Live dashboard:** https://thediamonddealer.github.io/market-brief/

> Research and system testing only. Not financial advice. Political transaction data is delayed public disclosure, not real-time execution data.

## What the project does

The dashboard combines:

- A market command centre with regime, risk gauge, asset bias and trigger proximity.
- Daily and weekly research views.
- An interpreted news feed with first-order, second-order and invalidation logic.
- CFTC Commitments of Traders positioning, including long/short history and percentiles.
- Rates and liquidity data from free official sources.
- Free official agency feeds for filings, macro, energy and critical-mineral context, with honest unavailable and failed states.
- Read-only Crowd Expectations for market-relevant event probabilities.
- Commodity deep dives covering gold, silver, copper, oil, natural gas, rare earths and other products.
- A conditional Scenario Lab using an embedded TradingView chart and the project’s own target-path reasoning.
- Political disclosure trackers using official House PTR PDFs and Senate eFD records.
- Estimated disclosure-derived portfolios, with explicit limitations.
- Dormant private-market-data plumbing that remains disabled while the repository and deployed site are public.

The system is intentionally **research-led rather than real-time**. Fast external widgets are kept separate from internal verified analysis.

## Current project status

Read [docs/PROJECT-STATUS.md](docs/PROJECT-STATUS.md) for the dated implementation state, completed audit findings, source availability, privacy boundaries and recommended next-work order.

The July 2026 post-integration audit found and corrected material issues involving Source Health recursion, false freshness, BLS status handling, Crowd Expectations validation, spread calculation, asset mapping and list concentration. Current unavailable sources remain visible rather than being substituted.

## Quick start

No frontend build step is required.

```bash
git clone https://github.com/TheDiamondDealer/market-brief.git
cd market-brief
python -m http.server 8000 --directory site
```

Open `http://localhost:8000`.

Do not open `site/index.html` directly with `file://`; browser security rules can prevent widgets and local data loading from behaving normally.

## Repository map

```text
.
├── AGENTS.md                         # Persistent engineering and data rules
├── README.md                         # Project overview and setup
├── CONTRIBUTING.md                   # Change and review expectations
├── operating-model.md                # Daily / weekly / monthly research model
├── prompts/                          # Research-generation prompts and rules
├── docs/
│   ├── PROJECT-STATUS.md             # Dated implementation, blockers and next steps
│   ├── RESEARCH-GOVERNANCE.md        # Investment-research mandate and protocol summary
│   ├── ARCHITECTURE.md               # System and data-flow design
│   ├── DATA-SOURCES.md               # Source trust and usage rules
│   ├── RUNBOOK.md                    # Operations and troubleshooting
│   ├── CODEX-HANDOFF.md              # Exact Codex setup and audit prompt
│   ├── OFFICIAL-FEEDS.md             # SEC/BLS/EIA/BEA/Census/USGS pipeline
│   └── CROWD-EXPECTATIONS.md         # Read-only prediction-market integration
├── scripts/
│   ├── update_political_disclosures.py
│   ├── update_political_disclosures_strict.py
│   └── ...                           # Official-data collectors and validators
├── site/
│   ├── index.html                    # Static application shell and script order
│   ├── data.js                       # Core seeded research state
│   ├── intelligence-data.js          # Interpreted news and tracker definitions
│   ├── political-data.js             # GENERATED political transaction cache
│   ├── free-data.js                  # GENERATED official market-data cache
│   ├── data/                          # Machine-readable generated JSON caches
│   ├── products-*.js                 # Commodity research library
│   ├── *-app.js / *-ui.js            # Rendering and interaction modules
│   └── *.css                         # Dashboard styles
└── .github/workflows/
    ├── validate.yml
    ├── deploy-pages.yml
    ├── update-political-disclosures.yml
    └── ...                           # Scheduled refresh and validation jobs
```

## Architecture in one minute

1. GitHub Actions downloads free official data and disclosure records.
2. Python collectors validate and normalize the source data.
3. Collectors write static JSON and browser-ready JavaScript caches under `site/`.
4. The browser loads ordered global data modules, then rendering modules.
5. Any change under `site/**` triggers GitHub Pages deployment.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

## Important source-of-truth rules

### Generated files

Do not manually maintain these as primary sources:

- `site/political-data.js`
- `site/data/political-disclosures.json`
- `site/data/political-disclosures-summary.json`
- generated official-market-data caches under `site/`

Change the relevant collector, run it, validate the output, and commit both code and generated data when appropriate.

### Political disclosures

- Trade date and filing date are separate fields.
- Late filings are retained permanently.
- Spouse, member, joint and dependent ownership must remain exactly attributed.
- Nancy Pelosi profiles must not describe Paul Pelosi’s transactions as Nancy personally trading.
- Portfolio values are statutory ranges and reconstruction estimates, not brokerage balances.
- Official House or Senate records outrank third-party parsers.

### Market data and news

- Never fabricate a price, consensus estimate, trade or filing.
- Display source and freshness where practical.
- TradingView widgets are external display/discovery layers; their data is not extracted into the internal bias engine.
- Biases are conditional research views, not trade recommendations.
- Licensed private data must not be activated while generated output remains publicly accessible.
- Read-only Crowd Expectations must never acquire wallet, signing, deposit or order functionality.

## Research governance

Investment research must follow [docs/RESEARCH-GOVERNANCE.md](docs/RESEARCH-GOVERNANCE.md).

Core requirements include:

- use AUD as the base currency;
- separate immediate risk, six-month trade, two-year investment and longer-term views;
- prioritise primary sources;
- distinguish fact, guidance, consensus, forecast, inference and opinion;
- analyse valuation and embedded expectations;
- present serious bear cases and invalidation conditions;
- compare the preferred security with stronger, cheaper or lower-risk alternatives;
- keep rare-earth elements, semiconductor subsectors and commodity benchmarks distinct.

## Validation

Use the complete offline validation sequence before merging broad changes:

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

For a visual check:

```bash
python -m http.server 8000 --directory site
```

Then verify at minimum:

- Command centre loads without console errors.
- Direct hashes such as `#trackers`, `#cot`, `#rates`, `#official-feeds`, `#crowd-expectations` and `#scenarios` work.
- Political tracker counts are non-zero after a successful import.
- COT long/short charts render when history exists.
- Expected unavailable and failed source states remain visible.
- Mobile navigation remains usable.

## Automated workflows

### Validation

`.github/workflows/validate.yml` compiles Python, checks JavaScript recursively, validates generated schemas and semantics, audits the static site and runs the full offline fixture and route test suite.

### GitHub Pages

`.github/workflows/deploy-pages.yml` deploys the `site/` directory whenever `site/**` changes.

### Political disclosures

`.github/workflows/update-political-disclosures.yml`:

- checks official House and Senate sources on weekdays;
- retains historical verified records;
- validates that Pelosi history is not silently empty;
- commits imported data or diagnostics;
- rejects malformed asset rows.

### Official agency feeds

The official-feed workflow keeps each agency independent, preserves stale verified records, exposes missing keys and validates BLS completeness before committing generated output.

### Crowd Expectations

The Crowd Expectations workflow runs every six hours, validates read-only boundaries and commits only validated generated market data.

### Research cadence

The intended operating cadence is defined in [operating-model.md](operating-model.md):

- Daily tactical brief.
- Weekly operational review.
- Monthly strategic refresh.

Monthly strategic files must not overwrite approved live regime, dossier or thresholds without explicit user approval.

## Moving the project to Codex

Connect Codex to this GitHub repository and select it as the working environment. `AGENTS.md` supplies persistent rules, while [docs/CODEX-HANDOFF.md](docs/CODEX-HANDOFF.md) contains the current audit-only prompt and implementation handoff pattern.

The first Codex pass should be audit-only and must not edit files. It should verify the current architecture, feeds, generated data, privacy gates, workflows, routes and audit fixes before proposing new work.

## Security and privacy

- Never commit passwords, API keys, cookies, login exports or private tokens.
- Use GitHub Actions Secrets for credentialed collectors.
- Anything under `site/` is public while the current GitHub Pages deployment remains active.
- Making the repository private is not sufficient by itself; deployed origins must also be protected before private feeds are activated.
- Rotate any credential that has been pasted into chat, an issue, a commit or a log.

## Known limitations

- The site is a growing static application with ordered global scripts rather than a bundled module framework.
- Some historical House PDF formats remain only partially parsed; profiles expose partial status instead of pretending coverage is complete.
- Political portfolios are PTR-derived until complete annual holdings baselines are added.
- TradingView supplies embedded charts/news but not an exportable internal API feed.
- The internal news feed is delayed and interpreted, not a live wire.
- SEC EDGAR remains blocked from GitHub-hosted runners.
- EIA, BEA and Census remain unavailable until their free keys are configured.
- Twelve Data remains disabled while the site is public.

## Documentation

- [Codex instructions](AGENTS.md)
- [Current project status](docs/PROJECT-STATUS.md)
- [Research governance](docs/RESEARCH-GOVERNANCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data sources and trust model](docs/DATA-SOURCES.md)
- [Operations runbook](docs/RUNBOOK.md)
- [Codex handoff](docs/CODEX-HANDOFF.md)
- [Free official agency feeds](docs/OFFICIAL-FEEDS.md)
- [Crowd Expectations](docs/CROWD-EXPECTATIONS.md)
- [Contributing](CONTRIBUTING.md)
- [Research operating model](operating-model.md)
