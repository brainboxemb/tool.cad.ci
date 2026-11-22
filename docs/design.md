# tool.cad.ci design

This document describes the stable boundary of `tool.cad.ci`.

## Purpose

`tool.cad.ci` is the thin command-line and reusable-workflow surface above one
exact released `lib.py.cad.ci` revision.

The tool owns:

- CLI argument parsing and exit handling;
- reusable GitHub Actions setup;
- exposure of the exact called tool revision and its pinned library source on the runner;
- GitHub artifact transport requested by a caller;
- release plumbing and tool-specific tests.

Generic CAD-CI configuration, SCons execution, evidence, build output and Pages
mechanics stay in `lib.py.cad.ci`.

## Library pin

`pyproject.toml` pins one exact library commit. A tool release therefore
identifies one exact tool/library stack.

A generic library feature is not reimplemented here. The tool is updated only
after the library feature is released and tested in its own repository.

Item-level `process` participation is one such library feature. The tool does
not parse or interpret `process`; it exposes the released library behavior
through the existing plan/run commands.

## Command environment

The reusable workflow may receive optional non-secret `environment_json`
values from its caller. The workflow helper validates those values and places
them in the inherited process environment before invoking `cad-ci run`.

Root `cad-ci.yml:variables` are different: they are repository configuration
owned and parsed by `lib.py.cad.ci`, not by this tool.

The effective command precedence is therefore:

1. runner/caller environment, including validated `environment_json`;
2. repository variables from root `cad-ci.yml`, applied by the library;
3. CAD-CI-owned `CAD_CI_*` runtime values, applied by the library.

The tool must not add a second merge/parser for root variables.

## Consumer template architecture

The public reusable workflows and root composite action are the executable API.
The files under `docs/manual/templates/` are canonical **copy-ready consumer wrappers**
for those APIs.

```text
new repository
  -> copy one versioned template
  -> keep the exact immutable released tool SHA recorded in the template
  -> change repository-owned trigger/policy values only
  -> call released public workflow/action
```

Each copy-ready YAML file carries its stable template id, integer template
version, tool release and exact release SHA in the header. No separate manifest
is required to understand or copy a template.

Templates deliberately do not contain generic runner bootstrap or CAD-CI
implementation. If a consumer needs generic behavior not expressible through a
shipped public surface, change the owning tool/library and publish a new
template version rather than adding a consumer-local workaround.

Template versioning is independent of semantic product versioning: increment a
template's integer when the copied consumer structure or required local
configuration changes. Update the pinned tool release/SHA when the handoff
baseline advances. Pure comments do not require a template-version bump.

## Reusable workflows

`reusable-pr.yml` is the normal complete pull-request entry point when a
consumer wants verification plus durable PR publication/cleanup.

`reusable-ci.yml` remains the high-level run-only entry point. Lower-level
reusable plan/run workflows exist for cases that need repository-specific
preparation between generic stages.

Workflow YAML remains orchestration-only. It does not own changed-item logic,
SCons decisions, item loops or consumer commands.

## Verification and release

A tool revision is released only after its own tests pass against the exact
library pin. The exact released tool revision is then tested from
`tool.cad.ci.test` before Forge or another CAD repository adopts it.


## GitHub Container Registry authentication

The reusable workflow owns runner-level GitHub credentials. Before invoking
`cad-ci run`, `reusable-run.yml` authenticates Docker to `ghcr.io` using:

- registry: `ghcr.io`;
- username: `${{ github.actor }}`;
- password: `${{ github.token }}`.

Both `reusable-ci.yml` and `reusable-run.yml` retain
`packages: read` together with `contents: read`. Reusable workflow
permissions may only stay equal or become narrower across the call chain, so
the high-level wrapper may not drop package-read permission before delegating.

The login is generic runner setup only:

- it contains no consumer image reference;
- it does not pull/build/publish any image itself;
- it does not export the token to consumer commands;
- it does not add registry semantics to `lib.py.cad.ci`.

A consumer that does not use GHCR still receives the same CAD-CI behavior; the
extra authenticated Docker registry entry is otherwise unused.


## High-level workflow concurrency

Only `reusable-ci.yml` owns the normal-consumer concurrency group.

The group is derived from caller repository, caller workflow and PR/branch
context, with `cancel-in-progress` enabled.

