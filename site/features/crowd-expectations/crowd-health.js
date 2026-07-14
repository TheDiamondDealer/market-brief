(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  let injecting = false;

  function normalizeStatus(value) {
    return core.freshness?.normalizeStatus?.(value) || String(value || 'unknown').toLowerCase();
  }

  function records() {
    const data = window.crowdExpectationsData || {};
    const generatedAt = data.generatedAtUtc || null;
    return (data.sourceStatus || []).map((source) => Object.freeze({
      id: `crowd:${source.id || 'polymarket'}`,
      family: 'crowd-expectations',
      name: source.source || 'Polymarket public market data',
      sourceObservedAt: source.observationDate || null,
      collectedAt: generatedAt,
      generatedAt,
      expectedCadence: source.expectedCadence || 'Every six hours',
      expectedCadenceDays: 1,
      lastSuccessfulAt: source.lastSuccessfulAt || null,
      status: normalizeStatus(source.status),
      detail: source.detail || '',
      error: source.error || null,
      url: source.url || data.provider?.documentationUrl || null
    }));
  }

  function inject() {
    if (injecting || !core.freshness?.get || !core.store?.setSlice) return;
    const base = core.freshness.get();
    if (!base) return;
    const merged = [
      ...(base.records || []).filter((item) => item.family !== 'crowd-expectations'),
      ...records()
    ];
    const statuses = core.freshness.STATUS || base.statuses || [];
    const counts = Object.fromEntries(
      statuses.map((status) => [status, merged.filter((item) => item.status === status).length])
    );
    const result = Object.freeze({
      ...base,
      generatedAt: new Date().toISOString(),
      counts: Object.freeze(counts),
      records: Object.freeze(merged)
    });
    injecting = true;
    try {
      core.store.setSlice('sourceHealth', result, {
        source: 'crowd-expectations:extension',
        force: true
      });
      window.marketSourceHealth = result;
      window.dispatchEvent(new CustomEvent('marketbrief:source-health', { detail: result }));
    } finally {
      injecting = false;
    }
  }

  window.addEventListener('marketbrief:crowd-data', () => window.setTimeout(inject, 0));
  window.addEventListener('marketbrief:source-health', () => window.setTimeout(inject, 0));
  window.addEventListener('load', inject, { once: true });
  window.setTimeout(inject, 0);
})();
