# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.18.0` is released at exact commit
`b62f9d0b169aa201a3c66c3166f364396b2d71bc`.

It pins released `lib.py.cad.ci 0.10.0` at exact commit
`397fb04005b46de8d433cb18c091b1e73714b877`.

External acceptance is complete:

- `tool.cad.ci.test` #73 / PR #74;
- acceptance run `45010776155` — success;
- the released root composite action passed durable same-runner execution;
- the immediately following step on that same runner verified the returned
  prepared scope and exact generated build commit;
- no artifact handoff or second post-action runner is required.

Issue #95 is complete and closed.

## Current work

### #99 repin released lib.py.cad.ci 0.11.0

Status: **now**.

`lib.py.cad.ci 0.11.0` is released at exact commit
`e621daf6e309bdd0e3f643a12007f1b66490696d`.

This tool change is a thin repin/release only:

- pin that exact library commit;
- release `tool.cad.ci 0.18.1`;
- keep CLI/workflow/root-action behavior unchanged;
- correct the stale README library-pin text;
- after release, hand off to `tool.cad.ci.test` for black-box acceptance.

Generic active-dependent selection semantics remain wholly library-owned.

## Open issue assessment — 2026-11-22

| Issue | Status | Next action |
| --- | --- | --- |
| #99 lib.py.cad.ci 0.11.0 repin / tool 0.18.1 | **now** | Pin exact released library, test, release, then external acceptance in `tool.cad.ci.test`. |

## Next trigger

Open a new issue only for:

- a new released library capability that needs thin public exposure;
- a genuine CLI/workflow/action surface defect;
- an exact released-library repin that requires a new tool release;
- measured consumer evidence that a reusable tool-owned orchestration surface
  is missing.

Every new released tool/library pair or public action contract must pass
`tool.cad.ci.test` before consumer adoption.
