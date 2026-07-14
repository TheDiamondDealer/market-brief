(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const research = core.adapters?.research?.() || (typeof fallback !== 'undefined' ? fallback : {});

  function slug(value = '') {
    return String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'unknown-asset';
  }

  function status(value = '') {
    const text = String(value).trim().toLowerCase();
    if (text.includes('price-confirmed') || text === 'confirmed') return 'confirmed';
    if (text.includes('developing')) return 'developing';
    if (text.includes('resolved')) return 'resolved';
    if (text.includes('diverg')) return 'diverging';
    return 'unclear';
  }

  function magnitude(value = '') {
    const text = String(value).trim().toLowerCase();
    return ['high', 'medium', 'low'].includes(text) ? text : 'unclear';
  }

  function direction(value = '') {
    const text = String(value).trim().toLowerCase();
    return ['up', 'down', 'mixed'].includes(text) ? text : 'unclear';
  }

  function eventDate(value = '') {
    const match = String(value).trim().match(/^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})$/);
    if (!match) return null;
    const months = { jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06', jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12' };
    const month = months[match[2].toLowerCase()];
    return month ? `${match[3]}-${month}-${String(match[1]).padStart(2, '0')}` : null;
  }

  function channels(item) {
    return (Array.isArray(item.channels) ? item.channels : []).map((entry) => ({
      label: String(Array.isArray(entry) ? entry[0] : entry?.label || '').trim() || 'Channel',
      detail: String(Array.isArray(entry) ? entry[1] : entry?.detail || '').trim() || 'Detail not specified in the legacy item.'
    }));
  }

  function findChannel(entries, patterns) {
    const match = entries.find((entry) => patterns.some((pattern) => pattern.test(entry.label)));
    return match?.detail || null;
  }

  function confirmationFor(itemStatus, entries) {
    const explicit = findChannel(entries, [/confirmation/i, /next test/i]);
    if (explicit) return explicit;
    if (itemStatus === 'confirmed') return 'The curated item describes contemporaneous price action as confirmation.';
    return 'Confirmation condition was not specified in the legacy item.';
  }

  function invalidationFor(entries) {
    return findChannel(entries, [/invalidation/i, /override test/i]) || 'Invalidation condition was not specified in the legacy item.';
  }

  function adaptItem(item = {}) {
    const normalizedChannels = channels(item);
    const normalizedStatus = status(item.status);
    const confirmation = confirmationFor(normalizedStatus, normalizedChannels);
    const invalidation = invalidationFor(normalizedChannels);
    const interpretations = (Array.isArray(item.assets) ? item.assets : []).map((asset) => ({
      assetId: slug(asset.name),
      assetName: String(asset.name || 'Unknown asset'),
      direction: direction(asset.direction),
      magnitude: magnitude(item.impact),
      horizon: 'unclear',
      confidence: 'unclear',
      mechanism: String(asset.reason || 'Mechanism was not specified in the legacy item.'),
      confirmation,
      invalidation
    }));
    return {
      id: String(item.id || slug(item.headline || 'news-item')),
      category: String(item.category || 'Uncategorised'),
      status: normalizedStatus,
      eventDate: eventDate(item.time),
      timeLabel: String(item.time || ''),
      headline: String(item.headline || 'Untitled curated item'),
      summary: String(item.summary || 'Summary unavailable.'),
      sources: [{ name: String(item.source || 'Source unavailable'), url: String(item.sourceUrl || '#') }],
      interpretations: interpretations.length ? interpretations : [{
        assetId: 'unclear', assetName: 'Asset not specified', direction: 'unclear', magnitude: magnitude(item.impact),
        horizon: 'unclear', confidence: 'unclear', mechanism: 'No asset interpretation was specified in the legacy item.',
        confirmation, invalidation
      }],
      channels: normalizedChannels,
      legacy: { impact: String(item.impact || ''), status: String(item.status || '') }
    };
  }

  function adapt(feed = research.newsFeed || {}) {
    const dataset = {
      schemaVersion: 1,
      generatedAt: String(feed.asOf || research.generatedAt || '') || null,
      sourceMode: 'curated-delayed',
      items: (Array.isArray(feed.items) ? feed.items : []).map(adaptItem)
    };
    window.marketImpactData = dataset;
    core.store?.setSlice('impactFeed', dataset, { source: 'legacy:curated-news-adapter' });
    return dataset;
  }

  function get() {
    return core.store?.getSlice('impactFeed') || window.marketImpactData || adapt();
  }

  core.impact = Object.freeze({ adapt, adaptItem, get });
  adapt();
})();
