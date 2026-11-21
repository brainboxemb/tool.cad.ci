#!/usr/bin/env python3
"""Support the reusable GitHub Actions workflows shipped with tool.cad.ci.

The workflow YAML owns only GitHub-specific orchestration. This helper owns
argument validation, exact plan/run command construction and the optional
non-secret consumer environment passed to domain commands.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


_ENV_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_RESERVED_ENV_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_")


def parse_bool(value: str) -> bool:
    """Parse the lower-case boolean form emitted by GitHub workflow inputs."""

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"invalid boolean value: {value}")



def positive_int(value: str) -> int:
    """Parse one strictly positive integer workflow/CLI value."""

    try:
        result = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("jobs must be a positive integer") from exc
    if result < 1:
        raise ValueError("jobs must be a positive integer")
    return result


def selection_args(
    *,
    source_sha: str,
    base_sha: str,
    full_run: bool,
) -> list[str]:
    """Return the exact generic selection arguments for plan/run."""

    source_sha = source_sha.strip()
    base_sha = base_sha.strip()
    if full_run:
        return []
    if not source_sha:
        raise ValueError("incremental CAD CI requires source_sha")
    if not base_sha:
        raise ValueError("incremental CAD CI requires base_sha")
    return ["--base", base_sha, "--head", source_sha]


def consumer_environment(raw: str) -> dict[str, str]:
    """Validate optional non-secret environment values for consumer commands."""

    text = raw.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("consumer environment must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("consumer environment must be a JSON object")

    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not _ENV_NAME.fullmatch(key):
            raise ValueError(f"invalid consumer environment name: {key!r}")
        if key.startswith(_RESERVED_ENV_PREFIXES):
            raise ValueError(f"reserved consumer environment name: {key}")
        if not isinstance(item, str):
            raise ValueError(
                f"consumer environment value for {key} must be a string"
            )
        result[key] = item
    return result


def library_revision(tool_root: Path) -> str:
    """Return the exact lib.py.cad.ci commit pinned by this tool revision."""

    data = tomllib.loads(
        (tool_root / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = data.get("project", {}).get("dependencies", [])
    prefix = (
        "brainboxemb-cad-ci-lib @ "
        "git+https://github.com/brainboxemb/lib.py.cad.ci.git@"
    )
    matches = [
        value[len(prefix):]
        for value in dependencies
        if isinstance(value, str) and value.startswith(prefix)
    ]
    if len(matches) != 1 or not re.fullmatch(r"[0-9a-f]{40}", matches[0]):
        raise ValueError("tool pyproject must pin one exact lib.py.cad.ci commit")
    return matches[0]


def _tool_command(*arguments: str) -> list[str]:
    """Use the exact tool/library source exposed on PYTHONPATH."""

    return [sys.executable, "-m", "cad_ci_tool.cli", *arguments]


def create_plan(
    *,
    repo: Path,
    source_sha: str,
    base_sha: str,
    full_run: bool,
) -> list[dict]:
    """Run one released cad-ci plan and return its JSON rows."""

    command = _tool_command(
        "plan",
        "--repo",
        str(repo.resolve()),
        *selection_args(
            source_sha=source_sha,
            base_sha=base_sha,
            full_run=full_run,
        ),
        "--json",
    )
    completed = subprocess.run(
        command,
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("cad-ci plan did not return valid JSON") from exc
    if not isinstance(value, list) or not all(
        isinstance(row, dict) for row in value
    ):
        raise ValueError("cad-ci plan must return a JSON list of objects")
    return value


def run_ci(
    *,
    repo: Path,
    source_sha: str,
    base_sha: str,
    full_run: bool,
    environment_json: str,
    jobs: int,
) -> None:
    """Run exactly one released cad-ci repository execution."""

    command = _tool_command(
        "run",
        "--repo",
        str(repo.resolve()),
        *selection_args(
            source_sha=source_sha,
            base_sha=base_sha,
            full_run=full_run,
        ),
        "--jobs",
        str(jobs),
    )
    env = dict(os.environ)
    env.update(consumer_environment(environment_json))
    subprocess.run(command, cwd=repo, env=env, check=True)


def write_github_output(path: Path, key: str, value: str) -> None:
    """Append one multiline-safe GitHub Actions step output."""

    delimiter = "CAD_CI_OUTPUT_EOF"
    if delimiter in value:
        raise ValueError("GitHub output contains reserved delimiter")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")


def main() -> int:
    """Dispatch reusable-workflow plan or run support."""

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    library = commands.add_parser("library-revision")
    library.add_argument("--tool-root", type=Path, required=True)
    library.add_argument("--github-output", type=Path, required=True)

    plan = commands.add_parser("plan")
    plan.add_argument("--repo", type=Path, required=True)
    plan.add_argument("--source-sha", default="")
    plan.add_argument("--base-sha", default="")
    plan.add_argument("--full-run", default="false")
    plan.add_argument("--github-output", type=Path, required=True)

    run_parser = commands.add_parser("run")
    run_parser.add_argument("--repo", type=Path, required=True)
    run_parser.add_argument("--source-sha", default="")
    run_parser.add_argument("--base-sha", default="")
    run_parser.add_argument("--full-run", default="false")
    run_parser.add_argument("--jobs", type=positive_int, default=1)
    run_parser.add_argument(
        "--environment-json",
        default=os.environ.get("CAD_CI_CONSUMER_ENV_JSON", "{}"),
    )

    args = parser.parse_args()

    try:
        if args.command == "library-revision":
            write_github_output(
                args.github_output,
                "revision",
                library_revision(args.tool_root),
            )
            return 0

        full_run = parse_bool(args.full_run)
        if args.command == "plan":
            rows = create_plan(
                repo=args.repo,
                source_sha=args.source_sha,
                base_sha=args.base_sha,
                full_run=full_run,
            )
            write_github_output(
                args.github_output,
                "plan_json",
                json.dumps(rows, separators=(",", ":")),
            )
            return 0

        run_ci(
            repo=args.repo,
            source_sha=args.source_sha,
            base_sha=args.base_sha,
            full_run=full_run,
            environment_json=args.environment_json,
            jobs=args.jobs,
        )
        return 0
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
