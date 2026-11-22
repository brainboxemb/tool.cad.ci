# Using tool.cad.ci from a consumer repository

Every consumer uses one exact released `tool.cad.ci` revision. Do not consume
moving `main`. For a new repository, start with
[`new-repository.md`](new-repository.md) and the versioned templates under
[`templates/github/workflows/`](../templates/github/workflows/README.md).

A normal run-only consumer starts from the canonical `cad-ci.yml` template
and keeps only its trigger, permissions and the exact released tool commit:

```yaml
jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@<exact-release-commit>
```

The reusable workflow owns generic checkout, Python/tool setup and one repository run. The consumer does not duplicate those steps.

**Credential rule:** For untrusted PR-head verification, use a read-only
workflow such as `reusable-ci.yml`. Never give untrusted item commands a
write-scoped token or invoke the durable composite action on arbitrary PR-head
source. The durable action is for trusted branch source. For untrusted/read-only PR
verification, use `reusable-ci.yml`.

A long-lived branch that needs later domain-owned work on the **same runner**
uses the root composite action in durable mode rather than splitting the flow
across reusable-workflow jobs:

```yaml
jobs:
  durable:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: read
    steps:
      - id: cad
        uses: brainboxemb/tool.cad.ci@<exact-release-commit>
        with:
          source_sha: ${{ github.sha }}
          durable_scope: ${{ github.ref_name }}
          source_ref: ${{ github.ref_name }}
          jobs: "2"
          github_token: ${{ github.token }}

      - name: Build consumer site
        run: >-
          python site/build.py
          --build-evidence "${{ steps.cad.outputs.prepared_scope }}"
          --build-commit "${{ steps.cad.outputs.build_commit }}"

      - name: Publish consumer Pages
        run: python -m cad_ci_tool publish pages ...
```

The durable action keeps checkout, exact tool/library bootstrap, one SCons run,
complete build-scope preparation and durable build publication in one runner
workspace. It does not upload/download build artifacts and does not start a
second CAD-CI job. Consumer site generation and Pages content remain outside the
action.

A consumer that needs **selection only** may call the public advanced
`reusable-plan.yml` at an exact released tool SHA. Do not call
`reusable-run.yml` directly; `reusable-ci.yml` owns the supported run-only
workflow. If domain setup and CAD-CI execution must share a runner, use the
root composite action.

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

The authoritative mapping is `templates/manifest.json`. A consumer may change
documented repository-owned values, but it must not silently grow generic
checkout/bootstrap, changed-path, CAD-CI execution, durable-state or merge API
logic. When the canonical template version changes, consumers can compare their
header against the released template before adopting it.


## Permanent development lanes

A repository using stable `main` plus long-lived `dev-cad` / `dev-ci`
starts from `cad-ci-lanes.yml`, not a local classifier.

The template configures the released `reusable-ci.yml` lane policy. The
consumer does not paginate pull-request files, loop over docs paths or compute
promotion `full_run` expressions. Repository-owned changes are limited to
intentional lane names/docs prefixes and ordinary workflow/job dependencies.
