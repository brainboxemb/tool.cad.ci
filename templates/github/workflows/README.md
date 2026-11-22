# Consumer workflow templates

These files are the canonical GitHub Actions starting points for repositories
that consume `tool.cad.ci`.

Every template has a stable template id and integer template version in its
header. The same values are recorded in [the template manifest](../../manifest.json).

| Template | Use when |
| --- | --- |
| `cad-ci.yml` | The workflow only needs a normal read-only CAD-CI run. |
| `cad-ci-lanes.yml` | PR validation uses stable `main` plus permanent `dev-cad` / `dev-ci` lanes with docs-only skip and full promotion validation. |
| `cad-ci-pr.yml` | The repository wants the complete one-runner PR lifecycle, including optional PR build publication/cleanup. |
| `cad-ci-same-runner.yml` | Repository-owned steps must run after CAD-CI in the same job/workspace. |
| `merge-policy.yml` | The repository uses the shared owner-issued `/merge` governance policy. Current template version 2 includes the required caller permission ceiling. |

Copy the chosen file into the consumer repository under
`.github/workflows/`, replace `TOOL_CAD_CI_RELEASE_SHA` with one exact
released commit from this repository, then change only documented
repository-owned configuration.

Do not copy checkout/bootstrap, changed-path classification, SCons execution,
durable build-store logic or GitHub merge implementation into a consumer.
If a new consumer needs generic behavior not represented by these templates,
change and release `tool.cad.ci` first.
