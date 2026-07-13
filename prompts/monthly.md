# Monthly Strategic Refresh

Use GPT-5.6 Terra with maximum reasoning and deep research. Run unattended and do not ask questions during research.

This is the strategic reset that the daily and weekly routines read from. The live baseline must remain unchanged until the user explicitly approves the draft.

Regions: United States, Australia, China and Japan.

Assets: use the exact tracked-asset list and grouping defined in `prompts/daily.md`. Do not silently add or remove assets. Give extra analytical weight to gold and silver.

## Read first

Read from `TheDiamondDealer/market-brief` on `main`:

- `operating-model.md`
- live `baseline-dossier.md`
- live `regime-state.md`
- live `thresholds.md`
- the last four or five reports in `weekly-log/`
- the prior monthly draft and review, if present

Use extensive multi-source research. Prefer primary sources, including central banks, statistical agencies, exchanges, regulators, EIA/IEA, OPEC, company filings and authoritative industry bodies. Date all point-in-time facts, separate facts from forecasts and never invent figures or links.

## Job 1 — regenerate the baseline dossier

Prepare a complete proposed five-part dossier:

1. Re-verify durable structural facts in Parts 1–3: supply shares, benchmarks, market mechanisms, transmission channels and key producers. Correct anything that changed.
2. Fully refresh Part 4, State of Play: current levels, dominant narrative by tracked asset and live cross-region threads, dated to the run.
3. Refresh Part 5 and the source list when better or more current sources are available.
4. Mark uncertain, estimated or contested figures explicitly.
5. Preserve useful durable material unless evidence justifies changing it.

## Job 2 — monthly strategic review

Include a one-page “What changed this month” summary first, followed by:

- the month’s net moves and defining narrative
- REGIME ASSESSMENT: explicitly classify the regime as intact, shifting or broken versus last month; give evidence and state exactly what would flip the verdict
- a proposed rewrite of `regime-state.md`, including active sign-flips
- RESET TRIGGER THRESHOLDS: propose current, decision-useful “lead the brief if breached” levels for at least gold, Brent, ASX 200, policy/hike odds and USD/JPY; explain why each level matters
- a proposed rewrite of `thresholds.md`
- structural shifts during the month, including relevant developments such as Simandou, Indonesian quotas, central-bank gold buying and OPEC+ policy
- one-to-three-month outlook by complex and the key swing factor for each
- a verified month-ahead major catalyst calendar with consensus and prior where available

## Mandatory human approval gate

Do not overwrite `baseline-dossier.md`, `regime-state.md` or `thresholds.md`.

Write drafts to:

- `monthly/YYYY-MM/baseline-dossier-DRAFT.md`
- `monthly/YYYY-MM/regime-state-DRAFT.md`
- `monthly/YYYY-MM/thresholds-DRAFT.md`
- `monthly/YYYY-MM/strategic-review.md`

Clearly label every draft as awaiting human approval. The live files may only be replaced by the separate manual workflow in `prompts/approve-monthly.md` after explicit user approval.

## Delivery

- Post the one-page “What changed this month” summary as the parent message in private Slack channel `#market-brief` (channel ID `C0BGV46RLES`).
- Post the remaining review as threaded replies with links to all draft files.
- State clearly that the live baseline, regime and thresholds have not changed and await approval.
- If the run cannot complete, post a concise warning to Slack when Slack remains available.

Rules: cite material claims; prioritize primary sources; confirm event dates at source; date point-in-time facts; separate facts from forecasts; flag inverted or regime-dependent relationships; state uncertainty; not financial advice.
