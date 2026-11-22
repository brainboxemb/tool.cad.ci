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

- `tool.cad.ci` provides `reusable-pr.yml` as the public complete pull-request workflow and `reusable-ci.yml` as the public run-only workflow. `reusable-plan.yml` is an advanced public plan-only API. `reusable-run.yml` is internal implementation behind `reusable-ci.yml`.
- A consumer references those workflows at one exact tool commit SHA.
- The called workflow checks out its own tool source using `job.workflow_repository` and `job.workflow_sha`; workflow and tool implementation therefore cannot drift.
- The complete PR workflow resolves the exact `lib.py.cad.ci` commit from that tool revision's `pyproject.toml`, checks out that source, and exposes both repositories through `PYTHONPATH`.
- The called workflow checks out the caller repository at the real source commit, not a temporary PR merge ref.
- `reusable-pr.yml` is the normal pull-request entry point when the consumer wants CAD-CI verification plus durable PR publication/cleanup.
- `reusable-ci.yml` remains the high-level run-only entry point and delegates to the generic run workflow from the same tool revision.
- `reusable-plan.yml` exposes the compact generic item plan without executing the graph.
- `reusable-run.yml` performs exactly one `cad-ci run` for `reusable-ci.yml`; direct external use is not a supported public contract.
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

Advanced `reusable-plan.yml` and internal `reusable-run.yml` must not share this
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


## One-runner pull-request workflow

`reusable-pr.yml` provides the complete PR verification and durable-build
publication/cleanup API. **Exactly one job and runner** handle the configured
lifecycle. No artifact upload/download, second publisher job, second tool
bootstrap, or extra SCons execution graph is permitted.

For `opened`, `synchronize` and `reopened` events:

1. Check out the exact PR-head source and exact called tool/library revisions.
2. Fetch the exact base commit only for an incremental run.
3. Install external runtime dependencies and authenticate generically to GHCR.
4. Run exactly one `cad-ci run` graph.
5. When `publish_build` (default true) and same-repository materialized
   `build/` output exist, prepare and publish the sparse PR scope **within
   that same job and workspace**.

For `pull_request.closed`, skip SCons and remove the same-repository PR
build scope when `publish_build` is enabled, using the same job.

Fork PRs must never publish or clean the caller's durable generated branches.
`publish_build: false` disables publication and cleanup, without adding a job.
Unknown events fail validation before checkout.

The one-runner design is intentional. Same-repository publication is a
caller-trust decision; fork PRs never publish. Callers requiring a strictly
read-only PR verification path use `reusable-ci.yml`. Do not introduce a
second runner or artifact handoff to change this contract.

Planning, build-store validation, freshness checking and publication policy
remain in `lib.py.cad.ci`; workflow YAML only orchestrates them.

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
- Full verification runs and closed-PR cleanup do not fetch an unused PR base commit.
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


## Bounded parallel SCons jobs

The public run surfaces expose the released library-owned SCons `jobs` option
without implementing parallel execution in this repository.

- `cad-ci run --jobs N` accepts only a positive integer and defaults to 1.
- The same-runner composite action exposes `jobs`, defaults to 1, validates it
  as a positive integer, and forwards it unchanged.
- `reusable-run.yml`, `reusable-ci.yml` and `reusable-pr.yml` expose a
  numeric `jobs` input with default 1 and forward it to the same generic run.
- The reusable helper validates `jobs` and emits exactly one
  `cad-ci run --jobs N`.
- The tool must not create threads/processes, partition targets, reinterpret the
  dependency graph or implement its own scheduler.
- Default behavior remains serial (`jobs=1`) for backward compatibility.
- Consumers may opt into `jobs > 1` only after the exact released tool stack
  has external black-box acceptance.


## Same-runner durable-lane action

The root composite `action.yml` supports two modes.

### Run-only mode

This remains the existing public behavior:

- caller supplies `source_sha`;
- caller supplies `base_sha` for incremental selection or `full_run=true`;
- action checks out/bootstrap/authenticates once;
- action runs exactly one CAD-CI graph;
- later caller steps may use the exposed tool/library stack on the same runner.

### Durable mode

The caller additionally supplies:

- `durable_scope`: one safe scope name; `main` selects stable-main semantics,
  every other safe name selects named-scope semantics;
- `source_ref`: the caller source ref recorded in durable publication
  provenance.

When `durable_scope` is non-empty:

- caller must not supply a manual `base_sha`;
- caller must not force `full_run=true`;
- after exact tool/library bootstrap, the action calls the library durable
  scope API to materialize the current generated `build` branch and resolve
  existing/missing state;
- the library owns scope validation, manifest parsing, stored
  `source_commit`, first-run/full-run and missing-main semantics;
- the action fetches the library-resolved base commit only for incremental runs;
- the action executes exactly one CAD-CI graph;
- the same runner/workspace calls the library durable publication API, which
  composes existing planner/build-store/generated-branch publication mechanics;
