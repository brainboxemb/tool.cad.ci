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

### #137 — one config-driven durable-lane reusable workflow

**Now. lib.py.cad.ci 0.13.0 is released at `8f0516a484e3eac11758b498ca181d5e39ed1efe`.**

Add one public `reusable-durable.yml` for permanent source branches. One job
and runner resolve the stored complete scope, run CAD-CI exactly once, publish
the build scope and, when root `cad-ci.yml` configures Pages, publish that
site through the same released library lifecycle.

Do not reintroduce root `action.yml`, consumer post-steps, artifact handoff or
tool-owned builder/publication semantics.

After release, qualify the exact stack in `tool.cad.ci.test` #141. Only then
migrate CAD #288 and Forge #740.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #137 Config-driven durable-lane workflow | **now** | Implement against released lib 0.13.0, release tool, then qualify in test #141. |
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
