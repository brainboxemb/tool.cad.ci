"""Read and validate the CI files owned by a consumer repository.

The root `cad-ci.yml` only discovers item folders. Each item folder owns a
`ci.yml` that describes its dependencies, watched inputs and ordered steps.
This keeps domain behaviour beside the code or model that owns it.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

from .model import Item, Step


class ConfigError(ValueError):
    """Raised when a consumer CI file is missing, unsafe or inconsistent."""


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load one YAML mapping and report the file name in configuration errors."""

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"missing config: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"config must be a mapping: {path}")
    return data


def _strings(value: object, field: str, path: Path) -> tuple[str, ...]:
    """Read a YAML list of strings as an immutable tuple."""

    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ConfigError(f"{field} must be a list of strings: {path}")
    return tuple(value)


def _step(data: object, path: Path) -> Step:
    """Validate one step and convert it to the runner's small Step object."""

    if not isinstance(data, dict):
        raise ConfigError(f"step must be a mapping: {path}")
    step_id = data.get("id")
    run = data.get("run")
    if not isinstance(step_id, str) or not _ID.fullmatch(step_id):
        raise ConfigError(f"step id must use letters, numbers, dot, dash or underscore: {path}")

    # A list is executed directly without a shell. A string is deliberately
    # kept for consumer commands that need shell syntax such as pipes.
    if isinstance(run, list):
        if not run or not all(isinstance(x, str) for x in run):
            raise ConfigError(f"step run list must contain strings: {path}:{step_id}")
        command: str | tuple[str, ...] = tuple(run)
    elif isinstance(run, str) and run:
        command = run
    else:
        raise ConfigError(f"step run is required: {path}:{step_id}")

    outputs = _strings(data.get("outputs"), "outputs", path)
    for output in outputs:
        output_path = Path(output)
        # Declared outputs are later hashed and reused. Letting a step declare
        # ../ would make one item own files outside its build directory.
        if output_path.is_absolute() or ".." in output_path.parts:
            raise ConfigError(f"output must stay inside the item build directory: {path}:{step_id}")
    return Step(step_id, command, outputs)


def load_repository(repo: Path) -> dict[str, Item]:
    """Discover and validate every configured CI item in `repo`.

    Folder globs let a repository add qualification/model items without also
    maintaining a second central item list.
    """

    repo = repo.resolve()
    root_path = repo / "cad-ci.yml"
    root = _load_yaml(root_path)
    if root.get("schema") != 1:
        raise ConfigError(f"unsupported schema in {root_path}")
    item_patterns = _strings(root.get("items"), "items", root_path)
    if not item_patterns:
        raise ConfigError(f"no items configured in {root_path}")

    item_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for pattern in item_patterns:
        rel_pattern = Path(pattern)
        if rel_pattern.is_absolute() or ".." in rel_pattern.parts:
            raise ConfigError(f"item path must stay inside the repository: {pattern}")

        has_glob = any(char in pattern for char in "*?[")
        matches = sorted(repo.glob(pattern)) if has_glob else [repo / rel_pattern]
        # A folder only becomes a CI item when it explicitly owns ci.yml.
        matches = [path for path in matches if path.is_dir() and (path / "ci.yml").is_file()]
        if not matches:
            raise ConfigError(f"item pattern matches no CI folders: {pattern}")
        for path in matches:
            rel = path.relative_to(repo)
            if rel not in seen_paths:
                seen_paths.add(rel)
                item_paths.append(rel)

    items: dict[str, Item] = {}
    for rel in item_paths:
        item_dir = repo / rel
        config_path = item_dir / "ci.yml"
        data = _load_yaml(config_path)

        item_id = data.get("id", rel.as_posix())
        if not isinstance(item_id, str) or not _ID.fullmatch(item_id):
            raise ConfigError(f"item id must use letters, numbers, dot, dash or underscore: {config_path}")
        if item_id in items:
            raise ConfigError(f"duplicate item id: {item_id}")

        # kind is intentionally descriptive only. The generic runner must not
        # gain hidden behaviour for names such as qualification or library-test.
        kind = data.get("kind", "item")
        if not isinstance(kind, str) or not kind:
            raise ConfigError(f"kind must be a string: {config_path}")

        strategy = data.get("strategy", {})
        if strategy is None:
            strategy = {}
        if not isinstance(strategy, dict):
            raise ConfigError(f"strategy must be a mapping: {config_path}")
        affected = strategy.get("affected", "changed")
        if affected not in ("changed", "direct", "always"):
            raise ConfigError(f"strategy.affected must be changed, direct or always: {config_path}")
        reuse = strategy.get("reuse", True)
        if not isinstance(reuse, bool):
            raise ConfigError(f"strategy.reuse must be true or false: {config_path}")

        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ConfigError(f"steps must be a non-empty list: {config_path}")
        steps = tuple(_step(value, config_path) for value in raw_steps)
        step_ids = [step.id for step in steps]
        if len(step_ids) != len(set(step_ids)):
            raise ConfigError(f"duplicate step id in {config_path}")

        # Without an explicit watch list the item owns its complete source
        # folder. Shared inputs can be added explicitly by the consumer.
        watch = _strings(data.get("watch"), "watch", config_path) or (f"{rel.as_posix()}/**",)
        for pattern in watch:
            watch_path = Path(pattern)
            if watch_path.is_absolute() or ".." in watch_path.parts:
                raise ConfigError(f"watch pattern must stay inside the repository: {config_path}")

        items[item_id] = Item(
            id=item_id,
            path=rel,
            kind=kind,
            needs=_strings(data.get("needs"), "needs", config_path),
            watch=watch,
            affected=affected,
            reuse=reuse,
            steps=steps,
            config_path=config_path,
            config_data=data,
        )

    # Resolve dependency names after every item is known. This catches typos
    # before planning or execution starts.
    for item in items.values():
        unknown = sorted(set(item.needs) - set(items))
        if unknown:
            raise ConfigError(f"{item.id} needs unknown item(s): {', '.join(unknown)}")
    _check_cycles(items)
    return items


def _check_cycles(items: dict[str, Item]) -> None:
    """Reject dependency loops because no valid execution order exists."""

    visiting: set[str] = set()
    done: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in done:
            return
        if item_id in visiting:
            raise ConfigError(f"dependency cycle includes {item_id}")
        visiting.add(item_id)
        for dependency in items[item_id].needs:
            visit(dependency)
        visiting.remove(item_id)
        done.add(item_id)

    for item_id in items:
        visit(item_id)
