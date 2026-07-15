(() => {
  'use strict';

  const EMPTY = Object.freeze({
    schemaVersion: 1,
    generatedAtUtc: null,
    provider: { id: 'gdelt-doc-2', name: 'GDELT DOC 2.0 API', readOnly: true },
    collection: {
      status: 'unavailable', expectedCadence: 'Hourly', queryCount: 0,
      successfulQueryCount: 0, rawArticleCount: 0, selectedArticleCount: 0,
      lastSuccessfulAt: null, error: 'GDELT discovery radar has not loaded.'
    },
    disclaimer: 'Unverified discovery radar. Confirmation is required.',
    topics: [], articles: [], sourceStatus: [], methodology: {}
  });

  async function load() {
    try {
      const response = await fetch('data/gdelt-radar.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      window.gdeltRadarData = data;
      window.dispatchEvent(new CustomEvent('marketbrief:gdelt-data', { detail: data }));
    } catch (error) {
      window.gdeltRadarData = {
        ...EMPTY,
        collection: { ...EMPTY.collection, error: `Unable to load GDELT radar: ${error.message}` }
      };
      window.dispatchEvent(new CustomEvent('marketbrief:gdelt-data', { detail: window.gdeltRadarData }));
    }
  }

  window.gdeltRadarData = window.gdeltRadarData || EMPTY;
  load();
})();
