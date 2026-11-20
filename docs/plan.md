# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.14.1` at
`18812d38e2390c23fd3c431cfde2ce9367bdfd40` is externally accepted and is
the current Forge stack.

Released `lib.py.cad.ci 0.8.4` at
`4e033fd17e911b3feb92b1a34433b884ca788ab6` adds safe durable-main cleanup
for items that no longer exist in current processed repository configuration.

The generic behavior is complete in the library. The tool only needs to expose
the new library input.

## Current goal

Complete #74 and release the next tool patch.

For `cad-ci build update-main`:

- affected current items remain the sparse replacement set;
- the complete current `process:true` item set is also passed to
  `lib.py.cad.ci 0.8.4`;
- the tool does not compare durable manifests, decide deletions or remove paths.

## Required proof

- the exact 0.8.4 library commit is pinned;
- changed/base-head selection remains unchanged for replacement items;
- the current processed set comes from released library planning semantics;
- non-processed items are absent from the current durable-main membership set;
- both item collections reach `update_main()` distinctly;
- existing PR/main preparation behavior remains unchanged;
- complete tool CI is green.

## Execution order

1. Pin exact released lib.py.cad.ci 0.8.4.
2. Expose current processed items to `update_main()`.
3. Test the thin CLI boundary.
4. Release the next tool patch.
5. Pin that release in `tool.cad.ci.test`.
6. Prove removed-item cleanup black-box.
7. Only then update Forge and retry durable main cleanup/Pages.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #74 Adopt lib.py.cad.ci 0.8.4 for removed durable main items | now | Thin tool exposure of the already released generic build-store contract. |

## Boundary

`lib.py.cad.ci` remains the sole owner of selection semantics, durable-store
membership/deletion, ownership safety and publication behavior.
