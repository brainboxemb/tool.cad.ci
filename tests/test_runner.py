from pathlib import Path
import json
import tempfile
import unittest

from cad_ci.config import load_repository
from cad_ci.runner import RunError, run_item


class RunnerTests(unittest.TestCase):
    def make_repo(self, root: Path):
        (root / "cad-ci.yml").write_text("schema: 1\nitems: [item]\n")
        item = root / "item"
        item.mkdir()
        (item / "input.txt").write_text("one\n")
        (item / "build.py").write_text(
            "import os, pathlib\nout=pathlib.Path(os.environ['CAD_CI_OUTPUT'])\nout.mkdir(parents=True, exist_ok=True)\n(out/'built.txt').write_text((pathlib.Path(__file__).parent/'input.txt').read_text())\n"
        )
        (item / "verify.py").write_text(
            "import os, pathlib\nout=pathlib.Path(os.environ['CAD_CI_OUTPUT'])\nassert (out/'built.txt').read_text().strip()\n(out/'verified.txt').write_text('ok\\n')\n"
        )
        (item / "ci.yml").write_text(
            "id: item\nwatch: [item/**]\nsteps:\n"
            "  - id: build\n    run: [python, build.py]\n    outputs: [built.txt]\n"
            "  - id: verify\n    run: [python, verify.py]\n    outputs: [verified.txt]\n"
        )

    def test_full_run_then_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            first = run_item(repo, items["item"], items)
            second = run_item(repo, items["item"], items)
            self.assertEqual(first, [("build", "ran"), ("verify", "ran")])
            self.assertEqual(second, [("build", "reused"), ("verify", "reused")])

    def test_exact_step_requires_current_earlier_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            with self.assertRaisesRegex(RunError, "earlier step build"):
                run_item(repo, items["item"], items, step="verify")
            run_item(repo, items["item"], items)
            events = run_item(repo, items["item"], items, step="verify")
            self.assertEqual(events, [("verify", "ran")])

    def test_changed_input_invalidates_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            run_item(repo, items["item"], items)
            (repo / "item" / "input.txt").write_text("two\n")
            items = load_repository(repo)
            events = run_item(repo, items["item"], items)
            self.assertEqual(events, [("build", "ran"), ("verify", "ran")])

    def test_missing_declared_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            path = repo / "item" / "ci.yml"
            path.write_text(path.read_text().replace("outputs: [built.txt]", "outputs: [missing.txt]"))
            items = load_repository(repo)
            with self.assertRaisesRegex(RunError, "declared output"):
                run_item(repo, items["item"], items)

    def test_dependency_output_change_invalidates_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "cad-ci.yml").write_text("schema: 1\nitems: [dep, item]\n")
            dep = repo / "dep"
            dep.mkdir()
            (dep / "run.py").write_text("import os, pathlib\nout=pathlib.Path(os.environ['CAD_CI_OUTPUT']); out.mkdir(parents=True, exist_ok=True); (out/'dep.txt').write_text('one')\n")
            (dep / "ci.yml").write_text("id: dep\nwatch: [dep/**]\nsteps: [{id: build, run: [python, run.py], outputs: [dep.txt]}]\n")
            item = repo / "item"
            item.mkdir()
            (item / "run.py").write_text("import os, pathlib\nout=pathlib.Path(os.environ['CAD_CI_OUTPUT']); out.mkdir(parents=True, exist_ok=True); (out/'item.txt').write_text('ok')\n")
            (item / "ci.yml").write_text("id: item\nneeds: [dep]\nwatch: [item/**]\nsteps: [{id: build, run: [python, run.py], outputs: [item.txt]}]\n")
            items = load_repository(repo)
            run_item(repo, items["dep"], items)
            run_item(repo, items["item"], items)
            (repo / "build" / "dep" / "dep.txt").write_text("changed")
            with self.assertRaisesRegex(RunError, "current result for dep"):
                run_item(repo, items["item"], items)

    def test_from_reruns_from_named_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            run_item(repo, items["item"], items)
            events = run_item(repo, items["item"], items, start="verify")
            self.assertEqual(events, [("verify", "ran")])

    def test_until_stops_after_named_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            events = run_item(repo, items["item"], items, until="build")
            self.assertEqual(events, [("build", "ran")])
            self.assertFalse((repo / "build" / "item" / "item.json").exists())


if __name__ == "__main__":
    unittest.main()
