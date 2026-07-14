Object.assign(window.scenarioAssets, {
  brent: {
    name: 'Brent crude', symbol: 'TVC:UKOIL', current: 79.31, unit: 'USD/bbl', presets: [76, 78, 80, 85, 90],
    upside: [['Seaborne supply','Verified Gulf, North Sea, Russian or other export disruption must reduce available cargoes.'],['Brent structure','Prompt Brent spreads should strengthen into backwardation rather than price rising alone.'],['Refined products','Diesel and gasoline cracks should confirm scarcity is reaching the refining system.'],['Brent–WTI spread','Brent should outperform WTI when the shock is global and seaborne rather than US-specific.'],['Demand resilience','Global refinery runs and freight demand must absorb the higher price.']],
    downside: [['De-escalation','Export flows improve and the global risk premium unwinds.'],['Structure','Brent time spreads and product cracks soften rather than confirm the headline move.'],['Demand destruction','Refinery runs, freight or end-demand weaken visibly.'],['Supply response','OPEC+ or other exporters return barrels faster than expected.'],['Macro','A stronger dollar and global slowdown pressure seaborne demand.']],
    confirmUp: 'Close above the active trigger with tighter Brent spreads, product cracks or verified export-flow stress.', confirmDown: 'Close below the invalidation zone while cargo availability and physical indicators improve.',
    invalidUp: 'Brent spikes but WTI, spreads, cracks and physical flows fail to confirm.', invalidDown: 'Fresh verified seaborne disruption restores backwardation and product tightness.'
  },
  wti: {
    name: 'WTI crude', symbol: 'TVC:USOIL', current: null, unit: 'USD/bbl', presets: [70, 75, 80, 85, 90],
    upside: [['US inventories','Commercial crude and Cushing stocks need to draw rather than rebuild.'],['WTI structure','Prompt WTI spreads should tighten, confirming near-term US scarcity.'],['Refinery demand','US refinery utilisation and crude runs need to remain firm.'],['Exports','Strong Gulf Coast exports can transmit global tightness into the US benchmark.'],['Shale response','Production growth must remain too slow to offset stronger demand or exports.']],
    downside: [['Inventory builds','US commercial or Cushing stocks rise persistently.'],['Production growth','Shale output and Canadian inflows outpace refinery and export demand.'],['Refinery weakness','Maintenance, outages or poor margins reduce crude intake.'],['Brent divergence','Brent remains firm while WTI weakens, signalling a US-specific surplus.'],['Macro','US demand and risk appetite weaken while the dollar strengthens.']],
    confirmUp: 'WTI rises with inventory draws, stronger prompt spreads and firm refinery runs.', confirmDown: 'WTI falls with inventory builds, weaker structure and softer refinery demand.',
    invalidUp: 'Price rises despite Cushing builds and soft WTI structure.', invalidDown: 'A verified US supply outage or export surge rapidly tightens Cushing and prompt spreads.'
  },
  'gas-us': {
    name: 'US natural gas — Henry Hub', symbol: 'NYMEX:NG1!', current: 2.89, unit: 'USD/MMBtu', presets: [2.5, 2.8, 3.0, 3.5, 4.0],
    upside: [['Weather','Hotter summer or colder winter forecasts need to lift power burn or heating demand.'],['Storage','Weekly injections must fall below seasonal expectations or withdrawals exceed them.'],['LNG feedgas','US liquefaction demand needs to rise through terminal restarts or new capacity.'],['Production','Dry-gas output must flatten or fall enough to tighten the balance.'],['Regional basis','Pipeline constraints or local scarcity should support Henry Hub and related hubs.']],
    downside: [['Mild weather','Heating and cooling demand disappoints.'],['Storage surplus','Inventories remain comfortably above seasonal norms.'],['Production growth','Shale and associated gas continue to rise.'],['LNG outage','Liquefaction downtime reduces feedgas demand.'],['Power substitution','Coal, renewables or weaker load reduce gas-fired generation.']],
    confirmUp: 'Henry Hub rises with tighter storage, stronger LNG feedgas and supportive weather revisions.', confirmDown: 'Price falls with storage builds, strong production and weak LNG or power demand.',
    invalidUp: 'A price spike occurs without a tighter storage or feedgas balance.', invalidDown: 'Weather, production disruption or LNG demand rapidly removes the storage surplus.'
  },
  'gas-uk': {
    name: 'UK natural gas — NBP', symbol: 'ICEEUR:UKG1!', current: null, unit: 'p/therm', presets: [60, 80, 100, 120, 150],
    upside: [['UK system balance','The National Gas system needs to tighten through stronger demand or weaker supply.'],['Norwegian and UK flows','North Sea, Norwegian or interconnector flows must fall or become less reliable.'],['LNG arrivals','Fewer cargoes, terminal constraints or stronger Asian competition need to reduce available LNG.'],['Weather and power','Colder, less windy or higher-power-demand conditions should increase gas burn.'],['Storage','UK and nearby European storage must draw faster than seasonal expectations.']],
    downside: [['Mild weather','Heating demand and gas-fired power burn weaken.'],['Strong flows','Norwegian, UKCS and interconnector supply remains reliable.'],['LNG abundance','Cargo arrivals and regasification increase.'],['Storage comfort','UK and European inventories remain adequate.'],['Industrial weakness','Demand destruction limits the need for prompt gas.']],
    confirmUp: 'NBP rises with a tighter UK system balance, weaker pipeline flows, fewer LNG arrivals or accelerating storage draws.', confirmDown: 'NBP falls as flows, LNG arrivals, storage and mild weather improve together.',
    invalidUp: 'Price rises while the UK system remains long and storage/flows improve.', invalidDown: 'A pipeline, LNG or weather shock abruptly tightens the UK balance.'
  }
});
