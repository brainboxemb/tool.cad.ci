from pathlib import Path
import tempfile
import unittest

from scripts.publish_release import release_version


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def make_root(self, root: Path, version: str, package_version: str | None = None):
        package_version = package_version or version
        (root / "VERSION").write_text(version + "\n")
        (root / "pyproject.toml").write_text(f'version = "{package_version}"\n')
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

    def test_package_version_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root, "0.1.0", "0.1.1")
            with self.assertRaisesRegex(ValueError, "do not match"):
                release_version(root)


if __name__ == "__main__":
    unittest.main()
