# GitHub Actions interfaces

Read the [public API inventory and review status](../../docs/api.md) **before selecting a workflow**. This directory mixes consumer interfaces with internal repository CI. A YAML filename alone does not establish a stable API.

| File | Role | Who should invoke it? |
| --- | --- | --- |
| `reusable-ci.yml` | High-level run-only CAD-CI workflow with concurrency | Normal run-only consumers |
| `reusable-pr.yml` | Complete PR verification, optional publication/cleanup on **one runner** | PR consumers requiring the complete lifecycle |
| `reusable-plan.yml` | **Public advanced** selection-only API; returns plan JSON and exact source/base commits | Callers that need planning without execution; not the normal run entry point |
| `reusable-run.yml` | **Internal** single-run implementation behind `reusable-ci.yml` | Do not call directly from consumers |
| `reusable-merge-policy.yml` | GitHub branch-governance service for owner-issued merges | Repository owners with an explicit branch policy; ownership under audit |
| `ci.yml` | Tests **this repository** | Internal; never a consumer entry point |

The root [`action.yml`](../../action.yml) is another **public** interface:
choose it when later consumer-owned work must stay on the same runner.
`reusable-pr.yml` also stays one job/runner, including publication and cleanup.
Do not introduce a second publish runner or artifact handoff. Durable action
publication is for trusted caller branch/source.

## Contract ownership

The [API document](../../docs/api.md) enumerates inputs, outputs, required permissions and side effects. [Requirements](../../docs/requirements.md) state intended behavior; [design](../../docs/design.md) must justify how it is delivered; [tests](../../tests/) and [external acceptance](https://github.com/brainboxemb/tool.cad.ci.test) must prove it. During issue #110's audit, **do not interpret historical workflow existence as approval to keep it**.

The executable helpers are in [`scripts/`](../../scripts/); generic CI mechanics belong in `lib.py.cad.ci`, not here. Consumers pin an immutable released tool commit. Use only interfaces marked public; `reusable-run.yml` is an implementation detail.
