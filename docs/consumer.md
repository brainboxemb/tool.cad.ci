# Using tool.cad.ci from a consumer repository

Every consumer uses one exact released `tool.cad.ci` revision. Do not consume
moving `main`. For a new repository, start with the [consumer manual](manual/README.md) and
copy a versioned workflow from [`manual/templates/`](manual/templates/).

A normal consumer starts from the canonical `cad-ci.yml` template and
keeps only its trigger, permissions and exact released tool version tag:

```yaml
jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@v0.30.0
```

The reusable workflow owns generic checkout, Python/tool setup and one
repository run. The consumer does not duplicate those steps.

**Credential rule:** untrusted PR verification uses read-only workflow
permissions. Repository-specific build, verification or site-generation implementation
belongs in repository-owned builders referenced from item `ci.yml` when it is
part of the repository CI graph. A need for work after CAD-CI is not a reason to add a
second execution API or a consumer-local orchestration workaround.

A consumer that genuinely needs **selection only** may use the documented
advanced `reusable-plan.yml` surface. `reusable-run.yml` remains internal
behind `reusable-ci.yml`.

Local/manual use still invokes the released CLI directly:

```text
cad-ci plan --repo . --base <base-sha> --head <head-sha>
cad-ci run  --repo . --base <base-sha> --head <head-sha>
```

The consumer owns its domain commands, credentials and runtime preparation. It
does not own changed-path rules, item loops, generic checkout/tool bootstrap,
persistent cache transport or rebuild decisions.

## Repository config

Root `cad-ci.yml` discovers items, defines repository defaults and names
repository-owned builders:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - tool
  - cases/*

builders:
  python-model: ci/builders/python-model
```

A normal item `ci.yml` stays declarative:

```yaml
id: simple-case
builder: python-model

needs:
  - tool

watch:
  item:
    - input/**
  repo:
    - shared/**
```

The builder directory owns the executable implementation:

```yaml
# ci/builders/python-model/builder.yml
schema: 1

steps:
  - id: build
    run: 'python "$CAD_CI_BUILDER_PATH/build.py"'
    outputs: [generated]

  - id: verify
    run: 'python "$CAD_CI_BUILDER_PATH/verify.py"'
    outputs: [verify.json]
```

`watch` selects top-level items from a Git diff. Builder step `inputs` drive
SCons incremental decisions when a narrower input set is useful. The complete
builder directory is automatically selection- and signature-significant for
every using item.

Legacy item-local `steps` remain accepted by the pinned library during
migration, but new repositories should keep executable `run` commands out of
item `ci.yml`.

One tool run makes one SCons-backed library run. The consumer does not need to
know or reproduce the dependency execution order.

## Output

Consumer output mirrors source item paths:

```text
build/cases/simple_case/
  generated/
  verify.json
  .cad-ci/
    item.json
    steps/
      build.json
      verify.json
```

Private SCons target/cache/state data lives below `.cache/cad-ci/` and is not
published as durable build output.

## Verification before consumer migration

A new tool release is first pinned and tested in `tool.cad.ci.test` using
representative generic cases. Only after that exact released stack passes should
Forge or CAD update its tool pin.


## Template provenance

Copied workflow files keep their canonical header:

```yaml
# template: tool.cad.ci/<template-id>
# template-version: <integer>
```

The template header is the authoritative provenance record. A consumer may
change documented repository-owned values, but it must not silently grow
generic checkout/bootstrap, changed-path, CAD-CI execution, durable-state or
merge API logic. When the canonical template version changes, consumers compare
their copied header with the released file under `docs/manual/templates/` before
adopting it.


## Permanent development lanes

A repository using stable `main` plus long-lived `dev-cad` / `dev-ci`
starts from `cad-ci-lanes.yml`, not a local classifier.

Template version 3 configures both released lane surfaces. Pull requests use
`reusable-ci.yml` lane policy; permanent `push` and
`workflow_dispatch` events use `reusable-durable.yml` with the current
branch name as source ref and durable scope. The durable route performs one
CAD-CI graph and library-owned build/Pages publication on one runner.

The wrapper exposes `build_branch` and `pages_branch` as repository-owned
generated-ref settings. Their defaults are `build` and `gh-pages`; isolated
acceptance or staging repositories may use values such as
`test-output/build` and `test-output/gh-pages`.

The consumer does not paginate pull-request files, loop over docs paths, compute
promotion `full_run` expressions, or add its own durable publication steps.
Repository-owned changes are limited to intentional branch/lane/docs-prefix
values, generated output branch names, permissions and ordinary workflow
dependencies.