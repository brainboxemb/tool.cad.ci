# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.25.0` @
  `92b9cbb59bf24f6b47ba1fae267f67f2becc503f`;
- `lib.py.cad.ci 0.12.0` @
  `64656db8df528a5c0de799e62c0f028fd0133486`;
- external released-stack acceptance passed in `tool.cad.ci.test` PR #135,
  final run `45063617081`, through the normal
  `reusable-ci.yml@v0.25.0` consumer path;
- the accepted fixture proves two declarative item `ci.yml` files can share
  one repository-owned builder and rebuild together when that builder changes;
- root `action.yml` and root `cad-ci.py` are no longer current public
  entrypoints.

Issue #134 is complete. Builder interpretation remains entirely library-owned;
the tool only pins and exposes the released library behavior.

## Current work

Consumer migration remains owned by the consumers:

- Forge: `lib.py.solidcraft.forge` #740;
- CAD repository: `2026-011-02.cad.solidcraft` #288.

Both consumers remain functional on historical immutable releases until their
current permanent-lane work reaches a safe migration point.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #140 Exact-SHA branch retirement | **now** | Release the separately reviewed retirement surface, then delete only the remaining manually audited unique refs in `tool.cad.ci.test` #180. |
| #138 Reusable conservative stale-branch cleanup | **complete** | Released in v0.26.0 and live-qualified in `tool.cad.ci.test` #180; keep the automatic policy conservative. |
| #124 Define conflict-resolution contract for permanent-lane merge policy | **separate governance work** | Resolve independently of CAD-CI execution architecture. |
| #117 Align historical changelog | **later / docs-only** | No runtime impact. |

## Boundary

The supported consumer architecture is config-first:

```text
consumer workflow
  -> released reusable workflow
       -> cad_ci_tool
            -> lib.py.cad.ci
                 -> root cad-ci.yml + declarative item ci.yml
                      -> repository builder.yml
                           -> SCons
```

Supported CLI entrypoints are the installed `cad-ci` command and
`python -m cad_ci_tool`. Do not introduce another root wrapper or GitHub
Actions execution route when the package/workflow entrypoints already cover the
requirement.
