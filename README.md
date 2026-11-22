# tool.cad.ci

`tool.cad.ci` is the **released consumer interface** to BrainboxEmb CAD CI:
a command-line tool, GitHub Actions reusable workflows and a same-runner
composite action. The reusable CAD-CI implementation lives in
`lib.py.cad.ci`; this repository does not implement another planner,
execution engine, cache, build store, Pages or Git publication mechanism.

It currently also exposes an optional **repository merge-governance workflow**.
That GitHub API capability is separate from CAD-CI execution and its long-term
product ownership is under review. Its presence does not authorise merge-policy
logic in the CAD-CI library.

**New repository setup:** [consumer onboarding](docs/new-repository.md).
**Versioned workflow templates:** [templates](templates/github/workflows/README.md).
**Public interfaces:** [API contract](docs/api.md).
**Workflow catalogue:** [workflows README](.github/workflows/README.md).
**Active work:** [repository plan](docs/plan.md).

The released 0.21.0 tool pins `lib.py.cad.ci` 0.11.1 at exact commit
`fa6bf244381dde609a0b04de673d774911c52fea`.

## Starting a consumer repository

Do not invent a generic GitHub Actions workflow in a consumer. Start from the
versioned templates shipped in [`templates/github/workflows/`](templates/github/workflows/README.md)
and follow [the new-repository guide](docs/new-repository.md).

Each copied template keeps a `template` id and integer `template-version`.
The consumer replaces only `TOOL_CAD_CI_RELEASE_SHA` with one immutable
released tool commit and changes documented repository-owned policy values.

## Consumer layout

```text
cad-ci.yml
shared/
cases/simple_case1/
  ci.yml
  build.py
  verify.py
```

Root `cad-ci.yml`:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

variables:
  BUILD_MODE: "verify"

