# Repository handoff manual

This directory is the copy-ready handoff for a repository that consumes
`tool.cad.ci`.

Do not start by designing a workflow from scratch. Choose the file that matches
the repository, copy it into `.github/workflows/`, and keep its header.

Current handoff baseline:

- tool release: **0.23.0**
- exact tool commit: `bc0a7b716f67a20e63eaf8b89a2c35c381fb8bf1`

Each YAML template contains:

- `template` — stable template identity;
- `template-version` — version of the copied repository wrapper;
- `tool-release` and `tool-release-sha` — the exact released tool it calls.

The YAML files already contain the exact release SHA. There is no release
placeholder to replace.

## Templates

| File | Template version | Use |
| --- | ---: | --- |
| `merge-policy.yml` | 2 | Owner-issued `/merge` policy for `main` + `dev-cad` + `dev-ci`. |
| `cad-ci-lanes.yml` | 1 | PR validation for permanent `main` / `dev-cad` / `dev-ci` lanes. |
| `cad-ci.yml` | 1 | Normal read-only PR CAD-CI without lane policy. |
| `cad-ci-pr.yml` | 1 | Complete one-runner PR lifecycle with optional durable PR publication. |
| `cad-ci-same-runner.yml` | 1 | Trusted durable branch flow with repository work after CAD-CI on the same runner. |

## First handoff: merge policy

For the standard branch layout, copy:

```text
docs/manual/merge-policy.yml
  -> .github/workflows/merge-policy.yml
```

It works without edits for:

```text
main
dev-cad
dev-ci
build
gh-pages
```

Only change values explicitly marked `Repository policy` when the consumer
repository intentionally differs. For example, uncomment
`integration_workflow` only when a repository wants the merge workflow to
dispatch its integration workflow.

Do not copy merge implementation, GitHub API calls, check/status evaluation,
branch cleanup or merge-method logic into the consumer. Those stay in the
released reusable workflow.

## New CAD-CI repository

A minimal root `cad-ci.yml`:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - models/*
```

Each selected item owns a `ci.yml`, for example:

```yaml
id: example-model

watch:
  - models/example-model/**

steps:
  - id: build
    inputs:
      - models/example-model/build.py
    run: [python, build.py]
    outputs: [generated]

  - id: verify
    inputs:
      - models/example-model/verify.py
    run: [python, verify.py]
    outputs: [verify.json]
```

Use `cad-ci-lanes.yml` when the repository follows the permanent-lane model.
Do not add a local PR-files query or docs-only/promotion classifier; that policy
is already part of the released reusable CI API.

## What the consumer may own

A consumer may own:

- event triggers;
- caller permissions;
- intentional branch/lane/docs-prefix values;
- optional integration workflow name;
- repository/domain work before or after the generic CAD-CI call;
- repository secrets and domain runtime configuration.

A consumer must not copy:

- generic checkout/tool/library bootstrap;
- PR-file pagination or changed-path classification;
- CAD-CI/SCons execution;
- durable build-store algorithms;
- merge/check/status/ref-lifecycle implementation.

When generic behavior is missing, change and release the owning tool/library
instead of adding a local workaround.
