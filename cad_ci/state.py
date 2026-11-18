"""Hash inputs and outputs used to decide whether CI results are reusable.

File outputs keep their historical SHA-256 value. Directory outputs use one
stable tree hash built from relative file paths and file hashes. This lets a
consumer declare a complete native/result directory without maintaining a
second hand-written manifest of every file inside it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .model import Item, Step
from .paths import files_for_patterns


class OutputHashError(ValueError):
    """Raised when a declared output cannot be hashed safely."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one regular file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_directory(path: Path) -> str:
    """Hash all regular files below one directory in stable path order.

    Symlinks are rejected instead of followed. A declared output is part of the
    item build directory; allowing a symlink to point elsewhere would make the
    recorded result depend on data outside that owned output tree.
    """

    if path.is_symlink():
        raise OutputHashError(f"declared output is a symlink: {path}")
    if not path.is_dir():
        raise OutputHashError(f"declared directory output is not a directory: {path}")

    digest = hashlib.sha256()
    digest.update(b"directory\0")
    for child in sorted(path.rglob("*"), key=lambda value: value.as_posix()):
        if child.is_symlink():
            raise OutputHashError(f"declared output contains a symlink: {child}")
        if not child.is_file():
            continue
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(child).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def sha256_output(path: Path) -> str | None:
    """Hash a declared file or directory output.

    Missing paths return None so the runner can use the same missing-output
    failure for files and directories. File hashes intentionally stay byte-for-
    byte compatible with v0.2 state.
    """

    if path.is_symlink():
        raise OutputHashError(f"declared output is a symlink: {path}")
    if path.is_file():
        return sha256_file(path)
    if path.is_dir():
        return sha256_directory(path)
    return None


def hash_data(data: object) -> str:
    """Hash JSON-compatible data with stable key ordering."""

    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def item_input_fingerprint(
    repo: Path,
    item: Item,
    dependency_results: dict[str, str],
) -> str:
    """Hash the watched source, item config and dependency results."""

    files = files_for_patterns(repo, item.watch)
    file_hashes = {
        path.relative_to(repo).as_posix(): sha256_file(path)
        for path in files
    }
    return hash_data(
        {
            "config": item.config_data,
            "files": file_hashes,
            "dependencies": dependency_results,
        }
    )


def step_input_fingerprint(
    item_fingerprint: str,
    step: Step,
    previous_result: str | None,
) -> str:
    """Hash the exact inputs that decide whether one step can be reused."""

    return hash_data(
        {
            "item": item_fingerprint,
            "step": {
                "id": step.id,
                "run": step.run,
                "outputs": step.outputs,
            },
            "previous_result": previous_result,
        }
    )


def step_result_fingerprint(
    input_fingerprint: str,
    outputs: dict[str, str],
) -> str:
    """Bind one successful step input to the hashes of its declared outputs."""

    return hash_data({"input": input_fingerprint, "outputs": outputs})


def read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON object, returning None for missing or invalid state files."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write stable, human-readable JSON state below the item output."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
