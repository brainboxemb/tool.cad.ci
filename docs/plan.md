# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released and accepted baseline

- `tool.cad.ci v0.31.0` @
  `27bdf67077ddd485cea95ba199069249c20c2a46`;
- v0.31.0 pins `lib.py.cad.ci 0.14.0` @
  `b24e9a3826dfc07e07b4f3fd9971fcb4ab5aa12d`;
- `tool.cad.ci.test` #223 externally accepted normal CI, durable
  publication, permanent-branch governance, exact-SHA retirement and cleanup
  for that exact stack;
- public workflow names and generated-branch configuration from v0.31 remain
  the accepted contract.

## Current work

### #151 — release v0.32.0 with lib.py.cad.ci 0.15.0

**Now.** Consume exact released `lib.py.cad.ci 0.15.0` @
`24c3abb267feea9ae91f24f8fdb435cba68f089a`.

Library 0.15.0 adds the generic post-build Pages renderer discovered by Forge
#740. The existing `reusable-durable.yml` already delegates durable Pages
publication to the library, so no new workflow input, job, runner or tool-owned
publication logic is required.

Required order:

1. pin exact library commit `24c3abb267feea9ae91f24f8fdb435cba68f089a`;
2. declare tool `0.32.0` and update release documentation;
3. repin copy-ready templates to exact `v0.32.0` without changing their
   template versions because wrapper structure is unchanged;
4. pass the complete tool repository test/API contract;
5. merge and publish exact immutable `v0.32.0`;
6. black-box qualify that exact release in `tool.cad.ci.test`, including a
   real durable publication-builder scenario;
7. only after that acceptance resume Forge #740.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #151 Release v0.32.0 with lib.py.cad.ci 0.15.0 | **now** | Pin exact library, release tool, then external acceptance. |
| #117 Align historical changelog | **later / docs-only** | Apply shared changelog presentation without runtime/API changes. |

## Boundary

The post-build Pages renderer remains entirely library-owned. The tool exposes
it only by pinning the released library through the existing durable workflow.
Do not add a consumer post-step phase, second CAD-CI graph or Pages renderer to
this repository.
