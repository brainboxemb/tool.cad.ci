# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released baseline

- `tool.cad.ci v0.29.0` @
  `d134eeaa846261adfcf4bc1a296cdc29c05ca01e`;
- v0.29.0 pins `lib.py.cad.ci 0.13.0` @
  `8f0516a484e3eac11758b498ca181d5e39ed1efe`;
- the one-runner `reusable-durable.yml` and canonical
  `cad-ci-lanes` template v2 are released;
- `tool.cad.ci.test` #141 / PR #216 is green for the existing v0.29.0
  black-box suite, but the new durable publication lifecycle still needs live
  acceptance on isolated generated refs;
- `lib.py.cad.ci 0.14.0` is now released at
  `b24e9a3826dfc07e07b4f3fd9971fcb4ab5aa12d` and owns configurable durable
  generated build/Page branch selection.

## Current work

### #147 — configurable generated output branches in durable workflow

**Now.** Expose the released library behavior through the existing one-runner
`reusable-durable.yml` surface without adding publication logic to the tool.

Public compatibility defaults remain:

```text
build_branch = build
pages_branch = gh-pages
```

A consumer may select isolated refs such as:

```text
test-output/build
test-output/gh-pages
```

Execution order:

1. pin exact released `lib.py.cad.ci 0.14.0`;
2. document the public workflow inputs in requirements/API/design;
3. pass build/Page branch names through `scripts/reusable_ci.py` to the
   library-owned durable APIs;
4. update workflow/API/template contract tests;
5. bump canonical `cad-ci-lanes` template to version 3 and expose the two
   literal branch inputs;
6. prepare and release `tool.cad.ci v0.30.0`;
7. finish live acceptance in `tool.cad.ci.test` #141 on
   `test-output/build` and `test-output/gh-pages`.

Do not fold the separate public naming cleanup from #145 into this change.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #147 Configurable generated output branches in durable workflow | **now** | Implement against released library 0.14.0, release v0.30.0, then finish #141. |
| #145 Simplify public workflow configuration names / remove needless `_json` suffixes | **later** | Audit public naming generically after #147; preserve released compatibility. |
| #117 Align historical changelog | **later / docs-only** | No runtime impact. |

## Boundary

The supported consumer architecture remains config-first:

```text
consumer workflow
  -> released reusable workflow
       -> cad_ci_tool
            -> lib.py.cad.ci
                 -> root cad-ci.yml + declarative item ci.yml
                      -> repository builder.yml
                           -> SCons
```

Generated branch selection is a workflow/publication transport setting. It is
not added to repository `cad-ci.yml`, and the tool does not reimplement build
store, Pages, freshness or Git publication semantics.
