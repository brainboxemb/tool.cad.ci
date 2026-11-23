# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released and accepted baseline

- `tool.cad.ci v0.32.0` @
  `19e894567ac534ce90428dc61c6afa126c1d3318`;
- v0.32.0 pins `lib.py.cad.ci 0.15.0` @
  `24c3abb267feea9ae91f24f8fdb435cba68f089a`;
- `tool.cad.ci.test` #232 externally accepted that exact stack through:
  - normal released-stack PR CI;
  - repository-owned root builders;
  - post-build `publication.pages.builder/output`;
  - named `dev-ci`, stable `main` and named `dev-cad` durable publication;
  - exact `CAD_CI_BUILD_COMMIT` context;
  - repository-variable precedence;
  - stable Pages root replacement with named-subtree preservation;
  - v0.32 permanent-branch merge governance;
- live acceptance output remains isolated on
  `test-output/build` / `test-output/gh-pages`;
- public workflow input names and generated-branch settings from v0.31 remain
  unchanged in v0.32.

## Current work

No open runtime/API work in this repository.

Forge #740 has exposed the next generic owner-layer requirement: reusable CAD
engine builders. That work belongs to `lib.py.cad.ci` #106. Do not add
build123d, CadQuery, SolidCraft or other engine execution logic to the tool
workflow layer.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #117 Align historical changelog | **later / docs-only** | Apply shared changelog presentation without runtime/API changes. |

## Boundary

`tool.cad.ci` remains the thin CLI/GitHub workflow adapter above the exact
released library. Builder schema, built-in CAD engine adapters, selection,
SCons execution, durable state and Pages rendering/publication remain
library-owned.

Do not add a consumer post-step phase, second CAD-CI graph or engine-specific
builder implementation to this repository.
