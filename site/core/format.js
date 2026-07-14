(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const formatterCache = new Map();

  function escapeHtml(value = '') {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function finiteNumber(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function numberFormatter(maximumFractionDigits = 0, options = {}) {
    const key = JSON.stringify({ maximumFractionDigits, ...options });
    if (!formatterCache.has(key)) {
      formatterCache.set(key, new Intl.NumberFormat('en-AU', { maximumFractionDigits, ...options }));
    }
    return formatterCache.get(key);
  }

  function formatNumber(value, maximumFractionDigits = 0, options = {}) {
    const number = finiteNumber(value);
    if (number === null) return '—';
    return numberFormatter(maximumFractionDigits, options).format(number);
  }

  function signed(value, suffix = '', maximumFractionDigits = 1) {
    const number = finiteNumber(value);
    if (number === null) return '—';
    return `${number > 0 ? '+' : ''}${formatNumber(number, maximumFractionDigits)}${suffix}`;
  }

  function compact(value, maximumFractionDigits = 1) {
    const number = finiteNumber(value);
    if (number === null) return '—';
    return numberFormatter(maximumFractionDigits, { notation: 'compact' }).format(number);
  }

  function percent(value, maximumFractionDigits = 1) {
    const number = finiteNumber(value);
    return number === null ? '—' : `${formatNumber(number, maximumFractionDigits)}%`;
  }

  function date(value, options = { day: '2-digit', month: 'short', year: 'numeric' }) {
    if (!value) return '—';
    const parsed = new Date(String(value).length === 10 ? `${value}T00:00:00` : value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString('en-AU', options);
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  core.format = Object.freeze({
    asArray,
    compact,
    date,
    escapeHtml,
    finiteNumber,
    formatNumber,
    percent,
    signed
  });
})();
