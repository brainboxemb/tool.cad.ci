"""Git publication tests using a local bare repository as the remote."""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import cad_ci.git_publish as git_publish

from cad_ci.build_store import prepare_main, prepare_overlay
from cad_ci.git_publish import (
    publish_build_scope,
    publish_pages,
    publish_pages_preview_cleanup,
)
from cad_ci.pages import Page, build_site


def git(cwd: Path, *args: str) -> str:
    """Return stdout from a Git command used by the test setup."""

    return subprocess.check_output(
        ["git", *args],
        cwd=cwd,
        text=True,
    ).strip()


def init_remote(root: Path) -> tuple[Path, Path]:
    """Create a source checkout with a local bare origin/main branch."""

    remote = root / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", str(remote)],
        check=True,
    )
    source = root / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=source,
        check=True,
    )
    (source / "README.md").write_text("source\n")
    subprocess.run(["git", "add", "."], cwd=source, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "source"],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(remote)],
        cwd=source,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "HEAD:main"],
        cwd=source,
        check=True,
    )
    return source, remote


def write_item(root: Path, path: str, value: str) -> None:
    """Write one complete fake runner item result."""

    item = root / path
    item.mkdir(parents=True)
    (item / "result.txt").write_text(value)
    (item / "item.json").write_text(json.dumps({
        "status": "pass",
        "input_fingerprint": f"in-{value}",
        "result_fingerprint": f"out-{value}",
    }))


def branch_file(remote: Path, branch: str, path: str) -> str:
    """Read one file directly from a branch in the bare test remote."""

    return subprocess.check_output(
        [
            "git",
            f"--git-dir={remote}",
            "show",
            f"{branch}:{path}",
        ],
        text=True,
    )


class GitPublishTests(unittest.TestCase):
    def test_build_branch_keeps_independent_pr_scopes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, remote = init_remote(root)

            candidate = root / "candidate"
            write_item(candidate, "qualification/a", "a")
            write_item(candidate, "qualification/b", "b")
            main = root / "main-candidate"
            prepare_main(
                candidate_root=candidate,
                out=main,
                item_paths=["qualification/a", "qualification/b"],
                source_commit="main-1",
            )
            publish_build_scope(
                source_repo=source,
                candidate=main,
                scope="main",
                message="main",
            )

            overlay_a = root / "overlay-a"
            prepare_overlay(
                candidate_root=candidate,
                out=overlay_a,
                item_paths=["qualification/a"],
                source_commit="pr-a",
                pull_request=1,
            )
            publish_build_scope(
                source_repo=source,
                candidate=overlay_a,
                scope="pr",
                pull_request=1,
                message="pr1",
            )

            overlay_b = root / "overlay-b"
            prepare_overlay(
                candidate_root=candidate,
                out=overlay_b,
                item_paths=["qualification/b"],
                source_commit="pr-b",
                pull_request=2,
            )
            publish_build_scope(
                source_repo=source,
                candidate=overlay_b,
                scope="pr",
                pull_request=2,
                message="pr2",
            )

            self.assertEqual(
                branch_file(
                    remote,
                    "build",
                    "pr/1/qualification/a/result.txt",
                ),
                "a",
            )
            self.assertEqual(
                branch_file(
                    remote,
                    "build",
                    "pr/2/qualification/b/result.txt",
                ),
                "b",
            )
            self.assertEqual(
                branch_file(
                    remote,
                    "build",
                    "main/qualification/a/result.txt",
                ),
                "a",
            )

    def test_pages_stable_and_preview_share_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, remote = init_remote(root)
            stable = root / "stable"
            preview = root / "preview"
            build_site(
                out=stable,
                site_title="Demo",
                pages=[Page("index.html", "Home", "<p>stable</p>")],
                provenance={"source": "main"},
            )
            build_site(
                out=preview,
                site_title="Demo",
                pages=[Page("index.html", "Home", "<p>preview</p>")],
                provenance={"source": "pr"},
            )

            publish_pages(
                source_repo=source,
                site=stable,
                message="stable",
            )
            publish_pages(
                source_repo=source,
                site=preview,
                pull_request=3,
                message="preview",
            )
            self.assertIn(
                "stable",
                branch_file(remote, "gh-pages", "index.html"),
            )
            self.assertIn(
                "preview",
                branch_file(
                    remote,
                    "gh-pages",
                    "previews/pr-3/index.html",
                ),
            )

            publish_pages_preview_cleanup(
                source_repo=source,
                pull_request=3,
                message="cleanup",
            )
            files = subprocess.check_output(
                [
                    "git",
                    f"--git-dir={remote}",
                    "ls-tree",
                    "-r",
                    "--name-only",
                    "gh-pages",
                ],
                text=True,
            )
            self.assertIn("index.html", files)
            self.assertNotIn("previews/pr-3/index.html", files)

    def test_refuses_stale_source_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, remote = init_remote(root)
            expected = git(source, "rev-parse", "HEAD")
            stable = root / "stable"
            build_site(
                out=stable,
                site_title="Demo",
                pages=[Page("index.html", "Home", "ok")],
                provenance={},
            )

            # Move remote main after the run's expected source was captured.
            (source / "README.md").write_text("new source\n")
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "move"],
                cwd=source,
                check=True,
            )
            subprocess.run(
                ["git", "push", "-q", "origin", "HEAD:main"],
                cwd=source,
                check=True,
            )

            with self.assertRaisesRegex(
                git_publish.GitPublishError,
                "source ref main moved",
            ):
                publish_pages(
                    source_repo=source,
                    site=stable,
                    message="stale",
                    source_ref="main",
                    expected_source=expected,
                )

    def test_retries_one_rejected_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, remote = init_remote(root)
            stable = root / "stable"
            build_site(
                out=stable,
                site_title="Demo",
                pages=[Page("index.html", "Home", "ok")],
                provenance={},
            )

            real_git = git_publish._git
            rejected = {"done": False}

            def one_rejection(cwd, *args, check=True):
                if args and args[0] == "push" and not rejected["done"]:
                    rejected["done"] = True
                    return subprocess.CompletedProcess(
                        ["git", *args],
                        1,
                        "",
                        "rejected non-fast-forward",
                    )
                return real_git(cwd, *args, check=check)

            with patch.object(
                git_publish,
                "_git",
                side_effect=one_rejection,
            ):
                commit = publish_pages(
                    source_repo=source,
                    site=stable,
                    message="retry",
                    retries=2,
                )
            self.assertTrue(commit)
            self.assertIn(
                "ok",
                branch_file(remote, "gh-pages", "index.html"),
            )


if __name__ == "__main__":
    unittest.main()
