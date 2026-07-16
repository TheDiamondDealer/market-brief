# Operations Runbook

## Purpose

This runbook covers local development, validation, scheduled collectors, deployment and common failure modes for the Market Brief Intelligence Console.

For the dated source and blocker state, read `docs/PROJECT-STATUS.md` first.

## Local development

From the repository root:

```bash
python -m http.server 8000 --directory site
```

Open:

```text
http://localhost:8000
```

Useful direct routes:

```text
http://localhost:8000/#home
http://localhost:8000/#today  (legacy redirect to #home)
http://localhost:8000/#news
http://localhost:8000/#cot
http://localhost:8000/#rates
http://localhost:8000/#official-feeds
http://localhost:8000/#crowd-expectations
http://localhost:8000/#scenarios
http://localhost:8000/#trackers
```

Use the browser console and network panel during smoke testing. A visually populated page can still contain script-order, hydration or stale-cache errors.

## Standard validation

Run the same sequence as `.github/workflows/validate.yml` for broad changes:

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

Do not judge success only from process exit codes. Inspect actual generated outputs, status counts, timestamps, source URLs and representative records.

## Browser smoke test

Verify at least:

- no browser-console exceptions;
- no unexpected 404s for generated modules;
- command centre renders;
- the Decision Console guide and conflict watch render, show source timestamps and keep official publications separate from conditional market pressure;
- `#trackers` shows imported counts rather than seeded zeros after a successful import;
- `#cot` renders current data and history when available;
- `#rates` renders mixed-frequency freshness correctly;
- `#official-feeds` shows current, failed and unavailable agencies honestly;
- `#crowd-expectations` loads read-only markets and source status;
- `#scenarios` works on desktop and mobile;
- representative asset and product-detail hashes work;
- sidebar and mobile navigation remain usable;
- generated-data failure states remain visible.

Use Playwright or another browser automation tool when available, but do not replace manual console and network inspection for material frontend changes.

## Political disclosure caches

Sanity checks:

```bash
python -m json.tool site/data/political-disclosures.json >/dev/null
python -m json.tool site/data/political-disclosures-summary.json >/dev/null
node --check site/political-data.js
```

Inspect counts:

```bash
python - <<'PY'
import json
from pathlib import Path

p = Path('site/data/political-disclosures-summary.json')
data = json.loads(p.read_text())
print('total trades:', data['totalTrades'])
for key, item in data['trackers'].items():
    print(key, item['trades'], item['holdings'], item['status'])
PY
```

Expected behaviour:

- Pelosi history is not zero after a successful historical import;
- a partial parser status is allowed and should list filing IDs;
- a source failure must not erase existing verified records;
- malformed page-header text must not appear as an asset;
- traded and filed dates remain separate;
- owner attribution remains exact.

## Running the political disclosure collector

Install the repository’s political dependencies:

```bash
python -m pip install --disable-pip-version-check --requirement requirements/political.txt
```

Run the hardened collector:

```bash
POLITICAL_DISCLOSURE_START_YEAR=2012 \
POLITICAL_DISCLOSURE_TIMEOUT=60 \
POLITICAL_REQUIRE_TRADES=1 \
python scripts/update_political_disclosures_strict.py
```

Then inspect:

```text
site/data/political-disclosures-summary.json
```

Inspect counts, latest filing dates, error lists and a sample of official source URLs.

## Adding a tracked politician

1. Add the person to tracker definitions in `site/politicians.js`.
2. Add aliases and chamber to `TRACKERS` in the political collector.
3. Preserve exact first/last-name matching rules to avoid importing a different person.
4. Run the collector locally.
5. Inspect transaction samples and source PDFs/pages.
6. Confirm generated data is loaded before rendering.
7. Confirm activity and stock-first views update.
8. Document source-specific parser limitations.

Do not add a tracker only to the interface. It is not operational until collector mapping, generated output and frontend hydration all work.

## Free official agency feeds

Primary workflow:

```text
.github/workflows/update-official-feeds.yml
```

Primary collector entry point:

```text
scripts/update_official_feeds_resilient.py
```

Validation:

```bash
python scripts/validate_official_feeds.py
```

Required secrets for the currently unavailable credentialed agencies:

```text
EIA_API_KEY
BEA_API_KEY
CENSUS_API_KEY
```

Optional:

```text
BLS_API_KEY
```

Missing keys must remain `unavailable`. They must not be placed in code, documentation examples containing real values, generated JSON or browser JavaScript.

### BLS shows partial with zero missing

This should fail the live workflow after the July 2026 audit.

Check:

