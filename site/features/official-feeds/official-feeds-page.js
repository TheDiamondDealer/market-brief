(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const state = { family: 'all', status: 'all', query: '' };
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  function data() { return window.officialFeedsData || { generatedAtUtc: null, collection: {}, sources: [], methodology: {} }; }
  function label(value = '') { return String(value).replaceAll('-', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
  function formatDate(value) {
    if (!value) return 'Unavailable';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const hasTime = /T\d{2}:\d{2}/.test(String(value));
    return new Intl.DateTimeFormat('en-AU', { dateStyle: 'medium', ...(hasTime ? { timeStyle: 'short' } : {}), timeZone: 'Australia/Melbourne' }).format(date);
  }
  function number(value) { return value === null || value === undefined || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-AU', { maximumFractionDigits: 4 }); }
  function signed(value) { return value === null || value === undefined || !Number.isFinite(Number(value)) ? '—' : `${Number(value) > 0 ? '+' : ''}${number(value)}`; }
  function statusClass(value = '') { const status = String(value).toLowerCase(); return status === 'current' ? 'current' : ['partial', 'delayed', 'unknown'].includes(status) ? 'partial' : 'stale'; }
  function ensureHost() {
    let node = document.getElementById('view-official-feeds');
    if (node) return node;
    const content = document.querySelector('main .content') || document.querySelector('main') || document.body;
    node = document.createElement('section');
    node.id = 'view-official-feeds';
    node.className = 'view';
    node.dataset.dynamicView = 'official-feeds';
    const footer = content.querySelector('.footer');
    if (footer) content.insertBefore(node, footer); else content.appendChild(node);
    return node;
  }
  function ensureNavigation() {
    const nav = document.getElementById('nav');
    if (nav && !nav.querySelector('[data-view="official-feeds"]')) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'nav-item'; button.dataset.view = 'official-feeds'; button.setAttribute('aria-label', 'Official Feeds'); button.title = 'Official Feeds';
      button.innerHTML = '<span class="nav-icon" aria-hidden="true">▣</span><span class="nav-label">Official Feeds</span>';
      button.addEventListener('click', () => router?.navigate?.('official-feeds') || (window.location.hash = '#official-feeds'));
      const rates = nav.querySelector('[data-view="rates"]');
      if (rates) rates.insertAdjacentElement('afterend', button); else nav.appendChild(button);
    }
    const grid = document.querySelector('#mobileMore .mobile-more-grid');
    if (grid && !grid.querySelector('[data-shell-view="official-feeds"]')) {
      const button = document.createElement('button');
      button.type = 'button'; button.dataset.shellView = 'official-feeds'; button.textContent = 'Official Feeds';
      button.addEventListener('click', () => router?.navigate?.('official-feeds') || (window.location.hash = '#official-feeds'));
      grid.prepend(button);
    }
  }
  function activate() {
    ensureHost();
    if (views?.activate('official-feeds', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-official-feeds'));
  }
  function visibleSources() {
    const query = state.query.trim().toLowerCase();
    return (data().sources || []).filter((source) => {
      const familyMatch = state.family === 'all' || source.family === state.family;
      const statusMatch = state.status === 'all' || source.status === state.status;
      const haystack = `${source.name} ${source.family} ${source.access} ${source.detail} ${(source.records || []).map((record) => `${record.name || ''} ${record.title || ''} ${record.ticker || ''} ${record.form || ''} ${record.group || ''} ${record.announcementType || ''} ${record.feedName || ''}`).join(' ')}`.toLowerCase();
      return familyMatch && statusMatch && (!query || haystack.includes(query));
    });
  }
  function filingCard(record) {
    return `<article class="official-record filing"><header><div><span>${escapeHtml(record.ticker || record.companyId || 'SEC')}</span><strong>${escapeHtml(record.company || record.name)}</strong></div><span class="official-form">${escapeHtml(record.form || 'Filing')}</span></header><p>${escapeHtml(record.title || record.primaryDocument || 'Official filing')}</p><dl><div><dt>Filed</dt><dd>${escapeHtml(formatDate(record.filedAt))}</dd></div><div><dt>Accepted</dt><dd>${escapeHtml(formatDate(record.acceptedAt))}</dd></div><div><dt>Report period</dt><dd>${escapeHtml(record.period || 'Not specified')}</dd></div><div><dt>Accession</dt><dd>${escapeHtml(record.accession || 'Unavailable')}</dd></div></dl><a href="${escapeHtml(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open official filing ↗</a></article>`;
  }
  function announcementCard(record) {
    const sensitive = record.marketSensitive ? '<span class="official-sensitive">Market sensitive</span>' : '<span class="official-neutral">Announcement</span>';
    return `<article class="official-record announcement"><header><div><span>${escapeHtml(record.ticker || 'ASX')}</span><strong>${escapeHtml(record.company || record.ticker || 'ASX issuer')}</strong></div>${sensitive}</header><p>${escapeHtml(record.title || record.name)}</p><dl><div><dt>Released</dt><dd>${escapeHtml(formatDate(record.releasedAt || record.observedAt))}</dd></div><div><dt>Category</dt><dd>${escapeHtml(record.announcementType || 'ASX announcement')}</dd></div><div><dt>Pages</dt><dd>${escapeHtml(record.pages ?? 'Unavailable')}</dd></div><div><dt>Evidence</dt><dd>Official ASX document</dd></div></dl><a href="${escapeHtml(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open ASX announcement ↗</a></article>`;
  }
  function policyCard(record) {
    return `<article class="official-record policy-release"><header><div><span>${escapeHtml(record.group || 'Federal Reserve')}</span><strong>${escapeHtml(record.publisher || 'Federal Reserve')}</strong></div><span class="official-form">Policy release</span></header><p>${escapeHtml(record.title || record.name)}</p><dl><div><dt>Published</dt><dd>${escapeHtml(formatDate(record.publishedAt || record.observedAt))}</dd></div><div><dt>Feed</dt><dd>${escapeHtml(record.feedName || 'Official RSS')}</dd></div><div><dt>Authority</dt><dd>Federal Reserve Board</dd></div><div><dt>Interpretation</dt><dd>Not inferred</dd></div></dl><a href="${escapeHtml(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open Federal Reserve release ↗</a></article>`;
  }
  function seriesCard(record) {
    const code = record.dataTypeCode || record.lineNumber || record.id;
    return `<article class="official-record series"><header><div><span>${escapeHtml(record.group || record.kind)}</span><strong>${escapeHtml(record.name)}</strong></div><span>${escapeHtml(record.frequency || '')}</span></header><div class="official-reading"><strong>${escapeHtml(number(record.value))}</strong><span>${escapeHtml(record.unit || '')}</span></div><dl><div><dt>Period</dt><dd>${escapeHtml(record.period || formatDate(record.observedAt))}</dd></div><div><dt>Previous</dt><dd>${escapeHtml(number(record.previous))}</dd></div><div><dt>Change</dt><dd>${escapeHtml(signed(record.change))}</dd></div><div><dt>Official code</dt><dd>${escapeHtml(code || 'Unavailable')}</dd></div></dl>${record.preliminary ? '<p class="official-note">Preliminary observation.</p>' : ''}<a href="${escapeHtml(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open official source ↗</a></article>`;
  }
  function releaseCard(record) { return `<article class="official-record release"><header><div><span>${escapeHtml(record.group || 'Release')}</span><strong>${escapeHtml(record.name)}</strong></div><span>${escapeHtml(record.period || '')}</span></header><p>${escapeHtml(record.detail || 'Official release metadata.')}</p><a href="${escapeHtml(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open official publication ↗</a></article>`; }
  function recordCard(record) {
    if (record.kind === 'filing') return filingCard(record);
    if (record.kind === 'announcement') return announcementCard(record);
    if (record.kind === 'policy-release') return policyCard(record);
    if (record.kind === 'release') return releaseCard(record);
    return seriesCard(record);
  }
  function sourceSection(source) {
    const records = source.records || [];
    return `<section class="official-source-section"><header class="official-source-header"><div><span class="official-kicker">${escapeHtml(source.family)}</span><h3>${escapeHtml(source.name)}</h3><p>${escapeHtml(source.detail || 'No source detail supplied.')}</p></div><div class="official-source-meta"><span class="data-state ${statusClass(source.status)}">${escapeHtml(label(source.status))}</span><strong>${records.length} record${records.length === 1 ? '' : 's'}</strong><small>${escapeHtml(source.access)}</small></div></header><dl class="official-source-dates"><div><dt>Observed</dt><dd>${escapeHtml(formatDate(source.observedAt))}</dd></div><div><dt>Collected</dt><dd>${escapeHtml(formatDate(source.collectedAt))}</dd></div><div><dt>Last success</dt><dd>${escapeHtml(formatDate(source.lastSuccessfulAt))}</dd></div><div><dt>Cadence</dt><dd>${escapeHtml(source.expectedCadence)}</dd></div></dl>${source.error ? `<div class="official-error"><strong>Source note</strong><span>${escapeHtml(source.error)}</span></div>` : ''}<div class="official-record-grid">${records.length ? records.map(recordCard).join('') : '<div class="official-empty">No verified observations are available from this source yet.</div>'}</div><a class="official-source-link" href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">Source documentation ↗</a></section>`;
  }
  function render() {
    const root = ensureHost();
    const current = data();
    const sources = visibleSources();
    const families = ['all', ...new Set((current.sources || []).map((source) => source.family))];
    const statuses = ['all', ...new Set((current.sources || []).map((source) => source.status))];
    const totalRecords = (current.sources || []).reduce((sum, source) => sum + (source.records?.length || 0), 0);
    root.dataset.officialFeeds = 'br-22';
    root.innerHTML = `<div class="official-feeds-page"><header class="official-feeds-hero"><div><span class="official-kicker">Primary official evidence</span><h2>Official Feeds</h2><p>ASX company announcements, Federal Reserve releases, SEC filings, energy fundamentals, labour and inflation, national accounts, Census indicators and critical-mineral publications. Every source keeps its own timestamp and failure state.</p></div><div class="official-hero-meta"><span class="data-state ${statusClass(current.collection?.status)}">${escapeHtml(label(current.collection?.status || 'unknown'))}</span><strong>${totalRecords} retained observations</strong><small>Generated ${escapeHtml(formatDate(current.generatedAtUtc))}</small></div></header><section class="official-summary" aria-label="Official feed totals"><article><span>Sources usable</span><strong>${escapeHtml(current.collection?.successCount || 0)}</strong></article><article><span>Unavailable</span><strong>${escapeHtml(current.collection?.unavailableCount || 0)}</strong></article><article><span>Failed / stale</span><strong>${escapeHtml(current.collection?.failureCount || 0)}</strong></article><article><span>Records retained</span><strong>${escapeHtml(totalRecords)}</strong></article></section><section class="official-controls" aria-label="Official feed filters"><label>Search<input type="search" value="${escapeHtml(state.query)}" placeholder="Company, announcement, policy release or series" data-official-query /></label><label>Family<select data-official-family>${families.map((family) => `<option value="${escapeHtml(family)}"${state.family === family ? ' selected' : ''}>${escapeHtml(family === 'all' ? 'All families' : family)}</option>`).join('')}</select></label><label>Status<select data-official-status>${statuses.map((status) => `<option value="${escapeHtml(status)}"${state.status === status ? ' selected' : ''}>${escapeHtml(status === 'all' ? 'All statuses' : label(status))}</option>`).join('')}</select></label></section><div class="official-source-list">${sources.length ? sources.map(sourceSection).join('') : '<div class="official-empty">No sources match the current filters.</div>'}</div><details class="official-methodology"><summary>Collection and trust rules</summary>${Object.entries(current.methodology || {}).map(([key, value]) => `<p><strong>${escapeHtml(label(key))}:</strong> ${escapeHtml(value)}</p>`).join('')}</details></div>`;
    root.querySelector('[data-official-query]')?.addEventListener('input', (event) => { state.query = event.target.value; render(); });
    root.querySelector('[data-official-family]')?.addEventListener('change', (event) => { state.family = event.target.value; render(); });
    root.querySelector('[data-official-status]')?.addEventListener('change', (event) => { state.status = event.target.value; render(); });
  }
  function show() { activate(); render(); }
  function register() {
    if (!router || register.done) return;
    register.done = true; ensureNavigation(); ensureHost(); router.register('official-feeds', show); router.register('official', show);
    const current = router.current?.();
    if (current?.path === 'official-feeds' || current?.path === 'official') router.dispatch(`#${current.path}`, { source: 'official-feeds-ready' });
  }
  window.addEventListener('marketbrief:official-feeds', () => { if (document.getElementById('view-official-feeds')?.classList.contains('active')) render(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', register, { once: true }); else register();
  window.addEventListener('load', register, { once: true });
})();
