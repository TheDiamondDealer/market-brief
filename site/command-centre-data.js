(() => {
  'use strict';
  if (typeof fallback === 'undefined') return;

  fallback.commandCentre = {
    updated: fallback.generatedAt,
    risk: {
      state: 'Risk-off inflation shock',
      score: 74,
      confidence: 'High',
      summary: 'Oil, yields and the US dollar are reinforcing one another while gold and bonds are failing to provide their normal defensive offset.',
      contradiction: 'The ASX remains comparatively resilient because energy and materials exposure is cushioning the index.',
      inputs: [
        { name: 'Energy shock', reading: 'Brent near trigger', score: 2, reason: 'Higher crude is feeding inflation and policy-tightening risk.' },
        { name: 'Rates', reading: 'US 10Y near 4.60%', score: 2, reason: 'Higher discount rates pressure duration assets and non-yielding metals.' },
        { name: 'US dollar', reading: 'Firm', score: 1, reason: 'Yield support and defensive demand reinforce the dollar.' },
        { name: 'Equity breadth', reading: 'Fragile', score: 1, reason: 'Headline indices are masking weakness in crowded growth exposure.' },
        { name: 'Defensive assets', reading: 'Diverging', score: 1, reason: 'Gold and bonds are not confirming a textbook haven response.' }
      ],
      changeConditions: [
        'Brent closes below $76 as Gulf flows improve.',
        'US 10-year yield closes below 4.45% and hike pricing falls materially.',
        'DXY falls below 100 while gold and equities recover confirmation levels.'
      ]
    },
    nextEvent: {
      name: 'US June CPI',
      time: 'Tuesday 14 July · 10:30 pm Melbourne',
      importance: 'High',
      logic: 'The cleanest test of whether the oil shock becomes a persistent inflation and rates impulse.'
    },
    changes: [
      'Gold moved into its warning zone while yields and DXY remained the dominant confirmation set.',
      'Brent approached the $80 headline trigger, but physical-market confirmation is still required.',
      'USD/JPY touched its trigger above 162, increasing intervention and reversal risk.',
      'The regime remains intact and strengthening rather than shifting.'
    ]
  };

  fallback.assetBiases = [
    {
      id: 'gold', name: 'Gold', group: 'Precious', reference: '~$4,072', bias: 'Bearish', confidence: 78,
      total: -5, primaryDriver: 'US yields and DXY', cot: 'Free CFTC import pending', nextEvent: 'US CPI',
      changeCondition: 'Close above $4,150 with yields and DXY falling.', productId: 'gold',
      components: [
        { name: 'Macro', score: -1, reason: 'Inflation risk is preserving a restrictive policy outlook.' },
        { name: 'Rates', score: -2, reason: 'Higher nominal and real yields raise gold’s opportunity cost.' },
        { name: 'Positioning', score: 0, reason: 'COT percentile will populate after the free CFTC pipeline is connected.' },
        { name: 'Cross-asset', score: -2, reason: 'DXY and yields are confirming downside while haven demand is failing.' }
      ]
    },
    {
      id: 'oil', name: 'Brent oil', group: 'Energy', reference: '$79.31', bias: 'Bullish', confidence: 76,
      total: 5, primaryDriver: 'Gulf supply risk', cot: 'Free CFTC import pending', nextEvent: 'Physical flows / inventories',
      changeCondition: 'Close below $76 with improving flows and softer time spreads.', productId: 'oil',
      components: [
        { name: 'Macro', score: 1, reason: 'Inflation sensitivity makes crude the first-order regime driver.' },
        { name: 'Physical', score: 2, reason: 'Supply-risk premium remains active near the headline trigger.' },
        { name: 'Positioning', score: 0, reason: 'Managed-money percentile will populate from CFTC data.' },
        { name: 'Cross-asset', score: 2, reason: 'Yields, DXY and inflation expectations are validating the oil impulse.' }
      ]
    },
    {
      id: 'copper', name: 'Copper', group: 'Base metals', reference: '~$6.22/lb', bias: 'Neutral / bearish', confidence: 54,
      total: -2, primaryDriver: 'China demand uncertainty', cot: 'Free CFTC import pending', nextEvent: 'China activity data',
      changeCondition: 'Close above $6.30 with falling inventories and aligned LME/ShFE strength.', productId: 'copper',
      components: [
        { name: 'Macro', score: -1, reason: 'Global financial conditions are restrictive.' },
        { name: 'China', score: -1, reason: 'Policy support has not yet produced broad physical-demand confirmation.' },
        { name: 'Positioning', score: 0, reason: 'COT and exchange-positioning data are not yet loaded.' },
        { name: 'Physical', score: 0, reason: 'Inventories and premiums need to confirm a durable direction.' }
      ]
    },
    {
      id: 'silver', name: 'Silver', group: 'Precious', reference: '$59.56', bias: 'Bearish', confidence: 69,
      total: -5, primaryDriver: 'Rates plus industrial risk', cot: 'Free CFTC import pending', nextEvent: 'US CPI / China data',
      changeCondition: 'Gold stabilises, yields fall and copper/industrial indicators improve.', productId: 'silver',
      components: [
        { name: 'Macro', score: -1, reason: 'Restrictive policy expectations weigh on precious metals.' },
        { name: 'Rates', score: -2, reason: 'Silver inherits gold’s sensitivity to yields and the dollar.' },
        { name: 'Industrial', score: -1, reason: 'China and manufacturing confirmation remain mixed.' },
        { name: 'Cross-asset', score: -1, reason: 'Gold weakness and risk reduction increase silver’s downside beta.' }
      ]
    },
    {
      id: 'usdjpy', name: 'USD/JPY', group: 'FX', reference: '~162.10', bias: 'Bullish / unstable', confidence: 66,
      total: 4, primaryDriver: 'Yield differential', cot: 'FX COT import pending', nextEvent: 'US CPI / intervention risk',
      changeCondition: 'Rapid close below 160 or verified intervention.',
      components: [
        { name: 'Rates', score: 2, reason: 'US-Japan yield differentials still favour the dollar.' },
        { name: 'Policy', score: 1, reason: 'US tightening risk contrasts with constrained Japanese policy.' },
        { name: 'Positioning', score: 0, reason: 'CFTC yen positioning will populate in the free-data pipeline.' },
        { name: 'Cross-asset', score: 1, reason: 'DXY strength confirms the move, but intervention risk limits confidence.' }
      ]
    },
    {
      id: 'us10y', name: 'US 10-year yield', group: 'Rates', reference: '~4.58%', bias: 'Higher yields', confidence: 80,
      total: 5, primaryDriver: 'Inflation and hike pricing', cot: 'Treasury futures COT pending', nextEvent: 'US CPI',
      changeCondition: 'Close below 4.45% with lower inflation and policy expectations.',
      components: [
        { name: 'Inflation', score: 2, reason: 'The oil shock is lifting the inflation risk premium.' },
        { name: 'Policy', score: 2, reason: 'The market is preserving tightening optionality.' },
        { name: 'Growth', score: 0, reason: 'Growth evidence is not the primary driver of the current move.' },
        { name: 'Cross-asset', score: 1, reason: 'DXY strength and gold weakness confirm the discount-rate channel.' }
      ]
    }
  ];
})();
