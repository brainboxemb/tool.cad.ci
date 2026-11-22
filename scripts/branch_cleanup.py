#!/usr/bin/env python3
"""Conservatively retire stale temporary branches in a GitHub repository.

A branch is deleted only when its current tip is positively proven retired:
the tip is already integrated into a configured durable ref, or the exact
(ref, SHA) matches a merged pull request head. Open PR heads, moved heads,
permanent/generated refs, backup refs and unique history are preserved.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import re
import subprocess
import sys
from urllib.parse import quote

from merge_policy import _strings, is_cleanup_eligible


class Refused(Exception):
    """Cleanup was not attempted because a safety precondition failed."""


class GitHubError(RuntimeError):
    """GitHub API operation failed."""

    def __init__(self, operation: str, status: int, detail: str):
        self.status = status
        super().__init__(f"{operation}: HTTP {status}: {detail[:250]}")


def api(method: str, endpoint: str, *, fields: dict[str, str] | None = None):
    """Call GitHub through gh and parse the final HTTP response."""
    argv = [
        "gh", "api", "-X", method,
        "-H", "Accept: application/vnd.github+json",
        "-i", endpoint,
    ]
    for name, value in (fields or {}).items():
        argv += ["-f", f"{name}={value}"]
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    matches = list(re.finditer(r"(?m)^HTTP/\S+ (\d{3})[^\n]*\r?$", result.stdout))
    if not matches:
        raise GitHubError(endpoint, 0, result.stderr or "missing HTTP response")
    match = matches[-1]
    status = int(match.group(1))
    raw = result.stdout[match.end():]
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


def paged_list(endpoint: str) -> list[dict]:
    """Fetch every page of a GitHub list endpoint."""
    values: list[dict] = []
    page = 1
    while True:
        glue = "&" if "?" in endpoint else "?"
        batch = api("GET", f"{endpoint}{glue}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise Refused(f"invalid list response for {endpoint}")
        values.extend(batch)
        if len(batch) < 100:
            return values
        page += 1


@dataclass
class CleanupResult:
    """Auditable branch lifecycle outcome."""

    deleted: list[str] = field(default_factory=list)
    open_pr: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)
    unique: list[str] = field(default_factory=list)


def branch_sha(repo: str, branch: str) -> str:
    payload = api("GET", f"repos/{repo}/git/ref/heads/{quote(branch, safe='')}")
    value = (payload.get("object") or {}).get("sha")
    if not isinstance(value, str) or not value:
        raise Refused(f"branch {branch} has no SHA")
    return value


def integration_status(repo: str, branch: str, target: str) -> str:
    """Return compare status for branch...target."""
    source = quote(branch, safe="")
    dest = quote(target, safe="")
    payload = api("GET", f"repos/{repo}/compare/{source}...{dest}")
    value = payload.get("status")
    if not isinstance(value, str):
        raise Refused(f"compare {branch}...{target} has no status")
    return value


def exact_merged_head(branch: str, sha: str, merged_heads: set[tuple[str, str]]) -> bool:
    return (branch, sha) in merged_heads


def is_integrated(repo: str, branch: str, durable_refs: tuple[str, ...]) -> bool:
    return any(
        integration_status(repo, branch, target) in {"ahead", "identical"}
        for target in durable_refs
    )


def cleanup(
    *,
    repo: str,
    stable_ref: str,
    lane_refs: tuple[str, ...],
    permanent_refs: tuple[str, ...],
    temporary_prefixes: tuple[str, ...],
) -> CleanupResult:
    """Evaluate and delete only positively retired temporary branches."""

    branches = paged_list(f"repos/{repo}/branches")
    open_pulls = paged_list(f"repos/{repo}/pulls?state=open")
    closed_pulls = paged_list(f"repos/{repo}/pulls?state=closed")

    open_heads = {
        ((pr.get("head") or {}).get("ref"))
        for pr in open_pulls
        if ((pr.get("head") or {}).get("repo") or {}).get("full_name") == repo
    }
    merged_heads = {
        (((pr.get("head") or {}).get("ref")), ((pr.get("head") or {}).get("sha")))
        for pr in closed_pulls
        if pr.get("merged_at")
        and ((pr.get("head") or {}).get("repo") or {}).get("full_name") == repo
    }
    durable_refs = (stable_ref, *lane_refs)
    result = CleanupResult()

    for entry in branches:
        branch = entry.get("name")
        listed_sha = ((entry.get("commit") or {}).get("sha"))
        if not isinstance(branch, str) or not isinstance(listed_sha, str):
            raise Refused("branch list contains incomplete entry")
        if not is_cleanup_eligible(
            branch,
            stable_ref=stable_ref,
            lane_refs=lane_refs,
            permanent_refs=permanent_refs,
            temporary_prefixes=temporary_prefixes,
        ):
            continue

        label = f"{branch} @ {listed_sha}"
        if branch in open_heads:
            result.open_pr.append(label)
            continue

        retired = is_integrated(repo, branch, durable_refs) or exact_merged_head(
            branch, listed_sha, merged_heads
        )
        if not retired:
            result.unique.append(label)
            continue

        current_sha = branch_sha(repo, branch)
        if current_sha != listed_sha:
            result.moved.append(
                f"{branch} @ {current_sha} (inspected {listed_sha})"
            )
            continue

        api("DELETE", f"repos/{repo}/git/refs/heads/{quote(branch, safe='')}")
        result.deleted.append(label)

    return result


def format_result(result: CleanupResult) -> str:
    groups = (
        ("Deleted integrated or exact merged-PR-head temporary branches", result.deleted),
        ("Kept because an open PR still uses the branch", result.open_pr),
        ("Kept because the branch moved during cleanup", result.moved),
        ("Kept because unique/unmerged commits remain", result.unique),
    )
    lines = ["Branch cleanup completed by conservative shared policy.", ""]
    for title, values in groups:
        if values:
            lines.append(f"{title}:")
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append(f"{title}: none")
        lines.append("")
    return "\n".join(lines).rstrip()


def comment(repo: str, issue_number: int, message: str) -> None:
    api(
        "POST",
        f"repos/{repo}/issues/{issue_number}/comments",
        fields={"body": message},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", required=True, type=int)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repository-owner", required=True)
    parser.add_argument("--stable-ref", default="main")
    parser.add_argument("--lane-refs-json", required=True)
    parser.add_argument("--permanent-refs-json", default='["build","gh-pages"]')
    parser.add_argument("--temporary-prefixes-json", required=True)
    args = parser.parse_args()

    try:
        if args.command != "/cleanup-branches":
            raise Refused("command must be /cleanup-branches")
        if args.actor != args.repository_owner:
            raise Refused("only the repository owner may request cleanup")
        result = cleanup(
            repo=args.repository,
            stable_ref=args.stable_ref,
            lane_refs=_strings(args.lane_refs_json, "lane refs"),
            permanent_refs=_strings(args.permanent_refs_json, "permanent refs"),
            temporary_prefixes=_strings(
                args.temporary_prefixes_json, "temporary prefixes"
            ),
        )
        message = format_result(result)
        print(message)
        comment(args.repository, args.issue_number, message)
        return 0
    except (Refused, GitHubError, ValueError, KeyError) as exc:
        message = f"Branch cleanup refused: {exc}"
        print(message, file=sys.stderr)
        try:
            comment(args.repository, args.issue_number, message)
        except Exception as comment_exc:  # best-effort reporting only
            print(f"Unable to post cleanup result: {comment_exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
