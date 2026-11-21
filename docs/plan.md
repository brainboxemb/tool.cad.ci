# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.14.2` at
`4c1016d594368146fb9c16602f01c158e85d9afb` is the current externally
accepted Forge stack.

It pins released `lib.py.cad.ci 0.8.4` at
`4e033fd17e911b3feb92b1a34433b884ca788ab6`.

The complete PR lifecycle already has a direct-source single-runner workflow.
Forge #558 exposed the corresponding main-runner gap: a reusable workflow owns
its called job, so Forge cannot append its site generator to that same runner
and currently pays artifact transport plus two extra tool bootstraps.

## Current goal

Complete #78 and release 0.15.0.

The release adds one root composite action for consumers that need
consumer-owned post-run steps on the same runner. The action is orchestration
only; it exposes the existing released run/build/publish stack without adding
generic CAD-CI behaviour.

## Required proof

- exact released action/tool source is the tool source; no second tool checkout;
- exact pinned library source is shallow-checked out;
- tool + library remain available through `PYTHONPATH` after the action;
- only external PyYAML/SCons dependencies are installed;
- exact source is checked out and only the exact base is fetched for an
  incremental run;
- full run skips the base fetch;
- GHCR authentication is generic and token-safe;
- exactly one `cad-ci run` is invoked;
- no artifact transport exists inside the action;
- no consumer/domain command or publication policy exists inside the action;
- complete tool CI is green;
- release 0.15.0 from the exact green merge commit;
- pin that exact release in `tool.cad.ci.test` and prove same-runner
  post-run CLI reuse before Forge adoption.

## Execution order

1. [#78] Add and test the root same-runner composite action.
2. [#78] Release 0.15.0 from the green merge commit.
3. [#78] Pin 0.15.0 in `tool.cad.ci.test` and add black-box same-runner
   acceptance.
4. Close #78 only after external acceptance is green.
5. Migrate Forge #558 to one main runner using the accepted action.
6. Continue #76 separately: expose released library 0.9.0 bounded parallel
   jobs; do not mix scheduling changes into the same-runner migration.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #78 Expose same-runner CAD-CI run action for consumer-owned post-run publication | now | Required by Forge #558 to eliminate artifact/runner/bootstrap boundaries while keeping Forge site generation consumer-owned. |
| #76 Expose released CAD-CI bounded parallel jobs | next | Library 0.9.0 already owns safe parallel execution; expose and externally accept it separately after the orchestration migration. |

## Boundary

`lib.py.cad.ci` remains the sole owner of selection semantics, SCons
execution, durable-store membership/deletion, Pages mechanics and generated
branch safety.
