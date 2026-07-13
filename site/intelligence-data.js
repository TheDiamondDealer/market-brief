fallback.newsFeed = {
  asOf: '13 July 2026, Melbourne close',
  delayNote: 'Delayed daily digest — refreshed after the research run, not a real-time wire.',
  items: [
    {
      id: 'hormuz-oil-rates',
      category: 'Energy',
      impact: 'High',
      status: 'Developing',
      time: '13 Jul 2026',
      headline: 'Hormuz risk is transmitting through oil, inflation and rates',
      summary: 'Renewed US–Iran escalation and the closure claim lifted crude. The important second-order effect is higher inflation and tighter-policy pricing rather than a simple safe-haven move.',
      source: 'Reuters',
      sourceUrl: 'https://www.reuters.com/business/media-telecom/global-markets-global-markets-2026-07-13/',
      assets: [
        { name: 'Brent', direction: 'up', reason: 'Physical-flow risk and a larger geopolitical premium.' },
        { name: 'US 10Y', direction: 'up', reason: 'Higher energy inflation preserves tightening risk.' },
        { name: 'DXY', direction: 'up', reason: 'Higher relative US yields support the dollar.' },
        { name: 'Gold', direction: 'down', reason: 'Dollar and yield pressure is overpowering haven demand.' },
        { name: 'Nasdaq', direction: 'down', reason: 'Higher discount rates pressure long-duration equities.' }
      ],
      channels: [
        ['First order', 'Oil and refined products rise on supply risk.'],
        ['Second order', 'Inflation expectations and Fed-hike pricing rise.'],
        ['Cross asset', 'Yields and USD firm; gold and duration assets weaken.'],
        ['Invalidation', 'Gulf flows improve and Brent closes back below the de-escalation level.']
      ]
    },
    {
      id: 'gold-haven-failure',
      category: 'Precious',
      impact: 'High',
      status: 'Price-confirmed',
      time: '13 Jul 2026',
      headline: 'Gold failed the textbook safe-haven test',
      summary: 'Gold fell during geopolitical escalation because the market treated the shock as inflationary and hawkish. This confirms the active sign-flip in the regime model.',
      source: 'Reuters',
      sourceUrl: 'https://www.reuters.com/world/india/gold-slides-over-1-oil-surges-strait-hormuz-closure-fears-2026-07-13/',
      assets: [
        { name: 'Gold', direction: 'down', reason: 'Higher nominal and real yields raise the opportunity cost.' },
        { name: 'Silver', direction: 'down', reason: 'Higher beta plus industrial-risk exposure.' },
        { name: 'DXY', direction: 'up', reason: 'Safe-haven dollar demand and rate support.' },
        { name: 'Bonds', direction: 'down', reason: 'Higher inflation expectations lift yields and lower prices.' }
      ],
      channels: [
        ['Rates', 'Higher yields reduce the appeal of non-yielding precious metals.'],
        ['Currency', 'A stronger USD makes dollar-priced metals more expensive offshore.'],
        ['Positioning', 'Crowded haven positioning can liquidate when the expected reaction fails.'],
        ['Override test', 'Gold rising with oil, DXY and yields for two sessions would challenge this read.']
      ]
    },
    {
      id: 'asia-semis',
      category: 'Equities',
      impact: 'High',
      status: 'Price-confirmed',
      time: '13 Jul 2026',
      headline: 'Asian semiconductors became the liquidity source',
      summary: 'The oil and rate shock hit crowded semiconductor exposure. AI enthusiasm did not insulate the most duration-sensitive parts of the market.',
      source: 'Reuters',
      sourceUrl: 'https://www.reuters.com/business/media-telecom/global-markets-global-markets-2026-07-13/',
      assets: [
        { name: 'Nikkei', direction: 'down', reason: 'Weak yen benefits are offset by imported inflation and higher global yields.' },
        { name: 'KOSPI', direction: 'down', reason: 'Concentrated semiconductor exposure amplifies risk reduction.' },
        { name: 'Nasdaq', direction: 'down', reason: 'Long-duration multiples are sensitive to the discount-rate shock.' },
        { name: 'VIX', direction: 'up', reason: 'Geopolitical and policy uncertainty lift hedging demand.' }
      ],
      channels: [
        ['Valuation', 'Higher yields compress long-duration equity multiples.'],
        ['Crowding', 'Popular AI positions are sold first when investors need liquidity.'],
        ['Margins', 'Higher energy and freight costs threaten downstream earnings.'],
        ['Next test', 'Breadth and credit spreads determine whether this is rotation or broader stress.']
      ]
    },
    {
      id: 'asx-aud-divergence',
      category: 'Macro',
      impact: 'Medium',
      status: 'Diverging',
      time: '13 Jul 2026',
      headline: 'ASX resilience and a weaker AUD are telling different stories',
      summary: 'Energy and resources cushioned the index while the currency weakened. The equity level looks resilient, but AUD still signals global risk aversion and imported-inflation pressure.',
      source: 'Australian market report',
      sourceUrl: 'https://www.theaustralian.com.au/business/markets/asx-200-to-open-higher-as-usiran-middle-east-strikes-continue-corp-travels-new-low/live-coverage/125fed1deba2237f23b495b7823f5b32',
      assets: [
        { name: 'ASX 200', direction: 'up', reason: 'Energy and materials weight cushions the headline index.' },
        { name: 'AUD/USD', direction: 'down', reason: 'Global risk aversion and stronger USD dominate.' },
        { name: 'Energy stocks', direction: 'up', reason: 'Higher realised oil prices support earnings.' },
        { name: 'Rate-sensitive stocks', direction: 'down', reason: 'Imported inflation keeps domestic rates restrictive.' }
      ],
      channels: [
        ['Index mix', 'Resources can lift the ASX even when the broader risk tone is weak.'],
        ['Currency', 'A softer AUD boosts translated offshore revenue but raises import costs.'],
        ['Inflation', 'Energy imports can extend RBA tightening pressure.'],
        ['Confirmation', 'Banks, materials and energy breadth must support the index move.']
      ]
    }
  ]
};

