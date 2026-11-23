# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.2` @
  `088644a05ff698957aef2ddc6cc5de037ddfa158`;
- `tool.cad.ci v0.35.0` @
  `9fcad92b7c5f10ae29a9cb085a4f25bb38ed00f9`;
- released-stack acceptance is owned by `tool.cad.ci.test`;
- consumers remain pinned to accepted releases until a newer exact stack passes
  that external acceptance.

## Current work

### #176 — central CAD release flow

**Now. Candidate implementation is on PR #177.**

The Forge v0.12.0 release attempt exposed a missing shared contract: a CAD-CI
consumer must not parse Pages or invent repository-local build checks before a
release.

Required order:

1. **complete** — document the release flow in the consumer manual;
2. **complete** — align requirements/design/API with that manual;
3. **complete** — define `reusable-release.yml` + `cad-release.yml` and their exact inputs/outputs;
4. **complete in candidate** — implement the shared CAD release workflow:
   - check the stable main ci-build-record from the generated build branch;
   - do not read `gh-pages`;
   - delegate tag/GitHub Release creation to exact released
     `tool.py.lib.ci v0.2.1`;
5. **complete in candidate** — copy-ready templates pin `v0.36.0`;
6. **now** — pass repository workflow/helper/template tests;
7. merge and release `tool.cad.ci v0.36.0`;
8. black-box accept the exact released flow in `tool.cad.ci.test`;
9. only then migrate Forge.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #176 central CAD release flow | **now** | PR #177 contains docs + reusable workflow + template; pass tests, release v0.36.0, then external acceptance. |
| #175 duplicate-looking main/dev runs | **next CI cleanup** | Decide whether the second post-merge run can be removed or reduced. |
| #174 readable CAD-CI names | **next CI cleanup** | Audit code/API/workflow names after #176's public names are chosen. |
| #173 duplicate CAD rebuild after permanent merge | **next CI cleanup** | Combine with #175 where behavior overlaps; prove required work before changing topology. |
| #172 self-describing Actions runs | **next CI cleanup** | Add literal run names after the release-flow work no longer blocks Forge. |
| #171 refresh permanent PR validation after branch updates | later | Keep separate from the release path. |
| #170 permanent-branch conflict recovery | later | Redesign after current release path is fixed; preserve exact branch history. |
| #164 reduce tool to shared workflows/governance adapters | later | Architectural cleanup; do not mix into #176. |
| #117 historical changelog alignment | later / docs-only | Keep separate from active work. |

## Boundary

`tool.cad.ci` transports released CAD-CI behavior into GitHub Actions. It
does not own generic build-record semantics, SCons execution or build-store
algorithms; those remain in `lib.py.cad.ci`.

For the release path, `tool.cad.ci` owns the CAD-specific workflow
composition. Generic tag/GitHub Release mechanics remain in
`tool.py.lib.ci`. A consumer must not fill gaps with local workflow code.
