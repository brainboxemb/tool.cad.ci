"""Pages-framework tests for site structure, previews and stable replacement."""

from pathlib import Path
import json
import tempfile
import unittest

from cad_ci.pages import (
    Page,
    PagesError,
    build_site,
    install_preview,
    install_stable,
    remove_preview,
)


class PagesTests(unittest.TestCase):
    def make_site(self, root: Path, label: str) -> Path:
        """Build one tiny site with a consumer-owned stylesheet."""

        site = root / label
        style = root / f"{label}.css"
        style.write_text("body { font-family: sans-serif; }\n")
        build_site(
            out=site,
            site_title="Demo",
            pages=[
                Page("index.html", "Home", f"<p>{label}</p>"),
                Page("guide/index.html", "Guide", "<p>Guide</p>"),
            ],
            provenance={
                "source_commit": label,
                "build_commit": "build-1",
            },
            stylesheet_source=style,
            base_path="/demo",
        )
        return site

    def test_framework_builds_navigation_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = self.make_site(root, "main")
            html = (site / "index.html").read_text()
            self.assertIn("<nav>", html)
            self.assertIn("/demo/guide/index.html", html)
            self.assertEqual(
                json.loads((site / "provenance.json").read_text())["source_commit"],
                "main",
            )

    def test_preview_does_not_change_stable_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "pages"
            pages.mkdir()
            stable = self.make_site(root, "stable")
            install_stable(site=stable, pages_root=pages)
            preview = self.make_site(root, "preview")
            install_preview(site=preview, pages_root=pages, pull_request=9)
            self.assertIn("stable", (pages / "index.html").read_text())
            self.assertIn(
                "preview",
                (pages / "previews/pr-9/index.html").read_text(),
            )

    def test_stable_update_preserves_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "pages"
            pages.mkdir()
            install_stable(
                site=self.make_site(root, "stable-1"),
                pages_root=pages,
            )
            install_preview(
                site=self.make_site(root, "preview"),
                pages_root=pages,
                pull_request=9,
            )
            install_stable(
                site=self.make_site(root, "stable-2"),
                pages_root=pages,
            )
            self.assertIn("stable-2", (pages / "index.html").read_text())
            self.assertIn(
                "preview",
                (pages / "previews/pr-9/index.html").read_text(),
            )

    def test_preview_cleanup_is_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "pages"
            pages.mkdir()
            site = self.make_site(root, "preview")
            install_preview(site=site, pages_root=pages, pull_request=9)
            install_preview(site=site, pages_root=pages, pull_request=10)
            self.assertTrue(remove_preview(pages_root=pages, pull_request=9))
            self.assertTrue(
                (pages / "previews/pr-10/index.html").is_file()
            )

    def test_rejects_page_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PagesError, "unsafe page path"):
                build_site(
                    out=Path(tmp) / "site",
                    site_title="Demo",
                    pages=[Page("../x.html", "X", "")],
                    provenance={},
                )


if __name__ == "__main__":
    unittest.main()
