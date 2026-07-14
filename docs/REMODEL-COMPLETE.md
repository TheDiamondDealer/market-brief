# Mandatory Remodel Completion Record

Completion date: 14 July 2026

## Scope completed

The mandatory remodel packages BR-01 through BR-19 are implemented.

### Foundation and trust

- BR-01 to BR-05 established repository, shell, schema and workflow foundations.
- BR-06 established exact CFTC contract identity and explicit unavailable markets.
- BR-07 delivered the COT Positioning workspace.
- BR-08 added the durable political filing ledger.
- BR-09 split political history into lazy annual files and search indexes.
- BR-10 delivered Political Flow and direct profiles.
- BR-11 added the versioned news-impact contract.
- BR-12 delivered the Impact Feed.

### Decision console

- BR-13 delivered per-asset decision workspaces.
- BR-14 rebuilt the Command Centre without the former composite-score gauge.
- BR-15 added the Melbourne-time calendar and no-look-ahead reaction lifecycle.
- BR-16 delivered the grouped Macro Monitor.
- BR-17 unified freshness and source health.

### Production release

- BR-18 added recursive syntax checks, static accessibility/performance auditing, payload budgets and viewport hardening.
- BR-19 aligned architecture, runbooks, source documentation, deployment validation, route verification and compatibility cleanup.

## Mandatory route contract

- `#home`
- `#news`
- `#news/<impact-id>`
- `#cot`
- `#trackers`
- `#trackers/<politician-id>`
- `#asset/<asset-id>`
- `#product/<asset-id>` compatibility alias
- `#events`
- `#calendar`
- `#calendar/<event-id>`
- `#rates`
- `#macro`
- `#sources`
- `#source-health`

`scripts/verify_release_routes.py` enforces these routes and generated-file ownership.

## Non-negotiable trust outcomes

- COT rows require exact verified identity; WTI, Brent, US gas and UK gas remain unavailable rather than substituted.
- Political Flow preserves actual trade date, filing date, disclosed owner/account, statutory range and official filing URL.
- Failed and partial political filings remain visible and retryable.
- Curated news remains delayed research and does not claim live-wire status.
- Unknown impact horizon, confidence, confirmation or invalidation remains unknown.
- Calendar consensus remains `Not sourced` without an approved provider.
- Macro series retain individual observation dates.
- Source failures are independent; one current source cannot conceal another stale source.
- No hidden composite risk score is used by the remodelled Command Centre.
- Generated files remain collector-owned.

## Items intentionally not completed

### BR-20 — optional feed/backend expansion

Not started. It requires explicit approval and may include licensed news, licensed prices, consensus feeds, rate probabilities, accounts, alerts, watchlists, a database, queues or secret-bearing APIs.

### Owner-only repository protection

GitHub issue #4 remains the source of truth for activating and testing the `main` protection ruleset. Code completion does not imply that the owner-side ruleset is active.

## Release verification rule

A successful Pages workflow means GitHub deployed an artifact. It is not the same as independently observing the new revision at the public URL. Release notes must state these facts separately.
