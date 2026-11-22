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
import shutil
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


_SCOPE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def durable_scope_name(value: str) -> str:
    """Validate one generated long-lived build scope name."""

    scope = value.strip()
    if (
        not scope
        or not _SCOPE_NAME.fullmatch(scope)
        or scope in {".", "..", ".cad-ci"}
    ):
        raise ValueError(f"invalid durable scope name: {value!r}")
    return scope


def exact_sha(value: str, label: str) -> str:
    """Validate one exact lowercase 40-character Git SHA."""

    sha = value.strip()
    if not _SHA.fullmatch(sha):
        raise ValueError(f"{label} must be an exact 40-character Git SHA")
    return sha


def resolve_durable_scope(
    *,
    repo: Path,
    generated_build: Path,
    scope: str,
    source_sha: str,
) -> dict[str, str]:
    """Fetch durable build state and resolve one lane's incremental base."""

    repo = repo.resolve()
    generated_build = generated_build.resolve()
    scope = durable_scope_name(scope)
    source_sha = exact_sha(source_sha, "source_sha")

    if generated_build.exists():
        shutil.rmtree(generated_build)

    subprocess.run(
        _tool_command(
            "build",
            "fetch",
            "--repo",
            str(repo),
            "--out",
            str(generated_build),
        ),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    manifest = generated_build / scope / "build.json"
    if not manifest.is_file():
        if scope == "main":
            raise ValueError(
                "durable main scope is missing; stable integration cannot "
                "be updated incrementally"
            )
        return {
            "scope": scope,
            "base_sha": source_sha,
            "full_run": "true",
            "scope_exists": "false",
            "generated_build": str(generated_build),
        }

    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"durable scope has invalid build.json: {scope}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError(f"durable scope has invalid build.json: {scope}")

    base_sha = value.get("source_commit")
    if not isinstance(base_sha, str) or not _SHA.fullmatch(base_sha):
        raise ValueError(
            f"durable scope has invalid source_commit: {scope}"
        )

    return {
        "scope": scope,
        "base_sha": base_sha,
        "full_run": "false",
        "scope_exists": "true",
        "generated_build": str(generated_build),
    }


def publish_durable_scope(
    *,
    repo: Path,
    generated_build: Path,
    prepared_scope: Path,
    candidate_root: Path,
    scope: str,
    scope_exists: bool,
    source_sha: str,
    base_sha: str,
    source_ref: str,
) -> dict[str, str]:
    """Prepare and publish one complete long-lived build scope."""

    repo = repo.resolve()
    generated_build = generated_build.resolve()
    prepared_scope = prepared_scope.resolve()
    candidate_root = candidate_root.resolve()
    scope = durable_scope_name(scope)
    source_sha = exact_sha(source_sha, "source_sha")
    base_sha = exact_sha(base_sha, "base_sha")
    source_ref = source_ref.strip()
    if not source_ref:
        raise ValueError("source_ref is required for durable publication")

    if prepared_scope.exists():
        shutil.rmtree(prepared_scope)

    if scope == "main":
        prepare = _tool_command(
            "build",
            "update-main",
            "--repo",
            str(repo),
            "--candidate-root",
            str(candidate_root),
            "--main",
            str(generated_build / "main"),
            "--out",
            str(prepared_scope),
            "--source-commit",
            source_sha,
            "--base",
            base_sha,
            "--head",
            source_sha,
        )
    elif scope_exists:
        prepare = _tool_command(
            "build",
            "update-named",
            "--repo",
            str(repo),
            "--candidate-root",
            str(candidate_root),
            "--named",
            str(generated_build / scope),
            "--name",
            scope,
            "--out",
            str(prepared_scope),
            "--source-commit",
            source_sha,
            "--base",
            base_sha,
            "--head",
            source_sha,
        )
    else:
        prepare = _tool_command(
            "build",
            "prepare-named",
            "--repo",
            str(repo),
            "--candidate-root",
            str(candidate_root),
            "--name",
            scope,
            "--out",
            str(prepared_scope),
            "--source-commit",
            source_sha,
        )

    subprocess.run(
        prepare,
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    publish = _tool_command(
        "publish",
        "build",
        "--repo",
        str(repo),
        "--candidate",
        str(prepared_scope),
        "--scope",
        "main" if scope == "main" else "named",
        *(
            []
            if scope == "main"
            else ["--scope-name", scope]
        ),
        "--message",
        f"build: {scope} {source_sha}",
        "--source-ref",
        source_ref,
        "--expected-source",
        source_sha,
    )
    completed = subprocess.run(
        publish,
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    build_commit = completed.stdout.strip()
    if not _SHA.fullmatch(build_commit):
        raise ValueError(
            "durable build publication did not return an exact commit"
        )

    return {
        "build_commit": build_commit,
        "prepared_scope": str(prepared_scope),
    }


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

    durable_resolve = commands.add_parser("durable-resolve")
    durable_resolve.add_argument("--repo", type=Path, required=True)
    durable_resolve.add_argument(
        "--generated-build",
        type=Path,
        required=True,
    )
    durable_resolve.add_argument("--scope", required=True)
    durable_resolve.add_argument("--source-sha", required=True)
    durable_resolve.add_argument(
        "--github-output",
        type=Path,
        required=True,
    )

    durable_publish = commands.add_parser("durable-publish")
    durable_publish.add_argument("--repo", type=Path, required=True)
    durable_publish.add_argument(
        "--generated-build",
        type=Path,
        required=True,
    )
    durable_publish.add_argument(
        "--prepared-scope",
        type=Path,
        required=True,
    )
    durable_publish.add_argument(
        "--candidate-root",
        type=Path,
        required=True,
    )
    durable_publish.add_argument("--scope", required=True)
    durable_publish.add_argument(
        "--scope-exists",
        choices=("true", "false"),
        required=True,
    )
    durable_publish.add_argument("--source-sha", required=True)
    durable_publish.add_argument("--base-sha", required=True)
    durable_publish.add_argument("--source-ref", required=True)
    durable_publish.add_argument(
        "--github-output",
        type=Path,
        required=True,
    )

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

        if args.command == "durable-resolve":
            resolved = resolve_durable_scope(
                repo=args.repo,
                generated_build=args.generated_build,
                scope=args.scope,
                source_sha=args.source_sha,
            )
            for key, value in resolved.items():
                write_github_output(
                    args.github_output,
                    key,
                    value,
                )
            return 0

        if args.command == "durable-publish":
            published = publish_durable_scope(
                repo=args.repo,
                generated_build=args.generated_build,
                prepared_scope=args.prepared_scope,
                candidate_root=args.candidate_root,
                scope=args.scope,
                scope_exists=args.scope_exists == "true",
                source_sha=args.source_sha,
                base_sha=args.base_sha,
                source_ref=args.source_ref,
            )
            for key, value in published.items():
                write_github_output(
                    args.github_output,
                    key,
                    value,
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
