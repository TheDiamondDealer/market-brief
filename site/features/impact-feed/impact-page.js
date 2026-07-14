(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const state = { category: 'all', status: 'all', asset: '', expandedId: null };

  function dataset() { return core.impact?.get?.() || window.marketImpactData || { schemaVersion: 1, sourceMode: 'curated-delayed', items: [] }; }
  function host() { return document.getElementById('view-news'); }
  function activate() {
    if (views?.activate('news', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-news'));
  }
  function directionGlyph(value) { return value === 'up' ? '↑' : value === 'down' ? '↓' : value === 'mixed' ? '↕' : '?'; }
  function statusLabel(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : 'Unclear'; }
  function sourceLinks(sources = []) {
    return sources.map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.name)} ↗</a>`).join('');
  }

  function filteredItems() {
    const needle = state.asset.trim().toLowerCase();
    return dataset().items.filter((item) => {
      const categoryMatch = state.category === 'all' || item.category === state.category;
      const statusMatch = state.status === 'all' || item.status === state.status;
      const assetMatch = !needle || item.interpretations.some((entry) => `${entry.assetName} ${entry.assetId}`.toLowerCase().includes(needle));
      return categoryMatch && statusMatch && assetMatch;
    });
  }

  function interpretationCard(entry) {
    return `<article class="impact-interpretation ${escapeHtml(entry.direction)}">
      <header><div><strong>${escapeHtml(entry.assetName)}</strong><span>${directionGlyph(entry.direction)} ${escapeHtml(entry.direction)}</span></div><div class="impact-meta-chips"><span>${escapeHtml(entry.magnitude)} magnitude</span><span>${escapeHtml(entry.horizon)} horizon</span><span>${escapeHtml(entry.confidence)} confidence</span></div></header>
      <dl><div><dt>Mechanism</dt><dd>${escapeHtml(entry.mechanism)}</dd></div><div><dt>Confirmation</dt><dd>${escapeHtml(entry.confirmation)}</dd></div><div><dt>Invalidation</dt><dd>${escapeHtml(entry.invalidation)}</dd></div></dl>
    </article>`;
  }

  function timelineItem(item) {
    const expanded = state.expandedId === item.id;
    const chips = item.interpretations.map((entry) => `<span class="impact-asset-chip ${escapeHtml(entry.direction)}" title="${escapeHtml(entry.mechanism)}">${escapeHtml(entry.assetName)} ${directionGlyph(entry.direction)}</span>`).join('');
    return `<article class="impact-timeline-item" id="impact-${escapeHtml(item.id)}">
      <div class="impact-timeline-marker" aria-hidden="true"></div>
      <div class="impact-card">
        <header><div class="impact-card-meta"><span class="impact-status ${escapeHtml(item.status)}">${escapeHtml(statusLabel(item.status))}</span><span>${escapeHtml(item.category)}</span><span>${escapeHtml(item.eventDate || item.timeLabel || 'Date unavailable')}</span></div><span class="impact-magnitude">${escapeHtml(item.legacy?.impact || 'Impact not ranked')}</span></header>
        <h3>${escapeHtml(item.headline)}</h3><p>${escapeHtml(item.summary)}</p>
        <div class="impact-assets" aria-label="Affected assets">${chips}</div>
        <div class="impact-card-actions"><div class="impact-sources">${sourceLinks(item.sources)}</div><button type="button" data-impact-expand="${escapeHtml(item.id)}" aria-expanded="${expanded}">${expanded ? 'Hide causal detail' : 'Show causal detail'}</button></div>
        ${expanded ? `<div class="impact-expanded"><div class="impact-chain">${item.channels.map((channel, index) => `<article><span>${index + 1}</span><div><strong>${escapeHtml(channel.label)}</strong><p>${escapeHtml(channel.detail)}</p></div></article>`).join('')}</div><div class="impact-interpretations">${item.interpretations.map(interpretationCard).join('')}</div></div>` : ''}
      </div>
    </article>`;
  }

  function render() {
    const root = host();
    if (!root) return;
    const feed = dataset();
    const items = filteredItems();
    const categories = ['all', ...new Set(feed.items.map((item) => item.category))];
    const statuses = ['all', 'developing', 'confirmed', 'diverging', 'resolved', 'unclear'].filter((value) => value === 'all' || feed.items.some((item) => item.status === value));
    root.dataset.impactFeedRemodel = 'br-12';
    root.innerHTML = `<div class="impact-feed-page">
      <header class="impact-feed-hero"><div><span class="impact-kicker">Delayed curated research</span><h2>Impact Feed</h2><p>What changed, which assets are affected, the mechanism, and what would confirm or invalidate the interpretation. This is not a real-time news wire.</p></div><div class="impact-feed-status"><span class="data-state current">Contract v${escapeHtml(feed.schemaVersion)}</span><strong>${escapeHtml(feed.sourceMode)}</strong><small>As of ${escapeHtml(feed.generatedAt || 'time unavailable')}</small></div></header>
      <section class="impact-controls" aria-label="Impact Feed filters">
        <label><span>Filter by affected asset</span><input id="impactAssetSearch" type="search" value="${escapeHtml(state.asset)}" placeholder="Gold, Nasdaq, AUD…" autocomplete="off"></label>
        <div><span>Category</span><div class="impact-filter-group" role="group" aria-label="News category">${categories.map((category) => `<button type="button" data-impact-category="${escapeHtml(category)}" aria-pressed="${state.category === category}">${escapeHtml(category === 'all' ? 'All' : category)}</button>`).join('')}</div></div>
        <div><span>State</span><div class="impact-filter-group" role="group" aria-label="Impact state">${statuses.map((status) => `<button type="button" data-impact-status="${escapeHtml(status)}" aria-pressed="${state.status === status}">${escapeHtml(statusLabel(status))}</button>`).join('')}</div></div>
      </section>
      <section><div class="impact-section-heading"><div><span class="impact-kicker">Timeline</span><h3>Market-moving interpretations</h3></div><span>${items.length} item${items.length === 1 ? '' : 's'} shown</span></div><div class="impact-timeline">${items.length ? items.map(timelineItem).join('') : '<div class="impact-empty">No impact records match the current filters.</div>'}</div></section>
      <details class="impact-methodology"><summary>How to read this feed</summary><p>Magnitude is inherited from the existing editorial impact label. Direction and mechanism are preserved from the curated asset interpretation. Horizon, confidence, confirmation and invalidation remain marked unclear or not specified when the source item did not supply them.</p><p>Developing means the causal interpretation is still being tested. Confirmed means the curated item explicitly described price confirmation. Resolved should be used only after the event’s market impact is no longer active.</p></details>
    </div>`;

    root.querySelector('#impactAssetSearch')?.addEventListener('input', (event) => { state.asset = event.target.value; render(); });
    root.querySelectorAll('[data-impact-category]').forEach((button) => button.addEventListener('click', () => { state.category = button.dataset.impactCategory; render(); }));
    root.querySelectorAll('[data-impact-status]').forEach((button) => button.addEventListener('click', () => { state.status = button.dataset.impactStatus; render(); }));
    root.querySelectorAll('[data-impact-expand]').forEach((button) => button.addEventListener('click', () => {
      state.expandedId = state.expandedId === button.dataset.impactExpand ? null : button.dataset.impactExpand;
      render();
      document.getElementById(`impact-${button.dataset.impactExpand}`)?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }));
  }

  function show(id = null) {
    activate();
    if (id) state.expandedId = id;
    render();
    if (id) window.setTimeout(() => document.getElementById(`impact-${id}`)?.scrollIntoView({ block: 'start' }), 0);
  }

  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    router.register('news', () => show());
    router.registerPattern('impact-detail', /^news\/([^/]+)$/, (route) => show(decodeURIComponent(route.params.id)), (match) => ({ id: match[1] }));
    const current = router.current?.();
    if (current?.path === 'news' || current?.path?.startsWith('news/')) router.dispatch(`#${current.path}`, { source: 'impact-feed-ready' });
  }

  function initialise() { registerRoutes(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
  window.addEventListener('load', registerRoutes, { once: true });
})();
