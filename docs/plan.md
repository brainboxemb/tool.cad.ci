# Repository plan

This file is the current source of truth for unfinished work in `tool.cad.ci`.

The repository is the thin CLI and reusable GitHub Actions surface above
`lib.py.cad.ci`. Generic CAD-CI behaviour stays in the library.

## Current status

`tool.cad.ci 0.12.0` is released at commit
`05af21546ea71907cd9db4b56f5d5ccd644c0170`.

It pins released `lib.py.cad.ci 0.7.0`, exposes timing evidence through the
thin CLI and includes high-level superseded-run cancellation.

## Current goal

Complete #54: remove this repository's own GitHub Pages site and its build /
publication plumbing.

This does not remove or change the generic `cad-ci publish pages` command.

## Execution order

1. Remove repository-local site build/publication code.
2. Remove the docs publication job and site build from repository CI.
3. Remove the now-unused docs-only Python dependency.
4. Keep README/docs as the repository documentation source.
5. Keep generic Pages/publication CLI behavior and tests unchanged.
6. Merge after normal repository tests are green.
7. Do not create a new tool release solely for this housekeeping change.
8. Remove/disable stale GitHub Pages branch/settings separately if repository
   tooling permits it.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #54 Remove the repository's own GitHub Pages site | now | Repository housekeeping; removes redundant docs build/deploy overhead without changing the released CAD-CI Pages feature. |

No other open implementation issues exist in this repository snapshot.

## Boundary

The repository has Markdown documentation only. Generic Pages and generated-
branch publication remain library/tool product features and are still tested
externally.
