# Free Official Agency Feeds

## Purpose

This pipeline expands Market Brief with primary government observations that complement FRED, CFTC and political disclosures.

| Agency | Coverage | Credential |
|---|---|---|
| SEC EDGAR | Priority filings for semiconductor, mining and critical-mineral companies | None |
| BLS | CPI, core CPI, PPI, payrolls, unemployment, participation, earnings and job openings | None; free registration key optional |
| EIA | US crude, refined-product, refinery and natural-gas fundamentals | Free API key |
| BEA | GDP, income, spending, PCE prices and corporate-profit table lines | Free API key |
| Census | Trade, retail, manufacturing, inventories, housing and construction indicators | Free API key |
| USGS | Annual Mineral Commodity Summaries release status | None |

## Data flow

```text
Official agency API/page
        ↓
scripts/update_official_feeds_resilient.py
        ├── CIK-pinned SEC submissions adapter
        ├── independent adapter per remaining agency
        ├── source-specific identity checks
        ├── timestamp and cadence preservation
        ├── previous verified record retention
        └── credential scrubbing
        ↓
site/data/official-feeds.json
        ↓
#official-feeds + #sources
```

The browser never calls credentialed agency APIs. GitHub Actions performs collection and publishes only normalized observations.

## What works without configuration

SEC, BLS and USGS can run without secrets. SEC uses a versioned ticker-to-CIK registry and the official `data.sec.gov/submissions` endpoint. Every response must confirm the expected ticker before filings are accepted. This avoids depending on the separate SEC ticker-directory file, which can reject cloud runners. BLS uses the public Version 2 timeseries endpoint. USGS detects the current annual Mineral Commodity Summaries edition and does not OCR the PDF.

## Free keys to add

Repository settings → Secrets and variables → Actions → Secrets:

```text
EIA_API_KEY
BEA_API_KEY
CENSUS_API_KEY
```

Optional:

```text
BLS_API_KEY
```

Missing keys produce explicit `unavailable` sources while the no-key agencies continue running. An optional repository variable may provide a more specific SEC user agent:

```text
SEC_USER_AGENT=Market Brief research contact <your monitored contact>
```

Do not place a credential in that variable.

## Scheduling

`.github/workflows/update-official-feeds.yml` runs on weekdays at `22:10 UTC`, Saturday at `03:20 UTC`, manually, and after collector/configuration changes.

## Failure behaviour

- one agency failure does not prevent other agencies from updating;
- prior verified records are retained as `stale`;
- a missing key is `unavailable`, not `failed`;
- a partial agency response is visible as `partial`;
- source observation, collection and last-success times remain separate;
- no market consensus is inferred from official actuals;
- unsafe or ambiguous series and company identities are rejected rather than substituted.

## Source-specific notes

### SEC

Priority forms include 8-K, 10-Q, 10-K, 6-K, 20-F, Form 4, offering documents and beneficial-ownership filings. Each configured company has a pinned CIK. The returned submissions payload must list the configured ticker; a mismatch is rejected and reported. Each accepted record keeps its accession, filed date, accepted time, report period and official archive URL.

The desired ticker list may be broader than the CIK-verified list. New or uncertain companies remain outside collection until their official CIK identity is added and verified.

### BLS

Series IDs are versioned in `scripts/official_feeds_registry.json`. Annual-average period `M13` is excluded so it cannot replace a monthly observation.

### EIA

The registry uses exact legacy series identifiers through EIA API v2's `seriesid` compatibility route. The returned official description must include configured identity terms.

### BEA

The collector requests official NIPA tables and matches configured line descriptions. If a table changes and descriptions no longer match, the table becomes partial rather than selecting an arbitrary line.

### Census

The first implementation preserves official data-type and category codes and does not guess a human-readable meaning. A later verified dictionary join can improve labels.

### USGS

The initial connection tracks the official annual release and source document. Individual mineral values require a structured official data join; PDF OCR is intentionally not used.

## Validation

```bash
python -m py_compile scripts/update_official_feeds.py scripts/update_official_feeds_resilient.py scripts/validate_official_feeds.py
python -m unittest tests/test_official_feeds.py -v
python scripts/validate_official_feeds.py
node --check site/features/official-feeds/official-feeds-data.js
node --check site/features/official-feeds/official-feeds-health.js
node --check site/features/official-feeds/official-feeds-page.js
python scripts/audit_static_site.py
```

## Generated-file ownership

Do not manually maintain `site/data/official-feeds.json`. Change the collector or registry, run the pipeline and validate the generated result.
