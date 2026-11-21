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


## Single-runner PR architecture

The PR workflow intentionally keeps verification and publication in one GitHub
job so a normal PR does not pay for a second runner, second checkout, second
Python setup, tool reinstall or artifact handoff.

```text
pull_request opened/synchronize/reopened
  -> one ubuntu runner
     -> checkout PR head
     -> checkout/install exact called tool
     -> GHCR login
     -> cad-ci run
     -> build/ has materialized output?
        no  -> success
        yes -> same-repository PR?
               no  -> success without durable publication
               yes -> cad-ci build prepare-pr
                      -> cad-ci publish build --scope pr
```

```text
pull_request closed
  -> one ubuntu runner
     -> checkout default branch
     -> checkout/install exact called tool
     -> cad-ci publish build-cleanup --pull-request N
```

The one-runner workflow changes only GitHub orchestration. It reuses existing
CLI operations and therefore does not create a second implementation of build
selection or publication semantics.

## PR performance contract

The workflow design avoids avoidable runner-boundary overhead:

- no `actions/upload-artifact` / `actions/download-artifact` between run and
  PR publication;
- no second runner for normal PR publication;
- no repeated checkout/setup/install phase between verification and publish.

Consumer/domain performance remains outside tool.cad.ci. The workflow provides
the minimal generic orchestration needed to measure end-to-end PR latency.


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
