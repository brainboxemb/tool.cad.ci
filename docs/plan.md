# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-22).

## Released baseline

- `tool.cad.ci 0.22.0` @
  `76b5ba24084a09a69e6f25b34c16e869f7240a58`;
- `lib.py.cad.ci 0.11.1` @
  `fa6bf244381dde609a0b04de673d774911c52fea`;
- external 0.22.0 template acceptance completed in `tool.cad.ci.test`.

## Current work

### #121 — complete canonical permanent-lane consumers

Consumer migration exposed two owner gaps:

1. Forge/CAD still carry local docs-only/promotion PR classifiers.
2. merge-policy template v1 lacks the calling-job permission ceiling.

Execution order:

1. add optional lane PR policy to the existing `reusable-ci -> reusable-run`
   one-runner path;
2. add canonical `cad-ci-lanes` template version 1;
3. correct merge-policy wrapper and increment that template to version 2;
4. prove helper classification and no extra runner/bootstrap on docs-only skip;
5. release candidate `0.23.0` after repository CI;
6. externally accept the exact release in `tool.cad.ci.test`;
7. migrate Forge/CAD dev-ci wrappers and remove their local classifiers.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #121 Complete canonical lane consumer templates | **now** | Implement/test/release 0.23.0 then migrate consumers. |
| #117 Align historical changelog with shared meta template and guidance | **later / docs-only** | No behavior impact. |

## Boundary

No second classifier job or runner. No consumer GitHub PR pagination/path loop.
`reusable-pr.yml` remains one job/one runner and is unchanged by #121.
