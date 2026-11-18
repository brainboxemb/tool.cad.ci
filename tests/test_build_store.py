"""Build-store tests for complete baselines, sparse PR overlays and promotion."""

from pathlib import Path
import json
import tempfile
import unittest

from cad_ci.build_store import (
    BuildStoreError,
    install_scope,
    load_manifest,
    prepare_main,
    prepare_overlay,
    promote_overlay,
    remove_pr,
    resolve_view,
)


def write_item(root: Path, path: str, value: str) -> None:
    """Create the smallest complete runner result needed by store tests."""

    item = root / path
    item.mkdir(parents=True)
    (item / "result.txt").write_text(value)
    (item / "item.json").write_text(json.dumps({
        "item": path.replace("/", "-"),
        "status": "pass",
        "input_fingerprint": f"input-{value}",
        "result_fingerprint": f"result-{value}",
    }))


def write_main(root: Path, rows: dict[str, str]) -> None:
    """Create a small valid complete main baseline."""

    for path, value in rows.items():
        write_item(root, path, value)
    manifest = {
        "schema": 1,
        "scope": "main",
        "source_commit": "main-old",
        "items": {
            path: {
                "source_commit": "main-old",
                "input_fingerprint": f"input-{value}",
                "result_fingerprint": f"result-{value}",
            }
            for path, value in rows.items()
        },
    }
    (root / "build.json").write_text(json.dumps(manifest))


class BuildStoreTests(unittest.TestCase):
    def test_prepare_main_bootstraps_complete_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            write_item(candidate, "qualification/item-a", "a")
            write_item(candidate, "qualification/item-b", "b")
            main = root / "main"
            manifest = prepare_main(
                candidate_root=candidate,
                out=main,
                item_paths=["qualification/item-a", "qualification/item-b"],
                source_commit="main-1",
            )
            self.assertEqual(manifest["scope"], "main")
            self.assertEqual(
                set(manifest["items"]),
                {"qualification/item-a", "qualification/item-b"},
            )

    def test_overlay_is_sparse_and_keeps_source_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            write_item(candidate, "qualification/item-a", "new-a")
            write_item(candidate, "qualification/item-b", "new-b")
            overlay = root / "overlay"
            manifest = prepare_overlay(
                candidate_root=candidate,
                out=overlay,
                item_paths=["qualification/item-a"],
                source_commit="head-1",
                pull_request=7,
            )
            self.assertEqual(set(manifest["items"]), {"qualification/item-a"})
            self.assertTrue((overlay / "qualification/item-a/result.txt").is_file())
            self.assertFalse((overlay / "qualification/item-b").exists())

    def test_resolve_overlays_only_selected_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main = root / "main"
            write_main(
                main,
                {
                    "qualification/item-a": "old-a",
                    "qualification/item-b": "old-b",
                },
            )
            candidate = root / "candidate"
            write_item(candidate, "qualification/item-a", "new-a")
            overlay = root / "overlay"
            prepare_overlay(
                candidate_root=candidate,
                out=overlay,
                item_paths=["qualification/item-a"],
                source_commit="head-1",
                pull_request=7,
            )
            resolved = root / "resolved"
            resolve_view(main=main, overlay=overlay, out=resolved)
            self.assertEqual(
                (resolved / "qualification/item-a/result.txt").read_text(),
                "new-a",
            )
            self.assertEqual(
                (resolved / "qualification/item-b/result.txt").read_text(),
                "old-b",
            )

    def test_promotion_preserves_unaffected_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main = root / "main"
            write_main(
                main,
                {
                    "qualification/item-a": "old-a",
                    "qualification/item-b": "old-b",
                },
            )
            candidate = root / "candidate"
            write_item(candidate, "qualification/item-a", "new-a")
            overlay = root / "overlay"
            prepare_overlay(
                candidate_root=candidate,
                out=overlay,
                item_paths=["qualification/item-a"],
                source_commit="head-1",
                pull_request=7,
            )
            promoted = root / "promoted"
            manifest = promote_overlay(
                main=main,
                overlay=overlay,
                out=promoted,
                source_commit="main-new",
            )
            self.assertEqual(
                (promoted / "qualification/item-a/result.txt").read_text(),
                "new-a",
            )
            self.assertEqual(
                (promoted / "qualification/item-b/result.txt").read_text(),
                "old-b",
            )
            self.assertEqual(manifest["source_commit"], "main-new")

    def test_install_and_cleanup_pr_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            write_item(candidate, "qualification/item-a", "new-a")
            overlay = root / "overlay"
            prepare_overlay(
                candidate_root=candidate,
                out=overlay,
                item_paths=["qualification/item-a"],
                source_commit="head-1",
                pull_request=7,
            )
            store = root / "store"
            target = install_scope(
                candidate=overlay,
                store=store,
                scope="pr",
                pull_request=7,
            )
            self.assertEqual(load_manifest(target)["pull_request"], 7)
            self.assertTrue(remove_pr(store=store, pull_request=7))
            self.assertFalse(remove_pr(store=store, pull_request=7))

    def test_rejects_candidate_without_complete_item_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate/qualification/item-a"
            candidate.mkdir(parents=True)
            (candidate / "item.json").write_text(json.dumps({"status": "fail"}))
            with self.assertRaisesRegex(BuildStoreError, "not complete/pass"):
                prepare_overlay(
                    candidate_root=root / "candidate",
                    out=root / "overlay",
                    item_paths=["qualification/item-a"],
                    source_commit="x",
                    pull_request=1,
                )


if __name__ == "__main__":
    unittest.main()
