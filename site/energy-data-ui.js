(() => {
  'use strict';

  const marketData = window.freeMarketData || { cot: [] };
  const $ = (id) => document.getElementById(id);
  const cot = (id) => (marketData.cot || []).find((row) => row.id === id);
  const signed = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
    const number = Number(value);
    return `${number > 0 ? '+' : ''}${number.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  };
  const percentile = (row) => row?.netPercentile5y === null || row?.netPercentile5y === undefined ? 'percentile unavailable' : `${Number(row.netPercentile5y).toFixed(1)}th percentile`;
  const summary = (row) => row
    ? `${row.crowding}; net ${signed(row.net)}; ${percentile(row)}; report ${row.reportDate}`
    : 'No verified current benchmark contract is mapped. Older or similarly named contracts are excluded.';

  function updateProductReferences() {
    if (typeof fallback === 'undefined' || !Array.isArray(fallback.products)) return;
    const oil = fallback.products.find((item) => item.id === 'oil');
    const gas = fallback.products.find((item) => item.id === 'natural-gas');
    if (oil) oil.current = 'Brent reference ~$79.31; verify WTI on live chart';
    if (gas) gas.current = 'Henry Hub reference ~$2.89; verify UK NBP on live chart';
  }

  function updateBiasEngine() {
    if (typeof fallback === 'undefined' || !Array.isArray(fallback.assetBiases)) return;
    const oilBias = fallback.assetBiases.find((item) => item.id === 'oil');
    if (oilBias) {
      oilBias.name = 'Oil — Brent / WTI';
      oilBias.cot = `Brent: ${summary(cot('oil-brent'))}. WTI: ${summary(cot('oil-wti'))}.`;
      const positioning = oilBias.components?.find((component) => component.name.toLowerCase().includes('position'));
      if (positioning) positioning.reason = 'Brent and WTI positioning are assessed separately. A missing current primary contract remains unavailable rather than being replaced with a stale or similarly named series.';
    }
  }

  const evidenceMap = {
    'Brent managed-money positioning': 'oil-brent',
    'WTI managed-money positioning': 'oil-wti',
    'US Henry Hub positioning': 'gas-us',
    'UK NBP positioning': 'gas-uk'
  };

  function refreshDetailReference() {
    const match = location.hash.match(/^#product\/(oil|natural-gas)$/);
    if (!match) return;
    const cards = $('productDetail')?.querySelectorAll('.deep-hero .card.stat');
    if (!cards?.length) return;
    const expected = match[1] === 'oil'
      ? 'Brent reference ~$79.31; verify WTI on live chart'
      : 'Henry Hub reference ~$2.89; verify UK NBP on live chart';
    cards.forEach((card) => {
      if (card.querySelector('.stat-label')?.textContent?.trim() === 'Current reference') {
        const value = card.querySelector('.stat-value');
        if (value) value.textContent = expected;
      }
    });
  }

  function refreshEvidencePanel() {
    const panel = $('physicalEvidencePanel');
    if (!panel) return;
    panel.querySelectorAll('.evidence-item').forEach((item) => {
      const name = item.querySelector('h4')?.textContent?.trim();
      const cotId = evidenceMap[name];
      if (!cotId) return;
      const row = cot(cotId);
      const reading = item.querySelector('.evidence-reading');
      const status = item.querySelector('.evidence-status');
      const meta = item.querySelector('.evidence-meta');
      if (reading) reading.textContent = summary(row);
      if (status) {
        status.textContent = row ? 'automatic' : 'pending';
        status.className = `evidence-status ${row ? 'automatic' : 'pending'}`;
      }
      if (meta) {
        const spans = meta.querySelectorAll('span');
        if (spans[0]) spans[0].textContent = row?.market || `CFTC COT — ${cotId}`;
        if (spans[1]) spans[1].textContent = row ? `Report ${row.reportDate}` : 'Current mapping unavailable';
      }
    });
  }

  function refreshEnergyDetail() {
    refreshDetailReference();
    refreshEvidencePanel();
  }

  function initialise() {
    updateProductReferences();
    updateBiasEngine();
    const detail = $('productDetail');
    if (detail) {
      const observer = new MutationObserver(() => requestAnimationFrame(() => requestAnimationFrame(refreshEnergyDetail)));
      observer.observe(detail, { childList: true, subtree: true });
    }
    window.addEventListener('hashchange', () => requestAnimationFrame(() => requestAnimationFrame(refreshEnergyDetail)));
    refreshEnergyDetail();
  }

  initialise();
})();
