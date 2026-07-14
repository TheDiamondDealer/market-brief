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
    brent: {
      name: 'Brent crude', symbol: 'TVC:UKOIL', current: 79.31, unit: 'USD/bbl', presets: [76, 78, 80, 85, 90],
      upside: [
        ['Seaborne supply', 'Verified Gulf, North Sea, Russian or other export disruption must reduce available cargoes.'],
        ['Brent structure', 'Prompt Brent spreads should strengthen into backwardation rather than price rising alone.'],
        ['Refined products', 'Diesel and gasoline cracks should confirm scarcity is reaching the refining system.'],
        ['Brent–WTI spread', 'Brent should outperform WTI when the shock is global and seaborne rather than US-specific.'],
        ['Demand resilience', 'Global refinery runs and freight demand must absorb the higher price.']
      ],
      downside: [
        ['De-escalation', 'Export flows improve and the global risk premium unwinds.'],
        ['Structure', 'Brent time spreads and product cracks soften rather than confirm the headline move.'],
        ['Demand destruction', 'Refinery runs, freight or end-demand weaken visibly.'],
        ['Supply response', 'OPEC+ or other exporters return barrels faster than expected.'],
        ['Macro', 'A stronger dollar and global slowdown pressure seaborne demand.']
      ],
      confirmUp: 'Close above the active trigger with tighter Brent spreads, product cracks or verified export-flow stress.',
      confirmDown: 'Close below the invalidation zone while cargo availability and physical indicators improve.',
      invalidUp: 'Brent spikes but WTI, spreads, cracks and physical flows fail to confirm.',
      invalidDown: 'Fresh verified seaborne disruption restores backwardation and product tightness.'
    },
    wti: {
      name: 'WTI crude', symbol: 'TVC:USOIL', current: 77.0, unit: 'USD/bbl', presets: [72, 75, 78, 80, 85],
      upside: [
        ['US inventories', 'Commercial crude and Cushing stocks need to draw rather than rebuild.'],
        ['WTI structure', 'Prompt WTI spreads should tighten, confirming near-term US scarcity.'],
        ['Refinery demand', 'US refinery utilisation and crude runs need to remain firm.'],
        ['Exports', 'Strong Gulf Coast exports can transmit global tightness into the US benchmark.'],
        ['Shale response', 'Production growth must remain too slow to offset stronger demand or exports.']
      ],
      downside: [
        ['Inventory builds', 'US commercial or Cushing stocks rise persistently.'],
        ['Production growth', 'Shale output and Canadian inflows outpace refinery and export demand.'],
        ['Refinery weakness', 'Maintenance, outages or poor margins reduce crude intake.'],
        ['Brent divergence', 'Brent remains firm while WTI weakens, signalling a US-specific surplus.'],
        ['Macro', 'US demand and risk appetite weaken while the dollar strengthens.']
      ],
      confirmUp: 'WTI rises with inventory draws, stronger prompt spreads and firm refinery runs.',
      confirmDown: 'WTI falls with inventory builds, weaker structure and softer refinery demand.',
      invalidUp: 'Price rises despite Cushing builds and soft WTI structure.',
      invalidDown: 'A verified US supply outage or export surge rapidly tightens Cushing and prompt spreads.'
    },
    'gas-us': {
      name: 'US natural gas — Henry Hub', symbol: 'NYMEX:NG1!', current: 2.89, unit: 'USD/MMBtu', presets: [2.5, 2.8, 3.0, 3.5, 4.0],
      upside: [
        ['Weather', 'Hotter summer or colder winter forecasts need to lift power burn or heating demand.'],
        ['Storage', 'Weekly injections must fall below seasonal expectations or withdrawals exceed them.'],
        ['LNG feedgas', 'US liquefaction demand needs to rise through terminal restarts or new capacity.'],
        ['Production', 'Dry-gas output must flatten or fall enough to tighten the balance.'],
        ['Regional basis', 'Pipeline constraints or local scarcity should support Henry Hub and related hubs.']
      ],
      downside: [
        ['Mild weather', 'Heating and cooling demand disappoints.'],
        ['Storage surplus', 'Inventories remain comfortably above seasonal norms.'],
        ['Production growth', 'Shale and associated gas continue to rise.'],
        ['LNG outage', 'Liquefaction downtime reduces feedgas demand.'],
        ['Power substitution', 'Coal, renewables or weaker load reduce gas-fired generation.']
      ],
      confirmUp: 'Henry Hub rises with tighter storage, stronger LNG feedgas and supportive weather revisions.',
      confirmDown: 'Price falls with storage builds, strong production and weak LNG or power demand.',
      invalidUp: 'A price spike occurs without a tighter storage or feedgas balance.',
      invalidDown: 'Weather, production disruption or LNG demand rapidly removes the storage surplus.'
    },
    'gas-uk': {
      name: 'UK natural gas — NBP', symbol: 'ICEEUR:UKG1!', current: 100, unit: 'p/therm reference', presets: [70, 90, 110, 130, 160],
      upside: [
        ['UK system balance', 'The National Gas system needs to tighten through stronger demand or weaker supply.'],
        ['Norwegian and UK flows', 'North Sea, Norwegian or interconnector flows must fall or become less reliable.'],
        ['LNG arrivals', 'Fewer cargoes, terminal constraints or stronger Asian competition need to reduce available LNG.'],
        ['Weather and power', 'Colder, less windy or higher-power-demand conditions should increase gas burn.'],
        ['Storage', 'UK and nearby European storage must draw faster than seasonal expectations.']
      ],
      downside: [
        ['Mild weather', 'Heating demand and gas-fired power burn weaken.'],
        ['Strong flows', 'Norwegian, UKCS and interconnector supply remains reliable.'],
        ['LNG abundance', 'Cargo arrivals and regasification increase.'],
        ['Storage comfort', 'UK and European inventories remain adequate.'],
        ['Industrial weakness', 'Demand destruction limits the need for prompt gas.']
      ],
      confirmUp: 'NBP rises with a tighter UK system balance, weaker pipeline flows, fewer LNG arrivals or accelerating storage draws.',
      confirmDown: 'NBP falls as flows, LNG arrivals, storage and mild weather improve together.',
      invalidUp: 'Price rises while the UK system remains long and storage/flows improve.',
      invalidDown: 'A pipeline, LNG or weather shock abruptly tightens the UK balance.'
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
    $('scenarioReference').textContent = `Latest research reference: ${asset.current.toLocaleString()} ${asset.unit}. Verify the live chart before using the target.`;
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

    $('scenarioOutput').innerHTML = `<div class="scenario-result-head"><div><span class="scenario-direction ${direction}">${upside ? 'Upside' : 'Downside'} path</span><h3>What would it take for ${escapeHtml(asset.name)} to reach ${target.toLocaleString()}?</h3><p>A ${Math.abs(distance).toFixed(1)}% move from the stored research reference. This is conditional scenario analysis, not a price prediction.</p></div></div>
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
      script.textContent = JSON.stringify({ colorTheme: 'dark', isTransparent: true, width: '100%', height: '560', locale: 'en', importanceFilter: '-1,0,1', countryFilter: 'us,au,cn,jp,eu,gb' });
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
