# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.27.1` @
  `716d22ce79551155b68413bd50fe3bf9d15d2254`;
- `lib.py.cad.ci 0.12.0` @
  `64656db8df528a5c0de799e62c0f028fd0133486`;
- v0.27.1 fixed and live-qualified the merge-command self-check race on
  `tool.cad.ci.test` PR #190;
- v0.27.0 branch cleanup and exact-SHA retirement remain live-qualified;
- root `action.yml` and root `cad-ci.py` are no longer current public
  entrypoints.

## Current work

### #124 — reviewed conflict resolution for permanent lanes

A second real consumer conflict is now reproduced by
`tool.cad.ci.test` PR #200 (`main -> dev-cad`). The v0.28.0 candidate adds
an owner-reviewed `/merge-resolved` path that preserves exact permanent
parents, uses a separate green resolution PR as the reviewed tree carrier and
advances the permanent base without force.

Release only after unit/API contracts are green. Then adopt the immutable
release in `tool.cad.ci.test` and use PR #200 as the live black-box
qualification before continuing the `dev-cad -> main` promotion proof.

Consumer migration remains owned by the consumers:

- Forge: `lib.py.solidcraft.forge` #740;
- CAD repository: `2026-011-02.cad.solidcraft` #288.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #124 Define conflict-resolution contract for permanent-lane merge policy | **now** | Release v0.28.0 and live-qualify reviewed conflict recovery on `tool.cad.ci.test` PR #200. |
| #138 Reusable conservative stale-branch cleanup | **complete** | Released in v0.26.0 and live-qualified in `tool.cad.ci.test` #180; keep the automatic policy conservative. |
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
