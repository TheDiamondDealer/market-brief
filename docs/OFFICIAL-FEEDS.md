# Free Official Agency and Exchange Feeds

## Purpose

This pipeline adds primary-source observations that complement FRED, CFTC, political disclosures and the discovery-only GDELT radar. Official records are evidence inputs; the collector does not infer market direction or investment conclusions.

| Source | Coverage | Credential |
|---|---|---|
| ASX public company announcements | Announcement metadata and official document links for the configured strategic-resource watchlist | None |
| Federal Reserve RSS | Monetary-policy releases, speeches, testimony, credit/liquidity and balance-sheet releases | None |
| SEC EDGAR | Priority filings for semiconductor, mining and critical-mineral companies | None |
| BLS | CPI, core CPI, PPI, payrolls, unemployment, participation, earnings and job openings | None; free registration key optional |
| EIA | US crude, refined-product, refinery and natural-gas fundamentals | Free API key |
| BEA | GDP, income, spending, PCE prices and corporate-profit table lines | Free API key |
| Census | Trade, retail, manufacturing, inventories, housing and construction indicators | Free API key |
| USGS | Annual Mineral Commodity Summaries release status | None |

## Data flow

```text
Official agency / exchange endpoint
        ↓
scripts/update_official_feeds_resilient.py
        ├── six existing agency adapters
        └── independent source failure handling
        ↓
temporary six-source snapshot
        ↓
scripts/update_official_news.py
        ├── ASX per-company announcement adapter
        ├── Federal Reserve RSS adapter
        ├── previous ASX/Fed snapshot retention
        ├── identity and domain checks
        └── collection-count recalculation
        ↓
site/data/official-feeds.json
        ↓
#official-feeds + #sources
```

The browser never calls upstream sources. GitHub Actions performs collection and publishes normalized public metadata.

## ASX public announcements

The integration monitors the versioned watchlist in `scripts/official_news_registry.json` and stores:

- announcement ID;
- issuer code and name where supplied;
- headline;
- release timestamp;
- market-sensitive flag;
- announcement category and page count where supplied;
- direct official ASX document link.

Trust and licensing boundaries:

- the endpoint is the public per-company announcement endpoint;
- this is **not** the licensed complete real-time ASX ComNews product;
- the system does not claim complete market-wide coverage or redistribution rights;
- a returned issuer code must match the requested ticker;
- malformed records and identity mismatches are rejected;
- the collector stores metadata and official links, not copied announcement bodies;
- a temporary failure retains the last verified records as stale.

The initial watchlist focuses on rare earths, critical minerals, lithium, uranium and major diversified miners. Additions require an exact ASX code and a reason tied to the research universe.

## Federal Reserve official RSS

Configured feeds include:

- monetary-policy releases;
- speeches;
- testimony;
- credit and liquidity programs and balance-sheet releases.

Rules:

- only links on `www.federalreserve.gov` are accepted;
- duplicate releases appearing in more than one feed are clustered by official URL;
- publication timestamps are converted to UTC and displayed in Melbourne time by the browser;
- headline/link metadata is evidence only and does not create a market interpretation;
- temporary feed failures retain previously verified records as stale.

## Existing agencies

### SEC

Priority forms include 8-K, 10-Q, 10-K, 6-K, 20-F, Form 4, offering documents and beneficial-ownership filings. Each configured company has a pinned CIK. The returned submissions payload must list the configured ticker before filings are accepted.

### BLS

Series IDs are versioned in `scripts/official_feeds_registry.json`. Annual-average period `M13` is excluded so it cannot replace a monthly observation. Benign advisory messages do not make a complete configured series set partial.

### EIA

The registry uses exact series identities. Returned descriptions must include configured identity terms.

### BEA

The collector requests official NIPA tables and matches configured line descriptions. Unmatched lines become partial rather than being guessed.

### Census

Official data-type and category codes are preserved until a verified dictionary join exists.

### USGS

The connection tracks the official annual Mineral Commodity Summaries release and does not OCR the PDF.

## Credentials

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

ASX and Federal Reserve collection require no key. Credentials must never appear in source files, browser JavaScript, generated data or logs.

## Scheduling

`.github/workflows/update-official-feeds.yml` runs every four hours on weekdays, once on Saturday, manually, and after relevant collector/configuration changes.

The workflow:

1. preserves the previous eight-source snapshot;
2. refreshes the six existing agencies;
3. merges fresh ASX and Federal Reserve records;
4. retains prior ASX/Fed records as stale when required;
5. validates the expanded contract;
6. commits only changed generated data;
7. deploys the static site after success.

## Failure behaviour

- one source failure does not prevent other sources from updating;
- prior verified records are retained as `stale`;
- a missing free API key is `unavailable`, not `failed`;
- a partial response remains visible as `partial`;
- observation, collection and last-success times remain separate;
- unsafe identities, domains or URLs are rejected rather than substituted;
- a successful run must never silently replace populated data with an empty source.

## Validation

```bash
python -m py_compile scripts/update_official_feeds.py scripts/update_official_feeds_resilient.py scripts/update_official_news.py scripts/validate_official_feeds.py
python -m unittest tests/test_official_feeds.py tests/test_official_news_feeds.py -v
python scripts/validate_official_feeds.py
node --check site/features/official-feeds/official-feeds-data.js
node --check site/features/official-feeds/official-feeds-health.js
node --check site/features/official-feeds/official-feeds-page.js
python scripts/audit_static_site.py
```

## Generated-file ownership

Do not manually maintain `site/data/official-feeds.json` as the primary solution. Change the collector or registry, run the pipeline, inspect representative records, validate and then commit generated output.
