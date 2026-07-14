#!/usr/bin/env python3
"""Apply the BR-05 adapter/router migration to existing static renderers."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"BR-05 migration failed: missing {label}")
    return text.replace(old, new, 1)


def sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"BR-05 migration failed: {label} replacements={count}")
    return updated


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def migrate_index() -> None:
    path = SITE / "index.html"
    text = path.read_text(encoding="utf-8")
    if 'core/router.js' in text:
        return
    text = replace_once(
        text,
        '<script src="energy-expansion.js"></script>\n<script src="app.js"></script>',
        '<script src="energy-expansion.js"></script>\n'
        '<script src="core/format.js"></script>\n'
        '<script src="core/status.js"></script>\n'
        '<script src="core/store.js"></script>\n'
        '<script src="core/adapters.js"></script>\n'
        '<script src="core/router.js"></script>\n'
        '<script src="app.js"></script>',
        'core script insertion',
    )
    write(path, text)


def migrate_app() -> None:
    path = SITE / "app.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const data = typeof fallback !== 'undefined' \? fallback : null;.*?  const listHtml",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const data = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : null);
  if (!data) {
    document.body.innerHTML = '<div style=\"padding:40px;color:white;font-family:system-ui\">Dashboard data failed to load.</div>';
    return;
  }

  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\\\"', '&quot;').replaceAll(\"'\", '&#039;'));

  const listHtml""",
        'app adapter header',
    )
    text = sub_once(
        text,
        r"  function setView\(view, updateHash = true\) \{.*?\n  \}\n\n  function renderToday",
        """  function setView(view, updateHash = true) {
    if (updateHash && view !== 'product-detail' && router) {
      router.navigate(view, { replace: true });
      return;
    }
    if (views?.activate(view)) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    const target = $(`view-${view}`) || $('view-today');
    target.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => {
      const isProductDetail = view === 'product-detail' && button.dataset.view === 'products';
      button.classList.toggle('active', button.dataset.view === view || isProductDetail);
    });
    closeMenu();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (updateHash && view !== 'product-detail') history.replaceState(null, '', `#${view}`);
  }

  function renderToday""",
        'app view adapter',
    )
    text = replace_once(text, '  function openProduct(id) {', '  function openProduct(id, updateHash = true) {', 'app product signature')
    text = replace_once(
        text,
        "    setView('product-detail', false);\n    history.replaceState(null, '', `#product/${product.id}`);",
        "    setView('product-detail', false);\n    if (updateHash && router) router.navigate(`product/${product.id}`, { replace: true });\n    else if (updateHash) history.replaceState(null, '', `#product/${product.id}`);",
        'app product route',
    )
    text = sub_once(
        text,
        r"  function handleRoute\(\) \{.*?\n  \}\n\n  function initialise",
        """  function handleRouteLegacy() {
    const route = location.hash.replace(/^#/, '') || 'today';
    if (route.startsWith('product/')) {
      openProduct(route.split('/')[1], false);
      return;
    }
    const allowed = ['today', 'week', 'regime', 'triggers', 'assets', 'products', 'archive'];
    setView(allowed.includes(route) ? route : 'today', false);
  }

  function registerCoreRoutes() {
    if (!router) return false;
    ['today', 'week', 'regime', 'triggers', 'assets', 'products', 'archive'].forEach((route) => {
      router.register(route, () => setView(route, false));
    });
    router.registerPattern('product-detail', /^product\\/([^/]+)$/, (route) => openProduct(route.params.id, false), (match) => ({ id: decodeURIComponent(match[1]) }));
    return true;
  }

  function initialise""",
        'app route registration',
    )
    text = replace_once(text, "    renderArchive();\n\n    document.querySelectorAll", "    renderArchive();\n    const routed = registerCoreRoutes();\n\n    document.querySelectorAll", 'app route setup')
    text = replace_once(
        text,
        "    window.addEventListener('hashchange', handleRoute);\n    handleRoute();",
        "    if (!routed) {\n      window.addEventListener('hashchange', handleRouteLegacy);\n      handleRouteLegacy();\n    }",
        'app legacy route fallback',
    )
    write(path, text)


