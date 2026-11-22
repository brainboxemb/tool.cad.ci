from pathlib import Path
import tempfile
import unittest

from unittest.mock import patch
from urllib.error import HTTPError

from scripts.publish_release import release_version, publish


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def make_root(self, root: Path, version: str, package_version: str | None = None):
        package_version = package_version or version
        (root / "VERSION").write_text(version + "\n")
        (root / "pyproject.toml").write_text(f'[project]\nversion = "{package_version}"\n')
        (root / "CHANGELOG.md").write_text(f"## {version} - 2026-11-18\n")

    def test_release_version_checks_all_version_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.1.0")
            self.assertEqual(release_version(root), "0.1.0")

    def test_development_version_is_not_releasable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.1.0-dev")
            with self.assertRaisesRegex(ValueError, "not a release version"):
                release_version(root)

    def test_version_text_outside_project_metadata_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            (root / "pyproject.toml").write_text(
                '# version = "0.3.1"\n[project]\nversion = "0.3.0"\n'
            )
            with self.assertRaisesRegex(ValueError, "do not match"):
                release_version(root)

    def test_release_tag_must_be_a_real_heading_not_body_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            (root / "CHANGELOG.md").write_text(
                "## 0.3.0 - earlier\nSee ## 0.3.1 - later\n"
            )
            with self.assertRaisesRegex(ValueError, "no 0.3.1 release heading"):
                release_version(root)

    def test_release_requires_exact_sha_and_canonical_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            for owner_repo, sha in (("owner/repo", "main"), ("owner", "a" * 40)):
                with self.subTest(repo=owner_repo, sha=sha):
                    with self.assertRaises(ValueError):
                        publish(owner_repo, sha, "token", root=root)

    def test_existing_release_is_idempotent_only_at_same_exact_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            with patch("scripts.publish_release._request", side_effect=[
                {"object": {"type": "commit", "sha": "a" * 40}},
                {"tag_name": "v0.3.1"},
            ]) as request:
                result = publish("owner/repo", "a" * 40, "token", root=root)
            self.assertEqual(result, "release already exists: v0.3.1 at " + "a" * 40)
            self.assertEqual(request.call_count, 2)

    def test_existing_tag_on_different_commit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            with patch("scripts.publish_release._request", return_value={
                "object": {"type": "commit", "sha": "b" * 40},
            }) as request:
                with self.assertRaisesRegex(ValueError, "refusing to relabel"):
                    publish("owner/repo", "a" * 40, "token", root=root)
            request.assert_called_once()

    def test_annotated_tag_resolves_to_real_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            with patch("scripts.publish_release._request", side_effect=[
                {"object": {"type": "tag", "sha": "c" * 40}},
                {"object": {"type": "commit", "sha": "a" * 40}},
                {"tag_name": "v0.3.1"},
            ]) as request:
                result = publish("owner/repo", "a" * 40, "token", root=root)
            self.assertIn("a" * 40, result)
            self.assertEqual(request.call_count, 3)

    def test_missing_tag_creates_exact_release(self):
        missing = HTTPError("https://api.github.com", 404, "Not found", {}, None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.3.1")
            with patch("scripts.publish_release._request", side_effect=[
                missing, missing, {"id": 123},
            ]) as request:
                result = publish("owner/repo", "a" * 40, "token", root=root)
            self.assertEqual(result, "published release: v0.3.1 at " + "a" * 40)
            self.assertEqual(request.call_count, 3)
            self.assertEqual(request.call_args.kwargs["data"]["target_commitish"], "a" * 40)

    def test_package_version_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.1.0", "0.1.1")
            with self.assertRaisesRegex(ValueError, "do not match"):
                release_version(root)


if __name__ == "__main__":
    unittest.main()
