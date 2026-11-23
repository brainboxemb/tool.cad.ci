# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.17.0` is immutable at
  `a68bcd9e3940b21872dea5fc210bcd9a26519ebc`;
- that release owns built-in build123d/CadQuery shared batching, reusable
  verification integration and the canonical library package hierarchy;
- `lib.py.cad.verification v0.16.0` remains the verification engine consumed
  by the library integration.

## Current work

### #154 — release tool v0.33.0

**Now.**

Keep the tool thin while moving it to the final owner-layer library release:

1. pin the exact `lib.py.cad.ci v0.17.0` commit;
2. migrate obsolete root-module imports to canonical library owner packages;
3. change no public CLI/workflow behavior;
4. publish `tool.cad.ci v0.33.0`;
5. repin copy-ready templates to exact `v0.33.0` without template-version changes;
6. hand the exact released tool/library pair to `tool.cad.ci.test` for black-box acceptance.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #154 Release v0.33.0 with lib.py.cad.ci 0.17.0 builders + verification | **now** | Finish thin-tool CI/release, then external acceptance. |
| #117 Align historical changelog | later / docs-only | Apply shared changelog presentation only. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter above the exact
released library. Builder schema, verification integration, selection, SCons,
runtime batching, durable state and Pages publication remain library-owned.

Do not add compatibility shims for old library import paths, a consumer post-step
phase, a second CAD-CI graph or engine-specific implementation here.
