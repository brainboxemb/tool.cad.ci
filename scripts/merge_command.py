#!/usr/bin/env python3
"""Execute a configured merge policy against GitHub's API.

The merge itself is irreversible. Post-merge failures are reported separately.
No pull-request code is checked out or executed by this command.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import re
import subprocess
import sys
import time

from merge_policy import evaluate, _strings
from merge_resolution import parse_resolution_command, verify_merge_object


class Refused(Exception):
    """A merge was not attempted because its preconditions failed."""


class MergeOutcomeUnknown(RuntimeError):
    """The merge API call failed without proof whether GitHub merged the PR."""


class GitHubError(RuntimeError):
    """GitHub API operation failed; status is available when returned."""

    def __init__(self, operation: str, status: int, detail: str):
        self.status = status
        super().__init__(f"{operation}: HTTP {status}: {detail[:250]}")


def api(
    method: str,
    endpoint: str,
    *,
    fields: dict[str, str] | None = None,
    field_lists: dict[str, list[str]] | None = None,
):
    """Call GitHub with JSON and distinguish API absence from API failure."""
    argv = ["gh", "api", "-X", method, "-H", "Accept: application/vnd.github+json",
            "-i", endpoint]
    for name, value in (fields or {}).items():
        # GitHub refs PATCH requires a JSON boolean for force, not a string.
        argv += ["-F" if name == "force" else "-f", f"{name}={value}"]
    for name, values in (field_lists or {}).items():
        for value in values:
            argv += ["-f", f"{name}[]={value}"]
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    # gh api -i returns headers and body; the last response handles 100/redirects.
    matches = list(re.finditer(r"(?m)^HTTP/\S+ (\d{3})[^\n]*\r?$", result.stdout))
    if not matches:
        raise GitHubError(endpoint, 0, result.stderr or "missing HTTP response")
    match = matches[-1]
    status = int(match.group(1))
    raw = result.stdout[match.end():]
    # Separate the final response headers from its body (gh api -i).
    parts = re.split(r"\r?\n\r?\n", raw, maxsplit=1)
    content = (parts[1] if len(parts) == 2 else "").strip()
    if result.returncode != 0 or not 200 <= status < 300:
        raise GitHubError(endpoint, status, content or result.stderr)
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise GitHubError(endpoint, status, "invalid JSON response") from exc


def pages(endpoint: str, key: str) -> list[dict]:
    """Fetch every page of a GitHub list endpoint; reject incomplete results."""
    values: list[dict] = []
    page = 1
    total = None
    while True:
        glue = "&" if "?" in endpoint else "?"
        payload = api("GET", f"{endpoint}{glue}per_page=100&page={page}")
        if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
            raise Refused(f"invalid {key} API response")
        if total is None:
            total = payload.get("total_count")
            if not isinstance(total, int) or total < 0:
                raise Refused(f"{key} API response has no total_count")
        batch = payload[key]
        values.extend(batch)
        if len(values) >= total:
            break
        if not batch:
            raise Refused(f"incomplete {key} API response ({len(values)}/{total})")
        page += 1
    if len(values) != total:
        raise Refused(f"inconsistent {key} API response ({len(values)}/{total})")
    return values


def ready_pr(repo: str, number: int, retries: int = 5) -> dict:
    """Wait briefly for GitHub's asynchronous mergeability calculation."""
    for attempt in range(retries):
        pr = api("GET", f"repos/{repo}/pulls/{number}")
        if pr.get("state") != "open":
            raise Refused("pull request is not open")
        if pr.get("draft") is not False:
            raise Refused("pull request is still a draft")
        if pr.get("mergeable") is not None:
            if pr["mergeable"] is not True:
                raise Refused("pull request is not mergeable")
            return pr
        if attempt + 1 < retries:
            time.sleep(min(2**attempt, 5))
    raise Refused("mergeability still unknown after bounded retries")


