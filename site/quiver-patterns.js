(() => {
  'use strict';
  if (typeof fallback === 'undefined' || !fallback.trackers) return;

  const data = fallback;
  const watched = new Set(JSON.parse(localStorage.getItem('marketBriefWatchedPoliticians') || '[]'));
  let filter = 'All';
  let sort = 'name';
  let busy = false;
  let scheduled = false;

  const save = () => localStorage.setItem('marketBriefWatchedPoliticians', JSON.stringify([...watched]));
  const label = (id) => data.trackers[id]?.displayName || data.trackers[id]?.title || id;
  const ids = () => {
    const preferred = Array.isArray(data.trackerOrder) ? data.trackerOrder : [];
    return [...preferred, ...Object.keys(data.trackers).filter((id) => !preferred.includes(id))].filter((id) => data.trackers[id]);
  };
  const metrics = (id) => {
    const tracker = data.trackers[id] || {};
    const trades = Array.isArray(tracker.trades) ? tracker.trades : [];
    const holdings = Array.isArray(tracker.portfolio?.holdings) ? tracker.portfolio.holdings : [];
    const open = holdings.filter((item) => !String(item.status || '').toLowerCase().includes('closed'));
    const lags = trades.map((trade) => Number.parseInt(String(trade.lag || '').match(/\d+/)?.[0] || '', 10)).filter(Number.isFinite);
    const latest = trades.map((trade) => trade.filed).filter(Boolean).sort().reverse()[0] || 'No filing imported';
    return { trades: trades.length, holdings: open.length, lag: lags.length ? Math.round(lags.reduce((a, b) => a + b, 0) / lags.length) : null, latest };
  };

  function ensureControls() {
    const directory = document.querySelector('.tracker-directory');
    if (!directory || document.getElementById('quiverControls')) return;
    const host = document.createElement('div');
    host.id = 'quiverControls';
    host.innerHTML = `<div class="tracker-control-row"><div class="asset-filter quiver-filter">${['All','Watched','House','Senate','Executive'].map((name) => `<button data-qfilter="${name}" class="${name === filter ? 'active' : ''}">${name}${name === 'Watched' ? ` (${watched.size})` : ''}</button>`).join('')}</div><label class="tracker-sort">Sort <select id="quiverSort"><option value="name">Name</option><option value="recent">Latest filing</option><option value="trades">Trade count</option><option value="holdings">Open holdings</option></select></label></div>`;
    directory.insertAdjacentElement('afterend', host);
    host.addEventListener('click', (event) => {
      const button = event.target.closest('[data-qfilter]');
      if (!button) return;
      filter = button.dataset.qfilter;
      host.querySelectorAll('[data-qfilter]').forEach((item) => item.classList.toggle('active', item === button));
      applyDirectory();
    });
    host.querySelector('#quiverSort').value = sort;
    host.querySelector('#quiverSort').addEventListener('change', (event) => { sort = event.target.value; applyDirectory(); });
  }

  function applyDirectory() {
    if (busy) return;
    busy = true;
    const tabs = document.getElementById('trackerTabs');
    if (!tabs) { busy = false; return; }
    const buttons = [...tabs.querySelectorAll('button[data-tracker]')];
    buttons.forEach((button) => {
      const id = button.dataset.tracker;
      const tracker = data.trackers[id] || {};
      const visible = filter === 'All' || (filter === 'Watched' && watched.has(id)) || tracker.chamber === filter || (filter === 'Executive' && tracker.kind === 'executive');
      button.hidden = !visible;
      let star = button.querySelector('.watch-star');
      if (!star) {
        star = document.createElement('span');
        star.className = 'watch-star';
        star.dataset.watchId = id;
        star.setAttribute('role', 'button');
        star.setAttribute('aria-label', `Watch ${label(id)}`);
        button.appendChild(star);
      }
      star.textContent = watched.has(id) ? '★' : '☆';
      star.classList.toggle('active', watched.has(id));
    });
    const sorted = buttons.sort((a, b) => {
      const am = metrics(a.dataset.tracker); const bm = metrics(b.dataset.tracker);
      if (sort === 'trades') return bm.trades - am.trades || label(a.dataset.tracker).localeCompare(label(b.dataset.tracker));
      if (sort === 'holdings') return bm.holdings - am.holdings || label(a.dataset.tracker).localeCompare(label(b.dataset.tracker));
      if (sort === 'recent') return String(bm.latest).localeCompare(String(am.latest)) || label(a.dataset.tracker).localeCompare(label(b.dataset.tracker));
      return label(a.dataset.tracker).localeCompare(label(b.dataset.tracker));
    });
    const currentOrder = buttons.map((button) => button.dataset.tracker).join('|');
    const desiredOrder = sorted.map((button) => button.dataset.tracker).join('|');
    if (currentOrder !== desiredOrder) sorted.forEach((button) => tabs.appendChild(button));
    renderBoard();
    busy = false;
  }

  function renderBoard() {
    const tabs = document.getElementById('trackerTabs');
    if (!tabs) return;
    let host = document.getElementById('disclosureBoard');
    if (!host) { host = document.createElement('div'); host.id = 'disclosureBoard'; tabs.insertAdjacentElement('afterend', host); }
    const rows = ids().filter((id) => {
      const tracker = data.trackers[id];
      return filter === 'All' || (filter === 'Watched' && watched.has(id)) || tracker.chamber === filter || (filter === 'Executive' && tracker.kind === 'executive');
    }).sort((a, b) => metrics(b).trades - metrics(a).trades || label(a).localeCompare(label(b)));
    const signature = JSON.stringify({ filter, rows, watched: [...watched].sort(), metrics: rows.map((id) => metrics(id)) });
    if (host.dataset.signature === signature) return;
    host.dataset.signature = signature;
    host.innerHTML = `<div class="section-title compact"><h3>Disclosure activity board</h3><span>Activity ranking, not investment performance</span></div><div class="card table-wrap"><table class="matrix politician-board"><thead><tr><th>Person</th><th>Type</th><th>Trades retained</th><th>Open holdings</th><th>Latest filing</th><th>Watch</th></tr></thead><tbody>${rows.map((id) => { const tracker = data.trackers[id]; const m = metrics(id); return `<tr><td><button class="person-link" data-open-person="${id}">${label(id)}</button></td><td>${tracker.kind === 'executive' ? 'Executive' : (tracker.chamber || 'Congress')}</td><td>${m.trades}</td><td>${m.holdings}</td><td>${m.latest}</td><td><button class="watch-button ${watched.has(id) ? 'active' : ''}" data-board-watch="${id}">${watched.has(id) ? 'Watching' : '+ Watch'}</button></td></tr>`; }).join('')}</tbody></table></div>`;
  }

  function enhanceProfile() {
    const content = document.getElementById('trackerContent');
    const active = document.querySelector('#trackerTabs button.active[data-tracker]');
    if (!content || !active || content.dataset.quiverEnhanced === active.dataset.tracker) return;
    const id = active.dataset.tracker;
    const m = metrics(id);
    content.dataset.quiverEnhanced = id;
    const bar = document.createElement('div');
    bar.className = 'profile-quickbar';
    bar.innerHTML = `<div><strong>${label(id)}</strong><span>Official disclosure workspace</span></div><div class="profile-quick-actions"><button data-profile-scroll="portfolio">Portfolio</button><button data-profile-scroll="trades">Trades</button><button data-profile-scroll="sources">Sources</button><button class="watch-button ${watched.has(id) ? 'active' : ''}" data-profile-watch="${id}">${watched.has(id) ? '★ Watching' : '+ Watch'}</button></div>`;
    content.prepend(bar);
    const summary = document.createElement('div');
    summary.className = 'grid cols-4 quiver-summary';
    summary.innerHTML = `<article class="card stat"><span class="stat-label">Trades retained</span><div class="stat-value">${m.trades}</div></article><article class="card stat"><span class="stat-label">Open holdings</span><div class="stat-value">${m.holdings}</div></article><article class="card stat"><span class="stat-label">Average filing lag</span><div class="stat-value">${m.lag === null ? '—' : `${m.lag}d`}</div></article><article class="card stat"><span class="stat-label">Latest filing</span><div class="stat-value" style="font-size:14px">${m.latest}</div></article>`;
    bar.insertAdjacentElement('afterend', summary);
    const note = document.createElement('article');
    note.className = 'card backtest-note';
    note.innerHTML = '<strong>Disclosure data versus strategy returns</strong><p>Trades and holdings are public disclosure records. Return, CAGR and Sharpe metrics would be hypothetical backtests and will stay separate until the method accounts for filing lag, value ranges, options, slippage and benchmark choice.</p>';
    summary.insertAdjacentElement('afterend', note);
  }

  document.addEventListener('click', (event) => {
    const star = event.target.closest('[data-watch-id], [data-board-watch], [data-profile-watch]');
    if (star) {
      event.preventDefault(); event.stopPropagation();
      const id = star.dataset.watchId || star.dataset.boardWatch || star.dataset.profileWatch;
      watched.has(id) ? watched.delete(id) : watched.add(id); save();
      document.getElementById('quiverControls')?.remove();
      ensureControls(); applyDirectory();
      document.getElementById('trackerContent')?.removeAttribute('data-quiver-enhanced'); enhanceProfile();
      return;
    }
    const opener = event.target.closest('[data-open-person]');
    if (opener) document.querySelector(`#trackerTabs button[data-tracker="${CSS.escape(opener.dataset.openPerson)}"]`)?.click();
    const scroll = event.target.closest('[data-profile-scroll]');
    if (scroll) {
      const wanted = scroll.dataset.profileScroll;
      const heading = [...document.querySelectorAll('#trackerContent h3')].find((node) => node.textContent.toLowerCase().includes(wanted));
      heading?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, true);

  const observer = new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      ensureControls(); applyDirectory(); enhanceProfile();
    });
  });
  const tabsHost = document.getElementById('trackerTabs');
  const contentHost = document.getElementById('trackerContent');
  if (tabsHost) observer.observe(tabsHost, { childList: true, subtree: false });
  if (contentHost) observer.observe(contentHost, { childList: true, subtree: false });
  ensureControls(); applyDirectory(); enhanceProfile();
})();
