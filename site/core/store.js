(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const state = Object.create(null);
  const metadata = Object.create(null);
  const listeners = new Set();

  function emit(change) {
    listeners.forEach((listener) => {
      try { listener(change, api); } catch (error) { console.error('Market Brief store listener failed', error); }
    });
  }

  function setSlice(name, value, meta = {}) {
    if (!name) throw new TypeError('Store slice name is required.');
    const previous = state[name];
    state[name] = value;
    metadata[name] = { ...metadata[name], ...meta, updatedAt: new Date().toISOString() };
    if (previous !== value || meta.force === true) emit({ name, previous, value, meta: metadata[name] });
    return value;
  }

  function getSlice(name, fallbackValue = null) {
    return Object.prototype.hasOwnProperty.call(state, name) ? state[name] : fallbackValue;
  }

  function getMetadata(name) {
    return metadata[name] ? { ...metadata[name] } : null;
  }

  function select(selector, fallbackValue = null) {
    if (typeof selector !== 'function') return fallbackValue;
    try { return selector(state, metadata); } catch (_) { return fallbackValue; }
  }

  function subscribe(listener, { immediate = false } = {}) {
    if (typeof listener !== 'function') throw new TypeError('Store listener must be a function.');
    listeners.add(listener);
    if (immediate) listener({ name: null, previous: null, value: snapshot(), meta: null }, api);
    return () => listeners.delete(listener);
  }

  function snapshot() {
    return { ...state };
  }

  const api = Object.freeze({ getMetadata, getSlice, select, setSlice, snapshot, subscribe });
  core.store = api;
})();
