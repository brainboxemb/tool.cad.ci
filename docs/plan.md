# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.2` @
  `088644a05ff698957aef2ddc6cc5de037ddfa158`;
- `tool.cad.ci v0.34.2` @
  `37f7a82c6769279d33367144c56976da89bb1a5d`;
- exact v0.34.2/v0.18.2 external acceptance is complete in
  `tool.cad.ci.test #248`, including CadQuery Workplane + Assembly and
  dev-ci/main/dev-cad durable provenance;
- `lib.py.cad.verification v0.16.0` remains immutable at
  `c7c145b7be0c602724e8cca874ef29990baaad1e`.

## Current work

### #168 — targeted reusable CI selection / v0.35.0

**Now.** This is the missing staged-migration invocation contract exposed by
Forge #740.

Required order:

1. expose optional public `item` and JSON-list `changed_paths` on the
   read-only reusable CI surface;
2. forward directly to existing CLI `--item` / `--changed` selection;
3. keep targeted selectors mutually exclusive with effective full-run;
4. update canonical `cad-ci-lanes` to template version 5 so manual targeted
   dispatch is read-only while empty dispatch remains durable;
5. keep exact library pin v0.18.2; add no planner/SCons behavior here;
6. require tool CI green and publish exact `tool.cad.ci v0.35.0`;
7. externally black-box accept targeted single- and multi-item selection in
   `tool.cad.ci.test`;
8. only then repin Forge #740/#755 and qualify 1 -> 5 -> 10 -> full.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #168 targeted reusable CI selection | **now** | Finish v0.35.0, external acceptance, then return to Forge #740. |
| #164 workflow/tool ownership cleanup | later | Architectural cleanup; do not block Forge migration. |
| #117 historical changelog alignment | later / docs-only | Keep separate from active migration. |

## Boundary

`tool.cad.ci` transports GitHub workflow inputs to the released CLI. It does
not own affected-item calculation, dependency closure, direct-dependent
selection, SCons execution/cache, builders, verification-package wiring or
durable publication semantics.
