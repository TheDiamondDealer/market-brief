# Dashboard Intelligence Data Update

Run this after every successful daily market brief.

Update `site/intelligence-data.js`, `site/command-centre-data.js` and the research-controlled portions of `site/research-data.js` on `main`. Do not change application code or styling. Do not manually overwrite `site/free-data.js` or `site/data/free-market-data.json`; the official-data workflow owns those files.

## Evidence hierarchy

Use evidence in this order:

1. official government, regulator, exchange, central-bank or company release
2. primary filing, report, speech or dataset
3. high-quality wire or financial publication for context
4. specialist commodity or industry publication
5. social media only as an unconfirmed discovery lead

For market-moving policy or geopolitical claims, use an official announcement or two reliable independent sources. Distinguish announced, proposed, enacted, effective, delayed, reversed and price-confirmed.

TradingView widgets are an external discovery and charting layer only. Never scrape or import TradingView headlines, chart values or indicators into the bias engine. Independently verify anything discovered there.

## Command centre

Refresh `fallback.commandCentre` with:

- successful-run timestamp
- risk state, transparent 0–100 score and cautious confidence label
- concise summary and one important contradiction
- three to six visible risk inputs with reading, score and reason
- conditions that would move the gauge into another state
- next high-impact event in Melbourne time and why it matters
- three to six material changes from the previous successful state

The risk score is an interpretable summary, not a probability.

## Asset bias engine

Refresh `fallback.assetBiases` for actively monitored assets. For each asset include:

- stable ID, name, group and verified research reference
- cautious directional label
- confidence from 0 to 100
- integer total equal to the visible component scores
- primary driver
- current COT/positioning state from `window.freeMarketData`, or explicitly stale/pending/unavailable
- next relevant event
- exact condition that changes the bias
- product deep-dive link where available
- three to five components scored from -2 to +2 with one-sentence explanations

Confidence reflects agreement, evidence quality and confirmation. Do not mechanically treat a high COT percentile as bullish or a low percentile as bearish; decide whether positioning confirms momentum or creates contrarian liquidation/squeeze risk.

## Rates and liquidity

Review the latest official-data cache:

- US 2-, 5-, 10- and 30-year yields
- US 10-year real yield
- 10-year inflation breakeven
- 2s10s and 5s30s
- high-yield credit spread
- effective federal funds rate and SOFR
- trade-weighted US dollar

Classify why yields moved: growth, inflation risk, policy expectations, bond supply/term premium, or risk-off/deleveraging. Do not assign one universal impact to a yield move before identifying its cause.

## Physical commodity confirmation

Update non-automatic readings in `window.marketResearchData.physicalChecklists`. Preserve automatic FRED and CFTC readings. A futures-price move alone is not physical confirmation.

### Gold

Review real yields, US dollar, COT, ETF flows, central-bank demand and regional physical premiums.

### Oil — always separate Brent and WTI

Never write “oil” as one undifferentiated market.

For **Brent**, review:

- outright price and front spreads
- seaborne cargo availability and tanker/export flows
- OPEC+ supply and compliance
- North Sea, Gulf, Russian and other export disruptions
- global refinery runs and diesel/gasoline cracks
- Brent managed-money positioning when a current verified contract is available

For **WTI**, review:

- outright price and front spreads
- EIA commercial inventories and Cushing stocks
- US production, Canadian inflows and Gulf Coast exports
- US refinery utilisation and crude runs
- WTI managed-money positioning from the exact current contract shown in the CFTC cache

Always evaluate the **Brent–WTI spread**. State whether the move is global/seaborne, US-specific or broad across both benchmarks. Do not substitute a stale NYMEX series for a current ICE/CFTC-covered WTI series without naming the exact contract.

### Natural gas — always separate US Henry Hub and UK NBP

Never use TTF as though it were the UK benchmark. TTF is a continental-European cross-check; UK gas is NBP.

For **US Henry Hub**, review:

- EIA storage versus seasonal norms
- dry-gas and associated-gas production
- LNG feedgas, terminal outages/restarts and export capacity
- weather and gas-fired power burn
- pipeline constraints and regional basis
- current verified Henry Hub positioning when available

For **UK NBP**, review:

- UK system balance and storage
- UK Continental Shelf and Norwegian flows
- interconnector imports/exports
- LNG arrivals and regasification
- UK weather, wind generation and gas-fired power demand
- industrial demand
- NBP positioning only when a current exact official contract is available; otherwise show unavailable

Treat the Henry Hub–NBP divergence as a signal. Explain whether LNG, pipelines, storage or weather is preventing regional convergence.

### Copper

Review LME/COMEX/Shanghai inventories, treatment charges, regional premiums, China grid/manufacturing demand, mine disruptions, scrap response and COT.

### Silver

Review the gold/rates channel, industrial metals and manufacturing, COT, exchange inventories, premiums and ETF/bar-and-coin flows.

### Rare earths

Review NdPr, dysprosium and terbium separately; Chinese quotas/export controls; China versus ex-China premiums; magnet prices/lead times; and ex-China project milestones.

For every updated physical reading retain the exact source, observation date/freshness and one-sentence interpretation. Leave unavailable values pending rather than estimating them.

## Event reaction lifecycle

Maintain `window.marketResearchData.eventReactions` for the highest-impact events.

Before the event record:

- official release and Melbourne-readable time
- previous value
- consensus only when reliably sourced; otherwise say no dependable free consensus is available
- upside, mixed and downside scenarios
- assets expected to react and current-regime transmission

After the event record:

- actual value and revisions
- surprise versus verified consensus when available
- immediate, market-close, +1 session and +5 session reactions
- verdict: confirmed, faded, reversed, structural or too early

Do not fill future reaction windows early. Preserve the original scenario for later review.

## Trigger proximity

Keep `site/data.js` synchronized with `thresholds.md`. Preserve warning, triggered, confirmed and invalidated as separate states. Never invent a current value; keep the prior verified value and mark freshness when a new value cannot be verified.

## News feed

Refresh `fallback.newsFeed` with three to eight decision-relevant stories. Each item must include:

- stable ID, category, High/Medium impact and status
- Melbourne-readable date/time
- concise headline and two-sentence summary
- exact source and URL
- three to six affected assets with expected direction under the current regime and reason
- First order, Second order, Cross asset and Confirmation/Invalidation channels

This is a delayed research digest, not a live wire. Keep active news to no more than 30 items.

## Political trackers

Use official House, Senate and executive-branch records as primary sources. Third-party tools may assist discovery but cannot override the filing.

For every verified transaction retain asset/ticker, transaction type, owner, trade date, filing date, statutory range, source URL and calendar-day lag. Keep late filings permanently. Never call a spouse trade the member’s personal trade or calculate performance before public filing.

For Trump policy events, classify threat, proposal, executive action, implementation, exemption, pause, retaliation or de-escalation. Include target, announcement date, effective date when verified, status, affected assets and transmission channel.

## Safety and quality

- Never invent a trade, holding, amount, date, return, source, owner, ticker, market price, physical reading or economic release.
- Preserve older verified items unless correcting a documented error.
- Escape apostrophes and maintain valid JavaScript.
- JavaScript and free-data workflows must pass before completion.
- Commit data updates to `main`; this triggers Pages deployment.
- Keep the research/not-financial-advice warning visible.
