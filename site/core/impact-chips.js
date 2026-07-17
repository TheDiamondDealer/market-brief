(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};

  const DIRECTIONS = ['up', 'down', 'mixed', 'watch', 'activity'];
  const TIERS = ['observed', 'verified', 'ai'];
  const ARROWS = { up: '↑', down: '↓', mixed: '↔', watch: '◔', activity: '•' };
  const DIRECTION_WORD = { up: 'upward pressure', down: 'downward pressure', mixed: 'attention signal', watch: 'watchpoint', activity: 'activity' };

  const escapeHtml = (value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  function assetLabel(assetId) {
    const asset = (window.marketAssetBoard?.assets || []).find((entry) => entry.id === assetId);
    return asset ? asset.label : String(assetId || 'Unknown asset');
  }

  function chip(signal = {}) {
    const direction = DIRECTIONS.includes(signal.direction) ? signal.direction : 'mixed';
    const tier = TIERS.includes(signal.tier) ? signal.tier : 'observed';
    const dim = signal.confidence === 'low' ? ' conf-low' : '';
    const label = assetLabel(signal.assetId);
    const classes = `impact-chip ${direction} tier-${tier}${dim}`;
    const title = signal.detail ? ` title="${escapeHtml(signal.detail)}"` : '';
    const aria = ` aria-label="${escapeHtml(`${label}: ${DIRECTION_WORD[direction]}`)}"`;
    const body = `<span class="impact-chip-arrow" aria-hidden="true">${ARROWS[direction]}</span>${escapeHtml(label)}`;
    if (signal.href) {
      return `<a class="${classes}" href="${escapeHtml(signal.href)}"${title}${aria}>${body}</a>`;
    }
    return `<span class="${classes}"${title}${aria}>${body}</span>`;
  }

  function chipStrip(signals = [], options = {}) {
    const max = Number(options.max) || 8;
    const list = (Array.isArray(signals) ? signals : []).filter(Boolean).slice(0, max);
    if (!list.length) return '';
    // <span>, not <div>: callers interpolate strips inside <p>/<th>/<span>,
    // and a div start tag would auto-close an open paragraph.
    return `<span class="impact-chips">${list.map(chip).join('')}</span>`;
  }

  core.impactChips = Object.freeze({ chip, chipStrip });
})();
