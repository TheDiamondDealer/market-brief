(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  // --- Week view (#week) - PR-3 Task 3, spec S5.3 ----------------------------
  // The same board grammar as the home Pressure Board (Task 2), windowed to the
  // trailing 7 days, plus a day-by-day AI-tagged digest, this week's COT shifts,
  // crowd swings and the week ahead. #view-week + the 'week' nav button already
  // exist in index.html - a LEGACY static "Week ahead" recap wired up by
  // app.js's registerCoreRoutes() (router.register('week', () =>
  // setView('week', false))), populated once from site/data.js's static
  // fallback. register() below reuses the existing host node and re-registers
  // 'week' (Map.set semantics in core/router.js overwrite the earlier legacy
  // handler) - the exact same supersede-the-legacy-route mechanism
  // command-page.js already used to replace the old 'today' view with the
  // Pressure Board home page.
  function ensureHost() {
    let node = document.getElementById('view-week');
    if (node) return node;
    const content = document.querySelector('main .content') || document.querySelector('main') || document.body;
    node = document.createElement('section');
    node.id = 'view-week';
    node.className = 'view';
    node.dataset.dynamicView = 'week';
    const footer = content.querySelector('.footer');
    if (footer) content.insertBefore(node, footer); else content.appendChild(node);
    return node;
  }

  function activate() {
    ensureHost();
    if (views?.activate('week', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-week'));
  }

  function directionGlyph(value) { return value === 'up' ? '↑' : value === 'down' ? '↓' : value === 'mixed' ? '↕' : '?'; }

  // --- Shared trailing-7d engine call (feeds sections 1, 3 and 4) ------------
  // One windowed collectDeterministicSignals() call per render(), computed once
  // and passed to every section that reads signals - keeps a single "since"
  // floor consistent across the whole page instead of three separate calls.
  const NET_LABEL = { up: '↑ upward pressure', down: '↓ downward pressure', contested: 'CONTESTED', quiet: 'QUIET' };
  const FAMILY_ORDER = ['Energy', 'Metals', 'Softs/Ags', 'Rates/FX', 'Indices', 'Themes'];

  function computeSince() {
    return new Date(Date.now() - 7*24*3600*1000).toISOString().slice(0,10);
  }

  function collectWeekBuckets(since) {
    const engine = core.impactEngine;
    const boardAssets = Array.isArray(window.marketAssetBoard?.assets) ? window.marketAssetBoard.assets : [];
    if (!engine?.collectDeterministicSignals || !boardAssets.length) return null;
    try {
      return engine.collectDeterministicSignals({
        freeData: window.freeMarketData,
        crowdData: window.crowdExpectationsData,   // NOTE: real global is crowdExpectationsData
        equityData: window.equityMarketData,
      }, { since }) || {};
    } catch (error) {
      return null;
    }
  }

  function flattenSignals(buckets) {
    if (!buckets) return [];
    return Object.values(buckets).flatMap((bucket) => Array.isArray(bucket?.signals) ? bucket.signals : []);
  }

  // --- Section 1: This week's pressure board ---------------------------------
  // Identical row grammar to the home board (command-page.js's pressureRow) -
  // same family grouping, same columns, same QUIET-dims-but-never-hides rule -
  // just windowed to the trailing 7 days via collectWeekBuckets()'s `since`.
  function priceMove(asset) {
    const etfIds = Array.isArray(asset?.etfIds) ? asset.etfIds : [];
    const watchlist = Array.isArray(window.equityMarketData?.watchlist) ? window.equityMarketData.watchlist : [];
    for (const etfId of etfIds) {
      const row = watchlist.find((entry) => entry?.id === etfId);
      const change = Number(row?.percentChange);
      if (row && row.status === 'current' && Number.isFinite(change)) {
        return `${change > 0 ? '+' : ''}${change.toFixed(2)}% (${row.symbol || etfId.toUpperCase()})`;
      }
    }
    return '—';
  }

  function weekPressureRow(asset, bucket) {
    const safeBucket = bucket || { net: 'quiet', counts: { up: 0, down: 0, mixed: 0 }, signals: [] };
    const netKey = ['up', 'down', 'contested', 'quiet'].includes(safeBucket.net) ? safeBucket.net : 'quiet';
    const counts = safeBucket.counts || { up: 0, down: 0, mixed: 0 };
    const strongest = (safeBucket.signals || [])[0] || null;
    const driverText = strongest ? (strongest.label || strongest.detail || '—') : '—';
    // QUIET rows still render (dimmed via .net-quiet), never hidden - every board
    // asset produces a row regardless of whether the trailing-7d window found signals.
    return `<a class="pressure-row net-${netKey}" href="#asset/${encodeURIComponent(asset.id)}">
      <span class="pressure-row-asset">${escapeHtml(asset.label || asset.id)}</span>
      <span class="pressure-row-net">${NET_LABEL[netKey]}</span>
      <span class="pressure-row-counts">${counts.up}↑ ${counts.down}↓ ${counts.mixed}↔</span>
      <span class="pressure-row-price">${escapeHtml(priceMove(asset))}</span>
      <span class="pressure-row-driver">${escapeHtml(driverText)}</span>
    </a>`;
  }

  function weekPressureBoardUnavailable() {
    return `<section class="pressure-board week-board command-panel" aria-labelledby="weekBoardTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Trailing 7 days</span><h3 id="weekBoardTitle">This week's pressure board</h3></div></div>
      <div class="command-empty">Week pressure board unavailable — impact engine not loaded.</div>
    </section>`;
  }

  function weekPressureBoard(buckets) {
    const boardAssets = Array.isArray(window.marketAssetBoard?.assets) ? window.marketAssetBoard.assets : [];
    if (!buckets || !boardAssets.length) return weekPressureBoardUnavailable();
    const groups = new Map();
    boardAssets.forEach((asset) => {
      const family = asset.family || 'Other';
      if (!groups.has(family)) groups.set(family, []);
      groups.get(family).push(asset);
    });
    const orderedFamilies = [...FAMILY_ORDER.filter((name) => groups.has(name)), ...[...groups.keys()].filter((name) => !FAMILY_ORDER.includes(name))];
    const groupsMarkup = orderedFamilies.map((family) => `<div class="pressure-family"><span class="pressure-family-label">${escapeHtml(family)}</span><div class="pressure-rows">${groups.get(family).map((asset) => weekPressureRow(asset, buckets[asset.id])).join('')}</div></div>`).join('');
    return `<section class="pressure-board week-board command-panel" aria-labelledby="weekBoardTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Trailing 7 days</span><h3 id="weekBoardTitle">This week's pressure board</h3></div><span>${boardAssets.length} assets · net pressure from observed signals, last 7 days</span></div>
      ${groupsMarkup}
    </section>`;
  }

  // --- Section 2: Day-by-day digest (AI ledger) ------------------------------
  // Guarded fetch mirrors gdelt-page.js's loadImpactTags() / asset-page.js's
  // loadImpactTags() - a missing/failed data/impact-tags.json must degrade to
  // the honest empty state below, never crash the page. Render happens first
  // with whatever is cached (nothing, on first load); patchDayDigest() below
  // replaces just #weekDayDigestMount once the fetch resolves (mirrors
  // command-page.js's patchTopDrivers()).
  let weekLedger = null;
  let weekLedgerFetchStarted = false;
  const CONFIDENCE_RANK = { high: 3, medium: 2, low: 1 };

  async function loadWeekLedger() {
    if (weekLedgerFetchStarted) return;
    weekLedgerFetchStarted = true;
    try {
      const response = await fetch('data/impact-tags.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      weekLedger = await response.json();
    } catch (error) {
      weekLedger = null;
    }
    patchDayDigest();
  }

  function formatDayLabel(day) {
    const parsed = new Date(`${day}T00:00:00Z`);
    if (Number.isNaN(parsed.getTime())) return day;
    // Format in UTC against a UTC-midnight instant so the displayed day always
    // matches the parsed calendar day regardless of the viewer's local timezone.
    return new Intl.DateTimeFormat('en-AU', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' }).format(parsed);
  }

  function dayBuckets(since) {
    const items = Array.isArray(weekLedger?.items) ? weekLedger.items : [];
    const eligible = items.filter((item) => item?.tagState === 'tagged' && Array.isArray(item.tags) && item.tags.length && typeof item.seenAt === 'string' && item.seenAt.length >= 10);
    const byDay = new Map();
    eligible.forEach((item) => {
      const day = item.seenAt.slice(0, 10);
      if (day < since) return; // outside the trailing-7d window - same honest exclusion the engine applies to its own signals
      if (!byDay.has(day)) byDay.set(day, []);
      byDay.get(day).push(item);
    });
    return [...byDay.keys()].sort((a, b) => b.localeCompare(a)).map((day) => {
      const ranked = byDay.get(day).map((item) => ({
        item,
        tagCount: item.tags.length,
        maxConfidence: item.tags.reduce((max, tag) => Math.max(max, CONFIDENCE_RANK[tag.confidence] || 0), 0),
      }));
      ranked.sort((a, b) => (b.tagCount - a.tagCount) || (b.maxConfidence - a.maxConfidence));
      return { day, items: ranked.slice(0, 4).map((entry) => entry.item) };
    });
  }

  function dayHeadline(item) {
    const chips = core.impactChips?.chipStrip?.((item.tags || []).map((tag) => ({
      assetId: tag.assetId,
      direction: tag.direction,
      tier: 'ai',
      confidence: tag.confidence,
      source: 'ai',
      label: 'AI-tagged',
      detail: tag.mechanism,
      at: item.seenAt || null,
      href: '',
    }))) || '';
    const link = item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : '';
    return `<article class="week-day-headline"><h4>${escapeHtml(item.headline || 'Headline unavailable')}</h4>${chips}<div class="week-day-meta"><span>${escapeHtml(item.domain || 'Source unavailable')}</span>${link}</div></article>`;
  }

  function dayCard(entry) {
    const items = entry.items;
    return `<div class="week-day-card"><header><h4>${escapeHtml(formatDayLabel(entry.day))}</h4><span>${items.length} headline${items.length === 1 ? '' : 's'}</span></header>${items.map(dayHeadline).join('')}</div>`;
  }

  function dayDigestInner(since) {
    const days = dayBuckets(since);
    if (!days.length) return '<div class="command-empty">No AI-tagged headline landed in the trailing 7-day window (ledger empty, awaiting the next tagging run, or add ANTHROPIC_API_KEY).</div>';
    return `<div class="week-day-grid">${days.map(dayCard).join('')}</div>`;
  }

  function dayDigest(since) {
    return `<section class="command-panel week-day-digest" aria-labelledby="weekDayDigestTitle">
      <div class="command-section-heading"><div><span class="command-kicker">AI-tagged, by day</span><h3 id="weekDayDigestTitle">Day-by-day digest</h3></div><a href="#news">Open Impact Feed</a></div>
      <div id="weekDayDigestMount">${dayDigestInner(since)}</div>
    </section>`;
  }

  function patchDayDigest() {
    const mount = document.getElementById('weekDayDigestMount');
    if (!mount) return;
    mount.innerHTML = dayDigestInner(computeSince());
  }

  // --- Sections 3 & 4 share one row shape: named asset + direction + detail,
  // linking into the dossier (spec S5.3 sections 3/4). --------------------
  function signalRow(signal) {
    const asset = core.impactEngine?.assetById?.(signal.assetId);
    const label = asset?.label || signal.assetId;
    const direction = ['up', 'down', 'mixed'].includes(signal.direction) ? signal.direction : 'mixed';
    return `<a class="week-signal-row" href="#asset/${encodeURIComponent(signal.assetId)}">
      <div class="week-signal-row-head"><strong>${escapeHtml(label)}</strong><span class="week-signal-direction ${direction}">${directionGlyph(direction)} ${escapeHtml(direction)}</span></div>
      <p>${escapeHtml(signal.detail || 'No detail supplied.')}</p>
    </a>`;
  }

  // --- Section 3: This week's COT shifts --------------------------------------
  // COT prints Friday, so a trailing-7d window always spans the latest report -
  // featured as its own block (filtered from the same collected result used by
  // section 1) rather than folded into the generic asset rows.
  function cotShifts(buckets) {
    const signals = flattenSignals(buckets).filter((signal) => signal.source === 'cot');
    return `<section class="command-panel" aria-labelledby="weekCotTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Positioning, last 7 days</span><h3 id="weekCotTitle">This week's COT shifts</h3></div><a href="#cot">Open COT</a></div>
      ${signals.length ? `<div class="week-signal-list">${signals.map(signalRow).join('')}</div>` : '<div class="command-empty">No COT-source position shift landed in the trailing 7 days.</div>'}
    </section>`;
  }

  // --- Section 4: Crowd swings of the week ------------------------------------
  // deriveCrowdSignals() doesn't carry the raw point-swing as its own field,
  // only formatted into `detail` text ("moved X.Xpts over 7 days"); parse that
  // back out for "largest first" ordering rather than re-deriving the engine's
  // own business logic here. A non-matching detail (engine text ever changes)
  // sorts to the back but still renders - never dropped.
  function crowdSwingMagnitude(signal) {
    const match = /moved\s+([\d.]+)pts/i.exec(signal.detail || '');
    return match ? Number(match[1]) : 0;
  }

  function crowdSwings(buckets) {
    const signals = flattenSignals(buckets)
      .filter((signal) => signal.source === 'crowd')
      .sort((a, b) => crowdSwingMagnitude(b) - crowdSwingMagnitude(a));
    return `<section class="command-panel" aria-labelledby="weekCrowdTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Attention swings ≥5pt, last 7 days</span><h3 id="weekCrowdTitle">Crowd swings of the week</h3></div><a href="#crowd-expectations">Open Crowd Expectations</a></div>
      ${signals.length ? `<div class="week-signal-list">${signals.map(signalRow).join('')}</div>` : '<div class="command-empty">No prediction-market swing of 5 points or more landed in the trailing 7 days.</div>'}
    </section>`;
  }

  // --- Section 5: Week ahead ---------------------------------------------------
  // Real global is window.marketCalendarData / core.calendar.get() (NOT
  // window.calendarData) - mirrors command-page.js's watchpointsToday(), widened
  // from "next 3" to the full next-7-day horizon. If the calendar dataset isn't
  // loaded yet (module load race - same accepted class of risk as Task 2's
  // Watchpoints), this degrades to the honest note below, never a crash.
  function upcomingWeekEvents(limit = 10) {
    const source = core.calendar?.get?.() || window.marketCalendarData || null;
    const events = Array.isArray(source?.events) ? source.events : null;
    if (!events) return null;
    const now = Date.now();
    const horizon = now + 7*24*3600*1000;
    return events
      .filter((event) => {
        if (event?.state !== 'upcoming' || typeof event.scheduledAt !== 'string' || !event.scheduledAt) return false;
        const at = Date.parse(event.scheduledAt);
        return Number.isFinite(at) && at >= now && at <= horizon;
      })
      .sort((a, b) => Date.parse(a.scheduledAt) - Date.parse(b.scheduledAt))
      .slice(0, limit);
  }

  // Standing invalidation triggers, if readily available - reuses the same
  // research.triggers adapter command-page.js's triggerCards() already reads.
  function standingTriggers() {
    const research = core.adapters?.research?.() || {};
    const active = (research.triggers || []).filter((item) => ['warning', 'triggered'].includes(item.status)).slice(0, 6);
    return active.length ? active.map((item) => `<article><div><strong>${escapeHtml(item.asset)}</strong><span>${escapeHtml(item.current || 'Current reading unavailable')}</span></div><span class="data-state ${item.status === 'triggered' ? 'stale' : 'partial'}">${escapeHtml(item.status)}</span><p><strong>Trigger:</strong> ${escapeHtml(item.trigger || 'Not specified')}</p><p><strong>Confirmation:</strong> ${escapeHtml(item.confirmation || 'Not specified')}</p></article>`).join('') : '<div class="command-empty">No warning or triggered research condition is currently listed.</div>';
  }

  function weekAhead() {
    let upcoming = null;
    try {
      upcoming = upcomingWeekEvents(10);
    } catch (error) {
      upcoming = null;
    }
    const calendarMarkup = upcoming === null
      ? '<p class="watchpoints-calendar-note">Calendar releases shown on the Calendar page.</p>'
      : (upcoming.length
        ? `<div class="watchpoints-calendar">${upcoming.map((event) => `<article><strong>${escapeHtml(event.name || 'Scheduled release')}</strong><span>${escapeHtml(event.scheduledLabel || 'Time unavailable')}</span></article>`).join('')}</div>`
        : '<div class="command-empty">No scheduled release is currently listed for the next 7 days.</div>');
    return `<section class="command-panel" aria-labelledby="weekAheadTitle">
      <div class="command-section-heading"><div><span class="command-kicker">Next 7 days</span><h3 id="weekAheadTitle">Week ahead</h3></div><a href="#calendar">Open Calendar</a></div>
      <div class="watchpoints-grid">
        <div class="watchpoints-column"><span class="command-daily-label">Scheduled releases</span>${calendarMarkup}</div>
        <div class="watchpoints-column"><span class="command-daily-label">Standing invalidation triggers</span><div class="command-trigger-list">${standingTriggers()}</div></div>
      </div>
    </section>`;
  }

  // --- Render -------------------------------------------------------------------
  function render() {
    const root = ensureHost();
    if (!root) return;
    const since = computeSince();
    const buckets = collectWeekBuckets(since);
    root.dataset.weekRemodel = 'pr3-task3';
    root.innerHTML = `<div class="week-page">
      <header class="command-hero"><div><span class="command-kicker">Weekly recap and outlook</span><h2>Week ahead</h2><p class="week-hero-note">The same board grammar over the trailing 7 days, plus what happened day by day, this week's positioning and attention shifts, and what the next 7 days test.</p></div><div class="command-hero-meta"><span class="data-state current">Trailing 7 days</span><strong>${escapeHtml(since)} → today</strong><small>Melbourne time</small></div></header>
      ${weekPressureBoard(buckets)}
      ${dayDigest(since)}
      ${cotShifts(buckets)}
      ${crowdSwings(buckets)}
      ${weekAhead()}
    </div>`;
  }

  function show() { activate(); render(); }
  function register() {
    if (!router || register.done) return;
    register.done = true;
    ensureHost();
    router.register('week', show);
    const current = router.current?.();
    if (current?.path === 'week') router.dispatch('#week', { source: 'week-ready' });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', register, { once: true });
  else register();
  window.addEventListener('load', register, { once: true });
  loadWeekLedger();
})();
