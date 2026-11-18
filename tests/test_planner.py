from pathlib import Path
import tempfile
import unittest

from cad_ci.config import load_repository
from cad_ci.planner import affected_items, build_plan


class PlannerTests(unittest.TestCase):
    def make_repo(self, root: Path):
        (root / "cad-ci.yml").write_text("schema: 1\nitems: [lib, example, qa, qb]\n")
        configs = {
            "lib": "id: lib\nwatch: [src/**, lib/**]\nsteps: [{id: test, run: [python, -c, 'print(1)']}]\n",
            "example": "id: example\nneeds: [lib]\nwatch: [example/**]\nsteps: [{id: test, run: [python, -c, 'print(1)']}]\n",
            "qa": "id: qa\nneeds: [example]\nwatch: [qa/**]\nsteps: [{id: test, run: [python, -c, 'print(1)']}]\n",
            "qb": "id: qb\nneeds: [example]\nwatch: [qb/**]\nsteps: [{id: test, run: [python, -c, 'print(1)']}]\n",
        }
        for name, config in configs.items():
            folder = root / name
            folder.mkdir(parents=True)
            (folder / "ci.yml").write_text(config)

    def test_one_qualification_change_does_not_select_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            selected = affected_items(items, ("qa/model.txt",))
            self.assertEqual(selected, {"qa"})
            plan = build_plan(items, selected)
            self.assertEqual([x.item.id for x in plan], ["lib", "example", "qa"])
            self.assertEqual([x.reason for x in plan], ["dependency", "dependency", "affected"])

    def test_shared_library_change_selects_dependants(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            items = load_repository(repo)
            selected = affected_items(items, ("src/core.py",))
            self.assertEqual(selected, {"lib", "example", "qa", "qb"})

    def test_always_item_is_selected_without_path_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo)
            path = repo / "lib" / "ci.yml"
            path.write_text(path.read_text().replace("watch: [src/**, lib/**]", "strategy: {affected: always}\nwatch: [src/**, lib/**]"))
            items = load_repository(repo)
            selected = affected_items(items, ("README.md",))
            self.assertEqual(selected, {"lib", "example", "qa", "qb"})


if __name__ == "__main__":
    unittest.main()
