# Using tool.cad.ci from Forge or CAD

Forge and CAD consume a released `tool.cad.ci` revision as external tooling.

Do not call a reusable workflow from this repository and do not consume moving
`main`. A consumer records one exact released tool commit, bootstraps it and
invokes that checkout against its own repository.

Example external-repository pin:

```yaml
repositories:
  cad-ci:
    type: git
    url: https://github.com/brainboxemb/tool.cad.ci.git
    version: <exact-release-commit>
```

Then:

```text
python ext/cad-ci/cad-ci.py plan --repo . --base <base-sha> --head <head-sha>
python ext/cad-ci/cad-ci.py run  --repo . --base <base-sha> --head <head-sha>
```

The consumer workflow owns GitHub-specific setup such as checkout and
credentials. It does not own changed-path rules, item loops, consumer commands
or rebuild decisions.

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
