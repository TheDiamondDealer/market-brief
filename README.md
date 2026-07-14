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
- Commodity deep dives covering gold, silver, copper, oil, natural gas, rare earths and other products.
- A conditional Scenario Lab using an embedded TradingView chart and the project’s own target-path reasoning.
- Political disclosure trackers using official House PTR PDFs and Senate eFD records.
- Estimated disclosure-derived portfolios, with explicit limitations.

The system is intentionally **research-led rather than real-time**. Fast external widgets are kept separate from internal verified analysis.

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
├── AGENTS.md                         # Instructions Codex reads before work
├── README.md                         # Project overview and setup
├── CONTRIBUTING.md                   # Change and review expectations
├── operating-model.md                # Daily / weekly / monthly research model
├── prompts/                          # Research-generation prompts and rules
├── docs/
│   ├── ARCHITECTURE.md               # System and data-flow design
│   ├── CODEX-HANDOFF.md              # Exact Codex setup and starter tasks
│   └── RUNBOOK.md                    # Operations and troubleshooting
├── scripts/
│   ├── update_political_disclosures.py
│   ├── update_political_disclosures_strict.py
│   └── ...                           # Free official-data collectors and validators
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
    ├── deploy-pages.yml
    ├── update-political-disclosures.yml
    └── ...                           # Scheduled data refresh and validation jobs
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

## Validation

Run these before merging changes:

```bash
# JavaScript syntax
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check

# Python collector syntax
python -m py_compile scripts/*.py

# Generated political disclosure data
python -m json.tool site/data/political-disclosures.json >/dev/null
python -m json.tool site/data/political-disclosures-summary.json >/dev/null
node --check site/political-data.js
```

For a visual check:

```bash
python -m http.server 8000 --directory site
```

Then verify at minimum:

- Command centre loads without console errors.
- Direct hashes such as `#trackers`, `#cot`, `#rates` and `#scenarios` work.
- Political tracker counts are non-zero after a successful import.
- COT long/short charts render when history exists.
- Mobile navigation remains usable.

## Automated workflows

### GitHub Pages

`.github/workflows/deploy-pages.yml` deploys the `site/` directory whenever `site/**` changes.

### Political disclosures

`.github/workflows/update-political-disclosures.yml`:

- checks official House and Senate sources on weekdays;
- retains historical verified records;
- validates that Pelosi history is not silently empty;
- commits imported data or diagnostics;
- rejects malformed asset rows.

### Research cadence

The intended operating cadence is defined in [operating-model.md](operating-model.md):

- Daily tactical brief.
- Weekly operational review.
- Monthly strategic refresh.

Monthly strategic files must not overwrite approved live regime, dossier or thresholds without explicit user approval.

## Moving the project to Codex

Yes: connect Codex to this GitHub repository and select it as the working environment. The repository now includes `AGENTS.md`, which provides persistent project rules to Codex, plus a dedicated [Codex handoff guide](docs/CODEX-HANDOFF.md).

A good first task is:

> Read `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md` and `operating-model.md`. Audit the repository without changing files. Report the current architecture, generated-file boundaries, failing workflows, stale data and the five highest-priority technical risks.

## Security

- Never commit passwords, API keys, cookies, login exports or private tokens.
- Use GitHub Actions secrets for any future credentialed integration.
- Public official sources should normally require no repository secret.
- Rotate any password that has been pasted into chat, an issue, a commit or a log.

## Known limitations

- The site is a growing static application with multiple ordered global scripts rather than a bundled module framework.
- Some historical House PDF formats remain only partially parsed; profiles expose partial status instead of pretending coverage is complete.
- Political portfolios are PTR-derived until complete annual holdings baselines are added.
- TradingView supplies embedded charts/news but not an exportable data API for this project.
- The internal news feed is delayed and interpreted, not a live wire.

## Documentation

- [Codex instructions](AGENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Operations runbook](docs/RUNBOOK.md)
- [Codex handoff](docs/CODEX-HANDOFF.md)
- [Contributing](CONTRIBUTING.md)
- [Research operating model](operating-model.md)
