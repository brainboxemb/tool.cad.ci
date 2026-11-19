# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current goal

Keep the released CAD-CI tool stable while removing one remaining unwanted
workflow side effect. Do not add Forge, SolidCraft or ordinary Python-library
CI behaviour here.

## Execution order

1. Complete #42 on this branch: cache restore/save is removed and tests reject
   persistent cache actions.
2. Release 0.8.0 after this repository's CI is green.
3. Update `tool.cad.ci.test` to the exact 0.8.0 commit and require external
   acceptance to pass.
4. Only then update Forge/CAD repositories to the accepted 0.8.0 pin.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #43 Make docs/plan.md the repository work source of truth | now | Housekeeping required to make this plan and issue assessment permanent repository policy. |
| #42 Remove implicit GitHub Actions cache side effects from reusable CAD-CI | now | Active 0.8.0 change: cache restore/save has been removed. Complete repository CI, release, and external acceptance before closing. |
| #26 Allow reusable run workflow to hand build output to downstream consumer jobs | effectively complete but still open | The current 0.7.1 workflow exposes `upload_build`, `build_artifact_name`, uploads `build/`, and the external test passes. Re-check the exact acceptance wording, then close if no requirement remains. |
| #1 Implement v0.1 repository-local CI planner and runner | effectively complete but still open | The repository has progressed to 0.7.1 and the planner/runner/tool stack is released and externally tested. Review the original checklist only to confirm no historical requirement is still intentionally open, then close/supersede. |

## Boundary

Do not use this plan to redesign `lib.py.cad.ci`. If a change requires new
generic execution, selection, SCons, build-store or Pages behaviour, implement
and release that in `lib.py.cad.ci` first.
