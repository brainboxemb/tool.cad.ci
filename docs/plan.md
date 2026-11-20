# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `tool.cad.ci` 0.12.2 is externally accepted with
`lib.py.cad.ci` 0.7.1.

Forge #366 has proven one sparse PR durable-build scope. The next stable-main
step exposed one CLI translation defect: `build prepare-main` currently passes
all configured items, including `process: false` items, while the released
library defines a full run as exactly the processed items.

## Current goal

Complete #60 without adding new selection semantics.

For unselected `build prepare-main`, translate the request to the released
library full-run selection:

```text
affected_items(items, None)
```

Selectable build operations remain unchanged.

## Execution order

1. Update requirements/design for full-run main-candidate selection.
2. Make unselected `prepare-main` use the library full-run selection.
3. Add a CLI test proving `process: false` output is not required.
4. Keep all publication/workflow tests green.
5. Release the next patch version.
6. Externally accept the exact release in `tool.cad.ci.test`.
7. Return to Forge #366 stable `build/main` bootstrap.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #60 Make build prepare-main use the library full-run process selection | now | Direct blocker for Forge #366 stable main bootstrap; tool must reuse library-owned full-run semantics. |

## Boundary

The tool does not decide what `process` means.

`lib.py.cad.ci` owns full-run selection. The CLI only delegates to that
existing semantics when `prepare-main` has no explicit selection source.