1. whether all configured series were returned;
2. whether `detail` states `0 missing`;
3. whether advisory text was incorrectly treated as incompleteness;
4. whether an old generated cache is being served;
5. whether the hardened collector and live guard are present on the reviewed branch.

Complete observations may keep advisory text while remaining current.

### SEC EDGAR shows HTTP 403

The known GitHub-hosted-runner limitation is a provider access failure, not automatically a collector defect.

Check:

- descriptive user agent;
- pinned CIK identity;
- ticker confirmation;
- direct official submissions endpoint;
- throttling;
- current runner environment.

Do not replace official filings with an unverified third-party parser merely to populate the page. Test a controlled alternate outbound environment separately.

### EIA, BEA or Census unavailable

Check the associated Actions secret first.

After configuring a key:

1. manually dispatch the official-feed workflow;
2. inspect workflow output per agency;
3. verify source identity and units;
4. inspect generated records;
5. confirm Source Health;
6. confirm the page route;
7. do not describe the source as operational until the generated cache proves it.

### USGS current but has no mineral values

This is expected in the initial implementation. It tracks the annual official release and does not OCR PDF tables.

Individual values require a verified structured official data join.

## Crowd Expectations

Primary workflow:

```text
.github/workflows/update-crowd-expectations.yml
```

Collector entry point:

```text
scripts/update_crowd_expectations_hardened.py
```

Validation:

```bash
python scripts/validate_crowd_expectations.py
```

Expected boundaries:

- read-only public market data;
- no wallet;
- no authentication;
- no signing;
- no deposits;
- no order endpoints;
- no trading recommendation claim.

### Crowd page is empty

Check:

1. `site/data/crowd-expectations.json` exists and validates;
2. collection status and error;
3. the feature loader includes the data, health, page, command and asset modules;
4. `#crowd-expectations` route exists;
5. browser network requests for the JSON succeed;
6. no source-health event recursion is occurring;
7. the live cache is not stale behind a deployment.

A successful empty selection should be rejected by the collector.

### Crowd list is dominated by one event family

Check the balancing stage:

- it runs after all relevance, liquidity, volume and quality filters;
- category reserves do not introduce unqualified markets;
- category cap is enforced;
- event-family cap is enforced;
- category counts and shocks are rebuilt from the final selection.

A zero category remains acceptable when no qualifying market passes the unchanged thresholds.

### Wrong asset attached to a market

Asset mapping must use event wording.

Examples:

- WTI price event → WTI;
- Brent event → Brent;
- broad oil-supply or Hormuz event may affect both Brent and WTI;
- gas, copper, gold, silver and rare earths require relevant event language.

Do not restore broad category-wide asset contamination.

### Resolution source appears missing

Check:

1. direct `resolutionSource` field;
2. event metadata;
3. official URL in the market rules.

A market without an identifiable source cannot receive Grade A.

### Midpoint used on a wide book

Calculate:

```text
spread = bestAsk - bestBid
```

Do not allow a conflicting provider spread field to override the actual bid and ask.

## Private Twelve Data feed

The private feed must remain disabled while the repository or deployed site is public.

Expected public state:

- mode: disabled;
- status: unavailable;
- no prices;
- no latest observations;
- explanatory privacy/licensing error.

Never test activation with a real key on the public branch.

Activation checklist:

- [ ] repository private;
- [ ] Cloudflare Pages deployed;
- [ ] Cloudflare Access protects custom domain;
- [ ] Cloudflare Access protects generated `pages.dev` origin;
- [ ] public GitHub Pages origin disabled or removed;
- [ ] provider plan reviewed for intended internal use;
- [ ] `TWELVE_DATA_API_KEY` stored in Actions Secrets;
- [ ] private-access gate enabled after independent verification;
- [ ] private-market-data gate enabled after independent verification;
- [ ] generated output inspected before deployment;
- [ ] no licensed data appears in public Git history or artifacts.

### False freshness check

A failed quote must not be masked by retained history.

Verify:

- fresh quote count;
- fresh history count;
- retained stale count;
- collection status;
- `lastSuccessfulAt` only advances after a fresh accepted response.

## Source Health troubleshooting

Source Health extensions must be idempotent.

Symptoms of recursion include:

- repeated `marketbrief:source-health` events;
- unnecessary store writes;
- high CPU use;
- continuous rerendering;
- counts that oscillate or duplicate.

Verify each extension:

- filters its own family from the base records;
- constructs expected records;
- compares existing and expected records;
- returns without writing when already injected;
- dispatches only after a genuine change.

## Deployment

