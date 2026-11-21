# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.16.0` at
`2b0dbb45b93d5de820d96059d23184891824c030` exposes the released named
complete build/Page scope API from `lib.py.cad.ci 0.9.1`.

External acceptance in `tool.cad.ci.test` #60 exposed a library-only
compatibility defect: 0.9.1 durable build validation rejects current SCons
engine-schema-2 evidence. Library issue #74 fixes that without changing the
tool API.

## Current goal

Complete #82 by pinning exact released `lib.py.cad.ci 0.9.2`.

This is a dependency-only patch:
- pin the exact 0.9.2 library commit;
- update the boundary test/release metadata;
- change no CLI, workflow or publication semantics;
- release a patch tool version;
- resume `tool.cad.ci.test` #60.

## Execution order

1. [#82, now] Pin exact released lib.py.cad.ci 0.9.2 and update boundary evidence.
2. [#82] Release the exact green tool patch.
3. [tool.cad.ci.test #60] Repin and rerun complete black-box acceptance.
4. [Forge #572] Adopt only the accepted stack.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #82 Adopt lib.py.cad.ci patch for current SCons evidence schema | now | lib.py.cad.ci 0.9.2 is released; pin it now and resume external named-scope acceptance. |
| #76 Expose released CAD-CI bounded parallel jobs | later | Independent scheduling exposure; keep separate from the development-lane migration. |

Immediate chain:

`lib #74 -> tool #82 -> acceptance #60 -> Forge #572`.
