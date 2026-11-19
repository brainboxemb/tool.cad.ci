# Repository instructions

## Scope

`tool.cad.ci` is the CI planner and runner used by the SolidCraft Forge and CAD repositories.

Keep it narrow. Do not turn it into a general CI framework. Add behaviour only when Forge or CAD needs it.

The consumer repository owns:

- item folders;
- item commands;
- domain checks;
- qualification rules;
- expected files and other domain data.

`tool.cad.ci` owns:

- reading the consumer CI files;
- affected-item selection, including direct-only fan-in items;
- dependency ordering;
- run planning;
- step execution;
- saved step state;
- safe reuse of unchanged results.

Do not add Forge-specific step names or CAD-model rules to this repository.

## Language

Write like an engineer explaining the system to another engineer.

- Use short, direct sentences.
- Use normal engineering words.
- Prefer concrete names from the code and repository.
- Say what a component reads, checks, runs, writes, or returns.
- Explain cause and effect directly.
- Use established software terms when they help.
- Avoid academic, management, and architecture-heavy wording.
- Do not invent a term when a normal engineering term already exists.
- Do not make a simple mechanism sound more abstract than it is.

Prefer:

> The runner reads `ci.yml`, checks which inputs changed, and runs the affected items.

Do not write:

> The orchestration layer evaluates repository-local execution semantics to derive the applicable build topology.

Prefer names such as `changed_files`, `affected_items`, `build_plan`, `run_step`, and `previous_result`.

## Code comments and explanations

Code must be explained clearly enough that another engineer can understand the intent without reconstructing it from the implementation.

Every Python module should start with a short module docstring that says what the module owns.

Public and non-trivial helper functions should have a short docstring that explains:

- what the function does;
- what important input it expects;
- what it returns or changes when that is not obvious.

Add comments inside functions where they help explain:

- why a decision is made;
- why a safety check exists;
- why earlier output may or may not be reused;
- why dependencies are expanded;
- why a partial rerun refuses stale state;
- why generated branches are updated in a particular way;
- why an apparently simpler implementation is deliberately not used.

The goal is not to comment every assignment. The goal is that the important flow and rules are visible in the code.

Prefer:

> `# A changed dependency can change every item that consumes its output.`

> `# Do not rebuild earlier steps for --step. A stale prerequisite must fail visibly.`

Do not write comments that only repeat syntax:

> `# Loop over dependencies.`

When a core module has almost no explanatory text, treat that as incomplete documentation and fix it before merge.

## Git workflow

One logical change uses one branch and one pull request.

- Start from the intended target branch.
- Keep unrelated work out of the branch.
- Prepare a complete logical patch before pushing when practical.
- Do not create a commit for every edited file.
- Run focused local tests before pushing.
- When CI reports several related failures, collect them and make one follow-up fix.
- Merge only when the required tests are green.
- Do not develop consumers against moving `main` of this tool.
- Release the tool first, then pin that release or its exact commit in Forge/CAD.

If the repository uses numbered issues/change records, keep the same work item through branch, PR, tests, and release notes.

## Tests

Tests are part of the implementation, not a later cleanup step.

For runner behaviour:

1. add or update a focused unit test;
2. run the full tool test suite;
3. prove the behaviour in `exp.2026-014.cad-ci-consumer` when it affects consumer execution;
4. only then use it in Forge or CAD.

Do not use a real Forge or CAD workflow as the first test of runner behaviour.

## Consumer files

The root `cad-ci.yml` only lists CI item folders and root-level settings.

Each item folder owns its `ci.yml`. Keep item-specific commands and watch paths there.

Build output mirrors the item source path under `build/`. Do not flatten unrelated items into one output directory.

## GitHub Actions

Keep workflow YAML thin. It may own:

- triggers;
- permissions;
- checkout;
- runner setup;
- credentials;
- artifact upload/download.

Affected selection, dependency ordering, item loops, reuse decisions, and step execution belong in tested code in this repository.

Local and GitHub Actions execution must use the same `cad-ci` commands.

## Release

A release is made only after:

- the tool unit tests pass;
- the synthetic consumer passes end to end;
- the release version is fixed in `VERSION`, `pyproject.toml`, and `CHANGELOG.md`;
- the exact release commit is on `main`.

The `CI` workflow calls `scripts/publish_release.py` after the green `main` test job. Keep version checks and GitHub release policy in that script, not inline in workflow YAML.

Forge and CAD consume a pinned released revision as external tooling. They do not call a workflow from moving `main` in this repository.
