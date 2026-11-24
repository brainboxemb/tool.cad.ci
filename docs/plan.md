# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-24).

## Accepted owner baseline

- `lib.py.cad.ci v0.18.2` @
  `088644a05ff698957aef2ddc6cc5de037ddfa158`;
- `tool.cad.ci v0.36.1` @
  `8a9acb8ea69581728a3850c658b4c1ae2db6ff5a`;
- `tool.cad.ci.test #256` externally accepted the v0.36.1 central release
  flow, including stale-source refusal, exact-main release and idempotency;
- consumers remain pinned to accepted releases until a newer exact stack passes
  external acceptance.

## Current work

### #181 — sparse PR render review evidence

**Now.**

CAD model PRs can already build exact sparse native output inside
`reusable-pr.yml`, but the output disappears with the runner. That blocks
pre-merge visual acceptance of exact PR renders in consumers such as CAD #348,
#362 and #373.

Implementation direction:

1. keep the existing one-job / one-runner PR topology;
2. execute CAD-CI exactly once;
3. when materialized sparse `build/` output exists, write exact PR/head/base
   review provenance;
4. upload that existing sparse tree as one same-job
   `cad-review-evidence` artifact;
5. do not add a download step, second runner, second CAD graph or PR Pages
   publication;
6. document operator retrieval and enforce the topology in workflow tests;
7. patch-release as v0.36.2;
8. black-box accept the released artifact in `tool.cad.ci.test` before CAD
   consumers migrate.

This is GitHub Actions transport only. Item selection, build output semantics
and SCons execution remain owned by `lib.py.cad.ci`.

## Recently completed baseline work

- #176 central CAD release flow: released and externally accepted through
  v0.36.1.
- #178 reusable release runtime bootstrap: fixed in v0.36.1 and externally
  accepted by `tool.cad.ci.test #256`.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #181 sparse PR CAD review artifact | **now** | Finish same-job evidence upload, release v0.36.2, then externally prove sparse PNG/provenance contents. |
| #180 replace public `durable` terminology | **next naming slice** | Define owner-layer/public migration before renaming workflow/API surfaces. |
| #175 duplicate-looking permanent-merge runs | **later CI cleanup** | Determine which second-branch work is truly required and coordinate with #173. |
| #174 readable CAD-CI names | **later naming audit** | Audit public terms after the focused #180 branch-build rename decision. |
| #173 duplicate rebuild after permanent merge | **later / may need library primitive** | Prove one-build multi-scope publication ownership before changing merge topology. |
| #172 self-describing Actions runs | **later UX** | Add literal run names after public branch-build naming is settled. |
| #171 refresh promotion PR validation | **later** | Reproduce externally and design around GitHub token recursion without consumer hacks. |
| #170 permanent-lane conflict recovery | **later** | Prefer stable-into-development reconciliation while preserving exact-tree provenance. |
| #164 reduce tool to shared workflows/governance adapters | **later architecture** | Migrate only after released installed CAD-CI CLI ownership is ready. |
| #117 historical changelog alignment | **later / docs-only** | Normalize history separately; do not mix retrospective cleanup into functional releases. |

## Boundary

`tool.cad.ci` transports released CAD-CI behavior into GitHub Actions. It
does not own generic build-record semantics, affected-item selection, SCons
execution or build-store algorithms; those remain in `lib.py.cad.ci`.

GitHub-required same-job artifact upload is tool-owned transport. It may carry
already-produced sparse output, but must not reinterpret or rebuild that output.