GitHub Pages deploys the `site/` directory through:

```text
.github/workflows/deploy-pages.yml
```

A commit touching `site/**` should trigger deployment.

After deployment:

1. inspect the workflow conclusion;
2. open the live URL;
3. hard refresh or use a private window;
4. check the affected route directly;
5. inspect developer tools for 404s and JavaScript errors;
6. verify generated timestamp or expected behaviour.

A commit to `main` is not proof that Pages is live.

Documentation-only changes may not trigger a Pages deployment, which is expected.

## Workflow troubleshooting

### Political trackers show zero

Check in this order:

1. Does the summary JSON contain non-zero counts?
2. Does `site/political-data.js` exist and pass syntax validation?
3. Is the generated module loaded before tracker rendering, or through the documented loader?
4. Does the browser network panel show a 404?
5. Does the console show fallback or initialization errors?
6. Is Pages serving an older deployment?

If JSON is populated but the UI shows zero, the likely defect is loading or hydration rather than source import.

### Political importer fails

Inspect:

- House source errors;
- Senate source errors;
- parsing errors;
- failing filing ID and official URL;
- actual response content type;
- older PDF layout requirements.

Never solve a parser error by silently dropping the filing.

### Malformed political asset names

Reject rows containing:

- null characters;
- page-header identity text;
- district labels;
- table headers inside the asset;
- non-statutory stray prices.

Required response:

1. reject malformed row;
2. reparse using fallback;
3. preserve valid history;
4. strengthen validation;
5. rerun and inspect summary.

### COT page has current values but no history chart

Check:

1. generated records contain history arrays;
2. intended primary contract was selected;
3. chart script is loaded;
4. report date is current;
5. unsafe mappings were not substituted.

### Conflict watch is stale or empty

Check `.github/workflows/update-conflict-watch.yml`, then inspect `site/data/conflict-watch.json` for collection and per-source status. A feed failure must retain only previously verified items from that source and label them `stale-retained`. An empty successful feed can be legitimate when no title matches the 14-day market-relevance filter; do not weaken the filter merely to populate the panel. UKMTO warnings remain a direct manual primary-source link rather than scraped data.

### Wrong COT contract selected

Compare the generated code, complete official market-and-exchange name, report family and exchange with `scripts/cot_contracts.json`. A micro, mini, ultra, index, financial or cross-rate contract is valid only when it is the exact named registry product. Never use one as a substitute for another intended benchmark, and always reject a similarly named contract on the wrong exchange.

Prefer unavailable status over a misleading substitute. For partial refresh failures, confirm retained rows carry `dataState: stale-retained` and the source-status detail identifies the affected IDs.

### Rates page is stale

Check generated source status and each series’ last observation date.

Remember:

- official daily series may update after market close;
- weekends and holidays create expected gaps;
- different series can have different latest dates.

Do not stamp the whole dashboard current because one series updated.

### Scenario Lab chart is blank

Check:

- browser content blockers;
- TradingView script availability;
- widget container dimensions;
- symbol validity;
- console network or CSP errors.

The project’s scenario explanation should still function independently from TradingView.

### Sidebar or mobile regression

Test:

- desktop above 1100 px;
- tablet around 800–1000 px;
- mobile below 780 px;
- long navigation lists;
- sticky panels;
- chart height;
- footer and disclaimers.

Avoid fixed overlays that cover navigation items.

## Data recovery

Generated history is committed to Git.

Recovery normally means:

1. identify last known-good generated-data commit;
2. compare collector or schema change that followed;
3. restore generated files only when safe regeneration is unavailable;
4. fix source collector;
5. regenerate and validate;
6. avoid force-pushing over useful history.

## Safe rollback

For a frontend regression:

1. revert the specific feature commit;
2. preserve newer compatible generated-data commits;
3. rerun validation;
4. deploy;
5. verify the affected route.

For a collector regression:

1. disable scheduled workflow if it could corrupt data;
2. retain last verified cache;
3. fix and test against fixtures and official samples;
4. re-enable only after validation.

## Release checklist

Before declaring a feature complete:

- [ ] source of truth identified;
- [ ] generated-file boundaries respected;
- [ ] complete validation passes;
- [ ] actual generated output inspected;
- [ ] local site tested;
- [ ] direct route tested;
- [ ] desktop and mobile checked;
- [ ] no secret added;
- [ ] privacy and licensing boundaries preserved;
- [ ] partial/stale/failed/unavailable states remain honest;
- [ ] documentation updated;
- [ ] deployment triggered where applicable;
- [ ] live deployment independently verified or explicitly described as unverified.
