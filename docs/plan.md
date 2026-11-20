# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current goal

Complete #51: consume the exact released `lib.py.cad.ci 0.6.0` revision so
item-level `process` participation is available through the released thin tool
stack.

The generic behavior is already implemented and released in the library. This
repository must not add a second parser, planner or execution rule for
`process`.

## Execution order

1. Pin exact library release commit
   `dac8c5b5e1147a401730fda31f9bf9de2278c4ee`.
2. Prove through tool tests that:
   - the exact library revision is pinned;
   - plan/run continue to delegate selection/execution to the library;
   - no local `process` implementation is introduced.
3. Release the updated tool only after this repository CI is green.
4. Update `tool.cad.ci.test` to the exact released tool revision and prove
   staged processing end to end.
5. Only after black-box acceptance may Forge consume the released `process`
   behavior.
6. Complete #46 separately.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #51 Consume lib.py.cad.ci 0.6.0 process selection | now | Required downstream adoption step for the already released library behavior. Keep the tool thin and release one exact tool/library stack. |
| #46 Cancel superseded normal CAD-CI runs centrally | next | Independent reusable-workflow behavior. Do not mix it into the process-selection pin/release. |

## Released state

`tool.cad.ci 0.10.0` already includes the completed GHCR authentication work
from #49. That work is not part of #51 and must remain unchanged.

## Boundary

`lib.py.cad.ci` owns `process` parsing, validation, Git selection and SCons
target participation. `tool.cad.ci` only pins the released library and exposes
its existing CLI/workflow surface.
