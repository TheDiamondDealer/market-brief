(() => {
  'use strict';
  if (typeof fallback === 'undefined') return;

  const product = (id) => (fallback.products || []).find((item) => item.id === id);

  const oil = product('oil');
  if (oil) {
    Object.assign(oil, {
      name: 'Oil — Brent & WTI',
      tagline: 'Global seaborne crude, US crude and the physical risk premium.',
      benchmark: 'Brent / WTI',
      sensitivity: 'Supply flows / inflation / refining',
      thesis: 'Oil must be read through two separate benchmarks. Brent is the cleaner global seaborne and geopolitical signal; WTI is more exposed to US inventories, Cushing logistics and shale supply. A durable global shock should strengthen Brent, WTI, time spreads and refined-product cracks together rather than only one headline contract.',
      marketStructure: [
        'Track Brent and WTI outright prices separately and calculate the Brent–WTI spread.',
        'Brent reflects global seaborne scarcity; WTI reflects the US inland, Cushing and export balance.',
        'Front-month time spreads reveal prompt tightness inside each benchmark.',
        'Gasoline and diesel cracks show whether crude strength is transmitting into consumer inflation.',
        'Tanker traffic, export flows and refinery runs matter more than political rhetoric alone.'
      ],
      benchmarks: [
        ['Brent front month', 'Global seaborne crude benchmark'],
        ['WTI front month', 'US crude and Cushing benchmark'],
        ['Brent–WTI spread', 'Global versus US regional tightness'],
        ['Brent and WTI time spreads', 'Prompt physical tightness'],
        ['Dubai/Oman', 'Middle East sour-crude reference'],
        ['Gasoline and diesel cracks', 'Refining and consumer-inflation transmission']
      ],
      supply: [
        'OPEC+ production and compliance',
        'Strait of Hormuz traffic and Gulf exports',
        'US shale output, Cushing stocks and Gulf Coast exports',
        'Canadian and Latin American flows into the US system',
        'Sanctions, outages and refinery availability'
      ],
      demand: [
        'Global refinery runs and seaborne freight',
        'US driving, aviation and refinery demand',
        'China and India refinery throughput',
        'Petrochemical margins and product exports'
      ],
      catalysts: [
        'Verified disruption to global seaborne exports',
        'OPEC+ policy change',
        'EIA US inventory and Cushing surprises',
        'IEA/OPEC balance revisions',
        'Refinery outages and product shortages',
        'A sharp change in the Brent–WTI spread'
      ],
      risks: [
        'Rapid geopolitical de-escalation',
        'Demand destruction from higher prices',
        'Unexpected OPEC+ supply return',
        'US production or exports rising faster than expected',
        'Global recession or stronger dollar'
      ],
      triggers: [
        ['Brent warning', '$78–80/bbl in the current framework'],
        ['Brent confirmation', 'Close above trigger with tighter spreads, cracks or verified flow stress'],
        ['WTI confirmation', 'US inventories/Cushing and WTI structure agree with the move'],
        ['Regional divergence', 'Brent outperforms WTI when seaborne risk exceeds US tightness'],
        ['Invalidation', 'Both benchmarks weaken as flows improve and structure softens']
      ],
      related: ['US yields', 'DXY', 'Airlines', 'Energy equities', 'Inflation breakevens', 'Natural gas'],
      notes: [
        'Never use “crude oil” as one undifferentiated signal: show Brent and WTI side by side.',
        'A Brent-only rally can be geopolitical; a joint Brent/WTI rally with stronger cracks is broader confirmation.'
      ]
    });
  }

  const gas = product('natural-gas');
  if (gas) {
    Object.assign(gas, {
      name: 'Natural gas — US & UK',
      tagline: 'Henry Hub, UK NBP, LNG flows and regional weather balances.',
      benchmark: 'Henry Hub / UK NBP',
      sensitivity: 'Weather / storage / LNG / pipelines',
      thesis: 'Natural gas is regional rather than one global commodity. Henry Hub reflects US production, storage, power burn and LNG feedgas. UK NBP reflects the British balancing system, North Sea and Norwegian flows, storage, interconnectors and competition for LNG. Their divergence is often more informative than either outright price.',
      marketStructure: [
        'Henry Hub is the primary US benchmark and trades in USD per MMBtu.',
        'UK NBP is the British benchmark and trades in pence per therm.',
        'TTF remains a useful continental-European cross-check, but it is not the UK benchmark.',
        'LNG liquefaction, shipping and regasification connect regions imperfectly.',
        'Weather, storage and pipeline flows dominate short-term pricing.'
      ],
      benchmarks: [
        ['Henry Hub', 'US natural-gas benchmark'],
        ['UK NBP', 'United Kingdom natural-gas benchmark'],
        ['TTF', 'Continental-European cross-check'],
        ['JKM', 'Asian LNG benchmark'],
        ['US and UK storage', 'Seasonal balance'],
        ['LNG feedgas, freight and outages', 'Regional transmission']
      ],
      supply: [
        'US dry-gas production and associated gas',
        'US LNG terminal availability and feedgas',
        'UK Continental Shelf, Norwegian and interconnector flows',
        'UK storage and LNG regasification',
        'Qatar, US and Australian LNG availability'
      ],
      demand: [
        'US power burn, heating/cooling and industrial demand',
        'UK heating demand and gas-fired power generation',
        'European industrial demand and storage requirements',
        'Asian LNG buying and cargo competition'
      ],
      catalysts: [
        'US and UK weather revisions',
        'EIA US storage surprise',
        'UK/Northwest European storage and flow changes',
        'US LNG export outage or restart',
        'Norwegian, UK or interconnector disruption',
        'LNG shipping disruption or cargo diversion'
      ],
      risks: [
        'Mild weather',
        'High storage',
        'US production growth',
        'Weak UK or European industrial demand',
        'Rapid restoration of pipeline or LNG availability'
      ],
      triggers: [
        ['US Henry Hub', 'Price, storage, production and LNG feedgas must agree'],
        ['UK NBP', 'Price, storage, Norwegian/UK flows and LNG arrivals must agree'],
        ['Regional divergence', 'Henry Hub weak while NBP rises signals constrained transatlantic transmission'],
        ['Convergence', 'Improving LNG/pipeline availability narrows the US–UK gap']
      ],
      related: ['Oil', 'Power prices', 'LNG shipping', 'UK utilities', 'European industry', 'Fertiliser'],
      notes: [
        'The dashboard should never label TTF as the UK benchmark; UK gas is tracked through NBP.',
        'US and UK gas can move in opposite directions because storage, weather and infrastructure are regional.'
      ]
    });
  }

  const research = window.marketResearchData;
  if (research?.physicalChecklists) {
    research.physicalChecklists.oil = {
      title: 'Brent and WTI physical-market checklist',
      summary: 'A global oil thesis requires separate confirmation from Brent and WTI. Their spread, time structures, inventories and product cracks show whether the move is global, US-specific or merely headline-driven.',
      items: [
        { name: 'Brent managed-money positioning', reading: 'Official CFTC mapping pending/current by contract availability', status: 'pending', source: 'CFTC COT — oil-brent', freshness: 'Weekly', interpretation: 'Shows whether global-benchmark exposure confirms the move or is becoming crowded.' },
        { name: 'WTI managed-money positioning', reading: 'Official CFTC mapping pending/current by contract availability', status: 'pending', source: 'CFTC COT — oil-wti', freshness: 'Weekly', interpretation: 'Shows speculative exposure in the US crude benchmark.' },
        { name: 'Brent–WTI spread', reading: 'Research update required', status: 'pending', source: 'Exchange/market data', freshness: 'Daily', interpretation: 'Brent outperformance often indicates tighter seaborne conditions relative to the US balance.' },
        { name: 'Brent and WTI time spreads', reading: 'Research update required', status: 'pending', source: 'Exchange/market data', freshness: 'Daily', interpretation: 'Strengthening backwardation in both benchmarks is stronger physical confirmation.' },
        { name: 'Gasoline and diesel cracks', reading: 'Research update required', status: 'pending', source: 'Exchange/market data', freshness: 'Daily', interpretation: 'Product cracks reveal refining tightness and consumer-inflation transmission.' },
        { name: 'US inventories and Cushing', reading: 'Research update required', status: 'pending', source: 'US EIA', freshness: 'Weekly', interpretation: 'US draws support WTI; builds can explain WTI underperformance versus Brent.' },
        { name: 'Tanker and export flows', reading: 'Research update required', status: 'pending', source: 'Official port/export data and verified shipping reports', freshness: 'Daily/weekly', interpretation: 'Verified seaborne disruption is stronger evidence than political rhetoric.' },
        { name: 'Refinery utilisation and runs', reading: 'Research update required', status: 'pending', source: 'EIA and regional agencies', freshness: 'Weekly', interpretation: 'Refinery demand determines crude intake and product availability.' }
      ]
    };

    research.physicalChecklists['natural-gas'] = {
      title: 'US Henry Hub and UK NBP checklist',
      summary: 'US and UK gas are separate regional systems. Each benchmark needs its own weather, storage, production/flow and LNG confirmation before a directional view is upgraded.',
      items: [
        { name: 'US Henry Hub positioning', reading: 'Official CFTC mapping pending/current by contract availability', status: 'pending', source: 'CFTC COT — gas-us', freshness: 'Weekly', interpretation: 'Managed-money exposure shows whether the US gas move is crowded or under-owned.' },
        { name: 'UK NBP positioning', reading: 'Official CFTC mapping pending/current by contract availability', status: 'pending', source: 'CFTC COT — gas-uk', freshness: 'Weekly', interpretation: 'Shows speculative exposure where an official current CFTC-covered NBP contract is available.' },
        { name: 'US storage versus seasonal norms', reading: 'Research update required', status: 'pending', source: 'US EIA', freshness: 'Weekly', interpretation: 'Storage surplus or deficit is the core Henry Hub balance signal.' },
        { name: 'US production and LNG feedgas', reading: 'Research update required', status: 'pending', source: 'EIA, pipeline and terminal disclosures', freshness: 'Daily/weekly', interpretation: 'Production and LNG demand determine whether storage trends can persist.' },
        { name: 'UK storage and system balance', reading: 'Research update required', status: 'pending', source: 'National Gas and storage operators', freshness: 'Daily/weekly', interpretation: 'The UK system balance shows prompt scarcity more directly than a broad European headline.' },
        { name: 'UK, Norwegian and interconnector flows', reading: 'Research update required', status: 'pending', source: 'National Gas, Gassco and interconnector operators', freshness: 'Daily', interpretation: 'Flow disruptions can tighten NBP even when Henry Hub remains soft.' },
        { name: 'LNG arrivals and regasification', reading: 'Research update required', status: 'pending', source: 'Terminal and shipping disclosures', freshness: 'Daily/weekly', interpretation: 'LNG availability is the main bridge between US abundance and UK scarcity.' },
        { name: 'Weather and gas-fired power demand', reading: 'Research update required', status: 'pending', source: 'Meteorological and grid/system data', freshness: 'Daily', interpretation: 'Temperature and power burn can rapidly alter both regional balances.' }
      ]
    };
  }
})();
