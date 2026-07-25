(() => {
  'use strict';
  const core = window.MarketBriefCore || {};
  const escapeHtml = core.format?.escapeHtml || ((v = '') => String(v)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));

  const router = core.router;
  const views = core.adapters?.views;

  // Only the RBA has an official "last actual" print today (the rba-cash-rate series).
  const OFFICIAL_SERIES_BY_BANK = { rba: 'rba-cash-rate' };

  // Activate this view's <section> (mirrors command-page.js / political-page.js). The feature
  // registers its OWN route (see the tail) — app.js/free-data-ui only own their own views.
  function activate() {
    if (views?.activate?.('rate-decisions', { scroll: false })) return;
    document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === 'view-rate-decisions'));
  }

  function data() { return window.centralBankDecisionsData || { banks: [], collection: {} }; }

  function lastActual(bankId) {
    const seriesId = OFFICIAL_SERIES_BY_BANK[bankId];
    if (!seriesId) return null;
    const sources = Array.isArray(window.officialFeedsData?.sources) ? window.officialFeedsData.sources : [];
    for (const source of sources) {
      const record = (source.records || []).find((r) => r.id === seriesId);
      if (record) return record;
    }
    return null;
  }

  function sparkline(history) {
    const points = (Array.isArray(history) ? history : []).filter((p) => Number.isFinite(Number(p.probability)));
    if (points.length < 2) return '<span class="rd-spark-empty">history building…</span>';
    const w = 96, h = 24;
    const xs = (i) => (points.length === 1 ? 0 : (i / (points.length - 1)) * w);
    const ys = (p) => h - Number(p) * h;
    const d = points.map((p, i) => `${xs(i).toFixed(1)},${ys(p.probability).toFixed(1)}`).join(' ');
    return `<svg class="rd-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${d}" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>`;
  }

  function outcomeRow(outcome, modalLabel) {
    const pct = Number(outcome.probabilityPercent) || 0;
    const isModal = outcome.label === modalLabel;
    return `<div class="rd-outcome ${isModal ? 'is-modal' : ''}">
      <span class="rd-outcome-label">${escapeHtml(outcome.label)}</span>
      <span class="rd-outcome-bar"><span style="width:${Math.max(2, Math.min(100, pct))}%"></span></span>
      <span class="rd-outcome-pct">${pct.toFixed(1)}%</span>
      ${sparkline(outcome.history)}
    </div>`;
  }

  function meetingCard(meeting) {
    const dir = meeting.impliedDirection || 'hold';
    return `<article class="rd-meeting">
      <header><h4>${escapeHtml(meeting.decisionDate || 'Date unavailable')}</h4>
        <span class="rd-lean rd-lean-${escapeHtml(dir)}">${escapeHtml(dir)}</span></header>
      <div class="rd-outcomes">${(meeting.outcomes || []).map((o) => outcomeRow(o, meeting.modalOutcome)).join('')}</div>
      <footer><a href="${escapeHtml(meeting.marketUrl || 'https://polymarket.com/')}" target="_blank" rel="noopener noreferrer">View market ↗</a></footer>
    </article>`;
  }

  function bankCard(bank) {
    const actual = lastActual(bank.id);
    const actualRow = actual
      ? `<p class="rd-actual">Last actual: ${escapeHtml(String(actual.change))} ${escapeHtml(actual.unit || '')} on ${escapeHtml(actual.observedAt || '—')} <span>(official print)</span></p>`
      : '';
    const meetings = (bank.meetings || []);
    return `<section class="rd-bank">
      <div class="rd-bank-head"><span class="rd-flag" aria-hidden="true">${escapeHtml(bank.flag || '')}</span>
        <div><h3>${escapeHtml(bank.name)}</h3><span class="rd-ccy">${escapeHtml(bank.currency || '')}</span></div></div>
      ${actualRow}
      <div class="rd-meetings">${meetings.length ? meetings.map(meetingCard).join('') : '<div class="command-empty">No live decision market.</div>'}</div>
    </section>`;
  }

  function render() {
    const mount = document.getElementById('rateDecisionsMount');
    if (!mount) return;
    const feed = data();
    const banks = (feed.banks || []).filter((b) => (b.meetings || []).length);
    const badge = document.getElementById('rateDecisionsUpdated');
    if (badge) badge.textContent = feed.collection?.status === 'current'
      ? `${feed.collection.banksCovered} central banks`
      : (feed.collection?.status || 'Unavailable');
    mount.innerHTML = banks.length
      ? `<div class="rd-grid">${banks.map(bankCard).join('')}</div>
         <p class="rd-methodology">Read-only Polymarket market-implied probabilities. A probability is crowd expectation, not a forecast or trade recommendation.</p>`
      : '<div class="command-empty">No central-bank decision markets are currently available.</div>';
  }

  function show() { activate(); render(); }
  function registerRoute() {
    if (!router || registerRoute.done) return;
    registerRoute.done = true;
    router.register('rate-decisions', show);
    if (router.current?.()?.path === 'rate-decisions') router.dispatch('#rate-decisions', { source: 'rate-decisions-ready' });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', registerRoute, { once: true });
  else registerRoute();
  window.addEventListener('load', registerRoute, { once: true });
  // Repaint in place when data arrives (mount is static in index.html; harmless if not active).
  window.addEventListener('marketbrief:central-bank-decisions', render);
  window.addEventListener('marketbrief:official-feeds', render);
})();
