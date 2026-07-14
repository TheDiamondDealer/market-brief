(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  const GROUPS = Object.freeze([
    { id: 'rates-liquidity', name: 'Rates & liquidity', description: 'Policy rates, secured overnight funding and the nominal Treasury curve.', ids: ['DFF', 'SOFR', 'DGS2', 'DGS5', 'DGS10', 'DGS30'] },
    { id: 'inflation-real-yields', name: 'Inflation & real yields', description: 'Market-implied inflation compensation and inflation-adjusted Treasury yields.', ids: ['DFII10', 'T10YIE'] },
    { id: 'credit', name: 'Credit', description: 'Connected spread measures that can reveal stress outside government bonds.', ids: ['BAMLH0A0HYM2'] },
    { id: 'us-dollar', name: 'US dollar', description: 'Broad trade-weighted dollar conditions from the connected official series.', ids: ['DTWEXBGS'] },
    { id: 'employment-growth', name: 'Employment & growth', description: 'No approved automated employment or growth series is connected yet.', ids: [] }
  ]);

  function host() { return document.getElementById('view-rates'); }
  function activate() {
    if (views?.activate('rates', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-rates'));
  }
  function number(value, digits = 2) { return value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(undefined, { maximumFractionDigits: digits }); }
  function sourceStatus() { return (official.sourceStatus || []).find((item) => `${item.source || ''} ${item.id || ''}`.toLowerCase().includes('fred')) || { status: (official.rates || []).length ? 'current' : 'unavailable', detail: 'Series status derived from the generated official cache.' }; }
  function statusClass(value = '') {
    const text = String(value).toLowerCase();
    if (text.includes('current') || text.includes('success')) return 'current';
    if (text.includes('partial')) return 'partial';
    return 'stale';
  }
  function trendLabel(row) {
    if (row.change === null || row.change === undefined) return 'Change unavailable';
    if (Number(row.change) > 0) return `Up ${row.changeBps === null ? number(row.change, 4) : `${number(row.changeBps, 1)} bp`}`;
    if (Number(row.change) < 0) return `Down ${row.changeBps === null ? number(Math.abs(row.change), 4) : `${number(Math.abs(row.changeBps), 1)} bp`}`;
    return 'Unchanged';
  }
  function sparkline(row) {
    if (row.previous === null || row.previous === undefined || row.value === null || row.value === undefined) return '<span class="macro-no-spark">No previous observation</span>';
    const previous = Number(row.previous);
    const current = Number(row.value);
    const high = Math.max(previous, current);
    const low = Math.min(previous, current);
    const span = high - low || 1;
    const y1 = 30 - ((previous - low) / span) * 20;
    const y2 = 30 - ((current - low) / span) * 20;
    const summary = `${row.name}: previous ${previous} ${row.unit}, latest ${current} ${row.unit}.`;
    return `<svg class="macro-spark" viewBox="0 0 100 40" role="img" aria-label="${escapeHtml(summary)}"><line x1="5" y1="${y1}" x2="95" y2="${y2}"></line><circle cx="5" cy="${y1}" r="3"></circle><circle cx="95" cy="${y2}" r="3"></circle></svg>`;
  }
  function cadence(row) { return row.id === 'DFF' || row.id === 'SOFR' ? 'Daily business-day observation' : 'Daily market observation'; }

  function seriesCard(row, status) {
    return `<article class="macro-series-card">
      <header><div><span>${escapeHtml(row.kind || 'series')}</span><h4>${escapeHtml(row.name)}</h4></div><span class="data-state ${statusClass(status.status)}">${escapeHtml(status.status || 'Unavailable')}</span></header>
      <div class="macro-reading"><strong>${number(row.value, row.unit === 'index' ? 4 : 2)}${row.unit === '%' ? '%' : ''}</strong><span>${escapeHtml(trendLabel(row))}</span></div>
      ${sparkline(row)}
      <dl><div><dt>Observation date</dt><dd>${escapeHtml(row.date || 'Unavailable')}</dd></div><div><dt>Expected cadence</dt><dd>${escapeHtml(cadence(row))}</dd></div><div><dt>Previous</dt><dd>${number(row.previous, row.unit === 'index' ? 4 : 2)}${row.unit === '%' ? '%' : ''}</dd></div><div><dt>Series ID</dt><dd>${escapeHtml(row.id)}</dd></div></dl>
      <a href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener noreferrer">Official FRED series ↗</a>
    </article>`;
  }

  function groupPanel(group, status) {
    const rows = group.ids.map((id) => (official.rates || []).find((row) => row.id === id)).filter(Boolean);
    return `<section class="macro-group" id="macro-${escapeHtml(group.id)}"><div class="macro-section-heading"><div><span class="macro-kicker">${escapeHtml(group.id)}</span><h3>${escapeHtml(group.name)}</h3><p>${escapeHtml(group.description)}</p></div><span>${rows.length} connected series</span></div>${rows.length ? `<div class="macro-series-grid">${rows.map((row) => seriesCard(row, status)).join('')}</div>` : '<div class="macro-unavailable"><span class="data-state stale">Unavailable</span><strong>No approved series connected</strong><p>This panel remains empty rather than using estimates or an unsourced proxy.</p></div>'}</section>`;
  }

  function curvePanel() {
    const rows = official.curveSpreads || [];
    return `<section class="macro-group"><div class="macro-section-heading"><div><span class="macro-kicker">Curve structure</span><h3>Treasury curve spreads</h3><p>Derived only from the connected nominal Treasury observations.</p></div><span>${rows.length} spreads</span></div><div class="macro-curve-grid">${rows.length ? rows.map((row) => `<article><span>${escapeHtml(row.name)}</span><strong>${number(row.value, 1)} ${escapeHtml(row.unit)}</strong><p>${escapeHtml(row.interpretation)}</p></article>`).join('') : '<div class="macro-unavailable">Curve spreads unavailable.</div>'}</div></section>`;
  }

  function render() {
    const root = host();
    if (!root) return;
    const status = sourceStatus();
    root.dataset.macroMonitorRemodel = 'br-16';
    root.innerHTML = `<div class="macro-page">
      <header class="macro-hero"><div><span class="macro-kicker">Official macro evidence</span><h2>Macro Monitor</h2><p>Rates, liquidity, inflation compensation, real yields, credit and the broad US dollar. Every series keeps its own observation date, cadence and official source.</p></div><div class="macro-hero-meta"><span class="data-state ${statusClass(status.status)}">${escapeHtml(status.status || 'Unavailable')}</span><strong>${escapeHtml(status.source || 'FRED official series')}</strong><small>Cache generated ${escapeHtml(official.generatedAt || 'time unavailable')}</small></div></header>
      <section class="macro-source-note"><strong>Source status</strong><p>${escapeHtml(status.detail || 'No additional source detail supplied.')}</p></section>
      ${GROUPS.map((group) => groupPanel(group, status)).join('')}
      ${curvePanel()}
      <details class="macro-methodology"><summary>Interpretation limits</summary><p>The small line shows only the previous and latest connected observations; it is not a long-history chart. A current cache timestamp does not replace each series’ observation date. Missing employment and growth data remains unavailable until an approved pipeline is added.</p></details>
    </div>`;
  }

  function show() { activate(); render(); }
  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    router.register('rates', show);
    router.register('macro', show);
    const current = router.current?.();
    if (current?.path === 'rates' || current?.path === 'macro') router.dispatch(`#${current.path}`, { source: 'macro-monitor-ready' });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoutes, { once: true });
  else registerRoutes();
  window.addEventListener('load', registerRoutes, { once: true });
})();
