(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;

  const routeMeta = {
    home: ['Command Centre', 'What matters now, the active regime and what could change it.'],
    today: ['Daily Brief', 'The latest research-led cross-asset recap.'],
    news: ['Impact Feed', 'Interpreted market-moving developments and transmission channels.'],
    cot: ['COT Positioning', 'Official weekly positioning with disclosed report categories.'],
    rates: ['Rates & Liquidity', 'Observed yields, spreads, policy rates and financial conditions.'],
    'official-feeds': ['Official Feeds', 'Primary agency filings, energy fundamentals and economic observations.'],
    official: ['Official Feeds', 'Primary agency filings, energy fundamentals and economic observations.'],
    events: ['Calendar & Reactions', 'High-impact events, scenarios and post-event follow-through.'],
    week: ['Week Ahead', 'The active weekly thesis, event radar and verified moves.'],
    regime: ['Regime', 'The strategic interpretation layer used across the console.'],
    triggers: ['Trigger Zones', 'Decision levels, confirmation rules and invalidation conditions.'],
    assets: ['Assets', 'Cross-asset monitoring levels and directional logic.'],
    products: ['Research Library', 'Commodity dossiers, market structure and active catalysts.'],
    'product-detail': ['Product Dossier', 'Detailed commodity research workspace.'],
    scenarios: ['Scenario Lab', 'Conditional market paths and the evidence required to support them.'],
    trackers: ['Political Flow', 'Policy events and delayed official financial disclosures.'],
    archive: ['Archive', 'Daily, weekly and strategic research memory.']
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
    const [title, subtitle] = routeMeta[view] || routeMeta.home;
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
  window.addEventListener('resize', () => { setMenuState(Boolean(sidebar?.classList.contains('open'))); if (window.innerWidth >= 600) closeMore({ restoreFocus: false }); });
  $('search')?.setAttribute('aria-label', 'Search locally available assets, catalysts and research routes');
  setMenuState(Boolean(sidebar?.classList.contains('open')));
  if (router) router.start(window.__marketInitialHash || window.location.hash || '#home'); else syncNavigation();
})();
