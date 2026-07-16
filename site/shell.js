(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;

  const routeMeta = {
    home: ['Command Centre', 'What matters now, the active regime and what could change it.'],
    today: ['Command Centre', 'Daily Brief is now part of the decision console.'],
    news: ['Impact Feed', 'Interpreted market-moving developments and transmission channels.'],
    cot: ['COT Positioning', 'Official weekly positioning with disclosed report categories.'],
    rates: ['Rates & Liquidity', 'Observed yields, spreads, policy rates and financial conditions.'],
    'official-feeds': ['Official Feeds', 'Primary agency filings, energy fundamentals and economic observations.'],
    official: ['Official Feeds', 'Primary agency filings, energy fundamentals and economic observations.'],
    'crowd-expectations': ['Crowd Expectations', 'Read-only market-implied probabilities for decision-relevant events.'],
    crowd: ['Crowd Expectations', 'Read-only market-implied probabilities for decision-relevant events.'],
    equities: ['Equity Tape', 'Private delayed market-price watchlist.'],
    events: ['Calendar & Reactions', 'High-impact events, scenarios and post-event follow-through.'],
    week: ['Week Ahead', 'The active weekly thesis, event radar and verified moves.'],
    regime: ['Regime', 'The strategic interpretation layer used across the console.'],
    triggers: ['Trigger Zones', 'Decision levels, confirmation rules and invalidation conditions.'],
    assets: ['Assets', 'Cross-asset monitoring levels and directional logic.'],
    products: ['Research Library', 'Commodity dossiers, market structure and active catalysts.'],
    'product-detail': ['Product Dossier', 'Detailed commodity research workspace.'],
    scenarios: ['Scenario Lab', 'Conditional market paths and the evidence required to support them.'],
    trackers: ['Political Flow', 'Policy events and delayed official financial disclosures.'],
    archive: ['Archive', 'Daily, weekly and strategic research memory.'],
    asset: ['Asset Workspace', 'Evidence, flip conditions, catalysts and positioning for one asset.']
  };

  const $ = (id) => document.getElementById(id);
  const sidebar = $('sidebar');
  const overlay = $('overlay');
  const menu = $('menu');
  const moreButton = $('mobileMoreButton');
  const moreDrawer = $('mobileMore');
  const moreClose = $('mobileMoreClose');
  const railToggle = $('railToggle');

  function activeView() { return document.querySelector('.view.active')?.id?.replace(/^view-/, '') || 'home'; }
  function updatePageContext(view = activeView()) {
    const hash = String(window.location.hash || '').replace(/^#/, '');
    const key = hash.startsWith('asset/') ? 'asset' : hash.startsWith('product/') ? 'product-detail' : view;
    const [title, subtitle] = routeMeta[key] || routeMeta.home;
    if ($('pageTitle')) $('pageTitle').textContent = title;
    if ($('pageSubtitle')) $('pageSubtitle').textContent = subtitle;
    document.title = `${title} · Market Brief`;
  }
  function syncNavigation(view = activeView()) {
    document.querySelectorAll('[data-shell-view], #nav button[data-view]').forEach((button) => {
      const route = button.dataset.shellView || button.dataset.view;
      const isProductAlias = view === 'product-detail' && route === 'products';
      const current = route === view || isProductAlias;
      button.classList.toggle('active', current);
      if (current) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
    });
    updatePageContext(view);
  }
  function setMenuState(open) {
    menu?.setAttribute('aria-expanded', String(open));
    sidebar?.setAttribute('aria-hidden', String(!open && window.matchMedia('(max-width: 1279px)').matches));
  }
  function closeMore({ restoreFocus = true } = {}) {
    if (!moreDrawer || moreDrawer.hidden) return;
    moreDrawer.hidden = true;
    moreButton?.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('more-open');
    if (!sidebar?.classList.contains('open')) overlay?.classList.remove('show');
    if (restoreFocus) moreButton?.focus();
  }
  function openMore() {
    if (!moreDrawer) return;
    moreDrawer.hidden = false;
    moreButton?.setAttribute('aria-expanded', 'true');
    document.body.classList.add('more-open');
    overlay?.classList.add('show');
    moreClose?.focus();
  }
  function goToRoute(route) {
    closeMore({ restoreFocus: false });
    if (router) router.navigate(route, { replace: true });
    else {
      const desktopButton = document.querySelector(`#nav button[data-view="${CSS.escape(route)}"]`);
      if (desktopButton) desktopButton.click(); else window.location.hash = route;
    }
    requestAnimationFrame(() => syncNavigation());
  }
  document.querySelectorAll('[data-shell-view]').forEach((button) => button.addEventListener('click', () => goToRoute(button.dataset.shellView)));
  moreButton?.addEventListener('click', () => { if (moreDrawer?.hidden) openMore(); else closeMore(); });
  moreClose?.addEventListener('click', () => closeMore());
  railToggle?.addEventListener('click', () => {
    const expanded = !document.body.classList.contains('rail-expanded');
    document.body.classList.toggle('rail-expanded', expanded);
    railToggle.setAttribute('aria-expanded', String(expanded));
    try { localStorage.setItem('marketBriefRailExpanded', expanded ? '1' : '0'); } catch (_) { /* optional */ }
  });
  try {
    const expanded = localStorage.getItem('marketBriefRailExpanded') === '1';
    document.body.classList.toggle('rail-expanded', expanded);
    railToggle?.setAttribute('aria-expanded', String(expanded));
  } catch (_) { /* optional */ }
  overlay?.addEventListener('click', () => closeMore({ restoreFocus: false }));
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    closeMore();
    if (sidebar?.classList.contains('open')) { sidebar.classList.remove('open'); overlay?.classList.remove('show'); menu?.focus(); }
  });
  const sidebarObserver = sidebar && new MutationObserver(() => setMenuState(sidebar.classList.contains('open')));
  sidebarObserver?.observe(sidebar, { attributes: true, attributeFilter: ['class'] });
  const viewObserver = new MutationObserver(() => syncNavigation());
  document.querySelectorAll('.view').forEach((view) => viewObserver.observe(view, { attributes: true, attributeFilter: ['class'] }));
  if (router) router.subscribe(() => requestAnimationFrame(() => syncNavigation())); else window.addEventListener('hashchange', () => requestAnimationFrame(() => syncNavigation()));
  window.addEventListener('hashchange', () => updatePageContext());
  window.addEventListener('resize', () => { setMenuState(Boolean(sidebar?.classList.contains('open'))); if (window.innerWidth >= 600) closeMore({ restoreFocus: false }); });
  $('search')?.setAttribute('aria-label', 'Search locally available assets, catalysts and research routes');

  // Global search jump palette: matches views, asset workspaces, dossiers and tracked filers.
  const paletteEsc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  function searchIndex() {
    const research = window.MarketBriefCore?.adapters?.research?.() || {};
    const mk = (label, hint, hash, extra) => ({ label, hint, hash, search: `${label} ${extra || ''}`.trim().toLowerCase() });
    const entries = Object.entries(routeMeta)
      .filter(([route]) => !['today', 'official', 'crowd', 'equities', 'product-detail', 'asset'].includes(route))
      .map(([route, meta]) => mk(meta[0], 'View', route));
    (research.assetBiases || []).forEach((bias) => { if (bias?.name) entries.push(mk(bias.name, 'Asset workspace', `asset/${bias.productId || bias.id}`, bias.group)); });
    (research.products || []).forEach((product) => { if (product?.name) entries.push(mk(product.name, 'Research dossier', `product/${product.id}`, product.group)); });
    const trackers = research.trackers || {};
    (research.trackerOrder || Object.keys(trackers)).forEach((id) => { const filer = trackers[id]; const label = filer?.title || filer?.name; if (label) entries.push(mk(label, 'Political profile', `trackers/${id}`, id)); });
    return entries;
  }
  function renderSearchResults(query) {
    const box = $('searchResults');
    if (!box) return;
    const term = String(query || '').trim().toLowerCase();
    if (term.length < 2) { box.hidden = true; box.innerHTML = ''; return; }
    const matches = searchIndex().filter((entry) => (entry.search || '').includes(term)).slice(0, 8);
    box.innerHTML = matches.length
      ? matches.map((entry) => `<button type="button" role="option" data-palette-hash="${paletteEsc(entry.hash)}"><strong>${paletteEsc(entry.label)}</strong><span>${paletteEsc(entry.hint)}</span></button>`).join('')
      : '<div class="search-empty">No local match across views, assets, dossiers and tracked filers.</div>';
    box.hidden = false;
  }
  function closeSearchResults() { const box = $('searchResults'); if (box) { box.hidden = true; box.innerHTML = ''; } }
  const paletteInput = $('search');
  if (paletteInput) {
    paletteInput.addEventListener('input', () => renderSearchResults(paletteInput.value));
    paletteInput.addEventListener('keydown', (event) => {
      const box = $('searchResults');
      if (event.key === 'Escape') { closeSearchResults(); return; }
      if (event.key === 'ArrowDown' && box && !box.hidden) { event.preventDefault(); box.querySelector('button')?.focus(); return; }
      if (event.key === 'Enter' && box && !box.hidden) {
        const first = box.querySelector('button[data-palette-hash]');
        if (first) { event.preventDefault(); event.stopImmediatePropagation(); window.location.hash = first.dataset.paletteHash; closeSearchResults(); }
      }
    });
  }
  $('searchResults')?.addEventListener('keydown', (event) => {
    const options = [...event.currentTarget.querySelectorAll('button')];
    const index = options.indexOf(document.activeElement);
    if (event.key === 'ArrowDown') { event.preventDefault(); options[Math.min(index + 1, options.length - 1)]?.focus(); }
    if (event.key === 'ArrowUp') { event.preventDefault(); if (index <= 0) paletteInput?.focus(); else options[index - 1]?.focus(); }
    if (event.key === 'Escape') { closeSearchResults(); paletteInput?.focus(); }
  });
  document.addEventListener('click', (event) => {
    const option = event.target.closest?.('[data-palette-hash]');
    if (option) { window.location.hash = option.dataset.paletteHash; closeSearchResults(); if (paletteInput) paletteInput.value = ''; return; }
    if (!event.target.closest?.('.search')) closeSearchResults();
  }, true);

  setMenuState(Boolean(sidebar?.classList.contains('open')));
  if (router) router.start(window.__marketInitialHash || window.location.hash || '#home'); else syncNavigation();
})();
