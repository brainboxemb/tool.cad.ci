# tool.cad.ci design

This document describes the stable boundary of `tool.cad.ci`.

## Purpose

`tool.cad.ci` is the thin command-line and reusable-workflow surface above one
exact released `lib.py.cad.ci` revision.

The tool owns:

- CLI argument parsing and exit handling;
- reusable GitHub Actions setup;
- installation of the exact called tool revision;
- GitHub artifact transport requested by a caller;
- release plumbing and tool-specific tests.

Generic CAD-CI configuration, SCons execution, evidence, build output and Pages
mechanics stay in `lib.py.cad.ci`.

## Library pin

`pyproject.toml` pins one exact library commit. A tool release therefore
identifies one exact tool/library stack.

A generic library feature is not reimplemented here. The tool is updated only
after the library feature is released and tested in its own repository.

## Command environment

The reusable workflow may receive optional non-secret `environment_json`
values from its caller. The workflow helper validates those values and places
them in the inherited process environment before invoking `cad-ci run`.

Root `cad-ci.yml:variables` are different: they are repository configuration
owned and parsed by `lib.py.cad.ci`, not by this tool.

The effective command precedence is therefore:

1. runner/caller environment, including validated `environment_json`;
2. repository variables from root `cad-ci.yml`, applied by the library;
3. CAD-CI-owned `CAD_CI_*` runtime values, applied by the library.

The tool must not add a second merge/parser for root variables.

## Reusable workflows

`reusable-ci.yml` is the normal entry point. Lower-level reusable plan/run
workflows exist for cases that need repository-specific preparation between
generic stages.

Workflow YAML remains orchestration-only. It does not own changed-item logic,
SCons decisions, item loops or consumer commands.

## Verification and release

A tool revision is released only after its own tests pass against the exact
library pin. The exact released tool revision is then tested from
`tool.cad.ci.test` before Forge or another CAD repository adopts it.


## GitHub Container Registry authentication

The reusable workflow owns runner-level GitHub credentials. Before invoking
`cad-ci run`, `reusable-run.yml` authenticates Docker to `ghcr.io` using:

- registry: `ghcr.io`;
- username: `${{ github.actor }}`;
- password: `${{ github.token }}`.

Both `reusable-ci.yml` and `reusable-run.yml` retain
`packages: read` together with `contents: read`. Reusable workflow
permissions may only stay equal or become narrower across the call chain, so
the high-level wrapper may not drop package-read permission before delegating.

The login is generic runner setup only:

- it contains no consumer image reference;
- it does not pull/build/publish any image itself;
- it does not export the token to consumer commands;
- it does not add registry semantics to `lib.py.cad.ci`.

A consumer that does not use GHCR still receives the same CAD-CI behavior; the
extra authenticated Docker registry entry is otherwise unused.
