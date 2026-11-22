# Repository instructions

## Purpose

`tool.cad.ci` provides the released CLI and GitHub Actions adapters above
`lib.py.cad.ci`. Its optional merge-governance workflow is a **separate,
explicitly documented GitHub API surface**, not part of CAD-CI execution.

Keep this repository narrow:
- command-line parsing;
- human/JSON output;
- exit-code handling;
- CLI documentation;
- release plumbing;
- reusable GitHub Actions workflows that expose the released CLI stack;
- CLI/workflow-specific tests;
- GitHub merge-governance policy adapter and its own tests, pending the
  explicit ownership decision in issue #110.

Do not implement generic CI behaviour here. Every public surface must map to
requirements, a documented API, design and observable acceptance evidence.
See `docs/api.md`. A new workflow or script is not justified only because a
consumer needs a temporary workaround.

## Library boundary

`lib.py.cad.ci` owns:
- configuration loading/validation, including builder resolution;
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

## Consumer templates

`docs/manual/` is the canonical consumer-manual location. Copy-ready workflow
files live only under `docs/manual/templates/`. Each template must have a stable
`template` id, integer `template-version` and exact released `tool-release` tag
in its header.

A consumer repository must start from these manual templates rather than
inventing generic CAD-CI orchestration. Templates may contain caller triggers,
permissions and repository-owned policy values, but never generic
checkout/bootstrap, changed-path classification, CAD-CI execution, durable
state/publication or merge API implementation.

When the copied workflow structure changes, increment that template's integer
version and update tests/manual in the same change. Keep the template files copy-ready: use an exact released version tag and no
version placeholder.

## Documentation layout

Keep the top level of `docs/` small and predictable. The normal core documents
are:

- `api.md`;
- `consumer.md`;
- `design.md`;
- `handoff.md`;
- `plan.md`;
- `requirements.md`.

`docs/manual/` contains user-facing consumer documentation.
`docs/manual/templates/` contains copy-ready workflow templates.
`docs/background/` contains specialist explanatory material that is useful to
retain but is not a core repository contract.

Do not add one-off Markdown files to the root of `docs/` when the content
belongs in the manual, background, API, design or requirements documents.

`docs/handoff.md` follows the shared structure from
`brainboxemb/meta.cad.solidcraft/templates/docs/handoff.md`. It is a durable
new-session entrypoint, not a second plan; current status stays in GitHub and
`docs/plan.md`.

## GitHub Actions

Generic consumer setup belongs in released reusable workflows. A normal
consumer calls the high-level `reusable-ci.yml` workflow at one exact
tool.cad.ci version tag instead of copying checkout/Python/tool-install/plan/run
steps. Lower-level plan/run workflows exist only for explicitly documented
advanced use.

Repository-specific build, verification, site or publication implementation
belongs in repository-owned builders referenced by root `cad-ci.yml` and
declarative item `ci.yml` where the generic library contract can express it. Do not add a second GitHub Actions execution
route merely to preserve a runner for consumer-owned post steps.

The reusable workflow revision is also the tool revision. Checkout the workflow
repository using `job.workflow_repository` and `job.workflow_sha`, then install
that source. Do not require a second consumer pin for the same generic stack.

Keep workflow YAML thin. It may own permissions, checkout, runner setup,
credentials and GitHub-required artifact transport.

Do not put changed-path rules, item loops, consumer commands, rebuild decisions
or execution timeout policy in consumer workflow YAML. Generic lane PR
classification belongs in the released reusable-ci preflight/helper, not in a
consumer. Consumer-specific runtime/image
or publication work stays in the consumer until it has its own generic contract.

## PR lifecycle architectural invariant

`reusable-pr.yml` performs verification, optional sparse publication and
closed-PR cleanup on **exactly one runner in one job**. This is an explicit
performance and public API constraint. Do **not** add a second publisher job,
artifact handoff, repeated checkout/Python setup, or second CAD-CI graph to
address a local issue. Tests and documentation must enforce this boundary.

Treat same-repository PR publication and durable composite publication as
trusted-source caller contracts. For strict read-only PR verification use
`reusable-ci.yml`. Do not create a second runner or artifact handoff to
"solve" this; keep the public topology stable.

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
