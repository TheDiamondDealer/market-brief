(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};

  function assets() {
    return Array.isArray(window.marketAssetBoard?.assets) ? window.marketAssetBoard.assets : [];
  }

  function assetById(id) {
    return assets().find((asset) => asset.id === id) || null;
  }

  function assetByCotId(cotId) {
    return assets().find((asset) => asset.cotId === cotId) || null;
  }

  function assetsByRateId(rateId) {
    return assets().filter((asset) => asset.rateId === rateId);
  }

  function assetsByCrowdAlias(alias) {
    return assets().filter((asset) => (asset.crowdAliases || []).includes(alias));
  }

  function assetByCalendarAlias(label) {
    return assets().find((asset) => (asset.calendarAliases || []).includes(label)) || null;
  }

  function themeForTicker(tickerId) {
    return assets().find((asset) => (asset.memberTickers || []).includes(tickerId)) || null;
  }

  function netPressure(counts = {}) {
    const up = Number(counts.up) || 0;
    const down = Number(counts.down) || 0;
    const mixed = Number(counts.mixed) || 0;
    if (up + down + mixed === 0) return 'quiet';
    if (up > 0 && up >= 2 * down) return 'up';
    if (down > 0 && down >= 2 * up) return 'down';
    return 'contested';
  }

  function signedContracts(change) {
    return `${change > 0 ? 'rose' : 'fell'} ${Math.abs(change).toLocaleString('en')} contracts`;
  }

  function deriveCotSignals(freeData = window.freeMarketData || {}) {
    const rows = Array.isArray(freeData.cot) ? freeData.cot : [];
    const rowById = new Map(rows.map((row) => [row.id, row]));
    const signals = [];
    assets().forEach((asset) => {
      if (!asset.cotId) return;
      const row = rowById.get(asset.cotId);
      const change = Number(row?.weekChange);
      if (!row || !Number.isFinite(change) || change === 0) return;
      signals.push({
        assetId: asset.id,
        direction: change > 0 ? 'up' : 'down',
        tier: 'observed',
        source: 'cot',
        label: `${row.category || 'Speculative'} positioning`,
        detail: `Net ${row.category || 'speculative'} position ${signedContracts(change)} - ${row.name || 'CFTC contract'}${row.contract?.exchange ? ', ' + row.contract.exchange : ''} (CFTC week ending ${row.reportDate || 'date unavailable'}).`,
        at: row.reportDate || null,
        status: row.dataState || 'current',
        href: '',
      });
    });
    return signals;
  }

  function deriveRateSignals(freeData = window.freeMarketData || {}) {
    const rows = Array.isArray(freeData.rates) ? freeData.rates : [];
    // Source-level honesty: FRED rate rows share one source status. Page calls pass a
    // single-row dataset, so fall back to the global cache's sourceStatus. Never assert
    // 'current' when the source cache is a stale/partial fallback.
    const statusArr = Array.isArray(freeData.sourceStatus)
      ? freeData.sourceStatus
      : (typeof window !== 'undefined' && Array.isArray(window.freeMarketData?.sourceStatus) ? window.freeMarketData.sourceStatus : []);
    const fredSource = statusArr.find((entry) => `${entry.source || ''} ${entry.id || ''}`.toLowerCase().includes('fred'));
    const rateStatus = fredSource?.status || 'current';
    const signals = [];
    rows.forEach((row) => {
      const change = Number(row?.change);
      if (!Number.isFinite(change) || change === 0) return;
      assetsByRateId(row.id).forEach((asset) => {
        const observed = asset.rateInvert ? -change : change;
        // Non-coercing gate: Number.isFinite(null) is false, but Number(null) === 0 —
        // coercion would render an invented "0bps" for real rows like DTWEXBGS (changeBps: null).
        const moveText = Number.isFinite(row.changeBps)
          ? `${Math.abs(row.changeBps)}bps`
          : `${Math.abs(change)} ${row.unit || ''}`.trim();
        signals.push({
          assetId: asset.id,
          direction: observed > 0 ? 'up' : 'down',
          tier: 'observed',
          source: 'rates',
          label: row.name || row.id,
          detail: `${row.name || row.id} moved ${change > 0 ? 'up' : 'down'} ${moveText} (${row.date || 'date unavailable'})${asset.rateInvert ? '; this series is risk-inverted' : ''}.`,
          at: row.date || null,
          status: rateStatus,
          href: '',
        });
      });
    });
    return signals;
  }

  function deriveCrowdSignals(crowdData = {}) {
    const markets = Array.isArray(crowdData.markets) ? crowdData.markets : [];
    const signals = [];
    markets.forEach((market) => {
      const swing = Number(market?.change7dPoints);
      if (!Number.isFinite(swing) || Math.abs(swing) < 5) return;
      const aliases = Array.isArray(market.assets) ? market.assets : [];
      const matched = new Set();
      aliases.forEach((alias) => {
        assetsByCrowdAlias(alias).forEach((asset) => {
          if (matched.has(asset.id)) return;
          matched.add(asset.id);
          signals.push({
            assetId: asset.id,
            direction: 'mixed',
            tier: 'observed',
            source: 'crowd',
            label: 'Crowd repricing',
            detail: `Prediction-market odds moved ${Math.abs(swing).toFixed(1)}pts over 7 days: ${market.question || 'question unavailable'}. A probability move signals attention, not price direction.`,
            at: market.updatedAt || null,
            status: market.status || 'current',
            href: '',
          });
        });
      });
    });
    return signals;
  }

  function deriveEtfSignals(equityData = {}) {
    const rows = Array.isArray(equityData.watchlist) ? equityData.watchlist : [];
    const rowById = new Map(rows.map((row) => [row.id, row]));
    const signals = [];
    assets().forEach((asset) => {
      (asset.etfIds || []).forEach((etfId) => {
        const row = rowById.get(etfId);
        const change = Number(row?.percentChange);
        if (!row || row.status !== 'current' || !Number.isFinite(change) || change === 0) return;
        signals.push({
          assetId: asset.id,
          direction: change > 0 ? 'up' : 'down',
          tier: 'observed',
          source: 'etf',
          label: `${row.name || etfId.toUpperCase()} price`,
          detail: `${row.name || etfId.toUpperCase()} moved ${change > 0 ? '+' : ''}${change.toFixed(2)}% in the last accepted session.`,
          at: row.observedAt || null,
          status: 'current',
          href: '',
        });
      });
    });
    return signals;
  }

  function deriveBlsPrintSignals(blsSource = {}) {
    const rules = Array.isArray(window.marketAssetBoard?.officialSeriesRules)
      ? window.marketAssetBoard.officialSeriesRules
      : [];
    const records = Array.isArray(blsSource.records) ? blsSource.records : [];
    const recordById = new Map(records.map((record) => [record.id, record]));
    const signals = [];
    rules.forEach((rule) => {
      const record = recordById.get(rule.seriesId);
      const change = Number(record?.change);
      if (!record || !Number.isFinite(change) || change === 0) return;
      const asset = assetById(rule.assetId);
      if (!asset) return;
      signals.push({
        assetId: asset.id,
        direction: change > 0 ? 'up' : 'down',
        tier: 'observed',
        source: 'bls',
        label: record.name || rule.seriesName || rule.seriesId,
        detail: `${record.name || rule.seriesId} printed ${change > 0 ? 'up' : 'down'} ${Math.abs(change)} ${record.unit || ''} vs the previous observation (${record.period || 'period unavailable'}).`,
        at: record.observedAt || null,
        status: blsSource.status || 'current',
        href: '',
      });
    });
    return signals;
  }

  function collectDeterministicSignals({ freeData, crowdData, equityData, blsSource } = {}, options = {}) {
    const all = [
      ...deriveCotSignals(freeData),
      ...deriveRateSignals(freeData),
      ...deriveCrowdSignals(crowdData),
      ...deriveEtfSignals(equityData),
      ...deriveBlsPrintSignals(blsSource),
    ];
    // options.since: ISO YYYY-MM-DD window floor. Signals with an unknown date
    // (at: null) are excluded from windowed aggregation — an undated signal must
    // never masquerade as in-window pressure. ISO strings compare lexicographically.
    const since = typeof options.since === 'string' && options.since ? options.since : null;
    const windowed = since ? all.filter((signal) => typeof signal.at === 'string' && signal.at >= since) : all;
    const result = {};
    assets().forEach((asset) => {
      result[asset.id] = { counts: { up: 0, down: 0, mixed: 0 }, net: 'quiet', signals: [] };
    });
    windowed.forEach((signal) => {
      const bucket = result[signal.assetId];
      if (!bucket) return;
      bucket.signals.push(signal);
      if (signal.direction === 'up') bucket.counts.up += 1;
      else if (signal.direction === 'down') bucket.counts.down += 1;
      else bucket.counts.mixed += 1;
    });
    Object.values(result).forEach((bucket) => {
      bucket.net = netPressure(bucket.counts);
    });
    return result;
  }

  core.impactEngine = Object.freeze({
    netPressure,
    deriveCotSignals,
    deriveRateSignals,
    deriveCrowdSignals,
    deriveEtfSignals,
    deriveBlsPrintSignals,
    collectDeterministicSignals,
    assetById,
    assetByCotId,
    assetsByRateId,
    assetsByCrowdAlias,
    assetByCalendarAlias,
    themeForTicker,
  });
})();
