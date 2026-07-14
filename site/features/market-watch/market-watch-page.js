(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const state = { group: 'all', status: 'all', query: '', sort: 'absolute-day' };
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  function data() { return core.adapters?.equities?.() || window.equityMarketData || { collection: {}, provider: {}, watchlist: [], methodology: {} }; }
  function label(value = '') { return String(value).replaceAll('-', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
  function statusClass(value = '') { return ['failed', 'stale', 'unavailable'].includes(value) ? 'stale' : ['partial', 'delayed', 'unknown'].includes(value) ? 'partial' : 'current'; }
  function moveClass(value) { return Number(value) > 0 ? 'up' : Number(value) < 0 ? 'down' : 'flat'; }
  function percent(value, sign = true) { return value === null || value === undefined || !Number.isFinite(Number(value)) ? '—' : `${sign && Number(value) > 0 ? '+' : ''}${Number(value).toFixed(2)}%`; }
  function money(row) { if (row.price === null || row.price === undefined) return '—'; return new Intl.NumberFormat('en-AU', { style: 'currency', currency: row.currency || 'USD', maximumFractionDigits: Number(row.price) < 10 ? 3 : 2 }).format(row.price); }
  function dateLabel(value) { if (!value) return 'Observation unavailable'; const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat('en-AU', { dateStyle: 'medium', timeStyle: String(value).length > 10 ? 'short' : undefined, timeZone: 'Australia/Melbourne' }).format(date); }
  function ratio(value) { return value === null || value === undefined || !Number.isFinite(Number(value)) ? '—' : `${Number(value).toFixed(2)}×`; }

  function ensureNavigation() {
    if (!document.querySelector('#nav [data-view="equities"]')) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'nav-item'; button.dataset.view = 'equities';
      button.innerHTML = '<span class="nav-icon">↗</span><span class="nav-label">Equity Tape</span>';
      button.addEventListener('click', () => { window.location.hash = '#equities'; });
      (document.querySelector('#nav .nav-group') || document.getElementById('nav'))?.appendChild(button);
    }
    if (!document.querySelector('.mobile-more [data-view="equities"]')) {
      const button = document.createElement('button'); button.type = 'button'; button.dataset.view = 'equities'; button.textContent = 'Equity Tape';
      button.addEventListener('click', () => { window.location.hash = '#equities'; });
      document.querySelector('.mobile-more')?.appendChild(button);
    }
  }

  function host() {
    let node = document.getElementById('view-equities');
    if (node) return node;
    node = document.createElement('section'); node.id = 'view-equities'; node.className = 'view'; node.setAttribute('aria-hidden', 'true');
    document.getElementById('main-content')?.appendChild(node);
    return node;
  }

  function activate() {
    if (!views?.activate('equities', { scroll: false })) {
      document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-equities'));
    }
    const title = document.getElementById('page-title'); if (title) title.textContent = 'Equity Tape';
    const subtitle = document.getElementById('page-subtitle'); if (subtitle) subtitle.textContent = 'Private delayed market-price watchlist';
  }

  function value(row, path) { let current = row; for (const part of path.split('.')) current = current?.[part]; return Number.isFinite(Number(current)) ? Number(current) : Number.NEGATIVE_INFINITY; }
  function rows() {
    const query = state.query.trim().toLowerCase();
    const filtered = (data().watchlist || []).filter((row) => (state.group === 'all' || row.group === state.group) && (state.status === 'all' || row.status === state.status) && (!query || `${row.symbol} ${row.name} ${row.exchange} ${row.group}`.toLowerCase().includes(query)));
    const sorters = {
      'absolute-day': (a, b) => Math.abs(value(b, 'percentChange')) - Math.abs(value(a, 'percentChange')),
      'day-desc': (a, b) => value(b, 'percentChange') - value(a, 'percentChange'),
      'month-desc': (a, b) => value(b, 'returns.month') - value(a, 'returns.month'),
      'volume-desc': (a, b) => value(b, 'volumeRatio20') - value(a, 'volumeRatio20'),
      symbol: (a, b) => a.symbol.localeCompare(b.symbol)
    };
    return filtered.sort(sorters[state.sort] || sorters['absolute-day']);
  }

  function controls(dataset) {
    const groups = ['all', ...new Set((dataset.watchlist || []).map((row) => row.group))];
    return `<section class="market-watch-controls"><label>Search<input id="market-watch-search" type="search" value="${escapeHtml(state.query)}" placeholder="Ticker or company"></label><label>Sort<select id="market-watch-sort"><option value="absolute-day">Largest daily move</option><option value="day-desc">Best daily move</option><option value="month-desc">Best one-month return</option><option value="volume-desc">Highest relative volume</option><option value="symbol">Ticker A–Z</option></select></label><label>Group<select id="market-watch-group">${groups.map((group) => `<option value="${escapeHtml(group)}"${state.group === group ? ' selected' : ''}>${escapeHtml(group === 'all' ? 'All groups' : group)}</option>`).join('')}</select></label><label>Status<select id="market-watch-status">${['all','current','partial','stale','failed','unavailable','unknown'].map((status) => `<option value="${status}"${state.status === status ? ' selected' : ''}>${label(status)}</option>`).join('')}</select></label></section>`;
  }

  function tableRow(row) { return `<tr><th scope="row"><strong>${escapeHtml(row.symbol)}</strong><span>${escapeHtml(row.name)}</span><small>${escapeHtml(row.group)} · ${escapeHtml(row.exchange)}</small></th><td><strong>${escapeHtml(money(row))}</strong><small>${escapeHtml(row.currency || '')}</small></td><td class="${moveClass(row.percentChange)}">${percent(row.percentChange)}</td><td class="${moveClass(row.returns?.week)}">${percent(row.returns?.week)}</td><td class="${moveClass(row.returns?.month)}">${percent(row.returns?.month)}</td><td class="${moveClass(row.distanceFromMovingAverages?.day200)}">${percent(row.distanceFromMovingAverages?.day200)}</td><td>${ratio(row.volumeRatio20)}</td><td>${percent(row.range52Week?.positionPercent, false)}</td><td><span class="market-trend ${escapeHtml(row.trend?.state || 'insufficient')}">${label(row.trend?.state || 'insufficient')}</span></td><td><span class="data-state ${statusClass(row.status)}">${label(row.status)}</span><small>${escapeHtml(dateLabel(row.observedAt))}</small></td></tr>`; }
  function card(row) { return `<article class="market-watch-card"><header><div><strong>${escapeHtml(row.symbol)}</strong><span>${escapeHtml(row.name)}</span></div><span class="data-state ${statusClass(row.status)}">${label(row.status)}</span></header><div class="market-watch-price"><strong>${escapeHtml(money(row))}</strong><span class="${moveClass(row.percentChange)}">${percent(row.percentChange)}</span></div><dl><div><dt>1 week</dt><dd>${percent(row.returns?.week)}</dd></div><div><dt>1 month</dt><dd>${percent(row.returns?.month)}</dd></div><div><dt>vs 200D</dt><dd>${percent(row.distanceFromMovingAverages?.day200)}</dd></div><div><dt>Volume</dt><dd>${ratio(row.volumeRatio20)}</dd></div></dl><footer><span class="market-trend ${escapeHtml(row.trend?.state || 'insufficient')}">${label(row.trend?.state || 'insufficient')}</span><small>${escapeHtml(row.exchange)} · ${escapeHtml(dateLabel(row.observedAt))}</small></footer></article>`; }

  function render() {
    const dataset = data(); const visible = rows(); const root = host(); if (!root) return;
    const usable = (dataset.watchlist || []).filter((row) => row.price !== null && row.price !== undefined).length;
    root.innerHTML = `<div class="market-watch-page"><header class="market-watch-hero"><div><span class="market-watch-kicker">Private price layer</span><h2>Equity Tape</h2><p>Semiconductors, rare-earth and critical-mineral equities, miners and benchmark ETFs. Prices are collected server-side; No API credential reaches the browser.</p></div><div class="market-watch-hero-meta"><span class="data-state ${statusClass(dataset.collection?.status)}">${label(dataset.collection?.status || 'unknown')}</span><strong>${escapeHtml(dataset.provider?.name || 'Twelve Data')}</strong><small>${escapeHtml(dateLabel(dataset.generatedAtUtc))}</small></div></header>${dataset.collection?.mode === 'disabled' ? '<aside class="market-watch-gate"><strong>Feed safely dormant</strong><p>Collection begins only after the repository is private, Cloudflare Access is confirmed, the API secret exists and both activation variables are true.</p></aside>' : ''}<section class="market-watch-summary"><article><span>Configured</span><strong>${dataset.watchlist?.length || 0}</strong></article><article><span>Usable prices</span><strong>${usable}</strong></article><article><span>Source warnings</span><strong>${dataset.collection?.failureCount || 0}</strong></article></section>${controls(dataset)}<section class="market-watch-panel"><div class="market-watch-heading"><div><span class="market-watch-kicker">Watchlist</span><h3>${visible.length} instruments</h3></div><a href="#sources">Source health</a></div><div class="market-watch-table-scroll"><table class="market-watch-table"><thead><tr><th>Instrument</th><th>Price</th><th>Day</th><th>1W</th><th>1M</th><th>vs 200D</th><th>Rel volume</th><th>52W</th><th>Trend</th><th>Status</th></tr></thead><tbody>${visible.map(tableRow).join('') || '<tr><td colspan="10">No instruments match the current filters.</td></tr>'}</tbody></table></div><div class="market-watch-card-grid">${visible.map(card).join('')}</div></section></div>`;
    document.getElementById('market-watch-search')?.addEventListener('input', (event) => { state.query = event.target.value; render(); });
    document.getElementById('market-watch-sort')?.addEventListener('change', (event) => { state.sort = event.target.value; render(); });
    document.getElementById('market-watch-group')?.addEventListener('change', (event) => { state.group = event.target.value; render(); });
    document.getElementById('market-watch-status')?.addEventListener('change', (event) => { state.status = event.target.value; render(); });
    const sort = document.getElementById('market-watch-sort'); if (sort) sort.value = state.sort;
  }

  function enhanceCommandCentre() {
    const home = document.querySelector('#view-home .command-page'); if (!home || home.querySelector('[data-private-equity-tape]')) return;
    const movers = (data().watchlist || []).filter((row) => row.price !== null && row.percentChange !== null && row.percentChange !== undefined).sort((a,b) => Math.abs(Number(b.percentChange))-Math.abs(Number(a.percentChange))).slice(0,5);
    const section = document.createElement('section'); section.className = 'command-panel'; section.dataset.privateEquityTape = 'true';
    section.innerHTML = `<div class="command-section-heading"><div><span class="command-kicker">Private Equity Tape</span><h3>Largest watchlist moves</h3></div><a href="#equities">Open tape</a></div>${movers.length ? `<div class="command-table-scroll"><table class="command-table compact"><tbody>${movers.map((row) => `<tr><th>${escapeHtml(row.symbol)}<small>${escapeHtml(row.name)}</small></th><td>${escapeHtml(money(row))}</td><td class="${moveClass(row.percentChange)}">${percent(row.percentChange)}</td><td>${label(row.trend?.state || 'insufficient')}</td></tr>`).join('')}</tbody></table></div>` : '<div class="command-empty">Private price collection is not active yet.</div>'}`;
    home.querySelector('.command-source-panel')?.before(section);
  }

  function show() { ensureNavigation(); activate(); render(); enhanceCommandCentre(); }
  function register() { if (!router || register.done) return; register.done = true; router.register('equities', show); ensureNavigation(); enhanceCommandCentre(); }
  window.addEventListener('marketbrief:equity-data', () => { core.adapters?.equities?.(); core.freshness?.refresh?.(); if (router?.current?.()?.path === 'equities') render(); enhanceCommandCentre(); });
  window.addEventListener('marketbrief:route', enhanceCommandCentre);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', register, { once: true }); else register();
  window.addEventListener('load', register, { once: true });
})();
