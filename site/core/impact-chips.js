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
    // Default an empty href to the asset's dossier route so every board-asset chip becomes
    // navigation currency at once. Unknown assets (not on the board) keep no href - the
    // dossier route can't render them, and a <span> is the honest choice (no dead links).
    const board = window.marketAssetBoard?.assets || [];
    const isBoardAsset = board.some((entry) => entry.id === signal.assetId);
    const href = signal.href || (isBoardAsset ? `#asset/${signal.assetId}` : '');
    if (href) {
      return `<a class="${classes}" href="${escapeHtml(href)}"${title}${aria}>${body}</a>`;
    }
    return `<span class="${classes}"${title}${aria}>${body}</span>`;
  }

  function chipStrip(signals = [], options = {}) {
    // Clamp to a non-negative integer; default 8. Number(x) || 8 would turn an
    // explicit {max:0} ("render none") into 8, and negatives into surprising slice() behaviour.
    const max = Number.isInteger(options.max) && options.max >= 0 ? options.max : 8;
    const list = (Array.isArray(signals) ? signals : []).filter(Boolean).slice(0, max);
    if (!list.length) return '';
    // <span>, not <div>: callers interpolate strips inside <p>/<th>/<span>,
    // and a div start tag would auto-close an open paragraph.
    return `<span class="impact-chips">${list.map(chip).join('')}</span>`;
  }

  core.impactChips = Object.freeze({ chip, chipStrip });
})();
