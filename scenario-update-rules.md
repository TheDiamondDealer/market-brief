# Scenario Lab Update Rules

After every successful daily market brief, review `site/scenario-lab.js` and update only the data-driven parts when verified facts changed.

For each supported asset:

- update the latest verified research reference price and date
- update target presets using active thresholds and nearby decision zones
- refresh upside and downside requirements from the current regime
- preserve separate confirmation and invalidation tests
- add or remove macro catalysts only when the event calendar changes
- never read or scrape prices from the embedded TradingView widget

The scenario answer must state:

- percentage distance from the latest verified research reference
- macro conditions required
- physical or positioning conditions required
- relevant scheduled events
- confirmation evidence
- invalidation evidence
- that the result is conditional scenario analysis, not a forecast or recommendation

TradingView widgets are visual context only. Official/free data sources and the repository research remain the source of record.
