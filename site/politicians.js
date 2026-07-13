(() => {
  'use strict';
  if (typeof fallback === 'undefined') return;
  fallback.trackers = fallback.trackers || {};

  const houseSources = [
    ['Official House financial disclosures', 'https://disclosures-clerk.house.gov/FinancialDisclosure'],
    ['Quiver congressional trading', 'https://www.quiverquant.com/congresstrading/']
  ];
  const senateSources = [
    ['Official Senate financial disclosures', 'https://efdsearch.senate.gov/search/home/'],
    ['Quiver congressional trading', 'https://www.quiverquant.com/congresstrading/']
  ];

  const context = [
    ['Trade date', 'When the transaction occurred, not when it became public.'],
    ['Filed date', 'When the disclosure was filed and became discoverable.'],
    ['Owner', 'Member, spouse, joint or dependent exactly as reported.'],
    ['Amount', 'A statutory range rather than an exact position size.'],
    ['Portfolio', 'A disclosure-derived estimate reconstructed from annual holdings and later transactions.']
  ];

  const addCongressTracker = ({ id, name, chamber }) => {
    if (fallback.trackers[id]) return;
    fallback.trackers[id] = {
      kind: 'congress',
      displayName: name,
      title: `${name} disclosure tracker`,
      subtitle: 'Public transactions, filing delays and an estimated disclosure-derived portfolio.',
      updated: '14 July 2026',
      cadence: 'Official disclosure portals checked daily; history retained permanently',
      warning: 'Congressional disclosures are delayed and report value ranges rather than exact quantities. A transaction may belong to a spouse, joint account or dependent and must be labelled exactly as filed.',
      stats: [
        ['Source', chamber === 'Senate' ? 'Senate eFD' : 'House disclosures'],
        ['History', 'All verified trades'],
        ['Late filings', 'Still included'],
        ['Portfolio', 'Estimated ledger']
      ],
      trades: [],
      emptyMessage: `No verified ${name} transaction records have been imported into this build yet. The tracker will retain all future and historical filings once verified.`,
      context: [...context],
      sourceLinks: chamber === 'Senate' ? senateSources : houseSources,
      chamber
    };
  };

  fallback.trackers.trump.kind = 'executive';
  fallback.trackers.trump.displayName = 'Donald Trump';
  fallback.trackers.pelosi.kind = 'congress';
  fallback.trackers.pelosi.displayName = 'Nancy Pelosi';
  fallback.trackers.pelosi.chamber = 'House';

  [
    { id: 'tim-moore', name: 'Tim Moore', chamber: 'House' },
    { id: 'dan-meuser', name: 'Dan Meuser', chamber: 'House' },
    { id: 'cleo-fields', name: 'Cleo Fields', chamber: 'House' },
    { id: 'rob-bresnahan', name: 'Rob Bresnahan', chamber: 'House' },
    { id: 'donald-beyer', name: 'Donald Beyer', chamber: 'House' },
    { id: 'sheldon-whitehouse', name: 'Sheldon Whitehouse', chamber: 'Senate' },
    { id: 'josh-gottheimer', name: 'Josh Gottheimer', chamber: 'House' }
  ].forEach(addCongressTracker);

  fallback.trackerOrder = [
    'trump', 'pelosi', 'tim-moore', 'dan-meuser', 'cleo-fields',
    'rob-bresnahan', 'donald-beyer', 'sheldon-whitehouse', 'josh-gottheimer'
  ];
})();
