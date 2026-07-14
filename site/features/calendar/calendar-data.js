(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const evidence = core.adapters?.evidence?.() || window.marketResearchData || {};
  const ASSETS = ['Gold', 'Silver', 'Copper', 'Brent', 'WTI', 'Bonds', 'US 10Y', 'DXY', 'USD', 'AUD', 'AUD/USD', 'Nasdaq', 'ASX 200', 'Iron ore', 'China-sensitive equities'];

  function scheduledAt(label = '') {
    const match = String(label).match(/^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s+·\s+(\d{1,2}):(\d{2})\s+(am|pm)\s+Melbourne$/i);
    if (!match) return null;
    const months = { january: '01', february: '02', march: '03', april: '04', may: '05', june: '06', july: '07', august: '08', september: '09', october: '10', november: '11', december: '12' };
    const month = months[match[2].toLowerCase()];
    if (!month) return null;
    let hour = Number(match[4]) % 12;
    if (match[6].toLowerCase() === 'pm') hour += 12;
    const offset = ['10', '11', '12', '01', '02', '03'].includes(month) ? '+11:00' : '+10:00';
    return `${match[3]}-${month}-${String(match[1]).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${match[5]}:00${offset}`;
  }

  function valueRecord(value, sourceName, { pending = false } = {}) {
    const text = value === null || value === undefined ? '' : String(value);
    if (pending || /^pending$/i.test(text)) return { value: text || null, status: 'pending', source: sourceName || null };
    if (/not sourced|verification required|to verify/i.test(text)) return { value: text, status: 'not-sourced', source: null };
    return { value, status: 'sourced', source: sourceName || null };
  }

  function reaction(label, value) {
    const text = String(value || 'Pending');
    const pending = /^pending$/i.test(text);
    return { label, value: text, status: pending ? 'pending' : 'observed', observedAt: null };
  }

  function assetsFor(event) {
    const text = JSON.stringify(event).toLowerCase();
    return ASSETS.filter((asset) => text.includes(asset.toLowerCase()));
  }

  function stateFor(actual, reactions) {
    const allObserved = Object.values(reactions).every((entry) => entry.status === 'observed');
    if (allObserved) return 'reaction-complete';
    if (actual.status === 'sourced') return 'released';
    return 'upcoming';
  }

  function adaptItem(event = {}) {
    const time = scheduledAt(event.scheduled);
    const reactions = {
      immediate: reaction('Immediate', event.reactions?.immediate),
      close: reaction('Melbourne / primary close', event.reactions?.close),
      day1: reaction('+1 trading day', event.reactions?.day1),
      day5: reaction('+5 trading days', event.reactions?.day5)
    };
    const actual = valueRecord(event.actual, event.source, { pending: /^pending$/i.test(String(event.actual || '')) });
    return {
      id: String(event.id || 'unnamed-event'),
      name: String(event.event || 'Unnamed event'),
      importance: 'research-priority',
      scheduledLabel: String(event.scheduled || 'Time not supplied'),
      scheduledAt: time,
      timeStatus: time ? 'verified-melbourne' : 'needs-verification',
      state: stateFor(actual, reactions),
      source: { name: String(event.source || 'Official source not specified'), url: null },
      assets: assetsFor(event),
      previous: valueRecord(event.previous, event.source),
      consensus: valueRecord(event.consensus, null),
      actual,
      scenarios: (event.scenarios || []).map((item) => ({ label: String(item[0] || 'Scenario'), interpretation: String(item[1] || 'Interpretation not supplied') })),
      reactions,
      verdict: String(event.verdict || 'Too early')
    };
  }

  function adapt(items = evidence.eventReactions || []) {
    const dataset = {
      schemaVersion: 1,
      timezone: 'Australia/Melbourne',
      generatedAt: evidence.updated || null,
      events: items.map(adaptItem)
    };
    window.marketCalendarData = dataset;
    core.store?.setSlice('calendar', dataset, { source: 'research:event-reaction-adapter' });
    return dataset;
  }

  function get() { return core.store?.getSlice('calendar') || window.marketCalendarData || adapt(); }
  core.calendar = Object.freeze({ adapt, adaptItem, get, scheduledAt });
  adapt();
})();
