# Contributing

## Principles

Changes should improve one or more of:

- data correctness;
- source transparency;
- analytical usefulness;
- operational reliability;
- usability and accessibility;
- maintainability.

Visual polish is valuable, but it must not hide stale, missing or uncertain data.

## Before starting

Read:

- `AGENTS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/RUNBOOK.md`
- `operating-model.md`

Determine whether the target file is hand-maintained or generated.

## Branch and pull request workflow

For code, collector or data-contract changes:

1. Create a focused branch.
2. Make the smallest coherent change.
3. Regenerate affected outputs.
4. Run validation.
5. Serve the site locally and inspect affected routes.
6. Open a pull request with evidence.

Suggested branch names:

```text
codex/fix-political-hydration
codex/add-cot-validation
codex/mobile-scenario-layout
```

## Pull request description

Include:

- problem;
- change;
- source/data implications;
- files generated;
- checks run;
- screenshots for visible changes;
- known limitations;
- deployment implications.

Example:

```markdown
## Problem
Political disclosure JSON was populated, but the browser did not load the generated module.

## Change
Added the generated data module to the documented load order and added a hydration smoke test.

## Validation
- `node --check` on all site scripts
- political JSON validation
- local `#trackers` test
- desktop and mobile screenshots

## Limitations
Some older House filings remain partial and are still labelled accordingly.
```

## Generated data

Do not hand-edit generated outputs as the primary solution.

Generated political files include:

```text
site/political-data.js
site/data/political-disclosures.json
site/data/political-disclosures-summary.json
```

Update the collector and regenerate.

If a generated file must be manually restored during an incident, document why and follow with a collector fix.

## Data-source changes

A new source requires:

- source authority assessment;
- access and licensing check;
- update frequency;
- schema and failure handling;
- freshness display;
- deduplication rule;
- validation rule;
- documentation update.

Do not scrape a logged-in product merely because an account is available. Prefer public official data or a permitted API.

## Frontend changes

The frontend is static and script order matters.

When adding JavaScript:

- identify required globals;
- load data before consumers;
- avoid duplicate event listeners;
- preserve direct hash routes;
- check desktop and mobile;
- do not cover navigation with fixed cards;
- expose an honest empty/error state.

## Collector changes

Collectors should:

- use explicit timeouts;
- use a descriptive user agent;
- validate response type;
- deduplicate with stable IDs;
- preserve existing verified history;
- avoid replacing populated data with empty output;
- write concise diagnostics;
- be safe to rerun.

## Validation commands

```bash
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check
python -m py_compile scripts/*.py
python -m json.tool site/data/political-disclosures.json >/dev/null
python -m json.tool site/data/political-disclosures-summary.json >/dev/null
node --check site/political-data.js
```

Then:

```bash
python -m http.server 8000 --directory site
```

## Review standards

Reject a change when it:

- fabricates missing values;
- removes source attribution;
- confuses trade date with filing date;
- attributes spouse activity to a politician personally;
- substitutes the wrong market benchmark;
- treats an external widget as an internal API;
- silently deletes verified history;
- claims deployment success without verification;
- introduces a secret into the public site or logs;
- changes research governance without documentation.

## Documentation expectation

Update documentation whenever a change alters:

- architecture;
- setup;
- workflow behaviour;
- generated files;
- data contracts;
- failure handling;
- research approval rules;
- operational commands.

The repository—not chat history—should remain the durable project record.
