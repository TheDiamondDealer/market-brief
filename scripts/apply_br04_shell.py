#!/usr/bin/env python3
"""Apply the BR-04 shell markup without altering feature sections or data."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "site" / "index.html"

SIDEBAR = '''  <aside class="sidebar" id="sidebar" aria-label="Application navigation">
    <div class="brand">
      <div class="mark" aria-hidden="true">M</div>
      <div class="brand-copy"><h1>Market Brief</h1><p>Intelligence console</p></div>
    </div>
    <button class="rail-toggle" id="railToggle" type="button" aria-label="Expand navigation rail" aria-expanded="false" data-tooltip="Expand navigation">
      <span class="nav-icon" aria-hidden="true">⇥</span><span class="rail-toggle-label">Expand navigation</span>
    </button>
    <nav class="nav" id="nav" aria-label="Market Brief sections">
      <span class="nav-section-label">Primary</span>
      <button type="button" class="nav-item active" data-view="home" aria-label="Command Centre" title="Command Centre" data-tooltip="Command Centre"><span class="nav-icon" aria-hidden="true">⌂</span><span class="nav-label">Command Centre</span></button>
      <button type="button" class="nav-item" data-view="news" aria-label="Impact Feed" title="Impact Feed" data-tooltip="Impact Feed"><span class="nav-icon" aria-hidden="true">⚡</span><span class="nav-label">Impact Feed</span></button>
      <button type="button" class="nav-item" data-view="events" aria-label="Calendar and reactions" title="Calendar and reactions" data-tooltip="Calendar"><span class="nav-icon" aria-hidden="true">◷</span><span class="nav-label">Calendar</span></button>
      <button type="button" class="nav-item" data-view="cot" aria-label="COT Positioning" title="COT Positioning" data-tooltip="COT Positioning"><span class="nav-icon" aria-hidden="true">⇄</span><span class="nav-label">COT Positioning</span></button>
      <button type="button" class="nav-item" data-view="trackers" aria-label="Political Flow" title="Political Flow" data-tooltip="Political Flow"><span class="nav-icon" aria-hidden="true">◎</span><span class="nav-label">Political Flow</span></button>
      <span class="nav-section-label">Research</span>
      <button type="button" class="nav-item" data-view="rates" aria-label="Rates and liquidity" title="Rates and liquidity" data-tooltip="Rates and liquidity"><span class="nav-icon" aria-hidden="true">⌁</span><span class="nav-label">Rates &amp; Liquidity</span></button>
      <button type="button" class="nav-item" data-view="today" aria-label="Daily Brief" title="Daily Brief" data-tooltip="Daily Brief"><span class="nav-icon" aria-hidden="true">◉</span><span class="nav-label">Daily Brief</span></button>
      <button type="button" class="nav-item" data-view="week" aria-label="Week Ahead" title="Week Ahead" data-tooltip="Week Ahead"><span class="nav-icon" aria-hidden="true">◫</span><span class="nav-label">Week Ahead</span></button>
      <button type="button" class="nav-item" data-view="regime" aria-label="Regime" title="Regime" data-tooltip="Regime"><span class="nav-icon" aria-hidden="true">◇</span><span class="nav-label">Regime</span></button>
      <button type="button" class="nav-item" data-view="triggers" aria-label="Trigger Zones" title="Trigger Zones" data-tooltip="Trigger Zones"><span class="nav-icon" aria-hidden="true">⚑</span><span class="nav-label">Trigger Zones</span></button>
      <button type="button" class="nav-item" data-view="assets" aria-label="Assets" title="Assets" data-tooltip="Assets"><span class="nav-icon" aria-hidden="true">◆</span><span class="nav-label">Assets</span></button>
      <button type="button" class="nav-item" data-view="products" aria-label="Research Library" title="Research Library" data-tooltip="Research Library"><span class="nav-icon" aria-hidden="true">▦</span><span class="nav-label">Research Library</span></button>
      <button type="button" class="nav-item" data-view="scenarios" aria-label="Scenario Lab" title="Scenario Lab" data-tooltip="Scenario Lab"><span class="nav-icon" aria-hidden="true">↗</span><span class="nav-label">Scenario Lab</span></button>
      <button type="button" class="nav-item" data-view="archive" aria-label="Archive" title="Archive" data-tooltip="Archive"><span class="nav-icon" aria-hidden="true">▤</span><span class="nav-label">Archive</span></button>
    </nav>
    <div class="side-note"><strong>Research system</strong><span>Observed facts and interpretation remain separate throughout the console.</span></div>
  </aside>'''

TOPBAR = '''    <header class="topbar" aria-label="Page header">
      <button class="menu" id="menu" type="button" aria-label="Open navigation" aria-controls="sidebar" aria-expanded="false">☰</button>
      <div class="page-context">
        <h1 id="pageTitle">Command Centre</h1>
        <p id="pageSubtitle">What matters now, the active regime and what could change it.</p>
      </div>
      <div class="search" role="search"><input id="search" type="search" placeholder="Search local assets, catalysts and research…" autocomplete="off" /><span class="kbd" aria-hidden="true">⌘ K</span></div>
      <div class="freshness-cluster"><div class="fresh" role="status" aria-live="polite"><span class="dot" aria-hidden="true"></span><span id="freshness">Loading latest brief…</span></div></div>
    </header>'''

MOBILE = '''
<nav class="mobile-bottom-nav" aria-label="Primary mobile navigation">
  <button type="button" class="mobile-nav-button" data-shell-view="home" aria-label="Command Centre"><span class="nav-icon" aria-hidden="true">⌂</span><span>Home</span></button>
  <button type="button" class="mobile-nav-button" data-shell-view="news" aria-label="Impact Feed"><span class="nav-icon" aria-hidden="true">⚡</span><span>Impact</span></button>
  <button type="button" class="mobile-nav-button" data-shell-view="events" aria-label="Calendar"><span class="nav-icon" aria-hidden="true">◷</span><span>Calendar</span></button>
  <button type="button" class="mobile-nav-button" data-shell-view="cot" aria-label="COT Positioning"><span class="nav-icon" aria-hidden="true">⇄</span><span>COT</span></button>
  <button type="button" class="mobile-nav-button" data-shell-view="trackers" aria-label="Political Flow"><span class="nav-icon" aria-hidden="true">◎</span><span>Political</span></button>
  <button type="button" class="mobile-nav-button" id="mobileMoreButton" aria-label="More navigation" aria-controls="mobileMore" aria-expanded="false"><span class="nav-icon" aria-hidden="true">•••</span><span>More</span></button>
</nav>
<section class="mobile-more" id="mobileMore" role="dialog" aria-modal="true" aria-labelledby="mobileMoreTitle" hidden>
  <div class="mobile-more-header"><h2 id="mobileMoreTitle">More sections</h2><button type="button" class="mobile-more-close" id="mobileMoreClose" aria-label="Close more navigation">×</button></div>
  <div class="mobile-more-grid">
    <button type="button" data-shell-view="rates">Rates &amp; Liquidity</button>
    <button type="button" data-shell-view="today">Daily Brief</button>
    <button type="button" data-shell-view="week">Week Ahead</button>
    <button type="button" data-shell-view="regime">Regime</button>
    <button type="button" data-shell-view="triggers">Trigger Zones</button>
    <button type="button" data-shell-view="assets">Assets</button>
    <button type="button" data-shell-view="products">Research Library</button>
    <button type="button" data-shell-view="scenarios">Scenario Lab</button>
    <button type="button" data-shell-view="archive">Archive</button>
  </div>
</section>
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"BR-04 migration failed: missing {label}")
    return text.replace(old, new, 1)


def main() -> int:
    text = INDEX.read_text(encoding="utf-8")
    if 'styles/tokens.css' in text and 'shell.js' in text:
        print("BR-04 shell already applied")
        return 0

    text = replace_once(text, '<meta name="theme-color" content="#071014" />', '<meta name="theme-color" content="#050607" />', 'theme colour')
    text = replace_once(text, '  <link rel="stylesheet" href="styles.css" />', '  <link rel="stylesheet" href="styles/tokens.css" />\n  <link rel="stylesheet" href="styles/base.css" />\n  <link rel="stylesheet" href="styles.css" />', 'base stylesheet')
    text = replace_once(text, '  <link rel="stylesheet" href="free-data.css" />', '  <link rel="stylesheet" href="free-data.css" />\n  <link rel="stylesheet" href="styles/shell.css" />', 'shell stylesheet position')
    text = replace_once(text, '<body>\n', '<body>\n<a class="skip-link" href="#main-content">Skip to main content</a>\n', 'body start')

    text, count = re.subn(r'  <aside class="sidebar" id="sidebar">.*?  </aside>', SIDEBAR, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"BR-04 migration failed: sidebar replacements={count}")

    text = replace_once(text, '  <main>', '  <main id="main-content" tabindex="-1">', 'main landmark')
    text, count = re.subn(r'    <header class="topbar">.*?    </header>', TOPBAR, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"BR-04 migration failed: topbar replacements={count}")

    text = replace_once(text, '<script>window.__marketInitialHash', MOBILE + '<script>window.__marketInitialHash', 'mobile navigation insertion')
    text = replace_once(text, '  <script src="command-centre.js"></script>\n', '  <script src="command-centre.js"></script>\n  <script src="shell.js"></script>\n', 'shell script')

    INDEX.write_text(text, encoding="utf-8")
    print("Applied BR-04 shell markup; feature sections and data scripts preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
