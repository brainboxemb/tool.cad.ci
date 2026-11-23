# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.2` is released at
  `088644a05ff698957aef2ddc6cc5de037ddfa158`;
- v0.18.2 preserves real `cq.Assembly` support while restoring normal
  `cq.Workplane` / Shape export compatibility found by external #248;
- `lib.py.cad.verification v0.16.0` remains immutable at
  `c7c145b7be0c602724e8cca874ef29990baaad1e`;
- current released tool baseline is v0.34.1 on lib v0.18.1.

## Current work

### #165 — publish tool v0.34.2

**Now.**

Publish a thin exact-library adoption patch:

1. pin exact `lib.py.cad.ci v0.18.2` @ `088644a05ff698957aef2ddc6cc5de037ddfa158`;
2. change no tool-owned CAD-CI behavior;
3. publish `tool.cad.ci v0.34.2`;
4. repin copy-ready workflow templates to exact v0.34.2 while preserving
   template-version numbers because copied workflow structure is unchanged;
5. keep CLI/workflow contracts and one-runner lifecycle semantics unchanged;
6. repin existing tool.cad.ci.test #248 and rerun full external acceptance
   before Forge #740 resumes.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #165 Publish v0.34.2 on lib.py.cad.ci 0.18.2 | **now** | Finish exact-stack CI/release, then rerun external #248. |
| #117 Align historical changelog | later / docs-only | Keep separate from the active Forge migration. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter. CadQuery model
form detection/export, path matching, builder capability parsing,
verification-package wiring, SCons, runtime batching and cache semantics remain
library-owned.
