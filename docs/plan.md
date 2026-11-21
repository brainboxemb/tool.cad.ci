# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.16.1` at exact commit
`4c6bb8b35009ef5008bd99134cf84b59fddc0b8a` consumes externally accepted
`lib.py.cad.ci 0.9.2`.

The named-scope chain (#82 / tool.cad.ci.test #60) is complete.

`lib.py.cad.ci 0.9.3` is now released at exact commit
`74486c441f1f2b170ff3dc06e0edcaf662fbec6b`. It reduces selective-run startup
work by preparing only the active SCons target closure and sharing one source
inventory per invocation.

Historical PR #77 is closed as stale because it was based on tool 0.14.2 and
would downgrade current release state. Open issue #76 remains valid future work
for thin bounded-jobs exposure.

## Current goal

Complete #84 by pinning exact released `lib.py.cad.ci 0.9.3`.

This is a dependency-only patch:
- pin the exact 0.9.3 library commit;
- update the boundary test and release metadata;
- change no CLI, workflow, publication or selection semantics;
- release tool.cad.ci 0.16.2;
- black-box the exact released stack before Forge adopts it.

## Execution order

1. [#84, now] Pin exact lib.py.cad.ci 0.9.3.
2. [#84] Release exact green tool.cad.ci 0.16.2.
3. [tool.cad.ci.test] Add one released-stack acceptance issue for the selective
   startup behavior.
4. [Forge] Adopt the accepted exact tool revision and remeasure the real
   selective PR startup interval.
5. [#76, later] Expose bounded jobs as a separate tool change.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #84 Adopt lib.py.cad.ci 0.9.3 selective-startup optimization | **now** | Dependency-only repin required to expose the released generic optimization. |
| #76 Expose released CAD-CI bounded parallel jobs | **later** | Still valid, but deliberately separate so startup optimization can be measured independently. |

Immediate chain:

`lib 0.9.3 -> tool #84 / 0.16.2 -> black-box acceptance -> Forge measurement`.
