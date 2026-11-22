# Workflow helper scripts

These files are **implementation helpers**, not a separate public command API. Public interfaces are described in [docs/api.md](../docs/api.md) and the [workflow index](../.github/workflows/README.md).

| File | Owner and reason for existence |
| --- | --- |
| `reusable_ci.py` | GitHub Actions bootstrap, library pin resolution, environment forwarding, plan/run argument adaptation and workflow output exchange. Durable scope state/publication is delegated to `cad_ci.durable`; no manifest or build-store semantics live here. |
| `merge_policy.py` | Pure branch-role classification; no GitHub API writes. The merge-governance product boundary is under review in issue #110. |
| `merge_command.py` | GitHub API adapter for normal/reviewed-resolved merge readiness, validation gates, exact ref mutation, post-merge lifecycle and reporting. See `docs/background/merge-policy.md`. |\n| `merge_resolution.py` | Pure parser and exact tree/parent verification for owner-reviewed conflicted permanent-ref recovery; no GitHub writes. |
| `publish_release.py` | Repository release maintenance; not used by consumers as a supported API. |

A helper becomes public only by an explicit API decision, documentation, tests and a compatible release. Do not add another script to work around a missing library API; file the library requirement first. Do not move large business logic into workflow inline Bash as a substitute for a proper implementation boundary.

Changes to these helpers need traceable requirements/design justification and behavioral tests. See [AGENTS.md](../AGENTS.md).
