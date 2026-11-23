# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released and accepted baseline

- `tool.cad.ci v0.31.0` @
  `27bdf67077ddd485cea95ba199069249c20c2a46`;
- v0.31.0 pins `lib.py.cad.ci 0.14.0` @
  `b24e9a3826dfc07e07b4f3fd9971fcb4ab5aa12d`;
- configurable durable generated branches remain exposed through
  `build_branch` / `pages_branch`;
- public workflow configuration now uses literal consumer-facing names:
  `stable_branch`, `development_branches`, `permanent_branches`,
  `temporary_branch_prefixes`, `resolution_branch_prefix`,
  `pull_request_policy` and `command_environment`;
- JSON remains an encoded value format for structured/list workflow inputs;
  internal helper/CLI flags may retain explicit transport names such as
  `--lane-refs-json` and `--environment-json`;
- released v0.30.0 and earlier tags remain immutable and retain their original
  public workflow contracts;
- `tool.cad.ci.test` #223 is complete: v0.31.0 passed real GitHub PR,
  durable publication, permanent-branch promotion/synchronization,
  merge-policy, exact-SHA retirement and conservative cleanup acceptance;
- live durable acceptance remains isolated on
  `test-output/build` / `test-output/gh-pages`; normal consumer defaults
  remain `build` / `gh-pages`.

## v0.31 public workflow-name acceptance

Issue #145 is complete.

External evidence in `tool.cad.ci.test` includes:

- PR #225 / run #280 (`45147169700`) for
  `pull_request_policy` and `command_environment`;
- PR #227 / run #284 (`45148007487`) for direct development-branch
  promotion classification and forced full run;
- PR #228 / merge-policy run #56 (`45148617436`) for live
  `stable_branch`, `development_branches` and `permanent_branches`;
- branch-retirement run #44 (`45148940131`);
- branch-cleanup run #49 (`45149155623`);
- final accepted-baseline promotion/synchronization through PRs #229-#231,
  with final dev-cad durable run #295 green.

No compatibility aliases were added to v0.31.0. Older exact release tags remain
the compatibility boundary.

## Current work

No open runtime/API work.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #117 Align historical changelog | **later / docs-only** | Apply shared changelog presentation without runtime/API changes. |

## Boundary

Generic merge/cleanup behavior, CAD-CI execution, publication and JSON parsing
remain in their existing owners. Public workflow naming is a tool/workflow
adapter concern only.

Forge/CAD may now migrate to the fully accepted v0.31.0 public workflow
contract through their separately reviewed consumer issues.