def migrate_intelligence() -> None:
    path = SITE / "intelligence-app.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const data = typeof fallback !== 'undefined' \? fallback : null;.*?  const keyRows",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const data = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : null);
  if (!data) return;

  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\\\"', '&quot;').replaceAll(\"'\", '&#039;'));
  const keyRows""",
        'intelligence adapter header',
    )
    text = sub_once(
        text,
        r"  function showView\(view, updateHash = true\) \{.*?\n  \}\n\n  let activeNewsFilter",
        """  function showView(view, updateHash = true) {
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
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (updateHash) history.replaceState(null, '', `#${view}`);
  }

  let activeNewsFilter""",
        'intelligence view adapter',
    )
    text = sub_once(
        text,
        r"  const applyExtendedRoute = \(\) => \{.*?  applyExtendedRoute\(\);",
        """  if (router) {
    router.register('news', () => showView('news', false));
    router.register('trackers', () => showView('trackers', false));
  } else {
    const applyExtendedRoute = () => {
      const route = location.hash.replace(/^#/, '');
      if (['news', 'trackers'].includes(route)) showView(route, false);
    };
    window.addEventListener('hashchange', applyExtendedRoute);
    applyExtendedRoute();
  }""",
        'intelligence route registration',
    )
    write(path, text)


def migrate_command() -> None:
    path = SITE / "command-centre.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  if \(typeof fallback === 'undefined'.*?  const biasClass",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const data = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : null);
  if (!data?.commandCentre || !Array.isArray(data.assetBiases)) return;

  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\\\"', '&quot;').replaceAll(\"'\", '&#039;'));

  const biasClass""",
        'command adapter header',
    )
    text = sub_once(
        text,
        r"  function showHome\(updateHash = true\) \{.*?\n  \}\n\n  function renderRiskGauge",
        """  function showHome(updateHash = true) {
    if (updateHash && router) {
      router.navigate('home', { replace: true });
      return;
    }
    if (!views?.activate('home')) {
      document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
      $('view-home')?.classList.add('active');
      document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === 'home'));
      $('sidebar')?.classList.remove('open');
      $('overlay')?.classList.remove('show');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    if (updateHash && !router) history.replaceState(null, '', '#home');
  }

  function renderRiskGauge""",
        'command view adapter',
    )
    text = replace_once(
        text,
        "  function openProduct(id) {\n    if (!id) return;\n    location.hash = `product/${id}`;\n  }",
        "  function openProduct(id) {\n    if (!id) return;\n    if (router) router.navigate(`product/${id}`, { replace: true });\n    else location.hash = `product/${id}`;\n  }",
        'command product route',
    )
    text = replace_once(text, "  function initialise() {\n    renderRiskGauge();", "  function initialise() {\n    if (router) router.register('home', () => showHome(false));\n    renderRiskGauge();", 'command route setup')
    text = replace_once(
        text,
        "    const initialHash = initialDocumentHash();\n    if (!initialHash) showHome(true);\n    else if (initialHash === '#home') showHome(false);",
        "    if (!router) {\n      const initialHash = initialDocumentHash();\n      if (!initialHash) showHome(true);\n      else if (initialHash === '#home') showHome(false);\n    }",
        'command legacy initial route',
    )
    write(path, text)


