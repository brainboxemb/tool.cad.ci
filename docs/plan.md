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

## Current work

### #95 — reusable durable-lane orchestration

Status: **now — release-prepared after green feature validation**.

Consumer evidence: `lib.py.solidcraft.forge` currently duplicates generic
durable-lane orchestration in its workflow YAML even though this repository's
consumer contract says generic orchestration belongs in released reusable
surfaces.

The existing same-runner root composite action is the correct execution
boundary. #95 extends that action with an optional durable mode rather than
creating a chain of reusable workflow jobs.

Required same-runner sequence:

```text
checkout caller source once
  -> resolve previous durable scope/base
  -> bootstrap exact tool/library once
  -> run exactly one CAD-CI/SCons graph
  -> prepare/update complete durable scope in the same workspace
  -> publish durable build scope
  -> expose scope/base/build-commit/prepared-scope outputs
  -> return to later consumer-owned steps on the same runner
```

Performance constraint:

- no second runner;
- no build artifact handoff;
- no repeated tool/library bootstrap;
- no repeated checkout;
- no second CAD-CI graph;
- no duplicate selection/freshness engine.

The normal run-only mode of `action.yml` remains supported unchanged.
`reusable-ci.yml` remains the normal high-level reusable workflow for callers
that do not need later same-runner work.

Implementation order:

1. define durable action inputs/outputs and scope semantics in requirements;
2. define helper/action ownership and one-run sequence in design;
3. extend helper tests before changing consumer repositories;
4. implement durable mode in the existing root composite action;
5. prove main scope, existing named scope, initial named scope, stale/malformed
   durable evidence, exact source freshness and jobs forwarding;
6. release **tool.cad.ci 0.18.0** with the existing exact lib.py.cad.ci 0.10.0
   pin; feature-head validation is already green before the version bump;
7. prove the released action in `tool.cad.ci.test` on one same-runner consumer
   flow;
8. only then replace duplicated durable orchestration in Forge.

## Open issue assessment — 2026-11-22

| Issue | Status | Assessment |
| --- | --- | --- |
| #95 Expose reusable durable-lane orchestration for CAD-CI consumers | **now** | Extend the existing same-runner composite action; explicitly avoid multi-job/artifact decomposition. |

## Next trigger

After #95 is released and externally accepted, return this repository to
demand-driven mode.

Every new released tool/library pair or public action contract must pass
`tool.cad.ci.test` before consumer adoption.
