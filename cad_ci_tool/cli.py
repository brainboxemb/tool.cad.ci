"""Command-line interface for planning, running and publishing CAD CI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cad_ci.config import ConfigError, load_repository
from cad_ci.git import GitError, changed_files
from cad_ci.planner import affected_items, build_plan
from cad_ci.runner import RunError, run_repository

def _positive_int(value: str) -> int:
    """Parse one strictly positive integer CLI value."""

    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if result < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


from .publication_cli import (
    PUBLICATION_ERRORS,
    add_publication_commands,
    run_publication_command,
)


def _parser() -> argparse.ArgumentParser:
    """Build one CLI used both locally and by GitHub Actions."""

    parser = argparse.ArgumentParser(prog="cad-ci")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "run"):
        command = sub.add_parser(name)
        command.add_argument(
            "--repo",
            type=Path,
            default=Path.cwd(),
        )

        source = command.add_mutually_exclusive_group()
        source.add_argument("--changed", nargs="*")
        source.add_argument("--base")
        command.add_argument("--head")
        command.add_argument("--item")

        if name == "plan":
            command.add_argument("--json", action="store_true")
        else:
            # The library defines three distinct partial-run operations.
            # Keep them mutually exclusive at the CLI boundary as well.
            partial = command.add_mutually_exclusive_group()
            partial.add_argument("--step")
            partial.add_argument("--from", dest="start")
            partial.add_argument("--until")
            command.add_argument(
                "--jobs",
                type=_positive_int,
                default=1,
                help="Maximum parallel SCons jobs; defaults to 1.",
            )

    add_publication_commands(sub)
    return parser


def _changed(
    repo: Path,
    args: argparse.Namespace,
) -> tuple[str, ...] | None:
    """Resolve CLI selection input to changed repository paths."""

    if args.base is not None:
        if args.head is None:
            raise RunError("--base requires --head")
        return changed_files(repo, args.base, args.head)
    if args.head is not None:
        raise RunError("--head requires --base")
    if args.changed is None:
        return None
    return tuple(args.changed)


def _select(items, changed, item_id):
    """Select one named top-level item or calculate affected items."""

    if item_id is not None:
        if item_id not in items:
            raise RunError(f"unknown item: {item_id}")
        return {item_id}
    return affected_items(items, changed)


def _print_plan(items, selected: set[str], *, as_json: bool) -> None:
    """Print explanatory item selection/dependency closure.

    This plan explains why an item is in repository scope. It deliberately
    does not claim whether SCons considers any step dirty or current.
    """

    plan = build_plan(items, selected)
    if as_json:
        print(
            json.dumps(
                [
                    {
                        "id": entry.item.id,
                        "path": entry.item.path.as_posix(),
                        "kind": entry.item.kind,
                        "reason": entry.reason,
                    }
                    for entry in plan
                ],
                indent=2,
            )
        )
        return

    for entry in plan:
        print(
            f"{entry.item.id}\t{entry.reason}\t"
            f"{entry.item.path.as_posix()}"
        )


def _run_items(args: argparse.Namespace) -> int:
    """Plan or execute one repository selection."""

    repo = args.repo.resolve()
    items = load_repository(repo)
    selected = _select(
        items,
        _changed(repo, args),
        args.item,
    )

    if args.command == "plan":
        _print_plan(
            items,
            selected,
            as_json=args.json,
        )
        return 0

    # One public run becomes one SCons invocation. The tool does not execute
    # items/dependencies itself and does not reimplement incremental decisions.
    run_repository(
        repo,
        items,
        selected,
        item_id=args.item,
        step=args.step,
        start=args.start,
        until=args.until,
        jobs=args.jobs,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse one command and convert expected library failures to exit code 2."""

    args = _parser().parse_args(argv)
    try:
        if args.command in {"build", "pages", "publish"}:
            return run_publication_command(args)
        return _run_items(args)
    except (
        ConfigError,
        GitError,
        RunError,
        *PUBLICATION_ERRORS,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
