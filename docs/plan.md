# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci 0.23.0` @
  `bc0a7b716f67a20e63eaf8b89a2c35c381fb8bf1`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- 0.23.0 external acceptance is tracked in `tool.cad.ci.test` #92.

## Current work

### #123 — repository documentation and consumer handoff

Keep the documentation structure predictable and make the consumer handoff
copy-ready without changing workflow behavior.

1. keep only the normal core documents at the top level of `docs/`:
   `api.md`, `consumer.md`, `design.md`, `handoff.md`, `plan.md` and
   `requirements.md`;
2. derive `docs/handoff.md` from the shared
   `meta.cad.solidcraft/templates/docs/handoff.md` structure;
3. keep consumer documentation under `docs/manual/`, with `README.md` as the
   short index and `manual.md` as the actual manual;
4. keep copy-ready, versioned YAML only under `docs/manual/templates/`;
5. move specialist explanatory documents to `docs/background/` rather than
   leaving one-off files in the root of `docs/`;
6. remove the superseded top-level `templates/` presentation and stale
   onboarding references;
7. update documentation links and template contract tests to enforce the layout;
8. do not change reusable workflow, CLI or runtime behavior.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #123 Organize docs/manual as consumer manual with versioned template subdirectory | **now** | Finish documentation cleanup and merge after CI. |
| #121 Complete canonical lane consumer templates | **released; acceptance pending** | 0.23.0 shipped; complete external test #92 before consumer migration. |
| #117 Align historical changelog with shared meta template and guidance | **later / docs-only** | No behavior impact. |

## Boundary

The manual, handoff and background organization are documentation/presentation
work. Public API behavior remains in the released workflows/action and their
requirements/design/tests.
