# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current accepted state

`tool.cad.ci 0.17.0` is released at exact commit
`d88d6e189c12edb5a30158c068145c099c17a019`.

It pins released `lib.py.cad.ci 0.9.3` at exact commit
`74486c441f1f2b170ff3dc06e0edcaf662fbec6b`.

External `tool.cad.ci.test` #66 / PR #67 passed the complete released-stack
suite.

Accepted public behavior includes:
- selective active-closure startup;
- `cad-ci run --jobs N`, default 1;
- reusable workflow/action jobs input;
- bounded SCons parallel execution through the library.

## Current work

### #91 — consume released lib.py.cad.ci 0.10.0

`lib.py.cad.ci 0.10.0` is released at exact commit
`397fb04005b46de8d433cb18c091b1e73714b877`.

That release adds the generic engine-owned dependency-output `copy:` step used
to remove repeated complete dependency-bundle materialization for projection-
only consumers.

This tool requires no new CLI or workflow behavior. #91 is therefore a thin
exact-pin patch release:

1. pin library commit `397fb040...` in `pyproject.toml`;
2. update the exact-pin boundary test;
3. keep the tool implementation/workflows/actions unchanged;
4. set tool version `0.17.1` in `VERSION`, `pyproject.toml` and changelog;
5. require the exact release-prepared PR head to pass this repository's tests;
6. squash-merge to main and require the normal release job to publish
   `v0.17.1`;
7. pin that exact released tool in `tool.cad.ci.test`;
8. prove dependency-copy behavior through the public released tool stack before
   Forge adopts it.

## Open issue assessment — 2026-11-22

| Issue | Status | Assessment |
| --- | --- | --- |
| #91 Consume released lib.py.cad.ci 0.10.0 dependency-output copy support | **now** | Exact released-library repin only; no generic implementation belongs here. |

## Next trigger

After #91 release and external acceptance, this repository returns to
demand-driven mode.

A future tool change is justified only by:
- a new released library capability that needs thin exposure;
- a public-surface defect;
- workflow/action integration behavior that is genuinely tool-owned.

Every release must be externally accepted in `tool.cad.ci.test` before
consumer adoption.
