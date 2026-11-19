# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current goal

Complete #49: make the released reusable CAD-CI workflow authenticate Docker
to GitHub Container Registry before consumer commands run.

This is generic GitHub workflow credential setup. The workflow does not know
which container image a consumer uses and does not move registry behavior into
`lib.py.cad.ci`.

## Execution order

1. Complete #49:
   - preserve `packages: read` through `reusable-ci.yml` and
     `reusable-run.yml`;
   - log Docker into `ghcr.io` with the workflow GitHub token before the CAD-CI
     command;
   - keep the token out of consumer environment/configuration;
   - test the workflow source contract.
2. Release the updated tool only after this repository CI is green.
3. Update `tool.cad.ci.test` to the exact released tool revision and prove a
   real consumer command sees authenticated GHCR Docker configuration.
4. Only after that black-box acceptance may Forge adopt the new tool revision
   and resume runtime-dependent verification.
5. Complete #46 separately; superseded-run cancellation remains independent
   reusable-workflow behavior.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #49 Authenticate GHCR in reusable CAD-CI workflow | now | Blocking Forge runtime consumption. Generic workflow credential setup belongs here, not in the CAD-CI library or consumer commands. |
| #46 Cancel superseded normal CAD-CI runs centrally | next | Independent reusable-workflow behavior; keep separate from registry authentication. |

## Boundary

`lib.py.cad.ci` remains unchanged. It owns CAD-CI planning/execution behavior,
not GitHub runner credentials.

The reusable workflow may authenticate the runner to GitHub-owned services with
the workflow token. It must not know consumer image names or expose credentials
to CAD-CI configuration.
