"""CLI-level checks for preparing durable build scopes from consumer item IDs."""

from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io

from cad_ci_tool.cli import main


def write_item(
    root: Path,
    path: str,
    item_id: str,
    value: str,
) -> None:
    """Write a minimal configured item and fake complete runner result."""

    item = root / path
    item.mkdir(parents=True)
    (item / "ci.yml").write_text(
        f"id: {item_id}\n"
        "steps:\n"
        "  - id: test\n"
        "    run: [python, -c, 'print(1)']\n"
    )
    (item / "result.txt").write_text(value)
    (item / "item.json").write_text(json.dumps({
        "status": "pass",
        "input_fingerprint": f"in-{value}",
        "result_fingerprint": f"out-{value}",
    }))


class PublicationCliTests(unittest.TestCase):
    def test_prepare_main_defaults_to_all_items_and_pr_uses_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "cad-ci.yml").write_text(
                "schema: 1\nitems: [qualification/*]\n"
            )
            candidate = root / "candidate"
            write_item(
                repo,
                "qualification/a",
                "qa",
                "source-a",
            )
            write_item(
                repo,
                "qualification/b",
                "qb",
                "source-b",
            )

            # Candidate output mirrors item source paths. Only runner state and
            # output are needed; the source ci.yml stays in the consumer repo.
            write_item(
                candidate,
                "qualification/a",
                "qa",
                "a",
            )
            write_item(
                candidate,
                "qualification/b",
                "qb",
                "b",
            )

            main_out = root / "main"
            pr_out = root / "pr"
            self.assertEqual(
                main([
                    "build",
                    "prepare-main",
                    "--repo",
                    str(repo),
                    "--candidate-root",
                    str(candidate),
                    "--out",
                    str(main_out),
                    "--source-commit",
                    "main-1",
                ]),
                0,
            )
            self.assertEqual(
                main([
                    "build",
                    "prepare-pr",
                    "--repo",
                    str(repo),
                    "--candidate-root",
                    str(candidate),
                    "--out",
                    str(pr_out),
                    "--source-commit",
                    "pr-1",
                    "--pull-request",
                    "4",
                    "--items",
                    "qa",
                ]),
                0,
            )
            self.assertTrue(
                (main_out / "qualification/b/result.txt").is_file()
            )
            self.assertFalse((pr_out / "qualification/b").exists())

    def test_prepare_pr_can_derive_selection_from_changed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "cad-ci.yml").write_text(
                "schema: 1\nitems: [qualification/*]\n"
            )
            candidate = root / "candidate"
            write_item(repo, "qualification/a", "qa", "source-a")
            write_item(repo, "qualification/b", "qb", "source-b")
            write_item(candidate, "qualification/a", "qa", "a")
            write_item(candidate, "qualification/b", "qb", "b")

            out = root / "pr"
            self.assertEqual(
                main([
                    "build",
                    "prepare-pr",
                    "--repo",
                    str(repo),
                    "--candidate-root",
                    str(candidate),
                    "--out",
                    str(out),
                    "--source-commit",
                    "pr-2",
                    "--pull-request",
                    "5",
                    "--changed",
                    "qualification/a/model.py",
                ]),
                0,
            )
            self.assertTrue((out / "qualification/a/result.txt").is_file())
            self.assertFalse((out / "qualification/b").exists())

    def test_selected_build_requires_selection_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "cad-ci.yml").write_text(
                "schema: 1\nitems: [qualification/*]\n"
            )
            candidate = root / "candidate"
            write_item(repo, "qualification/a", "qa", "source-a")
            write_item(candidate, "qualification/a", "qa", "a")

            self.assertEqual(
                main([
                    "build",
                    "prepare-pr",
                    "--repo",
                    str(repo),
                    "--candidate-root",
                    str(candidate),
                    "--out",
                    str(root / "pr"),
                    "--source-commit",
                    "pr-3",
                    "--pull-request",
                    "6",
                ]),
                2,
            )

    def test_build_fetch_delegates_to_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            out = root / "generated"
            stream = io.StringIO()

            with patch(
                "cad_ci_tool.publication_cli.materialize_generated_branch",
                return_value="abc123",
            ) as fetch, redirect_stdout(stream):
                result = main([
                    "build",
                    "fetch",
                    "--repo",
                    str(repo),
                    "--out",
                    str(out),
                ])

            self.assertEqual(result, 0)
            fetch.assert_called_once_with(
                source_repo=repo.resolve(),
                branch="build",
                out=out,
                remote="origin",
            )
            self.assertEqual(stream.getvalue().strip(), "abc123")


if __name__ == "__main__":
    unittest.main()
