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
import tomllib
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def release_version(root: Path = ROOT) -> str:
    """Return the release version after checking all version sources agree."""

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not _VERSION.fullmatch(version):
        raise ValueError(f"VERSION is not a release version: {version}")

    pyproject = tomllib.loads(
        (root / "pyproject.toml").read_text(encoding="utf-8")
    )
    if pyproject.get("project", {}).get("version") != version:
        raise ValueError("VERSION and [project].version in pyproject.toml do not match")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.compile(rf"(?m)^## {re.escape(version)} - ")
    if heading.search(changelog) is None:
        raise ValueError(f"CHANGELOG.md has no {version} release heading")
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


def _tag_commit(base: str, tag: str, token: str) -> str | None:
    """Resolve a lightweight or annotated tag to its actual immutable commit."""

    try:
        reference = _request(f"{base}/git/ref/tags/{tag}", token)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    target = reference.get("object") or {}
    # Annotated tags refer to tag objects, not immediately to commit objects.
    for _ in range(5):
        kind, sha = target.get("type"), target.get("sha")
        if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            raise ValueError(f"release tag {tag} has an invalid target")
        if kind == "commit":
            return sha
        if kind != "tag":
            raise ValueError(f"release tag {tag} targets unsupported object {kind}")
        value = _request(f"{base}/git/tags/{sha}", token)
        target = value.get("object") or {}
    raise ValueError(f"release tag {tag} has excessive tag indirection")


def publish(repository: str, sha: str, token: str, root: Path = ROOT) -> str:
    """Create the missing GitHub release for the exact supplied main commit."""

    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise ValueError("GITHUB_REPOSITORY must have owner/name form")
    if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise ValueError("GITHUB_SHA must be an exact 40-character commit")
    version = release_version(root)
    tag = f"v{version}"
    base = f"https://api.github.com/repos/{repository}"

    # Never treat an existing version as successful if it points to a
    # different commit. A newer main with unchanged VERSION is not a release.
    existing_commit = _tag_commit(base, tag, token)
    if existing_commit is not None and existing_commit != sha:
        raise ValueError(
            f"{tag} already points to {existing_commit}; refusing to relabel {sha}"
        )
    try:
        _request(f"{base}/releases/tags/{tag}", token)
    except HTTPError as exc:
        if exc.code != 404:
            raise
    else:
        if existing_commit is None:
            raise ValueError(f"release {tag} exists but tag reference is missing")
        return f"release already exists: {tag} at {existing_commit}"

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
