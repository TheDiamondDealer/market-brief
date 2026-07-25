(() => {
  'use strict';
  const EMPTY = Object.freeze({ schemaVersion: 1, generatedAtUtc: null,
    provider: { id: 'polymarket', name: 'Polymarket', readOnly: true },
    collection: { status: 'unavailable', banksCovered: 0, lastSuccessfulAt: null, error: 'Central-bank decisions have not loaded.' },
    banks: [], methodology: {}, sourceStatus: [] });
  async function load() {
    try {
      const response = await fetch('data/central-bank-decisions.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      window.centralBankDecisionsData = data;
      window.dispatchEvent(new CustomEvent('marketbrief:central-bank-decisions', { detail: data }));
    } catch (error) {
      window.centralBankDecisionsData = { ...EMPTY, collection: { ...EMPTY.collection, error: `Unable to load central-bank decisions: ${error.message}` } };
      window.dispatchEvent(new CustomEvent('marketbrief:central-bank-decisions', { detail: window.centralBankDecisionsData }));
    }
  }
  window.centralBankDecisionsData = window.centralBankDecisionsData || EMPTY;
  load();
})();
