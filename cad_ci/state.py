"""Create and validate the fingerprints used for safe output reuse.

Reuse is based on content, not only timestamps or Git history. An item's input
fingerprint includes its watched files, configuration and dependency results.
Each step then chains its result to the previous step.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .model import Item, Step
from .paths import files_for_patterns


def sha256_file(path: Path) -> str:
    """Return a SHA-256 hash without loading a large file into memory at once."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_data(data: object) -> str:
    """Hash JSON-compatible data in a stable key order."""

    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def item_input_fingerprint(repo: Path, item: Item, dependency_results: dict[str, str]) -> str:
    """Hash every declared input that can change an item's result."""

    files = files_for_patterns(repo, item.watch)
    file_hashes = {
        path.relative_to(repo).as_posix(): sha256_file(path)
        for path in files
    }

    # Dependency result hashes are inputs too. This prevents a consumer from
    # reusing output after an upstream item was rebuilt to different content.
    return hash_data(
        {
            "config": item.config_data,
            "files": file_hashes,
            "dependencies": dependency_results,
        }
    )


def step_input_fingerprint(item_fingerprint: str, step: Step, previous_result: str | None) -> str:
    """Hash the inputs for one step, including the previous step's result."""

    return hash_data(
        {
            "item": item_fingerprint,
            "step": {"id": step.id, "run": step.run, "outputs": step.outputs},
            "previous_result": previous_result,
        }
    )


def step_result_fingerprint(input_fingerprint: str, outputs: dict[str, str]) -> str:
    """Bind a step's validated outputs to the exact inputs that produced them."""

    return hash_data({"input": input_fingerprint, "outputs": outputs})


def read_json(path: Path) -> dict[str, Any] | None:
    """Read state JSON, returning None for missing or unusable state."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write deterministic, human-readable state JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
