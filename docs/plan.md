# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.27.0` @
  `bf9b2dff915e257a1229b156fdd024b062293218`;
- `lib.py.cad.ci 0.12.0` @
  `64656db8df528a5c0de799e62c0f028fd0133486`;
- v0.27.0 branch cleanup and exact-SHA retirement are live-qualified in
  `tool.cad.ci.test`;
- root `action.yml` and root `cad-ci.py` are no longer current public
  entrypoints.

## Current work

### #142 — current merge-command self-check race

`tool.cad.ci.test` PR #190 reproduced a stable-to-lane `/merge` refusal
because the current command check became visible before the Actions-runs API
indexed the matching `issue_comment` run. The v0.27.1 candidate passes
`github.run_id` explicitly into the merge command so the active command run
is excluded without relying on eventual API indexing.

After release, re-run PR #190 through the normal owner `/merge` path before
resuming consumer work.

Consumer migration remains owned by the consumers:

- Forge: `lib.py.solidcraft.forge` #740;
- CAD repository: `2026-011-02.cad.solidcraft` #288.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #142 Exclude current merge command from check validation | **now** | Release v0.27.1 and re-run `tool.cad.ci.test` PR #190 through `/merge`. |
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
