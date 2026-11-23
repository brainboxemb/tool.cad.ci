#!/usr/bin/env python3
"""Retire explicitly reviewed Git branches only at exact expected SHAs.

Unlike automatic stale-branch cleanup, this command treats an owner-supplied
(ref, SHA) pair as the retirement evidence. It is intended for unique history
that has been reviewed and intentionally declared disposable.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import re
import sys
from urllib.parse import quote

from branch_cleanup import GitHubError, Refused, api, comment, paged_list
from merge_policy import _strings


_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class RetirementResult:
    retired: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)


def parse_command(command: str) -> tuple[tuple[str, str], ...]:
    lines = [line.strip() for line in command.splitlines() if line.strip()]
    if not lines or lines[0] != "/retire-branches":
        raise Refused("first line must be exactly /retire-branches")
    if len(lines) == 1:
        raise Refused("at least one reviewed ref and SHA are required")

    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) != 2:
            raise Refused(f"invalid retirement line: {line!r}")
        ref, sha = parts
        if not ref or ref.startswith("refs/") or ref.startswith("-"):
            raise Refused(f"invalid branch ref: {ref!r}")
        if not _SHA.fullmatch(sha):
            raise Refused(f"invalid expected SHA for {ref}: {sha!r}")
        if ref in seen:
            raise Refused(f"duplicate branch ref: {ref}")
        seen.add(ref)
        pairs.append((ref, sha))
    return tuple(pairs)


def _ref_payload(repo: str, ref: str):
    try:
        return api("GET", f"repos/{repo}/git/ref/heads/{quote(ref, safe='')}")
    except GitHubError as exc:
        if exc.status == 404:
            return None
        raise


def _current_sha(repo: str, ref: str) -> str | None:
    payload = _ref_payload(repo, ref)
    if payload is None:
        return None
    sha = (payload.get("object") or {}).get("sha")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise Refused(f"branch {ref} has no valid current SHA")
    return sha


def retire(
    *,
    repo: str,
    reviewed: tuple[tuple[str, str], ...],
    stable_ref: str,
    lane_refs: tuple[str, ...],
    permanent_refs: tuple[str, ...],
) -> RetirementResult:
    protected = {stable_ref, *lane_refs, *permanent_refs}
    requested = {ref for ref, _ in reviewed}
    forbidden = sorted(requested & protected)
    if forbidden:
        raise Refused("protected refs cannot be retired: " + ", ".join(forbidden))

    open_pulls = paged_list(f"repos/{repo}/pulls?state=open")
    open_heads = {
        (pr.get("head") or {}).get("ref")
        for pr in open_pulls
        if ((pr.get("head") or {}).get("repo") or {}).get("full_name") == repo
    }
    blocked = sorted(requested & open_heads)
    if blocked:
        raise Refused("open PR heads cannot be retired: " + ", ".join(blocked))

    # Preflight every requested ref before any mutation.
    present: list[tuple[str, str]] = []
    result = RetirementResult()
    for ref, expected in reviewed:
        current = _current_sha(repo, ref)
        if current is None:
            result.missing.append(f"{ref} @ {expected}")
            continue
        if current != expected:
            raise Refused(
                f"{ref} moved before retirement: expected {expected}, current {current}"
            )
        present.append((ref, expected))

    # Re-read immediately before each DELETE. If a ref moves after preflight,
    # preserve it and report the race rather than deleting unexpected history.
    for ref, expected in present:
        current = _current_sha(repo, ref)
        if current is None:
            result.missing.append(f"{ref} @ {expected}")
            continue
        if current != expected:
            result.moved.append(
                f"{ref} @ {current} (reviewed {expected})"
            )
            continue
        api("DELETE", f"repos/{repo}/git/refs/heads/{quote(ref, safe='')}")
        result.retired.append(f"{ref} @ {expected}")

    return result


def format_result(result: RetirementResult) -> str:
    groups = (
        ("Retired exact-SHA reviewed branches", result.retired),
        ("Already missing", result.missing),
        ("Kept because the ref moved after review", result.moved),
    )
    lines = ["Exact-SHA branch retirement completed.", ""]
    for title, values in groups:
        lines.append(f"{title}:")
        lines.extend(f"- `{value}`" for value in values)
        if not values:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines).rstrip()


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
    args = parser.parse_args()

    try:
        if args.actor != args.repository_owner:
            raise Refused("only the repository owner may retire branches")
        reviewed = parse_command(args.command)
        result = retire(
            repo=args.repository,
            reviewed=reviewed,
            stable_ref=args.stable_ref,
            lane_refs=_strings(args.lane_refs_json, "lane refs"),
            permanent_refs=_strings(args.permanent_refs_json, "permanent refs"),
        )
        message = format_result(result)
        print(message)
        comment(args.repository, args.issue_number, message)
        return 0
    except (Refused, GitHubError, ValueError, KeyError) as exc:
        message = f"Branch retirement refused: {exc}"
        print(message, file=sys.stderr)
        try:
            comment(args.repository, args.issue_number, message)
        except Exception as comment_exc:
            print(f"Unable to post retirement result: {comment_exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
