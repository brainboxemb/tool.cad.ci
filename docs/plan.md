# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.17.2` is immutable at
  `d4e8140d988be06460326fda802e514b6b306d64`;
- it preserves host ownership of bind-mounted shared runtime output while
  retaining one-container batching and the build123d isolated interpreter;
- `lib.py.cad.verification v0.16.0` remains the reusable verification engine.

## Current work

### #158 — publish tool v0.33.2

**Now.**

Publish a dependency-only patch:

1. pin exact `lib.py.cad.ci v0.17.2`;
2. keep all tool implementation/workflow behavior unchanged;
3. publish `tool.cad.ci v0.33.2`;
4. repin copy-ready templates to exact v0.33.2 without template-version changes;
5. hand the exact released patch stack back to `tool.cad.ci.test` #240.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #158 Publish v0.33.2 with lib.py.cad.ci 0.17.2 ownership fix | **now** | Finish exact-stack CI/release and external acceptance. |
| #117 Align historical changelog | later / docs-only | Apply shared changelog presentation only. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter. Container user
identity, runtime batching, verification, SCons and cache semantics remain
library-owned.
