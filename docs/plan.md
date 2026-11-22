# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.24.0` @
  `18d374fad83e61b9a9b057931352ce4a2c8e2252`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- external acceptance passed in `tool.cad.ci.test` #102 / PR #104 through
  the single normal `reusable-ci.yml@v0.24.0` consumer path;
- the root composite action is no longer part of the current released surface.

## Current work

### #130 — remove redundant root cad-ci.py launcher

The package already owns both normal CLI entrypoints:

- installed console command `cad-ci`;
- source/module invocation `python -m cad_ci_tool`.

Remove root `cad-ci.py` because it adds no behavior and has no identified
consumer.

### Consumer migration after v0.24.0 acceptance

- Forge migration: `lib.py.solidcraft.forge` #740;
- CAD repository migration: `2026-011-02.cad.solidcraft` #288.

Those consumers still pin historical releases containing the removed root
action, so they remain functional until their lane-safe migrations are
completed.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #130 Remove root cad-ci.py launcher | **now** | Remove redundant launcher and stale surface wording; merge after green CI. |
| #124 Define conflict-resolution contract for permanent-lane merge policy | **later / governance** | Separate from CAD-CI execution cleanup. |
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

Do not introduce another wrapper, root launcher or GitHub Actions execution
route when the package/workflow entrypoints already cover the requirement.