- no artifact upload/download or second runner is used.

Durable mode exposes:

- `scope`;
- resolved `base_sha`;
- effective `full_run`;
- `scope_exists`;
- exact published `build_commit`;
- absolute `prepared_scope` path;
- existing exact `library_revision`.

The action does not build consumer sites and does not publish Pages. Consumer
site generation remains domain-owned and may run immediately after the action
on the same runner. Generic Pages publication remains a normal tool CLI call
from that same job.

The action must not implement a second selection engine, build-store format,
freshness model or publication mechanism. It orchestrates existing released
tool/library contracts only.

The caller job needs `contents: write` for durable publication and
`packages: read` for runtime image authentication.

Durable scope names use the library's complete-scope contract. `main` is the
stable complete scope; caller-named complete scopes must satisfy the same
build-store validation and may not use reserved `pr`. The tool must not carry
a second scope validator.


## Reusable dev-lane merge policy

tool.cad.ci provides a reusable GitHub Actions workflow for repositories using
long-lived development lanes such as:

```text
main
dev-cad
dev-ci
```

This is workflow orchestration owned by the tool repository. It must not add
generic CAD-CI planning/execution semantics and must not depend on Forge-specific
code.

Required behavior:

- merging is an explicit owner-controlled command; there is no silent auto-merge;
- the workflow receives the PR identity from the triggering repository and
  verifies the current PR head SHA immediately before merge;
- it verifies the latest required check/status state for that exact head before
  performing the merge;
- exact configured long-lived dev-lane -> main promotions use a normal merge
  commit;
- all other supported PR merges use squash;
- permanent refs, generated refs and backup refs are never deleted;
- only explicitly allow-listed temporary branch prefixes may be deleted;
- after a direct long-lived-lane -> main promotion, the long-lived lane is
  preserved/advanced at the resulting main merge commit;
- consumer-specific post-merge integration dispatch is configurable and may be
  omitted;
- the shared workflow must not hard-code Forge workflow names, repository names
  or consumer commands;
- consumer repositories keep only a thin wrapper/trigger and repository-local
  configuration.

The workflow must fail closed for draft, unmergeable, stale-head or non-green
pull requests.

The current Forge policy is the acceptance reference for the first release.
Downstream CAD's temporary local copy is not a second normative implementation.

## Stable-to-lane synchronization

The reusable dev-lane merge policy must distinguish three merge classes:

1. configured long-lived `lane -> stable` promotion;
2. configured long-lived `stable -> lane` synchronization;
3. every other supported pull request.

For exact configured `stable -> lane` synchronization:

- the merge method is a normal merge commit, never squash or rebase;
- stable and lane refs are both permanent and never cleanup targets;
- the stable source ref is not advanced, recreated or deleted after merge;
- GitHub updates the lane base ref through the merge result;
- the configured integration workflow is dispatched for the updated lane/base;
- the source must be the same repository as the target repository;
- exact-head, draft, mergeability, check and status gates remain unchanged.

Exact configured `lane -> stable` promotion keeps the existing 0.19.0
behavior: normal merge plus preservation/advancement of the long-lived lane at
the resulting stable merge commit.

Lane-to-lane, temporary-to-lane, temporary-to-stable and other ordinary
supported pull requests remain squash merges unless a separate future contract
explicitly changes them.

## Merge-command check isolation

The reusable merge policy must evaluate PR validation independently from
command workflows triggered by `issue_comment`.

For the exact current PR head SHA:

- fetch all pages of commit check-runs, failing if the response is incomplete;
- fetch all pages of GitHub Actions workflow runs for the same head with
  `event=issue_comment`;
- exclude only check-runs whose Actions run ID belongs to that command-run set;
- evaluate the latest remaining validation check per (GitHub App ID, check name),
  so independent apps with the same visible name cannot mask a failure;
- require at least one remaining validation check;
- accept only completed checks with conclusion `success`, `neutral` or
  `skipped`;
- continue rejecting pending, cancelled or failed non-command validation
  checks, and reject a PR whose base/head changed during validation;
- keep commit status-context validation unchanged.

The filter is event/identity based. It must not hard-code a consumer branch,
repository, workflow title or check name.

This rule applies to all merge classes, but is required for stable-to-lane
synchronization because the stable PR head is also the commit on which the
issue-comment command workflow executes.


## Composite-action source trust

The root same-runner action supports run-only use and durable publication on
trusted branch source. Durable mode is not a generic untrusted PR execution
surface. This is a documented caller constraint, not a separate architecture
workstream.

## Versioned consumer templates and onboarding

The released tool is responsible for telling a new repository how to consume
its public GitHub Actions APIs. Consumer repositories must not invent a second
generic workflow design.

Requirements:

- ship canonical templates for normal run-only CI, complete PR lifecycle,
  same-runner root action use and merge governance;
