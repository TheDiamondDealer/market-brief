# Weekly Commodities & Markets Review

Use GPT-5.6 Terra with maximum reasoning. Run unattended and do not ask questions.

Regions: United States, Australia, China and Japan.

Assets: use the exact tracked-asset list and grouping defined in `prompts/daily.md`. Do not silently add or remove assets. Give extra analytical weight to gold and silver.

Directional language means expected price pressure under the stated regime; it is analysis, not a trading signal or recommendation.

## Read first — do not re-derive the frame

Read from `TheDiamondDealer/market-brief` on `main`:

- `operating-model.md`
- `baseline-dossier.md` — durable mechanisms and structure, especially Parts 1–3
- `regime-state.md` — current regime and active sign-flips
- `thresholds.md` — active headline levels and risk zones
- all dated daily briefs in `brief-log/` from the last seven days

Then use current web research only to fill gaps, confirm developments and verify Friday closing levels. Prefer primary and authoritative sources. Never invent figures, dates, consensus estimates or links.

Produce a step-back synthesis, not five daily reports stapled together.

## REGIME DASHBOARD — first

Create a compact dashboard:

- **Regime:** label plus intact / shifting / broken.
- **Change this week:** strengthened / weakened / unchanged, with one sentence of evidence.
- **Risk tone:** risk-on / risk-off / mixed.
- **Volatility:** calm / elevated / dislocated.
- **Gold vs real yields:** confirmed / diverging / inconclusive.
- **Oil vs inflation expectations:** confirmed / diverging / inconclusive.
- **Yen carry health:** healthy / stretched / deteriorating / unwind.
- **China demand impulse:** improving / flat / weakening / unclear.
- **Price-confirmation score:** number of the week’s major catalysts that aligned, diverged or remain too early.
- **Complex bias for the coming week:** asset-specific upward / downward / mixed pressure with confidence and the single decisive condition. Do not create a single whole-market buy/sell label.

## TL;DR — THE WEEK IN 5 LINES

Write five plain, listenable lines covering the week’s net story and the single most important issue for the week ahead.

## WEEK IN REVIEW

- Net Monday-to-Friday close move for each tracked asset, grouped under Precious; Battery & Bulk; Energy; Equities; and Macro & FX. Show percentage changes where valid and do not substitute daily noise.
- Explain the two or three themes that actually drove the week. Separate signal from noise.
- Identify the biggest winners and losers across tracked assets.

## REACTION AUDIT — expected versus actual

For the three to five catalysts that mattered most, use:

| Catalyst | Expected under live regime | Actual cross-asset reaction | Verdict | What it reveals |
| --- | --- | --- | --- | --- |
| verified event | directional transmission | verified move and window | confirmed / diverged / too early | regime, positioning or liquidity insight |

Do not back-fit the expected reaction after seeing the move. Base it on `regime-state.md`, the prior daily log or the durable mechanism in the dossier.

## WHAT CHANGED — STRUCTURE, REGIME AND RISK ZONES

- State whether any active threshold or risk zone was entered, breached or exited during the week and whether it held into Friday’s close.
- For the most relevant zones show the Monday starting position, Friday ending position, confirmation/invalidation and what the transition means.
- Test whether the regime in `regime-state.md` remains intact.
- Assess material changes in correlations, central-bank tone, positioning and active sign-flips.
- If the regime is materially shifting or broken, say so at the top of the report and update `regime-state.md` with a dated change note, evidence and explicit flip conditions. Do not change the regime for ordinary volatility.
- Never manufacture zone bands; use only `thresholds.md`.

## CROSS-CURRENTS

Explain the most important developing cross-asset or cross-region threads, such as China demand into iron ore and AUD, or BOJ/yen into carry and global risk.

## THE WEEK AHEAD

Build a verified calendar for the coming Monday–Friday, including major data, central-bank decisions and speeches, relevant expiries, auctions and policy events.

For each event include:

- confirmed date and local release time, with Melbourne time where useful
- consensus and prior where available
- tracked assets most exposed
- regime-adjusted directional logic, including sign-flips or inverted relationships
- the price or policy evidence that would confirm or invalidate the interpretation

Flag the single highest-stakes event and add a three-row scenario map:

| Scenario | What would qualify | Regime-adjusted transmission | Exposed assets | Confirmation / invalidation |
| --- | --- | --- | --- | --- |
| Upside / hotter / hawkish | verified condition | mechanism | assets and directional pressure | price or policy evidence |
| In line / base case | verified condition | mechanism | assets and directional pressure | price or policy evidence |
| Downside / softer / dovish | verified condition | mechanism | assets and directional pressure | price or policy evidence |

Use event-appropriate labels. This is scenario analysis, not a forecast.

## CONVICTION SHIFTS

Explain which analytical setups became more or less compelling and why. Tie each shift to price confirmation, divergence, positioning or a risk-zone transition. This is analysis, not a recommendation or buy/sell instruction.

## Output and delivery

- Save the full report to `weekly-log/weekly-YYYY-Www.md`, using the ISO week number.
- Commit any justified weekly regime-state amendment in the same run.
- Post REGIME DASHBOARD followed by THE WEEK IN 5 LINES as the parent message in private Slack channel `#market-brief` (channel ID `C0BGV46RLES`).
- Post the remaining sections as threaded replies and include a link to the GitHub report.
- If completion fails, post a concise warning to Slack when Slack remains available.

Rules: separate confirmed news from forecasts; apply the live regime filter; cite material claims; date point-in-time facts; state uncertainty; not financial advice.
