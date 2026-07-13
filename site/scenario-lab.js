(() => {
  'use strict';

  const assets = {
    gold: {
      name: 'Gold', symbol: 'OANDA:XAUUSD', current: 4072, unit: 'USD/oz', presets: [3980, 4050, 4100, 4150, 4200],
      upside: [
        ['Rates', 'US real and nominal yields need to fall, reducing the opportunity cost of holding gold.'],
        ['US dollar', 'DXY weakness would remove the strongest current headwind.'],
        ['Macro catalyst', 'Softer CPI, weaker employment or a dovish Fed repricing would improve the path.'],
        ['Haven override', 'Gold would need to rise despite firm oil or geopolitical stress, showing haven demand has regained control.'],
        ['Flows', 'ETF inflows, central-bank demand or futures buying would need to confirm the move.']
      ],
      downside: [
        ['Rates', 'US 10-year and real yields remain high or break upward.'],
        ['US dollar', 'DXY strengthens as policy expectations turn more hawkish.'],
        ['Macro catalyst', 'Hot CPI or strong labour data preserves tightening risk.'],
        ['Technical confirmation', 'A daily close below $4,050 would strengthen the active bearish trigger.'],
        ['Positioning', 'Crowded haven positions liquidate after another failed safe-haven reaction.']
      ],
      confirmUp: 'Close above $4,150, ideally while DXY and yields fall.',
      confirmDown: 'Close below $4,050 with DXY ≥101 and US 10Y ≥4.60%.',
      invalidUp: 'Gold fails above $4,100 and yields/DXY continue rising.',
      invalidDown: 'Gold closes above $4,150 or rises for two sessions alongside oil, DXY and yields.'
    },
    oil: {
      name: 'Brent oil', symbol: 'TVC:UKOIL', current: 79.31, unit: 'USD/bbl', presets: [76, 78, 80, 85, 90],
      upside: [
        ['Physical supply', 'Verified export disruption, tanker restrictions or lower Gulf flows must tighten the physical market.'],
        ['Market structure', 'Brent time spreads and refined-product cracks should strengthen with price.'],
        ['Inventories', 'Unexpected draws or lower available stocks would confirm scarcity.'],
        ['Policy', 'OPEC+ restraint or sanctions enforcement would reduce effective supply.'],
        ['Demand', 'Refinery runs and freight demand must remain resilient enough to absorb the shock.']
      ],
      downside: [
        ['De-escalation', 'Gulf flows improve and the geopolitical premium unwinds.'],
        ['Physical confirmation', 'Time spreads and product cracks soften rather than confirm the headline risk.'],
        ['Demand', 'Higher prices produce visible demand destruction or weaker refinery runs.'],
        ['Supply response', 'OPEC+ or US production returns faster than expected.'],
        ['Macro', 'A stronger dollar and global slowdown pressure cyclical demand.']
      ],
      confirmUp: 'Daily close above $80 with tighter spreads, cracks or verified physical-flow stress.',
      confirmDown: 'Daily close below $76 while Gulf flows and physical indicators improve.',
      invalidUp: 'Price spikes intraday but closes below $80 without physical confirmation.',
      invalidDown: 'Fresh verified supply disruption restores backwardation and product tightness.'
    },
    copper: {
      name: 'Copper', symbol: 'COMEX:HG1!', current: 6.22, unit: 'USD/lb', presets: [6.00, 6.10, 6.25, 6.30, 6.50],
      upside: [
        ['China demand', 'Credit, grids, manufacturing and property activity need to improve together.'],
        ['Physical market', 'Visible inventories fall and regional premiums strengthen.'],
        ['Supply', 'Mine disruptions or lower treatment charges signal concentrate tightness.'],
        ['US dollar', 'DXY weakness would reduce the financial headwind.'],
        ['Cross-market confirmation', 'LME, COMEX and Shanghai copper should rise together rather than diverge.']
      ],
      downside: [
        ['China demand', 'Property, credit or manufacturing data weaken further.'],
        ['Inventories', 'Exchange stocks rebuild and physical premiums soften.'],
        ['US dollar', 'A stronger dollar tightens global financial conditions.'],
        ['Supply response', 'Mine and scrap supply improve faster than demand.'],
        ['Positioning', 'Speculative longs unwind without physical buyers replacing them.']
      ],
      confirmUp: 'Close above $6.30/lb with falling inventories and aligned LME/ShFE strength.',
      confirmDown: 'Close below $6.10/lb with weaker China and physical-market evidence.',
      invalidUp: 'Price returns inside $6.10–6.25 while inventories rise.',
      invalidDown: 'Physical premiums and inventory draws strengthen despite a temporary price dip.'
    },
    silver: {
      name: 'Silver', symbol: 'OANDA:XAGUSD', current: 59.56, unit: 'USD/oz', presets: [55, 58, 60, 62, 65],
      upside: [
        ['Gold channel', 'Gold must stabilise or rise as yields and the dollar soften.'],
        ['Industrial demand', 'Copper, solar and manufacturing signals need to improve.'],
        ['Flows', 'ETF or futures demand must absorb silver’s higher volatility.'],
        ['Macro catalyst', 'Softer inflation or labour data would support precious metals through rates.'],
        ['Relative value', 'The gold/silver ratio would need to compress as silver outperforms.']
      ],
      downside: [
        ['Rates and USD', 'Higher yields and a stronger dollar pressure the precious complex.'],
        ['Industrial cycle', 'China or global manufacturing expectations weaken.'],
        ['Volatility', 'Risk reduction forces liquidation in higher-beta silver positions.'],
        ['Gold failure', 'Gold remains unable to attract haven demand.'],
        ['Positioning', 'Crowded speculative exposure unwinds.']
      ],
      confirmUp: 'Silver outperforms gold while copper and industrial data improve.',
      confirmDown: 'Silver breaks support with gold weak, DXY/yields firm and industrial metals soft.',
      invalidUp: 'Silver rallies alone without gold, copper or flow confirmation.',
      invalidDown: 'Gold stabilises, yields fall and industrial demand indicators turn higher.'
    }
  };

  let selected = 'gold';
  let renderedWidgetFor = '';

  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value = '') => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const currentRegimeMeaning = () => typeof fallback !== 'undefined' && fallback.regime?.meaning
    ? fallback.regime.meaning
    : 'Use the latest regime state when interpreting the target.';

  function showScenarioView(updateHash = true) {
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    $('view-scenarios')?.classList.add('active');
    document.querySelectorAll('#nav button').forEach((button) => button.classList.toggle('active', button.dataset.view === 'scenarios'));
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
    if (updateHash) history.replaceState(null, '', '#scenarios');
    setTimeout(renderTradingView, 0);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderTradingView() {
    const host = $('scenarioChart');
    if (!host || renderedWidgetFor === selected) return;
    renderedWidgetFor = selected;
    host.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.textContent = JSON.stringify({
      autosize: true,
      symbol: assets[selected].symbol,
      interval: '60',
      timezone: 'Australia/Sydney',
      theme: 'dark',
      style: '1',
      locale: 'en',
      backgroundColor: 'rgba(7, 16, 20, 1)',
      gridColor: 'rgba(33, 52, 61, 0.45)',
      hide_top_toolbar: false,
      allow_symbol_change: true,
      save_image: false,
      calendar: false,
      support_host: 'https://www.tradingview.com'
    });
    host.appendChild(script);
  }

  function renderAssetControls() {
    $('scenarioAssets').innerHTML = Object.entries(assets).map(([id, asset]) => `<button data-scenario-asset="${id}" class="${id === selected ? 'active' : ''}">${escapeHtml(asset.name)}</button>`).join('');
    document.querySelectorAll('[data-scenario-asset]').forEach((button) => button.addEventListener('click', () => {
      selected = button.dataset.scenarioAsset;
      renderedWidgetFor = '';
      renderAssetControls();
      renderTradingView();
      renderTargetPanel();
    }));
  }

  function renderTargetPanel() {
    const asset = assets[selected];
    $('scenarioAssetName').textContent = asset.name;
    $('scenarioReference').textContent = `Latest research reference: ${asset.current.toLocaleString()} ${asset.unit}`;
    $('targetPresets').innerHTML = asset.presets.map((value) => `<button data-target-preset="${value}">${value.toLocaleString()}</button>`).join('');
    $('targetPrice').value = asset.presets.find((value) => value > asset.current) || asset.presets[asset.presets.length - 1];
    document.querySelectorAll('[data-target-preset]').forEach((button) => button.addEventListener('click', () => {
      $('targetPrice').value = button.dataset.targetPreset;
      calculateScenario();
    }));
    calculateScenario();
  }

  function calculateScenario() {
    const asset = assets[selected];
    const target = Number.parseFloat($('targetPrice').value);
    if (!Number.isFinite(target) || target <= 0) {
      $('scenarioOutput').innerHTML = '<div class="scenario-error">Enter a valid target price.</div>';
      return;
    }
    const upside = target >= asset.current;
    const distance = ((target / asset.current) - 1) * 100;
    const drivers = upside ? asset.upside : asset.downside;
    const confirmation = upside ? asset.confirmUp : asset.confirmDown;
    const invalidation = upside ? asset.invalidUp : asset.invalidDown;
    const direction = upside ? 'up' : 'down';

    $('scenarioOutput').innerHTML = `<div class="scenario-result-head"><div><span class="scenario-direction ${direction}">${upside ? 'Upside' : 'Downside'} path</span><h3>What would it take for ${escapeHtml(asset.name)} to reach ${target.toLocaleString()}?</h3><p>A ${Math.abs(distance).toFixed(1)}% move from the latest research reference. This is conditional scenario analysis, not a price prediction.</p></div></div>
      <div class="scenario-driver-list">${drivers.map(([label, body], index) => `<article><span>${index + 1}</span><div><strong>${escapeHtml(label)}</strong><p>${escapeHtml(body)}</p></div></article>`).join('')}</div>
      <div class="scenario-tests"><article><strong>Confirmation test</strong><p>${escapeHtml(confirmation)}</p></article><article><strong>What would invalidate this path</strong><p>${escapeHtml(invalidation)}</p></article></div>
      <div class="scenario-regime"><strong>Current regime filter</strong><p>${escapeHtml(currentRegimeMeaning())}</p></div>`;
  }

  function renderFreeWidgets() {
    const calendar = $('freeEconomicCalendar');
    if (calendar && !calendar.dataset.loaded) {
      calendar.dataset.loaded = 'true';
      calendar.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-events.js';
      script.async = true;
      script.textContent = JSON.stringify({ colorTheme: 'dark', isTransparent: true, width: '100%', height: '560', locale: 'en', importanceFilter: '-1,0,1', countryFilter: 'us,au,cn,jp,eu' });
      calendar.appendChild(script);
    }

    const news = $('freeTradingViewNews');
    if (news && !news.dataset.loaded) {
      news.dataset.loaded = 'true';
      news.innerHTML = '<div class="tradingview-widget-container__widget"></div>';
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-timeline.js';
      script.async = true;
      script.textContent = JSON.stringify({ feedMode: 'all_symbols', isTransparent: true, displayMode: 'regular', width: '100%', height: '560', colorTheme: 'dark', locale: 'en' });
      news.appendChild(script);
    }
  }

  function initialise() {
    renderAssetControls();
    renderTargetPanel();
    renderFreeWidgets();
    $('runScenario')?.addEventListener('click', calculateScenario);
    $('targetPrice')?.addEventListener('keydown', (event) => { if (event.key === 'Enter') calculateScenario(); });

    $('nav')?.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-view="scenarios"]');
      if (!button) return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      showScenarioView();
    }, true);

    const route = () => { if (location.hash === '#scenarios') showScenarioView(false); };
    window.addEventListener('hashchange', route);
    route();
  }

  initialise();
})();
