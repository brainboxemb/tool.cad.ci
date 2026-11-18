from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Step:
    id: str
    run: str | tuple[str, ...]
    outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Item:
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
