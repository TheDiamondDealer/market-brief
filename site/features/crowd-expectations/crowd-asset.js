(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  let rendering = false;

  const ALIASES = Object.freeze({
    gold: ['gold'],
    silver: ['silver'],
    copper: ['copper'],
    brent: ['brent'],
    wti: ['wti'],
    'gas-us': ['gas-us', 'natural-gas', 'henry-hub'],
    'gas-uk': ['gas-uk', 'lng'],
    'rare-earths': ['rare-earths', 'critical-minerals'],
    semiconductor: ['semiconductors'],
    semiconductors: ['semiconductors']
  });

  function currentAsset() {
    const match = window.location.hash.match(/^#(?:asset|product)\/([^/?#]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  function relevant(assetId) {
    const ids = new Set([assetId, ...(ALIASES[assetId] || [])]);
    return (window.crowdExpectationsData?.markets || [])
      .filter((market) => (market.assets || []).some((asset) => ids.has(asset)))
      .sort((a, b) => {
        const movement = Math.abs(Number(b.change24hPoints || 0)) - Math.abs(Number(a.change24hPoints || 0));
        return movement || Number(b.qualityScore || 0) - Number(a.qualityScore || 0);
      })
      .slice(0, 4);
  }

  function signed(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    const numeric = Number(value);
    return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)} pts`;
  }

  function render() {
    if (rendering) return;
    const assetId = currentAsset();
    const root = document.getElementById('view-product-detail');
    const workspace = root?.querySelector('.asset-workspace');
    if (!assetId || !workspace) return;
    rendering = true;
    try {
      let panel = workspace.querySelector('[data-crowd-asset-panel]');
      if (!panel) {
        panel = document.createElement('section');
        panel.className = 'asset-panel crowd-asset-panel';
        panel.dataset.crowdAssetPanel = 'true';
        const footer = workspace.querySelector('.asset-provenance');
        if (footer) workspace.insertBefore(panel, footer);
        else workspace.appendChild(panel);
      }
      const rows = relevant(assetId);
      panel.innerHTML = `<div class="asset-section-heading"><div><span class="asset-kicker">Crowd expectations</span><h3>Relevant event probabilities</h3></div><a href="#crowd-expectations">Open all markets</a></div>
        <p class="asset-panel-summary">Read-only market-implied probabilities. They are context—not a directional signal by themselves.</p>
        <div class="crowd-asset-list">${rows.length ? rows.map((market) => `<article>
          <header><strong>${escapeHtml(Number(market.probabilityPercent || 0).toFixed(1))}% YES</strong><span class="crowd-move ${Number(market.change24hPoints || 0) >= 0 ? 'up' : 'down'}">${escapeHtml(signed(market.change24hPoints))}</span></header>
          <p>${escapeHtml(market.question)}</p>
          <small>Quality ${escapeHtml(market.qualityGrade)} · ${escapeHtml(market.category)}</small>
        </article>`).join('') : '<div class="asset-empty">No relevant crowd market is currently mapped to this asset.</div>'}</div>`;
    } finally {
      rendering = false;
    }
  }

  const observer = new MutationObserver(() => window.setTimeout(render, 0));
  function start() {
    const root = document.getElementById('view-product-detail');
    if (root) observer.observe(root, { childList: true, subtree: false });
    render();
  }

  window.addEventListener('marketbrief:crowd-data', render);
  window.addEventListener('hashchange', render);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
  window.addEventListener('load', render, { once: true });
})();
