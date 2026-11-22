# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI/GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behavior remains library-owned.

## Current released and accepted state

`tool.cad.ci 0.20.0` is released at exact commit
`d45cdcef33cf1035311bab9a88c3f99208ef3b29`.

It pins released `lib.py.cad.ci 0.11.0` at exact commit
`e621daf6e309bdd0e3f643a12007f1b66490696d`.

External acceptance for 0.20.0 is complete:

- `tool.cad.ci.test` #82 / PR #83;
- acceptance run `45031453651` — success;
- accepted test-repository main commit
  `125e19b95c6cf4892f5d65aa6162cf71d4f89c57`.

Forge adopted 0.20.0 and proved:

- short-lived merge behavior remains functional;
- exact `main -> dev-cad` PR #721 can be made clean;
- full PR validation run `45032993674` is green.

## Current work

Issue #108 — **now**: remove the stable-to-lane merge-policy self-check
deadlock exposed by Forge #721.

When the stable branch itself is the PR head, the `issue_comment`
merge-policy workflow runs on that same commit. Released 0.20.0 currently
includes its own in-progress `merge / merge` check in the PR green gate and
refuses itself.

Required order:

1. keep the existing check/status gate and permanent merge classification;
2. query Actions runs for the exact PR head whose event is
   `issue_comment`;
3. exclude check-runs that belong to those command-run IDs before selecting the
   latest validation check per name;
4. require at least one remaining PR validation check;
5. keep failed/pending normal validation checks blocking;
6. release the fix as patch version 0.20.1 with the exact 0.11.0 library pin;
7. externally accept exact 0.20.1 in `tool.cad.ci.test`;
8. let Forge adopt that exact release and retry #721.

No `lib.py.cad.ci` change is expected.

## Open issue assessment — 2026-11-22

| Issue | Status | Current interpretation |
| --- | --- | --- |
| #108 ignore merge-command checks in stable-to-lane green gate | **now** | Patch the shared workflow, release 0.20.1, externally accept, then let Forge retry its real sync. |

## Next release checkpoint

Publish **0.20.1** only after #108 tests are green.

The release must retain exact `lib.py.cad.ci 0.11.0`. After publication,
`tool.cad.ci.test` must repin the exact immutable tool release and rerun the
complete black-box suite before any Forge consumer pin changes.

## Recently completed

- #106 stable-to-lane synchronization — released in tool.cad.ci 0.20.0 and
  externally accepted in run `45031453651`.
- #103 reusable dev-lane merge policy workflow — released as tool.cad.ci 0.19.0
  and accepted in run `45022699789`.
