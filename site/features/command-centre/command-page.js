(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const research = core.adapters?.research?.() || (typeof fallback !== 'undefined' ? fallback : {});
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const impact = () => core.impact?.get?.() || window.marketImpactData || { items: [] };
  const political = () => window.politicalDisclosureSummary || core.store?.getSlice?.('politicalSummary') || { recentFilings: [], sourceStatus: {} };
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  function host() { return document.getElementById('view-home'); }
  function activate() {
    if (views?.activate('home', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-home'));
  }
  function number(value) { return value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(); }
  function signed(value) { return value === null || value === undefined ? '—' : `${Number(value) > 0 ? '+' : ''}${number(value)}`; }
  function directionGlyph(value) { return value === 'up' ? '↑' : value === 'down' ? '↓' : value === 'mixed' ? '↕' : '?'; }
  function directionLabel(value) { return value === 'up' ? 'up' : value === 'down' ? 'down' : value === 'mixed' ? 'mixed' : 'unclear'; }
  function directionChip(label, direction, detail = '') {
    const normalized = directionLabel(direction);
    const accessible = `${label}: expected ${normalized}${detail ? `. ${detail}` : ''}`;
    return `<span class="market-direction-chip ${escapeHtml(normalized)}" title="${escapeHtml(detail)}" aria-label="${escapeHtml(accessible)}"><span>${escapeHtml(label)}</span><span class="market-direction-arrow" aria-hidden="true">${directionGlyph(normalized)}</span></span>`;
  }
  function directionStrip(entries = [], label = 'Expected market pressure') {
    return `<div class="market-direction-strip"><span class="market-direction-label">${escapeHtml(label)}</span><div class="market-direction-chips">${entries.map((entry) => directionChip(entry.assetName || entry.label || 'Asset', entry.direction || entry.dir, entry.mechanism || entry.detail || '')).join('')}</div></div>`;
  }
  function statusClass(value = '') {
    const text = String(value).toLowerCase();
    if (text.includes('current') || text.includes('confirmed')) return 'current';
    if (text.includes('partial') || text.includes('develop')) return 'partial';
    if (text.includes('failed') || text.includes('stale') || text.includes('unavailable')) return 'stale';
    return 'pending';
  }
  function productId(bias) { return bias.productId || bias.id; }

  function eventCards() {
    return (impact().items || []).slice(0, 3).map((item) => `<article class="command-event-card">
      <header><span class="data-state ${statusClass(item.status)}">${escapeHtml(item.status)}</span><span>${escapeHtml(item.eventDate || item.timeLabel || 'Date unavailable')}</span></header>
      <h3>${escapeHtml(item.headline)}</h3><p>${escapeHtml(item.summary)}</p>
      ${directionStrip((item.interpretations || []).slice(0, 6))}
      <a href="#news/${encodeURIComponent(item.id)}">Open causal analysis</a>
    </article>`).join('');
  }

  function dailyBrief() {
    const daily = research.daily || {};
    const stats = (daily.stats || []).slice(0, 6).map((stat) => ({
      label: stat.label,
      dir: stat.dir,
      detail: [stat.value, stat.move].filter(Boolean).join(' · ')
    }));
    const headlines = (daily.headlines || []).slice(0, 5);
    const chain = (research.regime?.chain || []).slice(0, 8);
    return `<section class="command-daily command-panel" aria-labelledby="commandDailyTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Daily Brief</span><h3 id="commandDailyTitle">${escapeHtml(daily.title || 'Today’s market brief')}</h3></div><span>${escapeHtml(daily.asOf || research.generatedAt || 'As-of time unavailable')}</span></div>
      ${stats.length ? directionStrip(stats, 'Today’s observed moves') : ''}
      <div class="command-daily-grid">
        <div class="command-daily-headlines"><span class="command-daily-label">Five things that matter</span>${headlines.length ? headlines.map((item, index) => `<article><span>${index + 1}</span><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.body)}</p></div></article>`).join('') : '<div class="command-empty">No daily headlines are available.</div>'}</div>
        <div class="command-daily-transmission"><span class="command-daily-label">Dominant transmission</span><div class="command-daily-chain">${chain.length ? chain.map((node, index) => `<span class="command-chain-node">${escapeHtml(node)}</span>${index < chain.length - 1 ? '<span class="command-chain-arrow" aria-hidden="true">→</span>' : ''}`).join('') : '<span class="command-empty">No regime chain is available.</span>'}</div></div>
      </div>
    </section>`;
  }

  function triggerCards() {
    const active = (research.triggers || []).filter((item) => ['warning', 'triggered'].includes(item.status)).slice(0, 6);
    return active.length ? active.map((item) => `<article><div><strong>${escapeHtml(item.asset)}</strong><span>${escapeHtml(item.current || 'Current reading unavailable')}</span></div><span class="data-state ${item.status === 'triggered' ? 'stale' : 'partial'}">${escapeHtml(item.status)}</span><p><strong>Trigger:</strong> ${escapeHtml(item.trigger || 'Not specified')}</p><p><strong>Confirmation:</strong> ${escapeHtml(item.confirmation || 'Not specified')}</p></article>`).join('') : '<div class="command-empty">No warning or triggered research conditions are currently listed.</div>';
  }

  function cotRows() {
    const rows = [...(official.cot || [])].filter((row) => row.contract?.identityStatus === 'verified').sort((a, b) => Math.abs(Number(b.weekChange || 0)) - Math.abs(Number(a.weekChange || 0))).slice(0, 6);
    return rows.length ? rows.map((row) => `<tr><th scope="row"><a href="#cot">${escapeHtml(row.name)}</a><small>${escapeHtml(row.contract?.cftcContractCode || '')}</small></th><td>${escapeHtml(row.contract?.category || row.category)}</td><td>${signed(row.net)}</td><td>${signed(row.weekChange)}</td><td>${escapeHtml(row.reportDate)}</td></tr>`).join('') : '<tr><td colspan="5">No verified COT rows are available.</td></tr>';
  }

  function politicalRows() {
    const rows = (political().recentFilings || []).slice(0, 6);
    return rows.length ? rows.map((trade) => `<tr><th scope="row"><a href="#trackers/${encodeURIComponent(trade.politicianId || '')}">${escapeHtml(trade.politician || trade.politicianId || 'Tracked filer')}</a><small>${escapeHtml(trade.ticker || trade.asset || '')}</small></th><td>${escapeHtml(trade.type || 'Not specified')}</td><td>${escapeHtml(trade.owner || 'Not specified')}</td><td>${escapeHtml(trade.traded || '—')}</td><td>${escapeHtml(trade.filed || '—')}</td><td>${escapeHtml(trade.amount || 'Range unavailable')}</td></tr>`).join('') : '<tr><td colspan="6">Recent political filing summary is unavailable.</td></tr>';
  }

  function biasRows() {
    return (research.assetBiases || []).slice(0, 12).map((bias) => `<tr><th scope="row"><a href="#asset/${encodeURIComponent(productId(bias))}">${escapeHtml(bias.name)}</a><small>${escapeHtml(bias.group || '')}</small></th><td><span class="command-bias ${escapeHtml(String(bias.bias || 'neutral').toLowerCase().replace(/\s+/g, '-'))}">${escapeHtml(bias.bias || 'Unclear')}</span></td><td>${escapeHtml(bias.primaryDriver || 'Not specified')}</td><td>${escapeHtml(bias.cot || 'Positioning unavailable')}</td><td>${escapeHtml(bias.nextEvent || 'No event specified')}</td><td>${escapeHtml(bias.changeCondition || 'Not specified')}</td></tr>`).join('');
  }

  function sourceFailures() {
    const failures = [];
    for (const source of official.sourceStatus || []) {
      if (!['current', 'ok', 'success'].includes(String(source.status || '').toLowerCase())) failures.push({ name: source.source || source.id || 'Official source', status: source.status || 'Unavailable', detail: source.detail || source.error || 'No detail supplied.' });
    }
    const ledger = political().sourceStatus?.filingLedger;
    if (Number(ledger?.retryable || 0)) failures.push({ name: 'Political filing ledger', status: 'Partial', detail: `${ledger.retryable} filing${ledger.retryable === 1 ? '' : 's'} remain retryable; prior verified records are retained.` });
    return failures;
  }

  function render() {
    const root = host();
    if (!root) return;
    const command = research.commandCentre || {};
    const failures = sourceFailures();
    const changes = (command.changes || []).slice(0, 3);
    root.dataset.commandCentreRemodel = 'br-14';
    root.innerHTML = `<div class="command-page">
      <header class="command-hero"><div><span class="command-kicker">Decision console</span><h2>${escapeHtml(research.regime?.verdict || 'Market regime unavailable')}</h2><p>${escapeHtml(research.regime?.meaning || command.risk?.summary || 'Regime interpretation is not available.')}</p></div><div class="command-hero-meta"><span class="data-state ${failures.length ? 'partial' : 'current'}">${failures.length ? `${failures.length} source warning${failures.length === 1 ? '' : 's'}` : 'Core sources current'}</span><strong>${escapeHtml(research.regime?.name || 'Regime name unavailable')}</strong><small>Updated ${escapeHtml(command.updated || research.generatedAt || 'time unavailable')}</small></div></header>
      ${dailyBrief()}
      <section class="command-priority"><div class="command-section-heading"><div><span class="command-kicker">What changed</span><h3>Priority market events</h3></div><span>Maximum three</span></div><div class="command-event-grid">${eventCards() || '<div class="command-empty">No curated impact records are available.</div>'}</div><p class="command-direction-note">Arrows show expected directional pressure under the current regime, not certainty or a trading recommendation. Open the causal analysis for the mechanism, confirmation and invalidation.</p></section>
      <section class="command-two-column"><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Next test</span><h3>${escapeHtml(command.nextEvent?.name || 'No event specified')}</h3></div><span>${escapeHtml(command.nextEvent?.time || 'Time unavailable')}</span></div><p>${escapeHtml(command.nextEvent?.logic || 'Decision logic unavailable.')}</p><div class="command-change-list">${changes.map((item, index) => `<article><span>${index + 1}</span><p>${escapeHtml(item)}</p></article>`).join('') || '<div class="command-empty">No change summary supplied.</div>'}</div></article><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Contradictions</span><h3>Active triggers</h3></div><span>Warning and triggered only</span></div><div class="command-trigger-list">${triggerCards()}</div></article></section>
      <section class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Bias board</span><h3>Asset decisions and flip conditions</h3></div><span>No composite score shown</span></div><div class="command-table-scroll"><table class="command-table"><thead><tr><th scope="col">Asset</th><th scope="col">Bias</th><th scope="col">Primary driver</th><th scope="col">Positioning</th><th scope="col">Next event</th><th scope="col">Condition that changes the bias</th></tr></thead><tbody>${biasRows() || '<tr><td colspan="6">Bias records unavailable.</td></tr>'}</tbody></table></div></section>
      <section class="command-two-column"><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">COT change</span><h3>Largest weekly positioning moves</h3></div><a href="#cot">Open COT</a></div><div class="command-table-scroll"><table class="command-table compact"><thead><tr><th scope="col">Contract</th><th scope="col">Category</th><th scope="col">Net</th><th scope="col">1 week</th><th scope="col">Report</th></tr></thead><tbody>${cotRows()}</tbody></table></div></article><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Political Flow</span><h3>Recent official disclosures</h3></div><a href="#trackers">Open Political Flow</a></div><div class="command-table-scroll"><table class="command-table compact"><thead><tr><th scope="col">Filer / asset</th><th scope="col">Action</th><th scope="col">Owner</th><th scope="col">Trade</th><th scope="col">Filed</th><th scope="col">Range</th></tr></thead><tbody>${politicalRows()}</tbody></table></div></article></section>
      <section class="command-source-panel"><div class="command-section-heading"><div><span class="command-kicker">Source health</span><h3>Failures that can change interpretation</h3></div><span>${failures.length} visible warning${failures.length === 1 ? '' : 's'}</span></div>${failures.length ? failures.map((failure) => `<article><span class="data-state ${statusClass(failure.status)}">${escapeHtml(failure.status)}</span><div><strong>${escapeHtml(failure.name)}</strong><p>${escapeHtml(failure.detail)}</p></div></article>`).join('') : '<div class="command-empty">No core source failure is currently reported.</div>'}</section>
    </div>`;
  }

  function show() { activate(); render(); }
  function registerRoute() {
    if (!router || registerRoute.done) return;
    registerRoute.done = true;
    router.register('home', show);
    if (router.current?.()?.path === 'home') router.dispatch('#home', { source: 'command-centre-ready' });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoute, { once: true });
  else registerRoute();
  window.addEventListener('load', registerRoute, { once: true });
})();
