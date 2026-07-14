(() => {
  'use strict';

  const core = window.MarketBriefCore = window.MarketBriefCore || {};
  const store = core.store;

  const EMPTY_RESEARCH = Object.freeze({
    generatedAt: 'Unavailable',
    regime: { verdict: 'Unavailable', name: 'Unavailable', meaning: '', chain: [], relationships: [], signFlips: [], shiftRules: [] },
    daily: { title: 'Daily brief unavailable', asOf: '', stats: [], headlines: [] },
    weekly: { tldr: [], events: [], moves: [], highStake: '' },
    triggers: [], products: [], archive: [], assetBiases: [], trackers: {}, trackerOrder: []
  });
  const EMPTY_OFFICIAL = Object.freeze({ rates: [], curveSpreads: [], cot: [], sourceStatus: [], methodology: {} });
  const EMPTY_EVIDENCE = Object.freeze({ physicalChecklists: {}, eventReactions: [] });
  const EMPTY_SCENARIOS = Object.freeze({});

  function readLegacyResearch() {
    return typeof fallback !== 'undefined' && fallback ? fallback : EMPTY_RESEARCH;
  }

  function readOfficialData() {
    return window.freeMarketData || EMPTY_OFFICIAL;
  }

  function readEvidenceData() {
    return window.marketResearchData || EMPTY_EVIDENCE;
  }

  function readScenarioData() {
    return window.scenarioAssets || EMPTY_SCENARIOS;
  }

  function refresh() {
    const research = readLegacyResearch();
    const official = readOfficialData();
    const evidence = readEvidenceData();
    const scenarios = readScenarioData();
    store?.setSlice('research', research, { source: 'legacy:fallback' });
    store?.setSlice('official', official, { source: 'legacy:freeMarketData' });
    store?.setSlice('evidence', evidence, { source: 'legacy:marketResearchData' });
    store?.setSlice('scenarios', scenarios, { source: 'legacy:scenarioAssets' });
    return { research, official, evidence, scenarios };
  }

  function research() {
    return store?.getSlice('research') || readLegacyResearch();
  }

  function official() {
    return store?.getSlice('official') || readOfficialData();
  }

  function evidence() {
    return store?.getSlice('evidence') || readEvidenceData();
  }

  function scenarios() {
    const current = readScenarioData();
    if (current !== EMPTY_SCENARIOS && current !== store?.getSlice('scenarios')) {
      store?.setSlice('scenarios', current, { source: 'legacy:scenarioAssets' });
    }
    return store?.getSlice('scenarios') || current;
  }

  function closeNavigation() {
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('overlay')?.classList.remove('show');
  }

  function activeView() {
    return document.querySelector('.view.active')?.id?.replace(/^view-/, '') || null;
  }

  function activateView(view, { scroll = true } = {}) {
    const target = document.getElementById(`view-${view}`);
    if (!target) return false;
    document.querySelectorAll('.view').forEach((node) => {
      const active = node === target;
      node.classList.toggle('active', active);
      node.setAttribute('aria-hidden', String(!active));
    });
    document.querySelectorAll('#nav button[data-view]').forEach((button) => {
      const productAlias = view === 'product-detail' && button.dataset.view === 'products';
      const current = button.dataset.view === view || productAlias;
      button.classList.toggle('active', current);
      if (current) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    closeNavigation();
    if (scroll) window.scrollTo({ top: 0, behavior: 'smooth' });
    return true;
  }

  const views = Object.freeze({ activate: activateView, active: activeView, closeNavigation });
  const legacy = Object.freeze({ evidence: readEvidenceData, official: readOfficialData, research: readLegacyResearch, scenarios: readScenarioData });

  core.adapters = Object.freeze({ evidence, legacy, official, refresh, research, scenarios, views });
  refresh();
})();
