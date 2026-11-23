# Merge-governance API and recovery contract

Status: current merge-governance API. Normal merge behavior is released; reviewed conflicted permanent-ref recovery is defined by issue #124. This API is separate from CAD-CI selection and execution.

## Caller contract

A caller exposes owner-only `/merge` and `/merge-resolved` comment triggers and invokes `reusable-merge-policy.yml` at an **immutable released SHA**. Inputs are documented in [API inventory](../api.md). The workflow runs `scripts/merge_command.py` from that same immutable tool revision; it never executes PR-head code.

Example consumer wrapper (replace the placeholder with an **immutable released**
40-character tool commit, never `main`):

```yaml
name: Merge policy
on:
  issue_comment:
    types: [created]

permissions:
  contents: read

jobs:
  merge:
    if: >-
      github.event.issue.pull_request &&
      (github.event.comment.body == '/merge' ||
       startsWith(github.event.comment.body, '/merge-resolved')) &&
      github.actor == github.repository_owner
    permissions:
      contents: write
      pull-requests: write
      issues: write
      checks: read
      statuses: read
      actions: write
    uses: brainboxemb/tool.cad.ci/.github/workflows/reusable-merge-policy.yml@<tool-release-sha>
    with:
      command: ${{ github.event.comment.body }}
      pull_request_number: ${{ github.event.issue.number }}
      stable_ref: main
      lane_refs_json: '["dev-cad","dev-ci"]'
      permanent_refs_json: '["build","gh-pages"]'
      integration_workflow: ci.yml
```

This API intentionally has **no workflow outputs**: it is an owner-command
operation, not a success-path data pipeline. Its observable result is a PR
comment, job conclusion and logs. A successful GitHub merge followed by a
failed lifecycle/dispatch keeps a **failed job**, with the successful merge SHA
shown explicitly so the operator cannot assume no merge happened.

The current policy permits only `github.actor == github.repository_owner`. This is **not** organization-maintainer support. Changing authorization requires an explicit decision and external acceptance (#114).

| Base / head | Merge method | Lifecycle | Integration |
| --- | --- | --- | --- |
| stable <- configured lane | normal merge | advance/recreate lane to stable merge SHA | stable and lane |
| configured lane <- stable | normal merge | lane is updated by GitHub PR merge; stable untouched | updated lane |
| configured lane <- temporary | squash | cleanup eligible allow-listed temporary head | updated lane |
| stable <- temporary | squash | cleanup eligible allow-listed temporary head | stable |
| lane <- different lane | squash | permanent head never deleted | updated lane |

A temporary head is eligible for deletion only if it matches the configured prefix allow-list, is not a permanent/generated ref, is not a backup ref, and originates in the caller repository. GitHub performs a SHA-pinned merge so a moved PR head is rejected.

## Readiness and check contract

The command rejects drafts, closed PRs, non-green checks or commit statuses. GitHub's asynchronous `mergeable: null` is polled with bounded exponential delay before refusal. The check-runs and issue-comment command-run APIs must be fetched completely; an incomplete response fails closed. Immediately before the PUT merge, the command fetches the PR again and rejects a changed base/head commit or branch role. The PUT itself is pinned to the checked head SHA. This reduces but cannot eliminate races with external branch updates. Checks are grouped by (GitHub App ID, name), using the latest check of each identity.

All `issue_comment` workflow runs for the checked head are excluded from the validation check set. This preserves #108's avoidance of self-check deadlock, including older command attempts. **At least one separate validation check must remain**. A pending/failed normal validation check always blocks the merge.

## Conflicted permanent-ref recovery

Normal `/merge` still refuses an unmergeable PR. For an exact permanent
`lane -> stable` or `stable -> lane` PR with a genuine conflict, the owner
may prepare a separate resolution branch using the reserved `resolve/`
prefix and open a **review-only** PR from that branch to the same base.

That resolution PR must be normally mergeable and green. It is never merged.
After reviewing its exact commit and Git tree, the owner comments on the
original conflicted PR:

```text
/merge-resolved
base <reviewed-base-sha>
head <reviewed-head-sha>
resolution-pr <review-pr-number>
resolution resolve/<name> <reviewed-resolution-commit-sha> <reviewed-tree-sha>
```

The shared command verifies the original PR is still conflicted at the exact
parent SHAs, verifies the separate review PR/ref/commit/tree and its independent
checks/statuses, then rechecks all mutable refs. It creates one Git commit with
the reviewed tree and parents exactly `[base, head]`, reads that object back,
rechecks every ref again, and advances the base ref without force.

Only after that irreversible ref update does normal permanent-lane lifecycle
run. Promotion can advance the retained lane and dispatch stable + lane;
synchronization dispatches the updated lane. The original conflicted PR and
review PR are closed, and the unchanged resolution ref is deleted.

If the original PR becomes normally mergeable, use `/merge` instead.
`/merge-resolved` is refused for temporary/ordinary PRs.

## Irreversible operation and recovery

The merge request is the irreversible commit boundary. Before it, validation failures are reported as `Merge refused before merge`. If the merge API call itself errors or returns an unrecognised response, the state is `MERGE OUTCOME UNKNOWN` and the command **must not claim no merge occurred**. After GitHub reports `merged=true`, failures in branch update/deletion or workflow dispatch **cannot** roll the merge back.

The command attempts to post a PR comment even if post-merge work failed. After a failed lane update, it may still dispatch the stable base, but it does not dispatch the unadvanced lane. Individual dispatch failures do not hide successes for other refs. The comment includes the accepted merge commit SHA and distinguishes:

- successful merge and completed lifecycle/dispatch;
- successful merge but incomplete lifecycle/dispatch (nonzero command exit);
- no merge attempted due to readiness/validation failure.

If GitHub rejects comment publication too, the error and merge SHA are still emitted in job logs. A failed post-merge operation currently requires an operator to inspect and recover the affected ref/dispatch. Temporary-head deletion checks the current head SHA immediately beforehand, but GitHub's REST delete is not conditional and that check is not an atomic guarantee against simultaneous external pushes. **Automatic recovery/replay is not implemented**; idempotent recovery is part of #112's remaining scope. A failed dispatch must not be mistaken for a failed merge.

## Security boundaries

- Only tool source at the called workflow revision is checked out; checkout credentials are not persisted.
- The job has a bounded timeout; Python runs through `python3` available on the runner image.
- The integration-workflow identifier is restricted to a YAML filename rather than a path.
- No arbitrary merge method input exists.
- The workflow currently has write permissions for PR merge, ref update, comments, and optional integration dispatch. Separate governance review (#114) must determine whether job-level permissions and stronger action SHA pinning can be adopted without breaking callers.
- Merge commands are serialized per **caller repository**, not per PR number, to avoid two command jobs racing on the same stable base. External/manual merges remain possible and cannot be fully serialized by this workflow (#114).

## Testing

`tests/test_merge_policy.py` exercises classification and YAML adapter boundaries. `tests/test_merge_command.py` covers bounded polling, pagination, check identity, command exclusion, HTTP 404 distinction and post-merge reporting using offline fixtures. These do **not** replace black-box acceptance in `tool.cad.ci.test`. Consumers must not repin to this branch; qualify an immutable release first.