The lower-level plan/run workflows deliberately have no matching group. Their
ordering can be part of a split consumer's caller workflow and must not be
cancelled against each other by this tool.


## Timing evidence boundary

Timing evidence is a library-owned feature. The CLI passes through the released
library's execution/evidence behavior unchanged.

The tool's tests verify that the exact library pin exposes the expected fields,
but the tool contains no clock, timestamp formatter or duration calculation.


## Repository documentation delivery

The tool repository itself uses Markdown documentation only.

Its own CI does not build or publish a Pages site and does not maintain
repository-local site-generation code.

This is separate from the product's generic Pages/publication commands, which
remain thin CLI exposure of library-owned behavior.

## Build artifact transport

Artifact transport is conditional on materialized output, not only on caller
intent.

```text
cad-ci run
  -> build/ exists with materialized content?
     yes -> expose artifact name -> upload build/
     no  -> empty artifact output -> no upload
```

The reusable workflow may inspect the filesystem after the released CLI
returns. This is GitHub transport behavior only. It does not interpret CAD-CI
selection or build semantics.

## Main candidate selection delegation

The CLI's unselected `build prepare-main` path delegates scope selection to the
library planner:

```text
load_repository()
  -> affected_items(items, None)
  -> repository-ordered selected Item objects
  -> build_store.prepare_main()
```

This keeps the distinction explicit:

- planner/library: owns full-run and `process` semantics;
- tool: converts CLI arguments to library calls;
- build store: validates and packages the supplied accepted items.

The tool must not use `items.values()` as a substitute for full-run selection,
because configured-but-nonprocessed items intentionally have no candidate
output.


## One-runner PR architecture

The complete `reusable-pr.yml` remains a **single job on one runner**
for its entire PR lifecycle. That was the established performance and
architecture requirement. It does not download/upload build artifacts or
repeat checkout/Python setup between verification and publication.

```text
PR opened/synchronize/reopened
  -> one runner
      -> exact PR head / exact tool and library
      -> GHCR authentication
      -> one CAD-CI run
      -> if materialized output and eligible same-repo PR:
           prepare PR build scope
           -> publish build scope in the same workspace

PR closed
  -> one runner
      -> trusted/default branch and pinned tool/library
      -> cleanup PR scope (same-repo only)
```

An optional `publish_build: false` flag suppresses publication/cleanup
while preserving the same one-runner verification behavior. A second
privileged publication runner is **not** an acceptable implementation
of this API. Security review must work within this architectural boundary,
and unresolved trust restrictions must be visible rather than silently
rewriting the product topology.

## PR performance contract

The workflow does not introduce artifact handoff, extra runners, repeated
tool/library checkout, or a second SCons graph to facilitate publication.
Any credential-security solution requires explicit evaluation of the
same-runner trade-off rather than replacing this contract.

## Direct source bootstrap for pull requests

A consumer PR must not rebuild BrainboxEmb's own released Python projects.

The reusable PR workflow uses the tool revision itself as the stack identity:

```text
checkout exact tool revision
  -> read exact lib.py.cad.ci commit from tool pyproject
  -> checkout exact library revision
  -> PYTHONPATH=<tool>:<library>
  -> install only external runtime dependencies
  -> python -m cad_ci_tool ...
```

This keeps the existing exact Git pin as the single library-version source of
truth while removing editable installation, project build isolation, project
metadata preparation and wheel builds from the consumer critical path.

SCons remains the CAD-CI execution engine on the GitHub runner. SolidCraft
remains a separate model runtime started only by a selected consumer action.


## PR bootstrap critical path

The reusable PR workflow treats repository history and runner setup as part of
the measured critical path.

For incremental PRs:

```text
checkout exact head, depth 1
  -> fetch exact base SHA, depth 1
  -> checkout exact tool + exact pinned library
  -> install only external runtime packages
  -> docker login through the existing runner CLI
  -> cad-ci run
```

The base fetch exists only to provide the two exact Git objects required by the
released library's base/head diff. Unrelated caller branches, tags and history
are not needed.

Direct `docker login --password-stdin` preserves generic GHCR authentication
while avoiding an additional action download/startup boundary.


## Main update membership delegation

The update-main CLI keeps sparse replacement selection and complete baseline
membership separate:

