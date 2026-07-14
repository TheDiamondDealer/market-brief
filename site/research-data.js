(() => {
  'use strict';
  window.marketResearchData = {
    updated: '15 July 2026, 08:30 AEST',
    physicalChecklists: {
      gold: { title:'Gold confirmation checklist', summary:'The CPI rebound needs rates, dollar, positioning and flows to confirm.', items:[
        {name:'US 10-year real yield',reading:'2.33% on 14 Jul, down 3 bp',status:'confirmed',source:'US Treasury',freshness:'Daily',interpretation:'Falling real yields supported the gold rebound.'},
        {name:'DXY',reading:'100.94, inside decision zone',status:'confirmed',source:'Reuters market close',freshness:'Daily',interpretation:'The softer dollar removed one leg of Monday’s bearish confirmation.'},
        {name:'COMEX managed money',reading:'CFTC week ended 7 Jul; lagged',status:'automatic',source:'CFTC COT',freshness:'Weekly',interpretation:'Use as crowding context, not same-day confirmation.'},
        {name:'ETF holdings and flows',reading:'Not verified in this pass',status:'pending',source:'Issuer disclosures',freshness:'Daily/weekly',interpretation:'Sustained inflows would broaden demand.'},
        {name:'Central-bank purchases',reading:'No new monthly release in this pass',status:'pending',source:'IMF / central banks',freshness:'Monthly',interpretation:'Official demand can override restrictive rates.'},
        {name:'Physical premiums',reading:'Not verified in this pass',status:'pending',source:'Regional market reports',freshness:'Weekly',interpretation:'Premiums distinguish physical from futures demand.'}
      ]},
      oil: { title:'Oil physical-market checklist', summary:'Brent is price-triggered and flow-confirmed; spreads, cracks and inventories are the next checks.', items:[
        {name:'Brent close',reading:'$84.73, above $80 trigger',status:'confirmed',source:'Reuters',freshness:'Daily',interpretation:'Price confirms a live supply premium.'},
        {name:'Tanker and export flows',reading:'Hormuz traffic near a two-month low',status:'confirmed',source:'Reuters / verified shipping reports',freshness:'Daily',interpretation:'Physical disruption validates more than rhetoric.'},
        {name:'Brent time spreads',reading:'Not independently verified',status:'pending',source:'Exchange data',freshness:'Daily',interpretation:'Stronger backwardation would add scarcity confirmation.'},
        {name:'Product cracks',reading:'Not independently verified',status:'pending',source:'Exchange data',freshness:'Daily',interpretation:'Cracks show pass-through to consumer inflation.'},
        {name:'US inventories',reading:'Next EIA release 16 Jul 00:30 AEST',status:'pending',source:'EIA',freshness:'Weekly',interpretation:'Draws would reinforce physical tightness.'},
        {name:'Refinery utilisation',reading:'95.8% in week ended 3 Jul',status:'confirmed',source:'EIA',freshness:'Weekly',interpretation:'High runs support crude demand but may rebuild products.'}
      ]},
      gas: { title:'Gas regional-split checklist', summary:'Do not treat gas as one market: Europe and the UK are pricing LNG-route risk while Henry Hub remains domestic.', items:[
        {name:'TTF',reading:'~€54.28/MWh, above €52 trigger',status:'confirmed',source:'Market data',freshness:'Daily',interpretation:'European gas is pricing LNG supply-route stress.'},
        {name:'UK NBP',reading:'~130.25 p/therm',status:'confirmed',source:'Market data',freshness:'Daily',interpretation:'UK pricing confirms the European move.'},
        {name:'Henry Hub',reading:'~$2.90/mmBtu',status:'diverging',source:'CME-linked market data',freshness:'Daily',interpretation:'Domestic US gas has not confirmed a global demand shock.'},
        {name:'LNG/Hormuz route',reading:'Physical shipping risk active',status:'confirmed',source:'Reuters',freshness:'Daily',interpretation:'Route concentration explains the regional premium.'}
      ]},
      copper: { title:'Copper physical-demand checklist', summary:'The $6.30 price break is provisional until China and physical evidence align.', items:[
        {name:'Copper price',reading:'~$6.32/lb, above $6.30',status:'confirmed',source:'Market data',freshness:'Daily',interpretation:'Price trigger fired.'},
        {name:'Iron ore / CNH / AUD',reading:'Ore >CNY760; CNH and AUD firmer',status:'partial',source:'Market data',freshness:'Daily',interpretation:'Cross-market direction is constructive.'},
        {name:'LME/COMEX/Shanghai inventories',reading:'Not verified in this pass',status:'pending',source:'Exchange reports',freshness:'Daily/weekly',interpretation:'Aligned draws are required for physical confirmation.'},
        {name:'Treatment charges and premiums',reading:'Not verified in this pass',status:'pending',source:'Industry reporting',freshness:'Weekly',interpretation:'Would separate concentrate tightness from macro buying.'},
        {name:'China activity',reading:'Due 15 Jul 12:00 AEST',status:'pending',source:'China NBS',freshness:'Event',interpretation:'Production, retail and investment composition are decisive.'}
      ]},
      silver: { title:'Silver dual-demand checklist', summary:'Silver gained with both gold and copper, but each leg still needs confirmation.', items:[
        {name:'Gold and real yields',reading:'Gold rebounded; 10Y real yield 2.33%',status:'confirmed',source:'Reuters / US Treasury',freshness:'Daily',interpretation:'Monetary channel improved.'},
        {name:'Industrial metals',reading:'Copper >$6.30; China data pending',status:'partial',source:'Market data / NBS calendar',freshness:'Daily',interpretation:'Industrial leg is price-positive but unconfirmed.'},
        {name:'COMEX positioning',reading:'CFTC week ended 7 Jul; lagged',status:'automatic',source:'CFTC COT',freshness:'Weekly',interpretation:'Crowding remains a risk control.'},
        {name:'Inventories and ETF flows',reading:'Not verified in this pass',status:'pending',source:'Exchange / issuer data',freshness:'Daily/weekly',interpretation:'Would confirm broader demand.'}
      ]},
      'rare-earths': { title:'Rare-earth supply-chain checklist', summary:'No new verified daily policy or supply-chain change; assess element by element.', items:[
        {name:'NdPr / Dy / Tb prices',reading:'Not refreshed in this pass',status:'pending',source:'Industry assessments',freshness:'Weekly',interpretation:'Element-specific pricing is essential.'},
        {name:'China quotas and export controls',reading:'No new verified change',status:'pending',source:'Chinese government',freshness:'Event',interpretation:'Policy can alter availability rapidly.'},
        {name:'Magnet lead times / ex-China projects',reading:'Not refreshed in this pass',status:'pending',source:'Company and government releases',freshness:'Monthly/event',interpretation:'Downstream milestones determine diversification.'}
      ]}
    },
    eventReactions: [
      {id:'us-cpi-2026-07',event:'US June CPI',scheduled:'14 July 2026 · 10:30 pm Melbourne',stage:'Close captured',source:'US Bureau of Labor Statistics',previous:'Headline 4.2% y/y; core 2.9% y/y',consensus:'Reuters: headline 3.8% y/y; core 2.8% y/y and 0.2% m/m',actual:'Headline -0.4% m/m, 3.5% y/y; core 0.0% m/m, 2.6% y/y',scenarios:[['Hotter','Not realised'],['Broadly in line','Not realised'],['Softer','Realised: yields/USD lower; gold/Nasdaq higher']],reactions:{immediate:'Hike odds, 2Y/10Y yields and DXY fell; gold and equities rose.',close:'S&P +0.38%, Nasdaq +0.90%, DXY 100.94, US10Y 4.589%, gold ~$4,052.',day1:'Pending — due after 15 Jul US close.',day5:'Pending — due after 21 Jul US close.'},verdict:'Price-confirmed dovish countershock; regime not broken'},
      {id:'china-activity-2026-q2',event:'China Q2 GDP and June activity',scheduled:'15 July 2026 · 12:00 pm Melbourne',stage:'Pre-event',source:'National Bureau of Statistics of China / Reuters poll',previous:'GDP 5.0% y/y and 1.3% q/q in Q1',consensus:'GDP 4.5% y/y and 0.9% q/q',actual:'Pending',scenarios:[['Broad upside','Copper, iron ore, AUD and China equities should confirm together.'],['Mixed composition','Separate industrial/export strength from retail/property weakness.'],['Broad downside','Pressure on ore, copper, AUD and materials equities.']],reactions:{immediate:'Pending',close:'Pending',day1:'Pending',day5:'Pending'},verdict:'Too early'},
      {id:'us-ppi-2026-07',event:'US June PPI',scheduled:'15 July 2026 · 10:30 pm Melbourne',stage:'Pre-event',source:'US Bureau of Labor Statistics',previous:'Final demand +0.9% m/m and +6.5% y/y in May',consensus:'No robust primary-source consensus verified at publication',actual:'Pending',scenarios:[['Hot / broad','Yields, DXY and hike odds rebound; gold/Nasdaq pressured.'],['Mixed','CPI relief and oil shock remain in conflict.'],['Soft / broad','Hike odds may fall below 50%; lower yields/USD support gold and duration.']],reactions:{immediate:'Pending',close:'Pending',day1:'Pending',day5:'Pending'},verdict:'Highest-stakes next event'}
    ]
  };
})();
