from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path


IGNORED_PARTS = {".git", "build", "__pycache__"}


def matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch(path, pattern)


def files_for_patterns(repo: Path, patterns: tuple[str, ...]) -> list[Path]:
    result: list[Path] = []
    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        rel_text = rel.as_posix()
        if any(matches(rel_text, pattern) for pattern in patterns):
            result.append(file_path)
    return sorted(set(result), key=lambda p: p.as_posix())
