(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const research = core.adapters?.research?.() || (typeof fallback !== 'undefined' ? fallback : {});
  const official = core.adapters?.official?.() || window.freeMarketData || {};
  const impact = () => core.impact?.get?.() || window.marketImpactData || { items: [] };
  const conflict = () => window.conflictWatchData || { collection: { status: 'failed', sourceStatus: [] }, items: [] };
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

  function timeLabel(value) {
    if (!value) return 'Time unavailable';
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime())
      ? value
      : parsed.toLocaleString('en-AU', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' });
  }

  function decisionGuide() {
    return `<details class="command-decision-guide">
      <summary><span class="command-kicker">How to use this console</span><h3 id="commandGuideTitle">From trigger to decision</h3></summary>
      <div class="command-decision-guide-body"><p>Start with the dominant driver, then require confirmation across prices and physical data. Use the asset pressure as a conditional map, and the flip condition as the point where the interpretation must change.</p>
      <ol><li><span>1</span><div><strong>Trigger</strong><small>What changed in policy, conflict, data or physical flows?</small></div></li><li><span>2</span><div><strong>Confirmation</strong><small>Do oil, yields, the dollar, volatility and exposed assets agree?</small></div></li><li><span>3</span><div><strong>Transmission</strong><small>Which assets face upward, downward or mixed pressure under this regime?</small></div></li><li><span>4</span><div><strong>Flip condition</strong><small>What observable evidence would weaken or reverse the view?</small></div></li></ol></div>
    </details>`;
  }

  function heroStats() {
    const stats = (research.daily?.stats || []).slice(0, 6);
    if (!stats.length) return '';
    return `<section class="command-stat-strip" aria-label="Today’s observed moves">${stats.map((stat) => {
      const dir = directionLabel(stat.dir);
      return `<article class="command-stat ${escapeHtml(dir)}"><span class="command-stat-label">${escapeHtml(stat.label)}</span><strong>${escapeHtml(stat.value || '—')}</strong><span class="command-stat-move"><span aria-hidden="true">${directionGlyph(stat.dir)}</span> ${escapeHtml(stat.move || 'No move recorded')}</span></article>`;
    }).join('')}</section>`;
  }

  function conflictWatch() {
    const feed = conflict();
    const collection = feed.collection || {};
    const items = (feed.items || []).slice(0, 5);
    const flowEscalation = [
      { label: 'Brent', direction: 'up', detail: 'Conditional on verified disruption to Gulf production, shipping or insurance capacity.' },
      { label: 'Gold', direction: 'up', detail: 'Safe-haven pressure is strongest when risk assets and real yields confirm.' },
      { label: 'Inflation risk', direction: 'up', detail: 'Sustained energy and freight costs can feed the policy channel.' },
      { label: 'Risk assets', direction: 'down', detail: 'Higher input costs and uncertainty can pressure margins and valuation.' },
    ];
    const deEscalation = [
      { label: 'Brent', direction: 'down', detail: 'Requires improving physical transit and lower freight or insurance stress, not rhetoric alone.' },
      { label: 'Inflation risk', direction: 'down', detail: 'A durable energy-premium reversal weakens the hawkish pass-through.' },
      { label: 'Risk assets', direction: 'up', detail: 'Relief is more credible when volatility and the dollar also ease.' },
      { label: 'Gold', direction: 'mixed', detail: 'Lower haven demand can be offset if yields and the dollar also fall.' },
    ];
    return `<section class="command-conflict command-panel" aria-labelledby="commandConflictTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Primary live trigger</span><h3 id="commandConflictTitle">Conflict and war transmission watch</h3></div><div class="command-conflict-meta"><span class="data-state ${statusClass(collection.status)}">${escapeHtml(collection.status || 'Unavailable')}</span><small>Checked ${escapeHtml(timeLabel(feed.generatedAtUtc))} · scheduled every 3 hours</small></div></div>
      <p class="command-conflict-intro">Official-source publications are shown as updates, not independently verified facts. The pressure maps below are Market Brief analysis: they apply only if the development is verified, materially changes physical flows or policy risk, and receives cross-asset confirmation.</p>
      <div class="command-conflict-map"><article><strong>Escalation with physical-flow confirmation</strong>${directionStrip(flowEscalation, 'Conditional pressure')}</article><article><strong>De-escalation with restored transit</strong>${directionStrip(deEscalation, 'Conditional pressure')}</article></div>
      <div class="command-conflict-updates">${items.length ? items.map((item) => `<article><header><span>${escapeHtml(item.source?.name || 'Official source')}</span><time datetime="${escapeHtml(item.publishedAt)}">${escapeHtml(timeLabel(item.publishedAt))}</time></header><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.summary)}</p><footer><div>${(item.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join('')}${item.dataState === 'stale-retained' ? '<span class="retained">Retained</span>' : ''}</div><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Open official update ↗</a></footer></article>`).join('') : '<div class="command-empty">No market-relevant official conflict publication is available in the current 14-day window.</div>'}</div>
      <div class="command-conflict-footer"><span>${escapeHtml(feed.methodology || 'Official publication watch unavailable.')}</span><a href="https://www.ukmto.org/ukmto-products/warnings" target="_blank" rel="noopener noreferrer">Open UKMTO maritime warnings ↗</a></div>
    </section>`;
  }

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
    const headlines = (daily.headlines || []).slice(0, 5);
    const chain = (research.regime?.chain || []).slice(0, 8);
    return `<section class="command-daily command-panel" aria-labelledby="commandDailyTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Daily Brief</span><h3 id="commandDailyTitle">${escapeHtml(daily.title || 'Today’s market brief')}</h3></div><span>${escapeHtml(daily.asOf || research.generatedAt || 'As-of time unavailable')}</span></div>
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
    const conflictCollection = conflict().collection || {};
    if (conflictCollection.status && conflictCollection.status !== 'current') failures.push({ name: 'Conflict publication watch', status: conflictCollection.status, detail: `${Number(conflictCollection.failureCount || 0)} official source refresh${Number(conflictCollection.failureCount || 0) === 1 ? '' : 'es'} failed; ${Number(conflictCollection.retainedItemCount || 0)} previously verified item${Number(conflictCollection.retainedItemCount || 0) === 1 ? '' : 's'} retained.` });
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
      ${heroStats()}
      ${conflictWatch()}
      ${dailyBrief()}
      <section class="command-priority"><div class="command-section-heading"><div><span class="command-kicker">What changed</span><h3>Priority market events</h3></div><span>Maximum three</span></div><div class="command-event-grid">${eventCards() || '<div class="command-empty">No curated impact records are available.</div>'}</div><p class="command-direction-note">Arrows show expected directional pressure under the current regime, not certainty or a trading recommendation. Open the causal analysis for the mechanism, confirmation and invalidation.</p></section>
      <section class="command-two-column"><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Next test</span><h3>${escapeHtml(command.nextEvent?.name || 'No event specified')}</h3></div><span>${escapeHtml(command.nextEvent?.time || 'Time unavailable')}</span></div><p>${escapeHtml(command.nextEvent?.logic || 'Decision logic unavailable.')}</p><div class="command-change-list">${changes.map((item, index) => `<article><span>${index + 1}</span><p>${escapeHtml(item)}</p></article>`).join('') || '<div class="command-empty">No change summary supplied.</div>'}</div></article><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Contradictions</span><h3>Active triggers</h3></div><span>Warning and triggered only</span></div><div class="command-trigger-list">${triggerCards()}</div></article></section>
      <section class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Bias board</span><h3>Asset decisions and flip conditions</h3></div><span>No composite score shown</span></div><div class="command-table-scroll"><table class="command-table"><thead><tr><th scope="col">Asset</th><th scope="col">Bias</th><th scope="col">Primary driver</th><th scope="col">Positioning</th><th scope="col">Next event</th><th scope="col">Condition that changes the bias</th></tr></thead><tbody>${biasRows() || '<tr><td colspan="6">Bias records unavailable.</td></tr>'}</tbody></table></div></section>
      <section class="command-two-column"><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">COT change</span><h3>Largest weekly positioning moves</h3></div><a href="#cot">Open COT</a></div><div class="command-table-scroll"><table class="command-table compact"><thead><tr><th scope="col">Contract</th><th scope="col">Category</th><th scope="col">Net</th><th scope="col">1 week</th><th scope="col">Report</th></tr></thead><tbody>${cotRows()}</tbody></table></div></article><article class="command-panel"><div class="command-section-heading"><div><span class="command-kicker">Political Flow</span><h3>Recent official disclosures</h3></div><a href="#trackers">Open Political Flow</a></div><div class="command-table-scroll"><table class="command-table compact"><thead><tr><th scope="col">Filer / asset</th><th scope="col">Action</th><th scope="col">Owner</th><th scope="col">Trade</th><th scope="col">Filed</th><th scope="col">Range</th></tr></thead><tbody>${politicalRows()}</tbody></table></div></article></section>
      ${decisionGuide()}
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