- every template has a stable template id and positive integer template
  version, duplicated in a machine-readable manifest;
- templates use only documented public `tool.cad.ci` surfaces and one
  explicit immutable release-SHA marker;
- templates contain only trigger, permission and repository-owned policy
  configuration; they do not copy generic checkout/bootstrap, PR-file
  pagination, changed-path classification, SCons/CAD-CI execution, durable
  state or merge implementation;
- existing consumer/repository names and workflow filenames are not encoded in
  the generic templates;
- a new-repository guide explains configuration, template selection, immutable
  pinning, allowed local customization and verification order;
- template structure is release-versioned and covered by automated tests so a
  copied consumer can identify its provenance and compare versions.

The templates are a consumer contract above the public Actions APIs, not a new
execution engine.

## Public API invariants (issue #110)

The following IDs name **externally observable requirements** independent of
specific filenames, shell commands or Python helper names. Earlier sections
supply detailed functional requirements; this section makes their public
boundary explicit. A requirement does not become satisfied merely because
an implementation exists.

| ID | Required public behaviour |
| --- | --- |
| API-001 | An immutable tool release defines one CLI version and one exact pinned `lib.py.cad.ci` revision. Moving branch references are not accepted release identities. |
| API-002 | `cad-ci plan` explains selected items/dependencies without asserting target freshness; `cad-ci run` delegates exactly one graph to the library/SCons. |
| API-003 | `cad-ci build`, `pages` and `publish` expose only released library-backed preparation/publication mechanics; generated outputs preserve evidence and source-freshness checks. |
| API-004 | Normal run-only consumers have one high-level reusable workflow; consumers needing subsequent domain work on the same runner have one composite-action entry point. No extra job boundary is added only for apparent reuse. |
| API-005 | One-job/one-runner PR workflow executes exactly one graph, optionally publishes sparse same-repository PR output and handles cleanup without artifact handoff. Fork PRs cannot publish. |
| API-006 | `reusable-plan.yml` is public advanced plan-only; `reusable-run.yml` is internal behind the stable `reusable-ci.yml`. Support levels, inputs/outputs and permissions are explicit and do not silently replace the root same-runner action. |
| GOV-001 | Merge governance is an **optional, separately identified** API, not CAD-CI planning. The caller supplies branch-role configuration but not an arbitrary merge method. Owner-controlled merges check current PR state and independent validation. |
| GOV-002 | Permanent lane promotion/synchronization preserve histories and permanent refs. Temporary cleanup is allow-listed, same-repository only, and must not knowingly delete a head that moved after validation. |
| GOV-003 | Every successful merge has a distinct, auditable post-merge outcome. Failure of a lifecycle/dispatch/comment action cannot turn a completed merge into a claimed refusal. An ambiguous merge API result must be reported as **unknown**, not as a refusal. |
| GOV-004 | Check evaluation is complete (including pagination), rejects incomplete information, and does not confuse command-run checks with PR-validation checks. `mergeable: null` is transient only for a bounded retry window. |
| SEC-001 | Privileged workflows check authorisation before mutation, run trusted tool source only, minimise token exposure, and do not execute submitted PR code. |

Open architectural decision: the current generic merge-governance workflow lives
in this repository, but it is not a CAD-CI algorithm. Its long-term home is
under review (#110). **Do not migrate or silently remove that API** while Forge
still consumes the exact released workflow.

Traceability and evidence are maintained in [API contract](api.md). Behaviour
requiring live GitHub mutation has **not** been certified by unit tests alone.


## Reusable permanent-lane PR policy

The stable public `reusable-ci.yml` may receive optional `pr_policy_json`.
Empty input preserves the normal run-only contract.

The policy object contains only:
- `stable_ref`;
- non-empty `lane_refs`;
- optional `docs_only_prefixes`.

For pull requests:
- explicit `full_run: true` always wins;
- exact configured lane -> stable promotion runs complete processed CAD-CI;
- a normal PR targeting a configured lane may skip expensive CAD-CI bootstrap
  only when the exact non-empty Git diff is entirely below configured docs-only
  prefixes;
- empty/unknown/mixed diffs run CAD-CI;
- unsupported/non-PR context runs rather than silently skipping.

Classification occurs on the same reusable-run runner after exact caller
checkout/base fetch and before Python/library/GHCR bootstrap. There is no
classifier job, artifact handoff or consumer-local GitHub PR pagination.

Consumers that use this policy must not copy path loops or promotion full-run
expressions into their own workflow YAML.

## Merge consumer permission ceiling

The canonical `tool.cad.ci/merge-policy` consumer template must grant the
calling reusable-workflow job the permissions required by
`reusable-merge-policy.yml`: actions/content/pull-requests/issues write and
checks/statuses read.

Template version 2 owns this correction. Repository-specific integration
workflow and extra temporary prefixes remain caller-owned values.
