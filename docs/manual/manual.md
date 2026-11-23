# Consumer manual

This manual explains how a repository consumes `tool.cad.ci` and how to
select the copy-ready templates in `templates/`.

Do not start by designing a workflow from scratch. Choose the file that matches
the repository, copy it into `.github/workflows/`, and keep its header.

Current handoff baseline:

- tool release: **v0.34.1**

Each YAML template contains:

- `template` — stable template identity;
- `template-version` — version of the copied repository wrapper;
- `tool-release` — the exact released version tag the template calls.

The YAML files already contain the exact release tag. There is no version
placeholder to replace.

## Templates

| File | Template version | Use |
| --- | ---: | --- |
| `merge-policy.yml` | 4 | Owner-issued `/merge` policy for `main` + `dev-cad` + `dev-ci`. |
| `branch-cleanup.yml` | 2 | Owner-issued `/cleanup-branches` maintenance for stale temporary refs. |
| `branch-retirement.yml` | 2 | Owner-issued exact-SHA retirement for separately reviewed unique history. |
| `cad-ci-lanes.yml` | 4 | PR validation plus durable build/Pages integration for permanent `main` / `dev-cad` / `dev-ci` lanes, with explicit generated branch names. |
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
repository intentionally differs. Public branch-role configuration uses:

```yaml
stable_branch: main
development_branches: '["dev-cad","dev-ci"]'
permanent_branches: '["build","gh-pages"]'
```

The list values are JSON-encoded because GitHub Actions transports workflow
inputs as strings. JSON is not part of the public field names. For example, uncomment
`integration_workflow` only when a repository wants the merge workflow to
dispatch its integration workflow.

Do not copy merge implementation, GitHub API calls, check/status evaluation,
branch cleanup or merge-method logic into the consumer. Those stay in the
released reusable workflows.

For a conflicted permanent-development-branch promotion or synchronization, do **not**
create a temporary merge workaround. Create a short-lived `resolve/*` branch
whose tree is the reviewed resolved result, open a normal review PR from that
branch to the same permanent base, and let its normal validation finish green.
Then use the exact evidence from the conflicted PR and review PR:

```text
/merge-resolved
base <base-sha>
head <head-sha>
resolution-pr <review-pr-number>
resolution resolve/<name> <resolution-commit-sha> <resolution-tree-sha>
```

The shared tool refuses moved parents, a changed resolution ref/tree, a
non-green review PR, ordinary temporary PRs, or a conflicted PR that has become
normally mergeable. The resolution PR itself is never merged; its reviewed tree
is used to construct the exact two-parent permanent merge commit.

For maintenance cleanup, copy `branch-cleanup.yml` beside the merge wrapper. The command only deletes allow-listed temporary refs with positive integration or exact merged-PR-head SHA evidence; open PR heads, moved refs, unique history and `backup/*` refs are retained and reported.

When unique history has been separately reviewed and intentionally declared disposable, use `branch-retirement.yml` instead of weakening cleanup. The issue comment carries one exact `branch SHA` pair per line after `/retire-branches`; permanent refs and open-PR heads are refused, and each SHA is re-read immediately before deletion.

## New CAD-CI repository

A minimal root `cad-ci.yml`:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - models/*

builders:
  solidcraft-model: ci/builders/solidcraft-model
```

Each selected item owns a small declarative `ci.yml`:

```yaml
id: example-model
builder: solidcraft-model

watch:
  item:
    - model.py
    - model.yml
```

The shared implementation is separate:

```yaml
# ci/builders/solidcraft-model/builder.yml
schema: 1

steps:
  - id: build
    run: 'python "$CAD_CI_BUILDER_PATH/build.py"'
    outputs: [model.sc, model.step]

  - id: verify
    run: 'python "$CAD_CI_BUILDER_PATH/verify.py"'
    outputs: [verification.json]
```

The name `solidcraft-model` is repository configuration; generic CAD-CI does
not contain SolidCraft-specific behavior. A repository may instead name any
builder that fits its own domain.

Use `cad-ci-lanes.yml` when the repository follows the permanent-development-branch model.
The same wrapper has two released routes: pull requests call
`reusable-ci.yml`; `push` or `workflow_dispatch` on `main`, `dev-cad`
or `dev-ci` calls `reusable-durable.yml` with the exact branch SHA/name as
source and durable scope. Do not add local publication steps or a second
CAD-CI run.

The durable job also names its generated output branches explicitly:

```yaml
build_branch: build
pages_branch: gh-pages
```

Those are compatibility defaults. A repository that needs isolated output may
use other Git branch names, for example `test-output/build` and
`test-output/gh-pages`. This changes only the generated refs; stable/named
scope and Pages subtree semantics remain unchanged.

When Pages can be built completely inside the normal CAD-CI graph, keep the
existing item-output publication form:

```yaml
publication:
  pages:
    item: site
    output: site
```

When the final site must use the prepared complete durable scope and the exact
generated build commit, use the library-owned post-build renderer instead:

```yaml
builders:
  pages-site: ci/builders/pages-site

publication:
  pages:
    builder: pages-site
    output: site
```

That builder is still repository-owned executable behavior. It contains one
plain command step and runs once after durable build publication, outside the
SCons graph, with CAD-CI-owned complete-scope/source/build provenance
environment. The consumer workflow does not add a post-step or second CAD-CI
run.

When the merge-policy wrapper should explicitly dispatch post-merge integration,
set its optional `integration_workflow` to `cad-ci.yml`. The dispatched
branch then enters the same durable route.

Do not add a local PR-files query or docs-only/promotion classifier; that policy
is already part of the released reusable CI API. The optional
`pull_request_policy` input uses `stable_branch`,
`development_branches` and `docs_only_prefixes`. Optional non-secret
command values use `command_environment`; the JSON serialization remains an
input value format, not a field-name suffix.

## What the consumer may own

A consumer may own:

- event triggers;
- caller permissions;
- intentional stable/development/docs-prefix values;
- generated build/Page branch names when defaults need isolation;
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
