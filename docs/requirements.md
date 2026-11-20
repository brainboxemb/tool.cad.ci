# Requirements

## Repository ownership

- Consumer repositories own `cad-ci.yml`, item `ci.yml`, commands and domain rules.
- `tool.cad.ci` is a thin CLI above one exact released `lib.py.cad.ci` commit.
- Generic execution, build-store, Pages and publication mechanics are not duplicated here.

## Planning

- Changed-file selection is performed by the library.
- Item-level `process` participation is parsed and enforced by the library; the tool does not duplicate that selection rule.
- `cad-ci plan` can show selected items and required dependency closure.
- A plan is explanatory and does not claim SCons target freshness.

## Running

- One `cad-ci run` command calls the library's `run_repository()` once.
- SCons owns dependency traversal, signatures, incremental decisions and cache reuse.
- `--step`, `--until` and `--from` are mutually exclusive.
- The tool forwards partial selectors to the library without adding its own state rules.
- Run output/evidence layout is defined by the library.
- Explicit execution of a non-processed item fails according to the released library contract.

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

- `tool.cad.ci` provides one high-level `reusable-ci.yml` workflow for normal consumers plus lower-level reusable planning/execution workflows for consumers that need domain setup between them.
- A consumer references those workflows at one exact tool commit SHA.
- The called workflow checks out its own tool source using `job.workflow_repository` and `job.workflow_sha`; workflow and tool implementation therefore cannot drift.
- The called workflow checks out the caller repository at the real source commit, not a temporary PR merge ref.
- `reusable-ci.yml` is the normal consumer entry point and delegates to the generic run workflow from the same tool revision.
- `reusable-plan.yml` exposes the compact generic item plan for consumers that need domain setup between planning and execution.
- `reusable-run.yml` performs exactly one `cad-ci run` and does not restore or save GitHub Actions cache state.
- A consumer can optionally request a `build/` artifact for a downstream domain/publication job; the artifact includes hidden `.cad-ci` evidence and excludes private `.cache/cad-ci` state.
- Optional consumer environment input is non-secret, validates variable names, and cannot overwrite GitHub/runner/action environment namespaces.
- Caller `environment_json` values are inherited process environment only; root `cad-ci.yml:variables` are parsed by the released library and override a caller value with the same name.
- The tool does not parse, duplicate or merge root repository variables.
- CAD-CI-owned `CAD_CI_*` values remain authoritative over both caller environment and repository variables.
- Domain image selection/build/publication remain consumer-owned.
- Generic authentication of the GitHub Actions runner to `ghcr.io` is
  reusable-workflow behavior: the caller grants `packages: read` and the
  workflow uses its GitHub token for Docker login before consumer commands run.
- The workflow never parses or selects a consumer container image and never
  exposes registry credentials through `environment_json` or CAD-CI-owned
  environment.

## CI use

- Local and GitHub Actions use the same `cad-ci` commands.
- Consumer repositories do not copy generic checkout/Python/tool-install/plan/run setup.
- Workflow YAML does not contain changed-item loops, domain commands or rebuild logic.
- Forge and CAD consume only a released tool revision.
- The released tool/library/workflow combination is proven in `tool.cad.ci.test` before consumer migration.


## Superseded high-level runs

The normal high-level `reusable-ci.yml` workflow must cancel an older
in-progress run when a newer run starts for the same caller repository, caller
workflow and PR/branch.

Different repositories, caller workflows and PRs/branches remain independent.

Lower-level `reusable-plan.yml` and `reusable-run.yml` must not share this
high-level concurrency group because split consumers may intentionally use both
within one caller-owned workflow.


## Timing evidence surface

The tool exposes the timing/evidence contract of its exact released library pin
without parsing, synthesizing or rewriting those fields.

For library 0.7.0 this includes run-level UTC timestamps and consumer-action
`started_at` / `finished_at` values, with null action timestamps when no
consumer command executed.


## Repository documentation

`tool.cad.ci` does not publish a repository-specific GitHub Pages
documentation site.

Repository documentation lives in `README.md` and `docs/`.

This requirement does not affect the generic `cad-ci publish pages` feature
or its generated-branch contract for consumers.

## Optional build artifact transport

When a caller requests `upload_build: true`, artifact transport depends on
actual materialized build output.

- If `build/` contains materialized output, the reusable workflow exposes the
  requested `build_artifact_name` and uploads `build/` including hidden
  `.cad-ci` evidence.
- If no materialized `build/` output exists, the workflow leaves
  `build_artifact_name` empty and skips upload.
- A successful CAD-CI run with no selected/materialized output must remain
  successful.
- The tool must not create synthetic empty build output and must not infer why
  no build output exists.

## Main build candidate selection

An unselected `cad-ci build prepare-main` represents the current repository
full-run scope.

The tool must obtain that scope from released library selection semantics using
`affected_items(items, None)`.

Therefore:

- `process: true` items participate in a complete main candidate;
- `process: false` items do not require candidate output;
- repository order is preserved when passing selected items to the build store;
- the tool must not implement a second interpretation of `process`.

Explicit/changed/base-head selection for sparse build operations remains
unchanged.
