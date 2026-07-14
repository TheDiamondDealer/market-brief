(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const ORDER = Object.freeze({ unavailable: 0, error: 1, stale: 2, partial: 3, delayed: 4, pending: 5, current: 6 });

  function normalize(value = '') {
    const text = String(value).trim().toLowerCase();
    if (!text) return 'pending';
    if (text.includes('unavailable') || text.includes('missing')) return 'unavailable';
    if (text.includes('error') || text.includes('failed')) return 'error';
    if (text.includes('stale')) return 'stale';
    if (text.includes('partial')) return 'partial';
    if (text.includes('delay')) return 'delayed';
    if (text.includes('current') || text.includes('complete') || text.includes('automatic') || text.includes('success')) return 'current';
    return 'pending';
  }

  function className(value) {
    return normalize(value);
  }

  function label(value) {
    const normalized = normalize(value);
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
  }

  function worst(values = []) {
    return values.reduce((current, value) => {
      const normalized = normalize(value);
      return ORDER[normalized] < ORDER[current] ? normalized : current;
    }, 'current');
  }

  function isUsable(value) {
    return !['unavailable', 'error'].includes(normalize(value));
  }

  core.status = Object.freeze({ className, isUsable, label, normalize, order: ORDER, worst });
})();
