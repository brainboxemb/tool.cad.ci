# Public API inventory and contract audit

Status: **audit draft**, 2026-11-22. This document distinguishes observed entry points from approved long-term contracts. It does not declare existing implementation automatically correct.

## Product boundary

`tool.cad.ci` exposes a released CAD-CI command-line interface and GitHub Actions adapters above an exactly pinned `lib.py.cad.ci` library (currently released 0.12.0 for this candidate). Planning, execution, cache decisions, build-store, Pages content placement and publication algorithms belong to the library. The repository also currently exposes a GitHub merge-governance workflow; whether that service belongs in this product is **under architecture review**.

A consumer uses an exact released version tag rather than a moving branch. CLI arguments and workflow_call inputs are separate interface types and are not interchangeable.

Consumer repository configuration is interpreted by the pinned library. The
preferred item contract is declarative: root `cad-ci.yml` names repository
builder directories, item `ci.yml` selects a builder, and the builder's
`builder.yml` owns executable steps. `tool.cad.ci` does not parse or
reinterpret that configuration.

## Surface inventory

| Surface | Intended audience / observed status | Implementation | Verification | Contract decision |
| --- | --- | --- | --- | --- |
| `cad-ci plan` | Public CLI, explain selection | `cad_ci_tool/cli.py` | `tests/test_run_cli.py`; external acceptance | Retain, confirm options |
| `cad-ci run` | Public CLI, run one SCons graph | `cad_ci_tool/cli.py` | `tests/test_run_cli.py`; external acceptance | Retain |
| `cad-ci build ...` | Public CLI, durable build operations | `cad_ci_tool/publication_cli.py` | `tests/test_publication_cli.py`; external acceptance | Retain, audit subcommand contracts |
| `cad-ci pages ...` | Public CLI, local Pages installation/cleanup | `cad_ci_tool/publication_cli.py` | `tests/test_publication_cli.py` | Retain, document arguments |
| `cad-ci publish ...` | Public CLI, generated branches and Pages | `cad_ci_tool/publication_cli.py` | `tests/test_publication_cli.py`; external acceptance | Retain, audit subcommand contracts |
| `reusable-ci.yml` | **Public stable** run-only workflow | `.github/workflows/reusable-ci.yml` | `tests/test_reusable_ci.py`; `tool.cad.ci.test` | Retain |
| `reusable-pr.yml` | **Public stable** complete PR verification/publication lifecycle | `.github/workflows/reusable-pr.yml` | `tests/test_reusable_ci.py`; candidate acceptance | Retain |
| `reusable-plan.yml` | **Public advanced** selection-only workflow | `.github/workflows/reusable-plan.yml` | unit/schema + external candidate plan output | Retain as explicit plan-only API; not default |
| `reusable-run.yml` | **Internal workflow implementation** delegated from `reusable-ci.yml` | `.github/workflows/reusable-run.yml` | unit/schema via public `reusable-ci.yml` | Not a supported direct consumer API |
| `reusable-merge-policy.yml` | GitHub merge governance; used by Forge | `.github/workflows/reusable-merge-policy.yml`, `scripts/merge_policy.py`, `scripts/merge_command.py`, `scripts/merge_resolution.py` | `tests/test_merge_policy.py`, `tests/test_merge_command.py`; external merge policy case | **Ownership review**; preserve current consumer behavior |
| `reusable-branch-cleanup.yml` | Conservative stale temporary-branch maintenance | `.github/workflows/reusable-branch-cleanup.yml`, `scripts/branch_cleanup.py` | `tests/test_branch_cleanup.py`; live external acceptance in `tool.cad.ci.test` #180 | Released governance surface |
| `reusable-branch-retirement.yml` | Separately reviewed exact-SHA branch retirement | `.github/workflows/reusable-branch-retirement.yml`, `scripts/branch_retirement.py` | `tests/test_branch_retirement.py`; live external acceptance required | Candidate destructive governance surface under #140 |
| `ci.yml` | This repository's CI, **not** consumer API | `.github/workflows/ci.yml` | GitHub Actions | Internal |
| `scripts/*.py` | Workflow/maintenance implementation, **not** separate public CLI contract | `scripts/` | associated tests | Internal unless explicitly promoted |

**Usage evidence:** Forge's `merge-policy.yml` calls the released merge-policy workflow. Forge and CAD still invoke historical released root actions; those immutable releases remain valid while their migration to the workflow/config model is tracked separately. `tool.cad.ci.test` now qualifies the released `reusable-ci.yml` consumer path.

## Versioned consumer wrappers

