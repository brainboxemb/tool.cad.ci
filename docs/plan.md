# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- current released baseline: `tool.cad.ci v0.23.0`;
- candidate release: `tool.cad.ci v0.24.0`;
- both use `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- `tool.cad.ci.test` #93 / PR #94 proves the v0.23.0 stack through one normal
  `reusable-ci.yml` consumer path.

## Current work

### #128 — release workflow-only consumer surface as v0.24.0

1. bump the tool version to `0.24.0`;
2. publish the action-free consumer surface introduced by #126 / PR #127;
3. update copy-ready templates to `@v0.24.0` without changing template versions;
4. merge only after tool CI is green;
5. let the normal main release job publish `v0.24.0`;
6. externally qualify that exact release in `tool.cad.ci.test`;
7. only then migrate Forge and the CAD repository from their historical root
   action pins to the released workflow/config model.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #128 Release tool.cad.ci 0.24.0 | **now** | Merge after green CI, then external qualification. |
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

Do not introduce a second GitHub Actions execution path for repository-specific
post steps. If config cannot express a genuinely generic lifecycle requirement,
change the owning library/tool contract first.
