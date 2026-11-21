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
suite.

Forge consumer evidence for this stack:
- old 0.16.1 / 0.9.2 pre-target interval: 26.507 s;
- new 0.16.2 / 0.9.3 pre-target interval: 1.375 s.

Historical PR #77 remains closed as stale and must not be revived.

## Current work

Issue #76 is **now**.

Expose the already released library-owned bounded SCons `jobs` option through
the thin tool surface.

This work must remain a pure forwarding layer:
- CLI `run --jobs N`, default 1;
- reusable workflow/action input, default 1;
- positive-integer validation at the public boundary;
- exact value forwarded to library `run_repository(..., jobs=N)`;
- no tool-owned worker pool, target loop, scheduling or cache logic.

## Why now

The startup bottleneck is already resolved in the owner library. Full promotion
runs still execute the complete graph with `jobs=1` and remain minutes long.
Bounded parallelism already exists in the released library, so exposing it is
the next owner-correct optimization step.

The goal is to enable measurement, not to promise a fixed total runtime.

## Execution order

1. [#76, now] Add/validate thin CLI and workflow jobs inputs.
2. [#76] Keep complete tool tests green and release the next minor version.
3. [tool.cad.ci.test] Pin the exact release and black-box `jobs > 1`.
4. [Forge] Adopt only after external acceptance; measure a full promotion with a
   deliberately bounded jobs value.
5. Keep default jobs=1 unless/until a consumer explicitly opts into parallelism.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #76 Expose released CAD-CI bounded parallel jobs | **now** | Generic support is already released in lib 0.9.3; expose only a validated thin forwarding surface. |
