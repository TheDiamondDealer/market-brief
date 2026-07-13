# Manual Monthly Approval

This is never scheduled. Run it only after the user explicitly identifies a monthly draft and says to approve or promote it.

1. Read the proposed files in `monthly/YYYY-MM/`.
2. Read the current live `baseline-dossier.md`, `regime-state.md` and `thresholds.md`.
3. Produce a concise change summary covering:
   - Regime change.
   - Threshold changes.
   - Major structural additions/removals.
   - Material source or methodology changes.
4. Ask for confirmation if the user's approval was not already explicit and unambiguous.
5. After explicit approval, replace the three live files with the approved drafts.
6. Preserve the monthly draft folder as the audit trail.
7. Commit with message: `Approve monthly strategic frame YYYY-MM`.
8. Post a short confirmation to private Slack channel `#market-brief` with the approved regime and thresholds.

Never promote a partial draft, a file containing an error marker, or a draft whose month was not identified.
