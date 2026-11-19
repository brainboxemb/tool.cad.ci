"""CLI checks for preparing durable SCons-backed build scopes."""

from pathlib import Path
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from cad_ci_tool.cli import main


def write_config(
    root: Path,
    path: str,
    item_id: str,
    *,
    needs: tuple[str, ...] = (),
) -> None:
    """Write one source item configuration used by build-store validation."""

    folder = root / path
    folder.mkdir(parents=True)
    needs_yaml = (
        "needs:\n" + "".join(f"  - {value}\n" for value in needs)
        if needs
        else ""
    )
    (folder / "ci.yml").write_text(
        f"id: {item_id}\n"
        f"{needs_yaml}"
        "steps:\n"
        "  - id: test\n"
        "    run: [python, -c, 'print(1)']\n"
        "    outputs: [result.txt]\n",
        encoding="utf-8",
    )


def write_candidate(
    root: Path,
    path: str,
    item_id: str,
    value: str,
) -> None:
    """Write candidate output plus complete SCons public evidence."""

    folder = root / path
    folder.mkdir(parents=True)
    (folder / "result.txt").write_text(value, encoding="utf-8")
    evidence = folder / ".cad-ci" / "item.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(
        json.dumps(
            {
                "schema": 1,
                "engine": "scons",
                "engine_schema": 1,
                "item": item_id,
                "status": "pass",
                "final_step": "test",
                "final_target_spec_digest": f"spec-{value}",
                "final_bundle_sha256": f"bundle-{value}",
            }
        ),
        encoding="utf-8",
    )


def make_repo(root: Path, *, dependency: bool = False) -> Path:
    """Create two generic configured cases."""

    repo = root / "repo"
    repo.mkdir()
    (repo / "cad-ci.yml").write_text(
        "schema: 1\nitems: [cases/*]\n",
        encoding="utf-8",
    )
    write_config(repo, "cases/a", "case-a")
    write_config(
        repo,
        "cases/b",
        "case-b",
        needs=("case-a",) if dependency else (),
    )
    return repo


def make_candidates(root: Path) -> Path:
    """Create matching candidate output for both configured cases."""

    candidate = root / "candidate"
    write_candidate(candidate, "cases/a", "case-a", "a")
    write_candidate(candidate, "cases/b", "case-b", "b")
    return candidate


class PublicationCliTests(unittest.TestCase):
    def test_prepare_main_defaults_to_all_items_and_pr_uses_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)
            candidate = make_candidates(root)

            main_out = root / "main"
            pr_out = root / "pr"
            self.assertEqual(
                main(
                    [
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
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
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
                        "case-a",
                    ]
                ),
                0,
            )
            self.assertTrue((main_out / "cases/b/result.txt").is_file())
            self.assertTrue((pr_out / "cases/a/result.txt").is_file())
            self.assertFalse((pr_out / "cases/b").exists())

    def test_prepare_pr_can_derive_selection_from_changed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)
            candidate = make_candidates(root)

            out = root / "pr"
            self.assertEqual(
                main(
                    [
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
                        "cases/a/model.py",
                    ]
                ),
                0,
            )
            self.assertTrue((out / "cases/a/result.txt").is_file())
            self.assertFalse((out / "cases/b").exists())

    def test_sparse_overlay_does_not_add_runtime_dependencies(self):
        """Explicit consumer scope stays sparse even though SCons needs case-a."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root, dependency=True)
            candidate = make_candidates(root)

            out = root / "pr"
            self.assertEqual(
                main(
                    [
                        "build",
                        "prepare-pr",
                        "--repo",
                        str(repo),
                        "--candidate-root",
                        str(candidate),
                        "--out",
                        str(out),
                        "--source-commit",
                        "pr-3",
                        "--pull-request",
                        "6",
                        "--items",
                        "case-b",
                    ]
                ),
                0,
            )
            self.assertTrue((out / "cases/b/result.txt").is_file())
            self.assertFalse((out / "cases/a").exists())

    def test_selected_build_requires_selection_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)
            candidate = make_candidates(root)

            self.assertEqual(
                main(
                    [
                        "build",
                        "prepare-pr",
                        "--repo",
                        str(repo),
                        "--candidate-root",
                        str(candidate),
                        "--out",
                        str(root / "pr"),
                        "--source-commit",
                        "pr-4",
                        "--pull-request",
                        "7",
                    ]
                ),
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
                result = main(
                    [
                        "build",
                        "fetch",
                        "--repo",
                        str(repo),
                        "--out",
                        str(out),
                    ]
                )

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
