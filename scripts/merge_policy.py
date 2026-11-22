#!/usr/bin/env python3
"""Resolve repository-neutral merge and branch-lifecycle policy."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


DEFAULT_TEMPORARY_PREFIXES = (
    "issue/",
    "fix/",
    "feature/",
    "accept/",
    "promote/",
    "docs/",
    "chore/",
)


@dataclass(frozen=True)
class MergePolicy:
    """Resolved merge/lifecycle policy for one pull request."""

    merge_method: str
    direct_lane_promotion: bool
    direct_lane_synchronization: bool
    cleanup_head: bool
    integrate_base: bool


def _strings(raw: str, label: str) -> tuple[str, ...]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{label} must be a unique string list")
    return tuple(value)


def is_direct_lane_promotion(
    *,
    base: str,
    head: str,
    stable_ref: str,
    lane_refs: tuple[str, ...],
) -> bool:
    """Return whether one configured long-lived lane is promoted to stable."""

    return base == stable_ref and head in lane_refs


def is_direct_lane_synchronization(
    *,
    base: str,
    head: str,
    stable_ref: str,
    lane_refs: tuple[str, ...],
) -> bool:
    """Return whether stable is synchronized into a configured long-lived lane."""

    return base in lane_refs and head == stable_ref


def is_cleanup_eligible(
    head: str,
    *,
    stable_ref: str,
    lane_refs: tuple[str, ...],
    permanent_refs: tuple[str, ...],
    temporary_prefixes: tuple[str, ...],
) -> bool:
    """Return whether a merged temporary source ref may be deleted."""

    permanent = {stable_ref, *lane_refs, *permanent_refs}
    if head in permanent:
        return False
    if head.startswith("backup/"):
        return False
    return head.startswith(temporary_prefixes)


def evaluate(
    *,
    base: str,
    head: str,
    stable_ref: str,
    lane_refs: tuple[str, ...],
    permanent_refs: tuple[str, ...] = (),
    temporary_prefixes: tuple[str, ...] = DEFAULT_TEMPORARY_PREFIXES,
) -> MergePolicy:
    """Resolve merge method, cleanup and integration-dispatch intent."""

    promotion = is_direct_lane_promotion(
        base=base,
        head=head,
        stable_ref=stable_ref,
        lane_refs=lane_refs,
    )
    synchronization = is_direct_lane_synchronization(
        base=base,
        head=head,
        stable_ref=stable_ref,
        lane_refs=lane_refs,
    )
    permanent_merge = promotion or synchronization
    durable_refs = {stable_ref, *lane_refs}
    return MergePolicy(
        merge_method="merge" if permanent_merge else "squash",
        direct_lane_promotion=promotion,
        direct_lane_synchronization=synchronization,
        cleanup_head=(
            not permanent_merge
            and is_cleanup_eligible(
                head,
                stable_ref=stable_ref,
                lane_refs=lane_refs,
                permanent_refs=permanent_refs,
                temporary_prefixes=temporary_prefixes,
            )
        ),
        integrate_base=base in durable_refs,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--stable-ref", default="main")
    parser.add_argument("--lane-refs-json", required=True)
    parser.add_argument("--permanent-refs-json", default="[]")
    parser.add_argument(
        "--temporary-prefixes-json",
        default=json.dumps(DEFAULT_TEMPORARY_PREFIXES),
    )
    args = parser.parse_args()

    result = evaluate(
        base=args.base,
        head=args.head,
        stable_ref=args.stable_ref,
        lane_refs=_strings(args.lane_refs_json, "lane refs"),
        permanent_refs=_strings(args.permanent_refs_json, "permanent refs"),
        temporary_prefixes=_strings(
            args.temporary_prefixes_json,
            "temporary prefixes",
        ),
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
