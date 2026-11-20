# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci 0.14.2` is the current accepted tool stack.

Released `lib.py.cad.ci 0.9.0` at exact commit
`91e4a87315a04b8cfde573e447c2bc4d871edd35` adds explicit bounded SCons
parallelism and target-private dependency snapshots. The library defaults to
`jobs=1`; scheduling and safety remain fully library-owned.

## Current goal

Complete #76 and release tool.cad.ci 0.15.0.

The tool only exposes the released library input:

- `cad-ci run --jobs N`;
- reusable-run workflow input `jobs`;
- high-level reusable-ci workflow forwards `jobs`;
- reusable-pr workflow accepts/forwards `jobs` so normal Forge PRs can use the
  feature.

No tool-owned worker pool, target loop, dependency locking or scheduling logic
is allowed.

## Required proof

- exact lib.py.cad.ci 0.9.0 commit is pinned;
- CLI default forwards `jobs=1`;
- explicit CLI jobs value forwards unchanged;
- reusable helper forwards one jobs value to the CLI;
- reusable-run, reusable-ci and reusable-pr expose/forward the same positive
  numeric input with default 1;
- selection, partial selectors, publication and concurrency semantics remain
  unchanged;
- complete tool CI is green;
- release 0.15.0 from the exact green main commit;
- tool.cad.ci.test proves jobs>1 through the released stack before Forge uses
  it.

## Execution order

1. Pin exact lib.py.cad.ci 0.9.0.
2. Add thin CLI/helper/workflow jobs forwarding.
3. Update tool-specific tests.
4. Prepare/release tool.cad.ci 0.15.0 in the same logical change.
5. Pin exact released 0.15.0 in tool.cad.ci.test.
6. Add black-box shared-dependency parallel acceptance there.
7. Only after external acceptance, adopt bounded jobs in Forge and remeasure
   the 10-case reference graph.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #76 Expose released CAD-CI bounded parallel jobs | now | Thin exposure of released library 0.9.0; no generic execution behavior belongs here. |

## Boundary

`lib.py.cad.ci` remains the sole owner of SCons scheduling, dependency
snapshots, parallel safety, selection and evidence.
