'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..', '..');
const slices = new Map();
const official = {
  generatedAtUtc: '2026-07-14T11:35:36+00:00',
  generatedAt: '14 July 2026, 9:35 PM AEST',
  rates: [
    { id: 'CURRENT', name: 'Current series', unit: '%', date: '2026-07-10', value: 4, sourceUrl: 'https://example.com/current' },
    { id: 'STALE', name: 'Stale series', unit: '%', date: '2026-05-01', value: 3, sourceUrl: 'https://example.com/stale' }
  ],
  cot: [{ id: 'gold', name: 'Gold', reportDate: '2026-07-07', category: 'Managed Money', sourceUrl: 'https://example.com/cot', contract: { identityStatus: 'verified', cftcContractCode: '088691', category: 'Managed Money' } }],
  sourceStatus: [{ id: 'fred', source: 'FRED', status: 'current', detail: 'Official cache loaded.' }]
};
const political = {
  generatedAt: '2026-07-14T09:00:00+10:00', totalTrades: 100,
  sourceStatus: { filingLedger: { filings: 50, retryable: 1 } }
};
const impact = { generatedAt: '14 July 2026', sourceMode: 'curated-delayed', items: [{}] };
const calendar = { generatedAt: '14 July 2026', timezone: 'Australia/Melbourne', events: [{}] };
const evidence = { updated: '14 July 2026', physicalChecklists: { oil: {} } };
const research = { generatedAt: '1 July 2026', regime: { name: 'Test regime' } };
const store = {
  getSlice: (name) => slices.get(name),
  setSlice: (name, value) => { slices.set(name, value); return value; },
  subscribe: () => () => {}
};
class CustomEvent { constructor(type, options = {}) { this.type = type; this.detail = options.detail; } }
const windowObject = {
  MarketBriefCore: {
    adapters: { official: () => official, evidence: () => evidence, research: () => research },
    impact: { get: () => impact }, calendar: { get: () => calendar }, store
  },
  freeMarketData: official,
  politicalDisclosureSummary: political,
  addEventListener: () => {},
  dispatchEvent: () => true,
  setTimeout: (callback) => callback()
};
windowObject.window = windowObject;
const context = vm.createContext({ console, CustomEvent, Date, fallback: research, window: windowObject });
vm.runInContext(fs.readFileSync(path.join(root, 'site/core/freshness.js'), 'utf8'), context, { filename: 'freshness.js' });

const registry = windowObject.marketSourceHealth;
assert.equal(registry.schemaVersion, 1);
assert.deepEqual(Array.from(registry.statuses), ['current', 'delayed', 'stale', 'failed', 'unavailable', 'partial', 'unknown']);
const byId = Object.fromEntries(Array.from(registry.records, (record) => [record.id, record]));
assert.equal(byId['macro:CURRENT'].status, 'current');
assert.equal(byId['macro:STALE'].status, 'stale', 'one stale series must remain stale even when the FRED pipeline is current');
assert.equal(byId['cot:gold'].status, 'current');
assert.equal(byId['political:filing-ledger'].status, 'partial');
assert.equal(byId['macro:CURRENT'].sourceObservedAt, '2026-07-10T00:00:00.000Z');
assert.equal(byId['macro:CURRENT'].collectedAt, '2026-07-14T11:35:36.000Z');
assert.equal(byId['macro:CURRENT'].expectedCadence, 'Daily business-day observation');
assert.equal(windowObject.MarketBriefCore.freshness.forId('macro:STALE').name, 'Stale series');
assert.ok(windowObject.MarketBriefCore.freshness.failures().some((record) => record.id === 'macro:STALE'));
assert.ok(windowObject.MarketBriefCore.freshness.failures().some((record) => record.id === 'political:filing-ledger'));
assert.ok(windowObject.MarketBriefCore.freshness.ageDays('2099-01-01T00:00:00Z') < 0);
assert.equal(
  windowObject.MarketBriefCore.freshness.cadenceStatus('2099-01-01T00:00:00Z', 5),
  'unknown',
  'future-dated observations outside tolerance must never be marked current'
);
assert.equal(slices.get('sourceHealth'), registry);
console.log('BR-17 freshness registry tests passed');
