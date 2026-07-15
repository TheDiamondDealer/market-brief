(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  let injecting = false;

  function normalizeStatus(value) {
    return core.freshness?.normalizeStatus?.(value) || String(value || 'unknown').toLowerCase();
  }

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

  function sameRecord(left, right) {
    return left && right
      && left.id === right.id
      && left.status === right.status
      && left.sourceObservedAt === right.sourceObservedAt
      && left.collectedAt === right.collectedAt
      && left.lastSuccessfulAt === right.lastSuccessfulAt
      && left.detail === right.detail
      && left.error === right.error
      && left.url === right.url;
  }

  function alreadyInjected(base, expected) {
    const existing = (base.records || []).filter((record) => record.family === 'official-free-feeds');
    if (existing.length !== expected.length) return false;
    const byId = new Map(existing.map((record) => [record.id, record]));
    return expected.every((record) => sameRecord(byId.get(record.id), record));
  }

  function inject() {
    if (injecting || !core.freshness?.get || !core.store?.setSlice) return;
    const base = core.freshness.get();
    if (!base) return;
    const expected = sourceRecords();
    if (alreadyInjected(base, expected)) return;

    const records = [
      ...(base.records || []).filter((record) => record.family !== 'official-free-feeds'),
      ...expected
    ];
    const statuses = core.freshness.STATUS || base.statuses || [];
    const counts = Object.fromEntries(
      statuses.map((status) => [status, records.filter((item) => item.status === status).length])
    );
    const result = Object.freeze({
      ...base,
      generatedAt: new Date().toISOString(),
      counts: Object.freeze(counts),
      records: Object.freeze(records)
    });

    injecting = true;
    try {
      core.store.setSlice('sourceHealth', result, { source: 'official-feeds:extension', force: true });
      window.marketSourceHealth = result;
      window.dispatchEvent(new CustomEvent('marketbrief:source-health', { detail: result }));
    } finally {
      injecting = false;
    }
  }

  window.addEventListener('marketbrief:official-feeds', () => window.setTimeout(inject, 0));
  window.addEventListener('marketbrief:source-health', () => window.setTimeout(inject, 0));
  window.addEventListener('load', inject, { once: true });
  window.setTimeout(inject, 0);
})();
