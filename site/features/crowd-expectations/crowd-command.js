(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  let rendering = false;

  function data() {
    return window.crowdExpectationsData || { markets: [], shocks: [], collection: {} };
  }

  function signed(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    const numeric = Number(value);
    return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)} pts`;
  }

  function render() {
    if (rendering) return;
    const root = document.getElementById('view-home');
    const commandPage = root?.querySelector('.command-page');
    if (!commandPage) return;
    rendering = true;
    try {
      let panel = commandPage.querySelector('[data-crowd-command-panel]');
      if (!panel) {
        panel = document.createElement('section');
        panel.className = 'command-panel crowd-command-panel';
        panel.dataset.crowdCommandPanel = 'true';
        const anchor = commandPage.querySelector('.command-priority');
        if (anchor) anchor.insertAdjacentElement('afterend', panel);
        else commandPage.prepend(panel);
      }

      const current = data();
      const candidates = (current.shocks?.length ? current.shocks : [...(current.markets || [])]
        .filter((market) => market.change24hPoints !== null && market.change24hPoints !== undefined)
        .sort((a, b) => Math.abs(Number(b.change24hPoints || 0)) - Math.abs(Number(a.change24hPoints || 0)))
        .slice(0, 4));
      panel.innerHTML = `<div class="command-section-heading"><div><span class="command-kicker">Crowd expectations</span><h3>Largest probability shifts</h3></div><a href="#crowd-expectations">Open Crowd Expectations</a></div>
        <div class="crowd-command-list">${candidates.length ? candidates.map((item) => `<article>
          <div><strong>${escapeHtml(item.question)}</strong><span>${escapeHtml(Number(item.probabilityPercent || 0).toFixed(1))}% YES</span></div>
          <span class="crowd-move ${Number(item.change24hPoints) >= 0 ? 'up' : 'down'}">${escapeHtml(signed(item.change24hPoints))}</span>
          <small>Quality ${escapeHtml(item.qualityGrade || '—')} · ${(item.assets || []).slice(0, 5).map((asset) => escapeHtml(String(asset).replaceAll('-', ' '))).join(', ') || 'Assets not mapped'}</small>
        </article>`).join('') : '<div class="command-empty">No qualified crowd-probability move is available yet.</div>'}</div>`;
    } finally {
      rendering = false;
    }
  }

  const observer = new MutationObserver(() => window.setTimeout(render, 0));
  function start() {
    const root = document.getElementById('view-home');
    if (root) observer.observe(root, { childList: true, subtree: false });
    render();
  }

  window.addEventListener('marketbrief:crowd-data', render);
  window.addEventListener('hashchange', render);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
  window.addEventListener('load', render, { once: true });
})();
