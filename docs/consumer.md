# Using tool.cad.ci from Forge or CAD

Forge and CAD consume a released `tool.cad.ci` revision as external tooling.

Do not call a reusable workflow from this repository. The consumer workflow checks out its own source and invokes the pinned tool against that checkout.

A consumer can record the tool beside its other external repositories, for example:

```yaml
repositories:
  cad-ci:
    type: git
    url: https://github.com/brainboxemb/tool.cad.ci.git
    version: <exact-release-commit>
```

After bootstrap, invoke the checkout directly:

```text
python ext/cad-ci/cad-ci.py plan --repo . --base <base-sha> --head <head-sha>
python ext/cad-ci/cad-ci.py run  --repo . --base <base-sha> --head <head-sha>
```

The workflow still owns GitHub-specific setup such as checkout, credentials and artifact transport. It does not own changed-path rules, item loops or item commands.

## Repository config

The root file only points to CI folders:

```yaml
schema: 1
items:
  - tests/unit
  - examples/*
  - qualification/*
```

Each discovered folder owns its behaviour:

```yaml
id: qualification-simple-box
kind: qualification
needs:
  - integration-simple-box
strategy:
  affected: changed
  reuse: true
steps:
  - id: build
    run: [python, build.py]
    outputs: [model.json]
  - id: verify
    run: [python, verify.py]
    outputs: [verified.json]
```

`kind` is only a label. The tool does not know what a library test, integration test or qualification means.
