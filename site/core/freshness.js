(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const store = core.store;
  const STATUS = Object.freeze(['current', 'delayed', 'stale', 'failed', 'unavailable', 'partial', 'unknown']);
  let refreshing = false;

  function parseDate(value) {
    if (!value) return null;
    if (value instanceof Date && !Number.isNaN(value.getTime())) return value;
    const direct = new Date(value);
    if (!Number.isNaN(direct.getTime())) return direct;
    const text = String(value).trim();
    const match = text.match(/^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})(?:,?\s+(\d{1,2}):(\d{2})\s*(AM|PM))?/i);
    if (!match) return null;
    const months = { january: 0, february: 1, march: 2, april: 3, may: 4, june: 5, july: 6, august: 7, september: 8, october: 9, november: 10, december: 11, jan: 0, feb: 1, mar: 2, apr: 3, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
    const month = months[match[2].toLowerCase()];
    if (month === undefined) return null;
    let hour = Number(match[4] || 0);
    if (match[6]) {
      hour %= 12;
      if (match[6].toUpperCase() === 'PM') hour += 12;
    }
    const result = new Date(Date.UTC(Number(match[3]), month, Number(match[1]), hour, Number(match[5] || 0)));
    return Number.isNaN(result.getTime()) ? null : result;
  }

  function iso(value) {
    const parsed = parseDate(value);
    return parsed ? parsed.toISOString() : null;
  }

  function ageDays(value, now = new Date()) {
    const parsed = parseDate(value);
    if (!parsed) return null;
    return (now.getTime() - parsed.getTime()) / 86400000;
  }

  function cadenceStatus(observedAt, cadenceDays, { futureToleranceDays = 1 } = {}) {
    const age = ageDays(observedAt);
    if (age === null) return 'unknown';
    if (age < -futureToleranceDays) return 'unknown';
    if (age <= cadenceDays * 1.5) return 'current';
    if (age <= cadenceDays * 3) return 'delayed';
    return 'stale';
  }

  function normalizeStatus(value, fallback = 'unknown') {
    const text = String(value || '').trim().toLowerCase();
    if (STATUS.includes(text)) return text;
    if (['ok', 'success', 'healthy', 'verified', 'parsed'].includes(text)) return 'current';
    if (text.includes('partial') || text.includes('retry')) return 'partial';
    if (text.includes('fail') || text.includes('error')) return 'failed';
    if (text.includes('stale')) return 'stale';
    if (text.includes('delay')) return 'delayed';
    if (text.includes('unavailable') || text.includes('missing')) return 'unavailable';
    if (text.includes('current')) return 'current';
    return fallback;
  }

  function record(input) {
    const status = normalizeStatus(input.status, input.error ? 'failed' : input.sourceObservedAt ? 'unknown' : 'unavailable');
    return Object.freeze({
      id: String(input.id),
      family: String(input.family || 'other'),
      name: String(input.name || input.id),
      sourceObservedAt: iso(input.sourceObservedAt),
      collectedAt: iso(input.collectedAt),
      generatedAt: iso(input.generatedAt),
      expectedCadence: input.expectedCadence || 'Not specified',
      expectedCadenceDays: input.expectedCadenceDays ?? null,
      lastSuccessfulAt: iso(input.lastSuccessfulAt),
      status,
      detail: input.detail ? String(input.detail) : '',
      error: input.error ? String(input.error) : null,
      url: input.url ? String(input.url) : null
    });
  }

  function officialRecords() {
    const data = core.adapters?.official?.() || window.freeMarketData || {};
    const generatedAt = data.generatedAtUtc || data.generatedAt;
    const rows = [];
    for (const rate of data.rates || []) {
      rows.push(record({
        id: `macro:${rate.id}`, family: 'official-macro', name: rate.name,
        sourceObservedAt: rate.date, collectedAt: generatedAt, generatedAt,
        expectedCadence: 'Daily business-day observation', expectedCadenceDays: 5,
        lastSuccessfulAt: generatedAt, status: cadenceStatus(rate.date, 5),
        detail: `${rate.id} · latest ${rate.value ?? 'unavailable'} ${rate.unit || ''}`.trim(), url: rate.sourceUrl
      }));
    }
    for (const cot of data.cot || []) {
      rows.push(record({
        id: `cot:${cot.id}`, family: 'official-cot', name: `${cot.name} COT`,
        sourceObservedAt: cot.reportDate, collectedAt: generatedAt, generatedAt,
        expectedCadence: 'Weekly CFTC report', expectedCadenceDays: 10,
        lastSuccessfulAt: generatedAt, status: cot.contract?.identityStatus === 'verified' ? cadenceStatus(cot.reportDate, 10) : 'unavailable',
        detail: `${cot.contract?.cftcContractCode || 'No code'} · ${cot.contract?.category || cot.category || 'Category unavailable'}`, url: cot.sourceUrl
      }));
    }
    for (const source of data.sourceStatus || []) {
      rows.push(record({
        id: `official-source:${source.id || source.source || rows.length}`, family: 'official-pipeline', name: source.source || source.name || source.id || 'Official pipeline',
        sourceObservedAt: source.observationDate || source.date || null, collectedAt: generatedAt, generatedAt,
        expectedCadence: source.expectedCadence || 'Pipeline-specific', lastSuccessfulAt: source.lastSuccessfulAt || generatedAt,
        status: source.status, detail: source.detail || source.message || '', error: source.error || null, url: source.url || source.sourceUrl || null
      }));
    }
    return rows;
  }

  function equityRecords() {
    const data = core.adapters?.equities?.() || window.equityMarketData || {};
    const generatedAt = data.generatedAtUtc;
    const rows = [];
    for (const source of data.sourceStatus || []) {
      rows.push(record({
        id: `market-price-source:${source.id || rows.length}`,
        family: 'market-prices',
        name: source.source || 'Twelve Data private market feed',
        sourceObservedAt: source.observationDate,
        collectedAt: generatedAt,
        generatedAt,
        expectedCadence: source.expectedCadence || 'Intraday snapshots plus daily full history',
        expectedCadenceDays: 3,
        lastSuccessfulAt: source.lastSuccessfulAt,
        status: source.status,
        detail: source.detail || '',
        error: source.error || null,
        url: source.url || data.provider?.sourceUrl || null
      }));
    }
    for (const item of data.watchlist || []) {
      const price = item.price === null || item.price === undefined ? 'price unavailable' : `${item.price} ${item.currency || ''}`.trim();
      const day = item.percentChange === null || item.percentChange === undefined ? 'day move unavailable' : `${Number(item.percentChange) > 0 ? '+' : ''}${item.percentChange}% day`;
      const acceptedStatus = item.status === 'current' ? cadenceStatus(item.observedAt, 3) : item.status;
      rows.push(record({
        id: `market-price:${item.id}`,
        family: 'market-prices',
        name: `${item.symbol} — ${item.name}`,
        sourceObservedAt: item.observedAt,
        collectedAt: item.collectedAt || generatedAt,
        generatedAt,
        expectedCadence: 'Intraday quote snapshot; daily history refresh',
        expectedCadenceDays: 3,
        lastSuccessfulAt: data.collection?.lastSuccessfulAt,
        status: acceptedStatus,
        detail: `${price} · ${day} · ${item.exchange || 'exchange unavailable'}`,
        error: item.error || null,
        url: item.sourceUrl || data.provider?.sourceUrl || null
      }));
    }
    return rows;
  }

  function politicalRecords() {
    const data = window.politicalDisclosureSummary || store?.getSlice('politicalSummary') || {};
    const generatedAt = data.generatedAt;
    const rows = [record({
      id: 'political:summary', family: 'political', name: 'Political disclosure summary',
      sourceObservedAt: generatedAt, collectedAt: generatedAt, generatedAt,
      expectedCadence: 'Weekday collector', expectedCadenceDays: 3,
      lastSuccessfulAt: generatedAt, status: generatedAt ? cadenceStatus(generatedAt, 3) : 'unavailable',
      detail: `${data.totalTrades ?? 0} retained transactions`, url: null
    })];
    const ledger = data.sourceStatus?.filingLedger;
    if (ledger) {
      rows.push(record({
        id: 'political:filing-ledger', family: 'political', name: 'Political filing ledger',
        sourceObservedAt: generatedAt, collectedAt: generatedAt, generatedAt,
        expectedCadence: 'Weekday collector', expectedCadenceDays: 3,
        lastSuccessfulAt: generatedAt, status: Number(ledger.retryable || 0) ? 'partial' : 'current',
        detail: `${ledger.filings || 0} filings tracked; ${ledger.retryable || 0} retryable`,
        error: Number(ledger.retryable || 0) ? 'One or more filing downloads or parser runs require retry.' : null
      }));
    }
    return rows;
  }

  function researchRecords() {
    const impact = core.impact?.get?.() || window.marketImpactData || {};
    const calendar = core.calendar?.get?.() || window.marketCalendarData || {};
    const evidence = core.adapters?.evidence?.() || window.marketResearchData || {};
    const research = core.adapters?.research?.() || (typeof fallback !== 'undefined' ? fallback : {});
    const conflict = window.conflictWatchData || {};
    const records = [
      record({ id: 'research:impact', family: 'research', name: 'Curated Impact Feed', sourceObservedAt: impact.generatedAt, collectedAt: impact.generatedAt, generatedAt: impact.generatedAt, expectedCadence: 'Research-run dependent', expectedCadenceDays: 7, lastSuccessfulAt: impact.generatedAt, status: impact.generatedAt ? cadenceStatus(impact.generatedAt, 7) : 'unavailable', detail: `${impact.items?.length || 0} curated events · ${impact.sourceMode || 'mode unavailable'}` }),
      record({ id: 'research:calendar', family: 'research', name: 'Calendar and reaction records', sourceObservedAt: calendar.generatedAt, collectedAt: calendar.generatedAt, generatedAt: calendar.generatedAt, expectedCadence: 'Research-run dependent', expectedCadenceDays: 7, lastSuccessfulAt: calendar.generatedAt, status: calendar.generatedAt ? cadenceStatus(calendar.generatedAt, 7) : 'unavailable', detail: `${calendar.events?.length || 0} tracked events · ${calendar.timezone || 'timezone unavailable'}` }),
      record({ id: 'research:physical', family: 'research', name: 'Physical and macro checklists', sourceObservedAt: evidence.updated, collectedAt: evidence.updated, generatedAt: evidence.updated, expectedCadence: 'Research-review dependent', expectedCadenceDays: 30, lastSuccessfulAt: evidence.updated, status: evidence.updated ? cadenceStatus(evidence.updated, 30) : 'unavailable', detail: `${Object.keys(evidence.physicalChecklists || {}).length} asset checklists` }),
      record({ id: 'research:baseline', family: 'research', name: 'Strategic research baseline', sourceObservedAt: research.generatedAt || research.updated, collectedAt: research.generatedAt || research.updated, generatedAt: research.generatedAt || research.updated, expectedCadence: 'Monthly strategic refresh', expectedCadenceDays: 35, lastSuccessfulAt: research.generatedAt || research.updated, status: (research.generatedAt || research.updated) ? cadenceStatus(research.generatedAt || research.updated, 35) : 'unavailable', detail: research.regime?.name || 'Regime record unavailable' })
    ];
    if (conflict.collection) {
      records.push(record({
        id: 'conflict:pipeline', family: 'official-conflict', name: 'Conflict publication watch',
        sourceObservedAt: conflict.items?.[0]?.publishedAt, collectedAt: conflict.generatedAtUtc, generatedAt: conflict.generatedAtUtc,
        expectedCadence: 'Every three hours', expectedCadenceDays: .25, lastSuccessfulAt: conflict.collection.status === 'current' ? conflict.generatedAtUtc : null,
        status: conflict.collection.status, detail: `${conflict.items?.length || 0} relevant official publications · ${conflict.collection.failureCount || 0} source failures`,
        error: conflict.collection.failureCount ? 'One or more official conflict feeds failed during the latest refresh.' : null
      }));
      for (const source of conflict.collection.sourceStatus || []) {
        const latest = (conflict.items || []).find((item) => item.source?.id === source.id);
        records.push(record({
          id: `conflict:${source.id}`, family: 'official-conflict', name: source.name,
          sourceObservedAt: latest?.publishedAt, collectedAt: conflict.generatedAtUtc, generatedAt: conflict.generatedAtUtc,
          expectedCadence: 'Every three hours', expectedCadenceDays: .25,
          lastSuccessfulAt: source.status === 'current' ? conflict.generatedAtUtc : null,
          status: source.status, detail: source.detail, error: source.status === 'failed' ? source.detail : null, url: source.url
        }));
      }
    }
    return records;
  }

  function build() {
    const records = [...officialRecords(), ...equityRecords(), ...politicalRecords(), ...researchRecords()];
    const counts = Object.fromEntries(STATUS.map((status) => [status, records.filter((item) => item.status === status).length]));
    return Object.freeze({ schemaVersion: 1, generatedAt: new Date().toISOString(), statuses: STATUS, counts: Object.freeze(counts), records: Object.freeze(records) });
  }

  function refresh() {
    if (refreshing) return store?.getSlice('sourceHealth') || null;
    refreshing = true;
    try {
      const result = build();
      store?.setSlice('sourceHealth', result, { source: 'freshness:registry', force: true });
      window.marketSourceHealth = result;
      window.dispatchEvent(new CustomEvent('marketbrief:source-health', { detail: result }));
      return result;
    } finally {
      refreshing = false;
    }
  }

  function get() { return store?.getSlice('sourceHealth') || window.marketSourceHealth || refresh(); }
  function all() { return [...(get()?.records || [])]; }
  function forId(id) { return all().find((item) => item.id === id) || null; }
  function failures() { return all().filter((item) => ['delayed', 'stale', 'failed', 'unavailable', 'partial'].includes(item.status)); }

  core.freshness = Object.freeze({ STATUS, ageDays, all, build, cadenceStatus, failures, forId, get, normalizeStatus, parseDate, refresh });
  store?.subscribe((change) => {
    if (change.name && change.name !== 'sourceHealth' && ['impactFeed', 'calendar', 'politicalSummary', 'equities'].includes(change.name)) window.setTimeout(refresh, 0);
  });
  window.addEventListener('marketbrief:equity-data', () => window.setTimeout(refresh, 0));
  refresh();
  window.addEventListener('load', refresh, { once: true });
})();