The executable GitHub Actions API is defined by the reusable workflows below. New
repositories do not invent their own generic wrapper around those surfaces:
they copy a versioned canonical wrapper from
[`docs/manual/templates/`](manual/README.md).

Template provenance is recorded twice:

- header: `# template: ...` and `# template-version: N`;
- copy-ready file header: exact released `tool-release` version tag.

The integer template version changes when the copied consumer structure or
required repository-owned configuration changes. It is separate from the
semantic `tool.cad.ci` release version. Every copied template calls one exact released tool version tag.

Manual templates are not an additional execution API. They are versioned,
copy-ready wrappers that only select and configure the supported surfaces below.

## GitHub Actions API (observed, not yet approved as a stable specification)

### `reusable-plan.yml`

Entry point: `workflow_call`. Inputs: `source_sha` (string, default triggering source SHA), `base_sha` (string, default triggering base/previous SHA), `full_run` (boolean, default false). Outputs: `plan_json` (compact selected item plan), `source_sha`, `base_sha`. Requires `contents: read`. Side effect: runner checkout/install and planning; **does not run the model graph or publish output**. This is an advanced **plan-only** API for callers that need the generic selection result without executing CAD-CI. Normal run consumers use `reusable-ci.yml`.

### `reusable-run.yml`

Entry point: `workflow_call`. Inputs: `source_sha`, `base_sha`, `full_run`, optional `pr_policy_json`, `jobs` (number, default 1), `environment_json` (nonsecret JSON string, default `{}`), `upload_build` (boolean, default false), `build_artifact_name` (string, default `cad-ci-build`). Output: `build_artifact_name` (empty when nothing uploaded). Requires `contents: read` and `packages: read`. Side effects: shallow caller checkout/base fetch, optional lane-policy preflight, then tool/library/Python/GHCR bootstrap and exactly one CAD-CI run when not skipped; optional Actions artifact upload. No durable build-branch publication.

### `reusable-ci.yml`

Entry point: `workflow_call`. Same run inputs and artifact-name output as `reusable-run.yml`, plus optional `pr_policy_json` (default empty). Adds caller-scoped concurrency/cancellation and delegates run to `reusable-run.yml`. This is the default public **run-only** workflow. `reusable-run.yml` is its internal implementation and is not a separate supported consumer API.

When `pr_policy_json` is set on a pull request, the existing single runner may apply stable/lane/docs-only policy before Python/library/GHCR bootstrap. The policy supports `stable_ref`, `lane_refs`, and `docs_only_prefixes`. Exact configured lane→stable promotion forces full CI; a non-empty development-lane diff entirely below configured docs prefixes succeeds without CAD-CI bootstrap; all other/unknown cases fail safe to running CI. No second classifier job is created.

### `reusable-pr.yml`

Public `workflow_call` entry point for a complete PR lifecycle:
`opened`, `reopened`, `synchronize` and `closed`. Inputs:
`full_run` (boolean, default false), `jobs` (positive number, default 1),
`environment_json` (non-secret string environment JSON, default `{}`),
`publish_build` (boolean, default true).

**Exactly one job and one runner.** It checks out the exact caller/source
and immutable tool/library pins, runs one CAD-CI graph, optionally
prepares and publishes the same-repository sparse PR build scope from
the same workspace, and cleans closed-PR output without SCons execution.
No artifact handoff or second runner is part of this API. Fork PRs do not
publish or delete durable caller branches. `publish_build: false`
disables write-side effects, not the job's declared maximum permissions;
a genuinely read-only caller should use `reusable-ci.yml`.

The workflow declares `contents: write` for optional durable output and
`packages: read` for GHCR. This is a deliberate one-runner contract:
same-repository PR publication runs in that job, while fork PRs never publish.
Callers needing strictly read-only verification use `reusable-ci.yml`.
Do not split the workflow into a second publication runner.

### `reusable-branch-retirement.yml` — separately reviewed destructive governance API

Entry point: `workflow_call`, intended behind an owner-only multiline
`/retire-branches` issue comment. Each subsequent line must contain exactly
one branch name and one reviewed 40-character SHA. The workflow refuses
stable/lane/permanent refs and open same-repository PR heads, preflights all
requested refs before mutation, and re-reads each SHA immediately before
deletion. Missing refs are idempotent; moved refs are retained and reported.

This API exists only for deliberately retiring unique history after review. It
does not alter the evidence rules of normal `/cleanup-branches`.

