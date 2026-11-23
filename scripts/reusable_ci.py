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
_SHA = re.compile(r"^[0-9a-f]{40}$")
_RESERVED_ENV_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_", "CAD_CI_", "PIP_", "LD_")
_RESERVED_ENV_NAMES = {
    "HOME", "PATH", "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP",
    "VIRTUAL_ENV", "DOCKER_CONFIG", "GH_TOKEN", "GITHUB_TOKEN",
    "SSH_AUTH_SOCK",
}


def exact_sha(value: str, name: str) -> str:
    """Validate one exact lowercase 40-character Git commit id."""

    normalized = value.strip()
    if _SHA.fullmatch(normalized) is None:
        raise ValueError(f"{name} must be exactly 40 lowercase hex characters")
    return normalized


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
        # For local callers a full run need not compare Git revisions.
        return []
    if not source_sha:
        raise ValueError("incremental CAD CI requires source_sha")
    if not base_sha:
        raise ValueError("incremental CAD CI requires base_sha")
    return [
        "--base", exact_sha(base_sha, "base_sha"),
        "--head", exact_sha(source_sha, "source_sha"),
    ]


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
        if key in _RESERVED_ENV_NAMES or key.startswith(_RESERVED_ENV_PREFIXES):
            raise ValueError(f"reserved consumer environment name: {key}")
        if not isinstance(item, str):
            raise ValueError(
                f"consumer environment value for {key} must be a string"
            )
        result[key] = item
    return result


def _policy_ref(value: object, name: str) -> str:
    """Validate one configured branch/ref name used by PR policy."""

    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if (
        not normalized
        or normalized.startswith("/")
        or ".." in normalized.split("/")
        or any(character.isspace() for character in normalized)
    ):
        raise ValueError(f"{name} must be a safe non-empty ref name")
    return normalized


def _policy_prefix(value: object) -> str:
    """Validate one repository-relative docs-only path prefix."""

    if not isinstance(value, str):
        raise ValueError("docs_only_prefixes entries must be strings")
    normalized = value.strip()
    if (
        not normalized
        or normalized.startswith("/")
        or ".." in Path(normalized).parts
    ):
        raise ValueError("docs_only_prefixes entries must be safe relative paths")
    return normalized


def parse_pr_policy(raw: str) -> dict[str, object]:
    """Validate optional long-lived-lane pull-request policy JSON."""

    text = raw.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("PR policy must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("PR policy must be a JSON object")

    allowed = {"stable_ref", "lane_refs", "docs_only_prefixes"}
    extra = set(value) - allowed
    if extra:
        raise ValueError(f"unsupported PR policy field(s): {sorted(extra)}")

    stable_ref = _policy_ref(value.get("stable_ref", "main"), "stable_ref")
    lane_value = value.get("lane_refs", [])
    if not isinstance(lane_value, list):
        raise ValueError("lane_refs must be a JSON list")
    lane_refs = tuple(
        _policy_ref(item, "lane_refs entry")
        for item in lane_value
    )
    if not lane_refs:
        raise ValueError("lane_refs must contain at least one ref")
    if len(set(lane_refs)) != len(lane_refs):
        raise ValueError("lane_refs must not contain duplicates")
    if stable_ref in lane_refs:
        raise ValueError("stable_ref must not also be a lane ref")

    prefix_value = value.get("docs_only_prefixes", [])
    if not isinstance(prefix_value, list):
        raise ValueError("docs_only_prefixes must be a JSON list")
    prefixes = tuple(_policy_prefix(item) for item in prefix_value)

    return {
        "stable_ref": stable_ref,
        "lane_refs": lane_refs,
        "docs_only_prefixes": prefixes,
    }


def git_changed_paths(
    repo: Path,
    *,
    base_sha: str,
    source_sha: str,
) -> tuple[str, ...]:
    """Return rename-disabled changed paths for one exact Git range."""

    base_sha = exact_sha(base_sha, "base_sha")
    source_sha = exact_sha(source_sha, "source_sha")
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "-z",
            "--no-renames",
            base_sha,
            source_sha,
        ],
        cwd=repo,
        stdout=subprocess.PIPE,
        check=True,
    )
    return tuple(
        item.decode("utf-8", errors="surrogateescape")
        for item in completed.stdout.split(b"\0")
        if item
    )


