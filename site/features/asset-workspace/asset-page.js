(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const evidence = core.adapters?.evidence?.() || window.marketResearchData || {};
  const scenarios = core.adapters?.scenarios?.() || window.scenarioAssets || {};
  const impact = () => core.impact?.get?.() || window.marketImpactData || { items: [] };
  const ASSET_ALIASES = Object.freeze({ brent: ['brent', 'oil'], wti: ['wti', 'oil'], 'gas-us': ['henry hub', 'us natural gas', 'gas'], 'gas-uk': ['nbp', 'uk natural gas', 'gas'], gold: ['gold'], silver: ['silver'], copper: ['copper'] });
  const CHECKLIST_KEYS = Object.freeze({ brent: 'oil', wti: 'oil', 'gas-us': 'gas-us', 'gas-uk': 'gas-uk' });
  const COT_IDS = Object.freeze({ gold: 'gold', silver: 'silver', copper: 'copper', brent: 'oil-brent', wti: 'oil-wti', 'gas-us': 'gas-us', 'gas-uk': 'gas-uk' });

  function host() { return document.getElementById('view-product-detail'); }
  function activate() {
    if (views?.activate('product-detail', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-product-detail'));
  }
  function asset(id) { return scenarios[id] || null; }
  function normalized(value = '') { return String(value).trim().toLowerCase(); }
  function aliases(id, item) { return [id, item?.name, ...(ASSET_ALIASES[id] || [])].filter(Boolean).map(normalized); }
  function relevantImpact(id, item) {
    const terms = aliases(id, item);
    return (impact().items || []).filter((event) => event.interpretations.some((entry) => terms.some((term) => normalized(`${entry.assetId} ${entry.assetName}`).includes(term))));
  }
  function relevantEvents(id, item) {
    const terms = aliases(id, item);
    return (evidence.eventReactions || []).filter((event) => terms.some((term) => normalized(JSON.stringify(event)).includes(term)));
  }
  function checklist(id) { return evidence.physicalChecklists?.[CHECKLIST_KEYS[id] || id] || null; }
  function cotState(id) {
    const cotId = COT_IDS[id] || id;
    const row = (official.cot || []).find((item) => item.id === cotId);
    if (row) return { kind: 'verified', row };
    const unavailable = official.cotContractRegistry?.unavailable?.find((item) => item.id === cotId);
    return unavailable ? { kind: 'unavailable', unavailable } : { kind: 'missing' };
  }
  function number(value) { return value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(); }
  function signed(value) { return value === null || value === undefined ? '—' : `${Number(value) > 0 ? '+' : ''}${number(value)}`; }
  function directionGlyph(value) { return value === 'up' ? '↑' : value === 'down' ? '↓' : value === 'mixed' ? '↕' : '?'; }
  function statusClass(value = '') {
    const text = normalized(value);
    if (text.includes('automatic') || text.includes('current') || text.includes('verified')) return 'current';
    if (text.includes('partial')) return 'partial';
    if (text.includes('pending') || text.includes('unavailable')) return 'stale';
    return 'pending';
  }

  function evidenceList(title, rows, tone) {
    return `<section class="asset-evidence-column ${tone}"><div class="asset-section-heading"><span>${escapeHtml(title)}</span><small>${rows.length} conditions</small></div>${rows.length ? rows.map(([label, detail]) => `<article><strong>${escapeHtml(label)}</strong><p>${escapeHtml(detail)}</p></article>`).join('') : '<div class="asset-empty">No conditions supplied.</div>'}</section>`;
  }

  function cotPanel(id) {
    const state = cotState(id);
    if (state.kind === 'verified') {
      const row = state.row;
      return `<section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">CFTC positioning</span><h3>Exact verified contract</h3></div><span class="data-state current">Current cache</span></div><div class="asset-stat-grid"><article><span>Net</span><strong>${signed(row.net)}</strong></article><article><span>1 week</span><strong>${signed(row.weekChange)}</strong></article><article><span>Long</span><strong>${number(row.long)}</strong></article><article><span>Short</span><strong>${number(row.short)}</strong></article></div><dl class="asset-source-list"><div><dt>Market</dt><dd>${escapeHtml(row.contract?.marketName || row.market)}</dd></div><div><dt>Code</dt><dd>${escapeHtml(row.contract?.cftcContractCode || 'Unavailable')}</dd></div><div><dt>Category</dt><dd>${escapeHtml(row.contract?.category || row.category)}</dd></div><div><dt>Report date</dt><dd>${escapeHtml(row.reportDate || 'Unavailable')}</dd></div></dl><a class="asset-source-link" href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener noreferrer">Official CFTC source ↗</a></section>`;
    }
    const reason = state.kind === 'unavailable' ? state.unavailable.reason : 'No verified exact-contract mapping is available for this asset.';
    return `<section class="asset-panel asset-unavailable"><div class="asset-section-heading"><div><span class="asset-kicker">CFTC positioning</span><h3>Unavailable</h3></div><span class="data-state stale">No substitute used</span></div><p>${escapeHtml(reason)}</p></section>`;
  }

  function impactPanel(id, item) {
    const events = relevantImpact(id, item);
    return `<section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">Impact Feed</span><h3>Relevant causal interpretations</h3></div><span>${events.length} event${events.length === 1 ? '' : 's'}</span></div>${events.length ? `<div class="asset-impact-list">${events.map((event) => {
      const entries = event.interpretations.filter((entry) => aliases(id, item).some((term) => normalized(`${entry.assetId} ${entry.assetName}`).includes(term)));
      return `<article><header><div><span class="data-state ${event.status === 'confirmed' ? 'current' : 'partial'}">${escapeHtml(event.status)}</span><strong>${escapeHtml(event.headline)}</strong></div><a href="#news/${encodeURIComponent(event.id)}">Open event</a></header><p>${escapeHtml(event.summary)}</p>${entries.map((entry) => `<dl><div><dt>Direction</dt><dd>${directionGlyph(entry.direction)} ${escapeHtml(entry.direction)}</dd></div><div><dt>Mechanism</dt><dd>${escapeHtml(entry.mechanism)}</dd></div><div><dt>Confirmation</dt><dd>${escapeHtml(entry.confirmation)}</dd></div><div><dt>Invalidation</dt><dd>${escapeHtml(entry.invalidation)}</dd></div></dl>`).join('')}</article>`;
    }).join('')}</div>` : '<div class="asset-empty">No current curated impact item explicitly names this asset.</div>'}</section>`;
  }

  function checklistPanel(id) {
    const data = checklist(id);
    if (!data) return `<section class="asset-panel asset-unavailable"><div class="asset-section-heading"><div><span class="asset-kicker">Physical / macro checks</span><h3>Checklist unavailable</h3></div><span class="data-state stale">Not connected</span></div><p>No asset-specific physical checklist is currently defined.</p></section>`;
    return `<section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">Physical / macro checks</span><h3>${escapeHtml(data.title)}</h3></div><span>Research updated ${escapeHtml(evidence.updated || 'date unavailable')}</span></div><p class="asset-panel-summary">${escapeHtml(data.summary)}</p><div class="asset-checklist">${data.items.map((entry) => `<article><header><strong>${escapeHtml(entry.name)}</strong><span class="data-state ${statusClass(entry.status)}">${escapeHtml(entry.status)}</span></header><p>${escapeHtml(entry.interpretation)}</p><dl><div><dt>Reading</dt><dd>${escapeHtml(entry.reading)}</dd></div><div><dt>Source</dt><dd>${escapeHtml(entry.source)}</dd></div><div><dt>Cadence</dt><dd>${escapeHtml(entry.freshness)}</dd></div></dl></article>`).join('')}</div></section>`;
  }

  function eventsPanel(id, item) {
    const events = relevantEvents(id, item);
    return `<section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">Event calendar</span><h3>Relevant scheduled catalysts</h3></div><span>${events.length} event${events.length === 1 ? '' : 's'}</span></div>${events.length ? `<div class="asset-events">${events.map((event) => `<article><div><strong>${escapeHtml(event.event)}</strong><span>${escapeHtml(event.scheduled)}</span></div><span class="data-state ${event.stage === 'Pre-event' ? 'pending' : 'current'}">${escapeHtml(event.stage)}</span><p>Actual: ${escapeHtml(event.actual)} · Consensus: ${escapeHtml(event.consensus)}</p><small>Official source: ${escapeHtml(event.source)}</small></article>`).join('')}</div>` : '<div class="asset-empty">No current calendar item explicitly references this asset.</div>'}</section>`;
  }

  function chart(item) {
    const symbol = encodeURIComponent(item.symbol || '');
    if (!symbol) return '<div class="asset-empty">External chart symbol unavailable.</div>';
    const src = `https://s.tradingview.com/widgetembed/?symbol=${symbol}&interval=D&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=F1F3F6&studies=[]&theme=dark&style=1&timezone=Australia%2FMelbourne&withdateranges=1&hideideas=1`;
    return `<div class="asset-chart-wrap"><iframe title="${escapeHtml(item.name)} external market chart" src="${src}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe><p>Display-only external TradingView chart. Provider data, delay and licensing terms apply; the site does not copy or recalculate the chart values.</p></div>`;
  }

  function render(id) {
    const root = host();
    if (!root) return;
    const item = asset(id);
    root.dataset.assetWorkspaceRemodel = 'br-13';
    if (!item) {
      root.innerHTML = `<div class="asset-workspace"><div class="asset-empty"><strong>Asset workspace unavailable</strong><p>No scenario record exists for “${escapeHtml(id)}”.</p><a href="#products">Return to assets</a></div></div>`;
      return;
    }
    root.innerHTML = `<div class="asset-workspace">
      <header class="asset-hero"><div><span class="asset-kicker">Decision workspace</span><h2>${escapeHtml(item.name)}</h2><p>Evidence for the current path, evidence that would flip it, relevant catalysts, positioning and physical-market checks in one route.</p></div><div class="asset-hero-meta"><span class="data-state current">Scenario record connected</span><strong>${escapeHtml(item.symbol || 'Chart symbol unavailable')}</strong><small>Official cache ${escapeHtml(official.generatedAt || 'time unavailable')}</small></div></header>
      <section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">External chart</span><h3>Market context</h3></div><span>Display only</span></div>${chart(item)}</section>
      <section class="asset-thesis-grid">${evidenceList('Evidence supporting upside', item.upside || [], 'positive')}${evidenceList('Evidence supporting downside', item.downside || [], 'negative')}</section>
      <section class="asset-panel"><div class="asset-section-heading"><div><span class="asset-kicker">Decision rules</span><h3>Confirmation and flip conditions</h3></div><span>No hidden score</span></div><div class="asset-rule-grid"><article><span>Upside confirmation</span><p>${escapeHtml(item.confirmUp || 'Not specified')}</p></article><article><span>Upside invalidation</span><p>${escapeHtml(item.invalidUp || 'Not specified')}</p></article><article><span>Downside confirmation</span><p>${escapeHtml(item.confirmDown || 'Not specified')}</p></article><article><span>Downside invalidation</span><p>${escapeHtml(item.invalidDown || 'Not specified')}</p></article></div></section>
      ${impactPanel(id, item)}
      <div class="asset-two-column">${cotPanel(id)}${eventsPanel(id, item)}</div>
      ${checklistPanel(id)}
      <footer class="asset-provenance"><strong>Source dates</strong><span>Official market cache: ${escapeHtml(official.generatedAt || 'unavailable')}</span><span>Research checklist: ${escapeHtml(evidence.updated || 'unavailable')}</span><span>Impact feed: ${escapeHtml(impact().generatedAt || 'unavailable')}</span></footer>
    </div>`;
  }

  function show(id) { activate(); render(id); }
  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    const handler = (route) => show(decodeURIComponent(route.params.id));
    router.registerPattern('asset-workspace', /^asset\/([^/]+)$/, handler, (match) => ({ id: match[1] }));
    router.registerPattern('product-detail', /^product\/([^/]+)$/, handler, (match) => ({ id: match[1] }));
    const current = router.current?.();
    if (current?.path?.startsWith('asset/') || current?.path?.startsWith('product/')) router.dispatch(`#${current.path}`, { source: 'asset-workspace-ready' });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoutes, { once: true });
  else registerRoutes();
  window.addEventListener('load', registerRoutes, { once: true });
})();
