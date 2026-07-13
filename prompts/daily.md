# Daily Market Brief

Use GPT-5.6 Terra with maximum reasoning. Run unattended and do not ask questions.

Read from `TheDiamondDealer/market-brief` on `main`:

- `baseline-dossier.md`
- `regime-state.md`
- `thresholds.md`
- The three most recent files in `brief-log/`

If the baseline still says BOOTSTRAP REQUIRED, stop and post a warning to private Slack channel `#market-brief`.

Research the last seven days, prioritising the last 24 hours. Confirm dates and exact source URLs. Prefer primary and authoritative sources. Never invent prices, dates, consensus values, sources or links. Give extra analytical weight to gold and silver without omitting material moves elsewhere.

Lead with the macro spine: DXY; US 10-year nominal and real yields; current Fed meeting probabilities; USD/JPY and AUD/JPY carry health; US index futures; relevant Asian markets. Then separately examine precious metals, battery/transition and bulk commodities, energy, equities, FX and central banks.

Apply the active regime and sign-flips. If a relationship cuts both ways, state the net regime-adjusted effect. Lead with any threshold breached. If the latest daily log is not the previous expected trading day, apply a catch-up rule and label missed developments by date.

Produce:

1. LISTEN: the three to five developments that actually moved the book, biggest first, each with a plain-language “so what.”
2. DIG IN: Macro & FX; Precious; Battery & Bulk; Energy; Equities. Each genuine catalyst includes headline, exact source link, impact direction, conviction and transmission mechanism.
3. ON THE RADAR: today's and this week's scheduled catalysts, with consensus/prior only when verified. Flag the highest-stakes event.

No buy or sell calls. Do not pad inactive sections.

Write the complete report to `brief-log/brief-YYYY-MM-DD.md` on `main`. If the regime materially shifted, update `regime-state.md` with a dated note at the top while preserving useful history.

Post LISTEN as the parent message in private Slack channel `#market-brief`. Post DIG IN and ON THE RADAR as threaded replies, splitting long content into readable messages. If completion fails, post a warning with the reason when Slack remains available.
