# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.15.0` is the current externally accepted stack.
It exposes the same-runner composite action already consumed by Forge.

Forge #572 now requires long-lived development integration lanes. The generic
named complete-scope mechanics belong first in `lib.py.cad.ci` #72.

## Current goal

Complete #80 immediately after the exact #72 library release.

Expose only the released library behavior needed to:

- prepare/update/publish one named complete build scope;
- publish one named Pages subtree;
- preserve existing `main` and PR interfaces during migration.

Do not implement reconciliation, path safety or Pages preservation locally.

## Required proof

- the exact released #72 library revision is pinned;
- CLI arguments are forwarded unchanged into the library;
- existing main/PR publication commands remain compatible;
- named build/Page scope commands have clear help and validation errors;
- complete tool CI remains green;
- release the exact green tool revision.

## Execution order

1. [lib.py.cad.ci #72] Wait for the generic named-scope release.
2. [#80, now after #72] Pin that exact release.
3. [#80] Expose the minimal CLI/workflow surface.
4. [#80] Run complete tool tests and release.
5. [tool.cad.ci.test #60] Black-box accept sibling-scope isolation.
6. [Forge #572] Adopt only the externally accepted release.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #80 Expose released named build/Page scopes for long-lived integration lanes | blocked on #72 | Next required step for Forge #572. No generic implementation belongs here. |
| #76 Expose released CAD-CI bounded parallel jobs | later | Independent scheduling exposure; keep separate from the development-lane migration. |

Immediate chain:

`lib #72 -> tool #80 -> acceptance #60 -> Forge #572`.
