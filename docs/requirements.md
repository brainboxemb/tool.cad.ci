# Requirements

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

## Durable build output

- Runner output mirrors the item source path under the local `build/` candidate root.
- Durable `build/main` is a complete accepted baseline.
- Durable `build/pr/<number>` is a sparse overlay containing only selected rebuilt items.
- Resolving a PR view starts with `main` and replaces overlay item paths.
- Promotion replaces only overlay item paths and preserves unaffected main items.
- `build.json` records per-item source, input fingerprint and result fingerprint.
- Cleanup of one PR changes only that PR namespace.

## Pages

- `gh-pages` stable HTML lives at the branch root.
- PR previews live under `previews/pr-<number>/`.
- Updating stable Pages preserves all previews.
- Updating or removing one preview preserves stable output and other previews.
- Every built site contains `provenance.json`.
- The shared framework owns HTML structure/navigation, not consumer CSS or domain content.
- Project Pages and preview sites can provide different base paths.

## Generated-branch publication

- Generated branches are never force-pushed.
- A publisher starts from the latest remote generated-branch head.
- Publication can require a source ref to still match an expected source commit.
- Source freshness is checked before work and again before push.
- A rejected generated-branch push is retried from the newer head with a bounded retry count.
- Repeated publication/cleanup may be idempotent.

## Use in CI

- Local and GitHub Actions runs use the same `cad-ci` commands.
- GitHub Actions does not contain changed-path selection, item loops, or item-specific commands.
- Forge and CAD consume a pinned released revision of `tool.cad.ci` as external tooling.
