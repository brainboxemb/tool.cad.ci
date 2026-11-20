# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.13.3 pins exact `lib.py.cad.ci` 0.8.3 at
`e8e951ed7e50c4fa754cc158729faf2927cccb31`.

Forge currently performs PR verification and PR publication in two separate
GitHub jobs/runners. A representative one-model PR measured about 55 seconds
end-to-end: roughly 38 seconds for verification and 15 seconds for a second
publication runner.

The current reusable bootstrap also installs tool.cad.ci as an editable
package. Pip then clones/builds the exact lib.py.cad.ci Git dependency and
builds both project packages before CAD-CI starts.

## Current goal

Complete #70 as tool.cad.ci 0.14.0.

The complete normal PR lifecycle must run on one runner:

`checkout -> CAD-CI run -> prepare-pr -> publish`

The workflow must use the exact called tool source and its exact pinned
lib.py.cad.ci source directly through `PYTHONPATH`. It must not build or
install either BrainboxEmb package during a consumer PR.

For a closed PR the same workflow performs only scope cleanup.

## Required proof

- normal PR execution uses exactly one GitHub job/runner;
- CAD-CI execution still calls the released library once;
- no artifact upload/download is used between verification and publication;
- no editable install or wheel build is performed for tool.cad.ci or
  lib.py.cad.ci;
- only external runtime dependencies are installed on the clean runner;
- publication uses existing library-owned build/publication commands;
- closed PRs cancel superseded work and remove their durable PR scope;
- tool.cad.ci.test black-box accepts the released workflow before Forge adopts
  it.

## Execution order

1. Add the single-runner reusable PR workflow and source bootstrap.
2. Pass complete tool CI.
3. Merge #70 and release tool.cad.ci 0.14.0 from the exact green main commit.
4. Add external acceptance in tool.cad.ci.test.
5. Update Forge to the released reusable PR workflow.
6. Measure one normal simple-box PR end-to-end against the <=30 s target.
7. Only then optimize any remaining measured bootstrap/checkout overhead.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #70 Add single-runner reusable PR build and publication workflow | now | Removes the second PR runner and avoids building/installing our own Python packages during consumer PRs. |

## Boundary

`lib.py.cad.ci` owns selection, SCons execution, build-store semantics,
source freshness and generated-branch publication mechanics.

`tool.cad.ci` owns GitHub Actions orchestration and the lightweight bootstrap
that exposes the exact tool/library source on the runner.
