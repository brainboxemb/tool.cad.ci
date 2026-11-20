# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

`tool.cad.ci 0.12.0` is released at commit
`05af21546ea71907cd9db4b56f5d5ccd644c0170`.

Repository-specific Pages publication has been removed from main without a
separate tool release.

Released `lib.py.cad.ci 0.7.1` is available at exact commit
`c031f5dce3a4b0b207d8ce24716b5e11cdd12df2`.

## Current goal

Complete #56 as the minimal `tool.cad.ci 0.12.1` patch.

The patch changes only the exact released library pin needed for the build-store
evidence compatibility regression fix.

## Execution order

1. Pin exact lib.py.cad.ci 0.7.1 commit.
2. Update the exact-pin boundary test.
3. Set tool version/changelog to 0.12.1.
4. Run normal tool tests.
5. Merge/release 0.12.1 after green CI.
6. Update the already-open tool.cad.ci.test PR #37 to exact 0.12.1 and rerun
   the same combined external acceptance.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #56 Pin lib.py.cad.ci 0.7.1 build-store compatibility fix | now | Minimal patch pin required by the failed external 0.12.0 acceptance. |

No other open implementation issues exist in this repository snapshot.

## Boundary

No CLI, workflow, timing or publication behavior changes in this patch.
Repository Pages housekeeping remains unreleased housekeeping and is not listed
as a 0.12.1 product change.
