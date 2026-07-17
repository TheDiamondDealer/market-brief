(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const router = core.router;
  const views = core.adapters?.views;
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  const state = { lifecycle: 'all', expandedId: null };

  function dataset() { return core.calendar?.get?.() || window.marketCalendarData || { events: [], timezone: 'Australia/Melbourne' }; }
  function host() { return document.getElementById('view-events'); }
  function activate() {
    if (views?.activate('events', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-events'));
  }
  function label(value = '') { return String(value).split('-').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' '); }
  function statusClass(value = '') { return value === 'reaction-complete' || value === 'released' || value === 'sourced' || value === 'observed' ? 'current' : value === 'not-sourced' || value === 'needs-verification' ? 'stale' : 'pending'; }
  function visibleEvents() { return dataset().events.filter((event) => state.lifecycle === 'all' || event.state === state.lifecycle); }

  function valueCard(title, record) {
    return `<article><span>${escapeHtml(title)}</span><strong>${escapeHtml(record.value ?? 'Unavailable')}</strong><small class="data-state ${statusClass(record.status)}">${escapeHtml(label(record.status))}</small>${record.source ? `<em>Source: ${escapeHtml(record.source)}</em>` : '<em>No approved source attached</em>'}</article>`;
  }

  function reactionTimeline(event) {
    return `<div class="calendar-reaction-grid">${Object.values(event.reactions).map((reaction, index) => `<article class="${escapeHtml(reaction.status)}"><span>${index + 1}</span><div><strong>${escapeHtml(reaction.label)}</strong><p>${escapeHtml(reaction.value)}</p><small>${reaction.observedAt ? `Observed ${escapeHtml(reaction.observedAt)}` : 'Observation pending'}</small></div></article>`).join('')}</div>`;
  }

  function watchChips(event) {
    const engine = core.impactEngine;
    const chips = core.impactChips;
    if (!engine || !chips) return '';
    const mapped = [];
    const leftover = [];
    const seen = new Set();
    (event.assets || []).forEach((label) => {
      const asset = engine.assetByCalendarAlias(label);
      if (!asset) {
        leftover.push(label);
        return;
      }
      // Dedupe by board asset: multiple calendar aliases can resolve to the
      // same asset (e.g. "Bonds" and "US 10Y" -> us10y). Chart it once; a
      // repeat alias is neither a second chip nor "Also relevant:" leftover.
      if (seen.has(asset.id)) return;
      seen.add(asset.id);
      mapped.push({
        assetId: asset.id,
        direction: 'watch',
        tier: 'observed',
        source: 'calendar',
        label: 'Scheduled release',
        detail: `${event.name || 'This release'} is scheduled; direction is unknowable before the print.`,
        at: event.scheduledAt || null,
        status: 'current',
        href: '',
      });
    });
    // All labels unmappable: return '' so the caller's unchanged "Relevant assets:" copy
    // renders instead — "Also relevant:" must only ever appear below actual chips.
    if (!mapped.length) return '';
    const chipHtml = chips.chipStrip(mapped);
    const textHtml = leftover.length ? `<span class="calendar-leftover-assets">Also relevant: ${leftover.map((l) => escapeHtml(l)).join(' · ')}</span>` : '';
    return chipHtml + textHtml;
  }

  function eventCard(event) {
    const expanded = state.expandedId === event.id;
    return `<article class="calendar-event-card" id="calendar-${escapeHtml(event.id)}">
      <header><div><span class="data-state ${statusClass(event.state)}">${escapeHtml(label(event.state))}</span><span>${escapeHtml(event.importance)}</span></div><span class="data-state ${statusClass(event.timeStatus)}">${escapeHtml(label(event.timeStatus))}</span></header>
      <div class="calendar-event-main"><div><span class="calendar-kicker">${escapeHtml(event.scheduledLabel)}</span><h3>${escapeHtml(event.name)}</h3><p>${event.assets.length ? watchChips(event) || `Relevant assets: ${escapeHtml(event.assets.join(' · '))}` : 'Relevant assets were not explicitly named in the source record.'}</p></div><button type="button" data-calendar-expand="${escapeHtml(event.id)}" aria-expanded="${expanded}">${expanded ? 'Hide workflow' : 'Open workflow'}</button></div>
      <div class="calendar-outcomes">${valueCard('Previous', event.previous)}${valueCard('Consensus', event.consensus)}${valueCard('Actual', event.actual)}</div>
      ${expanded ? `<div class="calendar-expanded"><section><div class="calendar-section-heading"><div><span class="calendar-kicker">Pre-event scenarios</span><h4>What the market may test</h4></div><span>Scenario map, not a forecast</span></div><div class="calendar-scenarios">${event.scenarios.map((scenario) => `<article><strong>${escapeHtml(scenario.label)}</strong><p>${escapeHtml(scenario.interpretation)}</p></article>`).join('')}</div></section><section><div class="calendar-section-heading"><div><span class="calendar-kicker">Reaction lifecycle</span><h4>Observed without look-ahead bias</h4></div><span>${escapeHtml(event.verdict)}</span></div>${reactionTimeline(event)}</section><footer><div><strong>Official release source</strong><span>${escapeHtml(event.source.name)}</span></div>${event.source.url ? `<a href="${escapeHtml(event.source.url)}" target="_blank" rel="noopener noreferrer">Open official source ↗</a>` : '<span>Official URL not yet attached</span>'}</footer></div>` : ''}
    </article>`;
  }

  function render() {
    const root = host();
    if (!root) return;
    const data = dataset();
    const events = visibleEvents();
    const states = ['all', 'upcoming', 'released', 'reaction-complete'];
    root.dataset.calendarRemodel = 'br-15';
    root.innerHTML = `<div class="calendar-page">
      <header class="calendar-hero"><div><span class="calendar-kicker">Economic event workflow</span><h2>Calendar & Reactions</h2><p>Release times are shown in Melbourne time. Previous, consensus and actual values carry separate source states; reaction windows stay pending until they can be observed without look-ahead bias.</p></div><div class="calendar-hero-meta"><span class="data-state current">Contract v${escapeHtml(data.schemaVersion)}</span><strong>${escapeHtml(data.timezone)}</strong><small>Research updated ${escapeHtml(data.generatedAt || 'time unavailable')}</small></div></header>
      <section class="calendar-controls" aria-label="Calendar lifecycle filters"><span>Lifecycle</span><div role="group">${states.map((value) => `<button type="button" data-calendar-state="${value}" aria-pressed="${state.lifecycle === value}">${escapeHtml(value === 'all' ? 'All' : label(value))}</button>`).join('')}</div></section>
      <section><div class="calendar-section-heading"><div><span class="calendar-kicker">Scheduled releases</span><h3>Event and reaction ledger</h3></div><span>${events.length} event${events.length === 1 ? '' : 's'} shown</span></div><div class="calendar-event-list">${events.length ? events.map(eventCard).join('') : '<div class="calendar-empty">No events match the selected lifecycle.</div>'}</div></section>
      <details class="calendar-methodology"><summary>Lifecycle rules</summary><p><strong>Upcoming:</strong> no sourced actual value. <strong>Released:</strong> the actual is sourced but one or more reaction windows remain pending. <strong>Reaction complete:</strong> immediate, close, +1 day and +5 day observations are all present.</p><p>Consensus is deliberately labelled Not sourced until an approved provider is connected. An approximate release label remains “Needs verification” and does not receive an invented timestamp.</p></details>
    </div>`;
    root.querySelectorAll('[data-calendar-state]').forEach((button) => button.addEventListener('click', () => { state.lifecycle = button.dataset.calendarState; render(); }));
    root.querySelectorAll('[data-calendar-expand]').forEach((button) => button.addEventListener('click', () => {
      state.expandedId = state.expandedId === button.dataset.calendarExpand ? null : button.dataset.calendarExpand;
      render();
      document.getElementById(`calendar-${button.dataset.calendarExpand}`)?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }));
  }

  function show(id = null) { activate(); if (id) state.expandedId = id; render(); }
  function registerRoutes() {
    if (!router || registerRoutes.done) return;
    registerRoutes.done = true;
    router.register('events', () => show());
    router.register('calendar', () => show());
    router.registerPattern('calendar-detail', /^calendar\/([^/]+)$/, (route) => show(decodeURIComponent(route.params.id)), (match) => ({ id: match[1] }));
    const current = router.current?.();
    if (current?.path === 'events' || current?.path === 'calendar' || current?.path?.startsWith('calendar/')) router.dispatch(`#${current.path}`, { source: 'calendar-ready' });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoutes, { once: true });
  else registerRoutes();
  window.addEventListener('load', registerRoutes, { once: true });
})();
