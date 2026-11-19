# Requirements

## Repository ownership

- Consumer repositories own `cad-ci.yml`, item `ci.yml`, commands and domain rules.
- `tool.cad.ci` is a thin CLI above one exact released `lib.py.cad.ci` commit.
- Generic execution, build-store, Pages and publication mechanics are not duplicated here.

## Planning

- Changed-file selection is performed by the library.
- `cad-ci plan` can show selected items and required dependency closure.
- A plan is explanatory and does not claim SCons target freshness.

## Running

- One `cad-ci run` command calls the library's `run_repository()` once.
- SCons owns dependency traversal, signatures, incremental decisions and cache reuse.
- `--step`, `--until` and `--from` are mutually exclusive.
- The tool forwards partial selectors to the library without adding its own state rules.
- Run output/evidence layout is defined by the library.

## Durable build output

- Candidate output mirrors item source paths below local `build/`.
- Complete item evidence lives below `<item>/.cad-ci/item.json`.
- Build preparation passes current loaded Item objects to the library.
- `build/main` is a complete accepted baseline.
- `build/pr/<number>` is a sparse overlay of selected top-level items only.
- Runtime SCons dependencies are not automatically added to a sparse overlay.
- Resolve/update/cleanup semantics are owned by the library.

## Pages and generated branches

- Stable Pages lives at the `gh-pages` root.
- PR previews live below `previews/pr-<number>/`.
- Generated branches are never force-pushed.
- Source freshness and retry behaviour are implemented in the library.

## Reusable GitHub Actions

- `tool.cad.ci` provides reusable `workflow_call` workflows for generic planning and execution.
- A consumer references those workflows at one exact tool commit SHA.
- The called workflow checks out its own tool source using `job.workflow_repository` and `job.workflow_sha`; workflow and tool implementation therefore cannot drift.
- The called workflow checks out the caller repository at the real source commit, not a temporary PR merge ref.
- `reusable-plan.yml` exposes the compact generic item plan for consumers that need domain setup between planning and execution.
- `reusable-run.yml` restores/saves `.cache/cad-ci/` and performs exactly one `cad-ci run`.
- Optional consumer environment input is non-secret, validates variable names, and cannot overwrite GitHub/runner/action environment namespaces.
- Domain image setup, credentials and publication remain consumer-owned unless separately specified as generic behaviour.

## CI use

- Local and GitHub Actions use the same `cad-ci` commands.
- Consumer repositories do not copy generic checkout/Python/tool-install/cache/plan/run setup.
- Workflow YAML does not contain changed-item loops, domain commands or rebuild logic.
- Forge and CAD consume only a released tool revision.
- The released tool/library/workflow combination is proven in `tool.cad.ci.test` before consumer migration.
