# Repository protection owner checklist

## Status

The repository contains the required pull-request validation workflow, immutable Action references and pinned Python dependency files. GitHub repository rules are account settings and must be applied by the repository owner after BR-03 merges.

Do not mark BR-03 protection complete until the acceptance drill at the end of this document has been performed.

## Required check

The required pull-request check is:

```text
offline-validation
```

It is defined in `.github/workflows/validate.yml` and covers JavaScript syntax, Python compilation, generated JSON schemas, semantic validation, workflow contracts, dependency pins, routes and offline fixtures.

## Create a ruleset for `main`

In GitHub:

1. Open **Settings → Rules → Rulesets**.
2. Create a new branch ruleset named `Protect main`.
3. Set enforcement to **Active**.
4. Target the default branch or include only `main`.
5. Enable **Require a pull request before merging**.
6. For a sole-owner repository, begin with zero required approvals. Increase to one approval after adding a second trusted maintainer; do not create a rule that the only maintainer cannot satisfy.
7. Enable **Require status checks to pass** and select `offline-validation` from a recent pull request run.
8. Enable **Require branches to be up to date before merging**.
9. Enable **Require conversation resolution before merging**.
10. Block force pushes and branch deletion.
11. Do not enable signed-commit enforcement until generated-data bot commits have an approved signing mechanism.

## Generated-data workflow bypass

The free-market and political collectors intentionally create validated generated-data commits directly on `main`. A blanket pull-request requirement will block those commits unless the ruleset has a narrowly scoped automation bypass.

Use this order of preference:

1. Add the **GitHub Actions** app as a ruleset bypass actor if the repository UI makes that actor available.
2. Grant bypass only for the `main` ruleset and retain the collectors’ least-privilege workflow permissions.
3. Do not add broad user, team or public-app bypasses.
4. If a safe GitHub Actions bypass is unavailable, do not activate the pull-request requirement yet. First migrate generated-data publication to a dedicated GitHub App or pull-request-based promotion workflow.

The bypass is acceptable only because both collector workflows:

- share the `generated-data-writer` queue;
- validate before commit;
- rebase and validate again before push;
- stop on collection, schema, semantic, syntax or rebase failure;
- deploy current `main` explicitly after success.

## Actions settings

In **Settings → Actions → General**:

- Keep the default workflow token permission read-only where the repository setting allows it. Individual workflows declare their required permissions explicitly.
- Do not allow GitHub Actions to create or approve pull requests unless a future reviewed workflow genuinely needs that capability.
- Restrict third-party Actions to approved sources. Repository workflows additionally pin every external Action to an immutable 40-character commit SHA.

## Dependency update process

`.github/dependabot.yml` opens weekly grouped pull requests for:

- Python dependencies under `requirements/`;
- GitHub Actions references.

Every dependency update must pass `offline-validation`. Action updates must remain pinned to a full commit SHA; dependency updates must remain exact `==` pins.

## Acceptance drill

After the ruleset is active, create temporary pull requests that perform each of the following one at a time:

1. Add a JavaScript syntax error to a production `site/*.js` file.
2. Malform one committed generated JSON file.
3. Empty Pelosi retained history or insert a known malformed marker such as `Name: Hon.` into a political asset row.

For every temporary pull request, confirm:

- `offline-validation` fails;
- GitHub blocks merge while the check is failing;
- restoring the valid file makes the check pass;
- no generated-data collector or Pages deployment publishes the invalid branch.

Close the temporary pull requests without merging.

## Owner completion record

Record the result in the BR-03 pull request or a repository issue:

```text
Ruleset active date:
Required check selected:
GitHub Actions bypass actor:
Broken-JS drill blocked merge: yes/no
Malformed-JSON drill blocked merge: yes/no
Invalid-political drill blocked merge: yes/no
Owner completing checklist:
```
