"""Tests that tool.cad.ci remains a thin CLI above lib.py.cad.ci."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB_COMMIT = "a68bcd9e3940b21872dea5fc210bcd9a26519ebc"


class LibraryBoundaryTests(unittest.TestCase):
    def test_generic_library_is_not_vendored_in_tool_repository(self):
        self.assertFalse((ROOT / "cad_ci").exists())

    def test_tool_has_only_its_cli_package(self):
        self.assertTrue((ROOT / "cad_ci_tool/cli.py").is_file())
        self.assertTrue((ROOT / "cad_ci_tool/publication_cli.py").is_file())

    def test_pyproject_pins_exact_library_commit(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("brainboxemb-cad-ci-lib", pyproject)
        self.assertIn(LIB_COMMIT, pyproject)
        self.assertIn('cad-ci = "cad_ci_tool.cli:main"', pyproject)

    def test_cli_imports_generic_behavior_from_library(self):
        cli = (ROOT / "cad_ci_tool/cli.py").read_text(encoding="utf-8")
        publication = (
            ROOT / "cad_ci_tool/publication_cli.py"
        ).read_text(encoding="utf-8")
        self.assertIn("from cad_ci.config", cli)
        self.assertIn("from cad_ci.repository.git", cli)
        self.assertIn("from cad_ci.repository.planner", cli)
        self.assertIn("from cad_ci.execution.runner", cli)
        self.assertIn("from cad_ci.config", publication)
        self.assertIn("from cad_ci.repository.git", publication)
        self.assertIn("from cad_ci.repository.planner", publication)
        self.assertIn("from cad_ci.publication.build_store", publication)
        self.assertIn("from cad_ci.publication.git_publish", publication)
        self.assertIn("from cad_ci.publication.pages", publication)

    def test_tool_does_not_implement_builder_resolution(self):
        for path in (
            ROOT / "cad_ci_tool/cli.py",
            ROOT / "cad_ci_tool/publication_cli.py",
            ROOT / "scripts/reusable_ci.py",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("builder.yml", text)
            self.assertNotIn("CAD_CI_BUILDER_PATH", text)

    def test_workflow_helper_only_delegates_durable_state(self):
        helper = (ROOT / "scripts/reusable_ci.py").read_text(encoding="utf-8")
        self.assertIn("from cad_ci.publication.durable import", helper)
        self.assertIn("fetch_durable_scope_state", helper)
        self.assertIn("publish_durable_scope", helper)
        self.assertIn("publish_durable_pages", helper)
        self.assertNotIn("build.json", helper)
        self.assertNotIn("from cad_ci.publication.build_store", helper)
        self.assertNotIn("from cad_ci.publication.pages", helper)
        self.assertNotIn("from cad_ci.publication.git_publish", helper)


if __name__ == "__main__":
    unittest.main()
