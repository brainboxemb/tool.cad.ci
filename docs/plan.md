# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

Released `lib.py.cad.ci` 0.8.0 is available at exact commit
`e2056c0d5ac361f0d021e58e55025e02c5688acf`.

Its hosted-runner contract and Git-diff affected-item behavior have already been
accepted independently in `tool.cad.ci.test` against the previous released
tool stack.

The current released tool is 0.12.3 and still pins library 0.7.1.

## Current goal

Complete #62 by publishing a thin tool release that pins exact library 0.8.0.

No CLI, workflow, selection, SCons or publication behavior is added here.

## Execution order

1. Pin exact library commit
   `e2056c0d5ac361f0d021e58e55025e02c5688acf`.
2. Update tool version/changelog for the feature-capable stack.
3. Run the complete tool test suite.
4. Merge only after green CI.
5. Confirm the release points to the exact tested main commit.
6. Pin that exact released tool in `tool.cad.ci.test`.
7. Externally accept local item paths/templates/nested IDs there.
8. Only then allow Forge reference-item migration.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #62 Adopt lib.py.cad.ci 0.8.0 local item configuration | now | Thin release step required before external acceptance and Forge adoption. |

## Boundary

`lib.py.cad.ci` owns all new configuration semantics. The tool only exposes the
exact released library through its existing CLI/workflow surface.
