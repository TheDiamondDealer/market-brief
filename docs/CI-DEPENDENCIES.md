# CI dependency policy

## Immutable GitHub Actions

Every external `uses:` reference under `.github/workflows/` must use a full 40-character commit SHA. Human-readable major or release labels remain as comments only.

Current pinned Actions:

- `actions/checkout` — `11bd71901bbe5b1630ceea73d27597364c9af683` (`v4.2.2`)
- `actions/setup-python` — `a26af69be951a213d495a4c3e4e4022e16d87065` (`v5`)
- `actions/setup-node` — `49933ea5288caeca8642d1e84afbd3f7d6820020` (`v4`)
- `actions/upload-artifact` — `ea165f8d65b6e75b540449e92b4886f43607fa02` (`v4`)
- `actions/configure-pages` — `983d7736d9b0ae728b81ab479565c72886d7745b` (`v5`)
- `actions/upload-pages-artifact` — `56afc609e74202658d3ffba0e8f6dda462b719fa` (`v3`)
- `actions/deploy-pages` — `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` (`v4`)

Local reusable workflows such as `./.github/workflows/deploy-pages.yml` are exempt from external SHA syntax because they are versioned inside this repository.

## Python dependency files

- `requirements/validation.txt` — schema and semantic validation.
- `requirements/political.txt` — political collectors plus validation.
- `requirements/ci.txt` — complete offline PR test environment.

Direct dependencies must use exact `==` versions. Workflows must install through the relevant requirement file and run `python -m pip check`.

## Enforcement

`scripts/check_ci_pins.py` fails when:

- an external Action uses a branch, tag or shortened SHA;
- a workflow installs named Python packages directly instead of using `requirements/`;
- a direct requirement is not pinned with `==`.

The script runs in the required `offline-validation` job and in both collector workflows. Pin failures are uploaded as a short-lived workflow artifact; invalid output is never committed merely to retain diagnostics.

## Updating dependencies

Dependabot proposes weekly grouped Python and GitHub Actions updates. Review the upstream change, preserve immutable Action SHAs, run the full required gate and merge only when the generated-data and parser tests remain green.
