from __future__ import annotations

from pathlib import Path
import subprocess


class GitError(RuntimeError):
    pass


def changed_files(repo: Path, base: str, head: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", base, head, "--"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "git diff failed"
        raise GitError(message)
    return tuple(line for line in completed.stdout.splitlines() if line)