def conflicted_pr(
    repo: str,
    number: int,
    expected_base_sha: str,
    expected_head_sha: str,
    retries: int = 5,
) -> dict:
    """Require one open PR that is still genuinely conflicted at reviewed parents."""
    for attempt in range(retries):
        pr = api("GET", f"repos/{repo}/pulls/{number}")
        if pr.get("state") != "open":
            raise Refused("pull request is not open")
        if pr.get("draft") is not False:
            raise Refused("pull request is still a draft")
        base = pr.get("base") or {}
        head = pr.get("head") or {}
        if base.get("sha") != expected_base_sha:
            raise Refused("reviewed base SHA no longer matches pull request")
        if head.get("sha") != expected_head_sha:
            raise Refused("reviewed head SHA no longer matches pull request")
        if pr.get("mergeable") is not None:
            if pr["mergeable"] is not False:
                raise Refused("pull request is mergeable; use normal /merge")
            return pr
        if attempt + 1 < retries:
            time.sleep(min(2**attempt, 5))
    raise Refused("mergeability still unknown after bounded retries")


def verify_fresh_pr(
    repo: str,
    number: int,
    previous: dict,
    *,
    require_mergeable: bool = True,
) -> None:
    """Reject a PR whose base/head/state changed while evidence was inspected."""
    current = api("GET", f"repos/{repo}/pulls/{number}")
    if current.get("state") != "open" or current.get("draft") is not False:
        raise Refused("PR changed state during validation")
    for side in ("base", "head"):
        before = previous.get(side) or {}
        after = current.get(side) or {}
        if after.get("ref") != before.get("ref") or after.get("sha") != before.get("sha"):
            raise Refused(f"PR {side} changed during validation; rerun checks")
    mergeable = current.get("mergeable")
    if require_mergeable and mergeable is not True:
        raise Refused("PR is no longer mergeable after validation")
    if not require_mergeable and mergeable is not False:
        raise Refused("conflicted PR changed mergeability; restart reviewed resolution")


def validated_checks(
    checks: list[dict],
    commands: list[dict],
    current_run_id: str = "",
) -> list[dict]:
    """Remove command-workflow checks, not normal PR validation checks.

    All indexed issue_comment runs on the checked SHA are excluded, including
    older command attempts. The current command run is excluded explicitly by
    run id as well, because its check can become visible before the Actions
    runs API indexes the corresponding issue_comment run.
    """
    command_ids = {str(run["id"]) for run in commands if "id" in run}
    if current_run_id:
        if not current_run_id.isdigit():
            raise Refused("current_run_id must be a numeric GitHub Actions run id")
        command_ids.add(current_run_id)
    pattern = re.compile(r"/actions/runs/(\d+)(?:/|$|[?#])")
    by_identity: dict[tuple[str, str], dict] = {}
    for check in checks:
        match = pattern.search(check.get("details_url") or "")
        if match and match.group(1) in command_ids:
            continue
        app = check.get("app") or {}
        identity = (str(app.get("id", "")), str(check.get("name", "")))
        ordering = (check.get("started_at") or "", int(check.get("id") or 0))
        previous = by_identity.get(identity)
        if previous is None or ordering > (
            previous.get("started_at") or "", int(previous.get("id") or 0)
        ):
            by_identity[identity] = check
    result = list(by_identity.values())
    if not result:
        raise Refused("no independent validation checks exist on current head")
    bad = [f"{c.get('name')}={c.get('status')}/{c.get('conclusion')}"
           for c in result if c.get("status") != "completed"
           or c.get("conclusion") not in {"success", "neutral", "skipped"}]
    if bad:
        raise Refused("checks are not green: " + ", ".join(bad))
    return result


def validate_commit(repo: str, sha: str, current_run_id: str = "") -> None:
    """Require independent green checks/statuses for one immutable commit."""
    checks = pages(f"repos/{repo}/commits/{sha}/check-runs", "check_runs")
    command_runs = pages(
        f"repos/{repo}/actions/runs?head_sha={sha}&event=issue_comment",
        "workflow_runs",
    )
    validated_checks(checks, command_runs, current_run_id)
    statuses = api("GET", f"repos/{repo}/commits/{sha}/status")
    if statuses.get("statuses") and statuses.get("state") != "success":
        raise Refused(f"commit status contexts are not green ({statuses.get('state')})")


