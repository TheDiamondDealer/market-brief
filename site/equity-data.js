(() => {
  window.equityMarketData = {"schemaVersion":1,"generatedAtUtc":"2026-07-15T04:40:52Z","provider":{"id":"twelve-data","name":"Twelve Data","sourceUrl":"https://twelvedata.com/","access":"credentialed-server-side","licenseMode":"private-internal-use-only","status":"unavailable","disclaimer":"Provider data is collected by GitHub Actions for an access-controlled internal dashboard. Do not enable while the repository or deployed site is publicly accessible."},"collection":{"mode":"disabled","status":"unknown","successCount":0,"failureCount":0,"errors":[]},"watchlist":[],"sourceStatus":[],"methodology":{}};
  const publish = (data) => { window.equityMarketData = data; window.dispatchEvent(new CustomEvent('marketbrief:equity-data', { detail: data })); };
  fetch('data/equity-market-data.json', { cache: 'no-store', credentials: 'same-origin' })
    .then((response) => { if (!response.ok) throw new Error(`Equity cache HTTP ${response.status}`); return response.json(); })
    .then(publish)
    .catch((error) => { window.equityMarketData.collection.status = 'failed'; window.equityMarketData.collection.errors = [String(error.message || error)]; publish(window.equityMarketData); });
})();
