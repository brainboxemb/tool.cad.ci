# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current goal

Adopt the released repository-variable support from `lib.py.cad.ci` through
#47 without duplicating configuration or environment logic in this tool.

## Execution order

1. `lib.py.cad.ci` 0.5.0 is published at exact commit
   `345794521fe162eb1908e1e8f38a6eabb02c8290`.
2. Complete #47 by pinning that exact library commit and documenting the
   resulting tool/library environment contract.
3. Release the updated tool after this repository's CI is green.
4. Update `tool.cad.ci.test` to the exact released tool commit and prove a
   root `cad-ci.yml:variables` value reaches a real consumer command.
5. Only after that external test update Forge through its own runtime-config
   issue.
6. Complete #46 separately; superseded-run cancellation is workflow behaviour
   and must not be mixed into the repository-variable change.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #47 Release tool.cad.ci with cad-ci.yml repository variable support | now | Active 0.9.0 change. The tested library 0.5.0 release exists; pin it, pass tool CI, release and prove the exact tool revision in `tool.cad.ci.test`. |
| #46 Cancel superseded normal CAD-CI runs centrally | next | Generic reusable-workflow behaviour. Keep separate from #47 and implement after the repository-variable release path is externally tested. |

No other open repository issues exist at this point in time.

## Boundary

Do not implement or parse root repository variables in this tool. That behaviour
belongs to `lib.py.cad.ci`. This repository pins the released library and
exposes it through the CLI/reusable workflows.
