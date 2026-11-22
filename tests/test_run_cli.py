"""CLI-level checks that tool.cad.ci exposes the released SCons runner."""

from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import json
import io
import tempfile
import unittest
from unittest.mock import patch

from cad_ci_tool.cli import main


def make_repo(root: Path, *, process: bool = True) -> Path:
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
    process_line = "" if process else "process: false\n"
    (case / "ci.yml").write_text(
        "id: case-a\n"
        + process_line
        + "watch: [cases/a/**]\n"
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
    def test_run_forwards_default_and_explicit_jobs_to_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))

            with patch("cad_ci_tool.cli.run_repository") as run:
                self.assertEqual(main(["run", "--repo", str(repo)]), 0)
            self.assertEqual(run.call_args.kwargs["jobs"], 1)

            with patch("cad_ci_tool.cli.run_repository") as run:
                self.assertEqual(
                    main(
                        [
                            "run",
                            "--repo",
                            str(repo),
                            "--jobs",
                            "3",
                        ]
                    ),
                    0,
                )
            self.assertEqual(run.call_args.kwargs["jobs"], 3)

    def test_run_rejects_non_positive_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            for value in ("0", "-1", "no"):
                with self.subTest(value=value):
                    error = io.StringIO()
                    with redirect_stderr(error):
                        with self.assertRaises(SystemExit) as caught:
                            main(
                                [
                                    "run",
                                    "--repo",
                                    str(repo),
                                    "--jobs",
                                    value,
                                ]
                            )
                    self.assertEqual(caught.exception.code, 2)
                    self.assertIn("positive integer", error.getvalue())

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
            self.assertIn("output=unchanged", first.getvalue())
            self.assertNotIn("materialization=", first.getvalue())

            step_evidence = json.loads(
                (
                    repo
                    / "build/cases/a/.cad-ci/steps/build.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(step_evidence["schema"], 4)
            self.assertEqual(step_evidence["action_type"], "command")
            self.assertEqual(step_evidence["output_state"], "UNCHANGED")
            self.assertTrue(step_evidence["action_executed"])
            self.assertIsNotNone(step_evidence["run_started_at"])
            self.assertIsNotNone(step_evidence["run_finished_at"])
            self.assertIsNotNone(step_evidence["started_at"])
            self.assertIsNotNone(step_evidence["finished_at"])
            self.assertNotIn("materialization", step_evidence)

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

            current_evidence = json.loads(
                (
                    repo
                    / "build/cases/a/.cad-ci/steps/build.json"
                ).read_text(encoding="utf-8")
            )
            self.assertFalse(current_evidence["action_executed"])
            self.assertIsNone(current_evidence["started_at"])
            self.assertIsNone(current_evidence["finished_at"])
            self.assertIsNotNone(current_evidence["run_started_at"])
            self.assertIsNotNone(current_evidence["run_finished_at"])

    def test_process_false_is_delegated_to_released_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root, process=False)

            plan = io.StringIO()
            with redirect_stdout(plan):
                self.assertEqual(
                    main(["plan", "--repo", str(repo), "--json"]),
                    0,
                )
            self.assertEqual(json.loads(plan.getvalue()), [])

            error = io.StringIO()
            with redirect_stderr(error):
                self.assertEqual(
                    main(
                        [
                            "run",
                            "--repo",
                            str(repo),
                            "--item",
                            "case-a",
                        ]
                    ),
                    2,
                )
            self.assertIn("item is not processed: case-a", error.getvalue())

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
