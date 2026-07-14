'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..', '..');
const slices = new Map();
const fallback = {
  generatedAt: '13 July 2026, Melbourne close',
  newsFeed: {
    asOf: '13 July 2026, Melbourne close',
    items: [{
      id: 'legacy-item',
      category: 'Precious',
      impact: 'High',
      status: 'Price-confirmed',
      time: '13 Jul 2026',
      headline: 'Legacy headline remains unchanged',
      summary: 'Legacy summary remains unchanged.',
      source: 'Reuters',
      sourceUrl: 'https://example.com/reuters',
      assets: [{ name: 'Gold', direction: 'down', reason: 'Higher yields pressure gold.' }],
      channels: [
        ['Rates', 'Yields remain the first-order channel.'],
        ['Override test', 'Gold recovers while yields stay high.']
      ]
    }]
  }
};

const windowObject = {
  MarketBriefCore: {
    adapters: { research: () => fallback },
    store: {
      getSlice: (name) => slices.get(name),
      setSlice: (name, value) => slices.set(name, value)
    }
  }
};
windowObject.window = windowObject;

const context = vm.createContext({ console, fallback, window: windowObject });
vm.runInContext(
  fs.readFileSync(path.join(root, 'site/features/impact-feed/impact-data.js'), 'utf8'),
  context,
  { filename: 'impact-data.js' }
);

const dataset = windowObject.marketImpactData;
assert.equal(dataset.schemaVersion, 1);
assert.equal(dataset.sourceMode, 'curated-delayed');
assert.equal(dataset.items.length, 1);
const item = dataset.items[0];
assert.equal(item.headline, fallback.newsFeed.items[0].headline);
assert.equal(item.summary, fallback.newsFeed.items[0].summary);
assert.equal(item.status, 'confirmed');
assert.equal(item.eventDate, '2026-07-13');
assert.deepEqual(item.sources[0], { name: 'Reuters', url: 'https://example.com/reuters' });
assert.equal(item.interpretations.length, 1);
const interpretation = item.interpretations[0];
assert.equal(interpretation.assetId, 'gold');
assert.equal(interpretation.direction, 'down');
assert.equal(interpretation.magnitude, 'high');
assert.equal(interpretation.horizon, 'unclear', 'legacy feed did not specify a horizon');
assert.equal(interpretation.confidence, 'unclear', 'legacy feed did not specify confidence');
assert.equal(interpretation.mechanism, 'Higher yields pressure gold.');
assert.equal(interpretation.confirmation, 'The curated item describes contemporaneous price action as confirmation.');
assert.equal(interpretation.invalidation, 'Gold recovers while yields stay high.');
assert.equal(slices.get('impactFeed'), dataset);

const unclear = windowObject.MarketBriefCore.impact.adaptItem({
  id: 'missing-fields', headline: 'No directional asset supplied', summary: 'No extra interpretation is inferred.', source: 'Example', sourceUrl: 'https://example.com'
});
assert.equal(unclear.interpretations[0].direction, 'unclear');
assert.equal(unclear.interpretations[0].mechanism, 'No asset interpretation was specified in the legacy item.');
assert.match(unclear.interpretations[0].invalidation, /not specified/i);

console.log('BR-11 news impact adapter tests passed');
