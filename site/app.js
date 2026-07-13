(() => {
  'use strict';

  const data = typeof fallback !== 'undefined' ? fallback : null;
  if (!data) {
    document.body.innerHTML = '<div style="padding:40px;color:white;font-family:system-ui">Dashboard data failed to load.</div>';
    return;
  }

  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value = '') => String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const listHtml = (items = []) => `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
  const closeMenu = () => {
    $('sidebar')?.classList.remove('open');
    $('overlay')?.classList.remove('show');
  };

  function setView(view, updateHash = true) {
    document.querySelectorAll('.view').forEach((node) => node.classList.remove('active'));
    const target = $(`view-${view}`) || $('view-today');
    target.classList.add('active');

    document.querySelectorAll('#nav button').forEach((button) => {
      const isProductDetail = view === 'product-detail' && button.dataset.view === 'products';
      button.classList.toggle('active', button.dataset.view === view || isProductDetail);
    });

    closeMenu();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (updateHash && view !== 'product-detail') history.replaceState(null, '', `#${view}`);
  }

  function renderToday() {
    $('freshness').textContent = `Updated ${data.generatedAt}`;
    $('dailyTitle').textContent = data.daily.title;
    $('dailySub').textContent = data.daily.asOf;
    $('dailyBadge').textContent = `● ${data.regime.verdict}`;

    $('marketStats').innerHTML = data.daily.stats.map((stat, index) => {
      const points = index % 2 === 0 ? '0,28 20,23 40,25 60,15 80,18 100,6' : '0,8 20,12 40,10 60,22 80,18 100,27';
      return `<article class="card stat">
        <div class="stat-top"><span class="stat-label">${escapeHtml(stat.label)}</span><span class="move ${escapeHtml(stat.dir)}">${escapeHtml(stat.move)}</span></div>
        <div class="stat-value">${escapeHtml(stat.value)}</div>
        <div class="spark"><svg viewBox="0 0 100 34" preserveAspectRatio="none"><polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2.5" /></svg></div>
      </article>`;
    }).join('');

    $('headlines').innerHTML = data.daily.headlines.map((item) => `<article class="headline"><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.body)}</p></div></article>`).join('');
    $('chain').innerHTML = data.regime.chain.map((node, index) => `${index ? '<span class="arrow">→</span>' : ''}<span class="node">${escapeHtml(node)}</span>`).join('');
  }

  function renderWeek() {
    $('weeklyTldr').innerHTML = listHtml(data.weekly.tldr);
    $('highStake').textContent = data.weekly.highStake;
    $('events').innerHTML = data.weekly.events.map((event) => `<article class="event">
      <div class="date">${escapeHtml(event.date)}</div>
      <div><strong>${escapeHtml(event.name)}</strong><p>${escapeHtml(event.logic)}</p></div>
      <span class="risk ${escapeHtml(event.risk)}">${escapeHtml(event.risk)}</span>
    </article>`).join('');
    $('weeklyMoves').innerHTML = `<thead><tr><th>Complex</th><th>Asset</th><th>Reference</th><th>Weekly move</th></tr></thead><tbody>${data.weekly.moves.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  }

  function renderRegime() {
    $('regimeName').textContent = data.regime.name;
    $('verdict').textContent = data.regime.verdict;
    $('regimeMeaning').textContent = data.regime.meaning;
    $('shiftRules').innerHTML = listHtml(data.regime.shiftRules);
    $('relationships').innerHTML = data.regime.relationships.map((item) => {
      const state = item.classification.toLowerCase().includes('confirm') ? 'confirmed' : item.classification.toLowerCase().includes('diverg') ? 'diverging' : 'unstable';
      return `<article class="relationship"><div class="row"><strong>${escapeHtml(item.name)}</strong><span class="status ${state}">${escapeHtml(item.classification)}</span></div><p>${escapeHtml(item.evidence)}</p></article>`;
    }).join('');
    $('signFlips').innerHTML = data.regime.signFlips.map((item) => `<article class="card"><div class="card-pad"><h3>${escapeHtml(item.title)}</h3><p class="muted">${escapeHtml(item.body)}</p></div></article>`).join('');
  }

  function renderTriggers() {
    $('triggersTable').innerHTML = `<thead><tr><th>Asset</th><th>Current</th><th>Warning / trigger</th><th>Confirmation</th><th>Status</th></tr></thead><tbody>${data.triggers.map((item) => `<tr>
      <td>${escapeHtml(item.asset)}<br><span class="muted">${escapeHtml(item.direction)}</span></td>
      <td>${escapeHtml(item.current)}</td>
      <td><strong>${escapeHtml(item.warning)}</strong><br>${escapeHtml(item.trigger)}</td>
      <td>${escapeHtml(item.confirmation)}<br><span class="muted">Invalidation: ${escapeHtml(item.invalidation)}</span></td>
      <td><span class="trigger-pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></td>
    </tr>`).join('')}</tbody>`;
  }

  let activeAssetGroup = 'All';
  function renderAssets() {
    const groups = ['All', ...new Set(data.triggers.map((item) => item.group))];
    $('assetFilters').innerHTML = groups.map((group) => `<button class="${group === activeAssetGroup ? 'active' : ''}" data-asset-group="${escapeHtml(group)}">${escapeHtml(group)}</button>`).join('');
    document.querySelectorAll('[data-asset-group]').forEach((button) => button.addEventListener('click', () => {
      activeAssetGroup = button.dataset.assetGroup;
      renderAssets();
    }));

    const items = activeAssetGroup === 'All' ? data.triggers : data.triggers.filter((item) => item.group === activeAssetGroup);
    $('assetCards').innerHTML = items.map((item) => `<article class="card stat searchable" data-search="${escapeHtml(`${item.asset} ${item.group} ${item.direction}`.toLowerCase())}">
      <div class="stat-top"><span class="stat-label">${escapeHtml(item.group)}</span><span class="trigger-pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></div>
      <div class="stat-value">${escapeHtml(item.current)}</div>
      <h3>${escapeHtml(item.asset)}</h3>
      <p class="muted">${escapeHtml(item.direction)}</p>
      <p class="muted"><strong>Trigger:</strong> ${escapeHtml(item.trigger)}</p>
    </article>`).join('');
  }

  let activeProductGroup = 'All';
  function productGroups() {
    return ['All', ...new Set(data.products.map((product) => product.group))];
  }

  function renderProducts(query = '') {
    const groups = productGroups();
    $('productFilters').innerHTML = groups.map((group) => `<button class="${group === activeProductGroup ? 'active' : ''}" data-product-group="${escapeHtml(group)}">${escapeHtml(group)}</button>`).join('');
    document.querySelectorAll('[data-product-group]').forEach((button) => button.addEventListener('click', () => {
      activeProductGroup = button.dataset.productGroup;
      renderProducts($('search').value.trim().toLowerCase());
    }));

    const normalized = query.trim().toLowerCase();
    const products = data.products.filter((product) => {
      const groupMatch = activeProductGroup === 'All' || product.group === activeProductGroup;
      const haystack = `${product.name} ${product.group} ${product.tagline} ${product.benchmark} ${product.sensitivity}`.toLowerCase();
      return groupMatch && (!normalized || haystack.includes(normalized));
    });

    $('productCount').textContent = `${products.length} product${products.length === 1 ? '' : 's'}`;
    $('productCards').innerHTML = products.length ? products.map((product) => `<article class="product-card" data-product-id="${escapeHtml(product.id)}" tabindex="0" role="button" aria-label="Open ${escapeHtml(product.name)} deep dive">
      <div class="product-icon">${escapeHtml(product.icon)}</div>
      <h3>${escapeHtml(product.name)}</h3>
      <p>${escapeHtml(product.tagline)}</p>
      <div class="product-meta"><span class="mini-pill">${escapeHtml(product.group)}</span><span class="mini-pill">${escapeHtml(product.status)}</span></div>
      <span class="product-open">Deep dive</span>
    </article>`).join('') : '<div class="card empty">No products match that search.</div>';

    document.querySelectorAll('[data-product-id]').forEach((card) => {
      const open = () => openProduct(card.dataset.productId);
      card.addEventListener('click', open);
      card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') open(); });
    });
  }

  const keyRows = (pairs = []) => `<div class="key-list">${pairs.map(([key, value]) => `<div class="key-row"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(value)}</span></div>`).join('')}</div>`;
  const bulletCard = (title, items) => `<article class="card deep-section"><h3>${escapeHtml(title)}</h3>${listHtml(items)}</article>`;

  function productTab(product, tab) {
    const content = $('productTabContent');
    if (!content) return;
    const overview = `<div class="grid cols-2">
      <article class="card deep-section"><h3>Investment thesis</h3><p>${escapeHtml(product.thesis)}</p></article>
      <article class="card deep-section"><h3>Market structure</h3>${listHtml(product.marketStructure)}</article>
      <article class="card deep-section"><h3>Active trigger levels</h3>${keyRows(product.triggers)}</article>
      <article class="card deep-section"><h3>Related markets</h3><div class="product-meta">${product.related.map((item) => `<span class="mini-pill">${escapeHtml(item)}</span>`).join('')}</div></article>
    </div>`;
    const tabs = {
      overview,
      benchmarks: `<article class="card deep-section"><h3>Benchmarks to track</h3>${keyRows(product.benchmarks)}</article>`,
      supply: bulletCard('Supply drivers', product.supply) + `<div style="height:16px"></div>` + bulletCard('Major producing countries', product.producers),
      demand: bulletCard('Demand drivers', product.demand),
      catalysts: bulletCard('Catalysts', product.catalysts),
      risks: bulletCard('Risks and invalidation factors', product.risks),
      notes: bulletCard('Research notes', product.notes)
    };
    content.innerHTML = tabs[tab] || overview;
    document.querySelectorAll('.deep-tabs button').forEach((button) => button.classList.toggle('active', button.dataset.tab === tab));
  }

  function openProduct(id) {
    const product = data.products.find((item) => item.id === id);
    if (!product) return;
    $('productDetail').innerHTML = `<section class="deep-hero">
      <div class="deep-hero-top"><div><div class="deep-icon">${escapeHtml(product.icon)}</div><div class="eyebrow">${escapeHtml(product.group)} deep dive</div><h2>${escapeHtml(product.name)}</h2><p>${escapeHtml(product.tagline)}</p></div><span class="deep-status">${escapeHtml(product.status)}</span></div>
      <div class="grid cols-4" style="margin-top:22px">
        <article class="card stat"><span class="stat-label">Benchmark</span><div class="stat-value" style="font-size:18px">${escapeHtml(product.benchmark)}</div></article>
        <article class="card stat"><span class="stat-label">Current reference</span><div class="stat-value" style="font-size:18px">${escapeHtml(product.current)}</div></article>
        <article class="card stat"><span class="stat-label">Key sensitivity</span><div class="stat-value" style="font-size:18px">${escapeHtml(product.sensitivity)}</div></article>
        <article class="card stat"><span class="stat-label">Updated</span><div class="stat-value" style="font-size:18px">${escapeHtml(product.updated)}</div></article>
      </div>
    </section>
    <div class="deep-tabs">
      ${[['overview','Overview'],['benchmarks','Benchmarks'],['supply','Supply'],['demand','Demand'],['catalysts','Catalysts'],['risks','Risks'],['notes','Notes']].map(([id, label]) => `<button data-tab="${id}" class="${id === 'overview' ? 'active' : ''}">${label}</button>`).join('')}
    </div>
    <div id="productTabContent"></div>`;
    document.querySelectorAll('.deep-tabs button').forEach((button) => button.addEventListener('click', () => productTab(product, button.dataset.tab)));
    productTab(product, 'overview');
    setView('product-detail', false);
    history.replaceState(null, '', `#product/${product.id}`);
  }

  function renderArchive() {
    $('archiveList').innerHTML = data.archive.map((item) => `<article class="archive-item"><span class="type">${escapeHtml(item.type)}</span><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.date)}</span></article>`).join('');
  }

  function handleSearch() {
    const query = $('search').value.trim().toLowerCase();
    const currentView = document.querySelector('.view.active')?.id || '';
    if (currentView === 'view-products') renderProducts(query);
    if (currentView === 'view-assets') {
      document.querySelectorAll('#assetCards .searchable').forEach((card) => {
        card.style.display = !query || card.dataset.search.includes(query) ? '' : 'none';
      });
    }
  }

  function handleRoute() {
    const route = location.hash.replace(/^#/, '') || 'today';
    if (route.startsWith('product/')) {
      openProduct(route.split('/')[1]);
      return;
    }
    const allowed = ['today', 'week', 'regime', 'triggers', 'assets', 'products', 'archive'];
    setView(allowed.includes(route) ? route : 'today', false);
  }

  function initialise() {
    renderToday();
    renderWeek();
    renderRegime();
    renderTriggers();
    renderAssets();
    renderProducts();
    renderArchive();

    document.querySelectorAll('#nav button').forEach((button) => button.addEventListener('click', () => setView(button.dataset.view)));
    $('productBack').addEventListener('click', () => setView('products'));
    $('menu').addEventListener('click', () => { $('sidebar').classList.add('open'); $('overlay').classList.add('show'); });
    $('overlay').addEventListener('click', closeMenu);
    $('search').addEventListener('input', handleSearch);
    $('search').addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      const query = $('search').value.trim().toLowerCase();
      const product = data.products.find((item) => `${item.name} ${item.tagline} ${item.group}`.toLowerCase().includes(query));
      if (product) openProduct(product.id);
    });
    document.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('search').focus(); }
    });
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
  }

  initialise();
})();
