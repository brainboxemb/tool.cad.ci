"""Prepare, resolve and promote durable per-item build output.

The runner writes candidate output below the consumer checkout's `build/`
directory. This module copies validated item directories into the durable build
store layout used by the `build` branch:

- `main/` is the complete accepted baseline;
- `pr/<number>/` is a sparse overlay for one pull request.

Only item directories listed in the overlay manifest are replaced. Unchanged
baseline items are preserved byte-for-byte during promotion.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Iterable


MANIFEST = "build.json"
ITEM_STATE = "item.json"


class BuildStoreError(RuntimeError):
    """Raised when candidate or stored build output cannot be trusted."""


def _safe_relative(path: Path | str) -> Path:
    """Return a normalized repository-relative item path.

    Build item paths come from consumer configuration. Reject absolute paths or
    `..` here as a second safety boundary before any generated branch is
    changed.
    """

    value = Path(path)
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise BuildStoreError(f"unsafe item path: {path}")
    return value


def _read_json(path: Path) -> dict:
    """Read one JSON object and report malformed generated state clearly."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildStoreError(f"missing generated file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildStoreError(f"invalid JSON in generated file: {path}") from exc
    if not isinstance(data, dict):
        raise BuildStoreError(f"generated JSON must be an object: {path}")
    return data


def _replace_tree(source: Path, target: Path) -> None:
    """Replace one directory without exposing a half-copied destination.

    The new tree is copied beside the destination first. Only the final rename
    changes the visible item directory.
    """

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    shutil.rmtree(temp)
    try:
        shutil.copytree(source, temp)
        old = target.parent / f".{target.name}.previous"
        if old.exists():
            shutil.rmtree(old)
        if target.exists():
            target.rename(old)
        try:
            temp.rename(target)
        except Exception:
            if old.exists() and not target.exists():
                old.rename(target)
            raise
        if old.exists():
            shutil.rmtree(old)
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def _item_record(candidate_root: Path, item_path: Path, source_commit: str) -> dict:
    """Build the manifest row for one complete runner item result."""

    state = _read_json(candidate_root / item_path / ITEM_STATE)
    if state.get("status") != "pass":
        raise BuildStoreError(f"item is not complete/pass: {item_path.as_posix()}")
    input_fingerprint = state.get("input_fingerprint")
    result_fingerprint = state.get("result_fingerprint")
    if not isinstance(input_fingerprint, str) or not isinstance(result_fingerprint, str):
        raise BuildStoreError(f"item state has no fingerprints: {item_path.as_posix()}")
    return {
        "source_commit": source_commit,
        "input_fingerprint": input_fingerprint,
        "result_fingerprint": result_fingerprint,
    }


