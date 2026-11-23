# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.2` @
  `088644a05ff698957aef2ddc6cc5de037ddfa158`;
- `tool.cad.ci v0.36.0` @
  `093eafb0eabf6b6617ec82dde17a76fdc718ae12`;
- released-stack acceptance is owned by `tool.cad.ci.test`;
- consumers remain pinned to accepted releases until a newer exact stack passes
  that external acceptance.

## Current work

### #178 — fix reusable release runtime bootstrap

**Now.**

External acceptance of v0.36.0 reached the new release workflow but failed
before the intended stale-source check because the workflow checked out the
pinned CAD-CI library without installing its runtime dependencies. Run
`45242477963` failed with `ModuleNotFoundError: No module named 'yaml'`.

Required order:

1. install the same PyYAML/SCons runtime dependencies already used by
   `reusable-run.yml` and `reusable-durable.yml` before `release-check`;
2. enforce that bootstrap in workflow tests;
3. patch-release `tool.cad.ci v0.36.1` and repin the copy-ready templates;
4. rerun `tool.cad.ci.test #256` from the failed stale-SHA step;
5. only after external acceptance may Forge #739 migrate.

### #176 — central CAD release flow

**Implemented and released in v0.36.0; external acceptance blocked by #178.**

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
6. **complete** — repository workflow/helper/template tests passed;
7. **complete** — released `tool.cad.ci v0.36.0`;
8. **blocked on #178** — black-box acceptance reached the release workflow and exposed the missing runtime bootstrap;
9. only after the v0.36.1 fix passes external acceptance may Forge migrate.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #178 release workflow runtime dependencies | **now** | Add the missing released-workflow bootstrap, patch-release v0.36.1 and rerun external acceptance. |
| #176 central CAD release flow | **implemented, acceptance blocked** | v0.36.0 is released; #178 fixes the dependency bootstrap found by `tool.cad.ci.test #256`. |
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
