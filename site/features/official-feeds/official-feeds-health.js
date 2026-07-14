(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  let injecting = false;
  function normalizeStatus(value) { return core.freshness?.normalizeStatus?.(value) || String(value || 'unknown').toLowerCase(); }
  function sourceRecords() {
    const data = window.officialFeedsData || {};
    const generatedAt = data.generatedAtUtc;
    return (data.sources || []).map((source) => Object.freeze({
      id: `official-feed:${source.id}`,
      family: 'official-free-feeds',
      name: source.name,
      sourceObservedAt: source.observedAt || null,
      collectedAt: source.collectedAt || generatedAt || null,
      generatedAt: generatedAt || null,
      expectedCadence: source.expectedCadence || 'Source-specific',
      expectedCadenceDays: null,
      lastSuccessfulAt: source.lastSuccessfulAt || null,
      status: normalizeStatus(source.status),
      detail: `${source.detail || ''}${source.records ? ` · ${source.records.length} retained record${source.records.length === 1 ? '' : 's'}` : ''}`.trim(),
      error: source.error || null,
      url: source.sourceUrl || null
    }));
  }
  function inject() {
    if (injecting || !core.freshness?.get || !core.store?.setSlice) return;
    const base = core.freshness.get();
    if (!base) return;
    const records = [...(base.records || []).filter((record) => record.family !== 'official-free-feeds'), ...sourceRecords()];
    const statuses = core.freshness.STATUS || base.statuses || [];
    const counts = Object.fromEntries(statuses.map((status) => [status, records.filter((item) => item.status === status).length]));
    const result = Object.freeze({ ...base, generatedAt: new Date().toISOString(), counts: Object.freeze(counts), records: Object.freeze(records) });
    injecting = true;
    try {
      core.store.setSlice('sourceHealth', result, { source: 'official-feeds:extension', force: true });
      window.marketSourceHealth = result;
      window.dispatchEvent(new CustomEvent('marketbrief:source-health', { detail: result }));
    } finally { injecting = false; }
  }
  window.addEventListener('marketbrief:official-feeds', () => window.setTimeout(inject, 0));
  window.addEventListener('marketbrief:source-health', () => window.setTimeout(inject, 0));
  window.addEventListener('load', inject, { once: true });
  window.setTimeout(inject, 0);
})();
