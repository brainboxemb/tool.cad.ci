# Set up a new CAD-CI consumer repository

This is the supported starting point for a new repository that consumes
`tool.cad.ci`. Do not design a new generic GitHub Actions flow in the
consumer. Start from the versioned templates shipped by this repository.

For detailed input/output semantics see [the public API contract](api.md).

## 1. Add repository configuration

Create root `cad-ci.yml`:

```yaml
schema: 1

defaults:
  timeout_seconds: 300

items:
  - models/*
```

Each item owns a `ci.yml`:

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

The exact configuration schema and execution semantics are library-owned and
exposed by the released tool stack.

## 2. Choose one consumer workflow template

Canonical templates live in
[`templates/github/workflows/`](../templates/github/workflows/).

Choose the smallest public surface that matches the repository:

- **normal run-only CI** → `cad-ci.yml`;
- **complete pull-request lifecycle** → `cad-ci-pr.yml`;
- **same-runner repository-owned post-processing** → `cad-ci-same-runner.yml`;
- **owner-issued merge governance** → additionally copy `merge-policy.yml`.

Do not combine templates merely for reuse aesthetics. In particular,
same-runner repository work uses the root composite action template rather
than splitting the job across reusable workflows.

## 3. Pin one immutable released tool revision

Every template contains:

```text
TOOL_CAD_CI_RELEASE_SHA
```

Replace that marker with the exact commit SHA of a released and externally
accepted `tool.cad.ci` version. Never consume moving `main`.

The tool revision itself pins the exact `lib.py.cad.ci` revision. A consumer
does not maintain a second library pin.

## 4. Keep only repository-owned configuration locally

The consumer may own:

- event triggers;
- the minimum caller permissions;
- lane names and integration workflow name for merge governance;
- repository/domain commands that run before or after the generic CAD-CI call;
- repository secrets and domain runtime configuration.

The consumer must not reimplement:

- generic checkout/tool/library bootstrap;
- PR file pagination or changed-path classification;
- CAD-CI item/SCons execution;
- durable scope state or publication algorithms;
- merge method/check/status/ref lifecycle logic.

If generic behavior is missing, open an issue in `tool.cad.ci` (or
`lib.py.cad.ci` when it is engine/state behavior) instead of adding a local
workaround.

## 5. Record template provenance

Keep the template header when copying:

```yaml
# template: tool.cad.ci/cad-ci
# template-version: 1
```

The id identifies the canonical source and the integer version records the
consumer structure. Repository-specific edits must remain below that contract
rather than silently turning the copied file into a new generic template.

The authoritative current versions are in
[`templates/manifest.json`](../templates/manifest.json).

## 6. Verify the repository

Before promoting a consumer change:

1. use an exact released tool SHA;
2. run the repository's existing contract/unit tests;
3. run the chosen workflow on a temporary PR or development lane;
4. for durable lanes, verify the generated build/Pages publication;
5. only then promote the consumer lane according to its normal branch policy.

The exact released tool/library stack is black-box accepted in
`tool.cad.ci.test` before real consumers repin to it.
