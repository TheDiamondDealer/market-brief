(() => {
  'use strict';
  const EMPTY = Object.freeze({schemaVersion:1,generatedAtUtc:null,collection:{status:'unavailable',successCount:0,failureCount:0,unavailableCount:6,lastSuccessfulAt:null,errors:['Official feeds have not loaded.']},sources:[],methodology:{}});
  async function load() {
    try {
      const response = await fetch('data/official-feeds.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      window.officialFeedsData = data;
      window.dispatchEvent(new CustomEvent('marketbrief:official-feeds', { detail: data }));
    } catch (error) {
      window.officialFeedsData = { ...EMPTY, collection: { ...EMPTY.collection, errors: [`Unable to load official feeds: ${error.message}`] } };
      window.dispatchEvent(new CustomEvent('marketbrief:official-feeds', { detail: window.officialFeedsData }));
    }
  }
  window.officialFeedsData = window.officialFeedsData || EMPTY;
  load();
})();
