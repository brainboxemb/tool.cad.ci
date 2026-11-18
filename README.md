# tool.cad.ci

Repository-local CI planning, execution and generated-output handling for the SolidCraft Forge and CAD repositories.

The consumer repository owns its CI behaviour. `tool.cad.ci` reads that behaviour, decides which items are affected, runs or reuses them, and can publish verified per-item build output and Pages.

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

## Run commands

```text
cad-ci plan --repo . --base <base-sha> --head <head-sha>
cad-ci run --repo . --base <base-sha> --head <head-sha>
cad-ci plan --repo . --changed qualification/item-a/model.py
cad-ci run --repo . --item item-a
cad-ci run --repo . --item item-a --step verify
cad-ci run --repo . --item item-a --from build
cad-ci run --repo . --item item-a --until verify
```

Generated runner output mirrors the item source path under `build/`.

For CI, prefer `--base/--head`. The tool runs `git diff` itself so changed-path logic does not live in workflow YAML.

## Durable build output

Prepare a complete baseline from every configured item:

```text
cad-ci build prepare-main \
  --repo . \
  --candidate-root build \
  --out output/main \
  --source-commit <sha>
```

Prepare a sparse PR overlay using item IDs:

```text
cad-ci build prepare-pr \
  --repo . \
  --candidate-root build \
  --out output/pr \
  --source-commit <sha> \
  --pull-request 12 \
  --items item-a
```

After the first complete baseline exists, update only rebuilt items on a normal main run:

```text
cad-ci build update-main \
  --repo . \
  --main generated-build/main \
  --candidate-root build \
  --out output/main \
  --source-commit <sha> \
  --items item-a
```

Resolve `main` plus a PR overlay with `cad-ci build resolve`. `cad-ci build promote` remains available when a verified PR overlay is deliberately promoted.

Generated branches are published with `cad-ci publish build` and `cad-ci publish pages`. The publisher uses normal pushes, checks that the source branch is still current, and retries branch-head races without force-push.

## Pages framework

`cad_ci.pages` provides:

- the base HTML structure and navigation;
- stable root and `previews/pr-N` handling;
- `provenance.json`;
- support for a consumer-supplied stylesheet;
- a configurable Pages base path.

Forge, CAD and other consumers keep their own content and CSS.

See `docs/build-pages.md` for the branch layout and publication flow.