def resolve_pr_policy(
    *,
    repo: Path,
    policy_json: str,
    event_name: str,
    base_ref: str,
    head_ref: str,
    base_sha: str,
    source_sha: str,
    explicit_full_run: bool,
) -> dict[str, object]:
    """Resolve whether one PR should run and whether it requires full CI."""

    policy = parse_pr_policy(policy_json)
    if not policy:
        return {
            "run_cad": True,
            "full_run": explicit_full_run,
            "classification": "default",
        }
    if event_name != "pull_request":
        return {
            "run_cad": True,
            "full_run": explicit_full_run,
            "classification": "non-pr",
        }
    if explicit_full_run:
        return {
            "run_cad": True,
            "full_run": True,
            "classification": "explicit-full",
        }

    stable_ref = policy["stable_ref"]
    lane_refs = policy["lane_refs"]
    prefixes = policy["docs_only_prefixes"]

    if base_ref == stable_ref and head_ref in lane_refs:
        return {
            "run_cad": True,
            "full_run": True,
            "classification": "lane-promotion",
        }

    if base_ref in lane_refs and prefixes:
        changed = git_changed_paths(
            repo,
            base_sha=base_sha,
            source_sha=source_sha,
        )
        if changed and all(
            any(path.startswith(prefix) for prefix in prefixes)
            for path in changed
        ):
            return {
                "run_cad": False,
                "full_run": False,
                "classification": "docs-only",
            }
        return {
            "run_cad": True,
            "full_run": False,
            "classification": "lane-incremental",
        }

    return {
        "run_cad": True,
        "full_run": False,
        "classification": (
            "stable-target" if base_ref == stable_ref else "unmanaged-base"
        ),
    }


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


def durable_state(
    *,
    repo: Path,
    generated_build: Path,
    scope: str,
    source_sha: str,
) -> dict[str, object]:
    """Resolve one complete durable scope through the pinned library."""

    from cad_ci.durable import fetch_durable_scope_state

    state = fetch_durable_scope_state(
        repo=repo.resolve(),
        generated_build=generated_build.resolve(),
        scope=scope,
        source_sha=exact_sha(source_sha, "source_sha"),
    )
    return {
        "scope": state.scope,
        "base_sha": state.base_sha,
        "full_run": state.full_run,
        "exists": state.exists,
    }


