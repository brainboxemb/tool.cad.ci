"""Small immutable data objects shared by the config, planner and runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Step:
    """One command in an item's ordered CI flow.

    `run` is either an argv tuple or a shell command. `outputs` lists files
    that must exist below the item's build directory after the step succeeds.
    """

    id: str
    run: str | tuple[str, ...]
    outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Item:
    """One consumer-owned folder that can be planned and run independently.

    The tool treats `kind` as descriptive metadata only. Behaviour comes from
    the item's own config, dependencies, watch paths and ordered steps.
    """

    id: str
    path: Path
    kind: str
    needs: tuple[str, ...]
    watch: tuple[str, ...]
    affected: str
    reuse: bool
    steps: tuple[Step, ...]
    config_path: Path
    config_data: dict[str, Any]
