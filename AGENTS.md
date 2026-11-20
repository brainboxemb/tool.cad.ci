# Repository instructions

## Purpose

`tool.cad.ci` is the thin CLI above the released `lib.py.cad.ci` library.

Keep this repository narrow:
- command-line parsing;
- human/JSON output;
- exit-code handling;
- CLI documentation;
- release plumbing;
- reusable GitHub Actions workflows that expose the released CLI stack;
- CLI/workflow-specific tests.

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

Generic consumer setup belongs in reusable workflows in this repository. A
normal consumer should call the single high-level `reusable-ci.yml` workflow
at one exact tool.cad.ci commit SHA instead of copying
checkout/Python/tool-install/plan/run steps. Lower-level plan/run
workflows exist only for consumers that need domain preparation between them.

The reusable workflow revision is also the tool revision. Checkout the workflow
repository using `job.workflow_repository` and `job.workflow_sha`, then install
that source. Do not require a second consumer pin for the same generic stack.

Keep workflow YAML thin. It may own permissions, checkout, runner setup,
credentials and GitHub-required artifact transport.

Do not put changed-path rules, item loops, consumer commands, rebuild decisions
or execution timeout policy in workflow YAML. Consumer-specific runtime/image
or publication work stays in the consumer until it has its own generic contract.

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

## Repository plan

`docs/plan.md` is the current source of truth for unfinished repository work.

Keep it as a current snapshot, not as historical documentation:

- state the current goal and execution order;
- include every open issue in an issue assessment snapshot;
- give each open issue an explicit status such as `now`, `later`, `blocked`, `probably obsolete`, or `effectively complete but still open`;
- explain briefly why that status applies;
- identify dependencies or blockers between issues;
- remove completed work from the active execution sections after merge/release, while keeping the issue assessment current.

Issues contain detail and history. README and design/requirements documents describe stable purpose and behavior. The plan tells an agent what work is actually current and what should happen next.



## Repository documentation site

Do not add a repository-specific GitHub Pages site to `tool.cad.ci`.
README/docs are the repository documentation source.

This rule does not restrict the generic `cad-ci publish pages` product
feature.
