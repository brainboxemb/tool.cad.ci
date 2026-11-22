# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current released state

`tool.cad.ci 0.17.1` is released at exact commit
`1012e6a539a2fddd8194124844fe208bf16cf4e4`.

It pins released `lib.py.cad.ci 0.10.0` at exact commit
`397fb04005b46de8d433cb18c091b1e73714b877`.

Release evidence:

- tool main test/release run `45006618862` — success;
- Git tag/GitHub Release `v0.17.1` resolve to the exact tool commit;
- library `v0.10.0` independently resolves to the exact pinned library commit.

The prior externally accepted consumer baseline remains tool 0.17.0 / lib
0.9.3 until the new exact released pair passes `tool.cad.ci.test`.

## Current work

### #91 — effectively complete, external acceptance pending

The thin tool implementation/release is complete.

No tool-owned generic behavior was added. The only product change is the exact
released library pin plus public-evidence schema compatibility in the tool's
consumer-facing test.

#91 remains open only until `tool.cad.ci.test` #70 / PR #71 proves:

- direct CLI consumption;
- reusable high-level workflow consumption;
- same-runner composite action consumption;
- the new dependency-output `copy:` case;
- the complete existing released-stack suite.

If external acceptance exposes a generic behavior defect, return to
`lib.py.cad.ci`; if it exposes a tool surface defect, reopen active work here.

## Open issue assessment — 2026-11-22

| Issue | Status | Assessment |
| --- | --- | --- |
| #91 Consume released lib.py.cad.ci 0.10.0 dependency-output copy support | **effectively complete but still open** | v0.17.1 is released; waiting only on exact released-stack black-box acceptance. |

## Next trigger

After external acceptance, close #91 and return this repository to
demand-driven mode.

A future tool change is justified only by:
- a new released library capability that needs thin exposure;
- a public-surface defect;
- workflow/action integration behavior that is genuinely tool-owned.

Consumers must not adopt moving tool main; they pin exact released revisions.
