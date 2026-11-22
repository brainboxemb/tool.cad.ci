"""Tests that tool.cad.ci remains a thin CLI above lib.py.cad.ci."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB_COMMIT = "64656db8df528a5c0de799e62c0f028fd0133486"


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
        for module in ("config", "git", "planner", "runner"):
            self.assertIn(f"from cad_ci.{module}", cli)
        for module in ("config", "build_store", "git_publish", "pages"):
            self.assertIn(f"from cad_ci.{module}", publication)

    def test_tool_does_not_implement_builder_resolution(self):
        for path in (
            ROOT / "cad_ci_tool/cli.py",
            ROOT / "cad_ci_tool/publication_cli.py",
            ROOT / "scripts/reusable_ci.py",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("builder.yml", text)
            self.assertNotIn("CAD_CI_BUILDER_PATH", text)

    def test_workflow_helper_does_not_own_durable_state(self):
        helper = (ROOT / "scripts/reusable_ci.py").read_text(encoding="utf-8")
        self.assertNotIn("cad_ci.durable", helper)
        self.assertNotIn("build.json", helper)
        self.assertNotIn("durable-resolve", helper)
        self.assertNotIn("durable-publish", helper)


if __name__ == "__main__":
    unittest.main()
