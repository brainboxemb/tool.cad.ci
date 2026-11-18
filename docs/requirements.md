# v0.1 requirements

## Repository ownership

- The consumer repository lists CI item folders in `cad-ci.yml`.
- Each item folder owns its `ci.yml`.
- Item commands and domain rules stay in the consumer repository.
- `kind` is descriptive only. The runner does not hardcode library, integration, qualification, Forge, or CAD behaviour.

## Planning

- The runner can find items affected by changed files.
- An affected dependency also affects its dependants.
- A plan includes required dependencies before the selected item.
- The plan is printable without running commands.

## Running

- A complete item can run from first to last step.
- One step can run by itself when earlier state and dependency state are current.
- `--from` and `--until` select a step range.
- Missing or stale prerequisite state stops a partial run with a clear error.

## Reuse

- Successful output may be reused only when the item inputs, item config, dependencies, step config, and declared output files still match.
- A complete successful item writes reusable item state.
- A partial run does not pretend that the whole item was rebuilt.

## Output

- Generated output mirrors the source item path under `build/`.
- Step state is stored with that item output.

## Use in CI

- Local and GitHub Actions runs use the same `cad-ci` command.
- GitHub Actions does not contain changed-path selection, item loops, or item-specific commands.
- Forge and CAD consume a pinned released revision of `tool.cad.ci` as external tooling.
