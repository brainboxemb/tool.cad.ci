#!/usr/bin/env python3
"""Publish the already-built tool.cad.ci documentation site to gh-pages."""

from __future__ import annotations

import argparse
from pathlib import Path

from cad_ci.git_publish import publish_pages


def main() -> int:
    """Publish stable docs only when the remote source ref is still current."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--source-ref", default="main")
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    commit = publish_pages(
        source_repo=args.repo.resolve(),
        site=args.site,
        message=f"Publish docs at {args.source_commit}",
        source_ref=args.source_ref,
        expected_source=args.source_commit,
    )
    print(commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
