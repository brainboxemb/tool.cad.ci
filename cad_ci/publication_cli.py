"""CLI commands for build-store and Pages publication operations.

These commands are separate from plan/run because publication often operates on
prepared candidate directories and generated-branch checkouts rather than on a
consumer's item graph.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_repository
from .build_store import (
    BuildStoreError,
    install_scope,
    prepare_main,
    prepare_overlay,
    promote_overlay,
    remove_pr,
    resolve_view,
)
from .git_publish import (
    GitPublishError,
    publish_build_pr_cleanup,
    publish_build_scope,
    publish_pages,
    publish_pages_preview_cleanup,
)
from .pages import PagesError, install_preview, install_stable, remove_preview


PUBLICATION_ERRORS = (BuildStoreError, PagesError, GitPublishError)


def add_publication_commands(sub: argparse._SubParsersAction) -> None:
    """Add build, pages and publish command groups to the main parser."""

    build = sub.add_parser("build", help="prepare and manage build-store scopes")
    build_sub = build.add_subparsers(dest="build_command", required=True)

    prepare_main_cmd = build_sub.add_parser("prepare-main")
    _candidate_args(prepare_main_cmd)

    prepare_pr = build_sub.add_parser("prepare-pr")
    _candidate_args(prepare_pr)
    prepare_pr.add_argument("--pull-request", type=int, required=True)

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
    install.add_argument("--scope", choices=("main", "pr"), required=True)
    install.add_argument("--pull-request", type=int)

    remove = build_sub.add_parser("remove-pr")
    remove.add_argument("--store", type=Path, required=True)
    remove.add_argument("--pull-request", type=int, required=True)

    pages = sub.add_parser("pages", help="install stable or preview site output")
    pages_sub = pages.add_subparsers(dest="pages_command", required=True)
    stable = pages_sub.add_parser("install-stable")
    stable.add_argument("--site", type=Path, required=True)
    stable.add_argument("--pages-root", type=Path, required=True)
    preview = pages_sub.add_parser("install-preview")
    preview.add_argument("--site", type=Path, required=True)
    preview.add_argument("--pages-root", type=Path, required=True)
    preview.add_argument("--pull-request", type=int, required=True)
    remove_preview_cmd = pages_sub.add_parser("remove-preview")
    remove_preview_cmd.add_argument("--pages-root", type=Path, required=True)
    remove_preview_cmd.add_argument("--pull-request", type=int, required=True)

    publish = sub.add_parser("publish", help="commit and push generated branches safely")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)

    publish_build = publish_sub.add_parser("build")
    _publish_common(publish_build)
    publish_build.add_argument("--candidate", type=Path, required=True)
    publish_build.add_argument("--scope", choices=("main", "pr"), required=True)
    publish_build.add_argument("--pull-request", type=int)

    publish_build_cleanup = publish_sub.add_parser("build-cleanup")
    _publish_common(publish_build_cleanup)
    publish_build_cleanup.add_argument("--pull-request", type=int, required=True)

    publish_pages_cmd = publish_sub.add_parser("pages")
    _publish_common(publish_pages_cmd)
    publish_pages_cmd.add_argument("--site", type=Path, required=True)
    publish_pages_cmd.add_argument("--pull-request", type=int)

    publish_pages_cleanup = publish_sub.add_parser("pages-cleanup")
    _publish_common(publish_pages_cleanup)
    publish_pages_cleanup.add_argument("--pull-request", type=int, required=True)


def _candidate_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by complete-main and sparse-PR preparation."""

    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--items", nargs="*")


def _candidate_paths(
    args: argparse.Namespace,
    *,
    require_selection: bool,
) -> tuple[Path, ...]:
    """Resolve consumer item IDs to their source paths for build-store layout."""

    items = load_repository(args.repo.resolve())
    if args.items:
        unknown = [item_id for item_id in args.items if item_id not in items]
        if unknown:
            raise BuildStoreError(f"unknown item(s): {', '.join(unknown)}")
        return tuple(items[item_id].path for item_id in args.items)
    if require_selection:
        raise BuildStoreError("PR candidate requires --items")
    return tuple(item.path for item in items.values())


def _publish_common(parser: argparse.ArgumentParser) -> None:
    """Add arguments every generated-branch publication needs."""

    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--message", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--retries", type=int, default=3)
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

    if args.build_command == "prepare-main":
        prepare_main(
            candidate_root=args.candidate_root,
            out=args.out,
            item_paths=_candidate_paths(args, require_selection=False),
            source_commit=args.source_commit,
        )
    elif args.build_command == "prepare-pr":
        prepare_overlay(
            candidate_root=args.candidate_root,
            out=args.out,
            item_paths=_candidate_paths(args, require_selection=True),
            source_commit=args.source_commit,
            pull_request=args.pull_request,
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
        )
        print(target)
    elif args.build_command == "remove-pr":
        print("removed" if remove_pr(store=args.store, pull_request=args.pull_request) else "absent")
    return 0


def _run_pages(args: argparse.Namespace) -> int:
    """Execute filesystem-only Pages installation or cleanup."""

    if args.pages_command == "install-stable":
        install_stable(site=args.site, pages_root=args.pages_root)
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
            **common,
        )
    else:
        commit = publish_pages_preview_cleanup(
            pull_request=args.pull_request,
            **common,
        )
    print(commit)
    return 0
