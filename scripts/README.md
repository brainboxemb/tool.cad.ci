# Workflow helper scripts

These files are **implementation helpers**, not a separate public command API. Public interfaces are described in [docs/api.md](../docs/api.md) and the [workflow index](../.github/workflows/README.md).

| File | Owner and reason for existence |
| --- | --- |
| `reusable_ci.py` | GitHub Actions bootstrap, library pin resolution, environment forwarding, plan/run argument adaptation and workflow output exchange. Durable scope state/publication is delegated to `cad_ci.durable`; no manifest or build-store semantics live here. |
| `merge_policy.py` | Pure branch-role classification; no GitHub API writes. The merge-governance product boundary is under review in issue #110. |
| `merge_command.py` | GitHub API adapter for merge readiness, validation gates, exact-SHA merge, post-merge lifecycle and reporting. See `docs/merge-policy.md`. |
| `publish_release.py` | Repository release maintenance; not used by consumers as a supported API. |

A helper becomes public only by an explicit API decision, documentation, tests and a compatible release. Do not add another script to work around a missing library API; file the library requirement first. Do not move large business logic into workflow inline Bash as a substitute for a proper implementation boundary.

Changes to these helpers need traceable requirements/design justification and behavioral tests. See [AGENTS.md](../AGENTS.md).


## Reusable durable-lane helpers

`scripts/reusable_ci.py durable-state` and `durable-publish` are internal
phases of the public `reusable-durable.yml` workflow.

They are not separate consumer APIs. `durable-state` delegates complete-scope
resolution to the pinned library before the single SCons run.
`durable-publish` delegates build-scope and optional configured Pages
publication to that same library afterward.
