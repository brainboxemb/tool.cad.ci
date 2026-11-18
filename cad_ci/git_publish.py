"""Publish generated build or Pages trees with normal Git pushes.

Generated branches can have several independent writers. Each publish attempt
starts from the current remote branch head, applies one scoped filesystem
change, commits it, and pushes without force. If another writer wins the race,
the change is reapplied to the newer head and retried.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

from .build_store import install_scope, remove_pr
from .pages import install_preview, install_stable, remove_preview


class GitPublishError(RuntimeError):
    """Raised when a generated branch cannot be published safely."""


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run Git with captured text output so failures can be reported clearly."""

    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise GitPublishError(message)
    return completed


def _remote_url(source_repo: Path, remote: str) -> str:
    """Read the remote URL from the consumer checkout."""

    return _git(source_repo, "remote", "get-url", remote).stdout.strip()


def _copy_auth_config(source_repo: Path, work: Path) -> None:
    """Copy checkout-scoped HTTP auth headers into the publish checkout.

    `actions/checkout` stores its token as Git HTTP config instead of putting
    credentials in the remote URL. A fresh temporary clone therefore needs the
    same extraheader before it can push.
    """

    rows = _git(
        source_repo,
        "config",
        "--get-regexp",
        r"^http\..*\.extraheader$",
        check=False,
    )
    if rows.returncode != 0:
        return
    for line in rows.stdout.splitlines():
        if not line.strip():
            continue
        key, value = line.split(None, 1)
        _git(work, "config", "--local", key, value)


