# Repository plan

Current work source of truth for `tool.cad.ci` (2026-11-22).
This repository owns the released CLI and GitHub Actions entry points above
`lib.py.cad.ci`. Generic SCons/build-store/Pages mechanics remain library-owned.

## Latest released baseline

- `tool.cad.ci 0.20.1` is tagged at
  `eb64a46b243db00e8dbb4b78b6643a2a7efa3fb9`.
- It pins `lib.py.cad.ci 0.11.0` at
  `e621daf6e309bdd0e3f643a12007f1b66490696d`.
- Draft PR #111 now pins released `lib.py.cad.ci 0.11.1` at
  `fa6bf244381dde609a0b04de673d774911c52fea`; that is candidate state, not
  part of the 0.20.1 release history.
- `tool.cad.ci.test` acceptance run
  `45033890474` succeeded for that released stack.
- Forge calls the 0.20.1 merge-governance workflow at its exact immutable SHA.
- The separate Forge/CAD composite-action pins may differ by consumer;
  do not silently repin them as part of tool fixes.

## Current goal: contract-first product repair

The first remediation is in **draft PR #111**, under issue #110.
It includes an API inventory, requirement IDs and traceability plus a
refactor of the privileged merge-workflow adapter. The PR is **not released**.

Order of work:

1. Stabilise merge-command API/error semantics and make unit/fixture CI green.
2. Check each merge safety requirement against the implementation (including
   SHA-pinned merge, check pagination, ref cleanup and irreversibility).
3. `lib.py.cad.ci 0.11.1` is released; pin that exact release and keep the
   durable-scope implementation out of this repository.
4. Workflow support levels are decided: stable public `reusable-ci`/`reusable-pr`, advanced public `reusable-plan`, internal `reusable-run`.
5. Obtain green tool CI and external acceptance against the exact released
   library + tool candidate before the tool release and consumer repins.

Avoid introducing extra GitHub jobs/runners or rebuilding a second generic
CI engine. Merge governance stays a separately identified interface pending
the product-ownership decision, not part of the CAD-CI execution engine.

## Repository-wide audit coverage

The original merge-policy finding initiated this audit, but **every source
surface is in scope**. A green unit test does not close a row that still needs
live GitHub acceptance.

| Surface | Findings / changes in draft PR #111 | Evidence / remaining gate |
| --- | --- | --- |
| CLI `cad_ci_tool/cli.py` | Remains thin above library; shared positive-integer parser | `test_run_cli.py`, CLI API matrix; released external cases |
| `cad_ci_tool/publication_cli.py` | No build-store algorithm duplicated; PR IDs/retries now validated as positive integers | `test_publication_cli.py`; external publish cases still on accepted release |
| `scripts/reusable_ci.py` | Exact source selection/pin bootstrap, single SCons graph and GitHub output adapter; durable state/publication moved to lib.py.cad.ci #87 | Boundary/unit tests; candidate external checks pending new library pin |
| `scripts/merge_policy.py` | Pure branch-role classifier, including stable/lane direction | `test_merge_policy.py`; candidate fake API checks |
| `scripts/merge_command.py` | API pagination, readiness, irreversible merge outcome, branch/dispatch reporting | `test_merge_command.py`; fake API candidate acceptance; **live merge/recovery GAP** |
| `scripts/publish_release.py` | TOML/changelog metadata validation and exact release SHA input | `test_release.py`; **live release gate GAP** |
| root `action.yml` | Pinned Actions; run-only credentials scrubbed; durable mode retained for trusted branch source | Unit + candidate run-only proof; released durable same-runner acceptance exists |
| `reusable-ci.yml` | Thin run-only entry point and caller-scoped cancellation retained | External candidate normal/no-output success |
| `reusable-run.yml` | Internal implementation behind public `reusable-ci`; shallow exact-source bootstrap | Covered through `reusable-ci`; direct consumer use unsupported |
| `reusable-plan.yml` | Public advanced plan-only API with exact source outputs | Unit/schema + external candidate plan output success; retained intentionally |
| `reusable-pr.yml` | **One job/runner**; optional same-runner PR publication/cleanup, no artifact handoff | One-runner structural and candidate verification tests; live publish/close acceptance still useful |
| `reusable-merge-policy.yml` | Privileged job wrapper only; exact checkout pin, timeout, serialized commands | Unit/schema + fake API; **live GitHub mutation GAP** |
| Repository-only `ci.yml` | Avoid editable install; exact pinned library checkout; release job runs only when VERSION changed on main | Tool CI; **live version-triggered release GAP** |
| Tests/documentation | API matrix, requirements IDs, tests and per-directory workflow/script docs | Review consistency and make acceptance evidence explicit |

`tool.cad.ci.test` [issue #86](https://github.com/brainboxemb/tool.cad.ci.test/issues/86)
and draft PR #87 run candidate-only checks with exact immutable SHAs.
Those checks do not repin `dependencies.repos` or rewrite the released
acceptance baseline.

Do not delete, rename or consolidate an existing public workflow until
its consumer use and versioned migration have been verified. A file with no
known consumer is not by itself evidence that it is obsolete.

## Open issue assessment

| Issue | Status | Next decision / dependency |
| --- | --- | --- |
| #110 Standalone product audit | **now** | Approve API inventory, requirements/design traceability, workflow retention and docs; PR #111. |
| #112 Post-merge recovery and outcome | **now** | Test irreversible merge boundary, distinct lifecycle/dispatch failures and retry/recovery policy; depends on merge adapter. |
| #113 Merge readiness/check gate | **now** | Validate complete API pagination, check identity, command-check exclusion and bounded mergeability polling with external fixtures. |

Cross-repository milestone: `meta.cad.solidcraft` #2. Detailed defects remain
in this repository. `tool.cad.ci.test` owns released-stack acceptance.

## Release checkpoint

`0.21.0` is the current candidate release. It follows the public API/library
boundary audit and is released only after the exact 0.11.1 + tool candidate
passes external acceptance. Never use
moving `main` or a draft branch as a production consumer pin.

Required sequence:
`green tool unit CI` → `reviewed API + behavior` → `main/release` →
`immutable exact tool pin in external acceptance` → `green acceptance` →
`Forge/CAD consumer repins and integration validation`.

## Recently completed

- #103 reusable merge-policy surface — tool 0.19.0.
- #106 stable-to-lane synchronization — tool 0.20.0.
- #108 isolate comment-triggered merge-command checks — tool 0.20.1.
