# Core frontend modules

BR-05 introduces a small browser core while preserving the static, no-bundler architecture and every existing legacy global.

## Load order

`site/index.html` loads curated and generated data first, then:

1. `site/core/format.js`
2. `site/core/status.js`
3. `site/core/store.js`
4. `site/core/adapters.js`
5. `site/core/router.js`
6. existing renderer and enhancement scripts
7. `site/shell.js`, which starts initial routing while feature packages continue loading asynchronously

This order is a runtime contract. Data scripts must remain before the adapters, and the core must remain before current renderers.

## Namespace

All new APIs live under `window.MarketBriefCore`.

### Formatting

`MarketBriefCore.format` provides shared HTML escaping, number, signed-number, percentage, compact-number and date formatting. Existing feature scripts retain a local fallback implementation so a partial script-load failure does not blank unrelated views.

### Status

`MarketBriefCore.status` normalises current, delayed, partial, stale, error, unavailable and pending states. It does not infer freshness from a generic page timestamp.

### Store

`MarketBriefCore.store` is a small observable slice store. The current slices are:

- `research` — the existing `fallback` object;
- `official` — `window.freeMarketData`;
- `evidence` — `window.marketResearchData`;
- `scenarios` — `window.scenarioAssets` when available;
- `route` — the currently dispatched shared-router record.

The store retains object references rather than cloning them because current enrichment scripts intentionally add verified COT and energy context to the existing research object. Later packages can replace individual adapters without rewriting every renderer at once.

### Adapters

`MarketBriefCore.adapters` wraps existing globals and supplies safe empty shapes. BR-05 does not delete, rename or freeze legacy globals. Current views obtain their data through:

- `adapters.research()`;
- `adapters.official()`;
- `adapters.evidence()`;
- `adapters.scenarios()`;
- `adapters.views.activate()`.

### Router

`MarketBriefCore.router` owns initial hash dispatch and subsequent hash changes. Feature scripts register their current render functions rather than competing to interpret the initial route independently. Because feature packages are loaded asynchronously, a package that owns the current initial hash redispatches that hash after registration.

Supported route groups remain unchanged, including direct links such as:

- `#home`
- `#news`
- `#cot`
- `#rates`
- `#events`
- `#scenarios`
- `#trackers`
- `#product/<id>`

Navigation continues to use replacement history by default, matching the previous interface behaviour. Browser-originated hash changes and direct initial hashes dispatch through the same registry.

## Migration boundary

BR-05 is an adapter migration, not a feature redesign:

- existing renderer files remain in place;
- feature content and data contracts are unchanged;
- generated data files are unchanged;
- no framework, package install or bundler is introduced;
- later feature packages may move one domain at a time from legacy globals to dedicated versioned data modules.

## Validation

`tests/js/core-runtime.test.js` executes the core in a minimal browser-like Node context. It covers formatting, status normalisation, store publication, legacy adapter identity, view activation, direct initial hash dispatch, dynamic product routes, hash changes and unknown-route fallback.

`tests/test_core_modules.py` enforces script order, adapter use by existing renderers and registration of the existing route set.
