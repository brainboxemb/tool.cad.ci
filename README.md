# tool.cad.ci

Small repository-local CI planner and runner for the SolidCraft Forge and CAD repositories.

The consumer repository owns its CI behaviour. `tool.cad.ci` reads that behaviour, decides which items are affected, builds an explicit plan, and runs or reuses item output.

## Consumer layout

```text
cad-ci.yml
src/
tests/unit/ci.yml
examples/example-a/ci.yml
qualification/item-a/ci.yml
```

Root `cad-ci.yml`:

```yaml
schema: 1
items:
  - tests/unit
  - examples/*
  - qualification/*
```

Item `ci.yml`:

```yaml
id: item-a
kind: qualification
needs:
  - integration-example-a
watch:
  - qualification/item-a/**
  - src/**
strategy:
  affected: changed
  reuse: true
steps:
  - id: build
    run: [python, build.py]
    outputs: [model.txt]
  - id: verify
    run: [python, verify.py]
    outputs: [verified.txt]
```

`kind` is descriptive only. The runner does not attach behaviour to names such as `qualification`, `library-test`, or `integration`.

## Commands

```text
cad-ci plan --repo . --base <base-sha> --head <head-sha>
cad-ci run --repo . --base <base-sha> --head <head-sha>
cad-ci plan --repo . --changed qualification/item-a/model.py
cad-ci run --repo . --item item-a
cad-ci run --repo . --item item-a --step verify
cad-ci run --repo . --item item-a --from build
cad-ci run --repo . --item item-a --until verify
```

Generated output mirrors the item path under `build/`.

For CI, prefer `--base/--head`. The tool runs `git diff` itself so changed-path logic does not live in workflow YAML. `--changed` is useful for local tests and diagnostics.
