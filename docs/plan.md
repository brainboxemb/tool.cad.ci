# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci v0.23.0`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- `tool.cad.ci.test` #93 / PR #94 now proves the v0.23.0 stack through one
  normal `reusable-ci.yml` consumer path.

## Current work

### #126 — remove the root composite action

The root `action.yml` created a second public CAD-CI execution route beside
the reusable workflows. Remove it from future tool releases.

1. remove root `action.yml`;
2. remove action-only `durable-resolve` / `durable-publish` adapter commands;
3. remove action-specific tests and same-runner API/design/requirements text;
4. keep generic durable mechanics in `lib.py.cad.ci`;
5. keep `reusable-ci.yml` as the normal consumer workflow;
6. do not replace the action with another consumer wrapper or hook;
7. track Forge/CAD migration separately because their existing immutable older
   release pins continue to contain the historical action.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #126 Remove root composite action | **now** | Finish removal, tests and release boundary. |
| #124 Define conflict-resolution contract for permanent-lane merge policy | **later / governance** | Separate from CAD-CI execution cleanup. |
| #121 Complete canonical lane consumer templates | **effectively released** | v0.23.0 shipped and external workflow acceptance is green; reconcile/close separately. |
| #117 Align historical changelog | **later / docs-only** | No runtime impact. |

## Boundary

The target consumer architecture is config-first:

```text
consumer workflow
  -> released reusable workflow
       -> cad_ci_tool
            -> lib.py.cad.ci
                 -> root cad-ci.yml + item ci.yml
                      -> SCons
```

Do not introduce a second GitHub Actions execution path for repository-specific
post steps. If config cannot express a genuinely generic lifecycle requirement,
change the owning library/tool contract first.
