(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const data = core.adapters?.official() || window.freeMarketData || { cot: [] };
  const rows = Array.isArray(data.cot) ? data.cot : [];
  const $ = (id) => document.getElementById(id);
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('\"', '&quot;').replaceAll("'", '&#039;'));
  const number = (value) => core.format?.formatNumber ? core.format.formatNumber(value || 0, 0) : Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const signed = (value) => core.format?.signed ? core.format.signed(value, '', 0) : `${Number(value) > 0 ? '+' : ''}${number(value)}`;
  const compact = (value) => core.format?.compact ? core.format.compact(value || 0, 1) : new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(value || 0));
  let activeId = rows.find((row) => row.id === 'gold' && Array.isArray(row.history52) && row.history52.length > 1)?.id
    || rows.find((row) => Array.isArray(row.history52) && row.history52.length > 1)?.id
    || rows[0]?.id
    || '';

  function addStylesheet() {
    if (document.querySelector('link[href="cot-chart.css"]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'cot-chart.css';
    document.head.appendChild(link);
  }

  function injectStructure() {
    if ($('cotVisualSection')) return;
    const summary = $('cotSummary');
    if (!summary) return;
    const section = document.createElement('section');
    section.id = 'cotVisualSection';
    section.className = 'cot-visual-section';
    section.innerHTML = `
      <article class="card cot-chart-card">
        <div class="cot-chart-toolbar">
          <div><div class="eyebrow">52-week history</div><h3>Long versus short positioning</h3><p>Select a market to see how institutional positioning has changed through time.</p></div>
          <div class="cot-chart-tabs" id="cotChartTabs"></div>
        </div>
        <div class="cot-chart-metrics" id="cotChartMetrics"></div>
        <div class="cot-chart-legend"><span class="long"><i></i>Long contracts</span><span class="short"><i></i>Short contracts</span></div>
        <div class="cot-chart-host" id="cotChartHost"></div>
      </article>
      <div class="cot-balance-title"><h3>Current long/short balance</h3><span>Each bar is normalised within its own market; contract sizes are not comparable across markets.</span></div>
      <div class="cot-balance-grid" id="cotBalanceGrid"></div>`;
    summary.insertAdjacentElement('afterend', section);
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-AU', { month: 'short', year: '2-digit' });
  }

  function pathFor(history, key, dimensions) {
    const { left, top, plotWidth, plotHeight, maxValue } = dimensions;
    if (!history.length || maxValue <= 0) return '';
    return history.map((point, index) => {
      const x = history.length === 1 ? left : left + (index / (history.length - 1)) * plotWidth;
      const y = top + plotHeight - (Number(point[key] || 0) / maxValue) * plotHeight;
      return `${index ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  function areaFor(history, key, dimensions) {
    const path = pathFor(history, key, dimensions);
    if (!path) return '';
    const firstX = dimensions.left;
    const lastX = dimensions.left + dimensions.plotWidth;
    const baseY = dimensions.top + dimensions.plotHeight;
    return `${path} L${lastX.toFixed(1)},${baseY.toFixed(1)} L${firstX.toFixed(1)},${baseY.toFixed(1)} Z`;
  }

  function chartSvg(row) {
    const history = Array.isArray(row?.history52) ? row.history52 : [];
    if (history.length < 2) {
      return '<div class="cot-chart-empty">The current position is available, but the 52-week history will appear after the refreshed CFTC cache completes.</div>';
    }

    const width = 1000;
    const height = 330;
    const dimensions = { left: 62, right: 22, top: 18, bottom: 38 };
    dimensions.plotWidth = width - dimensions.left - dimensions.right;
    dimensions.plotHeight = height - dimensions.top - dimensions.bottom;
    dimensions.maxValue = Math.max(...history.flatMap((point) => [Number(point.long || 0), Number(point.short || 0)]), 1) * 1.08;

    const longPath = pathFor(history, 'long', dimensions);
    const shortPath = pathFor(history, 'short', dimensions);
    const longArea = areaFor(history, 'long', dimensions);
    const shortArea = areaFor(history, 'short', dimensions);
    const grid = Array.from({ length: 5 }, (_, index) => {
      const fraction = index / 4;
      const y = dimensions.top + fraction * dimensions.plotHeight;
      const label = dimensions.maxValue * (1 - fraction);
      return `<line class="cot-grid-line" x1="${dimensions.left}" y1="${y}" x2="${width - dimensions.right}" y2="${y}"></line><text class="cot-axis-text" x="${dimensions.left - 10}" y="${y + 4}" text-anchor="end">${escapeHtml(compact(label))}</text>`;
    }).join('');

    const labelIndexes = [...new Set([0, Math.floor((history.length - 1) / 3), Math.floor((history.length - 1) * 2 / 3), history.length - 1])];
    const xLabels = labelIndexes.map((index) => {
      const x = dimensions.left + (index / (history.length - 1)) * dimensions.plotWidth;
      return `<text class="cot-axis-text" x="${x}" y="${height - 12}" text-anchor="middle">${escapeHtml(formatDate(history[index].date))}</text>`;
    }).join('');

    const latest = history.at(-1);
    const latestX = dimensions.left + dimensions.plotWidth;
    const longY = dimensions.top + dimensions.plotHeight - (Number(latest.long || 0) / dimensions.maxValue) * dimensions.plotHeight;
    const shortY = dimensions.top + dimensions.plotHeight - (Number(latest.short || 0) / dimensions.maxValue) * dimensions.plotHeight;

    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(row.name)} 52-week long and short positioning chart">
      <defs>
        <linearGradient id="cotLongGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2dd4bf" stop-opacity=".22"></stop><stop offset="100%" stop-color="#2dd4bf" stop-opacity="0"></stop></linearGradient>
        <linearGradient id="cotShortGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ff6b6b" stop-opacity=".15"></stop><stop offset="100%" stop-color="#ff6b6b" stop-opacity="0"></stop></linearGradient>
      </defs>
      ${grid}
      <path class="cot-long-area" d="${longArea}"></path>
      <path class="cot-short-area" d="${shortArea}"></path>
      <path class="cot-long-line" d="${longPath}"></path>
      <path class="cot-short-line" d="${shortPath}"></path>
      <circle class="cot-latest-dot long" cx="${latestX}" cy="${longY}" r="5"></circle>
      <circle class="cot-latest-dot short" cx="${latestX}" cy="${shortY}" r="5"></circle>
      ${xLabels}
    </svg>`;
  }

  function renderTabs() {
    const host = $('cotChartTabs');
    if (!host) return;
    host.innerHTML = rows.map((row) => `<button class="${row.id === activeId ? 'active' : ''}" data-cot-chart="${escapeHtml(row.id)}">${escapeHtml(row.name)}</button>`).join('');
    host.querySelectorAll('[data-cot-chart]').forEach((button) => button.addEventListener('click', () => {
      activeId = button.dataset.cotChart;
      renderTabs();
      renderSelectedChart();
    }));
  }

  function renderSelectedChart() {
    const row = rows.find((item) => item.id === activeId) || rows[0];
    if (!row) return;
    $('cotChartMetrics').innerHTML = `
      <article class="cot-chart-metric"><span>Long</span><strong>${number(row.long)}</strong></article>
      <article class="cot-chart-metric"><span>Short</span><strong>${number(row.short)}</strong></article>
      <article class="cot-chart-metric"><span>Net</span><strong class="${Number(row.net) >= 0 ? 'number-up' : 'number-down'}">${signed(row.net)}</strong></article>
      <article class="cot-chart-metric"><span>Weekly net change</span><strong class="${Number(row.weekChange) >= 0 ? 'number-up' : 'number-down'}">${signed(row.weekChange)}</strong></article>
      <article class="cot-chart-metric"><span>5-year net percentile</span><strong>${row.netPercentile5y === null || row.netPercentile5y === undefined ? '—' : `${Number(row.netPercentile5y).toFixed(1)}%`}</strong></article>`;
    $('cotChartHost').innerHTML = chartSvg(row);
  }

  function renderBalances() {
    const host = $('cotBalanceGrid');
    if (!host) return;
    host.innerHTML = rows.map((row) => {
      const gross = Math.max(0, Number(row.long || 0)) + Math.max(0, Number(row.short || 0));
      const longShare = gross > 0 ? (Number(row.long || 0) / gross) * 100 : 50;
      const shortShare = 100 - longShare;
      return `<article class="cot-balance-card">
        <div class="cot-balance-head"><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.crowding || '')}<br>${escapeHtml(row.reportDate || '')}</span></div>
        <div class="cot-balance-bar" title="Long ${longShare.toFixed(1)}%, short ${shortShare.toFixed(1)}% of reported long-plus-short positions"><span class="long" style="width:${longShare.toFixed(2)}%"></span><span class="short" style="width:${shortShare.toFixed(2)}%"></span></div>
        <div class="cot-balance-values"><div><span>Long</span><strong>${number(row.long)}</strong></div><div><span>Short</span><strong>${number(row.short)}</strong></div><div class="${Number(row.net) >= 0 ? 'net-positive' : 'net-negative'}"><span>Net</span><strong>${signed(row.net)}</strong></div></div>
      </article>`;
    }).join('');
  }

  function initialise() {
    addStylesheet();
    injectStructure();
    renderTabs();
    renderSelectedChart();
    renderBalances();
  }

  initialise();
})();