def ref_sha(repo: str, ref: str) -> str:
    """Read one exact branch SHA or fail closed."""
    payload = api("GET", f"repos/{repo}/git/ref/heads/{ref}")
    sha = (payload.get("object") or {}).get("sha")
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise Refused(f"branch {ref} has no valid SHA")
    return sha


def require_ref_sha(repo: str, ref: str, expected: str, label: str) -> None:
    current = ref_sha(repo, ref)
    if current != expected:
        raise Refused(
            f"{label} ref moved: {ref} expected {expected}, current {current}"
        )


def comment(repo: str, number: int, message: str) -> None:
    api("POST", f"repos/{repo}/issues/{number}/comments", fields={"body": message})


def ref_state(repo: str, ref: str) -> bool:
    """Only a genuine HTTP 404 means absent; all other failures propagate."""
    try:
        api("GET", f"repos/{repo}/git/ref/heads/{ref}")
        return True
    except GitHubError as exc:
        if exc.status == 404:
            return False
        raise


@dataclass
class PostMergeResult:
    """Actual lifecycle and dispatch outcomes; no silent partial success."""

    lifecycle: str = "not-requested"
    dispatched: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def post_merge(repo: str, base: str, head: str, merge_sha: str, policy,
               head_repo: str, merged_head_sha: str, integration_workflow: str) -> PostMergeResult:
    result = PostMergeResult()
    try:
        result.lifecycle = apply_lifecycle(repo, head, merge_sha, policy,
                                           head_repo, merged_head_sha)
    except (GitHubError, Refused) as exc:
        result.lifecycle = "FAILED"
        result.errors.append(f"branch lifecycle: {exc}")

    if integration_workflow:
        # The stable base can be integrated even if a lane update failed.
        refs = ([base] if policy.integrate_base else []) + (
            [head] if policy.direct_lane_promotion and result.lifecycle != "FAILED" else []
        )
        for ref in refs:
            try:
                api("POST", f"repos/{repo}/actions/workflows/{integration_workflow}/dispatches",
                    fields={"ref": ref})
                result.dispatched.append(ref)
            except GitHubError as exc:
                result.errors.append(f"integration dispatch {ref}: {exc}")
    return result


def apply_lifecycle(repo: str, head: str, merge_sha: str, policy,
                    head_repo: str, merged_head_sha: str) -> str:
    """Perform a single permitted branch operation, or report its failure."""
    lifecycle = "not-requested"
    if policy.direct_lane_promotion:
        if ref_state(repo, head):
            api("PATCH", f"repos/{repo}/git/refs/heads/{head}",
                fields={"sha": merge_sha, "force": "false"})
            lifecycle = "long-lived lane advanced to merge commit"
        else:
            api("POST", f"repos/{repo}/git/refs",
                fields={"ref": f"refs/heads/{head}", "sha": merge_sha})
            lifecycle = "long-lived lane recreated at merge commit"
    elif policy.direct_lane_synchronization:
        lifecycle = "long-lived lane synchronized by merge"
    elif policy.cleanup_head and head_repo == repo:
        # A new commit may have appeared on the branch after the PR merge.
        # Never delete a branch whose current head differs from the merged PR.
        try:
            current = api("GET", f"repos/{repo}/git/ref/heads/{head}")
        except GitHubError as exc:
            if exc.status != 404:
                raise
            lifecycle = "temporary head already absent"
        else:
            if current.get("object", {}).get("sha") != merged_head_sha:
                raise Refused("temporary branch moved after merge; refusing cleanup")
            api("DELETE", f"repos/{repo}/git/refs/heads/{head}")
            lifecycle = "temporary head deleted"

    return lifecycle


