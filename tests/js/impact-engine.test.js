'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const sandbox = { window: {} };
vm.createContext(sandbox);

function load(relative) {
  const file = path.join(__dirname, '..', '..', 'site', relative);
  vm.runInContext(fs.readFileSync(file, 'utf8'), sandbox, { filename: relative });
}

sandbox.window.marketAssetBoard = {
  schemaVersion: 1,
  assets: [
    { id: 'gold', label: 'Gold', kind: 'asset', family: 'Metals', cotId: 'gold', crowdAliases: ['gold'] },
    { id: 'us10y', label: 'US 10Y yield', kind: 'asset', family: 'Rates/FX', rateId: 'DGS10', cotId: 'us10y-cot' },
    { id: 'dxy', label: 'US dollar', kind: 'asset', family: 'Rates/FX', rateId: 'DTWEXBGS' },
    { id: 'risk-assets', label: 'Risk assets', kind: 'theme', family: 'Themes', rateId: 'BAMLH0A0HYM2', rateInvert: true },
    { id: 'inflation-risk', label: 'Inflation risk', kind: 'theme', family: 'Themes' },
    { id: 'semis', label: 'Semiconductors', kind: 'theme', family: 'Themes', etfIds: ['smh', 'soxx'], memberTickers: ['nvda'] },
    { id: 'nbp', label: 'UK gas (NBP)', kind: 'asset', family: 'Energy' },
  ],
  officialSeriesRules: [
    { seriesId: 'CUSR0000SA0', seriesName: 'US CPI all items', assetId: 'inflation-risk', rule: 'sign-of-change' },
  ],
};

load('core/impact-engine.js');
const engine = sandbox.window.MarketBriefCore.impactEngine;

// --- netPressure rule (spec §4.4) ---
assert.strictEqual(engine.netPressure({ up: 0, down: 0, mixed: 0 }), 'quiet');
assert.strictEqual(engine.netPressure({ up: 1, down: 0, mixed: 0 }), 'up');
assert.strictEqual(engine.netPressure({ up: 2, down: 1, mixed: 0 }), 'up');       // exactly 2:1
assert.strictEqual(engine.netPressure({ up: 3, down: 2, mixed: 0 }), 'contested');
assert.strictEqual(engine.netPressure({ up: 0, down: 4, mixed: 1 }), 'down');
assert.strictEqual(engine.netPressure({ up: 0, down: 0, mixed: 2 }), 'contested'); // evidence exists, direction unresolved

// --- COT derivation ---
const cotSignals = engine.deriveCotSignals({
  cot: [
    { id: 'gold', weekChange: 5200, category: 'Managed money', reportDate: '2026-07-07', name: 'Gold', contract: { exchange: 'COMMODITY EXCHANGE INC.' } },
    { id: 'silver', weekChange: -900, category: 'Managed money', reportDate: '2026-07-07' }, // unmapped in fixture board
    { id: 'us10y-cot', weekChange: 0, category: 'Leveraged funds', reportDate: '2026-07-07' }, // MAPPED but zero change — must be suppressed
  ],
});
assert.strictEqual(cotSignals.length, 1);
assert.deepStrictEqual(
  { assetId: cotSignals[0].assetId, direction: cotSignals[0].direction, tier: cotSignals[0].tier, source: cotSignals[0].source },
  { assetId: 'gold', direction: 'up', tier: 'observed', source: 'cot' });
assert.ok(cotSignals[0].detail.includes('COMMODITY EXCHANGE INC.'), 'COT chip detail must name the exact contract/exchange (provenance)');

// --- rate derivation with inversion ---
const rateSignals = engine.deriveRateSignals({
  rates: [
    { id: 'DGS10', name: 'US 10-year Treasury', change: -0.06, changeBps: -6, unit: '%', date: '2026-07-14', value: 4.2 },
    { id: 'BAMLH0A0HYM2', name: 'US high-yield spread', change: 0.11, changeBps: 11, unit: '%', date: '2026-07-14', value: 3.1 },
    { id: 'DTWEXBGS', name: 'US broad dollar index', change: -0.31, changeBps: null, unit: 'index', date: '2026-07-14', value: 119.2 }, // real shape: null changeBps
    { id: 'SOFR', name: 'SOFR', change: 0.01, changeBps: 1, unit: '%', date: '2026-07-14', value: 4.3 },
  ],
});
assert.strictEqual(rateSignals.length, 3);
const us10y = rateSignals.find((s) => s.assetId === 'us10y');
const risk = rateSignals.find((s) => s.assetId === 'risk-assets');
const dxy = rateSignals.find((s) => s.assetId === 'dxy');
assert.strictEqual(us10y.direction, 'down');
assert.strictEqual(risk.direction, 'down'); // spread widened → inverted
assert.strictEqual(dxy.direction, 'down');
assert.ok(!dxy.detail.includes('0bps'), 'null changeBps must never render as an invented 0bps');
assert.ok(dxy.detail.includes('0.31 index'), 'null changeBps falls back to raw change + unit');
assert.strictEqual(us10y.status, 'current'); // no sourceStatus supplied -> defaults current
const staleRates = engine.deriveRateSignals({
  rates: [{ id: 'DGS10', name: 'US 10-year Treasury', change: -0.06, changeBps: -6, unit: '%', date: '2026-07-14' }],
  sourceStatus: [{ source: 'FRED / Federal Reserve data', status: 'stale-fallback' }],
});
assert.strictEqual(staleRates[0].status, 'stale-fallback'); // rate signals propagate the FRED source status, never assert current

