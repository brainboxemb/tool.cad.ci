# Repository instructions

## Purpose

`tool.cad.ci` is the thin CLI above the released `lib.py.cad.ci` library.

Keep this repository narrow:
- command-line parsing;
- human/JSON output;
- exit-code handling;
- CLI documentation;
- release plumbing;
- CLI-specific tests.

Do not implement generic CI behaviour here.

## Library boundary

`lib.py.cad.ci` owns:
- configuration loading/validation;
- coarse affected-item selection;
- explanatory dependency planning;
- the SCons execution adapter;
- timeout/output handling;
- execution evidence;
- durable build scopes;
- Pages;
- generated-branch publication.

SCons is the only generic execution/rebuild/cache engine.

There must be no local `cad_ci/` package in this repository. The package comes
from the exact library commit pinned in `pyproject.toml`.

If a CLI change needs new generic behaviour, stop and implement/release it in
`lib.py.cad.ci` first.

## Run model

A `cad-ci run` command performs one library `run_repository()` call.

The tool does not:
- loop over items for execution;
- execute dependency plans itself;
- maintain step state;
- calculate rebuild fingerprints;
- decide whether output is reusable.

`cad-ci plan` is explanatory only. It may show selected items and dependency
closure/reasons, but it must not claim SCons dirty/current state.

`--step`, `--until` and `--from` are mutually exclusive and are forwarded
unchanged to the library.

## Publication model

Build-store commands pass current loaded `Item` objects to the library so
candidate `.cad-ci/item.json` evidence can be checked against current config.

Sparse PR scopes contain only the selected top-level items. Do not add runtime
SCons dependency closure to a PR overlay.

## Development process

One logical change uses one issue, one branch and one pull request.

For a library-dependent change:
1. finish and release `lib.py.cad.ci`;
2. pin the exact released library commit here;
3. update only CLI exposure;
4. pass this repository's tests;
5. release this tool after green main CI;
6. pin the exact tool release in `tool.cad.ci.test`;
7. pass black-box acceptance there;
8. only then migrate Forge or CAD.

Do not develop generic behaviour in this repository or in a real consumer.

## Tests

CLI tests should prove:
- exact library pin;
- one SCons repository run per CLI run;
- partial selectors reach the library correctly;
- publication passes current Item objects;
- sparse selection remains sparse;
- CLI errors become clear exit status.

The generic SCons acceptance matrix belongs in `lib.py.cad.ci`.
End-to-end released-stack acceptance belongs in `tool.cad.ci.test`.

## GitHub Actions

Keep workflow YAML thin. It may own triggers, permissions, checkout, runner
setup, credentials and GitHub-required artifact/cache transport.

Do not put changed-path rules, item loops, consumer commands, rebuild decisions
or execution timeout policy in workflow YAML.

## Language and comments

Use short, literal engineering language. Prefer names that say what the code
actually does. Avoid abstract CI terminology when a normal action name exists.

Python modules and non-obvious helpers need concise docstrings/comments that
explain intent and safety boundaries.

## Release

A release is made only after:
- CLI tests are green against the exact pinned library commit;
- version is fixed in `VERSION`, `pyproject.toml` and `CHANGELOG.md`;
- the exact release commit is on main and its test job is green.

Consumers pin a released tool revision. They never consume moving tool main.
