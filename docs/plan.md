# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.13.0 pins exact `lib.py.cad.ci` 0.8.0 and that
stack is externally accepted.

Released `lib.py.cad.ci` 0.8.1 is now available at exact commit
`ab701bf9ef46892040f4593a74b16805b7187bea`.

0.8.1 adds safe parent-relative paths inside explicit item-scoped source
patterns. No tool-owned behavior is required.

## Current goal

Complete #64 as a thin patch release that pins exact library 0.8.1.

## Execution order

1. Pin exact library commit
   `ab701bf9ef46892040f4593a74b16805b7187bea`.
2. Update version/changelog and exact-pin test.
3. Run complete tool CI.
4. Merge only after green CI.
5. Confirm release points to the exact tested main commit.
6. Externally accept that exact release in `tool.cad.ci.test`.
7. Only then start the Forge reference migration.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #64 Adopt lib.py.cad.ci 0.8.1 parent-relative item paths | now | Thin patch release required before external acceptance and Forge adoption. |

## Boundary

`lib.py.cad.ci` owns all source-path normalization semantics. The tool remains
a thin CLI/workflow consumer.
