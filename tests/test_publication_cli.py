"""CLI checks for preparing durable SCons-backed build scopes."""

from pathlib import Path
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from cad_ci.scons.engine import ENGINE_SCHEMA as SCONS_ENGINE_SCHEMA
from cad_ci_tool.cli import main


def write_config(
    root: Path,
    path: str,
    item_id: str,
    *,
    needs: tuple[str, ...] = (),
    process: bool = True,
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
        f"process: {'true' if process else 'false'}\n"
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
                "schema": 2,
                "engine": "scons",
                "engine_schema": SCONS_ENGINE_SCHEMA,
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

    def test_prepare_main_uses_library_full_run_process_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "cad-ci.yml").write_text(
                "schema: 1\nitems: [cases/*]\n",
                encoding="utf-8",
            )
            write_config(repo, "cases/active", "active-case", process=True)
            write_config(repo, "cases/parked", "parked-case", process=False)

            candidate = root / "candidate"
            write_candidate(candidate, "cases/active", "active-case", "active")

            out = root / "main"
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
                        str(out),
                        "--source-commit",
                        "main-processed",
                    ]
                ),
                0,
            )

            self.assertTrue((out / "cases/active/result.txt").is_file())
            self.assertFalse((out / "cases/parked").exists())
            manifest = json.loads((out / "build.json").read_text(encoding="utf-8"))
            self.assertEqual(tuple(manifest["items"]), ("cases/active",))

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

    def test_update_main_passes_sparse_replacements_and_current_processed_items(self):
        """The CLI exposes both library item sets without owning deletion logic."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "cad-ci.yml").write_text(
                "schema: 1\nitems: [cases/*]\n",
                encoding="utf-8",
            )
            write_config(repo, "cases/a", "case-a", process=True)
            write_config(repo, "cases/b", "case-b", process=True)
            write_config(repo, "cases/parked", "parked", process=False)

            with patch(
                "cad_ci_tool.publication_cli.update_main",
                return_value={},
            ) as update:
                result = main(
                    [
                        "build",
                        "update-main",
                        "--repo",
                        str(repo),
                        "--candidate-root",
                        str(root / "candidate"),
                        "--main",
                        str(root / "main"),
                        "--out",
                        str(root / "updated"),
                        "--source-commit",
                        "main-new",
                        "--changed",
                        "cases/a/model.py",
                    ]
                )

            self.assertEqual(result, 0)
            call = update.call_args.kwargs
            self.assertEqual(
                tuple(item.id for item in call["items"]),
                ("case-a",),
            )
            self.assertEqual(
                tuple(item.id for item in call["current_items"]),
                ("case-a", "case-b"),
            )
            self.assertEqual(call["source_commit"], "main-new")

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

    def test_prepare_named_defaults_to_complete_processed_item_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)
            candidate = make_candidates(root)
            out = root / "dev-cad"

            self.assertEqual(
                main(
                    [
                        "build",
                        "prepare-named",
                        "--repo",
                        str(repo),
                        "--candidate-root",
                        str(candidate),
                        "--out",
                        str(out),
                        "--source-commit",
                        "dev-1",
                        "--name",
                        "dev_cad",
                    ]
                ),
                0,
            )

            manifest = json.loads(
                (out / "build.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["scope"], "named")
            self.assertEqual(manifest["name"], "dev_cad")
            self.assertEqual(
                tuple(manifest["items"]),
                ("cases/a", "cases/b"),
            )

    def test_update_named_forwards_sparse_and_current_item_sets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root)

            with patch(
                "cad_ci_tool.publication_cli.update_named",
                return_value={},
            ) as update:
                result = main(
                    [
                        "build",
                        "update-named",
                        "--repo",
                        str(repo),
                        "--candidate-root",
                        str(root / "candidate"),
                        "--named",
                        str(root / "dev_cad"),
                        "--out",
                        str(root / "updated"),
                        "--source-commit",
                        "dev-new",
                        "--name",
                        "dev_cad",
                        "--changed",
                        "cases/a/model.py",
                    ]
                )

            self.assertEqual(result, 0)
            call = update.call_args.kwargs
            self.assertEqual(
                tuple(item.id for item in call["items"]),
                ("case-a",),
            )
            self.assertEqual(
                tuple(item.id for item in call["current_items"]),
                ("case-a", "case-b"),
            )
            self.assertEqual(call["name"], "dev_cad")
            self.assertEqual(call["source_commit"], "dev-new")

    def test_publish_named_build_scope_forwards_name_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            stream = io.StringIO()

            with patch(
                "cad_ci_tool.publication_cli.publish_build_scope",
                return_value="build123",
            ) as publish, redirect_stdout(stream):
                result = main(
                    [
                        "publish",
                        "build",
                        "--repo",
                        str(repo),
                        "--candidate",
                        str(root / "candidate"),
                        "--scope",
                        "named",
                        "--scope-name",
                        "dev_ci",
                        "--message",
                        "publish dev_ci",
                    ]
                )

            self.assertEqual(result, 0)
            call = publish.call_args.kwargs
            self.assertEqual(call["scope"], "named")
            self.assertEqual(call["scope_name"], "dev_ci")
            self.assertIsNone(call["pull_request"])
            self.assertEqual(stream.getvalue().strip(), "build123")

    def test_publish_pages_forwards_named_and_stable_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()

            with patch(
                "cad_ci_tool.publication_cli.publish_pages",
                return_value="page123",
            ) as publish:
                self.assertEqual(
                    main(
                        [
                            "publish",
                            "pages",
                            "--repo",
                            str(repo),
                            "--site",
                            str(root / "site"),
                            "--name",
                            "dev_cad",
                            "--message",
                            "preview",
                        ]
                    ),
                    0,
                )
            named_call = publish.call_args.kwargs
            self.assertEqual(named_call["name"], "dev_cad")
            self.assertEqual(named_call["preserve_subtrees"], [])

            with patch(
                "cad_ci_tool.publication_cli.publish_pages",
                return_value="page456",
            ) as publish:
                self.assertEqual(
                    main(
                        [
                            "publish",
                            "pages",
                            "--repo",
                            str(repo),
                            "--site",
                            str(root / "site"),
                            "--preserve-subtree",
                            "dev_cad",
                            "--preserve-subtree",
                            "dev_ci",
                            "--message",
                            "stable",
                        ]
                    ),
                    0,
                )
            stable_call = publish.call_args.kwargs
            self.assertIsNone(stable_call["name"])
            self.assertEqual(
                stable_call["preserve_subtrees"],
                ["dev_cad", "dev_ci"],
            )

    def test_public_counts_reject_zero_negative_and_non_numeric(self):
        """Every public PR identifier and publish retry count must be > 0."""

        from contextlib import redirect_stderr

        cases = (
            ["build", "remove-pr", "--store", "build", "--pull-request", "0"],
            ["pages", "remove-preview", "--pages-root", "site", "--pull-request", "-1"],
            ["publish", "pages-cleanup", "--message", "cleanup", "--pull-request", "abc"],
            ["publish", "pages", "--site", "site", "--message", "pages", "--retries", "0"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(arguments)
                self.assertEqual(error.exception.code, 2)



if __name__ == "__main__":
    unittest.main()
