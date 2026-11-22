# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.17.1` is released at exact commit
`1012e6a539a2fddd8194124844fe208bf16cf4e4`.

It pins released `lib.py.cad.ci 0.10.0` at exact commit
`397fb04005b46de8d433cb18c091b1e73714b877`.

External acceptance is complete:

- `tool.cad.ci.test` #70 / PR #71;
- complete run `45006989548` — success;
- direct CLI, reusable workflow and same-runner action passed;
- dependency-output `copy:` passed through the released public stack.

Issue #91 is complete and closed.

## Current work

No tool implementation is active.

The tool remains a thin exposure/pinning layer. Do not duplicate library-owned
SCons, bundle, projection, scheduling, caching or evidence behavior here.

## Next trigger

Open a new issue only for:

- a new released library capability that needs thin public exposure;
- a genuine CLI/workflow/action surface defect;
- an exact released-library repin that requires a new tool release.

Every new released tool/library pair must pass `tool.cad.ci.test` before
consumer adoption.
