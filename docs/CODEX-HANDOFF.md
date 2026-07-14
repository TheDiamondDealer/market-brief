# Codex Handoff Guide

## Is the GitHub repository enough?

The repository is the correct handoff boundary, but a bare repository is not enough for reliable work. Codex also needs:

- repository access;
- a reproducible environment;
- project-specific instructions;
- setup and validation commands;
- generated-file boundaries;
- known limitations and approval rules.

This repository now contains those items in:

- `AGENTS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/RUNBOOK.md`
- `CONTRIBUTING.md`
- `operating-model.md`

## Codex cloud setup

1. Open Codex and connect the GitHub account that can access `TheDiamondDealer/market-brief`.
2. Grant Codex access to this repository.
3. Create an environment rooted at the repository.
4. Use Python 3.12 or later and a current Node.js release.
5. No frontend package installation is required.
6. Allow internet access only for tasks that need official public sources or widget verification.
7. Do not add passwords or personal website credentials to the environment.

Suggested environment setup command:

```bash
python -m pip install --disable-pip-version-check requests beautifulsoup4 pdfplumber
python -m py_compile scripts/*.py
find site -maxdepth 1 -name '*.js' -print0 | xargs -0 -n1 node --check
```

No secret is required for the current public data collectors.

## Confirm Codex loaded the instructions

From the repository root, ask:

> List the instruction files you loaded, summarize the non-negotiable data rules, and identify which files are generated.

Expected result:

- Codex identifies `AGENTS.md`.
- Codex explains that political trade date and filing date remain separate.
- Codex identifies generated political-data files.
- Codex mentions the monthly approval boundary.
- Codex does not propose using pasted website passwords.

## Recommended first task

Use an audit-only task before asking Codex to change code:

> Read `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md`, `operating-model.md` and all workflows. Do not modify files. Report: architecture, current collectors, generated files, script load order, data freshness, failing or partial sources, deployment path, security risks and the five highest-priority technical debts. Cite file paths and line numbers.

This gives Codex a fresh understanding based on the repository rather than inherited chat history.

## Recommended second task

> Run the documented syntax and data validations. Serve the site locally. Check `#home`, `#cot`, `#rates`, `#scenarios` and `#trackers`. Confirm that populated political JSON is actually hydrated into the live UI. Fix only verified defects, then summarize tests and limitations.

## Good task format

Codex performs better when a task includes:

1. **Outcome** — what should be true when finished.
2. **Scope** — files or features included.
3. **Constraints** — data and security rules.
4. **Evidence** — tests or screenshots required.
5. **Delivery** — direct commit, branch or pull request.

Example:

> Add a tracked-politician detail chart showing purchases and sales by month. Use only imported official disclosure data. Preserve spouse attribution and filing lag. Do not modify generated files manually; update the rendering layer. Run all JavaScript checks, serve locally, verify `#trackers` at desktop and mobile widths, and open a pull request with screenshots and limitations.

## Suggested working mode

For meaningful changes:

- ask Codex to create a branch;
- request a pull request rather than pushing directly to `main`;
- review the diff and workflow impact;
- merge only after validation;
- let Pages deploy from `main`.

For small documentation corrections, a direct commit can be acceptable.

## High-value starter backlog

### Reliability

- Add a browser smoke test for all major hash routes.
- Add a script-order/data-hydration test.
- Add schema validation for generated market and political data.
- Stop timestamp-only generated commits when no substantive data changed.
- Add workflow summaries that clearly show imported, retained, partial and failed counts.

### Political data

- Incorporate annual holdings baselines.
- Improve parser coverage for older House PTR layouts.
- Add option-specific exposure rules.
- Add a review queue for malformed or low-confidence rows.
- Build Trump executive financial-disclosure ingestion separately from policy tracking.

### Market data

- Finish COT contract-map tests.
- Add per-series freshness rules to rates.
- Expand official physical-market evidence for oil, gas and metals.
- Add event-reaction persistence and backtesting with strict point-in-time rules.

### Frontend

- Replace fragile global script ordering with ES modules or a small build system only after a documented migration plan.
- Add route-level error boundaries.
- Improve mobile tables.
- Add accessible chart descriptions and keyboard navigation.

## Prompts to avoid

Avoid vague prompts such as:

> Make the dashboard better.

Avoid unsafe prompts such as:

> Fill missing political trades from whatever source looks close.

Avoid prompts that confuse disclosure and execution:

> Calculate returns from the hidden trade date as if investors knew immediately.

Better:

> Compare performance from the public filing date and clearly label the result as a hypothetical delayed-disclosure backtest.

## Required review questions

Before accepting Codex work, ask:

- Did it change a generated file manually?
- Did it preserve previously verified history?
- Did it fabricate or infer missing data?
- Did it keep benchmark and regional distinctions?
- Did it expose partial/stale states?
- Did it run the documented checks?
- Did it verify the live page or only trigger deployment?
- Did it update documentation when behaviour changed?

## Ownership transfer

The repository should remain the durable memory. Important decisions made in chat should be converted into one of:

- `AGENTS.md` for standing engineering rules;
- `docs/ARCHITECTURE.md` for system design;
- `docs/RUNBOOK.md` for operations;
- `operating-model.md` for research governance;
- a GitHub issue for unfinished work;
- a pull request description for a specific change.

Do not rely on a long conversation as the only record of project behaviour.
