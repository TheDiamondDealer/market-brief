# Dashboard Intelligence Data Update

Run this as part of every successful daily market brief after the written report is complete.

Update `site/intelligence-data.js`, `site/command-centre-data.js` and the research-controlled sections of `site/research-data.js` on `main` without changing application code or styling.

Do **not** manually overwrite `site/free-data.js` or `site/data/free-market-data.json`. Those files are produced by the free official-data workflow.

## Source hierarchy

Use this order of evidence:

1. official government, regulator, exchange, central-bank or company release
2. primary filing, report, speech or dataset
3. high-quality wire or financial publication for context
4. specialist commodity or industry publication
5. social media only as an unconfirmed discovery lead

For market-moving geopolitical or policy claims, prefer an official announcement or two independent reliable sources. Distinguish clearly between announced, proposed, enacted, effective, delayed, reversed and price-confirmed.

TradingView widgets are an external discovery layer only. Do not copy, scrape, parse or treat TradingView headlines, chart values or indicators as inputs to the bias engine. Independently verify any story discovered there.

## Command centre

Refresh `fallback.commandCentre` from the latest verified daily research.

Update:

- `updated` from the successful research run
- risk `state`, integer `score` from 0 to 100 and confidence label
- one concise risk summary
- one important contradiction or divergence
- three to six transparent risk inputs, each with reading, score and reason
- two to four conditions that would move the risk state back toward neutral or into a different regime
- the next high-impact event, Melbourne-readable time and regime-adjusted logic
- three to six material changes since the previous successful research state

The risk score is an interpretable summary, not a prediction probability. Do not increase precision beyond the quality of the underlying evidence.

## Asset bias engine

Refresh `fallback.assetBiases` for the actively monitored assets.

For each asset include:

- stable `id`, name, group and current research reference
- directional bias using cautious labels such as Bullish, Bearish, Neutral, Higher yields or Bullish / unstable
- confidence from 0 to 100
- integer total score derived from visible component scores
- primary driver
- COT or positioning state from `window.freeMarketData` when current; explicitly say stale, pending or unavailable otherwise
- next relevant event
- exact condition that would change the bias
- product link when the asset has a deep-dive page
- three to five visible components such as Macro, Rates, Physical, Positioning, China, Policy or Cross-asset
- each component must use a score from -2 to +2 and a one-sentence explanation

The total must equal the sum of the visible components. Confidence is based on agreement, evidence quality and confirmation—not on the absolute score alone. Preserve contradictions rather than forcing every input to agree.

Do not mechanically treat high COT percentile as bullish or low percentile as bearish. Decide whether positioning confirms momentum or creates contrarian crowding/liquidation risk.

## Rates and liquidity interpretation

Read the latest successful values from the free official-data cache. At minimum review:

- US 2-year, 5-year, 10-year and 30-year yields
- US 10-year real yield
- US 10-year inflation breakeven
- 2s10s and 5s30s curve spreads
- high-yield credit spread
- effective federal funds rate and SOFR
- trade-weighted US dollar

Classify the dominant reason yields moved:

- stronger or weaker growth
- inflation or inflation-risk premium
- tighter or easier policy expectations
- bond supply or term premium
- risk-off demand or forced deleveraging

Do not give a yield move one universal equity, gold or currency interpretation without identifying its cause.

## Physical commodity confirmation

Update the non-automatic readings in `window.marketResearchData.physicalChecklists` when verified evidence changes. Preserve automatic FRED and CFTC readings for the application to populate.

A futures-price move alone is not physical confirmation.

### Gold

Review real yields, US dollar, COT positioning, ETF flows, central-bank demand and regional physical premiums.

### Oil

Review Brent/WTI time spreads, gasoline and diesel cracks, commercial inventories, tanker/export flows, refinery utilisation, OPEC+ supply and managed-money positioning.

### Copper

Review LME/COMEX/Shanghai inventories, treatment charges, regional premiums, China grid/manufacturing demand, mine disruptions, scrap response and COT positioning.

### Silver

Review the gold/rates channel, industrial metals and manufacturing, COT, exchange inventories, physical premiums and ETF/bar-and-coin flows.

### Rare earths

Review individual NdPr, dysprosium and terbium prices, Chinese quotas/export controls, China versus ex-China premiums, magnet prices/lead times and ex-China project milestones.

