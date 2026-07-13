# Dashboard Intelligence Data Update

Run this as part of every successful daily market brief after the written report is complete.

Update `site/intelligence-data.js` on `main` without changing the application code or styling. Political transaction archives and portfolio ledgers must follow the rules below.

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

## Permanent political transaction history

Never discard a verified transaction because it is old or because it was disclosed late.

For both Trump and Pelosi trackers:

- retain every verified historical transaction permanently
- use the actual transaction date for chronology
- keep filing date as a separate field
- calculate and store disclosure lag in calendar days
- import a transaction even when it was filed 45 days or more after execution
- preserve the owner or account exactly as disclosed
- preserve the statutory amount range rather than inventing an exact value
- preserve the original filing URL
- de-duplicate using person + owner/account + asset + transaction type + transaction date + amount range + filing identifier
- sort the visible history by transaction date, newest first, but never delete older rows

When a tracker exceeds 500 transactions in the active file, move older verified rows into annual files under:

- `site/trades/trump-YYYY.js`
- `site/trades/pelosi-YYYY.js`

Each archive file must append records into the relevant tracker array. Load archive files before `intelligence-app.js`. The application paginates in groups of 100; do not truncate the underlying dataset.

## Portfolio reconstruction

Maintain `tracker.portfolio.holdings` for both Trump and Pelosi.

Rebuild the portfolio from:

1. the latest verified annual holdings disclosure as the opening baseline
2. every verified subsequent purchase, sale, exchange and option exercise
3. later annual disclosures used to reconcile and correct the ledger

For each holding store:

- asset/ticker and description
- owner or account exactly as disclosed
- latest disclosed or estimated amount range
- status: estimated open, reduced, closed, option exposure, fund exposure or unresolved
- last activity date
- confidence: high, medium or low
- source filing URL

Important limitations:

- disclosure ranges are not exact position sizes
- options cannot be converted into ordinary-share exposure without verified contract details
- a sale may reduce rather than fully close a position
- transfers, exchanges and annual-report reconciliation can change the inferred ledger
- do not call the result an exact portfolio or brokerage balance
- label it `Estimated current portfolio — disclosure-derived`

When evidence is insufficient, keep the position as unresolved rather than guessing.

## Trump tracker

Update policy events only when they are verified and market-relevant. Prioritise primary sources:

- White House presidential actions and fact sheets
- Federal Register
- USTR and Commerce releases
- official statements, followed by high-quality reporting for context

Classify each policy item as threat, proposal, executive action, implementation, exemption, pause, retaliation or de-escalation. Include target country/sector, announcement date, effective date when verified, current status, affected assets and the transmission channel.

Keep the tariff impact matrix structural. Do not mark a matrix row as an active policy unless a verified policy event exists.

For financial transactions and holdings:

- use official ethics filings and annual financial disclosures as primary records
- licensed or reputable parsers may assist discovery and reconciliation
- keep trust, personal, spouse, family, managed-account and discretionary-account labels distinct
- state when investment decisions are reported as third-party managed or discretionary
- never imply that Trump personally selected a transaction unless the filing establishes that

## Nancy Pelosi tracker

Check for new official House Periodic Transaction Reports and annual financial disclosures. The official filing is the primary source; third-party parsers can assist discovery but must not override it.

For each verified transaction include:

- asset/ticker and asset description
- purchase, sale, exchange or option exercise
- owner exactly as disclosed: member, spouse, joint or dependent
- transaction date
- filing date
- statutory amount range
- source filing URL
- disclosure lag in calendar days

Do not call a spouse transaction Nancy Pelosi's personal trade. Do not use the filing date as the trade date. Do not calculate performance before the filing became public; avoid look-ahead bias.

If no new filing exists, leave the complete trade history and portfolio unchanged and update only the checked date.

## Safety and quality

- Never invent a trade, holding, amount, date, return, source, owner or ticker.
- Preserve every older verified transaction unless correcting a documented error.
- Keep no more than 30 news items in the active site file; political trades use annual archives instead of deletion.
- Escape apostrophes and maintain valid JavaScript syntax.
- Commit the site-data update to `main`; this triggers GitHub Pages deployment.
- The dashboard must continue to say that this is research, not financial advice.
