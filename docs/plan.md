# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

The current release is `tool.cad.ci 0.11.0`, which pins released
`lib.py.cad.ci 0.6.0` and exposes item-level `process` participation. That
stack is externally accepted in `tool.cad.ci.test` and already consumed by
Forge.

## Current goal

Complete #46: cancel superseded normal high-level reusable CAD-CI runs
centrally.

## Execution order

1. Add one concurrency contract to high-level `reusable-ci.yml`.
2. Scope it by caller repository, caller workflow and PR/branch.
3. Enable `cancel-in-progress: true`.
4. Do not add the same group to `reusable-plan.yml` or `reusable-run.yml`;
   split consumers may intentionally call both within one caller workflow.
5. Prove the workflow contract in tool tests.
6. Include the change in one maintenance release after green CI.
7. Externally accept that exact release in `tool.cad.ci.test`.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #46 Cancel superseded normal CAD-CI runs centrally | now | Current tool-maintenance work; high-level reusable workflow only. |

No other open implementation issues exist in this repository snapshot.

## Boundary

This is GitHub Actions scheduling only. It does not change CAD item selection,
SCons execution, cache semantics or consumer commands.
