# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released baseline

- `tool.cad.ci v0.28.0` @
  `805304b6a950319aed7dc8a77e9c7b501bb3fb61`;
- released tool v0.28.0 still pins `lib.py.cad.ci 0.12.0` @
  `64656db8df528a5c0de799e62c0f028fd0133486`;
- reviewed permanent-ref conflict recovery is released and live-qualified in
  `tool.cad.ci.test` PR #200;
- the external test repository is back to only its permanent refs
  (`main`, `dev-cad`, `dev-ci`, `build`, `gh-pages`);
- root `action.yml` and root `cad-ci.py` are no longer current public
  entrypoints.

## Current work

### #137 — one config-driven durable-lane reusable workflow

**Now.** The existing `issue/137-durable-lane-workflow` branch and draft
PR #146 contain the one-runner `reusable-durable.yml` implementation. Do not
rebuild this work.

The candidate pins released `lib.py.cad.ci 0.13.0` @
`8f0516a484e3eac11758b498ca181d5e39ed1efe`, which owns the durable
integration/publication contract.

Current execution order:

1. reconcile the existing #137 branch with the accepted v0.28.0 main history;
2. keep one runner, one CAD-CI graph and library-owned durable state/publication;
3. pass the complete tool repository API/unit contract on PR #146;
4. release the resulting immutable tool revision;
5. qualify that exact release in `tool.cad.ci.test` issue #141;
6. only after black-box acceptance migrate CAD #288 and Forge #740.

Do not fold API naming cleanup from #145 into #137.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #137 Config-driven durable-lane workflow | **now** | Finish/review existing PR #146, release, then externally accept in `tool.cad.ci.test` #141. |
| #145 Simplify public workflow configuration names / remove needless `_json` suffixes | **later** | Audit all public workflow/template/script inputs generically after #137; preserve released compatibility. |
| #117 Align historical changelog | **later / docs-only** | No runtime impact. |

## Recently completed

- #124 reviewed permanent-ref conflict resolution: released in v0.28.0 and
  live-qualified through `tool.cad.ci.test` PR #200.
- conservative stale-branch cleanup and exact-SHA retirement are released and
  live-qualified; do not reopen them as part of #137.

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
