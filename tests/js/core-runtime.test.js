'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..', '..');
const eventListeners = new Map();

function classList(initial = []) {
  const values = new Set(initial);
  return {
    add: (...names) => names.forEach((name) => values.add(name)),
    remove: (...names) => names.forEach((name) => values.delete(name)),
    contains: (name) => values.has(name),
    toggle: (name, force) => {
      const next = force === undefined ? !values.has(name) : Boolean(force);
      if (next) values.add(name); else values.delete(name);
      return next;
    }
  };
}

function element(id, classes = []) {
  return {
    id,
    dataset: {},
    classList: classList(classes),
    attributes: {},
    setAttribute(name, value) { this.attributes[name] = String(value); },
    removeAttribute(name) { delete this.attributes[name]; }
  };
}

const views = [element('view-home', ['view', 'active']), element('view-cot', ['view']), element('view-news', ['view']), element('view-product-detail', ['view'])];
const nav = ['home', 'cot', 'news', 'products'].map((route) => {
  const node = element(`nav-${route}`);
  node.dataset.view = route;
  return node;
});
const elements = new Map([...views.map((node) => [node.id, node]), ['sidebar', element('sidebar')], ['overlay', element('overlay')]]);

const location = { hash: '#cot' };
const history = {
  replaceState(_state, _title, url) { location.hash = String(url).includes('#') ? `#${String(url).split('#').at(-1)}` : ''; }
};

const windowObject = {
  location,
  freeMarketData: { generatedAt: 'test', cot: [{ id: 'gold' }], rates: [] },
  marketResearchData: { physicalChecklists: { gold: { items: [] } }, eventReactions: [] },
  scenarioAssets: { gold: { name: 'Gold' } },
  addEventListener(type, listener) {
    const list = eventListeners.get(type) || [];
    list.push(listener);
    eventListeners.set(type, list);
  },
  dispatchEvent(event) {
    (eventListeners.get(event.type) || []).forEach((listener) => listener(event));
    return true;
  },
  scrollTo() {}
};

class CustomEvent {
  constructor(type, options = {}) { this.type = type; this.detail = options.detail; }
}

const context = vm.createContext({
  console,
  CustomEvent,
  Date,
  Intl,
  Map,
  Number,
  Object,
  RegExp,
  Set,
  String,
  URL,
  decodeURIComponent,
  document: {
    getElementById(id) { return elements.get(id) || null; },
    querySelector(selector) {
      if (selector === '.view.active') return views.find((node) => node.classList.contains('active')) || null;
      return null;
    },
    querySelectorAll(selector) {
      if (selector === '.view') return views;
      if (selector === '#nav button[data-view]') return nav;
      return [];
    }
  },
  fallback: {
    generatedAt: 'legacy',
    regime: { verdict: 'INTACT', name: 'Test', meaning: 'Meaning', chain: [], relationships: [], signFlips: [], shiftRules: [] },
    daily: { title: 'Daily', asOf: 'Today', stats: [], headlines: [] },
    weekly: { tldr: [], events: [], moves: [], highStake: '' },
    triggers: [], products: [], archive: [], assetBiases: [], trackers: {}, trackerOrder: []
  },
  history,
  location,
  window: windowObject
});
windowObject.window = windowObject;
windowObject.history = history;
windowObject.document = context.document;

for (const relative of ['site/core/format.js', 'site/core/status.js', 'site/core/store.js', 'site/core/adapters.js', 'site/core/router.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, relative), 'utf8'), context, { filename: relative });
}

const core = windowObject.MarketBriefCore;
assert.ok(core, 'core namespace should exist');
assert.equal(core.format.escapeHtml('<gold>'), '&lt;gold&gt;');
assert.equal(core.format.signed(12.5, ' bp'), '+12.5 bp');
assert.equal(core.status.normalize('Partial source'), 'partial');
assert.equal(core.status.worst(['current', 'stale', 'partial']), 'stale');
assert.equal(core.adapters.research(), context.fallback, 'legacy research object remains the adapter source');
assert.equal(core.adapters.official(), windowObject.freeMarketData, 'official cache remains available through the adapter');
assert.equal(core.store.getSlice('research'), context.fallback, 'adapter hydration populates the store');

let storeChange = null;
const unsubscribeStore = core.store.subscribe((change) => { storeChange = change; });
core.store.setSlice('test', { ready: true }, { source: 'test' });
assert.equal(storeChange.name, 'test');
unsubscribeStore();

assert.equal(core.adapters.views.activate('cot', { scroll: false }), true);
assert.equal(views.find((node) => node.id === 'view-cot').classList.contains('active'), true);
assert.equal(nav.find((node) => node.dataset.view === 'cot').attributes['aria-current'], 'page');

const calls = [];
core.router.register('home', (route) => calls.push(route.name));
core.router.register('cot', (route) => calls.push(route.name));
core.router.register('news', (route) => calls.push(route.name));
core.router.registerPattern('product-detail', /^product\/([^/]+)$/, (route) => calls.push(`product:${route.params.id}`), (match) => ({ id: match[1] }));

const initial = core.router.start('#cot');
assert.equal(initial.name, 'cot', 'initial hash should dispatch through the shared router');
assert.equal(core.store.getSlice('route').name, 'cot');
core.router.navigate('product/gold', { replace: true });
assert.equal(location.hash, '#product/gold');
assert.equal(calls.at(-1), 'product:gold');
location.hash = '#news';
windowObject.dispatchEvent({ type: 'hashchange' });
assert.equal(calls.at(-1), 'news', 'hash changes should dispatch registered routes');
const fallbackRoute = core.router.dispatch('#unknown');
assert.equal(fallbackRoute.name, 'home', 'unknown routes should use the registered home fallback');
assert.equal(context.fallback.generatedAt, 'legacy', 'legacy globals must not be removed or replaced');

console.log('BR-05 core runtime tests passed');
