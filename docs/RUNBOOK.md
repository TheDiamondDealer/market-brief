# Operations Runbook

## Purpose

This runbook covers local development, validation, scheduled collectors, deployment and common failure modes for the Market Brief Intelligence Console.

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
http://localhost:8000/#news
http://localhost:8000/#cot
http://localhost:8000/#rates
http://localhost:8000/#scenarios
http://localhost:8000/#trackers
```

Use the browser console during smoke testing. A visually populated page can still contain script-order errors.

## Standard validation

### JavaScript

```bash
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check
```

### Python

```bash
python -m py_compile scripts/*.py
```

### Political disclosure caches

```bash
python -m json.tool site/data/political-disclosures.json >/dev/null
python -m json.tool site/data/political-disclosures-summary.json >/dev/null
node --check site/political-data.js
```

### Political data sanity

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

- Pelosi history is not zero after a successful historical import.
- A partial parser status is allowed and should list filing IDs.
- A source failure must not erase existing verified records.
- Malformed page-header text must not appear as an asset.

## Running the political disclosure collector

Install dependencies:

```bash
python -m pip install requests beautifulsoup4 pdfplumber
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

Do not judge success only from the process exit code. Inspect counts, latest filing dates, error lists and a sample of source URLs.

## Adding a tracked politician

1. Add the person to the tracker definitions in `site/politicians.js`.
2. Add the person’s aliases and chamber to `TRACKERS` in `scripts/update_political_disclosures.py`.
3. Preserve exact first/last-name matching rules to avoid importing a different person.
4. Run the collector locally.
5. Inspect transaction samples and source PDFs/pages.
6. Confirm the generated tracker is loaded into the browser.
7. Confirm the activity board and stock-first search update.
8. Document any source-specific parser limitation.

Do not add a tracker only to the interface; a tracker is not operational until its collector mapping and generated data path work.

## Deployment

GitHub Pages deploys the `site/` directory through:

```text
.github/workflows/deploy-pages.yml
```

A commit touching `site/**` should trigger deployment.

After a deployment:

1. Wait for the Pages workflow.
2. Open the live URL.
3. Hard refresh with `Ctrl+F5` or use a private window.
4. Check the affected route directly.
5. Open developer tools and confirm no 404 or JavaScript errors.
6. Verify the page displays the new generated timestamp or expected behaviour.

A commit to `main` is not proof that Pages is live.

## Workflow troubleshooting

## Political trackers show zero

Check in this order:

1. Does `site/data/political-disclosures-summary.json` contain non-zero counts?
2. Does `site/political-data.js` exist and pass `node --check`?
3. Is the generated data module loaded by the page before tracker rendering, or is a documented loader used?
4. Does the browser network panel show a 404 for `political-data.js`?
5. Does the console show `fallback` or tracker initialization errors?
6. Is Pages serving an older cached deployment?

If JSON has populated data but the UI shows zero, the problem is almost certainly frontend loading/hydration, not the source importer.

## Political importer fails

Inspect:

- `sourceStatus.house.errors`
- `sourceStatus.senate.errors`
- `sourceStatus.parsing.errors`
- the failing filing ID and official URL
- whether the response is really a PDF/HTML page
- whether an old PDF layout needs another parser fallback

Never solve a parser error by dropping the filing silently.

## Malformed political asset names

Symptoms include:

- null characters;
- `Name: Hon.`;
- `State/District:`;
- table header text inside the asset;
- a non-statutory amount such as a stray single price.

Required response:

1. reject the malformed row;
2. reparse the filing using the fallback parser;
3. preserve other valid historical rows;
4. add or strengthen validation;
5. rerun the collector and inspect the summary.

## COT page has current values but no history chart

Check:

1. the generated COT records contain `history52` arrays;
2. the intended primary contract was selected;
3. the chart script is loaded;
4. the report date is current;
5. stale or unsafe contract mappings were not substituted.

A current balance card can render from one observation while the historical line chart still lacks data.

## Wrong COT contract selected

Reject variants such as:

- micro;
- mini;
- ultra;
- index;
- financial;
- cross-rate;
- a similarly named contract on the wrong exchange.

Prefer unavailable status over a misleading substitute.

## Rates page is stale

Check the generated source-status data and the last successful observation date.

Remember:

- official daily series may update after the market close;
- weekends and holidays create expected gaps;
- different series can have different latest dates.

Do not stamp the whole dashboard current merely because one series updated.

## Scenario Lab chart is blank

Check:

- browser content blockers;
- TradingView script availability;
- widget container dimensions;
- symbol validity;
- console network/CSP errors.

The project’s scenario explanation should still function with a verified user-entered current price even if TradingView is unavailable.

## Sidebar or mobile layout regression

Test:

- desktop width above 1100 px;
- tablet around 800–1000 px;
- mobile below 780 px;
- long navigation lists;
- sticky panels;
- chart height;
- footer and disclaimers.

Avoid fixed overlays that cover navigation items.

## Data recovery

Generated history is committed to Git, so recovery normally means:

1. identify the last known-good generated-data commit;
2. compare the collector/code change that followed;
3. restore generated files only if the source pipeline cannot safely regenerate them;
4. fix the collector;
5. rerun and validate;
6. avoid force-pushing over useful history.

## Safe rollback

For a frontend regression:

1. revert the specific feature commit;
2. preserve newer generated-data commits where compatible;
3. rerun JavaScript checks;
4. deploy;
5. verify the affected hash route.

For a collector regression:

1. stop or disable the scheduled workflow if it could corrupt data;
2. retain the last verified cache;
3. fix and test the collector against known filings;
4. re-enable scheduling after validation.

## Release checklist

Before declaring a feature complete:

- [ ] Source of truth identified.
- [ ] Generated-file boundaries respected.
- [ ] JavaScript syntax passes.
- [ ] Python syntax passes.
- [ ] JSON validates.
- [ ] Local site tested.
- [ ] Direct route tested.
- [ ] Desktop and mobile checked.
- [ ] No secret added.
- [ ] Partial/stale states remain honest.
- [ ] Documentation updated.
- [ ] Deployment triggered.
- [ ] Live deployment independently verified or explicitly described as unverified.