```text
load_repository()
  |
  +-> changed/base-head selection
  |      -> affected current Item objects
  |      -> update_main(items=...)
  |
  +-> affected_items(items, None)
         -> all current process:true Item objects
         -> update_main(current_items=...)
```

The second call is not a second interpretation of `process`: it delegates to
the same released library planner used by full-run selection.

The tool does not inspect `build/main/build.json` to decide what disappeared.
That comparison and all owned-path removal remain inside
`lib.py.cad.ci.update_main()`.

This distinction lets the library preserve an unselected current item while
removing a previous durable item that is no longer configured.


## Same-runner composite action

The root `action.yml` complements reusable workflows; it does not replace the
library or introduce a second CI engine.

A reusable workflow is appropriate when CAD-CI owns the whole called job. A
composite action is required when the caller must keep control of the job so it
can run domain-owned steps afterwards on the same runner.

The action revision is itself the exact tool revision. Therefore no second tool
checkout is required:

```text
brainboxemb/tool.cad.ci@<released-sha>
  -> GITHUB_ACTION_PATH == exact tool source
  -> read exact lib pin from that source
  -> shallow checkout exact lib source
  -> PYTHONPATH=<tool>:<lib>
  -> install external PyYAML/SCons only
  -> docker login ghcr.io
  -> one cad-ci run
  -> leave PYTHONPATH + workspace available to later caller steps
```

The caller can then invoke existing `cad-ci build` / `cad-ci publish`
commands without reinstalling the stack. The tool still does not decide which
consumer post-run commands exist or how domain content is generated.

This is GitHub-runner orchestration only. Selection, SCons execution,
build-store membership/deletion, Pages installation and generated-branch
freshness remain in `lib.py.cad.ci`.


## Bounded jobs forwarding architecture

Parallel execution remains inside the released library/SCons engine.

The tool surfaces carry one integer only:

```text
caller
  -> jobs = N
  -> tool CLI/workflow/action validation
  -> one cad-ci run --jobs N
  -> lib.py.cad.ci run_repository(..., jobs=N)
  -> SCons -j N
```

No intermediate layer expands N into target loops or workers. This keeps
selection, prerequisite scheduling, dirty/current decisions, dependency
snapshots and output evidence under one SCons execution graph.

Every public run surface defaults to 1. This preserves existing execution order
unless a consumer deliberately opts into bounded parallelism.


## Same-runner durable-lane orchestration

The existing root composite action remains the only same-runner public action.
Durable behavior is an optional mode inside that action; it is not a second
reusable workflow job.

```text
consumer job / one ubuntu runner
  -> tool.cad.ci/action.yml@exact-release
       -> checkout source once
       -> setup Python once
       -> resolve/check out exact pinned library once
       -> install external runtime deps once
       -> resolve durable scope/base (durable mode only)
       -> fetch exact incremental base when needed
       -> authenticate GHCR once
       -> scripts/reusable_ci.py run
            -> one cad-ci/SCons graph
       -> scripts/reusable_ci.py durable-publish
            -> existing build update/prepare CLI
            -> existing publish build CLI
       -> action outputs
  -> consumer-owned site generation
  -> generic cad_ci_tool publish pages
```

### Helper ownership

`scripts/reusable_ci.py` owns only workflow adaptation:

- parse/validate GitHub-facing arguments;
- bootstrap the exact library revision;
- call `cad_ci.durable.fetch_durable_scope_state` after bootstrap;
- serialize `scope`, `base_sha`, `full_run`, `scope_exists` and paths
  to GitHub outputs;
- construct the library `DurableScopeState` and call
  `cad_ci.durable.publish_durable_scope`;
- serialize the resulting build commit and prepared-scope path.

It does **not** parse `build.json`, validate complete-scope names, select
first/full versus incremental state, choose update-main/update-named/
prepare-named, or implement publication semantics. Those are library-owned.

### Composite action flow

For run-only mode the action preserves the existing validation/fetch/run
sequence.

For durable mode:

1. validate `source_sha`, `durable_scope`, `source_ref`, jobs and that no
   manual base/full-run override conflicts with durable resolution;
