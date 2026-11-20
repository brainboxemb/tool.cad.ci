# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

The released consumer stack is `tool.cad.ci` 0.12.1 with
`lib.py.cad.ci` 0.7.1.

Forge exposed one workflow-artifact transport defect while using
`upload_build: true`: a valid run that selects no CAD-CI targets produces no
`build/` directory, but the reusable workflow still advertises an artifact
name and fails on mandatory upload.

## Current goal

Complete #58 as a workflow-only artifact-transport fix.

The tool must distinguish:

- requested artifact transport;
- actual materialized build output.

No selection/build semantics move into this repository.

## Execution order

1. Update reusable-workflow requirements/design for optional materialized output.
2. Detect whether `build/` actually contains materialized output after
   `cad-ci run`.
3. Publish `build_artifact_name` only when output exists.
4. Upload only when output exists.
5. Extend workflow contract tests for both output/no-output behavior.
6. Merge/release the next patch after green CI.
7. Prove the released stack again in `tool.cad.ci.test`.
8. Only then update Forge and continue #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #58 Do not fail build-artifact upload when a CAD-CI run produces no build output | now | Generic reusable-workflow artifact-transport defect exposed by a docs-only Forge run. |

## Boundary

The tool may detect whether a transport source exists. It must not decide which
CAD-CI items should run or synthesize build output.

`lib.py.cad.ci` remains the owner of selection, execution and materialized
build semantics.
