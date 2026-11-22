"""CLI commands for build-store and Pages publication operations.

These commands are separate from plan/run because publication often operates on
prepared candidate directories and generated-branch checkouts rather than on a
consumer's item graph.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cad_ci.config import load_repository
from cad_ci.git import GitError, changed_files
from cad_ci.planner import affected_items
from cad_ci.build_store import (
    BuildStoreError,
    install_scope,
    prepare_main,
    prepare_named,
    prepare_overlay,
    update_main,
    update_named,
    promote_overlay,
    remove_pr,
    resolve_view,
)
from cad_ci.git_publish import (
    GitPublishError,
    publish_build_pr_cleanup,
    publish_build_scope,
    publish_pages,
    publish_pages_preview_cleanup,
    materialize_generated_branch,
)
from cad_ci.pages import (
    PagesError,
    install_named,
    install_preview,
    install_stable,
    remove_preview,
)


PUBLICATION_ERRORS = (BuildStoreError, PagesError, GitPublishError, GitError)

def positive_int(value: str) -> int:
    """Parse a strictly positive public CLI count (jobs, PR number, retries)."""

    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if result < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result



def add_publication_commands(sub: argparse._SubParsersAction) -> None:
    """Add build, pages and publish command groups to the main parser."""

    build = sub.add_parser("build", help="prepare and manage build-store scopes")
    build_sub = build.add_subparsers(dest="build_command", required=True)

    prepare_main_cmd = build_sub.add_parser("prepare-main")
    _candidate_args(prepare_main_cmd, selectable=False)

    prepare_named_cmd = build_sub.add_parser("prepare-named")
    _candidate_args(prepare_named_cmd, selectable=False)
    prepare_named_cmd.add_argument("--name", required=True)

    prepare_pr = build_sub.add_parser("prepare-pr")
    _candidate_args(prepare_pr, selectable=True)
    prepare_pr.add_argument("--pull-request", type=positive_int, required=True)

    update_main_cmd = build_sub.add_parser("update-main")
    _candidate_args(update_main_cmd, selectable=True)
    update_main_cmd.add_argument("--main", type=Path, required=True)

    update_named_cmd = build_sub.add_parser("update-named")
    _candidate_args(update_named_cmd, selectable=True)
    update_named_cmd.add_argument("--named", type=Path, required=True)
    update_named_cmd.add_argument("--name", required=True)

    resolve = build_sub.add_parser("resolve")
    resolve.add_argument("--main", type=Path, required=True)
    resolve.add_argument("--overlay", type=Path)
    resolve.add_argument("--out", type=Path, required=True)

    promote = build_sub.add_parser("promote")
    promote.add_argument("--main", type=Path, required=True)
    promote.add_argument("--overlay", type=Path, required=True)
    promote.add_argument("--out", type=Path, required=True)
    promote.add_argument("--source-commit", required=True)

    install = build_sub.add_parser("install")
    install.add_argument("--candidate", type=Path, required=True)
    install.add_argument("--store", type=Path, required=True)
    install.add_argument(
        "--scope",
        choices=("main", "named", "pr"),
        required=True,
    )
    install.add_argument("--pull-request", type=int)
    install.add_argument("--scope-name")

    fetch = build_sub.add_parser("fetch")
    fetch.add_argument("--repo", type=Path, default=Path.cwd())
    fetch.add_argument("--out", type=Path, required=True)
    fetch.add_argument("--branch", default="build")
    fetch.add_argument("--remote", default="origin")

    remove = build_sub.add_parser("remove-pr")
    remove.add_argument("--store", type=Path, required=True)
    remove.add_argument("--pull-request", type=positive_int, required=True)

    pages = sub.add_parser("pages", help="install stable or preview site output")
    pages_sub = pages.add_subparsers(dest="pages_command", required=True)
    stable = pages_sub.add_parser("install-stable")
    stable.add_argument("--site", type=Path, required=True)
    stable.add_argument("--pages-root", type=Path, required=True)
    stable.add_argument("--preserve-subtree", action="append", default=[])

    named = pages_sub.add_parser("install-named")
    named.add_argument("--site", type=Path, required=True)
    named.add_argument("--pages-root", type=Path, required=True)
    named.add_argument("--name", required=True)

    preview = pages_sub.add_parser("install-preview")
    preview.add_argument("--site", type=Path, required=True)
    preview.add_argument("--pages-root", type=Path, required=True)
    preview.add_argument("--pull-request", type=positive_int, required=True)
    remove_preview_cmd = pages_sub.add_parser("remove-preview")
    remove_preview_cmd.add_argument("--pages-root", type=Path, required=True)
    remove_preview_cmd.add_argument("--pull-request", type=positive_int, required=True)

    publish = sub.add_parser("publish", help="commit and push generated branches safely")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)

    publish_build = publish_sub.add_parser("build")
    _publish_common(publish_build)
    publish_build.add_argument("--candidate", type=Path, required=True)
    publish_build.add_argument(
        "--scope",
        choices=("main", "named", "pr"),
        required=True,
    )
    publish_build.add_argument("--pull-request", type=int)
    publish_build.add_argument("--scope-name")

    publish_build_cleanup = publish_sub.add_parser("build-cleanup")
    _publish_common(publish_build_cleanup)
    publish_build_cleanup.add_argument("--pull-request", type=positive_int, required=True)

    publish_pages_cmd = publish_sub.add_parser("pages")
    _publish_common(publish_pages_cmd)
    publish_pages_cmd.add_argument("--site", type=Path, required=True)
    pages_target = publish_pages_cmd.add_mutually_exclusive_group()
    pages_target.add_argument("--pull-request", type=int)
    pages_target.add_argument("--name")
    publish_pages_cmd.add_argument(
        "--preserve-subtree",
        action="append",
        default=[],
    )

    publish_pages_cleanup = publish_sub.add_parser("pages-cleanup")
    _publish_common(publish_pages_cleanup)
    publish_pages_cleanup.add_argument("--pull-request", type=positive_int, required=True)


def _candidate_args(
    parser: argparse.ArgumentParser,
    *,
    selectable: bool,
) -> None:
    """Add candidate arguments and optional planner-based selection inputs."""

    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    if not selectable:
        return

    source = parser.add_mutually_exclusive_group()
    source.add_argument("--items", nargs="+")
    source.add_argument("--changed", nargs="+")
    source.add_argument("--base")
    parser.add_argument("--head")


def _candidate_items(
    args: argparse.Namespace,
    *,
    require_selection: bool,
    loaded_items=None,
):
    """Resolve the exact top-level Item objects included in a build scope.

    Runtime dependencies are SCons' responsibility. A sparse PR overlay
    contains only the top-level items selected by the consumer/Git change.
    """

    repo = args.repo.resolve()
    items = load_repository(repo) if loaded_items is None else loaded_items

    explicit = getattr(args, "items", None)
    if explicit:
        unknown = [item_id for item_id in explicit if item_id not in items]
        if unknown:
            raise BuildStoreError(f"unknown item(s): {', '.join(unknown)}")
        return tuple(items[item_id] for item_id in explicit)

    base = getattr(args, "base", None)
    head = getattr(args, "head", None)
    changed = getattr(args, "changed", None)
    if base is not None:
        if head is None:
            raise BuildStoreError("--base requires --head")
        changed_paths = changed_files(repo, base, head)
    elif head is not None:
        raise BuildStoreError("--head requires --base")
    elif changed is not None:
        changed_paths = tuple(changed)
    else:
        if require_selection:
            raise BuildStoreError(
                "selected build operation requires --items, --changed, "
                "or --base/--head"
            )
        selected = affected_items(items, None)
        return tuple(
            item
            for item_id, item in items.items()
            if item_id in selected
        )

    selected = affected_items(items, changed_paths)
    return tuple(
        item
        for item_id, item in items.items()
        if item_id in selected
    )


def _current_processed_items(items):
    """Return repository-ordered current processed items via library semantics."""

    selected = affected_items(items, None)
    return tuple(
        item
        for item_id, item in items.items()
        if item_id in selected
    )


def _publish_common(parser: argparse.ArgumentParser) -> None:
    """Add arguments every generated-branch publication needs."""

    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--message", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--retries", type=positive_int, default=3)
    parser.add_argument("--source-ref")
    parser.add_argument("--expected-source")


def run_publication_command(args: argparse.Namespace) -> int:
    """Execute a parsed build/pages/publish command and print useful results."""

    if args.command == "build":
        return _run_build(args)
    if args.command == "pages":
        return _run_pages(args)
    if args.command == "publish":
        return _run_publish(args)
    raise ValueError(f"not a publication command: {args.command}")


def _run_build(args: argparse.Namespace) -> int:
    """Execute local build-store preparation or installation."""

    if args.build_command == "fetch":
        commit = materialize_generated_branch(
            source_repo=args.repo.resolve(),
            branch=args.branch,
            out=args.out,
            remote=args.remote,
        )
        print(commit)
    elif args.build_command == "prepare-main":
        prepare_main(
            candidate_root=args.candidate_root,
            out=args.out,
            items=_candidate_items(args, require_selection=False),
            source_commit=args.source_commit,
        )
    elif args.build_command == "prepare-named":
        prepare_named(
            candidate_root=args.candidate_root,
            out=args.out,
            items=_candidate_items(args, require_selection=False),
            source_commit=args.source_commit,
            name=args.name,
        )
    elif args.build_command == "prepare-pr":
        prepare_overlay(
            candidate_root=args.candidate_root,
            out=args.out,
            items=_candidate_items(args, require_selection=True),
            source_commit=args.source_commit,
            pull_request=args.pull_request,
        )
    elif args.build_command == "update-main":
        loaded_items = load_repository(args.repo.resolve())
        update_main(
            main=args.main,
            candidate_root=args.candidate_root,
            out=args.out,
            items=_candidate_items(
                args,
                require_selection=True,
                loaded_items=loaded_items,
            ),
            current_items=_current_processed_items(loaded_items),
            source_commit=args.source_commit,
        )
    elif args.build_command == "update-named":
        loaded_items = load_repository(args.repo.resolve())
        update_named(
            named=args.named,
            candidate_root=args.candidate_root,
            out=args.out,
            items=_candidate_items(
                args,
                require_selection=True,
                loaded_items=loaded_items,
            ),
            current_items=_current_processed_items(loaded_items),
            source_commit=args.source_commit,
            name=args.name,
        )
    elif args.build_command == "resolve":
        resolve_view(main=args.main, overlay=args.overlay, out=args.out)
    elif args.build_command == "promote":
        promote_overlay(
            main=args.main,
            overlay=args.overlay,
            out=args.out,
            source_commit=args.source_commit,
        )
    elif args.build_command == "install":
        target = install_scope(
            candidate=args.candidate,
            store=args.store,
            scope=args.scope,
            pull_request=args.pull_request,
            scope_name=args.scope_name,
        )
        print(target)
    elif args.build_command == "remove-pr":
        print("removed" if remove_pr(store=args.store, pull_request=args.pull_request) else "absent")
    return 0


def _run_pages(args: argparse.Namespace) -> int:
    """Execute filesystem-only Pages installation or cleanup."""

    if args.pages_command == "install-stable":
        install_stable(
            site=args.site,
            pages_root=args.pages_root,
            preserve_subtrees=args.preserve_subtree,
        )
    elif args.pages_command == "install-named":
        print(
            install_named(
                site=args.site,
                pages_root=args.pages_root,
                name=args.name,
            )
        )
    elif args.pages_command == "install-preview":
        print(
            install_preview(
                site=args.site,
                pages_root=args.pages_root,
                pull_request=args.pull_request,
            )
        )
    elif args.pages_command == "remove-preview":
        print(
            "removed"
            if remove_preview(
                pages_root=args.pages_root,
                pull_request=args.pull_request,
            )
            else "absent"
        )
    return 0


def _run_publish(args: argparse.Namespace) -> int:
    """Publish one generated-branch mutation and print the resulting commit SHA."""

    common = {
        "source_repo": args.repo.resolve(),
        "message": args.message,
        "remote": args.remote,
        "retries": args.retries,
        "source_ref": args.source_ref,
        "expected_source": args.expected_source,
    }
    if args.publish_command == "build":
        commit = publish_build_scope(
            candidate=args.candidate,
            scope=args.scope,
            pull_request=args.pull_request,
            scope_name=args.scope_name,
            **common,
        )
    elif args.publish_command == "build-cleanup":
        commit = publish_build_pr_cleanup(
            pull_request=args.pull_request,
            **common,
        )
    elif args.publish_command == "pages":
        commit = publish_pages(
            site=args.site,
            pull_request=args.pull_request,
            name=args.name,
            preserve_subtrees=args.preserve_subtree,
            **common,
        )
    else:
        commit = publish_pages_preview_cleanup(
            pull_request=args.pull_request,
            **common,
        )
    print(commit)
    return 0