def _resolution_review(
    repo: str,
    original_number: int,
    original_pr: dict,
    resolved,
) -> dict:
    """Require a separate green mergeable PR that exposes the reviewed tree."""
    if resolved.resolution_pr == original_number:
        raise Refused("resolution review PR must be separate from conflicted PR")
    review = ready_pr(repo, resolved.resolution_pr)
    base = review.get("base") or {}
    head = review.get("head") or {}
    head_repo = (head.get("repo") or {}).get("full_name", "")
    if base.get("ref") != (original_pr.get("base") or {}).get("ref"):
        raise Refused("resolution review PR must target the conflicted PR base")
    if base.get("sha") != resolved.base_sha:
        raise Refused("resolution review PR base SHA differs from reviewed base")
    if head_repo != repo:
        raise Refused("resolution review PR must originate in this repository")
    if head.get("ref") != resolved.resolution_ref:
        raise Refused("resolution review PR head ref differs from reviewed resolution")
    if head.get("sha") != resolved.resolution_sha:
        raise Refused("resolution review PR head SHA differs from reviewed resolution")

    require_ref_sha(
        repo, resolved.resolution_ref, resolved.resolution_sha, "resolution"
    )
    commit = api("GET", f"repos/{repo}/git/commits/{resolved.resolution_sha}")
    tree = (commit.get("tree") or {}).get("sha")
    if tree != resolved.resolution_tree:
        raise Refused(
            "resolution commit tree differs from reviewed tree: "
            f"expected {resolved.resolution_tree}, got {tree}"
        )

    validate_commit(repo, resolved.resolution_sha)
    verify_fresh_pr(repo, resolved.resolution_pr, review)
    return review


def _close_pr_if_open(repo: str, number: int) -> str:
    pr = api("GET", f"repos/{repo}/pulls/{number}")
    if pr.get("state") != "open":
        return "already closed"
    api("PATCH", f"repos/{repo}/pulls/{number}", fields={"state": "closed"})
    return "closed"


def _cleanup_resolution_ref(repo: str, ref: str, expected_sha: str) -> str:
    try:
        current = ref_sha(repo, ref)
    except GitHubError as exc:
        if exc.status == 404:
            return "resolution ref already absent"
        raise
    if current != expected_sha:
        return f"resolution ref moved to {current}; retained"
    api("DELETE", f"repos/{repo}/git/refs/heads/{ref}")
    return "resolution ref deleted"


