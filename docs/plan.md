# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.0` is immutable at
  `eb291abd6bb34b585d04019d154e7756d36436f9`;
- it adds wildcard-aware recursive `/**` matching and the public
  repository-builder `verification_package: true` capability with
  `CAD_CI_VERIFICATION_WHEEL`;
- `lib.py.cad.verification v0.16.0` remains immutable at
  `c7c145b7be0c602724e8cca874ef29990baaad1e`;
- the currently released tool baseline is v0.33.2.

## Current work

### #160 — publish tool v0.34.0

**Now.**

Publish a thin exact-library adoption release:

1. pin exact `lib.py.cad.ci v0.18.0`;
2. change no tool-owned CAD-CI behavior;
3. publish `tool.cad.ci v0.34.0`;
4. repin copy-ready workflow templates to exact v0.34.0 while preserving
   template-version numbers because copied workflow structure is unchanged;
5. update exact-stack qualification tests and consumer manual baseline;
6. hand the exact released stack to `tool.cad.ci.test` for black-box
   acceptance before Forge #740 resumes.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #160 Publish v0.34.0 on lib.py.cad.ci 0.18.0 | **now** | Finish exact-stack CI/release, then external acceptance. |
| #117 Align historical changelog | later / docs-only | Keep separate from the active Forge migration. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter. Path matching,
builder capability parsing, verification-package wiring, SCons, runtime
batching and cache semantics remain library-owned.
