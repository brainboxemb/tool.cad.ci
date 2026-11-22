# Using tool.cad.ci from Forge or CAD

Forge and CAD consume one exact released `tool.cad.ci` revision. Do not
consume moving `main`.

A normal consumer uses the high-level reusable workflow and keeps only its
trigger, permissions and the exact released tool commit:

```yaml
jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@<exact-release-commit>
```

The reusable workflow owns generic checkout, Python/tool setup and one repository run. The consumer does not duplicate those steps.

A consumer that needs domain preparation between planning and execution may
instead use `reusable-plan.yml` and `reusable-run.yml` at that same exact
tool commit. Forge's immutable runtime-image preparation is an example of such
domain work.

A consumer that needs later domain-owned work on the **same runner** can use the
released root composite action instead of reproducing generic setup locally.

For a long-lived durable lane, the same action resolves the previous build
scope, runs one CAD-CI graph, prepares/publishes the complete durable scope and
returns the prepared scope to later consumer steps without a job boundary:

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

      - run: ./consumer-site-build \
          --build-evidence "${{ steps.cad.outputs.prepared_scope }}"

      - run: python -m cad_ci_tool publish pages ...
```

This is deliberately one runner/workspace: no artifact upload/download, no
second checkout/bootstrap and no second SCons run. Site generation and Pages
content remain consumer-owned.

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
