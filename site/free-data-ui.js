(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const data = core.adapters?.official() || window.freeMarketData || { rates: [], curveSpreads: [], cot: [], sourceStatus: [], methodology: {} };
  const research = core.adapters?.evidence() || window.marketResearchData || { physicalChecklists: {}, eventReactions: [] };
  const legacyResearch = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : {});
  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\"', '&quot;').replaceAll("'", '&#039;'));
  const formatNumber = core.format?.formatNumber || ((value, maximumFractionDigits = 0) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(undefined, { maximumFractionDigits }));
  const signed = core.format?.signed || ((value, suffix = '') => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : `${Number(value) > 0 ? '+' : ''}${formatNumber(Number(value), 1)}${suffix}`);
  const statusClass = core.status?.className || ((status = '') => status.toLowerCase().includes('current') ? 'current' : status.toLowerCase().includes('partial') ? 'partial' : status.toLowerCase().includes('stale') ? 'stale' : 'pending');
  const directionClass = (value) => Number(value) > 0 ? 'number-up' : Number(value) < 0 ? 'number-down' : 'number-flat';

  function showView(view, updateHash = true) {
    if (updateHash && router) {
      router.navigate(view, { replace: true });
      return;
    }
    if (views?.activate(view)) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    $(`view-${view}`)?.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === view));
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
    if (updateHash) history.replaceState(null, '', `#${view}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderSourceStatus(hostId) {
    const host = $(hostId);
    if (!host) return;
    host.innerHTML = (data.sourceStatus || []).map((source) => `<article class="source-status">
      <div class="source-status-head"><strong>${escapeHtml(source.source)}</strong><span class="data-state ${statusClass(source.status)}">${escapeHtml(source.status)}</span></div>
      <p>${escapeHtml(source.detail)}</p>
      <a href="${escapeHtml(source.url)}" target="_blank" rel="noopener">Official source ↗</a>
    </article>`).join('');
  }

  function renderCot() {
    const rows = Array.isArray(data.cot) ? data.cot : [];
    $('cotUpdated').textContent = `Data cache: ${data.generatedAt || 'awaiting first run'}`;
    renderSourceStatus('cotSourceStatus');

    if (!rows.length) {
      $('cotSummary').innerHTML = '<article class="card data-summary-card"><span>Status</span><strong>Pending</strong><small>Run the free-data workflow once to populate CFTC positioning.</small></article>';
      $('cotTable').innerHTML = '<tbody><tr><td><div class="stock-empty">No CFTC rows have been cached yet. The scheduled workflow will populate this automatically.</div></td></tr></tbody>';
      return;
    }

    const sortedPercentile = [...rows].filter((row) => row.netPercentile5y !== null).sort((a, b) => b.netPercentile5y - a.netPercentile5y);
    const largestWeekly = [...rows].filter((row) => row.weekChange !== null).sort((a, b) => Math.abs(b.weekChange) - Math.abs(a.weekChange))[0];
    const newestDate = [...rows].map((row) => row.reportDate).sort().reverse()[0];
    $('cotSummary').innerHTML = `
      <article class="card data-summary-card"><span>Markets loaded</span><strong>${rows.length}</strong><small>Commodities plus selected financial futures.</small></article>
      <article class="card data-summary-card"><span>Highest net percentile</span><strong>${escapeHtml(sortedPercentile[0]?.name || '—')}</strong><small>${sortedPercentile[0] ? `${formatNumber(sortedPercentile[0].netPercentile5y, 1)}th percentile` : 'Insufficient history'}</small></article>
      <article class="card data-summary-card"><span>Largest weekly shift</span><strong>${escapeHtml(largestWeekly?.name || '—')}</strong><small>${largestWeekly ? signed(largestWeekly.weekChange) + ' contracts' : 'No comparison yet'}</small></article>
      <article class="card data-summary-card"><span>Latest report date</span><strong>${escapeHtml(newestDate || '—')}</strong><small>COT positions are normally Tuesday observations released Friday.</small></article>`;

    $('cotTable').innerHTML = `<thead><tr><th>Market</th><th>Category</th><th>Long</th><th>Short</th><th>Net</th><th>1 week</th><th>4 weeks</th><th>5-year percentile</th><th>Crowding</th><th>Open interest</th><th>Report date</th></tr></thead><tbody>${rows.map((row) => `<tr>
      <td><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.market)}</span></td>
      <td>${escapeHtml(row.category)}</td>
      <td>${formatNumber(row.long)}</td>
      <td>${formatNumber(row.short)}</td>
      <td class="${directionClass(row.net)}">${signed(row.net)}</td>
      <td class="${directionClass(row.weekChange)}">${signed(row.weekChange)}</td>
      <td class="${directionClass(row.fourWeekChange)}">${signed(row.fourWeekChange)}</td>
      <td>${row.netPercentile5y === null ? '—' : `${formatNumber(row.netPercentile5y, 1)}%`}</td>
      <td><span class="crowding-pill">${escapeHtml(row.crowding)}</span></td>
      <td>${formatNumber(row.openInterest)}</td>
      <td>${escapeHtml(row.reportDate)}</td>
    </tr>`).join('')}</tbody>`;

    $('cotMethodology').innerHTML = `<strong>Methodology</strong><p>${escapeHtml(data.methodology?.cot || '')}</p><p>${escapeHtml(data.methodology?.warning || '')}</p>`;
  }

  function rateDisplay(row) {
    if (row.unit === '%') return `${formatNumber(row.value, 2)}%`;
    return formatNumber(row.value, 2);
  }

  function renderRates() {
    const rows = Array.isArray(data.rates) ? data.rates : [];
    $('ratesUpdated').textContent = `Data cache: ${data.generatedAt || 'awaiting first run'}`;
    renderSourceStatus('ratesSourceStatus');

    if (!rows.length) {
      $('rateCards').innerHTML = '<article class="card rate-card"><span>Status</span><strong>Pending</strong><small>Run the free-data workflow once to populate rates.</small></article>';
      $('ratesTable').innerHTML = '<tbody><tr><td><div class="stock-empty">No rate observations have been cached yet.</div></td></tr></tbody>';
      return;
    }

    const preferred = ['DGS2', 'DGS5', 'DGS10', 'DGS30', 'DFII10', 'T10YIE', 'BAMLH0A0HYM2', 'DFF', 'SOFR', 'DTWEXBGS'];
    const ordered = [...rows].sort((a, b) => preferred.indexOf(a.id) - preferred.indexOf(b.id));
    $('rateCards').innerHTML = ordered.slice(0, 10).map((row) => `<article class="card rate-card">
      <span>${escapeHtml(row.name)}</span><strong>${rateDisplay(row)}</strong><small class="${directionClass(row.change)}">${row.changeBps !== null ? signed(row.changeBps, ' bp') : signed(row.change)} · ${escapeHtml(row.date)}</small>
    </article>`).join('');

    $('curveSpreads').innerHTML = (data.curveSpreads || []).map((spread) => `<article class="card curve-spread"><span class="eyebrow">Yield curve</span><strong>${escapeHtml(spread.name)} · ${signed(spread.value, spread.unit === 'bp' ? ' bp' : '')}</strong><p>${escapeHtml(spread.interpretation)}</p></article>`).join('');

    $('ratesTable').innerHTML = `<thead><tr><th>Series</th><th>Type</th><th>Latest</th><th>Previous</th><th>Change</th><th>Observation date</th><th>Source</th></tr></thead><tbody>${ordered.map((row) => `<tr>
      <td><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.id)}</span></td>
      <td>${escapeHtml(row.kind)}</td>
      <td>${rateDisplay(row)}</td>
      <td>${row.previous === null ? '—' : row.unit === '%' ? `${formatNumber(row.previous, 2)}%` : formatNumber(row.previous, 2)}</td>
      <td class="${directionClass(row.change)}">${row.changeBps !== null ? signed(row.changeBps, ' bp') : signed(row.change)}</td>
      <td>${escapeHtml(row.date)}</td>
      <td><a class="table-link" href="${escapeHtml(row.sourceUrl)}" target="_blank" rel="noopener">FRED ↗</a></td>
    </tr>`).join('')}</tbody>`;

    $('ratesMethodology').innerHTML = `<strong>Interpretation rule</strong><p>${escapeHtml(data.methodology?.rates || '')}</p><p>A rise in yields is not given one universal meaning. The daily research must classify whether growth, inflation, supply or tighter policy is the dominant cause.</p>`;
  }

  function renderEvents() {
    const events = Array.isArray(research.eventReactions) ? research.eventReactions : [];
    $('eventReactionCount').textContent = `${events.length} tracked event${events.length === 1 ? '' : 's'}`;
    $('eventReactionList').innerHTML = events.length ? events.map((event) => `<article class="card event-reaction-card">
      <div class="event-reaction-head"><div><div class="eyebrow">${escapeHtml(event.source)}</div><h3>${escapeHtml(event.event)}</h3><p>${escapeHtml(event.scheduled)}</p></div><span class="event-stage">${escapeHtml(event.stage)}</span></div>
      <div class="event-facts"><article class="event-fact"><span>Previous</span><strong>${escapeHtml(event.previous)}</strong></article><article class="event-fact"><span>Consensus</span><strong>${escapeHtml(event.consensus)}</strong></article><article class="event-fact"><span>Actual</span><strong>${escapeHtml(event.actual)}</strong></article></div>
      <div class="event-scenarios">${event.scenarios.map(([label, body]) => `<article class="event-scenario"><strong>${escapeHtml(label)}</strong><p>${escapeHtml(body)}</p></article>`).join('')}</div>
      <div class="reaction-timeline"><article class="reaction-step"><span>Immediate</span><strong>${escapeHtml(event.reactions.immediate)}</strong></article><article class="reaction-step"><span>Close</span><strong>${escapeHtml(event.reactions.close)}</strong></article><article class="reaction-step"><span>+1 day</span><strong>${escapeHtml(event.reactions.day1)}</strong></article><article class="reaction-step"><span>+5 days</span><strong>${escapeHtml(event.reactions.day5)}</strong></article></div>
      <div class="methodology-note"><strong>Current verdict: ${escapeHtml(event.verdict)}</strong><p>The event stays open until the reaction is classified as confirmed, faded, reversed or structurally important.</p></div>
    </article>`).join('') : '<div class="card stock-empty">No events are currently tracked.</div>';
  }

  function cotById(id) {
    return (data.cot || []).find((row) => row.id === id);
  }

  function rateById(id) {
    return (data.rates || []).find((row) => row.id === id);
  }

  function applyCotToBiasEngine() {
    if (!Array.isArray(legacyResearch.assetBiases)) return;
    const mapping = {
      gold: 'gold', oil: 'oil', copper: 'copper', silver: 'silver', yen: 'usdjpy', 'us10y-futures': 'us10y'
    };
    Object.entries(mapping).forEach(([cotId, biasId]) => {
      const cot = cotById(cotId);
      const bias = legacyResearch.assetBiases.find((item) => item.id === biasId);
      if (!cot || !bias) return;
      const inverseNote = cotId === 'yen' ? ' Yen futures positioning is inverse to USD/JPY direction.' : cotId === 'us10y-futures' ? ' Treasury-futures positioning is not the same as a yield position.' : '';
      bias.cot = `${cot.crowding}; net ${signed(cot.net)}; ${cot.netPercentile5y === null ? 'percentile unavailable' : `${formatNumber(cot.netPercentile5y, 1)}th percentile`}; ${cot.reportDate}.${inverseNote}`;
      const positioning = bias.components.find((component) => component.name.toLowerCase().includes('position'));
      if (positioning) positioning.reason = `${cot.category}: ${cot.crowding.toLowerCase()}, weekly change ${signed(cot.weekChange)} contracts. Research must decide whether this confirms momentum or creates contrarian crowding risk.`;
    });
  }

  function dynamicEvidence(productId, item) {
    const copy = { ...item };
    const cotMap = { gold: 'gold', oil: 'oil', copper: 'copper', silver: 'silver' };
    if (item.source.includes('CFTC') && cotMap[productId]) {
      const cot = cotById(cotMap[productId]);
      if (cot) {
        copy.reading = `${cot.crowding}; net ${signed(cot.net)}; ${cot.netPercentile5y === null ? 'percentile unavailable' : `${formatNumber(cot.netPercentile5y, 1)}th percentile`}`;
        copy.status = 'automatic';
        copy.freshness = `Report ${cot.reportDate}`;
      }
    }
    if (item.name.includes('real yield')) {
      const realYield = rateById('DFII10');
      if (realYield) {
        copy.reading = `${formatNumber(realYield.value, 2)}% (${signed(realYield.changeBps, ' bp')})`;
        copy.status = 'automatic';
        copy.freshness = realYield.date;
      }
    }
    if (item.name === 'US dollar') {
      const dollar = rateById('DTWEXBGS');
      if (dollar) {
        copy.reading = `Trade-weighted index ${formatNumber(dollar.value, 2)} (${signed(dollar.change)})`;
        copy.status = 'partial';
        copy.freshness = dollar.date;
      }
    }
    return copy;
  }

  function injectPhysicalEvidence() {
    const match = location.hash.match(/^#product\/(.+)$/);
    const detail = $('productDetail');
    if (!match || !detail) return;
    const productId = match[1];
    const checklist = research.physicalChecklists?.[productId];
    if (!checklist || detail.querySelector('#physicalEvidencePanel')) return;
    const anchor = detail.querySelector('#productBiasPanel') || detail.querySelector('.deep-hero');
    if (!anchor) return;
    const panel = document.createElement('article');
    panel.id = 'physicalEvidencePanel';
    panel.className = 'card physical-evidence-panel';
    const items = checklist.items.map((item) => dynamicEvidence(productId, item));
    panel.innerHTML = `<div class="eyebrow">Required evidence</div><h3>${escapeHtml(checklist.title)}</h3><p>${escapeHtml(checklist.summary)}</p><div class="evidence-list">${items.map((item) => `<article class="evidence-item"><div class="evidence-item-head"><h4>${escapeHtml(item.name)}</h4><span class="evidence-status ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></div><div class="evidence-reading">${escapeHtml(item.reading)}</div><p>${escapeHtml(item.interpretation)}</p><div class="evidence-meta"><span>${escapeHtml(item.source)}</span><span>${escapeHtml(item.freshness)}</span></div></article>`).join('')}</div>`;
    anchor.insertAdjacentElement('afterend', panel);
  }

  function renderTradingViewNews() {
    const host = $('tradingViewNewsFeed');
    if (!host || host.dataset.loaded) return;
    host.dataset.loaded = 'true';
    host.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-timeline.js';
    script.async = true;
    script.textContent = JSON.stringify({
      feedMode: 'all_symbols', isTransparent: true, displayMode: 'regular', width: '100%', height: '520', colorTheme: 'dark', locale: 'en'
    });
    host.appendChild(script);
  }

  function initialiseRoutes() {
    const supported = ['cot', 'rates', 'events'];
    if (router) {
      supported.forEach((view) => router.register(view, () => showView(view, false)));
      router.subscribe(() => requestAnimationFrame(() => requestAnimationFrame(injectPhysicalEvidence)));
      return;
    }
    $('nav')?.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-view]');
      if (!button || !supported.includes(button.dataset.view)) return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      showView(button.dataset.view);
    }, true);
    const route = () => {
      const target = location.hash.replace(/^#/, '');
      if (supported.includes(target)) showView(target, false);
      if (target === 'news') renderTradingViewNews();
      requestAnimationFrame(() => requestAnimationFrame(injectPhysicalEvidence));
    };
    window.addEventListener('hashchange', route);
    route();
  }

  function initialise() {
    applyCotToBiasEngine();
    renderCot();
    renderRates();
    renderEvents();
    renderTradingViewNews();
    initialiseRoutes();

    const detail = $('productDetail');
    if (detail) {
      const observer = new MutationObserver(() => requestAnimationFrame(() => requestAnimationFrame(injectPhysicalEvidence)));
      observer.observe(detail, { childList: true, subtree: false });
    }
    injectPhysicalEvidence();
  }

  initialise();
})();
