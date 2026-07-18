(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const api = core.political;
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const number = core.format?.formatNumber || ((value) => value === null || value === undefined ? '—' : Number(value).toLocaleString());
  const state = { summary: null, manifest: null, activeId: null, profile: null, yearData: null, year: null, politicianQuery: '', tickerQuery: '', loading: false, error: null };

  function host() { return document.getElementById('view-trackers'); }
  function statusClass(value = '') {
    const text = String(value).toLowerCase();
    if (text.includes('current') || text.includes('parsed')) return 'current';
    if (text.includes('partial')) return 'partial';
    if (text.includes('failed') || text.includes('unavailable')) return 'stale';
    return 'pending';
  }
  function date(value) { return value || 'Not available'; }
  function sourceLink(url, label = 'Official filing') {
    return url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)} ↗</a>` : '<span>Official link unavailable</span>';
  }
  function themeChip(trade) {
    const engine = core.impactEngine;
    const chips = core.impactChips;
    if (!engine || !chips || !trade.ticker) return '';
    const theme = engine.themeForTicker(String(trade.ticker).toLowerCase());
    if (!theme) return '';
    const type = String(trade.type || '').toLowerCase();
    const direction = type.startsWith('purchase') ? 'up' : type.startsWith('sale') ? 'down' : 'activity';
    return `<span class="political-theme-chip">${chips.chipStrip([{
      assetId: theme.id,
      direction,
      tier: 'observed',
      source: 'political',
      label: 'Disclosed trade',
      detail: `Disclosed ${trade.type || 'transaction'} in ${trade.ticker}; filed ${trade.lagDays ?? '?'} days after the trade. Disclosures are lagged and excluded from net-pressure windows.`,
      at: trade.filed || null,
      status: 'current',
      href: '',
    }])}</span>`;
  }
  function activate() {
    if (views?.activate('trackers', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-trackers'));
  }

  function ledgerSummary() {
    return state.summary?.sourceStatus?.filingLedger || window.politicalDisclosureData?.sourceStatus?.filingLedger || {};
  }

  function recentRows() {
    return Array.isArray(state.summary?.recentFilings) ? state.summary.recentFilings : [];
  }

  function trackerItems() {
    const entries = Object.values(state.manifest?.trackers || {});
    const needle = state.politicianQuery.trim().toLowerCase();
    return entries.filter((item) => !needle || `${item.name} ${item.id} ${item.chamber}`.toLowerCase().includes(needle));
  }

  function shell() {
    const root = host();
    if (!root) return;
    root.dataset.politicalFlowRemodel = 'br-10';
    root.innerHTML = `<div class="political-flow-page">
      <header class="political-flow-hero"><div><span class="political-kicker">Delayed public disclosure intelligence</span><h2>Political Flow</h2><p>Official House and Senate filings, separated into trade date, filing date, disclosed owner/account and statutory amount range. This is not real-time execution data. Theme chips on disclosed trades are contextual only — filings lag the trade date, so they are excluded from net-pressure windows.</p></div><div id="politicalFlowFreshness" class="political-flow-freshness"></div></header>
      <section id="politicalFlowStatus" aria-live="polite"></section>
      <section class="political-flow-controls" aria-label="Political Flow search">
        <label><span>Find a politician</span><input id="politicalFlowPoliticianSearch" type="search" placeholder="Pelosi, Whitehouse, House…" autocomplete="off"></label>
        <label><span>Find a ticker or asset</span><div class="political-ticker-row"><input id="politicalFlowTickerSearch" type="search" placeholder="NVDA, XOM, MP…" autocomplete="off"><button id="politicalFlowTickerButton" type="button">Search</button></div></label>
      </section>
      <div id="politicalFlowTickerResults"></div>
      <section><div class="political-section-heading"><div><span class="political-kicker">Directory</span><h3>Tracked official filers</h3></div><span id="politicalFlowCount"></span></div><div id="politicalFlowDirectory" class="political-directory"></div></section>
      <section><div class="political-section-heading"><div><span class="political-kicker">Recent filings</span><h3>Latest disclosed transactions</h3></div><span>Trade date and filing date remain separate</span></div><div id="politicalFlowRecent"></div></section>
      <section id="politicalFlowProfile" aria-live="polite"></section>
    </div>`;
    root.querySelector('#politicalFlowPoliticianSearch')?.addEventListener('input', (event) => {
      state.politicianQuery = event.target.value;
      renderDirectory();
    });
    const tickerSearch = () => searchTicker(root.querySelector('#politicalFlowTickerSearch')?.value || '');
    root.querySelector('#politicalFlowTickerButton')?.addEventListener('click', tickerSearch);
    root.querySelector('#politicalFlowTickerSearch')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') tickerSearch(); });
  }

  function renderFreshness() {
    const target = document.getElementById('politicalFlowFreshness');
    if (!target) return;
    const ledger = ledgerSummary();
    const retryable = Number(ledger.retryable || 0);
    target.innerHTML = `<span class="data-state ${retryable ? 'partial' : 'current'}">${retryable ? `${retryable} filing${retryable === 1 ? '' : 's'} need retry` : 'Collector current'}</span><strong>${number(state.manifest?.totalTrades || state.summary?.totalTrades || 0)} retained trades</strong><small>Generated ${escapeHtml(state.summary?.generatedAtHuman || state.manifest?.generatedAtHuman || 'time unavailable')}</small>`;
  }

  function renderStatus() {
    const target = document.getElementById('politicalFlowStatus');
    if (!target) return;
    const ledger = ledgerSummary();
    const retryable = Array.isArray(ledger.retryableFilings) ? ledger.retryableFilings : [];
    const sources = state.summary?.sourceStatus || {};
    const sourceErrors = [...(sources.house?.errors || []), ...(sources.senate?.errors || []), ...(sources.parsing?.errors || [])];
    target.innerHTML = `<div class="political-health-grid">
      <article><span>Filing ledger</span><strong>${number(ledger.filings || 0)}</strong><small>${escapeHtml(ledger.parserVersion || 'Parser version unavailable')}</small></article>
      <article><span>Retryable filings</span><strong>${number(ledger.retryable || 0)}</strong><small>Failures remain visible and are retried.</small></article>
      <article><span>Source warnings</span><strong>${number(sourceErrors.length)}</strong><small>Prior verified records are retained.</small></article>
    </div>${retryable.length ? `<details class="political-retry-list"><summary>View filing-specific parser/download issues</summary>${retryable.map((item) => `<article><div><strong>${escapeHtml(item.chamber)} · ${escapeHtml(item.trackerId)}</strong><span>${escapeHtml(item.filingId)} · ${escapeHtml(item.state)}</span></div><p>${escapeHtml(item.lastError || 'Retry pending')}</p>${sourceLink(item.reportUrl)}</article>`).join('')}</details>` : ''}`;
  }

  function renderDirectory() {
    const target = document.getElementById('politicalFlowDirectory');
    const count = document.getElementById('politicalFlowCount');
    if (!target) return;
    const items = trackerItems();
    if (count) count.textContent = `${items.length} profile${items.length === 1 ? '' : 's'}`;
    target.innerHTML = items.length ? items.map((item) => `<a class="political-person-card ${state.activeId === item.id ? 'active' : ''}" href="#trackers/${encodeURIComponent(item.id)}" data-political-id="${escapeHtml(item.id)}">
      <span class="political-person-head"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.chamber || 'Congress')}</span></span>
      <span>${number(item.tradeCount)} retained transactions</span><small>Latest trade ${escapeHtml(date(item.latestTrade))} · filed ${escapeHtml(date(item.latestFiling))}</small>
      <em class="data-state ${statusClass(item.status)}">${escapeHtml(item.status || 'Status unavailable')}</em>
    </a>`).join('') : '<div class="political-empty">No tracked filer matches that search.</div>';
  }

  function renderRecent() {
    const target = document.getElementById('politicalFlowRecent');
    if (!target) return;
    const rows = recentRows().slice(0, 24);
    target.innerHTML = rows.length ? `<div class="political-table-scroll"><table class="political-table"><thead><tr><th scope="col">Politician / asset</th><th scope="col">Transaction</th><th scope="col">Disclosed owner/account</th><th scope="col">Trade date</th><th scope="col">Filed</th><th scope="col">Disclosure lag</th><th scope="col">Statutory range</th><th scope="col">Source</th></tr></thead><tbody>${rows.map((trade) => `<tr>
      <th scope="row"><a href="#trackers/${encodeURIComponent(trade.politicianId || '')}"><strong>${escapeHtml(trade.politician || trade.politicianId || 'Tracked filer')}</strong><span>${escapeHtml(trade.ticker || trade.asset || 'Asset not specified')}</span><small>${escapeHtml(trade.asset || '')}</small></a>${themeChip(trade)}</th>
      <td>${escapeHtml(trade.type || 'Not specified')}</td><td>${escapeHtml(trade.owner || 'Not specified')}</td><td>${escapeHtml(date(trade.traded))}</td><td>${escapeHtml(date(trade.filed))}</td><td>${escapeHtml(trade.lag || (trade.lagDays === null || trade.lagDays === undefined ? '—' : `${trade.lagDays} days`))}</td><td>${escapeHtml(trade.amount || 'Range unavailable')}</td><td>${sourceLink(trade.sourceUrl, 'Filing')}</td>
    </tr>`).join('')}</tbody></table></div>` : '<div class="political-empty">No verified recent transactions are available.</div>';
  }

  async function searchTicker(query) {
    const target = document.getElementById('politicalFlowTickerResults');
    if (!target) return;
    const needle = String(query).trim();
    if (!needle) { target.innerHTML = ''; return; }
    target.innerHTML = '<div class="political-loading">Searching the compact ticker index…</div>';
    try {
      const rows = (await api.searchTickers(needle)).slice(0, 20);
      target.innerHTML = `<section class="political-search-results"><div class="political-section-heading"><div><span class="political-kicker">Asset reverse search</span><h3>Matches for “${escapeHtml(needle)}”</h3></div><span>${rows.length} result${rows.length === 1 ? '' : 's'}</span></div>${rows.length ? rows.map((item) => `<article><div><strong>${escapeHtml(item.ticker)}</strong><span>${number(item.tradeCount)} disclosed transactions · latest trade ${escapeHtml(date(item.latestTrade))}</span></div><div class="political-search-politicians">${(item.politicians || []).map((person) => `<a href="#trackers/${encodeURIComponent(person.id)}">${escapeHtml(person.name)}</a>`).join('')}</div><small>${escapeHtml((item.assets || []).slice(0, 3).join(' · '))}</small></article>`).join('') : '<div class="political-empty">No ticker or asset matches the current index.</div>'}</section>`;
    } catch (error) {
      target.innerHTML = `<div class="political-error"><strong>Ticker index unavailable</strong><span>${escapeHtml(error.message)}</span></div>`;
    }
  }

  function tradeTable(trades, caption) {
    return `<div class="political-table-scroll"><table class="political-table"><caption>${escapeHtml(caption)}</caption><thead><tr><th scope="col">Asset</th><th scope="col">Transaction</th><th scope="col">Disclosed owner/account</th><th scope="col">Trade date</th><th scope="col">Filed</th><th scope="col">Lag</th><th scope="col">Statutory range</th><th scope="col">Official source</th></tr></thead><tbody>${trades.length ? trades.map((trade) => `<tr><th scope="row"><strong>${escapeHtml(trade.ticker || 'No ticker')}</strong><span>${escapeHtml(trade.asset || 'Asset not specified')}</span>${themeChip(trade)}</th><td>${escapeHtml(trade.type || 'Not specified')}</td><td>${escapeHtml(trade.owner || 'Not specified')}</td><td>${escapeHtml(date(trade.traded))}</td><td>${escapeHtml(date(trade.filed))}</td><td>${escapeHtml(trade.lag || '—')}</td><td>${escapeHtml(trade.amount || 'Range unavailable')}</td><td>${sourceLink(trade.sourceUrl, 'Open filing')}</td></tr>`).join('') : '<tr><td colspan="8"><div class="political-empty">No verified trades are available for this selection.</div></td></tr>'}</tbody></table></div>`;
  }

  function portfolio(profile) {
    const data = profile.portfolio || {};
    const holdings = Array.isArray(data.holdings) ? data.holdings : [];
    return `<section class="political-profile-section"><div class="political-section-heading"><div><span class="political-kicker">Disclosure-derived portfolio</span><h4>Estimated open positions</h4></div><span>${holdings.length} reconstructed item${holdings.length === 1 ? '' : 's'}</span></div><div class="political-warning"><strong>${escapeHtml(data.status || 'Transaction-derived estimate')}</strong><p>${escapeHtml(data.basis || 'Periodic Transaction Reports do not provide a complete brokerage statement or guaranteed current holdings.')}</p><p>${escapeHtml(data.valuation || 'Values are statutory ranges, not current market values.')}</p></div>${holdings.length ? `<div class="political-holdings">${holdings.slice(0, 80).map((item) => `<article><div><strong>${escapeHtml(item.asset || 'Asset')}</strong><span>${escapeHtml(item.owner || 'Owner/account not specified')}</span></div><p>${escapeHtml(item.amount || 'Range unresolved')}</p><small>${escapeHtml(item.status || 'Status unresolved')} · ${escapeHtml(item.confidence || 'Low confidence')}</small>${sourceLink(item.sourceUrl)}</article>`).join('')}</div>` : '<div class="political-empty">Loadable holdings are not available for this profile.</div>'}</section>`;
  }

  async function loadYear(value) {
    if (!state.activeId || !value) return;
    const target = document.getElementById('politicalProfileHistory');
    if (target) target.innerHTML = '<div class="political-loading">Loading annual filing history…</div>';
    try {
      state.year = String(value);
      state.yearData = await api.year(state.activeId, value);
      renderProfile();
    } catch (error) {
      if (target) target.innerHTML = `<div class="political-error"><strong>Annual history unavailable</strong><span>${escapeHtml(error.message)}</span></div>`;
    }
  }

  function renderProfile() {
    const target = document.getElementById('politicalFlowProfile');
    const profile = state.profile;
    if (!target) return;
    if (state.loading) { target.innerHTML = '<div class="political-loading">Loading official profile files…</div>'; return; }
    if (state.error) { target.innerHTML = `<div class="political-error"><strong>Political profile unavailable</strong><span>${escapeHtml(state.error)}</span></div>`; return; }
    if (!profile) { target.innerHTML = '<div class="political-empty">Choose a tracked filer to open a disclosure profile.</div>'; return; }
    const years = Array.isArray(profile.years) ? profile.years : [];
    const recent = Array.isArray(profile.recentTrades) ? profile.recentTrades : [];
    const history = state.yearData?.trades || recent;
    const displayedYear = state.yearData?.year || 'Recent';
    target.innerHTML = `<article class="political-profile">
      <header><div><span class="political-kicker">Official filer profile</span><h3>${escapeHtml(profile.name || state.activeId)}</h3><p>${escapeHtml(profile.chamber || 'Congress')} · ${number(profile.tradeCount || recent.length)} retained transactions</p></div><div><span class="data-state ${statusClass(profile.status)}">${escapeHtml(profile.status || 'Status unavailable')}</span><small>Updated ${escapeHtml(profile.updated || state.summary?.generatedAtHuman || 'time unavailable')}</small></div></header>
      <div class="political-profile-stats"><article><span>Latest trade</span><strong>${escapeHtml(date(profile.latestTrade))}</strong></article><article><span>Latest filing</span><strong>${escapeHtml(date(profile.latestFiling))}</strong></article><article><span>Available years</span><strong>${number(years.length)}</strong></article><article><span>Parser warnings</span><strong>${number(profile.sourceStatus?.errors?.length || 0)}</strong></article></div>
      <p class="political-owner-note"><strong>Attribution rule:</strong> the “disclosed owner/account” field is preserved exactly. A spouse, dependent or joint-account transaction is not described as a personal trade by the member.</p>
      ${portfolio(profile)}
      <section class="political-profile-section"><div class="political-section-heading"><div><span class="political-kicker">Transaction ledger</span><h4>${escapeHtml(String(displayedYear))} history</h4></div><label class="political-year-select">Year <select id="politicalFlowYear"><option value="recent">Recent</option>${years.map((year) => `<option value="${year}" ${String(year) === String(state.year) ? 'selected' : ''}>${year}</option>`).join('')}</select></label></div><div id="politicalProfileHistory">${tradeTable(history, `${profile.name || state.activeId} ${displayedYear} disclosed transactions`)}</div></section>
    </article>`;
    target.querySelector('#politicalFlowYear')?.addEventListener('change', (event) => {
      if (event.target.value === 'recent') { state.year = null; state.yearData = null; renderProfile(); }
      else loadYear(event.target.value);
    });
  }

  async function openProfile(id, { updateRoute = false } = {}) {
    if (!id || !api) return;
    state.activeId = id;
    state.loading = true;
    state.error = null;
    state.year = null;
    state.yearData = null;
    renderDirectory();
    renderProfile();
    try {
      state.profile = await api.tracker(id);
    } catch (error) {
      state.profile = null;
      state.error = error.message;
    } finally {
      state.loading = false;
      renderDirectory();
      renderProfile();
      if (updateRoute) router?.navigate?.(`trackers/${id}`, { replace: true });
    }
  }

  async function initialiseData() {
    if (!api) throw new Error('Political lazy-data adapter is unavailable.');
    [state.manifest, state.summary] = await Promise.all([api.manifest(), api.summary()]);
    renderFreshness();
    renderStatus();
    renderDirectory();
    renderRecent();
    if (!state.activeId) state.activeId = Object.keys(state.manifest?.trackers || {})[0] || null;
    if (state.activeId) await openProfile(state.activeId);
  }

  function renderPage() {
    activate();
    shell();
    initialiseData().catch((error) => {
      state.error = error.message;
      const target = document.getElementById('politicalFlowStatus');
      if (target) target.innerHTML = `<div class="political-error"><strong>Political Flow data unavailable</strong><span>${escapeHtml(error.message)}</span></div>`;
      renderProfile();
    });
  }

  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    router.register('trackers', () => renderPage());
    router.registerPattern('political-profile', /^trackers\/([^/]+)$/, (route) => {
      activate();
      if (!host()?.dataset.politicalFlowRemodel) shell();
      const id = decodeURIComponent(route.params.id);
      if (!state.summary || !state.manifest) {
        state.activeId = id;
        initialiseData().then(() => openProfile(id)).catch((error) => { state.error = error.message; renderProfile(); });
      } else openProfile(id);
    }, (match) => ({ id: match[1] }));
    const current = router.current?.();
    if (current?.path === 'trackers' || current?.path?.startsWith('trackers/')) router.dispatch(`#${current.path}`, { source: 'political-flow-ready' });
  }

  function initialise() {
    registerRoutes();
    window.setTimeout(registerRoutes, 0);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
  window.addEventListener('load', () => {
    registerRoutes.done = false;
    registerRoutes();
  }, { once: true });
})();
