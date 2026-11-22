# Using tool.cad.ci from a consumer repository

Every consumer uses one exact released `tool.cad.ci` revision. Do not consume
moving `main`. For a new repository, start with the [consumer manual](manual/README.md) and
copy a versioned workflow from [`manual/templates/`](manual/templates/).

A normal consumer starts from the canonical `cad-ci.yml` template and
keeps only its trigger, permissions and exact released tool version tag:

```yaml
jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@v0.23.0
```

The reusable workflow owns generic checkout, Python/tool setup and one
repository run. The consumer does not duplicate those steps.

**Credential rule:** untrusted PR verification uses read-only workflow
permissions. Repository-specific build, verification or site-generation work
belongs in root `cad-ci.yml` and item `ci.yml` steps when it is part of the
repository CI graph. A need for work after CAD-CI is not a reason to add a
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

Root `cad-ci.yml` discovers items and can define repository defaults:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - tool
  - cases/*
```

Each item owns its behaviour:

```yaml
id: simple-case

needs:
  - tool

watch:
  - cases/simple_case/**
  - shared/**

steps:
  - id: build
    inputs:
      - cases/simple_case/build.py
      - cases/simple_case/input/**
      - shared/**
    run: [python, build.py]
    outputs: [generated]

  - id: verify
    inputs:
      - cases/simple_case/verify.py
    run: [python, verify.py]
    outputs: [verify.json]
```

`watch` selects top-level items from a Git diff. Step `inputs` drive SCons
incremental decisions.

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

The template configures the released `reusable-ci.yml` lane policy. The
consumer does not paginate pull-request files, loop over docs paths or compute
promotion `full_run` expressions. Repository-owned changes are limited to
intentional lane names/docs prefixes and ordinary workflow/job dependencies.
