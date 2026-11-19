"""Command-line interface for planning, running and publishing a consumer repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cad_ci.config import ConfigError, load_repository
from cad_ci.git import GitError, changed_files
from cad_ci.planner import affected_items, build_plan
from .publication_cli import (
    PUBLICATION_ERRORS,
    add_publication_commands,
    run_publication_command,
)
from cad_ci.runner import RunError, run_item


def _parser() -> argparse.ArgumentParser:
    """Build one CLI used both locally and by GitHub Actions."""

    parser = argparse.ArgumentParser(prog="cad-ci")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run"):
        command = sub.add_parser(name)
        command.add_argument("--repo", type=Path, default=Path.cwd())

        # CI normally supplies exact base/head revisions. --changed remains
        # useful for focused local tests and diagnostics.
        source = command.add_mutually_exclusive_group()
        source.add_argument("--changed", nargs="*")
        source.add_argument("--base")
        command.add_argument("--head")
        command.add_argument("--item")

        if name == "plan":
            command.add_argument("--json", action="store_true")
        else:
            group = command.add_mutually_exclusive_group()
            group.add_argument("--step")
            group.add_argument("--from", dest="start")
            command.add_argument("--until")

    add_publication_commands(sub)
    return parser


def _changed(repo: Path, args) -> tuple[str, ...] | None:
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
    """Select one named item or calculate all affected items."""

    if item_id is not None:
        if item_id not in items:
            raise RunError(f"unknown item: {item_id}")
        return {item_id}
    return affected_items(items, changed)


def _run_items(args: argparse.Namespace) -> int:
    """Run the existing item-plan and item-execution commands."""

    repo = args.repo.resolve()
    items = load_repository(repo)
    selected = _select(items, _changed(repo, args), args.item)
    plan = build_plan(items, selected)

    if args.command == "plan":
        if args.json:
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
        else:
            for entry in plan:
                print(
                    f"{entry.item.id}\t{entry.reason}\t"
                    f"{entry.item.path.as_posix()}"
                )
        return 0

    partial = args.step is not None or args.start is not None or args.until is not None
    if partial and args.item is None:
        raise RunError("--step/--from/--until require --item")

    # Partial execution is deliberately limited to the named item. Its
    # dependencies are validated by the runner, not silently rebuilt.
    execution_plan = plan
    if partial:
        execution_plan = [entry for entry in plan if entry.item.id == args.item]

    for entry in execution_plan:
        item_partial = partial and entry.item.id == args.item
        events = run_item(
            repo,
            entry.item,
            items,
            step=args.step if item_partial else None,
            start=args.start if item_partial else None,
            until=args.until if item_partial else None,
        )
        for step_id, action in events:
            print(f"{entry.item.id}:{step_id}\t{action}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse a command, run it and convert expected failures to exit code 2."""

    args = _parser().parse_args(argv)
    try:
        if args.command in {"build", "pages", "publish"}:
            return run_publication_command(args)
        return _run_items(args)
    except (ConfigError, GitError, RunError, *PUBLICATION_ERRORS) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
