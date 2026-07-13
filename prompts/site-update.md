# Dashboard Intelligence Data Update

Run this as part of every successful daily market brief after the written report is complete.

Update `site/intelligence-data.js` on `main` without changing the application code or styling.

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

## Trump tracker

Update policy events only when they are verified and market-relevant. Prioritise primary sources:

- White House presidential actions and fact sheets
- Federal Register
- USTR and Commerce releases
- official statements, followed by high-quality reporting for context

Classify each item as threat, proposal, executive action, implementation, exemption, pause, retaliation or de-escalation. Include target country/sector, announcement date, effective date when verified, current status, affected assets and the transmission channel.

Keep the tariff impact matrix structural. Do not mark a matrix row as an active policy unless a verified policy event exists.

For financial transactions, use only public financial disclosures or a licensed data source. State when accounts are third-party managed or discretionary. Never describe disclosure data as real-time or imply personal direction when that is not established.

## Nancy Pelosi tracker

Check for new official House Periodic Transaction Reports. Use the official filing as the primary source; third-party parsers can assist discovery but must not override the filing.

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

If no new verified filing exists, leave the existing trade history unchanged and update only the checked date.

## Safety and quality

- Never invent a trade, amount, date, return, source or ticker.
- Preserve older verified items unless correcting an error.
- Keep no more than 30 news items and 50 tracker events in the site file.
- Escape apostrophes and maintain valid JavaScript syntax.
- Commit the site-data update to `main`; this triggers GitHub Pages deployment.
- The dashboard must continue to say that this is research, not financial advice.