// --- crowd derivation: attention only, threshold 5pts ---
const crowdSignals = engine.deriveCrowdSignals({
  markets: [
    { assets: ['gold'], change7dPoints: 8.4, question: 'Gold above $2,600 by August?' },
    { assets: ['gold'], change7dPoints: 2.0, question: 'Below threshold' },
    { assets: ['gold'], change7dPoints: null, question: 'No history' },
  ],
});
assert.strictEqual(crowdSignals.length, 1);
assert.strictEqual(crowdSignals[0].direction, 'mixed');
assert.strictEqual(crowdSignals[0].status, 'current'); // market without status defaults to current
const staleCrowd = engine.deriveCrowdSignals({
  markets: [{ assets: ['gold'], change7dPoints: 8.4, status: 'stale', question: 'Stale market' }],
});
assert.strictEqual(staleCrowd[0].status, 'stale'); // market.status propagates, not hard-coded current

// --- ETF derivation respects row status ---
const etfSignals = engine.deriveEtfSignals({
  watchlist: [
    { id: 'smh', status: 'current', percentChange: 1.42, name: 'VanEck Semiconductor ETF' },
    { id: 'soxx', status: 'unavailable', percentChange: 2.0, name: 'iShares Semiconductor ETF' }, // non-current status must be excluded even with a numeric move
  ],
});
assert.strictEqual(etfSignals.length, 1);
assert.strictEqual(etfSignals[0].assetId, 'semis');
assert.strictEqual(etfSignals[0].direction, 'up');

// --- collect: every board asset present, quiet included ---
const collected = engine.collectDeterministicSignals({
  freeData: { cot: [{ id: 'gold', weekChange: 5200, category: 'Managed money', reportDate: '2026-07-07' }], rates: [] },
  crowdData: { markets: [] },
  equityData: { watchlist: [] },
});
assert.strictEqual(collected.gold.net, 'up');
// Spread into a host-realm object: vm-realm objects fail deepStrictEqual's prototype identity check.
assert.deepStrictEqual({ ...collected.gold.counts }, { up: 1, down: 0, mixed: 0 });
assert.strictEqual(collected.nbp.net, 'quiet');
assert.strictEqual(collected.nbp.signals.length, 0);

// --- status propagation: stale-retained COT rows stay distinguishable ---
const staleCot = engine.deriveCotSignals({
  cot: [{ id: 'gold', weekChange: 3100, category: 'Managed money', reportDate: '2026-07-07', dataState: 'stale-retained' }],
});
assert.strictEqual(staleCot[0].status, 'stale-retained');
assert.strictEqual(cotSignals[0].status, 'current'); // rows without dataState default to current

// --- windowed aggregation: out-of-window signals never count as pressure ---
const windowed = engine.collectDeterministicSignals({
  freeData: { cot: [{ id: 'gold', weekChange: 5200, category: 'Managed money', reportDate: '2026-07-07' }], rates: [] },
  crowdData: { markets: [] },
  equityData: { watchlist: [] },
}, { since: '2026-07-10' });
assert.strictEqual(windowed.gold.net, 'quiet'); // 7 Jul report is outside a 10 Jul window
assert.strictEqual(windowed.gold.signals.length, 0);

// --- BLS print rules (deterministic, registry-driven) ---
const blsSignals = engine.deriveBlsPrintSignals({
  status: 'current',
  records: [
    { id: 'CUSR0000SA0', name: 'US CPI all items', change: -1.411, unit: 'index', observedAt: '2026-06-01', period: '2026-06' },
    { id: 'CES0000000001', name: 'US nonfarm payrolls', change: 57.0, unit: 'thousands', observedAt: '2026-06-01' }, // no rule — skipped
    { id: 'WPSFD4', name: 'US PPI final demand', change: 0, unit: 'index', observedAt: '2026-06-01' }, // rule exists in real registry but zero change — and unmapped in this fixture
  ],
});
assert.strictEqual(blsSignals.length, 1);
assert.strictEqual(blsSignals[0].assetId, 'inflation-risk');
assert.strictEqual(blsSignals[0].direction, 'down');
assert.ok(blsSignals[0].detail.includes('CPI'));

// --- lookups ---
assert.strictEqual(engine.assetByCotId('gold').id, 'gold');
assert.strictEqual(engine.assetsByRateId('BAMLH0A0HYM2')[0].id, 'risk-assets');
assert.strictEqual(engine.themeForTicker('nvda').id, 'semis');
assert.strictEqual(engine.themeForTicker('fig'), null);

console.log('impact-engine tests passed');
