(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.commandCentre || !Array.isArray(fallback.assetBiases)) return;

  const data = fallback;
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const biasClass = (bias = '') => {
    const value = bias.toLowerCase();
    if (value.includes('bull') || value.includes('higher')) return 'bullish';
    if (value.includes('bear')) return 'bearish';
    if (value.includes('unstable')) return 'unstable';
    return 'neutral';
  };

  const componentClass = (score) => score > 0 ? 'positive' : score < 0 ? 'negative' : 'neutral';
  const componentLabel = (score) => score > 0 ? `+${score}` : String(score);

  function showHome(updateHash = true) {
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    $('view-home')?.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === 'home'));
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
    if (updateHash) history.replaceState(null, '', '#home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderRiskGauge() {
    const risk = data.commandCentre.risk;
    const riskAngle = Math.max(0, Math.min(100, risk.score)) * 3.6;
    $('commandRisk').innerHTML = `<article class="card risk-gauge-card">
      <div class="risk-ring" style="--risk-angle:${riskAngle}deg">
        <div class="risk-ring-inner"><strong>${escapeHtml(risk.score)}</strong><span>risk score</span></div>
      </div>
      <div class="risk-copy"><div class="eyebrow">Cross-asset risk gauge</div><h3>${escapeHtml(risk.state)}</h3><p>${escapeHtml(risk.summary)}</p><span class="risk-confidence">${escapeHtml(risk.confidence)} confidence</span></div>
    </article>`;

    $('riskInputs').innerHTML = risk.inputs.map((input) => `<article class="risk-input"><div><strong>${escapeHtml(input.name)} · ${escapeHtml(input.reading)}</strong><small>${escapeHtml(input.reason)}</small></div><span class="risk-score">+${escapeHtml(input.score)}</span></article>`).join('');
    $('riskChangeConditions').innerHTML = `<strong>What would move the gauge back toward neutral</strong><ul>${risk.changeConditions.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
    $('riskContradiction').textContent = risk.contradiction;
  }

  function renderCommandSummary() {
    const command = data.commandCentre;
    $('commandUpdated').textContent = `Updated ${command.updated}`;
    $('commandRegime').innerHTML = `<span>${escapeHtml(data.regime.verdict)}</span><span>${escapeHtml(data.regime.name)}</span>`;
    $('commandNextEvent').innerHTML = `<div class="eyebrow">Next high-impact test</div><h3>${escapeHtml(command.nextEvent.name)}</h3><div class="next-event-time">${escapeHtml(command.nextEvent.time)}</div><p>${escapeHtml(command.nextEvent.logic)}</p>`;
    $('commandChanges').innerHTML = command.changes.map((item, index) => `<article class="change-item"><span>${index + 1}</span><p>${escapeHtml(item)}</p></article>`).join('');

    const activeTriggers = data.triggers.filter((trigger) => ['warning', 'triggered'].includes(trigger.status));
    $('commandTriggers').innerHTML = activeTriggers.map((trigger) => `<article class="risk-input"><div><strong>${escapeHtml(trigger.asset)} · ${escapeHtml(trigger.current)}</strong><small>${escapeHtml(trigger.trigger)} · confirmation: ${escapeHtml(trigger.confirmation)}</small></div><span class="trigger-pill ${escapeHtml(trigger.status)}">${escapeHtml(trigger.status)}</span></article>`).join('');
  }

  function biasComponentsHtml(bias) {
    return `<div class="bias-components">${bias.components.map((component) => `<article class="bias-component"><div class="bias-component-top"><strong>${escapeHtml(component.name)}</strong><span class="component-score ${componentClass(component.score)}">${componentLabel(component.score)}</span></div><p>${escapeHtml(component.reason)}</p></article>`).join('')}</div>`;
  }

  function renderBiasDetail(id) {
    const bias = data.assetBiases.find((item) => item.id === id) || data.assetBiases[0];
    if (!bias) return;
    $('biasDetail').innerHTML = `<article class="card bias-detail">
      <div class="bias-detail-head"><div><div class="eyebrow">Auditable bias engine</div><h3>${escapeHtml(bias.name)} · ${escapeHtml(bias.bias)}</h3><p>Primary driver: ${escapeHtml(bias.primaryDriver)} · confidence ${escapeHtml(bias.confidence)}%</p></div><div class="bias-total ${componentClass(bias.total)}">${componentLabel(bias.total)}</div></div>
      ${biasComponentsHtml(bias)}
      <div class="bias-condition"><article><strong>Positioning state</strong><p>${escapeHtml(bias.cot)}</p></article><article><strong>Condition that changes the bias</strong><p>${escapeHtml(bias.changeCondition)}</p></article></div>
    </article>`;
  }

  function openProduct(id) {
    if (!id) return;
    location.hash = `product/${id}`;
  }

  function renderBiasBoard() {
    $('biasTable').innerHTML = `<thead><tr><th>Asset</th><th>Reference</th><th>Bias</th><th>Confidence</th><th>Primary driver</th><th>COT / positioning</th><th>Next event</th><th>Action</th></tr></thead><tbody>${data.assetBiases.map((bias) => `<tr>
      <td><strong>${escapeHtml(bias.name)}</strong><span>${escapeHtml(bias.group)}</span></td>
      <td>${escapeHtml(bias.reference)}</td>
      <td><span class="bias-chip ${biasClass(bias.bias)}">${escapeHtml(bias.bias)}</span></td>
      <td><strong>${escapeHtml(bias.confidence)}%</strong><div class="confidence-bar"><span style="width:${Math.max(0, Math.min(100, bias.confidence))}%"></span></div></td>
      <td>${escapeHtml(bias.primaryDriver)}</td>
      <td>${escapeHtml(bias.cot)}</td>
      <td>${escapeHtml(bias.nextEvent)}</td>
      <td><div class="bias-actions"><button data-bias-detail="${escapeHtml(bias.id)}">Why?</button>${bias.productId ? `<button data-bias-product="${escapeHtml(bias.productId)}">Deep dive</button>` : ''}</div></td>
    </tr>`).join('')}</tbody>`;

    document.querySelectorAll('[data-bias-detail]').forEach((button) => button.addEventListener('click', () => renderBiasDetail(button.dataset.biasDetail)));
    document.querySelectorAll('[data-bias-product]').forEach((button) => button.addEventListener('click', () => openProduct(button.dataset.biasProduct)));
    renderBiasDetail(data.assetBiases[0]?.id);
  }

  function injectProductBias() {
    const detail = $('productDetail');
    if (!detail || detail.querySelector('#productBiasPanel')) return;
    const match = location.hash.match(/^#product\/(.+)$/);
    if (!match) return;
    const bias = data.assetBiases.find((item) => item.productId === match[1]);
    const hero = detail.querySelector('.deep-hero');
    if (!bias || !hero) return;
    const panel = document.createElement('article');
    panel.id = 'productBiasPanel';
    panel.className = 'card product-bias-panel';
    panel.innerHTML = `<div class="bias-detail-head"><div><div class="eyebrow">Current bias engine</div><h3>${escapeHtml(bias.bias)} · ${escapeHtml(bias.confidence)}% confidence</h3><p>Primary driver: ${escapeHtml(bias.primaryDriver)}</p></div><span class="bias-chip ${biasClass(bias.bias)}">score ${componentLabel(bias.total)}</span></div>${biasComponentsHtml(bias)}<div class="bias-condition"><article><strong>Next event</strong><p>${escapeHtml(bias.nextEvent)}</p></article><article><strong>Bias changes when</strong><p>${escapeHtml(bias.changeCondition)}</p></article></div>`;
    hero.insertAdjacentElement('afterend', panel);
  }

  function politicalRecords() {
    const rows = [];
    Object.entries(data.trackers || {}).forEach(([id, tracker]) => {
      const person = tracker.displayName || tracker.title || id;
      (Array.isArray(tracker.trades) ? tracker.trades : []).forEach((trade) => rows.push({
        person, trackerId: id, recordType: 'Transaction', asset: trade.asset || '', action: trade.type || '', owner: trade.owner || 'Not specified',
        traded: trade.traded || '—', filed: trade.filed || '—', amount: trade.amount || 'Range unavailable', sourceUrl: trade.sourceUrl || ''
      }));
      (Array.isArray(tracker.portfolio?.holdings) ? tracker.portfolio.holdings : []).forEach((holding) => rows.push({
        person, trackerId: id, recordType: 'Holding', asset: holding.asset || '', action: holding.status || 'Estimated open', owner: holding.owner || 'Not specified',
        traded: holding.lastActivity || 'Annual baseline', filed: '—', amount: holding.amount || holding.range || 'Range unavailable', sourceUrl: holding.sourceUrl || ''
      }));
    });
    return rows;
  }

  function renderStockSearch(query = '') {
    const output = $('politicalStockResults');
    if (!output) return;
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      output.innerHTML = '<div class="stock-empty">Search a ticker or company—such as NVDA, XOM, LMT, MP or Newmont—to see every verified tracked transaction and estimated holding across the political watchlist.</div>';
      return;
    }

    const matches = politicalRecords().filter((row) => row.asset.toLowerCase().includes(normalized));
    const people = new Set(matches.map((row) => row.person));
    const transactions = matches.filter((row) => row.recordType === 'Transaction').length;
    const holdings = matches.filter((row) => row.recordType === 'Holding').length;

    if (!matches.length) {
      output.innerHTML = `<div class="stock-empty">No verified imported disclosure currently matches <strong>${escapeHtml(query)}</strong>. This does not mean no politician traded it; the historical disclosure backfill is still incomplete.</div>`;
      return;
    }

    output.innerHTML = `<div class="stock-result-summary"><article><span>Politicians</span><strong>${people.size}</strong></article><article><span>Transactions</span><strong>${transactions}</strong></article><article><span>Estimated holdings</span><strong>${holdings}</strong></article></div>
      <div class="stock-results card table-wrap"><table><thead><tr><th>Person</th><th>Asset</th><th>Record</th><th>Action/status</th><th>Owner</th><th>Trade/activity</th><th>Filed</th><th>Amount</th></tr></thead><tbody>${matches.map((row) => `<tr><td>${escapeHtml(row.person)}</td><td>${row.sourceUrl ? `<a class="table-link" href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(row.asset)} ↗</a>` : escapeHtml(row.asset)}</td><td>${escapeHtml(row.recordType)}</td><td>${escapeHtml(row.action)}</td><td>${escapeHtml(row.owner)}</td><td>${escapeHtml(row.traded)}</td><td>${escapeHtml(row.filed)}</td><td>${escapeHtml(row.amount)}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function initialiseStockSearch() {
    const input = $('politicalStockSearch');
    const button = $('politicalStockSearchButton');
    if (!input || !button) return;
    const run = () => renderStockSearch(input.value);
    input.addEventListener('input', run);
    input.addEventListener('keydown', (event) => { if (event.key === 'Enter') run(); });
    button.addEventListener('click', run);
    renderStockSearch('');
  }

  function initialDocumentHash() {
    if (typeof window.__marketInitialHash === 'string') return window.__marketInitialHash;
    const entry = performance.getEntriesByType('navigation')[0];
    if (!entry?.name) return location.hash;
    try { return new URL(entry.name).hash; } catch { return location.hash; }
  }

  function initialise() {
    renderRiskGauge();
    renderCommandSummary();
    renderBiasBoard();
    initialiseStockSearch();

    const detail = $('productDetail');
    if (detail) {
      const observer = new MutationObserver(() => requestAnimationFrame(injectProductBias));
      observer.observe(detail, { childList: true, subtree: false });
    }
    window.addEventListener('hashchange', () => {
      if (location.hash === '#home') showHome(false);
      requestAnimationFrame(injectProductBias);
    });
    $('nav')?.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-view="home"]');
      if (!button) return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      showHome();
    }, true);
    injectProductBias();

    const initialHash = initialDocumentHash();
    if (!initialHash) showHome(true);
    else if (initialHash === '#home') showHome(false);
  }

  initialise();
})();
