#!/usr/bin/env python3
"""Publish the release declared by VERSION after a green main CI run.

GitHub Actions supplies authentication and the exact main commit. This script
owns the release checks so version policy does not live as shell logic in YAML.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def release_version(root: Path = ROOT) -> str:
    """Return the release version after checking all version sources agree."""

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not _VERSION.fullmatch(version):
        raise ValueError(f"VERSION is not a release version: {version}")

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if f'version = "{version}"' not in pyproject:
        raise ValueError("VERSION and pyproject.toml do not match")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## {version} -" not in changelog:
        raise ValueError(f"CHANGELOG.md has no {version} release section")
    return version


def _request(url: str, token: str, *, method: str = "GET", data: dict | None = None):
    """Send one authenticated GitHub REST request and decode its JSON response."""

    payload = None if data is None else json.dumps(data).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def publish(repository: str, sha: str, token: str, root: Path = ROOT) -> str:
    """Create the missing GitHub release for the exact supplied main commit."""

    version = release_version(root)
    tag = f"v{version}"
    base = f"https://api.github.com/repos/{repository}"

    # Main workflows can be retried. Treat an existing tag/release as success so
    # a rerun does not fail after the first publication already completed.
    try:
        _request(f"{base}/releases/tags/{tag}", token)
        return f"release already exists: {tag}"
    except HTTPError as exc:
        if exc.code != 404:
            raise

    _request(
        f"{base}/releases",
        token,
        method="POST",
        data={
            "tag_name": tag,
            "target_commitish": sha,
            "name": tag,
            "body": f"tool.cad.ci {version}",
            "draft": False,
            "prerelease": False,
        },
    )
    return f"published release: {tag} at {sha}"


def main() -> int:
    """Read the Actions environment and publish or report a clear error."""

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repository or not sha or not token:
        print("ERROR: GITHUB_REPOSITORY, GITHUB_SHA and GITHUB_TOKEN are required", file=sys.stderr)
        return 2
    try:
        print(publish(repository, sha, token))
    except (ValueError, HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
