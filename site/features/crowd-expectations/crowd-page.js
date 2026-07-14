(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const state = { category: 'all', grade: 'all', query: '', sort: 'signal' };
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  function data() {
    return window.crowdExpectationsData || {
      generatedAtUtc: null,
      provider: { readOnly: true },
      collection: {},
      categories: [],
      markets: [],
      shocks: [],
      methodology: {}
    };
  }

  function statusClass(value = '') {
    const text = String(value).toLowerCase();
    if (text === 'current') return 'current';
    if (['partial', 'delayed', 'unknown'].includes(text)) return 'partial';
    return 'stale';
  }

  function label(value = '') {
    return String(value).replaceAll('-', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function formatDate(value) {
    if (!value) return 'Unavailable';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat('en-AU', {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: 'Australia/Melbourne'
    }).format(date);
  }

  function money(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '—';
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'USD',
      notation: numeric >= 1000000 ? 'compact' : 'standard',
      maximumFractionDigits: numeric >= 1000000 ? 1 : 0
    }).format(numeric);
  }

  function signedPoints(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    const numeric = Number(value);
    return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)} pts`;
  }

  function probability(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    return `${Number(value).toFixed(1)}%`;
  }

  function ensureHost() {
    let node = document.getElementById('view-crowd-expectations');
    if (node) return node;
    const content = document.querySelector('main .content') || document.querySelector('main') || document.body;
    node = document.createElement('section');
    node.id = 'view-crowd-expectations';
    node.className = 'view';
    node.dataset.dynamicView = 'crowd-expectations';
    const footer = content.querySelector('.footer');
    if (footer) content.insertBefore(node, footer);
    else content.appendChild(node);
    return node;
  }

  function navigate() {
    if (router) router.navigate('crowd-expectations', { replace: true });
    else window.location.hash = '#crowd-expectations';
  }

  function ensureNavigation() {
    const nav = document.getElementById('nav');
    if (nav && !nav.querySelector('[data-view="crowd-expectations"]')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'nav-item';
      button.dataset.view = 'crowd-expectations';
      button.setAttribute('aria-label', 'Crowd Expectations');
      button.title = 'Crowd Expectations';
      button.innerHTML = '<span class="nav-icon" aria-hidden="true">◉</span><span class="nav-label">Crowd Expectations</span>';
      button.addEventListener('click', navigate);
      const official = nav.querySelector('[data-view="official-feeds"]');
      if (official) official.insertAdjacentElement('afterend', button);
      else nav.appendChild(button);
    }

    const grid = document.querySelector('#mobileMore .mobile-more-grid');
    if (grid && !grid.querySelector('[data-shell-view="crowd-expectations"]')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.shellView = 'crowd-expectations';
      button.textContent = 'Crowd Expectations';
      button.addEventListener('click', navigate);
      grid.prepend(button);
    }
  }

  function activate() {
    ensureHost();
    if (views?.activate('crowd-expectations', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => {
      node.classList.toggle('active', node.id === 'view-crowd-expectations');
    });
  }

  function visibleMarkets() {
    const query = state.query.trim().toLowerCase();
    const rows = (data().markets || []).filter((market) => {
      const categoryMatch = state.category === 'all' || market.categoryId === state.category;
      const gradeMatch = state.grade === 'all' || market.qualityGrade === state.grade;
      const haystack = `${market.question} ${market.eventTitle || ''} ${market.category} ${(market.assets || []).join(' ')}`.toLowerCase();
      return categoryMatch && gradeMatch && (!query || haystack.includes(query));
    });
    return rows.sort((a, b) => {
      if (state.sort === 'move') return Math.abs(Number(b.change24hPoints || 0)) - Math.abs(Number(a.change24hPoints || 0));
      if (state.sort === 'probability') return Number(b.probabilityPercent || 0) - Number(a.probabilityPercent || 0);
      if (state.sort === 'liquidity') return Number(b.liquidity || 0) - Number(a.liquidity || 0);
      return (Number(b.qualityScore || 0) + Number(b.relevanceScore || 0) * 2)
        - (Number(a.qualityScore || 0) + Number(a.relevanceScore || 0) * 2);
    });
  }

  function historySparkline(market) {
    const points = market.history || [];
    if (points.length < 2) return '<div class="crowd-history-empty">History begins after repeated daily collections.</div>';
    const values = points.map((point) => Number(point.probability) * 100);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = Math.max(1, max - min);
    const coordinates = values.map((value, index) => {
      const x = values.length === 1 ? 50 : (index / (values.length - 1)) * 100;
      const y = 92 - ((value - min) / range) * 84;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(' ');
    return `<div class="crowd-sparkline" aria-label="${escapeHtml(points.length)} day probability history">
      <svg viewBox="0 0 100 100" role="img" aria-hidden="true"><polyline points="${coordinates}"></polyline></svg>
      <span>${escapeHtml(points[0].date)}</span><span>${escapeHtml(points.at(-1).date)}</span>
    </div>`;
  }

  function marketCard(market) {
    const moveClass = Number(market.change24hPoints || 0) > 0 ? 'up' : Number(market.change24hPoints || 0) < 0 ? 'down' : 'flat';
    const spread = market.spread === null || market.spread === undefined ? '—' : `${(Number(market.spread) * 100).toFixed(2)} pts`;
    return `<article class="crowd-market-card" data-grade="${escapeHtml(market.qualityGrade)}">
      <header>
        <div><span class="crowd-category">${escapeHtml(market.category)}</span><span class="crowd-grade grade-${escapeHtml(market.qualityGrade.toLowerCase())}">Quality ${escapeHtml(market.qualityGrade)} · ${escapeHtml(market.qualityScore)}</span></div>
        <span class="crowd-move ${moveClass}">${escapeHtml(signedPoints(market.change24hPoints))}</span>
      </header>
      <h3>${escapeHtml(market.question)}</h3>
      <div class="crowd-probability"><strong>${escapeHtml(probability(market.probabilityPercent))}</strong><span>YES · ${escapeHtml(market.probabilitySource)}</span></div>
      ${historySparkline(market)}
      <dl>
        <div><dt>7-day move</dt><dd>${escapeHtml(signedPoints(market.change7dPoints))}</dd></div>
        <div><dt>Spread</dt><dd>${escapeHtml(spread)}</dd></div>
        <div><dt>Liquidity</dt><dd>${escapeHtml(money(market.liquidity))}</dd></div>
        <div><dt>24h volume</dt><dd>${escapeHtml(money(market.volume24h))}</dd></div>
        <div><dt>Closes</dt><dd>${escapeHtml(formatDate(market.endDate))}</dd></div>
        <div><dt>Observed</dt><dd>${escapeHtml(formatDate(market.updatedAt))}</dd></div>
      </dl>
      <div class="crowd-assets">${(market.assets || []).map((asset) => `<span>${escapeHtml(label(asset))}</span>`).join('')}</div>
      <details><summary>Resolution and quality detail</summary>
        <p>${escapeHtml(market.description || 'No market description supplied.')}</p>
        <ul>${(market.qualityReasons || []).map((reason) => `<li>${escapeHtml(reason)}</li>`).join('')}</ul>
        <p><strong>Resolution source:</strong> ${market.resolutionSource ? `<a href="${escapeHtml(market.resolutionSource)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : 'Not supplied by market'}</p>
      </details>
      <a class="crowd-source-link" href="${escapeHtml(market.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open market page ↗</a>
    </article>`;
  }

  function shockRows(current) {
    const rows = current.shocks || [];
    if (!rows.length) return '<div class="crowd-empty">No five-point, quality-qualified 24-hour probability shock is currently detected.</div>';
    return rows.slice(0, 6).map((shock) => `<article>
      <div><strong>${escapeHtml(shock.question)}</strong><span>${escapeHtml(probability(shock.probabilityPercent))} current probability</span></div>
      <span class="crowd-move ${Number(shock.change24hPoints) >= 0 ? 'up' : 'down'}">${escapeHtml(signedPoints(shock.change24hPoints))}</span>
      <small>Quality ${escapeHtml(shock.qualityGrade)} · ${(shock.assets || []).map(label).join(', ')}</small>
    </article>`).join('');
  }

  function render() {
    const root = ensureHost();
    const current = data();
    const rows = visibleMarkets();
    const grades = ['all', 'A', 'B', 'C', 'D'];
    root.dataset.crowdExpectations = 'br-22';
    root.innerHTML = `<div class="crowd-page">
      <header class="crowd-hero">
        <div><span class="crowd-kicker">Read-only event markets</span><h2>Crowd Expectations</h2><p>Market-implied event probabilities for macro, policy, geopolitics, commodities and technology. These are crowd prices—not forecasts, truth estimates or trade recommendations.</p></div>
        <div class="crowd-hero-meta"><span class="data-state ${statusClass(current.collection?.status)}">${escapeHtml(label(current.collection?.status || 'unknown'))}</span><strong>${escapeHtml(current.collection?.selectedMarketCount || 0)} relevant markets</strong><small>Generated ${escapeHtml(formatDate(current.generatedAtUtc))}</small></div>
      </header>
      <div class="crowd-jurisdiction"><strong>Australia: read-only</strong><span>${escapeHtml(current.provider?.jurisdictionNote || 'No order functionality is included.')}</span></div>
      <section class="crowd-summary" aria-label="Crowd expectation totals">
        <article><span>Active scanned</span><strong>${escapeHtml(current.collection?.rawMarketCount || 0)}</strong></article>
        <article><span>Relevant retained</span><strong>${escapeHtml(current.collection?.selectedMarketCount || 0)}</strong></article>
        <article><span>Crowd shocks</span><strong>${escapeHtml((current.shocks || []).length)}</strong></article>
        <article><span>Provider mode</span><strong>Read-only</strong></article>
      </section>
      <section class="crowd-shocks"><div class="crowd-heading"><div><span class="crowd-kicker">Largest qualified changes</span><h3>Crowd probability shocks</h3></div><span>≥5 points in 24h · Quality A/B</span></div><div class="crowd-shock-list">${shockRows(current)}</div></section>
      <section class="crowd-controls" aria-label="Crowd expectation filters">
        <label>Search<input data-crowd-query type="search" value="${escapeHtml(state.query)}" placeholder="Fed, tariff, Taiwan, oil, chips…" /></label>
        <label>Category<select data-crowd-category><option value="all">All categories</option>${(current.categories || []).map((category) => `<option value="${escapeHtml(category.id)}"${state.category === category.id ? ' selected' : ''}>${escapeHtml(category.name)} (${escapeHtml(category.count)})</option>`).join('')}</select></label>
        <label>Quality<select data-crowd-grade>${grades.map((grade) => `<option value="${grade}"${state.grade === grade ? ' selected' : ''}>${grade === 'all' ? 'All grades' : `Grade ${grade}`}</option>`).join('')}</select></label>
        <label>Sort<select data-crowd-sort><option value="signal"${state.sort === 'signal' ? ' selected' : ''}>Signal quality</option><option value="move"${state.sort === 'move' ? ' selected' : ''}>Largest 24h move</option><option value="probability"${state.sort === 'probability' ? ' selected' : ''}>Highest probability</option><option value="liquidity"${state.sort === 'liquidity' ? ' selected' : ''}>Highest liquidity</option></select></label>
      </section>
      ${current.collection?.error ? `<div class="crowd-error"><strong>Collector note</strong><span>${escapeHtml(current.collection.error)}</span></div>` : ''}
      <section class="crowd-grid">${rows.length ? rows.map(marketCard).join('') : '<div class="crowd-empty">No markets match the current filters, or the first collection has not completed.</div>'}</section>
      <details class="crowd-methodology"><summary>Methodology and limitations</summary>${Object.entries(current.methodology || {}).map(([key, value]) => `<p><strong>${escapeHtml(label(key))}:</strong> ${escapeHtml(value)}</p>`).join('')}</details>
    </div>`;

    root.querySelector('[data-crowd-query]')?.addEventListener('input', (event) => { state.query = event.target.value; render(); });
    root.querySelector('[data-crowd-category]')?.addEventListener('change', (event) => { state.category = event.target.value; render(); });
    root.querySelector('[data-crowd-grade]')?.addEventListener('change', (event) => { state.grade = event.target.value; render(); });
    root.querySelector('[data-crowd-sort]')?.addEventListener('change', (event) => { state.sort = event.target.value; render(); });
  }

  function show() {
    activate();
    render();
  }

  function register() {
    if (!router || register.done) return;
    register.done = true;
    ensureNavigation();
    ensureHost();
    router.register('crowd-expectations', show);
    router.register('crowd', show);
    const current = router.current?.();
    if (current?.path === 'crowd-expectations' || current?.path === 'crowd') {
      router.dispatch(`#${current.path}`, { source: 'crowd-expectations-ready' });
    }
  }

  window.addEventListener('marketbrief:crowd-data', () => {
    if (document.getElementById('view-crowd-expectations')?.classList.contains('active')) render();
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', register, { once: true });
  else register();
  window.addEventListener('load', register, { once: true });
})();
