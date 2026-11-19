"""Tests that tool.cad.ci remains a thin CLI above lib.py.cad.ci."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB_COMMIT = "35f04ab18f529026b29698d5a2c81af9a796919a"


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


if __name__ == "__main__":
    unittest.main()
