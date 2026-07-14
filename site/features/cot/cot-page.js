(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const rows = Array.isArray(official.cot) ? official.cot.filter((row) => row?.contract?.identityStatus === 'verified') : [];
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const number = core.format?.formatNumber || ((value, digits = 0) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(undefined, { maximumFractionDigits: digits }));
  const signed = core.format?.signed || ((value) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : `${Number(value) > 0 ? '+' : ''}${number(value)}`);

  const CATEGORY_LABELS = Object.freeze({ all: 'All', metals: 'Metals', energy: 'Energy', currencies: 'Currencies', rates: 'Rates', indices: 'Indices', other: 'Other' });
  const ID_CATEGORIES = Object.freeze({ gold: 'metals', silver: 'metals', copper: 'metals', yen: 'currencies', 'usd-index': 'currencies', 'us10y-futures': 'rates' });
  const state = { category: 'all', query: '', mode: 'net', selectedId: rows[0]?.id || null };

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

  function metricValue(point, index, history) {
    if (state.mode === 'balance') {
      const gross = Number(point.long || 0) + Number(point.short || 0);
      return gross ? (Number(point.long || 0) / gross) * 100 : 50;
    }
    if (state.mode === 'change') return index ? Number(point.net || 0) - Number(history[index - 1].net || 0) : 0;
    return Number(point.net || 0);
  }

  function metricLabel(value) {
    if (state.mode === 'balance') return `${number(value, 1)}% long share`;
    if (state.mode === 'change') return `${signed(value)} weekly net change`;
    return `${signed(value)} net contracts`;
  }

  function visibleRows() {
    const query = state.query.trim().toLowerCase();
    return rows.filter((row) => {
      const categoryMatch = state.category === 'all' || categoryFor(row) === state.category;
      const contract = row.contract || {};
      const haystack = [row.id, row.name, row.market, row.category, contract.exchange, contract.cftcContractCode, contract.reportType].join(' ').toLowerCase();
      return categoryMatch && (!query || haystack.includes(query));
    });
  }

  function sourceStatus() {
    const cftc = (official.sourceStatus || []).find((item) => String(item.source || '').toLowerCase().includes('cftc'));
    if (!cftc) return { status: rows.length ? 'current' : 'unavailable', detail: rows.length ? 'Verified exact-contract cache loaded.' : 'No verified CFTC rows are available.', url: rows[0]?.sourceUrl || '#' };
    return cftc;
  }

  function sparkline(row) {
    const history = Array.isArray(row.history52) ? row.history52 : [];
    if (history.length < 2) return '<div class="cot-empty-chart">History unavailable for this exact contract.</div>';
    const values = history.map(metricValue);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const width = 720;
    const height = 220;
    const points = values.map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - 18 - ((value - min) / span) * (height - 36);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
    const latest = values.at(-1);
    const firstDate = history[0]?.date || '';
    const lastDate = history.at(-1)?.date || '';
    const summary = `${row.name} ${state.mode} history from ${firstDate} to ${lastDate}. Latest ${metricLabel(latest)}; range ${metricLabel(min)} to ${metricLabel(max)}.`;
    return `<figure class="cot-history-figure">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="cotChartTitle cotChartDesc" preserveAspectRatio="none">
        <title id="cotChartTitle">${escapeHtml(row.name)} positioning history</title>
        <desc id="cotChartDesc">${escapeHtml(summary)}</desc>
        <line class="cot-zero-line" x1="0" x2="${width}" y1="${height / 2}" y2="${height / 2}"></line>
        <polyline class="cot-history-line" points="${points}"></polyline>
      </svg>
      <figcaption><span>${escapeHtml(firstDate)}</span><strong>${escapeHtml(metricLabel(latest))}</strong><span>${escapeHtml(lastDate)}</span></figcaption>
      <p class="sr-only">${escapeHtml(summary)}</p>
    </figure>`;
  }

  function balanceBar(row) {
    const gross = Number(row.long || 0) + Number(row.short || 0);
    const longShare = gross ? (Number(row.long || 0) / gross) * 100 : 50;
    return `<div class="cot-balance" aria-label="Long ${number(longShare, 1)} percent; short ${number(100 - longShare, 1)} percent">
      <span class="cot-balance-long" style="width:${longShare.toFixed(1)}%"></span>
      <span class="cot-balance-short" style="width:${(100 - longShare).toFixed(1)}%"></span>
    </div><small>${number(longShare, 1)}% long / ${number(100 - longShare, 1)}% short</small>`;
  }

  function overview(rowsToShow) {
    if (!rowsToShow.length) return '<div class="cot-empty">No verified exact contracts match these filters.</div>';
    return rowsToShow.map((row) => {
      const value = state.mode === 'balance'
        ? balanceBar(row)
        : `<strong class="cot-overview-value">${state.mode === 'change' ? signed(row.weekChange) : signed(row.net)}</strong><small>${state.mode === 'change' ? 'weekly net change' : `${row.crowding} · ${row.netPercentile5y === null ? 'percentile unavailable' : `${number(row.netPercentile5y, 1)}th percentile`}`}</small>`;
      return `<button type="button" class="cot-overview-card ${state.selectedId === row.id ? 'selected' : ''}" data-cot-select="${escapeHtml(row.id)}" aria-pressed="${state.selectedId === row.id}">
        <span class="cot-overview-head"><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(CATEGORY_LABELS[categoryFor(row)] || 'Other')}</span></span>
        ${value}
        <span class="cot-overview-contract">${escapeHtml(row.contract?.cftcContractCode || 'No code')} · ${escapeHtml(row.category || 'No category')}</span>
      </button>`;
    }).join('');
  }

  function table(rowsToShow) {
    if (!rowsToShow.length) return '<div class="cot-empty">No verified exact contracts match these filters.</div>';
    return `<div class="cot-table-scroll"><table class="cot-dense-table">
      <thead><tr><th scope="col">Market / exact contract</th><th scope="col">Report category</th><th scope="col">Long</th><th scope="col">Short</th><th scope="col">Net</th><th scope="col">1 week</th><th scope="col">4 weeks</th><th scope="col">Open interest</th><th scope="col">5-year percentile</th><th scope="col">Report date</th></tr></thead>
      <tbody>${rowsToShow.map((row) => `<tr class="${state.selectedId === row.id ? 'selected' : ''}">
        <th scope="row"><button type="button" data-cot-select="${escapeHtml(row.id)}"><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.contract?.marketName || row.market)}</span><small>${escapeHtml(row.contract?.cftcContractCode || '')} · ${escapeHtml(row.contract?.exchange || '')}</small></button></th>
        <td>${escapeHtml(row.category)}</td><td>${number(row.long)}</td><td>${number(row.short)}</td>
        <td><span class="cot-number ${Number(row.net) >= 0 ? 'positive' : 'negative'}">${Number(row.net) >= 0 ? 'Net long ' : 'Net short '}${signed(row.net)}</span></td>
        <td>${signed(row.weekChange)}</td><td>${signed(row.fourWeekChange)}</td><td>${number(row.openInterest)}</td>
        <td>${row.netPercentile5y === null ? '—' : `${number(row.netPercentile5y, 1)}%`}</td><td>${escapeHtml(row.reportDate)}</td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  }

  function detail(row) {
    if (!row) return '<div class="cot-empty">Select a verified contract to inspect its history and provenance.</div>';
    const contract = row.contract || {};
    return `<article class="cot-detail-card">
      <header><div><span class="cot-kicker">Selected exact contract</span><h3>${escapeHtml(row.name)}</h3><p>${escapeHtml(contract.marketName || row.market)}</p></div><span class="cot-identity">✓ ${escapeHtml(contract.identityStatus || 'unknown')} identity</span></header>
      <div class="cot-detail-grid">
        <dl><div><dt>CFTC contract code</dt><dd>${escapeHtml(contract.cftcContractCode || 'Unavailable')}</dd></div><div><dt>Exchange</dt><dd>${escapeHtml(contract.exchange || 'Unavailable')}</dd></div><div><dt>Report family</dt><dd>${escapeHtml(contract.reportType || 'Unavailable')}</dd></div><div><dt>Report category</dt><dd>${escapeHtml(contract.category || row.category || 'Unavailable')}</dd></div></dl>
        <dl><div><dt>Long</dt><dd>${number(row.long)}</dd></div><div><dt>Short</dt><dd>${number(row.short)}</dd></div><div><dt>Net</dt><dd>${signed(row.net)}</dd></div><div><dt>Open interest</dt><dd>${number(row.openInterest)}</dd></div></dl>
      </div>
      ${sparkline(row)}
      <footer><div><strong>Observation</strong><span>${escapeHtml(row.reportDate)} · ${escapeHtml(row.dataMethod || 'CFTC exact-contract registry')}</span></div><a href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open official CFTC source ↗</a></footer>
    </article>`;
  }

  function render() {
    const host = document.getElementById('view-cot');
    if (!host) return;
    const filtered = visibleRows();
    if (!filtered.some((row) => row.id === state.selectedId)) state.selectedId = filtered[0]?.id || null;
    const selected = rows.find((row) => row.id === state.selectedId) || null;
    const status = sourceStatus();
    const categories = ['all', ...new Set(rows.map(categoryFor))];
    const latest = rows.map((row) => row.reportDate).filter(Boolean).sort().at(-1) || 'Unavailable';

    host.dataset.cotRemodel = 'br-07';
    host.innerHTML = `<div class="cot-page">
      <header class="cot-page-header"><div><span class="cot-kicker">Official weekly positioning</span><h2>COT Positioning</h2><p>Compare only verified exact CFTC contracts. Commodity rows use Managed Money; selected financial futures use Leveraged Funds.</p></div><div class="cot-freshness"><span class="data-state ${escapeHtml(String(status.status || 'unavailable').toLowerCase())}">${escapeHtml(status.status || 'Unavailable')}</span><strong>Latest report ${escapeHtml(latest)}</strong><small>Cache generated ${escapeHtml(official.generatedAt || 'unknown')}</small></div></header>
      <section class="cot-controls" aria-label="COT filters">
        <label class="cot-search"><span>Search contract, code or exchange</span><input id="cotWorkspaceSearch" type="search" value="${escapeHtml(state.query)}" placeholder="Gold, 088691, CBOT…" autocomplete="off"></label>
        <div class="cot-category-filters" role="group" aria-label="Market category">${categories.map((category) => `<button type="button" data-cot-category="${category}" aria-pressed="${state.category === category}">${escapeHtml(CATEGORY_LABELS[category] || category)}</button>`).join('')}</div>
        <div class="cot-mode-tabs" role="group" aria-label="Overview mode">${[['net', 'Net position'], ['balance', 'Long / short'], ['change', 'Weekly change']].map(([mode, label]) => `<button type="button" data-cot-mode="${mode}" aria-pressed="${state.mode === mode}">${label}</button>`).join('')}</div>
      </section>
      <section class="cot-source-banner" aria-label="CFTC source status"><div><strong>${escapeHtml(status.source || 'CFTC Commitments of Traders')}</strong><span>${escapeHtml(status.detail || 'Exact-contract cache status')}</span></div>${status.url ? `<a href="${escapeHtml(status.url)}" target="_blank" rel="noopener noreferrer">Official source ↗</a>` : ''}</section>
      <section><div class="cot-section-heading"><div><span class="cot-kicker">Overview</span><h3>${escapeHtml(CATEGORY_LABELS[state.category] || 'Filtered')} contracts</h3></div><span>${filtered.length} verified market${filtered.length === 1 ? '' : 's'}</span></div><div class="cot-overview-grid">${overview(filtered)}</div></section>
      <section><div class="cot-section-heading"><div><span class="cot-kicker">Comparison</span><h3>Exact-contract positioning table</h3></div><span>Values are contracts, not trader counts</span></div>${table(filtered)}</section>
      <section aria-live="polite">${detail(selected)}</section>
      <details class="cot-methodology"><summary>Methodology and limitations</summary><p>${escapeHtml(official.methodology?.cot || 'CFTC weekly observations selected by exact verified contract code and accepted market identity.')}</p><p>${escapeHtml(official.methodology?.warning || 'Unavailable intended benchmarks remain unavailable rather than being replaced with similar contracts.')}</p><p>Long, short and net values always refer to the report category named above. Percentiles compare net positioning with available five-year history and are not price forecasts.</p></details>
    </div>`;

    host.querySelector('#cotWorkspaceSearch')?.addEventListener('input', (event) => { state.query = event.target.value; render(); });
    host.querySelectorAll('[data-cot-category]').forEach((button) => button.addEventListener('click', () => { state.category = button.dataset.cotCategory; render(); }));
    host.querySelectorAll('[data-cot-mode]').forEach((button) => button.addEventListener('click', () => { state.mode = button.dataset.cotMode; render(); }));
    host.querySelectorAll('[data-cot-select]').forEach((button) => button.addEventListener('click', () => { state.selectedId = button.dataset.cotSelect; render(); host.querySelector('.cot-detail-card')?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }));
  }

  function initialise() {
    if (!document.getElementById('view-cot')) return;
    render();
    core.router?.subscribe?.((route) => { if (route.name === 'cot') render(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
})();
