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
  assets: [{ id: 'gold', label: 'Gold', kind: 'asset', family: 'Metals' }],
};

load('core/impact-chips.js');
const chips = sandbox.window.MarketBriefCore.impactChips;

const linked = chips.chip({ assetId: 'gold', direction: 'up', tier: 'observed', detail: 'Netted "up" <fast>', href: '#cot' });
assert.ok(linked.startsWith('<a '), linked);
assert.ok(linked.includes('href="#cot"'));
assert.ok(linked.includes('impact-chip up tier-observed'));
assert.ok(linked.includes('↑'));
assert.ok(linked.includes('Gold'));
assert.ok(!linked.includes('<fast>'), 'detail must be HTML-escaped');

const span = chips.chip({ assetId: 'gold', direction: 'down', tier: 'ai', confidence: 'low', href: '' });
assert.ok(span.startsWith('<span '), span);
assert.ok(span.includes('tier-ai'));
assert.ok(span.includes('conf-low'));
assert.ok(span.includes('↓'));

const unknown = chips.chip({ assetId: 'mystery', direction: 'sideways', tier: 'nope', href: '' });
assert.ok(unknown.includes('impact-chip mixed tier-observed'), 'invalid enums fall back safely');
assert.ok(unknown.includes('mystery'), 'unknown asset falls back to its id');

const strip = chips.chipStrip([
  { assetId: 'gold', direction: 'up', tier: 'observed', href: '' },
  null,
  { assetId: 'gold', direction: 'watch', tier: 'observed', href: '' },
]);
assert.ok(strip.startsWith('<span class="impact-chips"'), 'strip must be inline-safe (span, not div)');
assert.strictEqual((strip.match(/impact-chip /g) || []).length, 2);
assert.strictEqual(chips.chipStrip([]), '');

// max clamps to a non-negative integer; {max:0} renders none (not the default 8), negatives fall back to default
const many = Array.from({ length: 12 }, () => ({ assetId: 'gold', direction: 'up', tier: 'observed', href: '' }));
assert.strictEqual((chips.chipStrip(many).match(/impact-chip /g) || []).length, 8, 'default cap is 8');
assert.strictEqual((chips.chipStrip(many, { max: 3 }).match(/impact-chip /g) || []).length, 3);
assert.strictEqual(chips.chipStrip(many, { max: 0 }), '', '{max:0} renders none, not the default 8');

console.log('impact-chips tests passed');