def run_resolved(args) -> int:
    """Apply one reviewed resolved tree to a conflicted permanent-ref PR."""
    repository = args.repository
    number = args.pull_request_number
    resolved = parse_resolution_command(args.command, args.resolution_prefix)
    pr = conflicted_pr(
        repository,
        number,
        resolved.base_sha,
        resolved.head_sha,
    )
    base, head = pr["base"]["ref"], pr["head"]["ref"]
    head_repo = (pr["head"].get("repo") or {}).get("full_name", "")

    policy = evaluate(
        base=base,
        head=head,
        stable_ref=args.stable_ref,
        lane_refs=_strings(args.lane_refs_json, "lane refs"),
        permanent_refs=_strings(args.permanent_refs_json, "permanent refs"),
        temporary_prefixes=_strings(args.temporary_prefixes_json, "temporary prefixes"),
    )
    if not (policy.direct_lane_promotion or policy.direct_lane_synchronization):
        raise Refused("resolved merge recovery is only for permanent-ref direction")
    if head_repo != repository:
        raise Refused("permanent-branch merge must originate in this repository")

    review = _resolution_review(repository, number, pr, resolved)

    # Recheck all reviewed mutable identities immediately before creating the
    # merge object. The object creation itself does not advance any ref.
    verify_fresh_pr(repository, number, pr, require_mergeable=False)
    verify_fresh_pr(repository, resolved.resolution_pr, review)
    require_ref_sha(repository, base, resolved.base_sha, "base")
    require_ref_sha(repository, head, resolved.head_sha, "head")
    require_ref_sha(
        repository, resolved.resolution_ref, resolved.resolution_sha, "resolution"
    )

    created = api(
        "POST",
        f"repos/{repository}/git/commits",
        fields={
            "message": (
                f"Resolved permanent merge PR #{number}: {head} -> {base}"
            ),
            "tree": resolved.resolution_tree,
        },
        field_lists={"parents": [resolved.base_sha, resolved.head_sha]},
    )
    created_sha = created.get("sha")
    if not isinstance(created_sha, str):
        raise Refused("GitHub did not return a merge commit SHA")
    exact = api("GET", f"repos/{repository}/git/commits/{created_sha}")
    merge_sha = verify_merge_object(
        exact,
        expected_tree=resolved.resolution_tree,
        expected_parents=(resolved.base_sha, resolved.head_sha),
    )

    # Final race check before the irreversible ref update.
    verify_fresh_pr(repository, number, pr, require_mergeable=False)
    verify_fresh_pr(repository, resolved.resolution_pr, review)
    require_ref_sha(repository, base, resolved.base_sha, "base")
    require_ref_sha(repository, head, resolved.head_sha, "head")
    require_ref_sha(
        repository, resolved.resolution_ref, resolved.resolution_sha, "resolution"
    )

    try:
        api(
            "PATCH",
            f"repos/{repository}/git/refs/heads/{base}",
            fields={"sha": merge_sha, "force": "false"},
        )
    except GitHubError as exc:
        raise MergeOutcomeUnknown(
            f"PR #{number}, reviewed parents {resolved.base_sha}/"
            f"{resolved.head_sha}: base-ref update failed ({exc}); "
            "the resolved merge may have completed. Inspect refs before retrying."
        ) from exc

    outcome = post_merge(
        repository,
        base,
        head,
        merge_sha,
        policy,
        head_repo,
        resolved.head_sha,
        args.integration_workflow,
    )

    cleanup_notes: list[str] = []
    for pr_number, label in (
        (number, "conflicted PR"),
        (resolved.resolution_pr, "resolution review PR"),
    ):
        try:
            cleanup_notes.append(
                f"{label} {_close_pr_if_open(repository, pr_number)}"
            )
        except GitHubError as exc:
            outcome.errors.append(f"{label} close: {exc}")
    try:
        cleanup_notes.append(
            _cleanup_resolution_ref(
                repository, resolved.resolution_ref, resolved.resolution_sha
            )
        )
    except (GitHubError, Refused) as exc:
        outcome.errors.append(f"resolution ref cleanup: {exc}")

    message = (
        f"Resolved conflicted permanent merge at `{merge_sha}`: "
        f"`{head}` -> `{base}`. Parents: "
        f"`{resolved.base_sha}`, `{resolved.head_sha}`. "
        f"Reviewed resolution: PR #{resolved.resolution_pr}, "
        f"`{resolved.resolution_ref}@{resolved.resolution_sha}`, tree "
        f"`{resolved.resolution_tree}`. Branch lifecycle: "
        f"{outcome.lifecycle}. Integration dispatched: "
        f"{', '.join(outcome.dispatched) or 'none'}. "
        f"Resolution cleanup: {'; '.join(cleanup_notes) or 'none'}."
    )
    if outcome.errors:
        message += " Post-merge processing FAILED: " + "; ".join(outcome.errors)

    print(message, file=sys.stderr if outcome.errors else sys.stdout)
    try:
        comment(repository, number, message)
    except GitHubError as exc:
        print(f"Unable to post result comment: {exc}", file=sys.stderr)
        outcome.errors.append(f"report comment: {exc}")
    return 1 if outcome.errors else 0


