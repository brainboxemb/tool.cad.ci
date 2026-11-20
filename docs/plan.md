# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.13.3 pins exact `lib.py.cad.ci` 0.8.3 at
`e8e951ed7e50c4fa754cc158729faf2927cccb31`.

The released stack already provides:

- one SCons-backed repository run;
- streamed concise operator logging;
- durable sparse PR build preparation/publication;
- PR-scope cleanup;
- high-level run-only reusable CI.

Forge currently performs PR verification and PR publication in two separate
GitHub jobs/runners. A representative one-model PR measured about 55 seconds
end-to-end: roughly 38 seconds for verification and 15 seconds for a second
publication runner.

## Current goal

Complete #70 as tool.cad.ci 0.14.0 by adding one reusable PR workflow that
performs the complete PR lifecycle on one runner:

`run -> prepare-pr -> publish`

For a closed PR the same workflow performs only scope cleanup.

## Required proof

- normal PR execution uses exactly one GitHub job/runner;
- CAD-CI execution still calls the released library once;
- no artifact upload/download is used between verification and publication;
- publication uses existing `cad-ci build prepare-pr` and
  `cad-ci publish build` commands;
- closed PRs use existing `cad-ci publish build-cleanup`;
- fork PR verification can run without attempting publication;
- source freshness/retry/selection semantics remain library-owned;
- tool.cad.ci.test black-box accepts the released workflow before Forge adopts
  it.

## Execution order

1. Update requirements/design for the single-runner PR workflow.
2. Add `.github/workflows/reusable-pr.yml` and workflow-contract tests.
3. Release tool.cad.ci 0.14.0 from the exact green main commit.
4. Add external acceptance in tool.cad.ci.test.
5. Update Forge to the released reusable PR workflow.
6. Measure one normal simple-box PR end-to-end against the <=30 s target.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #70 Add single-runner reusable PR build and publication workflow | now | Removes the second PR publication runner while preserving the normal full PR lifecycle. |

## Boundary

`lib.py.cad.ci` owns selection, SCons execution, build-store semantics,
source freshness and generated-branch publication mechanics.

`tool.cad.ci` owns the reusable GitHub Actions orchestration that invokes
those existing commands on one runner.