For each updated item retain the exact source, observation date/freshness and one-sentence interpretation. If no dependable value is available, leave it pending rather than estimate it.

## Event reaction lifecycle

Maintain `window.marketResearchData.eventReactions` for the highest-impact scheduled and completed events.

Before the event record:

- official release name and Melbourne-readable time
- previous value
- consensus only when sourced from a reliable public source; otherwise state that no dependable free consensus is available
- upside, neutral/mixed and downside scenarios
- assets expected to react and current-regime transmission

After the event record:

- actual value and revisions
- surprise versus a verified consensus when available
- immediate reaction
- market-close reaction
- one-session reaction
- five-session reaction
- verdict: confirmed, faded, reversed, structural or too early

Do not fill future reaction windows early. Preserve the original pre-event scenario so later reviews can test whether the logic was correct.

## Trigger proximity

Keep `site/data.js` trigger references synchronized with the approved `thresholds.md` file.

A price touch is a warning unless the confirmation rule is satisfied. Preserve the distinction between:

- warning
- triggered
- confirmed
- invalidated

Never invent a current value. If the value cannot be verified, keep the prior verified value and mark its freshness clearly.

## News feed

Refresh `fallback.newsFeed` with the most decision-relevant three to eight stories from the daily research.

For each story include:

- unique stable `id`
- `category`: Macro, Politics, Energy, Precious, Equities, Battery, Bulk or FX
- `impact`: High or Medium; omit low-value filler
- `status`: New, Developing, Price-confirmed, Price-diverging or Too early
- event date/time in Melbourne-readable form
- concise headline
- two-sentence summary
- exact source name and URL
- `assets`: three to six assets, each with expected direction under the current regime and a one-sentence reason
- `channels`: First order, Second order, Cross asset and Confirmation/Invalidation

The feed is a delayed daily digest, not a live wire. Do not imitate another platform's wording or visual identity. Apply the live regime and sign-flips from `regime-state.md`.

## Political trackers and stock-first search

The stock-first search reads directly from every tracker's `trades` and `portfolio.holdings` arrays. No separate search index is required.

When importing disclosures:

- keep ticker and company description together where possible, for example `NVDA — NVIDIA Corp`
- preserve transaction date, filing date, disclosure lag, owner/account, amount range and source URL
- retain historical records permanently, including late filings
- update portfolio holdings only from verified annual disclosures and subsequent verified transactions
- keep member, spouse, joint, dependent, trust and managed-account labels exact

This automatically makes the transaction discoverable from both the politician page and the stock-first reverse search.

## Trump tracker

Update policy events only when they are verified and market-relevant. Prioritise primary sources:

- White House presidential actions and fact sheets
- Federal Register
- USTR and Commerce releases
- official statements, followed by high-quality reporting for context

Classify each item as threat, proposal, executive action, implementation, exemption, pause, retaliation or de-escalation. Include target country/sector, announcement date, effective date when verified, current status, affected assets and the transmission channel.

Keep the tariff impact matrix structural. Do not mark a matrix row as an active policy unless a verified policy event exists.

For financial transactions, use only public financial disclosures or a licensed data source. State when accounts are third-party managed or discretionary. Never describe disclosure data as real-time or imply personal direction when that is not established.

## Congressional trackers

Check for new official House and Senate transaction reports and annual disclosures. Use the official filing as the primary source; third-party parsers can assist discovery but must not override the filing.

For each verified transaction include:

- asset/ticker and asset description
- purchase, sale, exchange or option exercise
- owner exactly as disclosed
- transaction date
- filing date
- statutory amount range
- source filing URL
- disclosure lag in calendar days

Do not call a spouse transaction the member's personal trade. Do not use the filing date as the trade date. Do not calculate performance before the filing became public; avoid look-ahead bias.

If no new verified filing exists, leave the complete trade history and portfolio unchanged and update only the checked date.

## Safety and quality

- Never invent a trade, holding, amount, date, return, source, owner, ticker, market price, physical-market reading or economic release.
- Preserve older verified items unless correcting a documented error.
- Keep no more than 30 news items in the active feed; political transactions use annual archives rather than deletion.
- Escape apostrophes and maintain valid JavaScript syntax.
- The repository JavaScript and free-data validation workflows must pass before treating the update as complete.
- Commit the research-data update to `main`; this triggers GitHub Pages deployment.
- The dashboard must continue to say that this is research, not financial advice.
