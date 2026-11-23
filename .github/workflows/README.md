# GitHub Actions interfaces

Read the [public API contract](../../docs/api.md) **before selecting a workflow**. For a new consumer, start from the [copy-ready repository manual](../../docs/manual/README.md) rather than writing a wrapper from scratch. This directory mixes consumer interfaces with internal repository CI; a YAML filename alone does not establish a stable API.

| File | Role | Who should invoke it? |
| --- | --- | --- |
| `reusable-ci.yml` | High-level run-only CAD-CI workflow with concurrency | Normal run-only consumers |
| `reusable-durable.yml` | One-runner permanent-branch run + durable build/optional configured Pages publication, with configurable generated refs | Permanent `main` / named development-branch consumers |
| `reusable-pr.yml` | Complete PR verification, optional publication/cleanup on **one runner** | PR consumers requiring the complete lifecycle |
| `reusable-release.yml` | Check stable main ci-build-record, then delegate tag/GitHub Release to released tool.py.lib.ci | CAD-CI consumers publishing a release |
| `reusable-plan.yml` | **Public advanced** selection-only API; returns plan JSON and exact source/base commits | Callers that need planning without execution; not the normal run entry point |
| `reusable-run.yml` | **Internal** single-run implementation behind `reusable-ci.yml` | Do not call directly from consumers |
| `reusable-merge-policy.yml` | GitHub branch-governance service for owner-issued merges | Repository owners with an explicit branch policy; ownership under audit |\n| `reusable-branch-cleanup.yml` | Conservative maintenance cleanup for stale temporary branches | Repository owners using the shared branch policy; ownership under audit |
| `reusable-branch-retirement.yml` | Separately reviewed exact-SHA retirement for intentionally disposable unique history | Repository owners; destructive governance surface |
| `ci.yml` | Tests **this repository** | Internal; never a consumer entry point |

## Contract ownership

The [API document](../../docs/api.md) enumerates inputs, outputs, required permissions and side effects. [Requirements](../../docs/requirements.md) state intended behavior; [design](../../docs/design.md) must justify how it is delivered; [tests](../../tests/) and [external acceptance](https://github.com/brainboxemb/tool.cad.ci.test) must prove it. During issue #110's audit, **do not interpret historical workflow existence as approval to keep it**.

The executable helpers are in [`scripts/`](../../scripts/); generic CI mechanics belong in `lib.py.cad.ci`, not here. Consumers call an exact released tool version tag. Use only interfaces marked public; `reusable-run.yml` is an implementation detail.


## Canonical consumer wrappers

The executable workflows in this directory are owned here; the files consumers
copy live under [`docs/manual/`](../../docs/manual/README.md).

| Public surface | Canonical wrapper |
| --- | --- |
| `reusable-ci.yml` | `docs/manual/templates/cad-ci.yml` or PR job in `cad-ci-lanes.yml` |
| `reusable-durable.yml` | Durable push job in `docs/manual/templates/cad-ci-lanes.yml` (updated with the release that ships this workflow) |
| `reusable-pr.yml` | `docs/manual/templates/cad-ci-pr.yml` |
| `reusable-release.yml` | `docs/manual/templates/cad-release.yml` |
| `reusable-merge-policy.yml` | `docs/manual/templates/merge-policy.yml` |\n| `reusable-branch-cleanup.yml` | `docs/manual/templates/branch-cleanup.yml` |
| `reusable-branch-retirement.yml` | `docs/manual/templates/branch-retirement.yml` |

Do not add consumer-specific wrapper examples here. Update the canonical
manual template, its integer template version when needed, release pin and tests together.
