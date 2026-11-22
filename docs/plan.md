# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.19.0` is released at exact commit
`5677c41a61929b32ab2cb07087a6505f7b9347d8`.

It pins released `lib.py.cad.ci 0.11.0` at exact commit
`e621daf6e309bdd0e3f643a12007f1b66490696d`.

External acceptance for 0.19.0 is complete:

- `tool.cad.ci.test` #80 / PR #81;
- acceptance run `45022699789` — success;
- Forge #674 subsequently qualified and adopted the exact released merge-policy
  workflow for short-lived squash merges and direct lane-to-main promotions.

Current `main` includes the completed post-release plan reconciliation at
`9da97ea60f38468481c614dd1a39f952d23365f9`.

## Current work

Issue #106 — **now**: extend the released shared merge policy with a
history-preserving stable-to-lane synchronization path.

Consumer evidence is Forge #714/#717: exact `dev-cad -> main` promotion is
conflicted because stable `main` contains accepted commits that are not
ancestors of the lane. Released 0.19.0 currently squashes the required inverse
`main -> dev-cad` synchronization, which cannot establish that ancestry.

Required order:

1. freeze stable-to-lane semantics in requirements/design;
2. classify exact configured `stable -> lane` separately from
   `lane -> stable` promotion;
3. use a normal merge commit for both permanent-lane directions while keeping
   their lifecycle behavior distinct;
4. preserve all ordinary short-lived PRs as squash merges;
5. require same-repository source for permanent stable/lane operations;
6. test merge method, cleanup protection and integration dispatch;
7. release the completed tool change as the next tool version;
8. black-box accept that exact release in `tool.cad.ci.test`;
9. only then let Forge adopt it and synchronize `main -> dev-cad`.

No `lib.py.cad.ci` change is expected: this remains GitHub merge/lifecycle
workflow orchestration.

## Open issue assessment — 2026-11-22

| Issue | Status | Current interpretation |
| --- | --- | --- |
| #106 stable-to-lane synchronization | **now** | Generic tool-owned merge/lifecycle gap exposed by Forge #717; release and externally accept before consumer adoption. |

## Next release checkpoint

The next tool release must include #106 and retain the exact
`lib.py.cad.ci 0.11.0` pin unless an independent library requirement appears.

Do not let Forge consume moving tool `main`; consumer adoption waits for the
immutable tool release and `tool.cad.ci.test` acceptance.

## Recently completed

- #103 reusable dev-lane merge policy workflow — released as tool.cad.ci 0.19.0,
  external acceptance run `45022699789` green, and adopted/qualified by Forge
  #674.
