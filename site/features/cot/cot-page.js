(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const registry = official.cotContractRegistry || {};
  const rows = Array.isArray(official.cot)
    ? official.cot.filter((row) => row?.contract?.identityStatus === 'verified')
    : [];
  const referenceProductIds = Array.isArray(registry.referenceProductIds) && registry.referenceProductIds.length
    ? registry.referenceProductIds
    : rows.map((row) => row.id);
  const referenceOrder = new Map(referenceProductIds.map((id, index) => [id, index]));
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const number = core.format?.formatNumber || ((value, digits = 0) => (
    value === null || value === undefined || Number.isNaN(Number(value))
      ? '—'
      : Number(value).toLocaleString(undefined, { maximumFractionDigits: digits })
  ));
  const signed = core.format?.signed || ((value) => (
    value === null || value === undefined || Number.isNaN(Number(value))
      ? '—'
      : `${Number(value) > 0 ? '+' : ''}${number(value)}`
  ));
  const compact = core.format?.compact || ((value) => new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(Number(value || 0)));

  const CATEGORY_LABELS = Object.freeze({
    all: 'All',
    metals: 'Metals',
    energy: 'Energy',
    currencies: 'Currencies',
    rates: 'Rates',
    indices: 'Indices',
    grains: 'Grains',
    softs: 'Softs',
    other: 'Other',
  });
  const ID_CATEGORIES = Object.freeze({
    gold: 'metals',
    silver: 'metals',
    copper: 'metals',
    palladium: 'metals',
    platinum: 'metals',
    'brent-last-day': 'energy',
    'wti-crude-ice': 'energy',
    'wti-financial': 'energy',
    'natural-gas-nyme': 'energy',
    ethanol: 'energy',
    aud: 'currencies',
    'british-pound': 'currencies',
    'canadian-dollar': 'currencies',
    yen: 'currencies',
    'usd-index': 'currencies',
    'euro-fx': 'currencies',
    'eur-gbp': 'currencies',
    'brazilian-real': 'currencies',
    'mexican-peso': 'currencies',
    'new-zealand-dollar': 'currencies',
    'swiss-franc': 'currencies',
    'south-african-rand': 'currencies',
    'us10y-futures': 'rates',
    'ultra-us10y': 'rates',
    'ultra-us-bond': 'rates',
    'us30y-bond': 'rates',
    'us5y-note': 'rates',
    'fed-funds': 'rates',
    'us2y-note': 'rates',
    'sp500-emini': 'indices',
    'sp500-micro': 'indices',
    'nasdaq100-micro': 'indices',
    'nasdaq100-emini': 'indices',
    'russell2000-emini': 'indices',
    vix: 'indices',
    'dow-emini': 'indices',
    cocoa: 'softs',
    'cotton-2': 'softs',
    coffee: 'softs',
    'sugar-11': 'softs',
    corn: 'grains',
    oats: 'grains',
    'rough-rice': 'grains',
    soybeans: 'grains',
    'wheat-srw': 'grains',
    'bitcoin-cme': 'other',
  });
  const state = {
    category: 'all',
    query: '',
    mode: 'balance',
    selectedId: rows[0]?.id || null,
    sortKey: 'referenceOrder',
    sortDirection: 'asc',
  };

  function categoryFor(row) {
    if (ID_CATEGORIES[row.id]) return ID_CATEGORIES[row.id];
    const text = `${row.name || ''} ${row.market || ''}`.toLowerCase();
    if (/gold|silver|copper|metal/.test(text)) return 'metals';
    if (/oil|gas|crude|energy/.test(text)) return 'energy';
    if (/yen|dollar|euro|pound|franc|currency/.test(text)) return 'currencies';
    if (/treasury|note|bond|rate/.test(text)) return 'rates';
    if (/index|s&p|nasdaq|dow/.test(text)) return 'indices';
    return 'other';
  }

  function shares(point) {
    const long = Math.max(0, Number(point?.long || 0));
    const short = Math.max(0, Number(point?.short || 0));
    const gross = long + short;
    return {
      available: gross > 0,
      long: gross ? (long / gross) * 100 : null,
      short: gross ? (short / gross) * 100 : null,
    };
  }

  function historyPair(row) {
    const history = Array.isArray(row.history52) ? row.history52 : [];
    const latestHistory = history.at(-1);
    const previous = latestHistory?.date === row.reportDate ? history.at(-2) : latestHistory;
    return {
      current: { long: row.long, short: row.short, net: row.net, date: row.reportDate },
      previous: previous || null,
    };
  }

  function formatDate(value) {
    if (!value) return 'Unavailable';
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function sourceStatus() {
    const cftc = (official.sourceStatus || []).find((item) => String(item.source || '').toLowerCase().includes('cftc'));
    if (cftc) return cftc;
    return {
      status: rows.length ? 'current' : 'unavailable',
      detail: rows.length ? 'Verified exact-contract cache loaded.' : 'No verified CFTC rows are available.',
      url: rows[0]?.sourceUrl || '',
    };
  }

  function visibleRows() {
    const query = state.query.trim().toLowerCase();
    const filtered = rows.filter((row) => {
      const categoryMatch = state.category === 'all' || categoryFor(row) === state.category;
      const contract = row.contract || {};
      const haystack = [
        row.id,
        row.name,
        row.market,
        row.category,
        contract.exchange,
        contract.cftcContractCode,
        contract.reportType,
      ].join(' ').toLowerCase();
      return categoryMatch && (!query || haystack.includes(query));
    });
    const direction = state.sortDirection === 'asc' ? 1 : -1;
    return filtered.sort((a, b) => {
      if (state.sortKey === 'referenceOrder') {
        return (referenceOrder.get(a.id) ?? referenceOrder.size) - (referenceOrder.get(b.id) ?? referenceOrder.size);
      }
      if (state.sortKey === 'name') return String(a.name || '').localeCompare(String(b.name || '')) * direction;
      if (state.sortKey === 'longShare') return ((shares(a).long ?? -1) - (shares(b).long ?? -1)) * direction;
      return (Number(a[state.sortKey] || 0) - Number(b[state.sortKey] || 0)) * direction;
    });
  }

  function referenceCoverage() {
    const referenceIds = new Set(referenceProductIds);
    const loadedIds = new Set(rows.map((row) => row.id).filter((id) => referenceIds.has(id)));
    const currentCount = rows.filter((row) => referenceIds.has(row.id) && row.dataState !== 'stale-retained').length;
    const retainedCount = rows.filter((row) => referenceIds.has(row.id) && row.dataState === 'stale-retained').length;
    const unavailable = [...(Array.isArray(registry.unavailable) ? registry.unavailable : []), ...(Array.isArray(registry.missing) ? registry.missing : [])]
      .filter((item, index, all) => referenceIds.has(item?.id) && !loadedIds.has(item.id) && all.findIndex((candidate) => candidate?.id === item.id) === index);
    return {
      total: referenceProductIds.length,
      loaded: loadedIds.size,
      currentCount,
      retainedCount,
      unavailable,
    };
  }

  function positionLabel(row) {
    if (Number(row.net) > 0) return 'Net long';
    if (Number(row.net) < 0) return 'Net short';
    return 'Neutral';
  }

  function flowLabel(row) {
    if (Number(row.weekChange) > 0) return 'Net increased';
    if (Number(row.weekChange) < 0) return 'Net decreased';
    return 'Unchanged';
  }

  function chartBalance(rowsToShow) {
    const rowHeight = 34;
    const margin = { top: 30, right: 64, bottom: 12, left: 200 };
    const width = 980;
    const plotWidth = width - margin.left - margin.right;
    const height = margin.top + rowsToShow.length * rowHeight + margin.bottom;
    const axis = [0, 25, 50, 75, 100].map((tick) => {
      const x = margin.left + (tick / 100) * plotWidth;
      return `<line class="cot-chart-gridline ${tick === 50 ? 'zero' : ''}" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${margin.top - 6}" y2="${height - margin.bottom}"></line><text class="cot-chart-axis" x="${x.toFixed(1)}" y="${margin.top - 12}" text-anchor="middle">${tick}%</text>`;
    }).join('');
    const bars = rowsToShow.map((row, index) => {
      const split = shares(row);
      const y = margin.top + index * rowHeight;
      const barY = y + (rowHeight - 14) / 2;
      const name = `<text class="cot-chart-row-label" x="${margin.left - 12}" y="${y + rowHeight / 2 + 4}" text-anchor="end">${escapeHtml(row.name)}</text>`;
      if (!split.available) {
        return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: no reported long or short positions">
          ${name}<rect class="cot-chart-empty-bar" x="${margin.left}" y="${barY}" width="${plotWidth}" height="14" rx="7"></rect>
          <text class="cot-chart-value muted" x="${margin.left + plotWidth + 10}" y="${y + rowHeight / 2 + 4}" text-anchor="start">n/a</text>
        </g>`;
      }
      const longWidth = (split.long / 100) * plotWidth;
      return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: ${number(split.long, 1)} percent long and ${number(split.short, 1)} percent short">
        ${name}
        <rect class="cot-chart-long" x="${margin.left}" y="${barY}" width="${longWidth.toFixed(1)}" height="14"></rect>
        <rect class="cot-chart-short" x="${(margin.left + longWidth).toFixed(1)}" y="${barY}" width="${(plotWidth - longWidth).toFixed(1)}" height="14"></rect>
        <text class="cot-chart-value" x="${margin.left + plotWidth + 10}" y="${y + rowHeight / 2 + 4}" text-anchor="start">${number(split.long, 0)}%</text>
      </g>`;
    }).join('');
    return `<div class="cot-positioning-chart-scroll"><svg class="cot-positioning-svg" style="min-width:720px" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotPositioningTitle cotPositioningDesc">
      <title id="cotPositioningTitle">Long and short positioning by verified CFTC contract</title>
      <desc id="cotPositioningDesc">Each row totals 100 percent of reported long plus short positions. Green is long share, red is short share, and the right-hand value is the long percentage.</desc>
      ${axis}${bars}
    </svg></div>`;
  }

  function chartDirectional(rowsToShow, key, description) {
    const rowHeight = 34;
    const margin = { top: 30, right: 84, bottom: 12, left: 200 };
    const width = 980;
    const plotWidth = width - margin.left - margin.right;
    const height = margin.top + rowsToShow.length * rowHeight + margin.bottom;
    const maxAbsolute = Math.max(...rowsToShow.map((row) => Math.abs(Number(row[key] || 0))), 1);
    const zeroX = margin.left + plotWidth / 2;
    const axis = [-1, -0.5, 0, 0.5, 1].map((fraction) => {
      const x = zeroX + fraction * (plotWidth / 2);
      return `<line class="cot-chart-gridline ${fraction === 0 ? 'zero' : ''}" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${margin.top - 6}" y2="${height - margin.bottom}"></line><text class="cot-chart-axis" x="${x.toFixed(1)}" y="${margin.top - 12}" text-anchor="middle">${escapeHtml(compact(fraction * maxAbsolute))}</text>`;
    }).join('');
    const bars = rowsToShow.map((row, index) => {
      const value = Number(row[key] || 0);
      const barLength = (Math.abs(value) / maxAbsolute) * (plotWidth / 2);
      const y = margin.top + index * rowHeight;
      const barY = y + (rowHeight - 14) / 2;
      const negative = value < 0;
      const x = negative ? zeroX - barLength : zeroX;
      const outerX = negative ? zeroX - barLength - 8 : zeroX + barLength + 8;
      // Keep the value label out of the left-hand row-name gutter: a long negative bar would push
      // its label onto the market names, so render it just inside the bar's left end instead.
      const inside = negative && outerX < margin.left + 6;
      const valueX = inside ? x + 6 : outerX;
      const anchor = negative ? (inside ? 'start' : 'end') : 'start';
      return `<g class="cot-chart-market" data-cot-chart-select="${escapeHtml(row.id)}" tabindex="0" role="button" aria-label="${escapeHtml(row.name)}: ${escapeHtml(signed(value))} contracts">
        <text class="cot-chart-row-label" x="${margin.left - 12}" y="${y + rowHeight / 2 + 4}" text-anchor="end">${escapeHtml(row.name)}</text>
        <rect class="${negative ? 'cot-chart-negative' : 'cot-chart-positive'}" x="${x.toFixed(1)}" y="${barY}" width="${Math.max(barLength, 2).toFixed(1)}" height="14"></rect>
        <text class="cot-chart-value${inside ? ' inside' : ''}" x="${valueX.toFixed(1)}" y="${y + rowHeight / 2 + 4}" text-anchor="${anchor}">${escapeHtml(compact(value))}</text>
      </g>`;
    }).join('');
    return `<div class="cot-positioning-chart-scroll"><svg class="cot-positioning-svg" style="min-width:720px" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotPositioningTitle cotPositioningDesc">
      <title id="cotPositioningTitle">${escapeHtml(description)} by verified CFTC contract</title>
      <desc id="cotPositioningDesc">Bars extend right for positive (green) and left for negative (red) values. Values are contract counts and are not comparable across differently sized futures markets.</desc>
      ${axis}${bars}
    </svg></div>`;
  }

  function positioningChart(rowsToShow) {
    if (!rowsToShow.length) return '<div class="cot-empty">No verified exact contracts match these filters.</div>';
    if (state.mode === 'net') return chartDirectional(rowsToShow, 'net', 'Net positioning');
    if (state.mode === 'change') return chartDirectional(rowsToShow, 'weekChange', 'Weekly net-position change');
    return chartBalance(rowsToShow);
  }

  function sortButton(key, label) {
    const active = state.sortKey === key;
    const direction = active ? (state.sortDirection === 'asc' ? 'ascending' : 'descending') : 'none';
    const marker = active ? (state.sortDirection === 'asc' ? '↑' : '↓') : '';
    return `<button type="button" data-cot-sort="${key}" aria-label="Sort by ${escapeHtml(label)}" aria-pressed="${active}" data-sort-direction="${direction}">${escapeHtml(label)} <span aria-hidden="true">${marker}</span></button>`;
  }

  function shareCell(value, tone) {
    if (value === null || value === undefined) return '<span class="cot-share-empty">Not reported</span>';
    return `<div class="cot-share-cell"><strong>${number(value, 1)}%</strong><span class="cot-share-meter" aria-hidden="true"><i class="${tone}" style="width:${Math.max(0, Math.min(100, value)).toFixed(1)}%"></i></span></div>`;
  }

  function analysisTable(rowsToShow) {
    if (!rowsToShow.length) return '<div class="cot-empty">No verified exact contracts match these filters.</div>';
    return `<div class="cot-analysis-table-scroll"><table class="cot-analysis-table">
      <thead><tr>
        <th scope="col">${sortButton('name', 'Market')}</th>
        <th scope="col">Position</th>
        <th scope="col">Weekly flow</th>
        <th scope="col">${sortButton('longShare', 'Long %')}</th>
        <th scope="col">Prev long %</th>
        <th scope="col">Short %</th>
        <th scope="col">Prev short %</th>
        <th scope="col">${sortButton('net', 'Net position')}</th>
        <th scope="col">Previous net</th>
        <th scope="col">${sortButton('weekChange', '1W change')}</th>
        <th scope="col">Report</th>
      </tr></thead>
      <tbody>${rowsToShow.map((row) => {
        const pair = historyPair(row);
        const current = shares(pair.current);
        const previous = pair.previous ? shares(pair.previous) : null;
        const positive = Number(row.net) >= 0;
        const flowPositive = Number(row.weekChange) >= 0;
        return `<tr class="${state.selectedId === row.id ? 'selected' : ''}">
          <th scope="row"><button type="button" data-cot-select="${escapeHtml(row.id)}"><strong>${escapeHtml(row.name)}${row.dataState === 'stale-retained' ? ' <em class="cot-retained-badge">retained</em>' : ''}</strong><span>${escapeHtml(row.contract?.cftcContractCode || '')} · ${escapeHtml(row.contract?.exchange || '')}</span><small>${escapeHtml(row.category || '')}</small></button></th>
          <td><span class="cot-signal ${positive ? 'positive' : 'negative'}">${positionLabel(row)}</span></td>
          <td><span class="cot-flow ${flowPositive ? 'positive' : 'negative'}">${flowLabel(row)}</span></td>
          <td>${shareCell(current.long, 'long')}</td>
          <td class="cot-previous">${previous?.available ? `${number(previous.long, 1)}%` : '—'}</td>
          <td>${shareCell(current.short, 'short')}</td>
          <td class="cot-previous">${previous?.available ? `${number(previous.short, 1)}%` : '—'}</td>
          <td class="cot-contract-value ${positive ? 'positive' : 'negative'}">${signed(row.net)}</td>
          <td class="cot-previous">${pair.previous ? signed(pair.previous.net) : '—'}</td>
          <td><span class="cot-change ${flowPositive ? 'positive' : 'negative'}">${signed(row.weekChange)} <i aria-hidden="true">${flowPositive ? '↗' : '↘'}</i></span></td>
          <td class="cot-report-date">${escapeHtml(formatDate(row.reportDate))}</td>
        </tr>`;
      }).join('')}</tbody>
    </table></div>`;
  }

  function historyChart(row) {
    const history = Array.isArray(row?.history52) ? row.history52 : [];
    if (history.length < 2) return '<div class="cot-empty-chart">History unavailable for this exact contract.</div>';
    const values = history.map((point) => Number(point.net || 0));
    const min = Math.min(...values, 0);
    const max = Math.max(...values, 0);
    const span = max - min || 1;
    const width = 900;
    const height = 210;
    const xFor = (index) => 16 + (index / (values.length - 1)) * (width - 32);
    const yFor = (value) => 14 + ((max - value) / span) * (height - 34);
    const points = values.map((value, index) => `${xFor(index).toFixed(1)},${yFor(value).toFixed(1)}`).join(' ');
    const zeroY = yFor(0);
    const summary = `${row.name} net positioning history from ${history[0]?.date || ''} to ${history.at(-1)?.date || ''}. Latest ${signed(values.at(-1))} net contracts.`;
    return `<figure class="cot-history-figure">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotHistoryTitle cotHistoryDesc" preserveAspectRatio="none">
        <title id="cotHistoryTitle">${escapeHtml(row.name)} 52-week net positioning</title>
        <desc id="cotHistoryDesc">${escapeHtml(summary)}</desc>
        <defs><linearGradient id="cotHistoryArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#a970ff" stop-opacity=".32"></stop><stop offset="100%" stop-color="#a970ff" stop-opacity="0"></stop></linearGradient></defs>
        <line class="cot-zero-line" x1="0" x2="${width}" y1="${zeroY}" y2="${zeroY}"></line>
        <polygon class="cot-history-area" points="16,${height - 20} ${points} ${width - 16},${height - 20}"></polygon>
        <polyline class="cot-history-line" points="${points}"></polyline>
      </svg>
      <figcaption><span>${escapeHtml(formatDate(history[0]?.date))}</span><strong>${escapeHtml(signed(values.at(-1)))} net</strong><span>${escapeHtml(formatDate(history.at(-1)?.date))}</span></figcaption>
    </figure>`;
  }

  function detail(row) {
    if (!row) return '<div class="cot-empty">Select a verified contract to inspect its history and provenance.</div>';
    const contract = row.contract || {};
    return `<article class="cot-detail-card">
      <header><div><span class="cot-kicker">Selected exact contract</span><h3>${escapeHtml(row.name)}</h3><p>${escapeHtml(contract.marketName || row.market)}</p></div><span class="cot-identity ${row.dataState === 'stale-retained' ? 'retained' : ''}">${row.dataState === 'stale-retained' ? 'Previously verified · retained' : `✓ ${escapeHtml(contract.identityStatus || 'unknown')} identity`}</span></header>
      <div class="cot-detail-metrics">
        <div><span>Net position</span><strong class="${Number(row.net) >= 0 ? 'positive' : 'negative'}">${signed(row.net)}</strong></div>
        <div><span>1-week change</span><strong class="${Number(row.weekChange) >= 0 ? 'positive' : 'negative'}">${signed(row.weekChange)}</strong></div>
        <div><span>5-year percentile</span><strong>${row.netPercentile5y === null ? '—' : `${number(row.netPercentile5y, 1)}%`}</strong></div>
        <div><span>Open interest</span><strong>${number(row.openInterest)}</strong></div>
      </div>
      ${historyChart(row)}
      <footer><div><strong>${escapeHtml(contract.reportType || contract.category || row.category || 'CFTC report')}</strong><span>${escapeHtml(contract.cftcContractCode || 'No code')} · ${escapeHtml(contract.exchange || 'No exchange')} · observed ${escapeHtml(formatDate(row.reportDate))}</span></div><a href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open official CFTC source ↗</a></footer>
    </article>`;
  }

  function render() {
    const host = document.getElementById('view-cot');
    if (!host) return;
    const filtered = visibleRows();
    if (!filtered.some((row) => row.id === state.selectedId)) state.selectedId = filtered[0]?.id || null;
    const selected = rows.find((row) => row.id === state.selectedId) || null;
    const status = sourceStatus();
    const categories = Object.keys(CATEGORY_LABELS);
    const coverage = referenceCoverage();
    const latest = rows.map((row) => row.reportDate).filter(Boolean).sort().at(-1) || '';
    const coverageDetails = coverage.unavailable.map((item) => `<li><strong>${escapeHtml(item.label || item.id)}</strong><span>${escapeHtml(item.reason || 'No verified current observation is available.')}</span></li>`).join('');

    host.dataset.cotRemodel = 'reference-dashboard';
    host.innerHTML = `<div class="cot-page">
      <header class="cot-report-header">
        <div><span class="cot-kicker">Official weekly positioning</span><h2>COT positioning</h2><p>Commitment of Traders positioning analysis using only verified exact CFTC contracts.</p></div>
        <div class="cot-report-status"><span class="data-state ${escapeHtml(String(status.status || 'unavailable').toLowerCase())}">${escapeHtml(status.status || 'Unavailable')}</span><strong>${escapeHtml(formatDate(latest))}</strong><small>Generated ${escapeHtml(official.generatedAt || 'unknown')}</small></div>
      </header>
      <section class="cot-coverage-status" aria-label="Reference product coverage">
        <div><span class="cot-kicker">Reference coverage</span><strong>${coverage.loaded} of ${coverage.total} products available</strong><small>${coverage.currentCount} current${coverage.retainedCount ? ` · ${coverage.retainedCount} previously verified and retained` : ''}</small></div>
        ${coverage.unavailable.length ? `<details><summary>${coverage.unavailable.length} unavailable product${coverage.unavailable.length === 1 ? '' : 's'}</summary><ul>${coverageDetails}</ul></details>` : '<span class="cot-coverage-complete">All reference products loaded</span>'}
      </section>
      <section class="cot-filter-stack" aria-label="COT filters">
        <label class="cot-search"><span class="sr-only">Search contract, code or exchange</span><i aria-hidden="true">⌕</i><input id="cotWorkspaceSearch" type="search" value="${escapeHtml(state.query)}" placeholder="Search markets, codes or exchanges…" autocomplete="off"></label>
        <div class="cot-category-filters" role="group" aria-label="Market category">${categories.map((category) => `<button type="button" data-cot-category="${category}" aria-pressed="${state.category === category}">${escapeHtml(CATEGORY_LABELS[category] || category)}</button>`).join('')}</div>
      </section>
      <section class="cot-positioning-panel" aria-labelledby="cotPositioningHeading">
        <div class="cot-panel-heading"><div><span class="cot-kicker">Cross-market comparison</span><h3 id="cotPositioningHeading">Position distribution</h3><p>Normalised within each market; contract sizes are not comparable across markets.</p></div><div class="cot-mode-tabs" role="group" aria-label="Chart metric">${[['balance', 'Long / short'], ['net', 'Net position'], ['change', 'Weekly change']].map(([mode, label]) => `<button type="button" data-cot-mode="${mode}" aria-pressed="${state.mode === mode}">${label}</button>`).join('')}</div></div>
        <div class="cot-chart-legend" aria-label="Chart legend"><span class="long"><i></i>Long %</span><span class="short"><i></i>Short %</span><span>${filtered.length} verified market${filtered.length === 1 ? '' : 's'}</span></div>
        ${positioningChart(filtered)}
      </section>
      <section class="cot-analysis-section" aria-labelledby="cotAnalysisHeading">
        <div class="cot-panel-heading"><div><span class="cot-kicker">Latest versus previous report</span><h3 id="cotAnalysisHeading">Recent COT data analysis</h3></div><span class="cot-table-date">${escapeHtml(formatDate(latest))}</span></div>
        ${analysisTable(filtered)}
      </section>
      <section aria-live="polite">${detail(selected)}</section>
      <details class="cot-methodology"><summary>Source, methodology and limitations</summary><div class="cot-methodology-grid"><p>${escapeHtml(status.detail || 'Exact-contract cache status')}</p><p>${escapeHtml(official.methodology?.cot || 'CFTC weekly observations selected by exact verified contract code and accepted market identity.')}</p><p>${escapeHtml(official.methodology?.warning || 'Unavailable intended benchmarks remain unavailable rather than being replaced with similar contracts.')}</p></div>${status.url ? `<a href="${escapeHtml(status.url)}" target="_blank" rel="noopener noreferrer">Open CFTC source status ↗</a>` : ''}</details>
    </div>`;

    host.querySelector('#cotWorkspaceSearch')?.addEventListener('input', (event) => {
      state.query = event.target.value;
      const cursor = event.target.selectionStart;
      render();
      const input = host.querySelector('#cotWorkspaceSearch');
      input?.focus();
      input?.setSelectionRange(cursor, cursor);
    });
    host.querySelectorAll('[data-cot-category]').forEach((button) => button.addEventListener('click', () => {
      state.category = button.dataset.cotCategory;
      render();
    }));
    host.querySelectorAll('[data-cot-mode]').forEach((button) => button.addEventListener('click', () => {
      state.mode = button.dataset.cotMode;
      render();
    }));
    host.querySelectorAll('[data-cot-sort]').forEach((button) => button.addEventListener('click', () => {
      const key = button.dataset.cotSort;
      if (state.sortKey === key) state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
      else {
        state.sortKey = key;
        state.sortDirection = key === 'name' ? 'asc' : 'desc';
      }
      render();
    }));
    host.querySelectorAll('[data-cot-select]').forEach((button) => button.addEventListener('click', () => {
      state.selectedId = button.dataset.cotSelect;
      render();
      host.querySelector('.cot-detail-card')?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }));
    host.querySelectorAll('[data-cot-chart-select]').forEach((group) => {
      const select = () => {
        state.selectedId = group.dataset.cotChartSelect;
        render();
      };
      group.addEventListener('click', select);
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          select();
        }
      });
    });
  }

  function initialise() {
    if (!document.getElementById('view-cot')) return;
    render();
    core.router?.subscribe?.((route) => { if (route.name === 'cot') render(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
})();
