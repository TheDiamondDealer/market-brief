window.politicalDisclosureData={"generatedAt":null,"generatedAtHuman":"Awaiting first official import","methodology":"Official House PTR PDFs and Senate eFD PTR pages. Existing verified trades are retained during source failures.","trackers":{},"sourceStatus":{"house":{"filingsDiscovered":0,"errors":[]},"senate":{"errors":[]},"parsing":{"errors":[]}}};
(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;
  const source = window.politicalDisclosureData || {trackers:{}};
  Object.entries(source.trackers || {}).forEach(([id, imported]) => {
    const tracker = fallback.trackers[id];
    if (!tracker) return;
    tracker.trades = Array.isArray(imported.trades) ? imported.trades : [];
    tracker.updated = imported.updated || source.generatedAtHuman || tracker.updated;
    tracker.importStatus = imported.status;
    tracker.emptyMessage = imported.emptyMessage || tracker.emptyMessage;
    tracker.portfolio = Object.assign({}, tracker.portfolio || {}, imported.portfolio || {});
  });
})();
