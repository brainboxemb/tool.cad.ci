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

Accepted public behavior now includes:
- selective active-closure startup from lib 0.9.3;
- `cad-ci run --jobs N`, default 1;
- reusable run/high-level CI/PR jobs input;
- same-runner action jobs input;
- positive-integer validation;
- actual jobs=2 concurrent SCons action overlap proven through public evidence.

## Current work

No tool implementation is active.

Default jobs remains 1. Consumers may deliberately opt into a bounded jobs value
after measuring their own workload. The tool does not choose a consumer-wide
parallelism policy.

New tool work must start from a fresh issue and must remain a thin surface over
released library behavior. Generic selection/scheduling/cache/runtime logic does
not move into this repository.

## Next trigger

A future tool change is justified only by:
- a new released library capability that needs thin exposure;
- a public-surface defect;
- workflow/action integration behavior that is genuinely tool-owned.

Every release must be externally accepted in `tool.cad.ci.test` before
consumer adoption.
