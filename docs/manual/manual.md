# Consumer manual

This manual explains how a repository consumes `tool.cad.ci` and how to
select the copy-ready templates in `templates/`.

Do not start by designing a workflow from scratch. Choose the file that matches
the repository, copy it into `.github/workflows/`, and keep its header.

Current handoff baseline:

- tool release: **v0.23.0**

Each YAML template contains:

- `template` — stable template identity;
- `template-version` — version of the copied repository wrapper;
- `tool-release` — the exact released version tag the template calls.

The YAML files already contain the exact release tag. There is no version
placeholder to replace.

## Templates

| File | Template version | Use |
| --- | ---: | --- |
| `merge-policy.yml` | 2 | Owner-issued `/merge` policy for `main` + `dev-cad` + `dev-ci`. |
| `cad-ci-lanes.yml` | 1 | PR validation for permanent `main` / `dev-cad` / `dev-ci` lanes. |
| `cad-ci.yml` | 1 | Normal read-only PR CAD-CI without lane policy. |
| `cad-ci-pr.yml` | 1 | Complete one-runner PR lifecycle with optional durable PR publication. |

## First handoff: merge policy

For the standard branch layout, copy:

```text
docs/manual/templates/merge-policy.yml
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
- repository secrets and domain runtime configuration.

A consumer must not copy:

- generic checkout/tool/library bootstrap;
- PR-file pagination or changed-path classification;
- CAD-CI/SCons execution;
- durable build-store algorithms;
- merge/check/status/ref-lifecycle implementation.

When generic behavior is missing, change and release the owning tool/library
instead of adding a local workaround.
