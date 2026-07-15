(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  let injecting = false;

  function normalizeStatus(value) {
    return core.freshness?.normalizeStatus?.(value) || String(value || 'unknown').toLowerCase();
  }

  function records() {
    const data = window.gdeltRadarData || {};
    const generatedAt = data.generatedAtUtc || null;
    return (data.sourceStatus || []).map((source) => Object.freeze({
      id: `news-discovery:${source.id || 'gdelt-doc-2'}`,
      family: 'news-discovery',
      name: source.source || 'GDELT DOC 2.0 public API',
      sourceObservedAt: source.observationDate || null,
      collectedAt: generatedAt,
      generatedAt,
      expectedCadence: source.expectedCadence || 'Hourly',
      expectedCadenceDays: 1,
      lastSuccessfulAt: source.lastSuccessfulAt || null,
      status: normalizeStatus(source.status),
      detail: source.detail || '',
      error: source.error || null,
      url: source.url || data.provider?.documentationUrl || null
    }));
  }

  function sameRecord(left, right) {
    return left && right && left.id === right.id && left.status === right.status
      && left.sourceObservedAt === right.sourceObservedAt && left.collectedAt === right.collectedAt
      && left.lastSuccessfulAt === right.lastSuccessfulAt && left.detail === right.detail
      && left.error === right.error && left.url === right.url;
  }

  function inject() {
    if (injecting || !core.freshness?.get || !core.store?.setSlice) return;
    const base = core.freshness.get();
    if (!base) return;
    const expected = records();
    const existing = (base.records || []).filter((record) => record.family === 'news-discovery');
    const byId = new Map(existing.map((record) => [record.id, record]));
    if (existing.length === expected.length && expected.every((record) => sameRecord(byId.get(record.id), record))) return;

    const merged = [...(base.records || []).filter((record) => record.family !== 'news-discovery'), ...expected];
    const statuses = core.freshness.STATUS || base.statuses || [];
    const counts = Object.fromEntries(statuses.map((status) => [status, merged.filter((item) => item.status === status).length]));
    const result = Object.freeze({ ...base, generatedAt: new Date().toISOString(), counts: Object.freeze(counts), records: Object.freeze(merged) });

    injecting = true;
    try {
      core.store.setSlice('sourceHealth', result, { source: 'gdelt-radar:extension', force: true });
      window.marketSourceHealth = result;
      window.dispatchEvent(new CustomEvent('marketbrief:source-health', { detail: result }));
    } finally {
      injecting = false;
    }
  }

  window.addEventListener('marketbrief:gdelt-data', () => window.setTimeout(inject, 0));
  window.addEventListener('marketbrief:source-health', () => window.setTimeout(inject, 0));
  window.addEventListener('load', inject, { once: true });
  window.setTimeout(inject, 0);
})();
