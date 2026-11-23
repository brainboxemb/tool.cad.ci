# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.1` is released at
  `6064a53b9ea1c340d49893ca0f8d1fa5e3e138ea`;
- v0.18.1 adds only the library-owned CadQuery Assembly export correction from
  lib.py.cad.ci #128 on top of v0.18.0;
- `lib.py.cad.verification v0.16.0` remains immutable at
  `c7c145b7be0c602724e8cca874ef29990baaad1e`;
- the currently released tool baseline is `v0.34.0`, pinned to library
  v0.18.0.

## Current work

### #162 — publish tool v0.34.1

**Now.**

Publish a thin exact-library adoption patch:

1. pin exact `lib.py.cad.ci v0.18.1` @ `6064a53b9ea1c340d49893ca0f8d1fa5e3e138ea`;
2. change no tool-owned CAD-CI behavior;
3. publish `tool.cad.ci v0.34.1`;
4. repin copy-ready workflow templates to exact v0.34.1 while preserving
   template-version numbers because copied workflow structure is unchanged;
5. keep CLI/workflow contracts and one-runner lifecycle semantics unchanged;
6. hand the exact released stack to `tool.cad.ci.test` for one additional
   black-box CadQuery Assembly acceptance before Forge #740 resumes.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #162 Publish v0.34.1 on lib.py.cad.ci 0.18.1 | **now** | Finish exact-stack CI/release, then external Assembly acceptance. |
| #117 Align historical changelog | later / docs-only | Keep separate from the active Forge migration. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter. CadQuery model
form detection/export, path matching, builder capability parsing,
verification-package wiring, SCons, runtime batching and cache semantics remain
library-owned.