### `reusable-branch-cleanup.yml` — separate governance maintenance API\n\nEntry point: `workflow_call`, intended behind an owner-only `/cleanup-branches` comment. Required: `command` (exact `/cleanup-branches`), `issue_number`, `lane_refs_json`. Optional: `stable_ref` (default `main`), `permanent_refs_json` and `temporary_prefixes_json`. Requires `contents: write`, `pull-requests: read` and `issues: write`. It enumerates current branches/open PRs/merged PR head evidence, and deletes only allow-listed temporary branches whose current inspected SHA is positively retired by integration into a configured durable ref or an exact merged-PR `(ref, SHA)` record. It re-reads the branch SHA immediately before deletion. Permanent/generated refs, `backup/*`, open PR heads, moved refs and unique/unmerged history are retained and reported.\n\nThis maintenance surface is distinct from the post-merge cleanup performed by `reusable-merge-policy.yml`; it exists for stale branches left by historical/manual workflows. Live deletion must be qualified in `tool.cad.ci.test` before consumer adoption.\n\n### `reusable-merge-policy.yml` — separate governance API

Entry point: `workflow_call`, intended behind owner-only `/merge` and
multiline `/merge-resolved` commands. Required inputs are `command`,
`pull_request_number` and `lane_refs_json`. Optional policy inputs are
`stable_ref` (default `main`), `permanent_refs_json`,
`temporary_prefixes_json`, `integration_workflow`, and
`resolution_prefix` (default `resolve/`).

Normal `/merge` requires a mergeable PR and uses GitHub's PR merge endpoint.
`/merge-resolved` is only for a conflicted exact permanent-ref direction. Its
owner comment must bind the reviewed base/head SHAs, a separate green
resolution PR, its exact resolution ref/commit SHA, and its exact tree SHA. The
tool then creates and verifies a two-parent Git merge object, rechecks all refs,
and advances the base without force before applying the same permanent-lane
lifecycle and integration dispatch.

Requires `contents: write`, `pull-requests: write`, `issues: write`,
`checks: read`, `statuses: read`, `actions: write`. Side effects include
merge/ref mutation, resolution-ref cleanup, PR comments/closure and optional
integration dispatch. Branch-role and reviewed-tree safety rules are defined in
requirements/design.

## API review gates

1. Confirm **requirements** independently of current files. A feature is not approved just because it was previously implemented.
2. For every retained public entry point, assign stable requirement identifiers and a design section. Record caller, inputs, defaults, output meaning, error/exit behavior, permissions, side effects, and release compatibility.
3. Ensure one authoritative API specification; workflow headers and folder README should link here, not duplicate evolving specifications.
4. Identify consumers **by checked source references** and exact release pins. Document migration for changed/deprecated interfaces.
5. Verify error cases and observable behavior in unit tests and external released-stack acceptance. Text-only assertions in acceptance are maintenance checks, not sufficient integration proof.
6. Audit bootstrap duplication, avoid extra runner boundaries, and keep CAD-CI execution decisions out of workflow YAML.

See [requirements](requirements.md), [design](design.md), [consumer guide](consumer.md), and [plan](plan.md). Current traceability is **incomplete** until audited requirements have stable IDs and every row maps to behavioral tests.

### Consumer environment boundary

`environment_json` is an object of **non-secret string values**, available
to domain commands only. It is not a general runner-configuration channel.
The helper rejects malformed names, non-string values and reserved names
or prefixes including `GITHUB_*`, `ACTIONS_*`, `RUNNER_*`,
`CAD_CI_*`, `PIP_*`, `LD_*`, `PATH`, `PYTHONPATH`,
`PYTHONHOME`, `HOME`, `DOCKER_CONFIG`, `GH_TOKEN` and
`GITHUB_TOKEN`. This protects runner bootstrap, library selection and
CAD-CI-owned evidence paths from caller environment overrides. Such values
must use the owning workflow/runtime integration instead.

## CLI API (observed command schema)

The installed Python console script is `cad-ci`; `python -m cad_ci_tool`
uses the same parser. Exit status `0` means the command completed; parser
errors and expected library/configuration failures use `2` with diagnostics
on stderr. Commands that return content print plain text unless `plan --json`
is requested.

