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

- `tool.cad.ci` provides `reusable-pr.yml` as the high-level complete pull-request workflow, `reusable-ci.yml` as the high-level run-only workflow, plus lower-level reusable planning/execution workflows for consumers that need domain setup between them.
- A consumer references those workflows at one exact tool commit SHA.
- The called workflow checks out its own tool source using `job.workflow_repository` and `job.workflow_sha`; workflow and tool implementation therefore cannot drift.
- The complete PR workflow resolves the exact `lib.py.cad.ci` commit from that tool revision's `pyproject.toml`, checks out that source, and exposes both repositories through `PYTHONPATH`.
- The called workflow checks out the caller repository at the real source commit, not a temporary PR merge ref.
- `reusable-pr.yml` is the normal pull-request entry point when the consumer wants CAD-CI verification plus durable PR publication/cleanup.
- `reusable-ci.yml` remains the high-level run-only entry point and delegates to the generic run workflow from the same tool revision.
- `reusable-plan.yml` exposes the compact generic item plan for consumers that need domain setup between planning and execution.
- `reusable-run.yml` performs exactly one `cad-ci run` and does not restore or save GitHub Actions cache state.
- The released root `action.yml` is the same-runner run surface for a caller
  that must execute consumer-owned steps after CAD-CI without crossing a runner
  boundary.
- The composite action checks out the exact caller source, fetches only the
  exact incremental base when needed, uses its own released action source as
  the exact tool source, checks out the exact pinned library source, exposes
  both through `PYTHONPATH`, installs only external runtime dependencies,
  performs generic GHCR login and invokes exactly one `cad-ci run`.
- Environment entries written by the action keep the same exact CLI stack
  available to later caller steps in that job.
- The composite action does not own consumer-specific post-run commands,
  durable-build policy, site generation or Pages content. Those later steps
  call the already released generic CLI where appropriate.
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


## Single-runner pull-request workflow

`reusable-pr.yml` owns GitHub-only orchestration for the complete PR lifecycle.

For `opened`, `synchronize` and `reopened` events it must use one job and
one runner to:

1. check out the real PR head commit;
2. check out the exact called tool revision and its exact pinned library source;
3. expose both source trees through `PYTHONPATH` without building/installing either BrainboxEmb package;
4. install only external Python runtime dependencies required by the library;
5. authenticate generically to GHCR;
6. perform exactly one `cad-ci run`;
7. when materialized `build/` output exists and the PR belongs to the caller
   repository, run `cad-ci build prepare-pr`;
8. publish that prepared sparse scope with `cad-ci publish build --scope pr`.

There is no artifact transport between execution and publication because both
stages use the same workspace on the same runner.

For `pull_request.closed`, normal CAD-CI execution is skipped. The same
reusable workflow checks out the default branch/tool revision and invokes
`cad-ci publish build-cleanup --pull-request <number>`.

The caller grants `contents: write` and `packages: read`. GitHub may narrow
those permissions for untrusted/fork events. Durable PR publication is allowed
only when `github.event.pull_request.head.repo.full_name == github.repository`.
Verification must remain useful when publication is not allowed.

The workflow does not implement item selection, dependency traversal, build
validation, source freshness or generated-branch retry logic. Those remain in
the released library/CLI commands.


## PR bootstrap cost

The complete PR workflow must not run `pip install -e` for tool.cad.ci and
must not ask pip to clone/build the tool's Git dependency.

The exact tool source and exact pinned library source are executable Python
sources. The workflow places both roots on `PYTHONPATH` and invokes the CLI
with `python -m cad_ci_tool`.

A clean GitHub-hosted runner may install external dependencies such as SCons
and PyYAML from their published packages. Optimizing those downloads is a
separate measured step and must not reintroduce CAD/SCons build-cache semantics.


## PR bootstrap efficiency

The complete PR workflow minimizes fixed hosted-runner setup work without
changing CAD-CI semantics.

- The caller source checkout fetches only the exact PR head initially.
- Incremental runs explicitly fetch only the exact PR base commit required by
  released base/head selection. They do not fetch all branches, tags or history.
- Full runs and closed-PR cleanup do not fetch an unused PR base commit.
- GHCR authentication uses the runner Docker CLI with the workflow token and
  `--password-stdin`; it does not require a separate Docker login action.
- External PyYAML and SCons installation skips dependency recursion and eager
  bytecode compilation.
- This optimization does not introduce GitHub Actions cache state or alter
  SCons/cache semantics.


## Durable main current-configuration membership

`cad-ci build update-main` exposes the released library's removed-item cleanup
contract without duplicating it.

The tool passes two distinct item collections:

- affected current items selected by the existing sparse selection path;
- the complete current processed item set, obtained from released library
  full-run/process semantics.

The tool must not compare the durable manifest with repository configuration,
identify removed rows, delete paths or interpret absence from the sparse
candidate as deletion.

`process: false` items are not members of the current durable main baseline.

A deletion-only or mixed deletion/replacement update must remain a library-owned
operation once the required source/build inputs reach the command.


## Same-runner consumer action

A reusable workflow owns its called job, so a caller cannot append
consumer-owned steps to that same runner. The root composite action exists for
that case.

The caller owns the one job, its permissions and its high-level concurrency.
The action owns only generic CAD-CI setup and one run:

```text
one caller job
  -> tool.cad.ci composite action
       -> exact source checkout
       -> exact base fetch when incremental
       -> exact tool action source + pinned library source
       -> external runtime dependencies
       -> GHCR login
       -> exactly one cad-ci run
  -> caller-owned post-run steps on the same workspace
       -> may use python -m cad_ci_tool ...
```

No build artifact is required to cross from the action to the caller because
there is no runner boundary. The action must not add item loops, changed-path
logic, consumer commands or publication semantics.
