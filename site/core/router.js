(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const exactRoutes = new Map();
  const patternRoutes = [];
  const listeners = new Set();
  let started = false;
  let currentRoute = null;

  function normalize(value = '') {
    return String(value).trim().replace(/^#/, '').replace(/^\/+|\/+$/g, '');
  }

  function routeRecord(path) {
    const normalized = normalize(path) || 'home';
    if (exactRoutes.has(normalized)) return { name: normalized, path: normalized, params: {}, handler: exactRoutes.get(normalized) };
    for (const route of patternRoutes) {
      const match = normalized.match(route.pattern);
      if (match) return { name: route.name, path: normalized, params: route.params(match), handler: route.handler };
    }
    const fallback = exactRoutes.get('home') || exactRoutes.get('today') || null;
    return { name: fallback === exactRoutes.get('home') ? 'home' : 'today', path: normalized, params: {}, handler: fallback, unmatched: true };
  }

  function notify(route) {
    listeners.forEach((listener) => {
      try { listener(route); } catch (error) { console.error('Market Brief router listener failed', error); }
    });
    window.dispatchEvent(new CustomEvent('marketbrief:route', { detail: route }));
  }

  function dispatch(value = window.location.hash, meta = {}) {
    const route = routeRecord(value);
    currentRoute = { ...route, source: meta.source || 'dispatch' };
    core.store?.setSlice('route', currentRoute, { source: currentRoute.source, force: true });
    if (typeof route.handler === 'function') route.handler(currentRoute);
    notify(currentRoute);
    return currentRoute;
  }

  function register(name, handler) {
    const routeName = normalize(name);
    if (!routeName || typeof handler !== 'function') throw new TypeError('Router.register requires a route name and handler.');
    exactRoutes.set(routeName, handler);
    return () => exactRoutes.delete(routeName);
  }

  function registerPattern(name, pattern, handler, params = (match) => ({ value: match[1] })) {
    if (!(pattern instanceof RegExp) || typeof handler !== 'function') throw new TypeError('Router.registerPattern requires a RegExp and handler.');
    const route = { name, pattern, handler, params };
    patternRoutes.push(route);
    return () => {
      const index = patternRoutes.indexOf(route);
      if (index >= 0) patternRoutes.splice(index, 1);
    };
  }

  function navigate(value, { replace = true } = {}) {
    const path = normalize(value) || 'home';
    const hash = `#${path}`;
    if (replace) {
      history.replaceState(null, '', hash);
      return dispatch(hash, { source: 'navigate' });
    }
    if (window.location.hash === hash) return dispatch(hash, { source: 'navigate' });
    window.location.hash = hash;
    return routeRecord(hash);
  }

  function subscribe(listener, { immediate = false } = {}) {
    if (typeof listener !== 'function') throw new TypeError('Router listener must be a function.');
    listeners.add(listener);
    if (immediate && currentRoute) listener(currentRoute);
    return () => listeners.delete(listener);
  }

  function start(initialHash = window.location.hash) {
    if (!started) {
      window.addEventListener('hashchange', () => dispatch(window.location.hash, { source: 'hashchange' }));
      started = true;
    }
    return dispatch(initialHash || window.location.hash || '#home', { source: 'initial' });
  }

  function current() {
    return currentRoute ? { ...currentRoute, params: { ...currentRoute.params } } : null;
  }

  core.router = Object.freeze({ current, dispatch, navigate, normalize, register, registerPattern, start, subscribe });

  // Feature packages are loaded from one ordered, auditable manifest. This keeps
  // index.html stable while the remodel migrates individual routes.
  if (typeof document.createElement === 'function' && document.head?.appendChild) {
    const featureLoader = document.createElement('script');
    featureLoader.src = 'core/feature-loader.js';
    featureLoader.async = false;
    featureLoader.dataset.marketBriefFeatureLoader = 'true';
    featureLoader.addEventListener('error', () => console.error('Market Brief feature manifest failed to load.'));
    document.head.appendChild(featureLoader);
  }
})();