| Command group | Subcommands | Required selector or input contract | Output |
| --- | --- | --- | --- |
| `plan` | — | `--repo` (default current directory), `--changed` **or** `--base` + `--head`, optional `--item`, `--json` | Tab-separated item/reason/path or JSON array |
| `run` | — | Same selection; mutually exclusive `--step` / `--from` / `--until`; `--jobs` positive integer (default 1) | Progress/errors and library evidence under `build/` |
| `build` | `prepare-main`, `prepare-named`, `prepare-pr`, `update-main`, `update-named`, `resolve`, `promote`, `install`, `fetch`, `remove-pr` | Path/scope/source inputs as shown by `cad-ci build <verb> --help`. Sparse mutations require explicit `--items`, `--changed` or `--base` + `--head`. | Materialized scope or selected commit/path |
| `pages` | `install-stable`, `install-named`, `install-preview`, `remove-preview` | Local `--site`, `--pages-root`, named/PR scope where relevant | Materialized page tree / path / removal outcome |
| `publish` | `build`, `build-cleanup`, `pages`, `pages-cleanup` | `--message`, optional remote/retries and source provenance; scope-specific candidate/site | Published generated-branch commit SHA |

The command table is **not** a substitute for parser-derived `--help`:
it identifies API groups and their common invariants. Each released option
(including defaults and mutually exclusive selectors) is defined in
`cad_ci_tool/cli.py` and `cad_ci_tool/publication_cli.py`. Options cannot
be dropped without a compatibility decision, release notes, and acceptance.

## Traceability matrix — current evidence

Requirement IDs are defined in [requirements](requirements.md#public-api-invariants-issue-110).
An evidence cell marked **GAP** is incomplete, not passed.

| Requirement | Design rationale | Implementation | Unit/contract evidence | Consumer or external acceptance | Status |
| --- | --- | --- | --- | --- | --- |
| API-001 | Release/ownership architecture | `pyproject.toml`, `VERSION`, `scripts/publish_release.py` | `tests/test_release.py`, `test_library_boundary.py` | Exact pinned release in `tool.cad.ci.test` | Existing release contract |
| API-002 | Planning/running architecture | `cad_ci_tool/cli.py` | `tests/test_run_cli.py` | Synthetic execution cases in `tool.cad.ci.test` | Existing |
| API-003 | Build/Pages/publication sections | `cad_ci_tool/publication_cli.py` | `tests/test_publication_cli.py` | External `publish_case` | Existing |
| API-004 | Reusable workflow consumer boundary and concurrency | `reusable-ci.yml`, `scripts/reusable_ci.py` | `tests/test_reusable_ci.py` | `tool.cad.ci.test` released workflow acceptance | Existing |
| API-005 | One-job PR run + optional in-job publication/cleanup | `reusable-pr.yml` | Parsed one-job/no-artifact assertions + candidate verification | Live publish/cleanup acceptance remains | In progress |
| API-006 | Advanced/internal workflow boundary | public advanced `reusable-plan.yml`; internal `reusable-run.yml` | schema/contract tests + candidate plan acceptance | Explicit support levels documented | Complete |
| GOV-001 | Shared merge-policy workflow / branch classifier | `scripts/merge_policy.py`, `reusable-merge-policy.yml` | `tests/test_merge_policy.py` | Forge `/merge` consumer, existing external source-contract check | Ownership review |
| GOV-002 | Stable-to-lane extension / cleanup boundary | `scripts/merge_policy.py`, `scripts/merge_command.py` | `tests/test_merge_policy.py`, `tests/test_merge_command.py` | **GAP:** real lane/ref lifecycle with new implementation | Draft fix |
| GOV-003 | Irreversible merge and post-merge reporting | `scripts/merge_command.py` | `tests/test_merge_command.py` mocked failures | **GAP:** live partial-failure recovery proof | Draft fix |
| GOV-004 | Command-run check isolation | `scripts/merge_command.py` | `tests/test_merge_command.py` fixtures | v0.27.1 live stable-to-lane evidence in `tool.cad.ci.test` PR #190 | Accepted |\n| GOV-005 | Reviewed permanent-ref conflict recovery | `scripts/merge_command.py`, `scripts/merge_resolution.py` | `tests/test_merge_command.py`, `tests/test_merge_resolution.py` | **GAP until released:** conflicted permanent sync/promotion in `tool.cad.ci.test` | Candidate |
| SEC-001 | Trusted tool bootstrap and permission boundary | `reusable-merge-policy.yml` | `tests/test_merge_policy.py` source assertions | **GAP:** permission / denial / race matrix in external tests | Incomplete |

### Release/compatibility decisions still required

- The external `merge_policy_case/check.py` in `tool.cad.ci.test` checks
  specific strings from the old inline Bash implementation. Those assertions
  must become observable contract tests before qualifying a release containing
  the new Python adapter. Its existing 0.20.1 acceptance is **not** proof of
  the proposed implementation.
- Existing Forge and CAD consumers must remain pinned to their **accepted**
  releases until a new exact release completes acceptance.
- The split `plan`/`run` workflows and optional merge-governance API are
  not deleted simply because their current design is under review.
