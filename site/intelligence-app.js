(() => {
  'use strict';
  const data = typeof fallback !== 'undefined' ? fallback : null;
  if (!data) return;

  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const keyRows = (pairs = []) => `<div class="key-list">${pairs.map(([key, value]) => `<div class="key-row"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(value)}</span></div>`).join('')}</div>`;
  const sourceButtons = (links = []) => `<div class="source-buttons">${links.map(([label, url]) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(label)} ↗</a>`).join('')}</div>`;

  function showView(view, updateHash = true) {
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    $(`view-${view}`)?.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === view));
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (updateHash) history.replaceState(null, '', `#${view}`);
  }

  let activeNewsFilter = 'All';
  function renderNews(query = '') {
    if (!data.newsFeed) return;
    $('newsDelay').textContent = data.newsFeed.delayNote;
    const filters = ['All', 'High impact', ...new Set(data.newsFeed.items.map((item) => item.category))];
    $('newsFilters').innerHTML = filters.map((filter) => `<button class="${filter === activeNewsFilter ? 'active' : ''}" data-news-filter="${escapeHtml(filter)}">${escapeHtml(filter)}</button>`).join('');
    document.querySelectorAll('[data-news-filter]').forEach((button) => button.addEventListener('click', () => {
      activeNewsFilter = button.dataset.newsFilter;
      renderNews($('search').value.trim().toLowerCase());
    }));

    const normalized = query.toLowerCase();
    const items = data.newsFeed.items.filter((item) => {
      const filterMatch = activeNewsFilter === 'All' || (activeNewsFilter === 'High impact' ? item.impact === 'High' : item.category === activeNewsFilter);
      const haystack = `${item.headline} ${item.summary} ${item.category} ${item.assets.map((asset) => asset.name).join(' ')}`.toLowerCase();
      return filterMatch && (!normalized || haystack.includes(normalized));
    });

    $('newsFeed').innerHTML = items.length ? items.map((item) => `<article class="news-card">
      <div class="news-top"><div class="news-meta"><span class="impact-tag ${item.impact.toLowerCase()}">${escapeHtml(item.impact)} impact</span><span class="state-tag">${escapeHtml(item.status)}</span></div><span class="news-time">${escapeHtml(item.time)}</span></div>
      <h3>${escapeHtml(item.headline)}</h3><p>${escapeHtml(item.summary)}</p>
      <div class="asset-watch"><div class="asset-watch-label">Assets to watch</div><div class="asset-chips">${item.assets.map((asset) => `<button class="asset-chip ${escapeHtml(asset.direction)}" title="${escapeHtml(asset.reason)}">${escapeHtml(asset.name)} ${asset.direction === 'up' ? '↑' : asset.direction === 'down' ? '↓' : '→'}</button>`).join('')}</div></div>
      <div class="impact-explain"><div class="impact-label">Why this impacts markets</div><div class="impact-grid">${item.channels.map(([label, body]) => `<div class="impact-box"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(body)}</span></div>`).join('')}</div></div>
      <a class="source-link" href="${escapeHtml(item.sourceUrl)}" target="_blank" rel="noopener">Source: ${escapeHtml(item.source)} ↗</a>
    </article>`).join('') : '<div class="card empty">No news items match that filter.</div>';

    $('newsSidebar').innerHTML = `<article class="card explainer-card"><h3>How to read the feed</h3><p>Direction is expected pressure under the current regime, not a guaranteed move.</p><ul><li><strong>Assets to watch</strong> identifies the first markets likely to react.</li><li><strong>Why this impacts markets</strong> separates first-order and second-order channels.</li><li><strong>Invalidation</strong> tells you what would make the interpretation wrong.</li></ul></article><article class="card explainer-card"><h3>Current sign-flip</h3><p>${escapeHtml(data.regime.meaning)}</p></article><article class="card explainer-card"><h3>Data timing</h3><p>${escapeHtml(data.newsFeed.asOf)}. This build is intentionally delayed and research-led rather than a live headline wire.</p></article>`;
  }

  const tradeLimits = {};
  let activeTracker = 'trump';
  let trackerQuery = '';

  function orderedTrackerIds() {
    const preferred = Array.isArray(data.trackerOrder) ? data.trackerOrder : [];
    return [...preferred, ...Object.keys(data.trackers || {}).filter((id) => !preferred.includes(id))]
      .filter((id) => data.trackers[id]);
  }

  function renderTrackerDirectory() {
    const ids = orderedTrackerIds();
    const visible = ids.filter((id) => {
      const tracker = data.trackers[id];
      const haystack = `${tracker.displayName || tracker.title} ${tracker.chamber || ''} ${tracker.kind || ''}`.toLowerCase();
      return !trackerQuery || haystack.includes(trackerQuery);
    });
    $('trackerCount').textContent = `${visible.length} tracker${visible.length === 1 ? '' : 's'}`;
    $('trackerTabs').innerHTML = visible.map((id) => {
      const tracker = data.trackers[id];
      const label = tracker.displayName || tracker.title;
      const meta = tracker.kind === 'executive' ? 'Policy + disclosure' : `${tracker.chamber || 'Congress'} disclosure`;
      return `<button data-tracker="${id}" class="${id === activeTracker ? 'active' : ''}"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(meta)}</span></button>`;
    }).join('') || '<div class="card empty">No tracked politician matches that search.</div>';

    document.querySelectorAll('[data-tracker]').forEach((button) => button.addEventListener('click', () => {
      activeTracker = button.dataset.tracker;
      renderTrackers();
    }));
  }

  function renderPortfolio(tracker) {
    const portfolio = tracker.portfolio || { holdings: [] };
    const holdings = Array.isArray(portfolio.holdings) ? portfolio.holdings : [];
    const openCount = holdings.filter((item) => !String(item.status || '').toLowerCase().includes('closed')).length;
    return `<div class="section-title"><h3>Estimated current portfolio</h3><span>Disclosure-derived, not a brokerage statement</span></div>
      <div class="portfolio-summary grid cols-4">
        <article class="card stat"><span class="stat-label">Tracked positions</span><div class="stat-value" style="font-size:18px">${holdings.length}</div></article>
        <article class="card stat"><span class="stat-label">Potentially open</span><div class="stat-value" style="font-size:18px">${openCount}</div></article>
        <article class="card stat"><span class="stat-label">Ledger status</span><div class="stat-value" style="font-size:15px">${escapeHtml(portfolio.status || 'Reconstruction enabled')}</div></article>
        <article class="card stat"><span class="stat-label">Updated</span><div class="stat-value" style="font-size:15px">${escapeHtml(portfolio.updated || tracker.updated)}</div></article>
      </div>
      <article class="card portfolio-method"><strong>How the portfolio is built</strong><p>${escapeHtml(portfolio.basis || '')}</p><p>${escapeHtml(portfolio.valuation || '')}</p><p>${escapeHtml(portfolio.ownerNote || '')}</p></article>
      <div class="card table-wrap"><table class="matrix portfolio-table"><thead><tr><th>Asset</th><th>Owner / account</th><th>Estimated holding</th><th>Status</th><th>Last activity</th><th>Confidence</th></tr></thead><tbody>${holdings.length ? holdings.map((holding) => `<tr><td>${holding.sourceUrl ? `<a class="table-link" href="${escapeHtml(holding.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(holding.asset)} ↗</a>` : escapeHtml(holding.asset)}</td><td>${escapeHtml(holding.owner || 'Not specified')}</td><td>${escapeHtml(holding.amount || holding.range || 'Range unavailable')}</td><td>${escapeHtml(holding.status || 'Estimated open')}</td><td>${escapeHtml(holding.lastActivity || 'Annual disclosure baseline')}</td><td>${escapeHtml(holding.confidence || 'Medium')}</td></tr>`).join('') : `<tr><td colspan="6"><div class="empty-trades">${escapeHtml(portfolio.emptyMessage || 'No verified holdings have been imported yet.')}</div></td></tr>`}</tbody></table></div>`;
  }

  function renderTradeHistory(tracker, trackerId) {
    tradeLimits[trackerId] = tradeLimits[trackerId] || 100;
    const trades = Array.isArray(tracker.trades) ? [...tracker.trades] : [];
    trades.sort((a, b) => String(b.traded || '').localeCompare(String(a.traded || '')));
    const visible = trades.slice(0, tradeLimits[trackerId]);
    const remaining = Math.max(0, trades.length - visible.length);
    const history = tracker.historyPolicy || {};
    return `<div class="section-title"><h3>Complete disclosed transaction history</h3><span>${trades.length} verified transaction${trades.length === 1 ? '' : 's'} retained</span></div>
      <article class="card history-policy">${keyRows([['Retention', history.retention || 'All verified trades are retained.'],['Trade vs filing date', history.dating || 'Trade and filing dates remain separate.'],['Late filings', history.lateFilings || 'Late-filed trades are still added.'],['Large archives', history.archive || 'History is loaded in pages.']])}</article>
      <div class="card table-wrap"><table class="matrix trade-history-table"><thead><tr><th>Asset</th><th>Transaction</th><th>Owner</th><th>Trade date</th><th>Filed</th><th>Lag</th><th>Amount range</th></tr></thead><tbody>${visible.length ? visible.map((trade) => `<tr><td>${trade.sourceUrl ? `<a class="table-link" href="${escapeHtml(trade.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(trade.asset)} ↗</a>` : escapeHtml(trade.asset)}</td><td>${escapeHtml(trade.type)}</td><td>${escapeHtml(trade.owner || 'Not specified')}</td><td>${escapeHtml(trade.traded)}</td><td>${escapeHtml(trade.filed)}</td><td>${escapeHtml(trade.lag || '—')}</td><td>${escapeHtml(trade.amount || 'Range unavailable')}</td></tr>`).join('') : `<tr><td colspan="7"><div class="empty-trades">${escapeHtml(tracker.emptyMessage || 'No verified transactions have been imported yet.')}</div></td></tr>`}</tbody></table></div>
      ${remaining ? `<button class="load-more" data-load-more="${trackerId}">Load 100 more transactions (${remaining} remaining)</button>` : ''}`;
  }

  function renderTrackers() {
    if (!data.trackers) return;
    if (!data.trackers[activeTracker]) activeTracker = orderedTrackerIds()[0];
    renderTrackerDirectory();

    const tracker = data.trackers[activeTracker];
    const isTrump = tracker.kind === 'executive' || activeTracker === 'trump';
    const eyebrow = isTrump ? 'Executive branch' : `${tracker.chamber || 'Congressional'} disclosure`;
    const header = `<div class="card disclosure-card"><div class="tracker-head"><div><div class="eyebrow">${escapeHtml(eyebrow)}</div><h3>${escapeHtml(tracker.title)}</h3><p>${escapeHtml(tracker.subtitle)}</p></div><span class="tracker-updated">Updated ${escapeHtml(tracker.updated)}</span></div></div><div class="tracker-warning">${escapeHtml(tracker.warning)}</div><div class="grid cols-4">${tracker.stats.map(([label, value]) => `<article class="card stat"><span class="stat-label">${escapeHtml(label)}</span><div class="stat-value" style="font-size:17px">${escapeHtml(value)}</div></article>`).join('')}</div>`;
    const portfolio = renderPortfolio(tracker);
    const tradeHistory = renderTradeHistory(tracker, activeTracker);

    if (isTrump) {
      const events = Array.isArray(tracker.policyEvents) ? tracker.policyEvents : [];
      $('trackerContent').innerHTML = `${header}${portfolio}${tradeHistory}<div class="section-title"><h3>Policy event feed</h3><span>${escapeHtml(tracker.cadence)}</span></div><div class="card">${events.map((event) => `<article class="tracker-event"><div class="tracker-event-head"><div><span class="state-tag">${escapeHtml(event.type)}</span><h4>${escapeHtml(event.title)}</h4></div><span class="news-time">${escapeHtml(event.date)} · ${escapeHtml(event.status)}</span></div><p>${escapeHtml(event.detail)}</p><div class="tracker-assets">${event.assets.map((asset) => `<span>${escapeHtml(asset)}</span>`).join('')}</div><a class="source-link" href="${escapeHtml(event.sourceUrl)}" target="_blank" rel="noopener">Source: ${escapeHtml(event.source)} ↗</a></article>`).join('')}</div><div class="section-title"><h3>Tariff impact playbook</h3><span>Impact map — not a list of active policies</span></div><div class="card table-wrap"><table class="matrix"><thead><tr><th>Target</th><th>FX</th><th>Equities</th><th>Commodities</th></tr></thead><tbody>${(tracker.tariffMatrix || []).map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><div class="section-title"><h3>Public financial disclosure</h3><span>Delayed filing data</span></div><article class="card disclosure-card"><h3>${escapeHtml(tracker.disclosure?.headline || 'Public financial disclosure')}</h3><p>${escapeHtml(tracker.disclosure?.summary || '')}</p><div class="product-meta">${(tracker.disclosure?.labels || []).map((label) => `<span class="mini-pill">${escapeHtml(label)}</span>`).join('')}</div>${tracker.disclosure?.sourceUrl ? `<a class="source-link" href="${escapeHtml(tracker.disclosure.sourceUrl)}" target="_blank" rel="noopener">Source: ${escapeHtml(tracker.disclosure.source)} ↗</a>` : ''}${sourceButtons(tracker.sourceLinks)}</article>`;
    } else {
      const sourceDescription = tracker.chamber === 'Senate' ? 'Official Senate disclosures are the primary record.' : 'Official House disclosures are the primary record.';
      $('trackerContent').innerHTML = `${header}${portfolio}${tradeHistory}<div class="section-title"><h3>How to read the disclosure</h3><span>Avoid look-ahead bias</span></div><article class="card deep-section">${keyRows(tracker.context || [])}</article><article class="card disclosure-card" style="margin-top:16px"><h3>Data sources</h3><p>${escapeHtml(sourceDescription)} Third-party tools can assist discovery, but parsed records must be checked against the filing.</p>${sourceButtons(tracker.sourceLinks)}</article>`;
    }

    document.querySelector('[data-load-more]')?.addEventListener('click', (event) => {
      const id = event.currentTarget.dataset.loadMore;
      tradeLimits[id] = (tradeLimits[id] || 100) + 100;
      renderTrackers();
    });
  }

  renderNews();
  renderTrackers();

  $('trackerSearch')?.addEventListener('input', (event) => {
    trackerQuery = event.target.value.trim().toLowerCase();
    renderTrackerDirectory();
  });

  $('nav')?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-view]');
    if (!button || !['news', 'trackers'].includes(button.dataset.view)) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    showView(button.dataset.view);
  }, true);

  $('search')?.addEventListener('input', () => {
    if ($('view-news')?.classList.contains('active')) renderNews($('search').value.trim().toLowerCase());
  });

  const applyExtendedRoute = () => {
    const route = location.hash.replace(/^#/, '');
    if (['news', 'trackers'].includes(route)) showView(route, false);
  };
  window.addEventListener('hashchange', applyExtendedRoute);
  applyExtendedRoute();
})();