def _assert_source_current(
    *,
    source_repo: Path,
    remote: str,
    source_ref: str | None,
    expected_source: str | None,
) -> None:
    """Refuse publication when the source branch moved after this run started."""

    if source_ref is None and expected_source is None:
        return
    if not source_ref or not expected_source:
        raise GitPublishError("source_ref and expected_source must be supplied together")

    remote_url = _remote_url(source_repo, remote)
    result = subprocess.run(
        ["git", "ls-remote", remote_url, f"refs/heads/{source_ref}"],
        cwd=source_repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise GitPublishError(result.stderr.strip() or "could not read source ref")
    actual = result.stdout.split()[0] if result.stdout.strip() else ""
    if actual != expected_source:
        raise GitPublishError(
            f"source ref {source_ref} moved: expected {expected_source}, found {actual or 'missing'}"
        )


def _checkout_remote_branch(work: Path, branch: str) -> bool:
    """Check out the current remote branch, or create an empty orphan branch."""

    found = _git(work, "show-ref", "--verify", f"refs/remotes/origin/{branch}", check=False)
    if found.returncode == 0:
        _git(work, "checkout", "--quiet", "-B", branch, f"origin/{branch}")
        return True

    # A first publication has no remote generated branch yet. Start an orphan
    # branch so source/main history never becomes a parent of generated output.
    _git(work, "checkout", "--quiet", "--orphan", branch)
    _git(work, "rm", "-rf", ".", check=False)
    for child in tuple(work.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    return False


def _publish(
    *,
    source_repo: Path,
    branch: str,
    message: str,
    mutation: Callable[[Path], None],
    remote: str = "origin",
    retries: int = 3,
    source_ref: str | None = None,
    expected_source: str | None = None,
) -> str:
    """Apply one deterministic mutation to a generated branch and push it.

    A failed non-fast-forward is handled by cloning the new remote head and
    applying the same mutation again. No generated branch is ever force-pushed.
    """

    if retries < 1:
        raise GitPublishError("retries must be at least one")
    remote_url = _remote_url(source_repo, remote)
    last_error = ""

    for attempt in range(1, retries + 1):
        # Check freshness before every retry. A source branch can move while a
        # generated-branch race is being retried.
        _assert_source_current(
            source_repo=source_repo,
            remote=remote,
            source_ref=source_ref,
            expected_source=expected_source,
        )
        with tempfile.TemporaryDirectory(prefix="cad-ci-publish-") as tmp:
            work = Path(tmp) / "repo"
            clone = subprocess.run(
                ["git", "clone", "--quiet", "--no-checkout", remote_url, str(work)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if clone.returncode != 0:
                raise GitPublishError(clone.stderr.strip() or "git clone failed")

            _checkout_remote_branch(work, branch)
            _copy_auth_config(source_repo, work)
            _git(work, "config", "user.name", "tool.cad.ci")
            _git(work, "config", "user.email", "tool.cad.ci@users.noreply.github.com")

            mutation(work)
            _git(work, "add", "-A")

            # A repeated cleanup or publication may already match the remote
            # tree. Returning the current head makes the operation idempotent.
            changed = _git(work, "status", "--porcelain").stdout.strip()
            if not changed:
                head = _git(work, "rev-parse", "HEAD", check=False)
                return head.stdout.strip() if head.returncode == 0 else ""

            _git(work, "commit", "--quiet", "-m", message)
            commit = _git(work, "rev-parse", "HEAD").stdout.strip()

            # Check once more after preparing the commit. Expensive mutations
            # must not publish if the source branch moved during preparation.
            _assert_source_current(
                source_repo=source_repo,
                remote=remote,
                source_ref=source_ref,
                expected_source=expected_source,
            )
            push = _git(work, "push", "origin", f"HEAD:refs/heads/{branch}", check=False)
            if push.returncode == 0:
                return commit

            last_error = push.stderr.strip() or push.stdout.strip() or "git push failed"
            # Any branch-head race is retried from a fresh clone. Authentication
            # and policy errors will fail again and are returned after the bound.

    raise GitPublishError(
        f"could not publish {branch} after {retries} attempts: {last_error}"
    )


def publish_build_scope(
    *,
    source_repo: Path,
    candidate: Path,
    scope: str,
    message: str,
    pull_request: int | None = None,
    branch: str = "build",
    remote: str = "origin",
    retries: int = 3,
    source_ref: str | None = None,
    expected_source: str | None = None,
) -> str:
    """Install a prepared main/PR build scope and publish the build branch."""

    return _publish(
        source_repo=source_repo,
        branch=branch,
        message=message,
        remote=remote,
        retries=retries,
        source_ref=source_ref,
        expected_source=expected_source,
        mutation=lambda work: install_scope(
            candidate=candidate,
            store=work,
            scope=scope,
            pull_request=pull_request,
        ),
    )


def publish_build_pr_cleanup(
    *,
    source_repo: Path,
    pull_request: int,
    message: str,
    branch: str = "build",
    remote: str = "origin",
    retries: int = 3,
    source_ref: str | None = None,
    expected_source: str | None = None,
) -> str:
    """Remove one PR build overlay and publish only that scoped cleanup."""

    return _publish(
        source_repo=source_repo,
        branch=branch,
        message=message,
        remote=remote,
        retries=retries,
        source_ref=source_ref,
        expected_source=expected_source,
        mutation=lambda work: remove_pr(store=work, pull_request=pull_request),
    )


def publish_pages(
    *,
    source_repo: Path,
    site: Path,
    message: str,
    pull_request: int | None = None,
    branch: str = "gh-pages",
    remote: str = "origin",
    retries: int = 3,
    source_ref: str | None = None,
    expected_source: str | None = None,
) -> str:
    """Publish either the stable Pages root or one PR preview."""

    if pull_request is None:
        mutation = lambda work: install_stable(site=site, pages_root=work)
    else:
        mutation = lambda work: install_preview(
            site=site,
            pages_root=work,
            pull_request=pull_request,
        )
    return _publish(
        source_repo=source_repo,
        branch=branch,
        message=message,
        remote=remote,
        retries=retries,
        source_ref=source_ref,
        expected_source=expected_source,
        mutation=mutation,
    )


def publish_pages_preview_cleanup(
    *,
    source_repo: Path,
    pull_request: int,
    message: str,
    branch: str = "gh-pages",
    remote: str = "origin",
    retries: int = 3,
    source_ref: str | None = None,
    expected_source: str | None = None,
) -> str:
    """Remove one Pages preview and preserve stable/other preview content."""

    return _publish(
        source_repo=source_repo,
        branch=branch,
        message=message,
        remote=remote,
        retries=retries,
        source_ref=source_ref,
        expected_source=expected_source,
        mutation=lambda work: remove_preview(
            pages_root=work,
            pull_request=pull_request,
        ),
    )