items:
  - cases/*
```

Item `ci.yml`:

```yaml
id: simple-case

watch:
  - cases/simple_case1/**
  - shared/**

steps:
  - id: build
    inputs:
      - cases/simple_case1/build.py
      - cases/simple_case1/input/**
      - shared/**
    run: [python, build.py]
    outputs: [generated]

  - id: verify
    inputs:
      - cases/simple_case1/verify.py
    run: [python, verify.py]
    outputs: [verify.json]
```

`watch` is coarse Git-selection input. Step `inputs` are SCons build
dependencies. If a step omits `inputs`, it inherits the item `watch` paths.

Root `variables` are validated by the pinned library, injected into every
consumer command and included in SCons target signatures. Repository variables
override inherited caller values with the same name; CAD-CI-owned `CAD_CI_*`
values remain authoritative.

## Plan and run

```text
cad-ci plan --repo . --base <base-sha> --head <head-sha>
cad-ci run  --repo . --base <base-sha> --head <head-sha>

cad-ci run --repo . --item simple-case
cad-ci run --repo . --item simple-case --step verify
cad-ci run --repo . --item simple-case --until verify
cad-ci run --repo . --item simple-case --from build
```

`plan` explains which top-level items are selected and which dependencies they
have. It does not claim whether SCons considers a step dirty or current.

One `run` command makes one library `run_repository()` call. SCons owns
prerequisite traversal, incremental decisions and CacheDir reuse.

Partial selectors are mutually exclusive:
- `--step` forces that exact step after making prerequisites current;
- `--until` requests the named step normally;
- `--from` forces the named step and every following step.

Consumer output mirrors the item source path below `build/`. Public execution
evidence lives below `build/<item>/.cad-ci/`; private SCons state/cache stays
below `.cache/cad-ci/`.

## Reusable GitHub Actions

Consumers do not copy generic CAD-CI setup into their own workflows. Copy the
matching canonical consumer template, then pin the released reusable workflow
or root action at the exact tool commit.

For a complete normal PR run, the consumer keeps only its event trigger,
permissions and one reusable-workflow call:

```yaml
name: PR

on:
  pull_request:
    types: [opened, synchronize, reopened, closed]

permissions:
  contents: write
  packages: read

jobs:
  cad-ci:
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-pr.yml@<tool-commit>
```

`reusable-pr.yml` performs run, durable PR preparation/publication and closed-PR cleanup on one runner. It:
- checks out the caller repository at its real source commit;
- checks out `tool.cad.ci` at the same commit that contains the called workflow;
- resolves the tool's exact pinned library source and exposes both source trees through `PYTHONPATH` without building/installing either BrainboxEmb package;
- authenticates Docker to `ghcr.io` with the workflow GitHub token;
- performs exactly one `cad-ci run`;

Consumers such as Forge that need domain setup between selection and execution
can use the lower-level pair: first call `reusable-plan.yml`, prepare their
runtime image, then call `reusable-run.yml` with explicit source/base SHAs.
Normal consumers use `reusable-ci.yml` and do not reproduce generic
checkout/Python/tool-install/run setup locally. None of these workflows
contains Forge/SolidCraft/CAD-domain item names.

The optional `environment_json` input supplies non-secret caller values to
the inherited process environment. Stable repository expectations, such as a
runtime/version selected by that repository, belong in root
`cad-ci.yml:variables`. The pinned library applies those repository values
after caller environment. Secrets remain normal GitHub Actions
secrets/permissions. A caller that needs GHCR packages grants
`packages: read`; the reusable workflow uses that token permission for the
generic Docker login and does not expose the token to CAD-CI commands.

When consumer-owned work must happen **after** CAD-CI on the same hosted runner,
use the released root composite action instead of a reusable workflow:

```yaml
jobs:
  main:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: read
    steps:
      - uses: brainboxemb/tool.cad.ci@<tool-commit>
        with:
          source_sha: ${{ github.sha }}
          base_sha: ${{ github.event.before }}
          github_token: ${{ github.token }}

      - name: Consumer-owned post-run step
        run: python -m cad_ci_tool --help
```

The action checks out the caller source and exact pinned library source, exposes
the action/tool source plus library source through `PYTHONPATH`, installs only
external runtime dependencies, authenticates GHCR and performs exactly one
`cad-ci run`. The same `python -m cad_ci_tool` stack remains available to
later steps in that job. It does not contain consumer commands or publication
policy.

This surface is intended for consumers such as Forge where a domain-owned site
generator must run between generic build-store/publication commands. It avoids
artifact transport or a second runner merely to keep using CAD-CI after the
verification run.

When a downstream consumer job must publish or transform generated output, set
`upload_build: true`. The run workflow uploads the complete materialized
`build/` tree, including hidden `.cad-ci` evidence, and returns its name as
`build_artifact_name`. Private `.cache/cad-ci` SCons state is never part of
that artifact.

## Shared merge policy

The released reusable merge-policy workflow derives merge method from configured
permanent branch roles; callers do not choose a method manually.

- configured long-lived lane -> stable: normal merge, then preserve/advance the
  lane at the resulting stable merge commit;
- stable -> configured long-lived lane: normal history-preserving merge into the
  lane, with the stable source ref left unchanged;
- all other supported pull requests: squash merge;
- permanent/generated/backup refs are never cleanup targets; only explicitly
  allow-listed temporary heads may be deleted.

Both permanent-direction operations require the source head to belong to the
caller repository. The same exact-head/check/status gate is applied immediately
before every merge. Same-head GitHub Actions runs triggered by
`issue_comment` are command workflows, not PR validation, so their check-runs
are excluded from the validation set; at least one separate validation check
must remain green. Optional consumer integration dispatch runs for the updated
durable base; a promotion additionally dispatches the retained lane.

## Durable build output

Fetch the generated build branch:

```text
cad-ci build fetch --repo . --out generated-build
```

Prepare a complete main baseline:

```text
cad-ci build prepare-main \
  --repo . \
  --candidate-root build \
  --out output/main \
  --source-commit <sha>
```

Prepare a sparse PR overlay:

```text
cad-ci build prepare-pr \
  --repo . \
  --candidate-root build \
  --out output/pr \
  --source-commit <sha> \
  --pull-request 12 \
  --items simple-case
```

A PR overlay contains only the selected top-level items. Runtime prerequisites
that SCons made current are not automatically added to the sparse overlay.

Update selected main items with `cad-ci build update-main`. Resolve main plus
an optional PR overlay with `cad-ci build resolve`.

Generated branches are published with `cad-ci publish build` and
`cad-ci publish pages`. Publication uses normal pushes, checks source
freshness and retries only generated-branch races.

## Verification order

Generic execution behaviour is developed and tested in `lib.py.cad.ci`.
The CLI is tested here against one exact released library revision. The complete
released tool/library stack is then black-box tested in `tool.cad.ci.test`.

Only after that exact stack passes may Forge or CAD migrate to it.