def run(args) -> int:
    repository = args.repository
    number = args.pull_request_number
    # The current release intentionally allows only the repository account
    # owner. Organization role policy is a separate compatibility decision.
    if args.actor != args.repository_owner:
        raise Refused("only the repository owner may issue merge commands")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.ya?ml", args.integration_workflow or "x.yml"):
        raise Refused("integration_workflow must be one workflow YAML filename")
    if args.command.startswith("/merge-resolved"):
        return run_resolved(args)
    if args.command != "/merge":
        raise Refused("command must be /merge or reviewed /merge-resolved")
    pr = ready_pr(repository, number)
    base, head = pr["base"]["ref"], pr["head"]["ref"]
    head_sha = pr["head"]["sha"]
    head_repo = (pr["head"].get("repo") or {}).get("full_name", "")
    policy = evaluate(
        base=base, head=head, stable_ref=args.stable_ref,
        lane_refs=_strings(args.lane_refs_json, "lane refs"),
        permanent_refs=_strings(args.permanent_refs_json, "permanent refs"),
        temporary_prefixes=_strings(args.temporary_prefixes_json, "temporary prefixes"),
    )
    if (policy.direct_lane_promotion or policy.direct_lane_synchronization) and head_repo != repository:
        raise Refused("permanent-branch merge must originate in this repository")
    validate_commit(
        repository, head_sha, getattr(args, "current_run_id", "")
    )
    verify_fresh_pr(repository, number, pr)
    # The SHA parameter rejects a moved head. A network/API failure after this
    # irreversible call does NOT prove whether the merge happened.
    try:
        merged = api("PUT", f"repos/{repository}/pulls/{number}/merge",
                     fields={"sha": head_sha, "merge_method": policy.merge_method})
    except GitHubError as exc:
        raise MergeOutcomeUnknown(
            f"PR #{number}, validated head {head_sha}: merge API failed ({exc}); "
            "a merge may have completed. Inspect the PR before retrying."
        ) from exc
    if merged.get("merged") is not True or not merged.get("sha"):
        raise MergeOutcomeUnknown(
            f"PR #{number}, validated head {head_sha}: unexpected merge response "
            f"({merged}); verify merged state before retrying."
        )
    sha = merged["sha"]
    # Post-merge failures cannot undo the accepted merge. Report each phase.
    outcome = post_merge(
        repository, base, head, sha, policy, head_repo, head_sha, args.integration_workflow
    )
    if outcome.errors:
        message = (
            f"PR merged at `{sha}` ({head} -> {base}, {policy.merge_method}), "
            f"but post-merge processing FAILED: {'; '.join(outcome.errors)}. "
            f"Branch lifecycle: {outcome.lifecycle}. "
            f"Integration dispatched: {', '.join(outcome.dispatched) or 'none'}. "
            "Inspect the workflow and recover incomplete steps manually."
        )
    else:
        message = (
            f"Merged by shared repository policy: `{head} -> {base}` using "
            f"**{policy.merge_method}** at `{sha}`. Branch lifecycle: "
            f"{outcome.lifecycle}. Integration dispatched: "
            f"{', '.join(outcome.dispatched) or 'none'}."
        )
    print(message, file=sys.stderr if outcome.errors else sys.stdout)
    try:
        comment(repository, number, message)
    except GitHubError as exc:
        print(f"Unable to post result comment: {exc}", file=sys.stderr)
        outcome.errors.append(f"report comment: {exc}")
    return 1 if outcome.errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-request-number", required=True, type=int)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repository-owner", required=True)
    parser.add_argument("--stable-ref", default="main")
    parser.add_argument("--lane-refs-json", required=True)
    parser.add_argument("--permanent-refs-json", default='["build","gh-pages"]')
    parser.add_argument("--temporary-prefixes-json", required=True)
    parser.add_argument("--integration-workflow", default="")
    parser.add_argument("--current-run-id", default="")
    parser.add_argument("--resolution-prefix", default="resolve/")
    args = parser.parse_args()
    try:
        return run(args)
    except MergeOutcomeUnknown as exc:
        message = f"MERGE OUTCOME UNKNOWN: {exc}"
        print(message, file=sys.stderr)
        try:
            comment(args.repository, args.pull_request_number, message)
        except GitHubError as comment_error:
            print(f"Could not post uncertainty warning: {comment_error}", file=sys.stderr)
        return 1
    except (Refused, GitHubError, ValueError, KeyError) as exc:
        message = f"Merge refused before merge: {exc}"
        print(message, file=sys.stderr)
        try:
            comment(args.repository, args.pull_request_number, message)
        except GitHubError as comment_error:
            print(f"Could not post refusal: {comment_error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
