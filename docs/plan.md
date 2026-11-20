# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

The current released tool is 0.11.0. Released `lib.py.cad.ci 0.7.0` is now
available at exact commit `8955c74055105b06d6af69e0d2f82b6b1fbf575a`.

## Current goal

Complete one 0.12.0 maintenance release containing:

- #46 central cancellation of superseded high-level runs;
- adoption of released library 0.7.0 timing evidence.

No generic timing or SCons behavior is reimplemented in this repository.

## Execution order

1. Keep concurrency only on high-level `reusable-ci.yml`.
2. Pin exact library 0.7.0 commit.
3. Prove the CLI exposes BUILT/CURRENT timing evidence from the library.
4. Release the combined tool as 0.12.0 after green CI.
5. Accept that exact release once in `tool.cad.ci.test`, together with its
   #34/#35 acceptance-overhead housekeeping.
6. Only after that combined external acceptance update Forge.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #46 Cancel superseded normal CAD-CI runs centrally | now | Included in the combined 0.12.0 maintenance release with library 0.7.0 adoption. |

No other open implementation issues exist in this repository snapshot.

## Boundary

Workflow concurrency is scheduling only. Timing/evidence, item selection, SCons
execution and cache semantics remain owned by `lib.py.cad.ci`.
