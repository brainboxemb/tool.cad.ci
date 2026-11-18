#!/usr/bin/env python3
"""Build the tool.cad.ci documentation site with the library's own framework."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import mistune

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cad_ci.pages import Page, build_site


DOCS = (
    ("index.html", "Overview", ROOT / "README.md"),
    (
        "requirements/index.html",
        "Requirements",
        ROOT / "docs" / "requirements.md",
    ),
    (
        "consumer/index.html",
        "Consumer setup",
        ROOT / "docs" / "consumer.md",
    ),
    (
        "build-pages/index.html",
        "Build output and Pages",
        ROOT / "docs" / "build-pages.md",
    ),
)


def page(path: str, title: str, source: Path) -> Page:
    """Render one Markdown document to a framework Page object."""

    renderer = mistune.create_markdown(plugins=("table",))
    body = renderer(source.read_text(encoding="utf-8"))
    return Page(path=path, title=title, body_html=body)


def build(out: Path, *, source_commit: str, base_path: str) -> None:
    """Build the complete documentation site and record its source commit."""

    build_site(
        out=out,
        site_title="tool.cad.ci",
        pages=[page(*entry) for entry in DOCS],
        provenance={
            "schema": 1,
            "source_commit": source_commit,
            "generator": "tool.cad.ci",
        },
        stylesheet_source=ROOT / "site" / "site.css",
        base_path=base_path,
    )


def main() -> int:
    """Parse site build arguments used by local runs and GitHub Actions."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--base-path", default="/tool.cad.ci")
    args = parser.parse_args()
    build(
        args.out,
        source_commit=args.source_commit,
        base_path=args.base_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
