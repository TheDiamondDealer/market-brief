# BR-03 completion checklist

- [x] Required pull-request validation workflow exists.
- [x] Merge-queue validation trigger exists.
- [x] External GitHub Actions are pinned to immutable commit SHAs.
- [x] Python dependencies are installed from exact-version requirement files.
- [x] Dependency and Action updates are proposed by Dependabot.
- [x] CI proves broken JavaScript is rejected.
- [x] CI proves malformed JSON is rejected.
- [x] CI proves empty or malformed political retained history is rejected.
- [x] Owner repository-protection steps are documented.
- [ ] Owner has activated the `main` ruleset and completed the acceptance drill in `docs/REPOSITORY-PROTECTION.md`.

The final unchecked item is a GitHub repository setting, not a repository file change. Do not claim active branch protection until the owner records the drill results.