fallback.trackers = {
  trump: {
    title: 'Trump policy & disclosure tracker',
    subtitle: 'Market-moving policy, tariff actions and public financial disclosures.',
    updated: '13 July 2026',
    cadence: 'Policy checked daily; financial disclosures update when filed',
    warning: 'Policy events can be tracked daily. Personal portfolio information is disclosure-based, delayed and may reflect third-party discretionary accounts rather than Trump-directed trades.',
    stats: [
      ['Tracker type', 'Policy + disclosures'],
      ['Policy lag', 'Daily digest'],
      ['Trade data', 'Public filings only'],
      ['Current regime link', 'Oil → inflation → rates']
    ],
    policyEvents: [
      {
        date: '13 Jul 2026',
        type: 'Geopolitics',
        status: 'Developing',
        title: 'US–Iran escalation keeps the Hormuz risk premium active',
        detail: 'The market channel is oil higher, inflation risk higher, yields and USD firmer, with pressure on gold-duration behaviour and equities.',
        assets: ['Brent ↑', 'US 10Y ↑', 'DXY ↑', 'Gold ↓', 'Nasdaq ↓'],
        source: 'Reuters',
        sourceUrl: 'https://www.reuters.com/business/media-telecom/global-markets-global-markets-2026-07-13/'
      }
    ],
    tariffMatrix: [
      ['China', 'CNH/AUD downside; USD support', 'Technology and manufacturing split', 'Copper/soybeans pressured; gold depends on rates'],
      ['EU', 'EUR downside; USD support', 'European autos and luxury exposed', 'Risk-off support for gold unless yields dominate'],
      ['Canada', 'CAD downside', 'Energy, lumber and autos exposed', 'Oil mixed; lumber sensitive'],
      ['Mexico', 'MXN downside', 'Auto supply chains pressured; nearshoring beneficiaries', 'Industrial inputs and transport costs'],
      ['Steel / aluminium', 'Limited direct FX effect', 'Domestic producers benefit; users face margin pressure', 'Steel/aluminium prices higher'],
      ['Universal', 'Broad USD support; EM FX pressure', 'Risk-off with domestic substitution winners', 'Copper pressure; inflation and gold channels compete']
    ],
    disclosure: {
      headline: '2025 annual disclosure shows unusually high transaction volume',
      summary: 'Public reporting released in July 2026 was described as containing 21,285 stock trades across third-party-managed discretionary accounts. A transaction-level import is not yet connected to this dashboard.',
      labels: ['21,285 reported trades', 'Third-party discretionary accounts', 'Not real time', 'Transaction import pending'],
      source: 'Business Insider summary',
      sourceUrl: 'https://www.businessinsider.com/trump-portfolio-stock-trades-beat-market-analysis-2026-7'
    },
    sourceLinks: [
      ['White House presidential actions', 'https://www.whitehouse.gov/presidential-actions/'],
      ['Quiver Trump tracker', 'https://www.quiverquant.com/Donald-Trump-Stock-Trades/'],
      ['Quiver API', 'https://api.quiverquant.com/']
    ]
  },
  pelosi: {
    title: 'Nancy Pelosi disclosure tracker',
    subtitle: 'Periodic transaction reports, owner, filing lag and market context.',
    updated: '13 July 2026',
    cadence: 'Checked daily; updates only when a verified disclosure appears',
    warning: 'Congressional transaction reports are delayed disclosures, often filed weeks after the trade. Owner may be the member, spouse or dependent. Do not treat the filing date as the trade date.',
    stats: [
      ['Source', 'House PTR disclosures'],
      ['Legal framework', 'STOCK Act'],
      ['Maximum common lag', 'Up to 45 days'],
      ['Portfolio note', 'Spouse activity must be labelled']
    ],
    trades: [],
    emptyMessage: 'No new verified Pelosi PTR has been imported into this seeded build. The table and daily update rules are ready; the next official filing can be added without redesigning the page.',
    context: [
      ['Trade date', 'When the transaction occurred.'],
      ['Filed date', 'When the disclosure became public.'],
      ['Owner', 'Member, spouse, joint or dependent.'],
      ['Amount', 'Reported as a statutory range, not an exact value.'],
      ['Market impact', 'We calculate the move only after the disclosure became public to avoid look-ahead bias.']
    ],
    sourceLinks: [
      ['House financial disclosures', 'https://disclosures-clerk.house.gov/FinancialDisclosure'],
      ['Quiver Pelosi profile', 'https://www.quiverquant.com/congresstrading/politician/Nancy%20Pelosi-P000197'],
      ['Quiver API', 'https://api.quiverquant.com/']
    ]
  }
};
