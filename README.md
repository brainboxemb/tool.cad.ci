# tool.cad.ci

`tool.cad.ci` is the thin command-line interface for BrainboxEmb CAD CI.

The reusable implementation lives in `lib.py.cad.ci`. This repository owns
argument parsing, terminal output, documentation/release plumbing and
CLI-specific tests. It does not implement its own planner, execution engine,
cache, build store, Pages or Git publication mechanics.

The tool pins `lib.py.cad.ci` 0.3.0 at exact commit
`155ec24915e7b2d1b9f5306db9df84a50b53dba8`.

## Consumer layout

```text
cad-ci.yml
shared/
cases/simple_case1/
  ci.yml
  build.py
  verify.py
```

Root `cad-ci.yml`:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - cases/*
```

Item `ci.yml`:

```yaml
id: simple-case

watch:
  - cases/simple_case1/**
  - shared/**

steps:
  - id: build
    inputs:
      - cases/simple_case1/build.py
      - cases/simple_case1/input/**
      - shared/**
    run: [python, build.py]
    outputs: [generated]

  - id: verify
    inputs:
      - cases/simple_case1/verify.py
    run: [python, verify.py]
    outputs: [verify.json]
```

`watch` is coarse Git-selection input. Step `inputs` are SCons build
dependencies. If a step omits `inputs`, it inherits the item `watch` paths.

## Plan and run

```text
cad-ci plan --repo . --base <base-sha> --head <head-sha>
cad-ci run  --repo . --base <base-sha> --head <head-sha>

cad-ci run --repo . --item simple-case
cad-ci run --repo . --item simple-case --step verify
cad-ci run --repo . --item simple-case --until verify
cad-ci run --repo . --item simple-case --from build
```

`plan` explains which top-level items are selected and which dependencies they
have. It does not claim whether SCons considers a step dirty or current.

One `run` command makes one library `run_repository()` call. SCons owns
prerequisite traversal, incremental decisions and CacheDir reuse.

Partial selectors are mutually exclusive:
- `--step` forces that exact step after making prerequisites current;
- `--until` requests the named step normally;
- `--from` forces the named step and every following step.

Consumer output mirrors the item source path below `build/`. Public execution
evidence lives below `build/<item>/.cad-ci/`; private SCons state/cache stays
below `.cache/cad-ci/`.

## Reusable GitHub Actions

Consumers do not need to copy the generic CAD-CI setup into their own
workflows. Reference the released reusable workflow at the exact tool commit.

For a normal PR/push run:

```yaml
jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-run.yml@<tool-commit>
```

The called workflow:
- checks out the caller repository at its real source commit;
- checks out `tool.cad.ci` at the same commit that contains the called workflow;
- installs that exact tool/library stack;
- restores `.cache/cad-ci/`;
- performs exactly one `cad-ci run`;
- saves the SCons cache after success.

Consumers such as Forge that need domain setup between selection and execution
can first call `reusable-plan.yml`, prepare their runtime image, then call
`reusable-run.yml` with explicit source/base SHAs. The plan and run workflows
contain no Forge/SolidCraft/CAD-domain item names.

The optional `environment_json` input is only for non-secret domain values
such as an immutable runtime-image reference. Secrets remain normal GitHub
Actions secrets/permissions.

When a downstream consumer job must publish or transform generated output, set
`upload_build: true`. The run workflow uploads the complete materialized
`build/` tree, including hidden `.cad-ci` evidence, and returns its name as
`build_artifact_name`. Private `.cache/cad-ci` SCons state is never part of
that artifact.

## Durable build output

Fetch the generated build branch:

```text
cad-ci build fetch --repo . --out generated-build
```

Prepare a complete main baseline:

```text
cad-ci build prepare-main \
  --repo . \
  --candidate-root build \
  --out output/main \
  --source-commit <sha>
```

Prepare a sparse PR overlay:

```text
cad-ci build prepare-pr \
  --repo . \
  --candidate-root build \
  --out output/pr \
  --source-commit <sha> \
  --pull-request 12 \
  --items simple-case
```

A PR overlay contains only the selected top-level items. Runtime prerequisites
that SCons made current are not automatically added to the sparse overlay.

Update selected main items with `cad-ci build update-main`. Resolve main plus
an optional PR overlay with `cad-ci build resolve`.

Generated branches are published with `cad-ci publish build` and
`cad-ci publish pages`. Publication uses normal pushes, checks source
freshness and retries only generated-branch races.

## Verification order

Generic execution behaviour is developed and tested in `lib.py.cad.ci`.
The CLI is tested here against one exact released library revision. The complete
released tool/library stack is then black-box tested in `tool.cad.ci.test`.

Only after that exact stack passes may Forge or CAD migrate to it.
