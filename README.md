# Market Brief

A subscription-only commodities and markets briefing system operated by ChatGPT Scheduled Tasks.

## Delivery

- Daily: weekdays at 8:30 AM Australia/Melbourne
- Weekly: Sunday at 9:05 AM Australia/Melbourne
- Monthly: first weekday at 9:10 AM Australia/Melbourne
- Slack: private channel `#market-brief`
- Model preference: GPT-5.6 Terra, maximum reasoning

## Repository memory

- `baseline-dossier.md`: durable market structure and mechanisms
- `regime-state.md`: current macro regime and active sign-flips
- `thresholds.md`: levels that should lead a report when breached
- `brief-log/`: daily reports
- `weekly-log/`: weekly reports
- `monthly/`: human-reviewable monthly drafts
- `prompts/`: durable instructions used by scheduled tasks

The monthly task never overwrites live knowledge files. It creates drafts for review.
