# Repository plan

Current source of truth for unfinished work in `tool.cad.ci` (2026-11-23).

## Released and accepted baseline

- `tool.cad.ci v0.30.0` @
  `5fcd77d5a07a68ef97cfcdb52b534f85bec1f1f2`;
- v0.30.0 pins `lib.py.cad.ci 0.14.0` @
  `b24e9a3826dfc07e07b4f3fd9971fcb4ab5aa12d`;
- configurable durable generated branches are released through
  `build_branch` / `pages_branch`;
- `tool.cad.ci.test` #141 is complete: v0.30.0 passed synthetic and live
  stable/named durable build + Pages acceptance on reserved
  `test-output/*` refs;
- permanent acceptance lanes were synchronized after the completed v0.30
  baseline update.

## Current work

### #145 — simplify public workflow configuration names

**Now.** Remove serialization details and internal lane terminology from the
consumer-facing reusable-workflow API while keeping JSON parsing internal.

Target public names:

```text
stable_branch
development_branches
permanent_branches
temporary_branch_prefixes
pull_request_policy
command_environment
```

Internal workflow helper/script flags may keep explicit JSON transport names
such as `--lane-refs-json` and `--environment-json`.

`plan_json` remains unchanged because JSON is the public output format there,
not merely an implementation transport.

Compatibility policy:

- released tags remain immutable; v0.30.0 callers keep their existing inputs;
- v0.31.0 exposes the clean names without old-name aliases;
- consumers upgrade by taking the corresponding new canonical template
  versions;
- runtime/merge/cleanup semantics must not change.

Execution order:

1. define the public naming contract in requirements/design/API;
2. rename reusable-workflow inputs only, leaving internal parsers explicit;
3. update every affected canonical template and increment its template version;
4. update workflow/template/unit contract tests;
5. release exact `tool.cad.ci v0.31.0`;
6. adopt and qualify v0.31.0 in `tool.cad.ci.test` before Forge/CAD migration.

## Open issue assessment

| Issue | Status | Next |
| --- | --- | --- |
| #145 Simplify public workflow configuration names | **now** | Implement clean workflow names, release v0.31.0, then external acceptance. |
| #117 Align historical changelog | **later / docs-only** | Apply shared changelog presentation without runtime/API changes. |

## Boundary

The rename is limited to public workflow configuration. Generic merge/cleanup,
CAD-CI execution, publication and JSON parsing behavior remain in their current
owners.

Do not add compatibility aliases that permanently duplicate the public workflow
surface. Exact released tags already provide backward compatibility.
