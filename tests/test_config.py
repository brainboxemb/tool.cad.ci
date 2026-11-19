from pathlib import Path
import tempfile
import unittest

from cad_ci.config import ConfigError, load_repository


class ConfigTests(unittest.TestCase):
    def test_glob_discovers_item_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [qualification/*]\n")
            for name in ("a", "b"):
                folder = repo / "qualification" / name
                folder.mkdir(parents=True)
                (folder / "ci.yml").write_text(
                    f"id: {name}\nsteps:\n  - id: test\n    run: [python, -c, 'print(1)']\n"
                )
            items = load_repository(repo)
            self.assertEqual(set(items), {"a", "b"})
            self.assertEqual(items["a"].watch, ("qualification/a/**",))

    def test_loads_items_and_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [a, b]\n")
            for name, extra in (("a", ""), ("b", "needs: [a]\n")):
                folder = repo / name
                folder.mkdir()
                (folder / "ci.yml").write_text(
                    f"id: {name}\n{extra}watch: [{name}/**]\nsteps:\n  - id: test\n    run: [python, -c, 'print(1)']\n"
                )
            items = load_repository(repo)
            self.assertEqual(items["b"].needs, ("a",))


    def test_accepts_direct_affected_strategy(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [summary]\n")
            folder = repo / "summary"
            folder.mkdir()
            (folder / "ci.yml").write_text(
                "id: summary\n"
                "strategy: {affected: direct}\n"
                "steps: [{id: collect, run: [python, -c, 'print(1)']}]\n"
            )
            items = load_repository(repo)
            self.assertEqual(items["summary"].affected, "direct")

    def test_rejects_dependency_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [a, b]\n")
            for name, need in (("a", "b"), ("b", "a")):
                folder = repo / name
                folder.mkdir()
                (folder / "ci.yml").write_text(
                    f"id: {name}\nneeds: [{need}]\nsteps:\n  - id: test\n    run: [python, -c, 'print(1)']\n"
                )
            with self.assertRaises(ConfigError):
                load_repository(repo)

    def test_rejects_empty_item_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [qualification/*]\n")
            with self.assertRaisesRegex(ConfigError, "matches no CI folders"):
                load_repository(repo)

    def test_rejects_output_outside_item_build_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [a]\n")
            folder = repo / "a"
            folder.mkdir()
            (folder / "ci.yml").write_text("id: a\nsteps: [{id: test, run: [python, -c, 'print(1)'], outputs: [../escape.txt]}]\n")
            with self.assertRaisesRegex(ConfigError, "output must stay"):
                load_repository(repo)


if __name__ == "__main__":
    unittest.main()
