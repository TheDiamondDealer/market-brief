# Private Twelve Data Market Feed

## Purpose

This integration adds a credentialed market-price layer for:

- US semiconductor equities;
- rare-earth and critical-mineral companies;
- selected Australian critical-mineral companies;
- diversified miners;
- benchmark and sector ETFs.

The feed is designed for **one-user, access-controlled internal research**. It must not be activated while either the GitHub repository or the deployed dashboard is public.

Provider terms and exchange entitlements can change. Reconfirm the current Twelve Data plan and usage rights before activation or expanding access beyond the owner.

## Architecture

```text
Twelve Data API
       │
       │ API key stored only in GitHub Actions Secrets
       ▼
scripts/update_twelve_data.py
       ├── quote snapshots
       ├── daily history
       ├── return and moving-average calculations
       ├── per-symbol failure retention
       └── credential-scrubbing validation
       │
       ├── site/data/equity-market-data.json
       └── site/equity-data.js
                    │
                    ▼
         Cloudflare Pages + Access
                    │
                    ▼
          authorised owner account
```

No browser request is made to Twelve Data. The browser receives only the generated cache, and the API key never appears under `site/`.

## Safety gates

`.github/workflows/update-twelve-data.yml` will collect credentialed data only when all four conditions are true:

1. the GitHub repository is private;
2. repository variable `PRIVATE_SITE_ACCESS_CONFIRMED` equals `true`;
3. repository variable `PRIVATE_MARKET_DATA_ENABLED` equals `true`;
4. repository secret `TWELVE_DATA_API_KEY` exists.

Until then, the committed cache is an explicit unavailable-state dataset with no prices.

When `PRIVATE_MARKET_DATA_ENABLED=true`, `.github/workflows/deploy-pages.yml` stops publishing new revisions to the legacy public GitHub Pages origin. Cloudflare Pages must be the active deployment route before enabling the feed.

## Activation order

Do these steps in order.

### 1. Make the repository private

Repository settings → General → Danger Zone → Change repository visibility.

Do not activate the private feed in a public repository. Generated price caches are committed for retention and would otherwise be visible through Git history.

### 2. Create the Cloudflare Pages project

Connect the private GitHub repository.

Use:

```text
Framework preset: None
Build command:    leave blank
Build output:     site
Production branch: main
```

The project requires no Node build step.

### 3. Protect every Cloudflare hostname

Configure Cloudflare Access for:

- the production custom domain, when used;
- the generated `*.pages.dev` hostname.

Allow only the nominated owner identity. Email one-time PIN or a private identity provider is suitable.

Test in a signed-out/private browser window. The dashboard files and direct JSON paths must not load before authentication.

### 4. Retire the public origin

Disable GitHub Pages after confirming Cloudflare deployment, or leave the workflow safeguard in place so no private-feed revision is deployed there.

Confirm these paths cannot expose current private data without authentication:

```text
/equity-data.js
/data/equity-market-data.json
/#equities
```

### 5. Add the API secret

Repository settings → Secrets and variables → Actions → Secrets:

```text
TWELVE_DATA_API_KEY
```

Never paste the key into a workflow, issue, committed file or chat transcript.

### 6. Add activation variables

Repository settings → Secrets and variables → Actions → Variables:

```text
PRIVATE_SITE_ACCESS_CONFIRMED=true
PRIVATE_MARKET_DATA_ENABLED=true
```

Optional throttle override:

```text
TWELVE_DATA_REQUEST_INTERVAL_SECONDS=8.1
```

The default throttle is deliberately conservative for a low-rate plan.

### 7. Run the first full collection

Actions → **Update private Twelve Data market feed** → Run workflow → `full`.

Verify:

- workflow privacy gate reports enabled;
- collector tests pass;
- generated schema validation passes;
- `site/equity-data.js` contains no key;
- `#equities` shows prices and timestamps;
- `#sources` shows Twelve Data and each instrument;
- failed symbols are explicit rather than silently removed.

## Collection schedule

The workflow uses UTC schedules:

- `14:10`, `16:10`, `18:10`, `20:10` Monday–Friday: quote snapshots;
- `21:30` Monday–Friday: full daily-history refresh.

The exact relationship to US and Melbourne market hours changes during daylight-saving transitions. The schedule is intentionally approximate; source timestamps remain visible.

## Generated metrics

For each accepted instrument the collector can publish:

- latest accepted price;
- previous close and daily move;
- 1-week, 1-month, 3-month and 1-year returns;
- 20-, 50- and 200-session moving averages;
- distance from each moving average;
- current volume versus 20-session average volume;
- 52-week range position;
- a transparent moving-average trend classification;
- observation, collection and generation timestamps.

These are mechanical observations and classifications, not recommendations.

## Failure behaviour

The collector is defensive:

- one symbol failure does not erase other symbols;
- a failed symbol retains its last verified row and becomes `stale`;
- a partial quote/history response becomes `partial`;
- an all-source failure retains prior verified values;
- API errors are stored without request URLs or credentials;
- generated files fail validation if they contain `apikey=` or the secret name;
- disabled mode publishes no prices.

## Watchlist maintenance

Source of truth:

```text
scripts/twelve_data_watchlist.json
```

Each item requires:

```json
{
  "id": "nvda",
  "symbol": "NVDA",
  "name": "NVIDIA",
  "exchange": "NASDAQ",
  "group": "Semiconductors",
  "currency": "USD"
}
```

Use `apiExchange` only when the provider needs an explicit market, for example:

```json
{
  "id": "lyc",
  "symbol": "LYC",
  "apiExchange": "ASX"
}
```

A newly configured symbol may be unavailable under the current plan or provider symbology. That is a visible data state, not a reason to substitute another security.

## Local validation

Generate a no-price cache without a credential:

```bash
python scripts/update_twelve_data.py \
  --mode disabled \
  --reason "Private perimeter pending"
```

Run offline checks:

```bash
python -m py_compile scripts/update_twelve_data.py
python -m unittest tests/test_twelve_data_pipeline.py -v
python scripts/validate_generated_data.py
node --check site/equity-data.js
node --check site/features/market-watch/market-watch-page.js
python scripts/audit_static_site.py
```

Credentialed local runs should use an environment variable, never a command-line argument:

```bash
export TWELVE_DATA_API_KEY='...'
python scripts/update_twelve_data.py --mode full --max-symbols 2
```

## Files owned by the integration

Hand-maintained:

```text
scripts/update_twelve_data.py
scripts/twelve_data_watchlist.json
schemas/equity-market-data.schema.json
site/features/market-watch/market-watch-page.js
site/features/market-watch/market-watch-page.css
.github/workflows/update-twelve-data.yml
```

Generated:

```text
site/equity-data.js
site/data/equity-market-data.json
```

Do not manually repair a live generated price. Fix the collector or symbol configuration, rerun, validate and retain the source failure honestly.