def migrate_free_data() -> None:
    path = SITE / "free-data-ui.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const data = window.freeMarketData.*?  const directionClass",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const data = core.adapters?.official() || window.freeMarketData || { rates: [], curveSpreads: [], cot: [], sourceStatus: [], methodology: {} };
  const research = core.adapters?.evidence() || window.marketResearchData || { physicalChecklists: {}, eventReactions: [] };
  const legacyResearch = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : {});
  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\\\"', '&quot;').replaceAll(\"'\", '&#039;'));
  const formatNumber = core.format?.formatNumber || ((value, maximumFractionDigits = 0) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString(undefined, { maximumFractionDigits }));
  const signed = core.format?.signed || ((value, suffix = '') => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : `${Number(value) > 0 ? '+' : ''}${formatNumber(Number(value), 1)}${suffix}`);
  const statusClass = core.status?.className || ((status = '') => status.toLowerCase().includes('current') ? 'current' : status.toLowerCase().includes('partial') ? 'partial' : status.toLowerCase().includes('stale') ? 'stale' : 'pending');
  const directionClass""",
        'free data adapter header',
    )
    text = sub_once(
        text,
        r"  function showView\(view, updateHash = true\) \{.*?\n  \}\n\n  function statusClass\(status = ''\) \{.*?\n  \}",
        """  function showView(view, updateHash = true) {
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
  }""",
        'free data view/status adapters',
    )
    text = text.replace("typeof fallback === 'undefined' || !Array.isArray(fallback.assetBiases)", "!Array.isArray(legacyResearch.assetBiases)")
    text = text.replace('fallback.assetBiases', 'legacyResearch.assetBiases')
    text = sub_once(
        text,
        r"  function initialiseRoutes\(\) \{.*?\n  \}\n\n  function initialise",
        """  function initialiseRoutes() {
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

  function initialise""",
        'free data route registration',
    )
    write(path, text)


def migrate_scenario() -> None:
    path = SITE / "scenario-ui.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const assets = window.scenarioAssets.*?  const regimeMeaning = .*?;",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const assets = core.adapters?.scenarios() || window.scenarioAssets || {};
  const research = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : {});
  let selected = Object.keys(assets)[0] || '';
  let renderedWidgetFor = '';
  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('\\\"','&quot;').replaceAll(\"'\",'&#039;'));
  const regimeMeaning = () => research.regime?.meaning || 'Use the latest regime state when interpreting the target.';""",
        'scenario adapter header',
    )
    text = sub_once(
        text,
        r"  function showView\(updateHash = true\) \{.*?\n  \}\n\n  function renderChart",
        """  function showView(updateHash = true) {
    if (updateHash && router) {
      router.navigate('scenarios', { replace: true });
      return;
    }
    if (!views?.activate('scenarios')) {
      document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
      $('view-scenarios')?.classList.add('active');
      document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === 'scenarios'));
      $('sidebar')?.classList.remove('open');
      $('overlay')?.classList.remove('show');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    if (updateHash && !router) history.replaceState(null, '', '#scenarios');
    setTimeout(renderChart, 0);
  }

  function renderChart""",
        'scenario view adapter',
    )
    text = replace_once(
        text,
        "    const route = () => { if (location.hash === '#scenarios') showView(false); };\n    window.addEventListener('hashchange', route);\n    route();",
        "    if (router) router.register('scenarios', () => showView(false));\n    else {\n      const route = () => { if (location.hash === '#scenarios') showView(false); };\n      window.addEventListener('hashchange', route);\n      route();\n    }",
        'scenario route registration',
    )
    write(path, text)


def migrate_energy() -> None:
    path = SITE / "energy-data-ui.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const marketData = window.freeMarketData.*?  const summary = \(row\) => row\n    \? .*?;",
        """  const core = window.MarketBriefCore || {};
  const router = core.router;
  const marketData = core.adapters?.official() || window.freeMarketData || { cot: [] };
  const research = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : {});
  const $ = (id) => document.getElementById(id);
  const cot = (id) => (marketData.cot || []).find((row) => row.id === id);
  const signed = core.format?.signed || ((value) => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : `${Number(value) > 0 ? '+' : ''}${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`);
  const percentile = (row) => row?.netPercentile5y === null || row?.netPercentile5y === undefined ? 'percentile unavailable' : `${Number(row.netPercentile5y).toFixed(1)}th percentile`;
  const summary = (row) => row
    ? `${row.crowding}; net ${signed(row.net, '', 0)}; ${percentile(row)}; report ${row.reportDate}`
    : 'No verified current benchmark contract is mapped. Older or similarly named contracts are excluded.';""",
        'energy adapter header',
    )
    text = text.replace("typeof fallback === 'undefined' || !Array.isArray(fallback.products)", "!Array.isArray(research.products)")
    text = text.replace("typeof fallback === 'undefined' || !Array.isArray(fallback.assetBiases)", "!Array.isArray(research.assetBiases)")
    text = text.replace('fallback.products', 'research.products').replace('fallback.assetBiases', 'research.assetBiases')
    text = replace_once(
        text,
        "    window.addEventListener('hashchange', () => requestAnimationFrame(() => requestAnimationFrame(refreshEnergyDetail)));",
        "    if (router) router.subscribe(() => requestAnimationFrame(() => requestAnimationFrame(refreshEnergyDetail)));\n    else window.addEventListener('hashchange', () => requestAnimationFrame(() => requestAnimationFrame(refreshEnergyDetail)));",
        'energy route subscription',
    )
    write(path, text)


