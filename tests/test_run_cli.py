"""CLI-level checks that tool.cad.ci exposes the released SCons runner."""

from contextlib import redirect_stdout
from pathlib import Path
import io
import tempfile
import unittest

from cad_ci_tool.cli import main


def make_repo(root: Path) -> Path:
    """Create one small two-step consumer repository."""

    repo = root / "repo"
    repo.mkdir()
    (repo / "cad-ci.yml").write_text(
        "schema: 1\nitems: [cases/*]\n",
        encoding="utf-8",
    )
    case = repo / "cases" / "a"
    case.mkdir(parents=True)
    (case / "input.txt").write_text("one\n", encoding="utf-8")
    (case / "build.py").write_text(
        """import os
from pathlib import Path
out = Path(os.environ["CAD_CI_OUTPUT"])
out.mkdir(parents=True, exist_ok=True)
(out / "built.txt").write_text(Path(__file__).with_name("input.txt").read_text())
""",
        encoding="utf-8",
    )
    (case / "verify.py").write_text(
        """import os
from pathlib import Path
out = Path(os.environ["CAD_CI_OUTPUT"])
assert (out / "built.txt").read_text()
(out / "verified.txt").write_text("ok\\n")
""",
        encoding="utf-8",
    )
    (case / "ci.yml").write_text(
        "id: case-a\n"
        "watch: [cases/a/**]\n"
        "steps:\n"
        "  - id: build\n"
        "    inputs: [cases/a/input.txt, cases/a/build.py]\n"
        "    run: [python, build.py]\n"
        "    outputs: [built.txt]\n"
        "  - id: verify\n"
        "    inputs: [cases/a/verify.py]\n"
        "    run: [python, verify.py]\n"
        "    outputs: [verified.txt]\n",
        encoding="utf-8",
    )
    return repo


class RunCliTests(unittest.TestCase):
    def test_run_uses_released_scons_engine_and_reuses_current_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)

            first = io.StringIO()
            with redirect_stdout(first):
                self.assertEqual(
                    main(["run", "--repo", str(repo)]),
                    0,
                )
            self.assertIn("built: case-a:build", first.getvalue())
            self.assertTrue((repo / "build/cases/a/built.txt").is_file())
            self.assertTrue((repo / "build/cases/a/verified.txt").is_file())
            self.assertTrue(
                (repo / "build/cases/a/.cad-ci/item.json").is_file()
            )

            second = io.StringIO()
            with redirect_stdout(second):
                self.assertEqual(
                    main(["run", "--repo", str(repo)]),
                    0,
                )
            self.assertIn("current: case-a:build", second.getvalue())
            self.assertIn("current: case-a:verify", second.getvalue())

    def test_exact_step_is_forwarded_to_library_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)
            self.assertEqual(main(["run", "--repo", str(repo)]), 0)

            stream = io.StringIO()
            with redirect_stdout(stream):
                self.assertEqual(
                    main(
                        [
                            "run",
                            "--repo",
                            str(repo),
                            "--item",
                            "case-a",
                            "--step",
                            "build",
                        ]
                    ),
                    0,
                )
            self.assertIn("built: case-a:build", stream.getvalue())
            self.assertFalse(
                (repo / "build/cases/a/.cad-ci/item.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
