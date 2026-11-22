# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

This repository owns the released CLI and GitHub Actions adapters above
`lib.py.cad.ci`. Generic planning/execution, durable build-store state, Pages
and generated-branch publication semantics are library-owned.

## Released and accepted baseline

- `tool.cad.ci 0.21.0` @
  `b1474f6be66dc0236f2a5c2555af07a100447255`.
- Exact `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`.
- Main CI/release run `45045119748` succeeded.
- External released-stack acceptance run `45045346481` succeeded.
- Permanent `tool.cad.ci.test` baseline is main @
  `8218effedfc25c70b76d4237c15d1ff7aa47b709`.

The standalone API audit (#110) is complete. Merge-policy findings #112/#113
are closed. The unnecessary #114–#116 side tracks are closed.

## Public surfaces

- stable public: CLI, root `action.yml`, `reusable-ci.yml`,
  `reusable-pr.yml`;
- advanced public: `reusable-plan.yml`;
- internal implementation: `reusable-run.yml`;
- optional separate repository-governance API:
  `reusable-merge-policy.yml`;
- repository-local only: `ci.yml` and helper scripts unless explicitly
  documented otherwise.

`reusable-pr.yml` remains one job / one runner, including optional publication
and cleanup. Do not add a second publication runner or artifact handoff.

## Current work

No CAD-CI product implementation is active. Cross-repository consumer adoption
of 0.21.0 is tracked in `meta.cad.solidcraft` #2.

Do not repin consumers to moving main; use the exact released SHA above.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #117 Align historical changelog with shared meta template and guidance | **later / docs-only** | Apply shared changelog presentation without changing release history or product behavior. |

## Recently completed

- #110 standalone product/API audit — tool 0.21.0;
- #112 post-merge lifecycle/outcome — observable/manual recovery contract in 0.21.0;
- #113 merge readiness/check evaluation — fixed in 0.21.0;
- lib.py.cad.ci #87 durable complete-scope ownership correction — library 0.11.1.
