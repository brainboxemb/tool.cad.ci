"""Git helpers used to make local and GitHub CI selection behave the same."""

from __future__ import annotations

from pathlib import Path
import subprocess


class GitError(RuntimeError):
    """Raised when Git cannot calculate the requested repository state."""


def changed_files(repo: Path, base: str, head: str) -> tuple[str, ...]:
    """Return files changed between two exact Git revisions.

    The tool owns this comparison so workflow YAML only needs to supply the
    revisions. This keeps local runs and GitHub Actions on the same code path.
    """

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
