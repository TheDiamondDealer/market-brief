(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const state = { family: 'all', status: 'all' };

  function health() { return core.freshness?.get?.() || window.marketSourceHealth || { schemaVersion: 1, counts: {}, records: [] }; }
  function formatDate(value) {
    if (!value) return 'Unavailable';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat('en-AU', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Melbourne' }).format(date);
  }
  function label(value = '') { return String(value).split('-').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' '); }

  function ensureHost() {
    let node = document.getElementById('view-sources');
    if (node) return node;
    const content = document.querySelector('main .content') || document.querySelector('main') || document.body;
    node = document.createElement('section');
    node.id = 'view-sources';
    node.className = 'view';
    node.dataset.dynamicView = 'source-health';
    const footer = content.querySelector('.footer');
    if (footer) content.insertBefore(node, footer);
    else content.appendChild(node);
    return node;
  }

  function activate() {
    ensureHost();
    if (views?.activate('sources', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-sources'));
  }

  function visibleRecords() {
    return health().records.filter((record) => (state.family === 'all' || record.family === state.family) && (state.status === 'all' || record.status === state.status));
  }

  function sourceCard(record) {
    return `<article class="source-health-card ${escapeHtml(record.status)}">
      <header><div><span>${escapeHtml(label(record.family))}</span><h3>${escapeHtml(record.name)}</h3></div><span class="data-state ${escapeHtml(record.status)}">${escapeHtml(label(record.status))}</span></header>
      <p>${escapeHtml(record.detail || 'No additional source detail supplied.')}</p>
      <dl>
        <div><dt>Source observation</dt><dd>${escapeHtml(formatDate(record.sourceObservedAt))}</dd></div>
        <div><dt>Collected</dt><dd>${escapeHtml(formatDate(record.collectedAt))}</dd></div>
        <div><dt>Generated</dt><dd>${escapeHtml(formatDate(record.generatedAt))}</dd></div>
        <div><dt>Expected cadence</dt><dd>${escapeHtml(record.expectedCadence)}</dd></div>
        <div><dt>Last successful run</dt><dd>${escapeHtml(formatDate(record.lastSuccessfulAt))}</dd></div>
        <div><dt>Error</dt><dd>${escapeHtml(record.error || 'None reported')}</dd></div>
      </dl>
      ${record.url ? `<a href="${escapeHtml(record.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : '<span class="source-health-no-link">No source URL attached</span>'}
    </article>`;
  }

  function render() {
    const root = ensureHost();
    const data = health();
    const families = ['all', ...new Set(data.records.map((record) => record.family))];
    const statuses = ['all', ...data.statuses.filter((status) => data.counts[status])];
    const records = visibleRecords();
    const warnings = data.records.filter((record) => ['delayed', 'stale', 'failed', 'unavailable', 'partial'].includes(record.status)).length;
    root.dataset.sourceHealthRemodel = 'br-17';
    root.innerHTML = `<div class="source-health-page">
      <header class="source-health-hero"><div><span class="source-health-kicker">Unified observability</span><h2>Source Health</h2><p>Observation time, collection time, generation time, cadence and last successful run remain separate. A current source cannot conceal a stale or failed neighbour.</p></div><div class="source-health-hero-meta"><span class="data-state ${warnings ? 'partial' : 'current'}">${warnings ? `${warnings} warning${warnings === 1 ? '' : 's'}` : 'All connected sources current'}</span><strong>Registry v${escapeHtml(data.schemaVersion)}</strong><small>Evaluated ${escapeHtml(formatDate(data.generatedAt))}</small></div></header>
      <section class="source-health-counts" aria-label="Source status totals">${data.statuses.map((status) => `<article><span>${escapeHtml(label(status))}</span><strong>${escapeHtml(data.counts[status] || 0)}</strong></article>`).join('')}</section>
      <section class="source-health-controls" aria-label="Source health filters"><div><span>Family</span><div role="group">${families.map((family) => `<button type="button" data-source-family="${escapeHtml(family)}" aria-pressed="${state.family === family}">${escapeHtml(family === 'all' ? 'All' : label(family))}</button>`).join('')}</div></div><div><span>Status</span><div role="group">${statuses.map((status) => `<button type="button" data-source-status="${escapeHtml(status)}" aria-pressed="${state.status === status}">${escapeHtml(status === 'all' ? 'All' : label(status))}</button>`).join('')}</div></div></section>
      <section><div class="source-health-heading"><div><span class="source-health-kicker">Independent records</span><h3>Every source and series</h3></div><span>${records.length} record${records.length === 1 ? '' : 's'} shown</span></div><div class="source-health-grid">${records.length ? records.map(sourceCard).join('') : '<div class="source-health-empty">No source records match these filters.</div>'}</div></section>
      <details class="source-health-methodology"><summary>Status vocabulary</summary><p><strong>Current</strong> is inside the expected cadence window. <strong>Delayed</strong> has missed the normal window but may still be usable. <strong>Stale</strong> is materially old. <strong>Partial</strong> means some rows succeeded while others require retry. <strong>Failed</strong> means the latest run reported an error. <strong>Unavailable</strong> means no approved source is connected. <strong>Unknown</strong> means the timestamp cannot be safely interpreted.</p></details>
    </div>`;
    root.querySelectorAll('[data-source-family]').forEach((button) => button.addEventListener('click', () => { state.family = button.dataset.sourceFamily; render(); }));
    root.querySelectorAll('[data-source-status]').forEach((button) => button.addEventListener('click', () => { state.status = button.dataset.sourceStatus; render(); }));
  }

  function enhanceCommandCentre() {
    const panel = document.querySelector('#view-home.active .command-source-panel');
    if (!panel) return;
    let summary = panel.querySelector('.command-unified-health');
    if (!summary) {
      summary = document.createElement('div');
      summary.className = 'command-unified-health';
      panel.prepend(summary);
    }
    const data = health();
    const failures = core.freshness?.failures?.().slice(0, 5) || [];
    summary.innerHTML = `<div><strong>Unified source registry</strong><span>${failures.length ? `${failures.length} highest-priority warnings shown` : 'No delayed, stale, failed, unavailable or partial source'}</span></div><a href="#sources">Open full source health</a>${failures.length ? `<div class="command-unified-failures">${failures.map((record) => `<article><span class="data-state ${escapeHtml(record.status)}">${escapeHtml(label(record.status))}</span><div><strong>${escapeHtml(record.name)}</strong><small>Observed ${escapeHtml(formatDate(record.sourceObservedAt))} · cadence ${escapeHtml(record.expectedCadence)}</small></div></article>`).join('')}</div>` : ''}`;
  }

  function show() { activate(); core.freshness?.refresh?.(); render(); }
  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    ensureHost();
    router.register('sources', show);
    router.register('source-health', show);
    router.subscribe((route) => {
      if (route.path === 'home') window.setTimeout(enhanceCommandCentre, 0);
      if (route.path === 'sources' || route.path === 'source-health') render();
    });
    const current = router.current?.();
    if (current?.path === 'sources' || current?.path === 'source-health') router.dispatch(`#${current.path}`, { source: 'source-health-ready' });
    if (current?.path === 'home') window.setTimeout(enhanceCommandCentre, 0);
  }

  window.addEventListener('marketbrief:source-health', () => {
    if (document.getElementById('view-sources')?.classList.contains('active')) render();
    enhanceCommandCentre();
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoutes, { once: true });
  else registerRoutes();
  window.addEventListener('load', () => { registerRoutes(); enhanceCommandCentre(); }, { once: true });
})();
