# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.24.0` @
  `18d374fad83e61b9a9b057931352ce4a2c8e2252`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- external acceptance passed in `tool.cad.ci.test` #102 / PR #104 through
  the single normal `reusable-ci.yml@v0.24.0` consumer path;
- root `action.yml` and root `cad-ci.py` are no longer current public
  entrypoints.

## Current work

There is no unfinished CAD-CI execution-surface cleanup in this repository.

Consumer migration is now owned by the consumers:

- Forge: `lib.py.solidcraft.forge` #740;
- CAD repository: `2026-011-02.cad.solidcraft` #288.

Both consumers remain functional on historical immutable releases until their
current permanent-lane work reaches a safe migration point.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #124 Define conflict-resolution contract for permanent-lane merge policy | **separate governance work** | Resolve independently of CAD-CI execution architecture. |
| #117 Align historical changelog | **later / docs-only** | No runtime impact. |

## Boundary

The supported consumer architecture is config-first:

```text
consumer workflow
  -> released reusable workflow
       -> cad_ci_tool
            -> lib.py.cad.ci
                 -> root cad-ci.yml + item ci.yml
                      -> SCons
```

Supported CLI entrypoints are the installed `cad-ci` command and
`python -m cad_ci_tool`. Do not introduce another root wrapper or GitHub
Actions execution route when the package/workflow entrypoints already cover the
requirement.
