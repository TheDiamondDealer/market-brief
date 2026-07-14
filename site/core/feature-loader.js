(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const loaded = new Map();

  function stylesheet(href) {
    const key = `style:${href}`;
    if (loaded.has(key)) return loaded.get(key);
    const existing = document.querySelector(`link[data-market-brief-feature="${href}"]`);
    if (existing) return Promise.resolve(existing);
    const promise = new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.dataset.marketBriefFeature = href;
      link.addEventListener('load', () => resolve(link), { once: true });
      link.addEventListener('error', () => reject(new Error(`Unable to load ${href}`)), { once: true });
      document.head.appendChild(link);
    });
    loaded.set(key, promise);
    return promise;
  }

  function script(src) {
    const key = `script:${src}`;
    if (loaded.has(key)) return loaded.get(key);
    const existing = document.querySelector(`script[data-market-brief-feature="${src}"]`);
    if (existing) return Promise.resolve(existing);
    const promise = new Promise((resolve, reject) => {
      const node = document.createElement('script');
      node.src = src;
      node.async = false;
      node.dataset.marketBriefFeature = src;
      node.addEventListener('load', () => resolve(node), { once: true });
      node.addEventListener('error', () => reject(new Error(`Unable to load ${src}`)), { once: true });
      document.head.appendChild(node);
    });
    loaded.set(key, promise);
    return promise;
  }

  const manifest = Object.freeze([
    Object.freeze({ route: 'cot', styles: ['features/cot/cot-page.css'], scripts: ['features/cot/cot-page.js'] }),
    Object.freeze({ route: 'trackers', styles: ['features/political-flow/political-page.css'], scripts: ['features/political-flow/political-data.js', 'features/political-flow/political-page.js'] }),
    Object.freeze({ route: 'news', styles: ['features/impact-feed/impact-page.css'], scripts: ['features/impact-feed/impact-data.js', 'features/impact-feed/impact-page.js'] }),
    Object.freeze({ route: 'asset', styles: ['features/asset-workspace/asset-page.css'], scripts: ['features/asset-workspace/asset-page.js'] }),
    Object.freeze({ route: 'home', styles: ['features/command-centre/command-page.css'], scripts: ['features/command-centre/command-page.js'] }),
    Object.freeze({ route: 'calendar', styles: ['features/calendar/calendar-page.css'], scripts: ['features/calendar/calendar-data.js', 'features/calendar/calendar-page.js'] }),
    Object.freeze({ route: 'macro', styles: ['features/macro-monitor/macro-page.css'], scripts: ['features/macro-monitor/macro-page.js'] }),
    Object.freeze({ route: 'equities', styles: ['features/market-watch/market-watch-page.css'], scripts: ['equity-data.js', 'features/market-watch/market-watch-page.js'] }),
    Object.freeze({ route: 'official-feeds', styles: ['features/official-feeds/official-feeds-page.css'], scripts: ['features/official-feeds/official-feeds-data.js', 'features/official-feeds/official-feeds-health.js', 'features/official-feeds/official-feeds-page.js'] }),
    Object.freeze({ route: 'crowd-expectations', styles: ['features/crowd-expectations/crowd-page.css'], scripts: ['features/crowd-expectations/crowd-data.js', 'features/crowd-expectations/crowd-health.js', 'features/crowd-expectations/crowd-command.js', 'features/crowd-expectations/crowd-asset.js', 'features/crowd-expectations/crowd-page.js'] }),
    Object.freeze({ route: 'sources', styles: ['features/source-health/source-health-page.css'], scripts: ['features/source-health/source-health-page.js'] })
  ]);

  async function loadEntry(entry) {
    await Promise.all(entry.styles.map(stylesheet));
    for (const src of entry.scripts) await script(src);
  }

  Promise.all([stylesheet('styles/hardening.css'), script('core/freshness.js')])
    .then(() => Promise.all(manifest.map(loadEntry)))
    .catch((error) => {
      console.error('Market Brief feature asset load failed', error);
    });

  core.features = Object.freeze({ manifest, script, stylesheet });
})();
