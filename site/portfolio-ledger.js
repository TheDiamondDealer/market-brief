(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;

  const configureTracker = (id, options) => {
    const tracker = fallback.trackers[id];
    if (!tracker) return;

    tracker.trades = Array.isArray(tracker.trades) ? tracker.trades : [];
    tracker.historyPolicy = {
      retention: 'All verified disclosed transactions are retained permanently, regardless of age or filing delay.',
      dating: 'Transactions are ordered by the actual trade date. Filing date and disclosure lag remain separate fields.',
      lateFilings: 'A trade disclosed 45 days or more after execution is still imported and inserted into its proper historical position.',
      archive: 'Large histories are stored in annual archive files and loaded in pages so the dashboard stays fast.'
    };

    tracker.portfolio = tracker.portfolio || {};
    tracker.portfolio.updated = tracker.portfolio.updated || tracker.updated;
    tracker.portfolio.basis = tracker.portfolio.basis || 'Reconstructed from the latest verified annual holdings disclosure, then adjusted by every subsequent verified purchase, sale, exchange and option exercise.';
    tracker.portfolio.valuation = tracker.portfolio.valuation || 'Estimated from statutory disclosure ranges and public market prices; not an exact brokerage balance.';
    tracker.portfolio.holdings = Array.isArray(tracker.portfolio.holdings) ? tracker.portfolio.holdings : [];
    tracker.portfolio.emptyMessage = tracker.portfolio.emptyMessage || options.emptyMessage;
    tracker.portfolio.ownerNote = tracker.portfolio.ownerNote || options.ownerNote;
    tracker.portfolio.status = tracker.portfolio.status || 'Reconstruction enabled';
    tracker.portfolio.sourcePriority = tracker.portfolio.sourcePriority || options.sourcePriority;
  };

  configureTracker('trump', {
    emptyMessage: 'The portfolio ledger is ready, but transaction-level holdings have not yet been fully imported from the public ethics filings. Policy events remain separate from personal financial positions.',
    ownerNote: 'Accounts may be held through trusts or third-party discretionary managers. The dashboard must not imply that an individual transaction was personally selected unless the filing establishes that.',
    sourcePriority: 'Official ethics filings and annual financial disclosures first; licensed or reputable parsers may assist discovery and reconciliation.'
  });

  configureTracker('pelosi', {
    emptyMessage: 'The portfolio ledger is ready for the official annual holdings baseline and all subsequent Periodic Transaction Reports. Spouse, member, joint and dependent ownership remain separate.',
    ownerNote: 'Many reported transactions belong to Paul Pelosi. The owner field must remain exactly as disclosed and must not be described as Nancy Pelosi personally trading.',
    sourcePriority: 'Official House annual disclosures and Periodic Transaction Reports first; third-party parsers may assist discovery but cannot override the filing.'
  });
})();
