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
    Object.freeze({ route: 'news', styles: [], scripts: ['features/impact-feed/impact-data.js'] })
  ]);

  async function loadEntry(entry) {
    await Promise.all(entry.styles.map(stylesheet));
    for (const src of entry.scripts) await script(src);
  }

  Promise.all(manifest.map(loadEntry)).catch((error) => {
    console.error('Market Brief feature asset load failed', error);
  });

  core.features = Object.freeze({ manifest, script, stylesheet });
})();
