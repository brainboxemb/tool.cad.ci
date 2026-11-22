# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.18.0` is released at exact commit
`b62f9d0b169aa201a3c66c3166f364396b2d71bc`.

It pins released `lib.py.cad.ci 0.10.0` at exact commit
`397fb04005b46de8d433cb18c091b1e73714b877`.

External acceptance is complete:

- `tool.cad.ci.test` #73 / PR #74;
- acceptance run `45010776155` — success;
- the released root composite action passed durable same-runner execution;
- the immediately following step on that same runner verified the returned
  prepared scope and exact generated build commit;
- no artifact handoff or second post-action runner is required.

Issue #95 is complete and closed.

## Current work

No tool implementation is active.

The tool remains a thin exposure/pinning layer. Generic SCons, build-store,
projection, scheduling, caching and freshness behavior remains library-owned.

## Next trigger

Open a new issue only for:

- a new released library capability that needs thin public exposure;
- a genuine CLI/workflow/action surface defect;
- an exact released-library repin that requires a new tool release;
- measured consumer evidence that a reusable tool-owned orchestration surface
  is missing.

Every new released tool/library pair or public action contract must pass
`tool.cad.ci.test` before consumer adoption.
