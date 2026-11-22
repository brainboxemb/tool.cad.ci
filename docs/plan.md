# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.18.1` is released at exact commit
`e29d3127d5d3f9310f3cab4e27430a64a61c21cc`.

It pins released `lib.py.cad.ci 0.11.0` at exact commit
`e621daf6e309bdd0e3f643a12007f1b66490696d`.

External acceptance is complete:

- `tool.cad.ci.test` #77 / PR #78;
- acceptance run `45019713862` — success;
- the released root composite action passed durable same-runner execution;
- the immediately following step on that same runner verified the returned
  prepared scope and exact generated build commit;
- no artifact handoff or second post-action runner is required.

Issue #95 is complete and closed.

## Current work

Issue #103 — **now**: provide the reusable dev-lane merge/lifecycle policy as a
released GitHub Actions workflow surface.

Required order:

1. freeze the public workflow contract in requirements/design;
2. preserve current Forge acceptance semantics exactly;
3. implement the generic reusable workflow without Forge-specific names;
4. test merge-method, head/check verification, permanent-ref protection,
   temporary-branch cleanup and post-promotion lane preservation;
5. release a new tool.cad.ci version;
6. externally accept it in tool.cad.ci.test;
7. qualify released equivalence in Forge before removing Forge-local policy.

No lib.py.cad.ci change is expected: this is workflow orchestration, not generic
planning/execution semantics.

Issue #99 remains released and externally accepted; consumers may continue using
0.18.1 / 0.11.0 while #103 is developed.

## Open issue assessment — 2026-11-22

| Issue | Status | Current interpretation |
| --- | --- | --- |
| #103 reusable dev-lane merge policy workflow | **now** | Tool-owned reusable GitHub Actions surface; preserve Forge behavior, release, black-box accept, then migrate consumers. |

## Next trigger

Open a new issue only for:

- a new released library capability that needs thin public exposure;
- a genuine CLI/workflow/action surface defect;
- an exact released-library repin that requires a new tool release;
- measured consumer evidence that a reusable tool-owned orchestration surface
  is missing.

Every new released tool/library pair or public action contract must pass
`tool.cad.ci.test` before consumer adoption.
