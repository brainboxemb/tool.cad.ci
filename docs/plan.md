# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.14.0 at
`5bca68eb109a69e3a05e7711daf394926ee0e7d4` provides the complete
single-runner PR lifecycle and is externally accepted in `tool.cad.ci.test`.

Forge has adopted that workflow. A clean simple-box-only production PR measured
41 seconds end-to-end. The selected graph was exactly:

- `forge-package:tool_build`;
- `simple-box:contract_test`;
- `simple-box:model_verify`.

Measured fixed bootstrap cost before the first CAD-CI action includes roughly:

- caller checkout with full history/refs: 3.7 s;
- external PyYAML/SCons install: 3.1 s;
- docker/login-action: 1.8 s.

## Current goal

Complete #72 as tool.cad.ci 0.14.1 by removing avoidable PR bootstrap overhead
without changing selection, SCons execution, durable build or publication
semantics.

## Required proof

- caller PR head checkout is shallow;
- incremental selection fetches only the exact base SHA it needs;
- full runs/closed cleanup do not perform the base fetch;
- GHCR login uses Docker CLI directly and remains token-safe;
- external dependency install avoids dependency recursion and eager bytecode
  compilation;
- no persistent GitHub Actions cache is added;
- complete tool CI is green;
- released 0.14.1 is externally accepted before Forge adoption;
- the same simple-box-only Forge measurement is repeated.

## Execution order

1. Implement/test #72 in tool.cad.ci.
2. Release 0.14.1 from exact green main.
3. Accept exact 0.14.1 in tool.cad.ci.test.
4. Update Forge PR workflow pin only.
5. Repeat the one-file simple-box measurement.
6. Continue runtime optimization only from the new measured remainder.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #72 Reduce reusable PR bootstrap overhead | now | Removes measured fixed setup work before CAD-CI starts; no execution semantics change. |

## Boundary

`lib.py.cad.ci` remains the sole owner of selection, SCons execution,
build-store and publication semantics.

`tool.cad.ci` owns reusable GitHub runner orchestration and may minimize
checkout/authentication/package-bootstrap overhead without adding a second
planner or persistent build cache.