def prepare_main(
    *,
    candidate_root: Path,
    out: Path,
    item_paths: Iterable[Path | str],
    source_commit: str,
) -> dict:
    """Create a complete main candidate from the supplied item set.

    This is used to bootstrap a new build store or to deliberately rebuild the
    complete consumer catalog. Normal partial updates should use a PR overlay
    plus `promote_overlay` instead.
    """

    paths = tuple(_safe_relative(path) for path in item_paths)
    if not paths:
        raise BuildStoreError("main candidate requires at least one item")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    rows: dict[str, dict] = {}
    for item_path in paths:
        source = candidate_root / item_path
        if not source.is_dir():
            raise BuildStoreError(f"missing candidate item: {item_path.as_posix()}")
        rows[item_path.as_posix()] = _item_record(candidate_root, item_path, source_commit)
        target = out / item_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)

    manifest = {
        "schema": 1,
        "scope": "main",
        "source_commit": source_commit,
        "items": rows,
    }
    (out / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest



def update_main(
    *,
    main: Path,
    candidate_root: Path,
    out: Path,
    item_paths: Iterable[Path | str],
    source_commit: str,
) -> dict:
    """Create a new complete main baseline from selected fresh item output.

    The existing main baseline supplies every item that was not selected for
    this run. Selected item directories must be complete runner results in
    `candidate_root`. They are validated before the output tree is changed.
    """

    main_manifest = load_manifest(main, expected_scope="main")
    paths = tuple(_safe_relative(path) for path in item_paths)
    if not paths:
        raise BuildStoreError("main update requires at least one selected item")

    # Validate every replacement first. A bad candidate must fail before a
    # partially updated main candidate is exposed to later publication steps.
    replacements: dict[Path, dict] = {}
    for item_path in paths:
        source = candidate_root / item_path
        if not source.is_dir():
            raise BuildStoreError(
                f"missing candidate item: {item_path.as_posix()}"
            )
        replacements[item_path] = _item_record(
            candidate_root,
            item_path,
            source_commit,
        )

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(main, out)

    rows = dict(main_manifest["items"])
    for item_path, row in replacements.items():
        _replace_tree(candidate_root / item_path, out / item_path)
        rows[item_path.as_posix()] = row

    manifest = {
        "schema": 1,
        "scope": "main",
        "source_commit": source_commit,
        "items": rows,
    }
    (out / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def prepare_overlay(
    *,
    candidate_root: Path,
    out: Path,
    item_paths: Iterable[Path | str],
    source_commit: str,
    pull_request: int,
) -> dict:
    """Create a sparse PR overlay from selected complete runner item output."""

    if pull_request <= 0:
        raise BuildStoreError("pull_request must be positive")
    paths = tuple(_safe_relative(path) for path in item_paths)
    if not paths:
        raise BuildStoreError("overlay requires at least one item")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    rows: dict[str, dict] = {}
    for item_path in paths:
        source = candidate_root / item_path
        if not source.is_dir():
            raise BuildStoreError(f"missing candidate item: {item_path.as_posix()}")
        rows[item_path.as_posix()] = _item_record(candidate_root, item_path, source_commit)
        target = out / item_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)

    manifest = {
        "schema": 1,
        "scope": "pr",
        "pull_request": pull_request,
        "source_commit": source_commit,
        "items": rows,
    }
    (out / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_manifest(root: Path, *, expected_scope: str | None = None) -> dict:
    """Read and validate the generic build-store manifest."""

    data = _read_json(root / MANIFEST)
    if data.get("schema") != 1:
        raise BuildStoreError(f"unsupported build manifest schema in {root}")
    scope = data.get("scope")
    if scope not in {"main", "pr"}:
        raise BuildStoreError(f"invalid build scope in {root}: {scope!r}")
    if expected_scope is not None and scope != expected_scope:
        raise BuildStoreError(f"expected {expected_scope} build scope in {root}, found {scope}")
    items = data.get("items")
    if not isinstance(items, dict):
        raise BuildStoreError(f"build manifest has no item map: {root}")
    for path, row in items.items():
        _safe_relative(path)
        if not isinstance(row, dict):
            raise BuildStoreError(f"invalid item manifest row: {path}")
        if not (root / path / ITEM_STATE).is_file():
            raise BuildStoreError(f"manifest item directory is missing: {path}")
    return data


def resolve_view(*, main: Path, overlay: Path | None, out: Path) -> dict:
    """Build a complete read-only view from main plus an optional PR overlay."""

    main_manifest = load_manifest(main, expected_scope="main")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(main, out)

    merged_items = dict(main_manifest["items"])
    source_commit = main_manifest.get("source_commit", "")
    if overlay is not None:
        overlay_manifest = load_manifest(overlay, expected_scope="pr")
        for item_path in overlay_manifest["items"]:
            _replace_tree(overlay / item_path, out / item_path)
            merged_items[item_path] = overlay_manifest["items"][item_path]
        source_commit = overlay_manifest.get("source_commit", source_commit)

    # A resolved view is a temporary complete view, so record it as main-shaped
    # output rather than carrying PR sparsity into site/build consumers.
    manifest = {
        "schema": 1,
        "scope": "main",
        "source_commit": source_commit,
        "items": merged_items,
    }
    (out / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def promote_overlay(*, main: Path, overlay: Path, out: Path, source_commit: str) -> dict:
    """Create the next complete main baseline by replacing overlay item paths."""

    main_manifest = load_manifest(main, expected_scope="main")
    overlay_manifest = load_manifest(overlay, expected_scope="pr")

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(main, out)

    merged_items = dict(main_manifest["items"])
    for item_path, row in overlay_manifest["items"].items():
        _replace_tree(overlay / item_path, out / item_path)
        merged_items[item_path] = row

    manifest = {
        "schema": 1,
        "scope": "main",
        "source_commit": source_commit,
        "items": merged_items,
    }
    (out / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def install_scope(
    *,
    candidate: Path,
    store: Path,
    scope: str,
    pull_request: int | None = None,
) -> Path:
    """Install a prepared scope into a checked-out build-branch tree.

    This function only changes files. Git commit/push handling is deliberately
    separate so the same store logic is testable without a remote repository.
    """

    if scope == "main":
        load_manifest(candidate, expected_scope="main")
        target = store / "main"
    elif scope == "pr":
        load_manifest(candidate, expected_scope="pr")
        if pull_request is None or pull_request <= 0:
            raise BuildStoreError("PR scope requires a positive pull_request")
        target = store / "pr" / str(pull_request)
    else:
        raise BuildStoreError(f"unknown scope: {scope}")

    _replace_tree(candidate, target)
    return target


def remove_pr(*, store: Path, pull_request: int) -> bool:
    """Remove one durable PR overlay and leave every other scope untouched."""

    if pull_request <= 0:
        raise BuildStoreError("pull_request must be positive")
    target = store / "pr" / str(pull_request)
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True
