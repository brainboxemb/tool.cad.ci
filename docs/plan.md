# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.13.2 pins exact `lib.py.cad.ci` 0.8.2.

Released `lib.py.cad.ci` 0.8.3 is available at exact commit
`e8e951ed7e50c4fa754cc158729faf2927cccb31`.

0.8.3 fixes operator logging in the generic SCons adapter:
- consumer output is streamed live instead of replayed after the run;
- executed actions use concise CAD-CI labels;
- internal `_execute_bundle(...)` target/source dumps are suppressed.

No tool-owned behavior is required.

## Current goal

Complete #68 as a thin patch release that pins exact library 0.8.3.

## Execution order

1. Pin exact library commit
   `e8e951ed7e50c4fa754cc158729faf2927cccb31`.
2. Bump tool version to 0.13.3 and update changelog/exact-pin test.
3. Run complete tool CI.
4. Merge only after green CI.
5. Confirm release points to the exact tested main commit.
6. Externally accept streamed concise logging in `tool.cad.ci.test`.
7. Only then update the Forge consumer pin and rerun the real Forge proof.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #68 Adopt lib.py.cad.ci 0.8.3 streamed execution logging | now | Thin patch release required before external logging acceptance and Forge adoption. |

## Boundary

`lib.py.cad.ci` owns SCons execution and logging behavior.
The tool remains a thin CLI/workflow consumer.
