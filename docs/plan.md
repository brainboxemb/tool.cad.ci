# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.18.1` is released at exact commit
`e29d3127d5d3f9310f3cab4e27430a64a61c21cc`.

It pins released `lib.py.cad.ci 0.11.0` at exact commit
`e621daf6e309bdd0e3f643a12007f1b66490696d`.

External acceptance is complete:

- `tool.cad.ci.test` #77 / PR #78;
- acceptance run `45019713862` — success;
- the released root composite action passed durable same-runner execution;
- the immediately following step on that same runner verified the returned
  prepared scope and exact generated build commit;
- no artifact handoff or second post-action runner is required.

Issue #95 is complete and closed.

## Current work

No tool implementation is active.

Issue #99 is released and externally accepted. Consumers may adopt the exact
0.18.1 / 0.11.0 pair.

## Open issue assessment — 2026-11-22

No open tool issues remain after #99 is closed.

## Next trigger

Open a new issue only for:

- a new released library capability that needs thin public exposure;
- a genuine CLI/workflow/action surface defect;
- an exact released-library repin that requires a new tool release;
- measured consumer evidence that a reusable tool-owned orchestration surface
  is missing.

Every new released tool/library pair or public action contract must pass
`tool.cad.ci.test` before consumer adoption.
