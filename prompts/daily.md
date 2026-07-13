# Daily Commodities & Markets Brief

Use GPT-5.6 Terra with maximum reasoning. Run unattended and do not ask questions.

This is the tactical layer of the cascade. Explain what moved overnight, why it moved under the current regime, and what matters next. Do not re-derive durable market structure.

## Canonical scope

Regions: United States, Australia, China and Japan.

Tracked assets and drivers:

- Precious: gold, silver, platinum, palladium.
- Battery and transition: lithium, uranium, copper, nickel.
- Bulk: iron ore, thermal coal, coking coal.
- Energy: Brent, WTI, Henry Hub natural gas, European TTF gas.
- Equities: S&P 500, Nasdaq and ASX 200; flag material moves in ASX materials and energy.
- Macro and FX drivers: DXY, US 10-year nominal yield, US 10-year real yield, AUD/USD, USD/JPY, AUD/JPY and USD/CNY.
- Policy: Fed/FOMC, RBA, BOJ and PBOC.
- Watch bucket: zinc, tin, aluminium, rare earths, graphite, cobalt or another commodity only when there is an outsized, decision-relevant move.

This list is canonical for the weekly and monthly routines. Do not silently add or remove tracked assets. Give extra analytical weight to gold and silver without omitting material moves elsewhere.

## Step 0 — load the existing frame

Read from `TheDiamondDealer/market-brief` on `main`:

- `operating-model.md`
- `baseline-dossier.md` — trust its durable mechanisms; treat its dated State of Play as last known, not live
- `regime-state.md` — current regime and active sign-flips
- `thresholds.md` — active “lead the brief if breached” levels
- the three most recent dated files in `brief-log/`

If `baseline-dossier.md` still says `BOOTSTRAP REQUIRED`, stop and post this warning to Slack: “WARNING — Daily brief: baseline bootstrap has not completed.”

## Step 1 — apply the regime filter

Apply the live regime and sign-flips to every impact assessment.

For example, when the regime is hawkish or hiking-biased:

- hot CPI/PCE can be net bearish for gold when the real-yield and Fed channel dominates
- strong employment can be risk-negative when good news is bad news
- an oil spike must include the potential Fed-hawkish drag, not only the inflation-hedge effect

If the regime has changed, follow `regime-state.md`, not these examples. When a catalyst cuts both ways, state both channels and give the net regime-adjusted effect.

## Step 2 — current research

Research the last seven days, prioritising the last 24 hours and the overnight session.

Lead with the macro spine in this order:

1. DXY.
2. US 10-year nominal and real yields.
3. Current Fed meeting probabilities from a verified source.
4. USD/JPY and AUD/JPY carry health.
5. S&P 500 and Nasdaq futures or latest closes.
6. Relevant Asian trading, especially Nikkei and China; include KOSPI only when materially relevant.

Then research each tracked complex separately. Rotate search angles to avoid repeating stale stories.

Confirm every story’s publication date and event date. Prefer primary and authoritative sources. Discard undated claims and items older than seven days unless they are a major developing thread. Never invent prices, statistics, consensus values, dates, sources or links.

## Step 3 — catch-up and de-duplication

If the latest daily log is not the previous expected trading day, surface the most important missed developments since that log and label each by date.

Tag material stories as:

- `NEW`
- `DEVELOPING — first flagged YYYY-MM-DD`

Do not repeat yesterday’s story unless its facts, market impact or conviction materially changed.

## Headline triggers

Lead the brief when any active level in `thresholds.md` is breached. Also lead when:

- relevant Fed probability moves more than 10 percentage points in one day
- USD/JPY breaches its active threshold or the yen moves 3% or more in a carry-unwind episode
- a credible and sized China stimulus package is announced
- a regime-defining central-bank surprise or cross-asset correlation break occurs

State whether the breach was intraday only or held at the latest verified close.

## Output

### LISTEN

Give the three to five developments that actually moved the tracked book overnight, biggest first. Use plain spoken sentences suitable for listening. Each item must include a one-line “so what.” Lead with any triggered headline.

### DIG IN

Group genuine catalysts under:

- Macro & FX
- Precious
- Battery & Bulk
- Energy
- Equities

For each catalyst use:

> Headline — Source with exact link  
> Impact: Asset up / down / mixed | Conviction: high / medium / low  
> Why: one or two sentences explaining the transmission mechanism and net regime-adjusted effect.

If a complex has no meaningful new catalyst, say so in one line. Do not pad inactive sections.

### ON THE RADAR

List today’s and this week’s scheduled catalysts. Include confirmed date and release time, consensus and prior only when verified, exposed assets, and regime-adjusted directional logic. Flag the single highest-stakes event.

## Save and deliver

- Use the Melbourne calendar date for the report.
- Save the complete brief to `brief-log/brief-YYYY-MM-DD.md` on `main`.
- If the regime materially shifted, update the top of `regime-state.md` with a dated note, evidence and explicit flip conditions. Do not change it for ordinary volatility.
- Post LISTEN as the parent message in private Slack channel `#market-brief` (channel ID `C0BGV46RLES`).
- Post DIG IN and ON THE RADAR as threaded replies, splitting long sections into readable messages.
- Include a link to the GitHub report.
- If the run cannot complete, post: “WARNING — Daily brief: run issue — [reason]” when Slack remains available.

Rules: be direct and analytical; separate confirmed news from rumours and forecasts; cite material claims; state uncertainty; no buy or sell calls; not financial advice.