2. checkout caller source;
3. bootstrap exact tool/library source;
4. run `durable-resolve`;
5. fetch the resolved base commit only when `full_run=false`;
6. authenticate once;
7. execute the existing run helper exactly once using the resolved selection;
8. execute `durable-publish` in the same workspace;
9. expose outputs and return without cleaning the prepared scope or tool stack.

### Performance boundary

No durable phase may be moved into a second job merely for reuse aesthetics.
A job boundary would force one or more of:

- second runner startup;
- second checkout/bootstrap;
- second image/tool setup;
- artifact transport;
- reconstructed workspace state.

The reusable unit is therefore the composite action, not a sequence of jobs.

### Consumer workflow target

A long-lived consumer push job should reduce to roughly:

```yaml
- id: cad
  uses: brainboxemb/tool.cad.ci@<exact release>
  with:
    source_sha: ...
    durable_scope: ...
    source_ref: ...
    jobs: "2"

- run: <consumer site builder using steps.cad.outputs.prepared_scope>

- run: python -m cad_ci_tool publish pages ...
```

The site builder and Pages content remain consumer-owned.


## Shared merge-policy workflow

Issue #103 adds one reusable GitHub Actions workflow surface above GitHub's PR,
checks/status and refs APIs. It is deliberately separate from the CAD-CI
library/execution graph.

Conceptual flow:

```text
consumer /merge trigger
  -> reusable tool.cad.ci merge-policy workflow
       -> load exact PR/base/head
       -> reject draft/stale/unmergeable/non-green
       -> classify exact base/head pair
       -> merge with selected method
       -> preserve/advance configured long-lived lane when promoted
       -> optionally delete allow-listed temporary head
       -> optionally dispatch configured consumer integration workflow
```

### Public configuration boundary

The reusable workflow should accept repository-neutral configuration for:

- stable branch name (default may be `main`);
- long-lived lane names;
- temporary cleanup prefix allow-list;
- optional post-merge integration workflow identifier/ref inputs.

The caller must not pass an arbitrary merge method. Merge method is derived by
the shared policy from exact configured base/head roles.

### Safety boundary

The shared implementation owns:

- merge-method decision;
- current-head verification;
- check/status gate;
- temporary-branch cleanup allow-list enforcement;
- long-lived lane preservation after promotion.

The consumer owns:

- deciding to expose/use the `/merge` trigger;
- permissions;
- lane names/configuration;
- optional integration workflow dispatch target.

The implementation must never infer cleanup safety from branch age or naming
outside the explicit allow-list. Generated/build/Pages/backup refs are outside
the cleanup domain.

### Ownership

No `lib.py.cad.ci` change is required unless implementation exposes a genuine
planning/execution requirement. The first release should be implemented and
tested entirely in tool.cad.ci, then black-box accepted in tool.cad.ci.test and
finally qualified from Forge #674.

## Stable-to-lane merge-policy extension

Issue #106 extends the shared merge-policy classifier without changing CAD-CI
planning or execution.

The policy distinguishes explicit permanent-lane direction:

```text
lane -> stable
  method: merge
  class: promotion
  after merge: advance/recreate the lane at the stable merge commit
  integration: stable + retained lane

stable -> lane
  method: merge
  class: lane synchronization
  after merge: no source-ref mutation; the PR merge updates the lane base
  integration: updated lane

all other supported PRs
  method: squash
  class: ordinary
  after merge: cleanup only when the head matches the configured temporary
               allow-list
  integration: durable base when configured
```

The classifier should return explicit booleans (or one equivalent explicit
classification) for promotion and lane synchronization. The reusable workflow
must not infer synchronization from branch naming outside `stable_ref` and
`lane_refs_json`.

Permanent-direction PRs require the head repository to equal the caller
repository. This prevents a fork branch named `main` or like a configured lane
from being treated as a trusted permanent ref.

The existing promotion-only lane-advance operation remains promotion-only.
Stable-to-lane synchronization must not patch/recreate the stable source ref:
the normal PR merge already writes the lane base and preserves both histories.

The existing `integrate_base` rule remains appropriate for synchronization
because the base is a configured durable lane. Promotion additionally dispatches
the retained lane exactly as in 0.19.0.

## Command-workflow isolation in the PR green gate

Issue #108 keeps the existing merge-policy order but separates validation
checks from merge/release command runs.

