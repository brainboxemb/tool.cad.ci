"""Tests for declared directory outputs and recursive reuse checks."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from cad_ci.config import load_repository
from cad_ci.runner import RunError, run_item
from cad_ci.state import sha256_file, sha256_output


class DirectoryOutputTests(unittest.TestCase):
    def make_repo(self, root: Path) -> dict:
        """Create one item whose step owns a nested output directory."""

        (root / "cad-ci.yml").write_text(
            "schema: 1\nitems: [item]\n",
            encoding="utf-8",
        )
        item = root / "item"
        item.mkdir()
        (item / "input.txt").write_text("one\n", encoding="utf-8")
        (item / "build.py").write_text(
            "import os\n"
            "from pathlib import Path\n"
            "item = Path(__file__).parent\n"
            "out = Path(os.environ['CAD_CI_OUTPUT']) / 'bundle'\n"
            "(out / 'nested').mkdir(parents=True, exist_ok=True)\n"
            "(out / 'a.txt').write_text(item.joinpath('input.txt').read_text())\n"
            "(out / 'nested' / 'b.txt').write_text('nested\\n')\n",
            encoding="utf-8",
        )
        (item / "ci.yml").write_text(
            "id: item\n"
            "watch: [item/**]\n"
            "steps:\n"
            "  - id: build\n"
            "    run: [python, build.py]\n"
            "    outputs: [bundle]\n",
            encoding="utf-8",
        )
        return load_repository(root)

    def test_directory_output_is_reused_while_tree_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            items = self.make_repo(repo)

            first = run_item(repo, items["item"], items)
            second = run_item(repo, items["item"], items)

            self.assertEqual(first, [("build", "ran")])
            self.assertEqual(second, [("build", "reused")])

    def test_changing_nested_file_invalidates_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            items = self.make_repo(repo)
            run_item(repo, items["item"], items)

            nested = repo / "build/item/bundle/nested/b.txt"
            nested.write_text("changed\n", encoding="utf-8")
            events = run_item(repo, items["item"], items)

            self.assertEqual(events, [("build", "ran")])
            self.assertEqual(nested.read_text(encoding="utf-8"), "nested\n")

    def test_missing_directory_output_reruns_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            items = self.make_repo(repo)
            run_item(repo, items["item"], items)

            bundle = repo / "build/item/bundle"
            for child in sorted(bundle.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            bundle.rmdir()

            self.assertEqual(
                run_item(repo, items["item"], items),
                [("build", "ran")],
            )

    def test_regular_file_hash_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.txt"
            path.write_text("same\n", encoding="utf-8")
            self.assertEqual(sha256_output(path), sha256_file(path))

    @unittest.skipIf(os.name == "nt", "Windows symlink creation may require privileges")
    def test_symlink_inside_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            items = self.make_repo(repo)
            outside = repo / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")

            item = repo / "item"
            (item / "build.py").write_text(
                "import os\n"
                "from pathlib import Path\n"
                "out = Path(os.environ['CAD_CI_OUTPUT']) / 'bundle'\n"
                "out.mkdir(parents=True, exist_ok=True)\n"
                f"(out / 'link.txt').symlink_to({str(outside)!r})\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                RunError,
                "contains a symlink",
            ):
                run_item(repo, items["item"], items)


if __name__ == "__main__":
    unittest.main()
