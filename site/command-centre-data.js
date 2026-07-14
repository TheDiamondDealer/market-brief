(() => {
  'use strict';
  if (typeof fallback === 'undefined') return;

  fallback.commandCentre = {
    updated: '15 July 2026, 08:30 AEST',
    risk: {
      state: 'Dovish CPI countershock / live energy shock',
      score: 61,
      confidence: 'Medium-high',
      summary: 'Softer US inflation broke the rates-dollar confirmation loop, but Brent and European gas remain above trigger levels with physical Gulf constraints.',
      contradiction: 'US equities, gold, copper and iron ore accepted the dovish signal even as oil and gas strengthened.',
      inputs: [
        { name: 'Energy shock', reading: 'Brent $84.73; TTF >€52', score: 2, reason: 'Physical-flow risk preserves the inflation impulse.' },
        { name: 'Rates', reading: 'US 10Y 4.589%', score: 0, reason: 'Nominal and real yields fell after CPI but remain in warning territory.' },
        { name: 'Fed pricing', reading: 'Sep hike ~53%', score: -1, reason: 'A roughly 22-point one-day fall materially softened the policy impulse.' },
        { name: 'US dollar', reading: 'DXY 100.94', score: 0, reason: 'The dollar fell but remains inside its decision zone.' },
        { name: 'Risk assets', reading: 'Selective relief', score: -1, reason: 'Nasdaq and S&P rose while ASX breadth remained split.' }
      ],
      changeConditions: [
        'De-escalation requires Brent below $76 with improving Gulf flows.',
        'September hike pricing below 50% and the US 10-year below 4.45% would weaken the hawkish leg.',
        'DXY below 100 plus gold above $4,150 would challenge the rates-dominant sign-flip.'
      ]
    },
    nextEvent: {
      name: 'US June PPI',
      time: 'Wednesday 15 July · 10:30 pm Melbourne',
      importance: 'High',
      logic: 'The cleanest near-term test of whether the CPI countershock survives pipeline inflation and renewed energy pressure.'
    },
    changes: [
      'September hike probability fell from roughly 75% to 53%, triggering the daily move threshold but not the below-50% invalidation.',
      'Gold rebounded to the lower edge of its warning zone as real yields and DXY fell.',
      'Brent closed above $80 with physical-flow confirmation; TTF also held above €52.',
      'Copper cleared $6.30 and iron ore CNY760, but China activity still has to confirm physical demand.',
      'The regime remains intact; price confirmation is now divergent rather than reinforcing.'
    ]
  };

  fallback.assetBiases = [
    { id:'gold', name:'Gold', group:'Precious', reference:'$4,051.79', bias:'Neutral / recovering', confidence:64, total:1, primaryDriver:'Lower real yields and DXY', cot:'CFTC week ended 7 Jul; verify dashboard percentile', nextEvent:'US PPI', changeCondition:'Bullish above $4,150; bearish close below $4,050 with DXY/yield confirmation.', productId:'gold', components:[{name:'Macro',score:1,reason:'CPI delivered a dovish countershock.'},{name:'Rates',score:1,reason:'Nominal and real yields fell.'},{name:'Positioning',score:0,reason:'Weekly COT is lagged and not the daily driver.'},{name:'Cross-asset',score:-1,reason:'Brent strength can revive the hawkish channel.'}] },
    { id:'oil', name:'Brent oil', group:'Energy', reference:'$84.73', bias:'Bullish', confidence:84, total:6, primaryDriver:'Hormuz physical-flow constraint', cot:'CFTC week ended 7 Jul; lagged', nextEvent:'EIA petroleum report', changeCondition:'Close below $76 with improving flows and softer spreads.', productId:'oil', components:[{name:'Macro',score:1,reason:'Softer USD is supportive.'},{name:'Physical',score:2,reason:'Traffic remains impaired and price closed above trigger.'},{name:'Positioning',score:1,reason:'No verified crowding override in the daily frame.'},{name:'Cross-asset',score:2,reason:'European gas confirms regional supply stress.'}] },
    { id:'copper', name:'Copper', group:'Base metals', reference:'$6.32/lb', bias:'Bullish / unconfirmed', confidence:58, total:2, primaryDriver:'Lower USD plus China anticipation', cot:'CFTC week ended 7 Jul; lagged', nextEvent:'China Q2 and activity data', changeCondition:'Sustain above $6.30 with aligned inventories, premiums and China demand.', productId:'copper', components:[{name:'Macro',score:1,reason:'Lower DXY and yields eased financial conditions.'},{name:'China',score:1,reason:'Iron ore and CNH moved constructively ahead of data.'},{name:'Positioning',score:0,reason:'COT is not a same-day confirmation.'},{name:'Physical',score:0,reason:'Inventory and premium confirmation is incomplete.'}] },
    { id:'silver', name:'Silver', group:'Precious', reference:'$58.79', bias:'Recovering', confidence:60, total:2, primaryDriver:'Gold/rates relief plus copper', cot:'CFTC week ended 7 Jul; lagged', nextEvent:'US PPI / China data', changeCondition:'Sustain gains with gold above $4,150 and copper physically confirmed.', productId:'silver', components:[{name:'Macro',score:1,reason:'Softer CPI supports precious metals.'},{name:'Rates',score:1,reason:'Real yields fell.'},{name:'Industrial',score:1,reason:'Copper and iron ore strengthened.'},{name:'Cross-asset',score:-1,reason:'Energy inflation can reverse the rates relief.'}] },
    { id:'usdjpy', name:'USD/JPY', group:'FX', reference:'162.24', bias:'Bullish / unstable', confidence:54, total:2, primaryDriver:'Structural yield differential', cot:'FX COT week ended 7 Jul; lagged', nextEvent:'Warsh Senate testimony', changeCondition:'Close below 160 or verified intervention.', components:[{name:'Rates',score:0,reason:'US yields fell, removing fresh confirmation.'},{name:'Policy',score:1,reason:'Japan-US policy gap remains wide.'},{name:'Positioning',score:0,reason:'Crowding is not verified in the daily frame.'},{name:'Cross-asset',score:1,reason:'Price held above 162 despite lower DXY.'}] },
    { id:'us10y', name:'US 10-year yield', group:'Rates', reference:'4.589%', bias:'Neutral / lower', confidence:66, total:-2, primaryDriver:'CPI versus oil', cot:'Treasury futures COT week ended 7 Jul; lagged', nextEvent:'US PPI', changeCondition:'Below 4.45% confirms easing; above 4.60% with DXY strength restores hawkish confirmation.', components:[{name:'Inflation',score:0,reason:'Soft CPI conflicts with renewed energy inflation.'},{name:'Policy',score:-1,reason:'Hike odds fell sharply.'},{name:'Growth',score:0,reason:'China and US demand data are still pending.'},{name:'Cross-asset',score:-1,reason:'DXY fell and gold recovered.'}] }
  ];
})();
