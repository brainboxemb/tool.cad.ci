# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci 0.23.0` @
  `bc0a7b716f67a20e63eaf8b89a2c35c381fb8bf1`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- 0.23.0 external acceptance is tracked in `tool.cad.ci.test` #92.

## Current work

### #123 — repository handoff manual

Make `docs/manual/` the single user-facing handoff location.

1. put the generic handoff guide in `docs/manual/README.md`;
2. put copy-ready workflow files directly beside it;
3. keep template id/version and exact released tool pin in every YAML header;
4. make `merge-policy.yml` template version 2 directly copyable;
5. remove the separate top-level `templates/` tree and
   `docs/new-repository.md`;
6. point README/API/workflow documentation and tests only at `docs/manual/`;
7. do not change reusable workflow behavior.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #123 Make docs/manual the single copy-ready consumer handoff | **now** | Finish manual cleanup and merge after CI. |
| #121 Complete canonical lane consumer templates | **released; acceptance pending** | 0.23.0 shipped; complete external test #92 before consumer migration. |
| #117 Align historical changelog with shared meta template and guidance | **later / docs-only** | No behavior impact. |

## Boundary

The manual is presentation/handoff only. Public API behavior remains in the
released workflows/action and their requirements/design/tests.
