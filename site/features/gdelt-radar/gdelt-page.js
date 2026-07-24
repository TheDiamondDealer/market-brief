(() => {
  'use strict';

  const core = window.MarketBriefCore || {};
  const escapeHtml = core.format?.escapeHtml || ((value = '') => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;'));
  let topic = 'all';
  let scheduled = false;
  let impactTags = null;
  let impactTagsFailed = false;
  let impactTagsFetchStarted = false;

  function data() {
    return window.gdeltRadarData || { collection: { status: 'unavailable' }, articles: [], topics: [] };
  }

  function impactTagsById() {
    const map = new Map();
    const items = Array.isArray(impactTags?.items) ? impactTags.items : [];
    items.forEach((entry) => { if (entry && entry.id) map.set(entry.id, entry); });
    return map;
  }

  async function loadImpactTags() {
    if (impactTagsFetchStarted) return;
    impactTagsFetchStarted = true;
    try {
      const response = await fetch('data/impact-tags.json', { cache: 'no-store', credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      impactTags = await response.json();
      impactTagsFailed = false;
    } catch (error) {
      impactTags = null;
      impactTagsFailed = true;
    }
    scheduleRender();
  }

  function aiChipsMarkup(item) {
    const entry = impactTagsById().get(item.id);
    if (!entry) {
      // Not in the ledger yet, or the whole ledger failed to load: honest "pending" note either way.
      return '<span class="gdelt-ai-note">AI tagging pending</span>';
    }
    if (entry.tagState === 'unavailable') {
      return '<span class="gdelt-ai-note">AI tagging unavailable</span>';
    }
    if (entry.tagState !== 'tagged') {
      return '<span class="gdelt-ai-note">AI tagging pending</span>';
    }
    const tags = Array.isArray(entry.tags) ? entry.tags : [];
    if (!tags.length) return '';
    if (!core.impactChips || !window.marketAssetBoard?.assets) return '';
    const signals = tags.map((tag) => ({
      assetId: tag.assetId,
      direction: tag.direction,
      tier: 'ai',
      source: 'ai',
      label: 'AI-tagged',
      confidence: tag.confidence,
      detail: `${tag.mechanism} (AI-tagged from ${item.domain || 'source'}, ${tag.confidence} confidence).`,
      at: item.seenAt || null,
      status: 'current',
      href: '',
    }));
    const strip = core.impactChips.chipStrip(signals);
    return strip ? `<span class="gdelt-ai-chips">${strip}</span>` : '';
  }

  function relativeTime(value) {
    if (!value) return 'Time unavailable';
    const milliseconds = Date.parse(value);
    if (!Number.isFinite(milliseconds)) return value;
    const minutes = Math.max(0, Math.round((Date.now() - milliseconds) / 60000));
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 48) return `${hours}h ago`;
    return `${Math.round(hours / 24)}d ago`;
  }

  function statusLabel(value) {
    const status = String(value || 'unavailable').toLowerCase();
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  function cards(items) {
    if (!items.length) return '<div class="gdelt-empty">No discovery leads match this topic. The verified Impact Feed remains available below.</div>';
    return items.slice(0, 12).map((item) => `<article class="gdelt-card">
      <div class="gdelt-card-meta"><span>${escapeHtml(item.topics?.[0] || 'Discovery')}</span><span>Score ${escapeHtml(item.materialityScore)}</span><time datetime="${escapeHtml(item.seenAt || '')}">${escapeHtml(relativeTime(item.seenAt))}</time></div>
      <h4><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)} ↗</a></h4>
      <div class="gdelt-source"><strong>${escapeHtml(item.domain || 'Source unavailable')}</strong><span>${escapeHtml(item.sourceCountry || 'Country unavailable')}</span><span>${escapeHtml(item.language || 'Language unavailable')}</span></div>
      <div class="gdelt-tags">${(item.assets || []).slice(0, 5).map((asset) => `<span>${escapeHtml(asset)}</span>`).join('')}</div>
      ${aiChipsMarkup(item)}
      <p>${escapeHtml(item.verificationNote || 'Discovery lead only. Confirm against an official source.')}</p>
    </article>`).join('');
  }

  function render() {
    scheduled = false;
    const root = document.getElementById('view-news');
    const page = root?.querySelector('.impact-feed-page');
    const hero = page?.querySelector('.impact-feed-hero');
    if (!root || !page || !hero) return;

    let mount = root.querySelector('#gdeltRadarMount');
    if (!mount) {
      mount = document.createElement('section');
      mount.id = 'gdeltRadarMount';
      mount.className = 'gdelt-radar';
      hero.insertAdjacentElement('afterend', mount);
    }

    const feed = data();
    const collection = feed.collection || {};
    const allItems = Array.isArray(feed.articles) ? feed.articles : [];
    const visible = topic === 'all' ? allItems : allItems.filter((item) => (item.topicIds || []).includes(topic));
    const fingerprint = JSON.stringify([feed.generatedAtUtc, collection.status, topic, visible.map((item) => item.id), impactTags?.generatedAtUtc, impactTagsFailed]);
    if (mount.dataset.fingerprint === fingerprint) return;
    mount.dataset.fingerprint = fingerprint;

    mount.innerHTML = `<details ${allItems.length ? '' : 'open'}>
      <summary><div><span class="gdelt-kicker">Wide-net early warning</span><h3>GDELT Discovery Radar</h3><p>Machine-observed media coverage. Unverified until confirmed by an official source or trusted financial wire.</p></div><div class="gdelt-status"><span class="data-state ${escapeHtml(collection.status || 'unavailable')}">${escapeHtml(statusLabel(collection.status))}</span><strong>${escapeHtml(allItems.length)} leads</strong><small>${escapeHtml(collection.expectedCadence || 'Hourly')}</small></div></summary>
      <div class="gdelt-warning"><strong>Discovery only:</strong> a headline appearing here proves that coverage exists, not that the underlying claim is true, current or financially material.</div>
      <div class="gdelt-toolbar" role="group" aria-label="GDELT topic filters"><button type="button" data-gdelt-topic="all" aria-pressed="${topic === 'all'}">All</button>${(feed.topics || []).map((entry) => `<button type="button" data-gdelt-topic="${escapeHtml(entry.id)}" aria-pressed="${topic === entry.id}">${escapeHtml(entry.name)}</button>`).join('')}</div>
      ${impactTagsFailed ? '<p class="gdelt-ai-degraded">AI impact tagging is temporarily unavailable; showing untagged discovery leads.</p>' : ''}
      ${collection.error ? `<p class="gdelt-error">${escapeHtml(collection.error)}</p>` : ''}
      <div class="gdelt-grid">${cards(visible)}</div>
      <footer><span>Generated ${escapeHtml(feed.generatedAtUtc ? relativeTime(feed.generatedAtUtc) : 'time unavailable')}</span><a href="${escapeHtml(feed.provider?.documentationUrl || 'https://www.gdeltproject.org/')}" target="_blank" rel="noopener noreferrer">GDELT methodology ↗</a></footer>
    </details>`;

    mount.querySelectorAll('[data-gdelt-topic]').forEach((button) => button.addEventListener('click', () => {
      topic = button.dataset.gdeltTopic || 'all';
      mount.dataset.fingerprint = '';
      render();
    }));
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(render);
  }

  function initialise() {
    const root = document.getElementById('view-news');
    if (!root) return;
    const observer = new MutationObserver(scheduleRender);
    observer.observe(root, { childList: true, subtree: true });
    scheduleRender();
    loadImpactTags();
  }

  window.addEventListener('marketbrief:gdelt-data', scheduleRender);
  window.addEventListener('hashchange', scheduleRender);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
})();
