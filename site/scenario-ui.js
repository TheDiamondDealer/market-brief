(() => {
  'use strict';
  const assets = window.scenarioAssets || {};
  let selected = Object.keys(assets)[0] || '';
  let renderedWidgetFor = '';
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value = '') => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const regimeMeaning = () => typeof fallback !== 'undefined' && fallback.regime?.meaning ? fallback.regime.meaning : 'Use the latest regime state when interpreting the target.';

  function showView(updateHash = true) {
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    $('view-scenarios')?.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === 'scenarios'));
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
    if (updateHash) history.replaceState(null, '', '#scenarios');
    setTimeout(renderChart, 0);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderChart() {
    const host = $('scenarioChart');
    const asset = assets[selected];
    if (!host || !asset || renderedWidgetFor === selected) return;
    renderedWidgetFor = selected;
    const chartHeight = window.innerWidth <= 780 ? 360 : 440;
    host.style.height = `${chartHeight}px`;
    host.style.minHeight = `${chartHeight}px`;
    host.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.textContent = JSON.stringify({ autosize:false, width:'100%', height:chartHeight, symbol:asset.symbol, interval:'60', timezone:'Australia/Sydney', theme:'dark', style:'1', locale:'en', backgroundColor:'rgba(7, 16, 20, 1)', gridColor:'rgba(33, 52, 61, 0.45)', hide_top_toolbar:false, allow_symbol_change:true, save_image:false, calendar:false, support_host:'https://www.tradingview.com' });
    host.appendChild(script);
  }

  function renderControls() {
    $('scenarioAssets').innerHTML = Object.entries(assets).map(([id, asset]) => `<button data-scenario-asset="${id}" class="${id === selected ? 'active' : ''}">${escapeHtml(asset.name)}</button>`).join('');
    document.querySelectorAll('[data-scenario-asset]').forEach((button) => button.addEventListener('click', () => {
      selected = button.dataset.scenarioAsset;
      renderedWidgetFor = '';
      renderControls();
      renderChart();
      renderPanel();
    }));
  }

  function renderPanel() {
    const asset = assets[selected];
    if (!asset) return;
    $('scenarioAssetName').textContent = asset.name;
    $('scenarioReference').textContent = Number.isFinite(asset.current)
      ? `Stored research reference: ${asset.current.toLocaleString()} ${asset.unit}. Verify it against the live chart before analysing.`
      : `No verified stored reference for this benchmark. Read the live chart and enter the current price first (${asset.unit}).`;

    const row = document.querySelector('.scenario-input-row');
    row.innerHTML = '<input id="currentPrice" type="number" step="any" aria-label="Current price" placeholder="Current price" /><input id="targetPrice" type="number" step="any" aria-label="Target price" placeholder="Target price" /><button id="runScenario">Analyse</button>';
    $('currentPrice').value = Number.isFinite(asset.current) ? asset.current : '';
    const defaultTarget = Number.isFinite(asset.current) ? (asset.presets.find((value) => value > asset.current) ?? asset.presets.at(-1)) : '';
    $('targetPrice').value = defaultTarget;
    $('targetPresets').innerHTML = asset.presets.map((value) => `<button data-target-preset="${value}">${value.toLocaleString()}</button>`).join('');
    document.querySelectorAll('[data-target-preset]').forEach((button) => button.addEventListener('click', () => { $('targetPrice').value = button.dataset.targetPreset; calculate(); }));
    $('runScenario').addEventListener('click', calculate);
    ['currentPrice','targetPrice'].forEach((id) => $(id).addEventListener('keydown', (event) => { if (event.key === 'Enter') calculate(); }));
    if (Number.isFinite(asset.current)) calculate();
    else $('scenarioOutput').innerHTML = '<div class="scenario-error">Enter the current price shown on the live chart, then choose or enter a target.</div>';
  }

  function calculate() {
    const asset = assets[selected];
    const current = Number.parseFloat($('currentPrice')?.value);
    const target = Number.parseFloat($('targetPrice')?.value);
    if (!Number.isFinite(current) || current <= 0) { $('scenarioOutput').innerHTML = '<div class="scenario-error">Enter a valid current price from the live chart.</div>'; return; }
    if (!Number.isFinite(target) || target <= 0) { $('scenarioOutput').innerHTML = '<div class="scenario-error">Enter a valid target price.</div>'; return; }
    const upside = target >= current;
    const distance = ((target / current) - 1) * 100;
    const drivers = upside ? asset.upside : asset.downside;
    const confirmation = upside ? asset.confirmUp : asset.confirmDown;
    const invalidation = upside ? asset.invalidUp : asset.invalidDown;
    const direction = upside ? 'up' : 'down';
    $('scenarioOutput').innerHTML = `<div class="scenario-result-head"><div><span class="scenario-direction ${direction}">${upside ? 'Upside' : 'Downside'} path</span><h3>What would it take for ${escapeHtml(asset.name)} to reach ${target.toLocaleString()}?</h3><p>A ${Math.abs(distance).toFixed(1)}% move from the current price you entered. This is conditional scenario analysis, not a price prediction.</p></div></div><div class="scenario-driver-list">${drivers.map(([label, body], index) => `<article><span>${index + 1}</span><div><strong>${escapeHtml(label)}</strong><p>${escapeHtml(body)}</p></div></article>`).join('')}</div><div class="scenario-tests"><article><strong>Confirmation test</strong><p>${escapeHtml(confirmation)}</p></article><article><strong>What would invalidate this path</strong><p>${escapeHtml(invalidation)}</p></article></div><div class="scenario-regime"><strong>Current regime filter</strong><p>${escapeHtml(regimeMeaning())}</p></div>`;
  }

  function renderWidgets() {
    const calendar = $('freeEconomicCalendar');
    if (calendar && !calendar.dataset.loaded) {
      calendar.dataset.loaded = 'true';
      calendar.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-events.js';
      script.async = true;
      script.textContent = JSON.stringify({ colorTheme:'dark', isTransparent:true, width:'100%', height:'560', locale:'en', importanceFilter:'-1,0,1', countryFilter:'us,au,cn,jp,eu,gb' });
      calendar.appendChild(script);
    }
    const news = $('freeTradingViewNews');
    if (news && !news.dataset.loaded) {
      news.dataset.loaded = 'true';
      news.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-timeline.js';
      script.async = true;
      script.textContent = JSON.stringify({ feedMode:'all_symbols', isTransparent:true, displayMode:'regular', width:'100%', height:'560', colorTheme:'dark', locale:'en' });
      news.appendChild(script);
    }
  }

  function initialise() {
    if (!selected) return;
    renderControls();
    renderPanel();
    renderWidgets();
    $('nav')?.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-view="scenarios"]');
      if (!button) return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      showView();
    }, true);
    const route = () => { if (location.hash === '#scenarios') showView(false); };
    window.addEventListener('hashchange', route);
    route();
  }

  initialise();
})();
