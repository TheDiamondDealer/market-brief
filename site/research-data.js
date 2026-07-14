(() => {
  'use strict';

  window.marketResearchData = {
    updated: '14 July 2026',
    physicalChecklists: {
      gold: {
        title: 'Gold confirmation checklist',
        summary: 'Gold should not be upgraded or downgraded from price alone. Rates, the US dollar, positioning and physical/official flows must be assessed together.',
        items: [
          { name: 'US 10-year real yield', reading: 'Connected to free FRED pipeline', status: 'automatic', source: 'Federal Reserve Bank of St. Louis', freshness: 'Daily', interpretation: 'Falling real yields reduce the opportunity cost of holding gold.' },
          { name: 'US dollar', reading: 'Broad dollar index connected; DXY remains research-reviewed', status: 'partial', source: 'FRED / market research', freshness: 'Daily', interpretation: 'A weaker dollar normally supports gold, but the current regime must be checked.' },
          { name: 'COMEX managed-money positioning', reading: 'Connected to free CFTC pipeline', status: 'automatic', source: 'CFTC COT', freshness: 'Weekly', interpretation: 'Extreme long positioning raises liquidation risk; extreme shorts can create squeeze risk.' },
          { name: 'Gold ETF holdings and flows', reading: 'Research update required', status: 'pending', source: 'Issuer and exchange disclosures', freshness: 'Daily/weekly', interpretation: 'Sustained ETF inflows can confirm financial demand beyond futures positioning.' },
          { name: 'Central-bank purchases', reading: 'Research update required', status: 'pending', source: 'IMF, World Gold Council and central-bank releases', freshness: 'Monthly/quarterly', interpretation: 'Official-sector demand can create a haven override even when rates remain restrictive.' },
          { name: 'Physical premiums', reading: 'Research update required', status: 'pending', source: 'Regional market and refinery sources', freshness: 'Weekly', interpretation: 'Regional premiums help distinguish physical demand from futures-led price moves.' }
        ]
      },
      oil: {
        title: 'Oil physical-market checklist',
        summary: 'A geopolitical headline is not physical confirmation. Time spreads, product cracks, inventories, exports and refinery behaviour must validate the move.',
        items: [
          { name: 'Brent time spreads', reading: 'Research update required', status: 'pending', source: 'Exchange/market data', freshness: 'Daily', interpretation: 'Strengthening backwardation indicates prompt physical tightness.' },
          { name: 'Gasoline and diesel cracks', reading: 'Research update required', status: 'pending', source: 'Exchange/market data', freshness: 'Daily', interpretation: 'Product cracks show whether crude strength is transmitting into consumer inflation.' },
          { name: 'Commercial inventories', reading: 'Research update required', status: 'pending', source: 'EIA and IEA', freshness: 'Weekly/monthly', interpretation: 'Inventory draws support scarcity; builds can contradict a headline-driven rally.' },
          { name: 'Tanker and export flows', reading: 'Research update required', status: 'pending', source: 'Official port/export data and verified shipping reports', freshness: 'Daily/weekly', interpretation: 'Verified flow disruption is stronger evidence than rhetoric alone.' },
          { name: 'Refinery utilisation', reading: 'Research update required', status: 'pending', source: 'EIA and regional agencies', freshness: 'Weekly', interpretation: 'Refinery runs determine crude demand and product availability.' },
          { name: 'Managed-money positioning', reading: 'Connected to free CFTC pipeline', status: 'automatic', source: 'CFTC COT', freshness: 'Weekly', interpretation: 'Positioning shows whether a physical thesis is already crowded.' }
        ]
      },
      copper: {
        title: 'Copper physical-demand checklist',
        summary: 'Copper needs aligned Western and Chinese pricing plus inventory and premium confirmation before a structural demand thesis is treated as active.',
        items: [
          { name: 'LME, COMEX and Shanghai inventories', reading: 'Research update required', status: 'pending', source: 'Exchange warehouse reports', freshness: 'Daily/weekly', interpretation: 'Broad inventory draws are stronger than a draw isolated to one exchange.' },
          { name: 'Treatment charges', reading: 'Research update required', status: 'pending', source: 'Smelter and industry reporting', freshness: 'Weekly/monthly', interpretation: 'Falling treatment charges can signal concentrate tightness.' },
          { name: 'Regional physical premiums', reading: 'Research update required', status: 'pending', source: 'Industry and exchange reporting', freshness: 'Weekly', interpretation: 'Rising premiums confirm buyers are competing for physical metal.' },
          { name: 'China grid and manufacturing demand', reading: 'Research update required', status: 'pending', source: 'Chinese official and company releases', freshness: 'Monthly', interpretation: 'Grid and power investment can offset property weakness.' },
          { name: 'Mine disruptions and supply guidance', reading: 'Research update required', status: 'pending', source: 'Producer filings and government releases', freshness: 'Event-driven', interpretation: 'Verified production losses tighten the concentrate and refined balance.' },
          { name: 'Managed-money positioning', reading: 'Connected to free CFTC pipeline', status: 'automatic', source: 'CFTC COT', freshness: 'Weekly', interpretation: 'Extreme speculative exposure must be reconciled with physical evidence.' }
        ]
      },
      silver: {
        title: 'Silver dual-demand checklist',
        summary: 'Silver requires confirmation from both the monetary-metal channel and the industrial cycle because either side can dominate its higher volatility.',
        items: [
          { name: 'Gold and real-yield channel', reading: 'Connected partly to free FRED pipeline', status: 'partial', source: 'FRED and market research', freshness: 'Daily', interpretation: 'Lower yields and a firmer gold trend support the monetary component.' },
          { name: 'Industrial metals and manufacturing', reading: 'Research update required', status: 'pending', source: 'Official releases and exchange data', freshness: 'Daily/monthly', interpretation: 'Copper and manufacturing strength support the industrial component.' },
          { name: 'COMEX managed-money positioning', reading: 'Connected to free CFTC pipeline', status: 'automatic', source: 'CFTC COT', freshness: 'Weekly', interpretation: 'Crowding matters more in silver because liquidation can be violent.' },
          { name: 'Exchange inventories and premiums', reading: 'Research update required', status: 'pending', source: 'Exchange and physical market reports', freshness: 'Daily/weekly', interpretation: 'Inventory stress and premiums can confirm physical tightness.' },
          { name: 'ETF and bar/coin flows', reading: 'Research update required', status: 'pending', source: 'Issuer and mint disclosures', freshness: 'Daily/monthly', interpretation: 'Investment flows reveal whether the monetary bid is broadening.' }
        ]
      },
      'rare-earths': {
        title: 'Rare-earth supply-chain checklist',
        summary: 'Rare earths must be analysed element by element and through the complete chain from mining to separation, alloying and permanent magnets.',
        items: [
          { name: 'NdPr oxide price', reading: 'Research update required', status: 'pending', source: 'Industry price assessments', freshness: 'Weekly', interpretation: 'The core magnet feedstock is the best high-level signal for magnet economics.' },
          { name: 'Dysprosium and terbium prices', reading: 'Research update required', status: 'pending', source: 'Industry price assessments', freshness: 'Weekly', interpretation: 'Heavy rare-earth pricing reflects high-temperature magnet constraints.' },
          { name: 'China quotas and export controls', reading: 'Research update required', status: 'pending', source: 'Chinese government releases', freshness: 'Event-driven', interpretation: 'Policy changes can alter availability faster than mine supply.' },
          { name: 'FOB China versus ex-China premium', reading: 'Research update required', status: 'pending', source: 'Industry price assessments', freshness: 'Weekly', interpretation: 'A persistent ex-China premium supports regionalisation economics.' },
          { name: 'Magnet lead times and prices', reading: 'Research update required', status: 'pending', source: 'Manufacturers and industry reporting', freshness: 'Monthly', interpretation: 'Downstream confirmation is stronger than oxide prices alone.' },
          { name: 'Ex-China project milestones', reading: 'Research update required', status: 'pending', source: 'Company filings and government grants', freshness: 'Event-driven', interpretation: 'Commissioning, qualification and ramp-up determine real supply-chain diversification.' }
        ]
      }
    },
    eventReactions: [
      {
        id: 'us-cpi-2026-07',
        event: 'US June CPI',
        scheduled: '14 July 2026 · 10:30 pm Melbourne',
        stage: 'Pre-event',
        source: 'US Bureau of Labor Statistics',
        previous: 'Research verification required',
        consensus: 'Not sourced from an official free feed',
        actual: 'Pending',
        scenarios: [
          ['Hotter inflation', 'Yields and USD higher; pressure on gold, bonds and long-duration equities.'],
          ['Broadly in line', 'Current energy-shock and hawkish-policy regime remains the main guide.'],
          ['Softer inflation', 'Lower yields and USD could support gold and duration, subject to growth interpretation.']
        ],
        reactions: { immediate: 'Pending', close: 'Pending', day1: 'Pending', day5: 'Pending' },
        verdict: 'Too early'
      },
      {
        id: 'china-activity-2026-q2',
        event: 'China Q2 and activity data',
        scheduled: 'Mid-July 2026 · Melbourne time to verify',
        stage: 'Pre-event',
        source: 'National Bureau of Statistics of China',
        previous: 'Research verification required',
        consensus: 'Not sourced from an official free feed',
        actual: 'Pending',
        scenarios: [
          ['Broad upside surprise', 'Copper, iron ore, AUD and China-sensitive equities should strengthen together.'],
          ['Mixed composition', 'Asset reaction should depend on property, industrial production and credit details.'],
          ['Broad downside surprise', 'Pressure on bulk commodities, copper, AUD and materials equities.']
        ],
        reactions: { immediate: 'Pending', close: 'Pending', day1: 'Pending', day5: 'Pending' },
        verdict: 'Too early'
      }
    ]
  };
})();
