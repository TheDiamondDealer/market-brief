(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const cache = new Map();

  async function json(url) {
    if (!url) throw new Error('Political data URL is required.');
    if (cache.has(url)) return cache.get(url);
    const request = fetch(url, { credentials: 'same-origin', cache: 'no-cache' }).then(async (response) => {
      if (!response.ok) throw new Error(`Political data request failed (${response.status}) for ${url}`);
      return response.json();
    }).catch((error) => {
      cache.delete(url);
      throw error;
    });
    cache.set(url, request);
    return request;
  }

  async function manifest() {
    const value = window.politicalDisclosureManifest || await json('data/political/manifest.json');
    core.store?.setSlice('politicalManifest', value, { source: 'political:manifest' });
    return value;
  }

  async function summary() {
    const value = window.politicalDisclosureSummary || await json('data/political/summary.json');
    core.store?.setSlice('politicalSummary', value, { source: 'political:summary' });
    return value;
  }

  async function tracker(id) {
    const index = await manifest();
    const item = index.trackers?.[id];
    if (!item) throw new Error(`Unknown political tracker: ${id}`);
    return json(item.summaryUrl);
  }

  async function year(id, value) {
    const index = await manifest();
    const url = index.trackers?.[id]?.annualUrls?.[String(value)];
    if (!url) throw new Error(`No ${value} disclosure file is available for ${id}.`);
    return json(url);
  }

  async function politicians() {
    const index = await manifest();
    return json(index.politicianIndexUrl);
  }

  async function tickers() {
    const index = await manifest();
    return json(index.tickerIndexUrl);
  }

  async function searchPoliticians(query = '') {
    const data = await politicians();
    const needle = String(query).trim().toLowerCase();
    return (data.politicians || []).filter((item) => !needle || String(item.keywords || '').includes(needle));
  }

  async function searchTickers(query = '') {
    const data = await tickers();
    const needle = String(query).trim().toUpperCase();
    return (data.tickers || []).filter((item) => !needle || item.ticker.includes(needle) || (item.assets || []).some((asset) => String(asset).toUpperCase().includes(needle)));
  }

  function clear() {
    cache.clear();
  }

  core.political = Object.freeze({ clear, manifest, politicians, searchPoliticians, searchTickers, summary, tickers, tracker, year });
  summary().catch((error) => console.error('Political summary failed to initialise', error));
})();