def durable_publish(
    *,
    repo: Path,
    generated_build: Path,
    prepared_scope: Path,
    candidate_root: Path,
    scope: str,
    base_sha: str,
    full_run: bool,
    exists: bool,
    source_sha: str,
    source_ref: str,
) -> tuple[str, str]:
    """Publish one complete build scope and its optional configured Pages site."""

    from cad_ci.durable import (
        DurableScopeState,
        publish_durable_pages,
        publish_durable_scope,
    )

    source_sha = exact_sha(source_sha, "source_sha")
    state = DurableScopeState(
        scope=scope.strip(),
        base_sha=exact_sha(base_sha, "base_sha"),
        full_run=full_run,
        exists=exists,
    )
    source_ref = _policy_ref(source_ref, "source_ref")

    build_commit = publish_durable_scope(
        repo=repo.resolve(),
        generated_build=generated_build.resolve(),
        prepared_scope=prepared_scope.resolve(),
        candidate_root=candidate_root.resolve(),
        state=state,
        source_sha=source_sha,
        source_ref=source_ref,
    )
    pages_commit = publish_durable_pages(
        repo=repo.resolve(),
        generated_build=generated_build.resolve(),
        prepared_scope=prepared_scope.resolve(),
        state=state,
        source_sha=source_sha,
        source_ref=source_ref,
        build_commit=build_commit,
    )
    return build_commit, pages_commit or ""


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

    pr_policy = commands.add_parser("pr-policy")
    pr_policy.add_argument("--repo", type=Path, required=True)
    pr_policy.add_argument("--policy-json", required=True)
    pr_policy.add_argument("--event-name", required=True)
    pr_policy.add_argument("--base-ref", default="")
    pr_policy.add_argument("--head-ref", default="")
    pr_policy.add_argument("--base-sha", required=True)
    pr_policy.add_argument("--source-sha", required=True)
    pr_policy.add_argument("--full-run", default="false")
    pr_policy.add_argument("--github-output", type=Path, required=True)

    plan = commands.add_parser("plan")
    plan.add_argument("--repo", type=Path, required=True)
    plan.add_argument("--source-sha", default="")
    plan.add_argument("--base-sha", default="")
    plan.add_argument("--full-run", default="false")
    plan.add_argument("--github-output", type=Path, required=True)

    durable_state_parser = commands.add_parser("durable-state")
    durable_state_parser.add_argument("--repo", type=Path, required=True)
    durable_state_parser.add_argument(
        "--generated-build", type=Path, required=True
    )
    durable_state_parser.add_argument("--scope", required=True)
    durable_state_parser.add_argument("--source-sha", required=True)
    durable_state_parser.add_argument(
        "--github-output", type=Path, required=True
    )

    durable_publish_parser = commands.add_parser("durable-publish")
    durable_publish_parser.add_argument("--repo", type=Path, required=True)
    durable_publish_parser.add_argument(
        "--generated-build", type=Path, required=True
    )
    durable_publish_parser.add_argument(
        "--prepared-scope", type=Path, required=True
    )
    durable_publish_parser.add_argument(
        "--candidate-root", type=Path, required=True
    )
    durable_publish_parser.add_argument("--scope", required=True)
    durable_publish_parser.add_argument("--base-sha", required=True)
    durable_publish_parser.add_argument("--full-run", required=True)
    durable_publish_parser.add_argument("--exists", required=True)
    durable_publish_parser.add_argument("--source-sha", required=True)
    durable_publish_parser.add_argument("--source-ref", required=True)
    durable_publish_parser.add_argument(
        "--github-output", type=Path, required=True
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

        if args.command == "pr-policy":
            resolution = resolve_pr_policy(
                repo=args.repo,
                policy_json=args.policy_json,
                event_name=args.event_name,
                base_ref=args.base_ref,
                head_ref=args.head_ref,
                base_sha=args.base_sha,
                source_sha=args.source_sha,
                explicit_full_run=parse_bool(args.full_run),
            )
            for key in ("run_cad", "full_run", "classification"):
                value = resolution[key]
                if isinstance(value, bool):
                    value = str(value).lower()
                write_github_output(args.github_output, key, str(value))
            return 0

        if args.command == "durable-state":
            resolution = durable_state(
                repo=args.repo,
                generated_build=args.generated_build,
                scope=args.scope,
                source_sha=args.source_sha,
            )
            for key in ("scope", "base_sha", "full_run", "exists"):
                value = resolution[key]
                if isinstance(value, bool):
                    value = str(value).lower()
                write_github_output(args.github_output, key, str(value))
            return 0

        if args.command == "durable-publish":
            build_commit, pages_commit = durable_publish(
                repo=args.repo,
                generated_build=args.generated_build,
                prepared_scope=args.prepared_scope,
                candidate_root=args.candidate_root,
                scope=args.scope,
                base_sha=args.base_sha,
                full_run=parse_bool(args.full_run),
                exists=parse_bool(args.exists),
                source_sha=args.source_sha,
                source_ref=args.source_ref,
            )
            write_github_output(
                args.github_output, "build_commit", build_commit
            )
            write_github_output(
                args.github_output, "pages_commit", pages_commit
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
    except (
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        RuntimeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
