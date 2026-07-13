(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;

  const configureTracker = (id, tracker) => {
    tracker.trades = Array.isArray(tracker.trades) ? tracker.trades : [];
    tracker.historyPolicy = tracker.historyPolicy || {
      retention: 'All verified disclosed transactions are retained permanently, regardless of age or filing delay.',
      dating: 'Transactions are ordered by the actual trade date. Filing date and disclosure lag remain separate fields.',
      lateFilings: 'A trade disclosed 45 days or more after execution is still imported and inserted into its proper historical position.',
      archive: 'Large histories are stored in annual archive files and loaded in pages so the dashboard stays fast.'
    };

    const isTrump = id === 'trump';
    const isPelosi = id === 'pelosi';
    const displayName = tracker.displayName || tracker.title || id;

    tracker.portfolio = tracker.portfolio || {};
    tracker.portfolio.updated = tracker.portfolio.updated || tracker.updated;
    tracker.portfolio.basis = tracker.portfolio.basis || 'Reconstructed from the latest verified annual holdings disclosure, then adjusted by every subsequent verified purchase, sale, exchange and option exercise.';
    tracker.portfolio.valuation = tracker.portfolio.valuation || 'Estimated from statutory disclosure ranges and public market prices; not an exact brokerage balance.';
    tracker.portfolio.holdings = Array.isArray(tracker.portfolio.holdings) ? tracker.portfolio.holdings : [];
    tracker.portfolio.status = tracker.portfolio.status || 'Reconstruction enabled';

    if (isTrump) {
      tracker.portfolio.emptyMessage = tracker.portfolio.emptyMessage || 'The portfolio ledger is ready, but transaction-level holdings have not yet been fully imported from the public ethics filings. Policy events remain separate from personal financial positions.';
      tracker.portfolio.ownerNote = tracker.portfolio.ownerNote || 'Accounts may be held through trusts or third-party discretionary managers. The dashboard must not imply that an individual transaction was personally selected unless the filing establishes that.';
      tracker.portfolio.sourcePriority = tracker.portfolio.sourcePriority || 'Official ethics filings and annual financial disclosures first; licensed or reputable parsers may assist discovery and reconciliation.';
    } else if (isPelosi) {
      tracker.portfolio.emptyMessage = tracker.portfolio.emptyMessage || 'The portfolio ledger is ready for the official annual holdings baseline and all subsequent Periodic Transaction Reports. Spouse, member, joint and dependent ownership remain separate.';
      tracker.portfolio.ownerNote = tracker.portfolio.ownerNote || 'Many reported transactions belong to Paul Pelosi. The owner field must remain exactly as disclosed and must not be described as Nancy Pelosi personally trading.';
      tracker.portfolio.sourcePriority = tracker.portfolio.sourcePriority || 'Official House annual disclosures and Periodic Transaction Reports first; third-party parsers may assist discovery but cannot override the filing.';
    } else {
      tracker.portfolio.emptyMessage = tracker.portfolio.emptyMessage || `The ${displayName} portfolio ledger is ready for an official annual-disclosure baseline and all later verified transactions.`;
      tracker.portfolio.ownerNote = tracker.portfolio.ownerNote || 'Member, spouse, joint and dependent ownership must remain distinct. The tracker must not attribute a spouse or account transaction directly to the politician.';
      tracker.portfolio.sourcePriority = tracker.portfolio.sourcePriority || 'Official House or Senate disclosure records first; third-party parsers may assist discovery but cannot override the filing.';
    }
  };

  Object.entries(fallback.trackers).forEach(([id, tracker]) => configureTracker(id, tracker));
})();
