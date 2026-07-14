(() => {
  'use strict';

  const EMPTY = Object.freeze({
    schemaVersion: 1,
    generatedAtUtc: null,
    provider: {
      id: 'polymarket',
      name: 'Polymarket',
      readOnly: true,
      jurisdictionNote: 'Read-only market data only.'
    },
    collection: {
      status: 'unavailable',
      rawMarketCount: 0,
      selectedMarketCount: 0,
      lastSuccessfulAt: null,
      error: 'Crowd expectations have not loaded.'
    },
    categories: [],
    markets: [],
    shocks: [],
    methodology: {},
    sourceStatus: []
  });

  async function load() {
    try {
      const response = await fetch('data/crowd-expectations.json', {
        cache: 'no-store',
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      window.crowdExpectationsData = data;
      window.dispatchEvent(new CustomEvent('marketbrief:crowd-data', { detail: data }));
    } catch (error) {
      window.crowdExpectationsData = {
        ...EMPTY,
        collection: {
          ...EMPTY.collection,
          error: `Unable to load crowd expectations: ${error.message}`
        }
      };
      window.dispatchEvent(new CustomEvent('marketbrief:crowd-data', {
        detail: window.crowdExpectationsData
      }));
    }
  }

  window.crowdExpectationsData = window.crowdExpectationsData || EMPTY;
  load();
})();