def migrate_cot_chart() -> None:
    path = SITE / "cot-chart.js"
    text = path.read_text(encoding="utf-8")
    text = sub_once(
        text,
        r"  const data = window.freeMarketData.*?  const compact = .*?;",
        """  const core = window.MarketBriefCore || {};
  const data = core.adapters?.official() || window.freeMarketData || { cot: [] };
  const rows = Array.isArray(data.cot) ? data.cot : [];
  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\\\"', '&quot;').replaceAll(\"'\", '&#039;'));
  const number = (value) => core.format?.formatNumber ? core.format.formatNumber(value || 0, 0) : Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const signed = (value) => core.format?.signed ? core.format.signed(value, '', 0) : `${Number(value) > 0 ? '+' : ''}${number(value)}`;
  const compact = (value) => core.format?.compact ? core.format.compact(value || 0, 1) : new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(value || 0));""",
        'cot chart adapter header',
    )
    write(path, text)


def migrate_quiver() -> None:
    path = SITE / "quiver-patterns.js"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  if (typeof fallback === 'undefined' || !fallback.trackers) return;\n\n  const data = fallback;",
        "  const core = window.MarketBriefCore || {};\n  const data = core.adapters?.research() || (typeof fallback !== 'undefined' ? fallback : null);\n  if (!data?.trackers) return;",
        'quiver research adapter',
    )
    write(path, text)


def migrate_shell() -> None:
    path = SITE / "shell.js"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "  'use strict';\n\n  const routeMeta", "  'use strict';\n\n  const core = window.MarketBriefCore || {};\n  const router = core.router;\n\n  const routeMeta", 'shell router header')
    text = sub_once(
        text,
        r"  function goToRoute\(route\) \{.*?\n  \}",
        """  function goToRoute(route) {
    closeMore({ restoreFocus: false });
    if (router) router.navigate(route, { replace: true });
    else {
      const desktopButton = document.querySelector(`#nav button[data-view="${CSS.escape(route)}"]`);
      if (desktopButton) desktopButton.click();
      else window.location.hash = route;
    }
    requestAnimationFrame(() => syncNavigation());
  }""",
        'shell router navigation',
    )
    text = replace_once(
        text,
        "  window.addEventListener('hashchange', () => requestAnimationFrame(() => syncNavigation()));",
        "  if (router) router.subscribe(() => requestAnimationFrame(() => syncNavigation()));\n  else window.addEventListener('hashchange', () => requestAnimationFrame(() => syncNavigation()));",
        'shell route subscription',
    )
    text = replace_once(
        text,
        "  setMenuState(Boolean(sidebar?.classList.contains('open')));\n  syncNavigation();",
        "  setMenuState(Boolean(sidebar?.classList.contains('open')));\n  if (router) router.start(window.__marketInitialHash || window.location.hash || '#home');\n  else syncNavigation();",
        'shell router start',
    )
    write(path, text)


def main() -> int:
    migrate_index()
    migrate_app()
    migrate_intelligence()
    migrate_command()
    migrate_free_data()
    migrate_scenario()
    migrate_energy()
    migrate_cot_chart()
    migrate_quiver()
    migrate_shell()
    print('Applied BR-05 core adapters and shared router to existing renderers')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
