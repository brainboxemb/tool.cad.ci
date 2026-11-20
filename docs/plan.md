# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.13.1 pins exact `lib.py.cad.ci` 0.8.1.

Released `lib.py.cad.ci` 0.8.2 is available at exact commit
`d645b65281064f69f175bb645c6c956f72f3b446`.

0.8.2 makes durable build-store ownership safe for nested parent/child item
paths. No tool-owned behavior is required.

## Current goal

Complete #66 as a thin patch release that pins exact library 0.8.2.

## Execution order

1. Pin exact library commit
   `d645b65281064f69f175bb645c6c956f72f3b446`.
2. Bump tool version to 0.13.2 and update changelog/exact-pin test.
3. Run complete tool CI.
4. Merge only after green CI.
5. Confirm release points to the exact tested main commit.
6. Externally accept nested durable publication in `tool.cad.ci.test`.
7. Resume Forge PR #499 only after that external suite is green.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #66 Adopt lib.py.cad.ci 0.8.2 nested durable ownership | now | Thin patch release required before external publication acceptance and Forge adoption. |

## Boundary

`lib.py.cad.ci` owns durable item ownership and nested build-store behavior.
The tool remains a thin CLI/workflow consumer.