The reusable workflow obtains two API snapshots for the immutable PR head:

```text
GET /repos/{repo}/commits/{head}/check-runs
GET /repos/{repo}/actions/runs?head_sha={head}&event=issue_comment
```

The second response supplies the Actions run IDs that represent command
workflows on that head. Before the existing latest-check grouping, the policy
drops a check-run only when its `details_url` identifies one of those run IDs.

Conceptually:

```text
all check-runs at PR head
  - check-runs owned by issue_comment Actions runs at the same head
  = validation check-runs

validation check-runs
  -> latest by check name
  -> non-empty
  -> all completed + success/neutral/skipped
```

This removes both the current in-progress merge-policy check and any previous
failed issue-comment command checks from the validation set. It does not ignore
ordinary `pull_request`, `push` or other validation checks merely because
they are GitHub Actions checks.

Commit status contexts are evaluated exactly as before.

The filter remains in the reusable workflow because the command-run identity is
GitHub orchestration state, not CAD-CI planning behavior.

## Merge command implementation boundary (issue #110)

The public `reusable-merge-policy.yml` is a GitHub runner adapter: it
declares the `workflow_call` API, permissions, trusted tool checkout and one
command execution. Branch classification stays in the pure
`scripts/merge_policy.py`; API interactions, readiness gates and irreversible
merge outcome recording live in `scripts/merge_command.py`.

This is a **separate governance adapter**, not part of the
`lib.py.cad.ci` execution engine. Do not move CAD-CI planner/build-cache
concepts into merge handling. The broader question of the governance product's
repository ownership remains open.

Failure boundaries:

```text
PR state + source/base/head + independent validation checks
  -> reject before mutation (fail closed)
  -> PUT merge with exact validated head SHA
      | 2xx merged=true + SHA -> irreversible success
      | API failure/uncertain response -> outcome UNKNOWN; never call it a refusal
  -> branch lifecycle (best effort, recorded)
  -> dispatch appropriate durable refs (best effort, recorded)
  -> report accepted merge SHA and per-phase outcomes in PR comment and logs
```

A failed lane update must not prevent an independent stable-base dispatch;
a failed lane update also must **not** dispatch the stale lane. All post-merge
phase failures keep a nonzero job outcome, without claiming the accepted merge
was rolled back.

The existing token owner-only authorization is retained for compatibility
as the current intentional policy. The check exclusion retains issue #108's command-workflow
model, including **old** `issue_comment` attempts sharing the checked head.
Check identity now uses (GitHub App ID, check name) to avoid collisions.
API pagination must be complete; unknown mergeability retries are bounded.

A live GitHub test repository is still necessary to establish the mutation
and recovery contract. Unit fixtures cover this state machine but cannot
simulate GitHub branch-protection, token permission, eventual-consistency or
server-side branch deletion races.

## PR source trust

The one-runner design is intentional. Same-repository PR publication uses the
same runner by contract; fork PRs do not publish. Consumers needing a strict
read-only path use `reusable-ci.yml`. This trust assumption is documented so
future fixes do not reintroduce extra runners or artifact handoff.

## Same-runner lane PR preflight

The optional lane policy is implemented inside the existing internal
`reusable-run.yml` job:

```text
checkout exact caller source
  -> fetch exact base when incremental
  -> remove caller Git credential
  -> checkout exact called tool revision
  -> tool-owned pr-policy helper
       -> promotion: effective full_run=true
       -> docs-only lane diff: run_cad=false
       -> otherwise: run_cad=true
  -> if run_cad:
       setup Python + pinned library + GHCR
       -> exactly one cad-ci run
```

The tool-owned helper validates policy JSON and obtains changed paths from
rename-disabled exact Git diff. The workflow does not contain changed-path
rules. A docs-only skip avoids expensive bootstrap but still uses the same one
runner; no second classification job is introduced.

The canonical `cad-ci-lanes.yml` wrapper supplies the common
main/dev-cad/dev-ci policy. Consumers may change documented policy values but
must not duplicate the classifier.

## Merge template caller permissions

Reusable workflow permissions are bounded by the caller. Therefore canonical
merge template version 2 explicitly grants the same privileged job ceiling
required by `reusable-merge-policy.yml`; the called workflow still owns all
merge implementation and owner-command validation.
