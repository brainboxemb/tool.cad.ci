# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current released state

`tool.cad.ci 0.16.2` is released at exact commit
`59e4c4d3f377f906b33bb2d1fee808f96c6fb1b9`.

It pins released `lib.py.cad.ci 0.9.3` at exact commit
`74486c441f1f2b170ff3dc06e0edcaf662fbec6b`.

External `tool.cad.ci.test` #62 / PR #63 passed the complete released-stack
suite, including the selective-startup active-closure case.

Historical PR #77 remains closed as stale; it was based on tool 0.14.2 and must
not be revived or rebased into current main.

## Current work

There is no active release migration.

Open #76 remains valid **later** work: expose the already released library
`jobs` option through the thin CLI/reusable workflow surface.

#76 must start from current main and must not:
- downgrade the current tool version/library pin;
- add a tool-owned worker pool;
- duplicate selection, scheduling, dependency or SCons logic.

## Execution order

1. Consumers may adopt the externally accepted 0.16.2 / 0.9.3 stack.
2. Measure real consumer selective-run startup with that exact released stack.
3. Activate #76 only as a separate, independently justified tool change.
4. If #76 is implemented, release the next appropriate tool version and prove
   `jobs > 1` in tool.cad.ci.test before consumer adoption.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #76 Expose released CAD-CI bounded parallel jobs | **later** | Library support is already released; thin exposure remains useful but is intentionally separate from the accepted startup optimization. |
