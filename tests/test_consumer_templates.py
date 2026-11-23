"""Contract tests for copy-ready repository handoff templates."""

from __future__ import annotations

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MANUAL = DOCS / "manual"
TEMPLATES = MANUAL / "templates"
RELEASE = "v0.32.0"

EXPECTED = {
    "cad-ci.yml": ("tool.cad.ci/cad-ci", 1, "reusable-ci.yml"),
    "cad-ci-lanes.yml": ("tool.cad.ci/cad-ci-lanes", 4, "reusable-ci.yml"),
    "cad-ci-pr.yml": ("tool.cad.ci/cad-ci-pr", 1, "reusable-pr.yml"),
    "merge-policy.yml": ("tool.cad.ci/merge-policy", 4, "reusable-merge-policy.yml"),
    "branch-cleanup.yml": ("tool.cad.ci/branch-cleanup", 2, "reusable-branch-cleanup.yml"),
    "branch-retirement.yml": ("tool.cad.ci/branch-retirement", 2, "reusable-branch-retirement.yml"),
}


def load_yaml(path: Path) -> dict:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected mapping")
    return value


class ConsumerTemplateTests(unittest.TestCase):
    def test_docs_root_has_only_core_documents_and_documentation_dirs(self):
        actual = {path.name for path in DOCS.iterdir()}
        self.assertEqual(
            actual,
            {
                "api.md",
                "consumer.md",
                "design.md",
                "handoff.md",
                "plan.md",
                "requirements.md",
                "manual",
                "background",
            },
        )

    def test_manual_separates_documentation_from_templates(self):
        files = {path.name for path in MANUAL.iterdir() if path.is_file()}
        dirs = {path.name for path in MANUAL.iterdir() if path.is_dir()}
        self.assertEqual(files, {"README.md", "manual.md"})
        self.assertEqual(dirs, {"templates"})

    def test_template_directory_contains_only_expected_yaml(self):
        actual = {path.name for path in TEMPLATES.iterdir() if path.is_file()}
        self.assertEqual(actual, set(EXPECTED))

    def test_every_template_has_visible_provenance_and_release_tag(self):
        for filename, (template_id, version, _) in EXPECTED.items():
            text = (TEMPLATES / filename).read_text(encoding="utf-8")
            with self.subTest(template=filename):
                self.assertIn(f"# template: {template_id}", text)
                self.assertIn(f"# template-version: {version}", text)
                self.assertIn(f"# tool-release: {RELEASE}", text)
                self.assertNotIn("# tool-release-sha:", text)
                self.assertNotRegex(text, r"@[0-9a-f]{40}\\b")

    def test_templates_call_only_expected_public_surface(self):
        for filename, (_, _, surface) in EXPECTED.items():
            text = (TEMPLATES / filename).read_text(encoding="utf-8")
            with self.subTest(template=filename):
                if surface == "action.yml":
                    self.assertIn(
                        "uses: brainboxemb/tool.cad.ci@" + RELEASE,
                        text,
                    )
                else:
                    self.assertIn(surface + "@" + RELEASE, text)

    def test_templates_do_not_copy_generic_implementation(self):
        forbidden = (
            "actions/checkout@",
            "actions/setup-python@",
            "gh api",
            "pip install",
            "docker login",
            "scripts/reusable_ci.py",
            "cad-ci run",
            "scons",
        )
        for filename in EXPECTED:
            text = (TEMPLATES / filename).read_text(encoding="utf-8").lower()
            with self.subTest(template=filename):
                for value in forbidden:
                    self.assertNotIn(value, text)

    def test_lane_template_delegates_pr_and_durable_lifecycles(self):
        wf = load_yaml(TEMPLATES / "cad-ci-lanes.yml")
        self.assertEqual(set(wf["jobs"]), {"pr", "durable"})

        pr = wf["jobs"]["pr"]
        self.assertNotIn("runs-on", pr)
        self.assertEqual(
            pr["uses"],
            "brainboxemb/tool.cad.ci/.github/workflows/"
            "reusable-ci.yml@" + RELEASE,
        )
        self.assertEqual(
            pr["with"]["pull_request_policy"],
            '{"stable_branch":"main","development_branches":["dev-cad","dev-ci"],'
            '"docs_only_prefixes":["docs/"]}',
        )

        durable = wf["jobs"]["durable"]
        self.assertNotIn("runs-on", durable)
        self.assertEqual(
            durable["permissions"],
            {"contents": "write", "packages": "read"},
        )
        self.assertEqual(
            durable["uses"],
            "brainboxemb/tool.cad.ci/.github/workflows/"
            "reusable-durable.yml@" + RELEASE,
        )
        self.assertEqual(durable["with"]["source_sha"], "${{ github.sha }}")
        self.assertEqual(durable["with"]["source_ref"], "${{ github.ref_name }}")
        self.assertEqual(durable["with"]["scope"], "${{ github.ref_name }}")
        self.assertEqual(durable["with"]["build_branch"], "build")
        self.assertEqual(durable["with"]["pages_branch"], "gh-pages")
        self.assertIn("workflow_dispatch", wf["on"])
        self.assertIn("push", wf["on"])

        text = (TEMPLATES / "cad-ci-lanes.yml").read_text(encoding="utf-8")
        for forbidden in ("gh api", "git diff", "docs_only=true", "full_run:"):
            self.assertNotIn(forbidden, text)

    def test_branch_cleanup_template_is_copy_ready(self):
        wf = load_yaml(TEMPLATES / "branch-cleanup.yml")
        job = wf["jobs"]["cleanup"]
        self.assertEqual(
            job["permissions"],
            {"contents": "write", "pull-requests": "read", "issues": "write"},
        )
        self.assertEqual(job["with"]["stable_branch"], "main")
        self.assertEqual(job["with"]["development_branches"], '["dev-cad","dev-ci"]')
        self.assertEqual(
            job["uses"],
            "brainboxemb/tool.cad.ci/.github/workflows/"
            "reusable-branch-cleanup.yml@" + RELEASE,
        )

    def test_branch_retirement_template_is_copy_ready(self):
        wf = load_yaml(TEMPLATES / "branch-retirement.yml")
        job = wf["jobs"]["retire"]
        self.assertEqual(
            job["permissions"],
            {"contents": "write", "pull-requests": "read", "issues": "write"},
        )
        self.assertEqual(job["with"]["stable_branch"], "main")
        self.assertEqual(job["with"]["development_branches"], '["dev-cad","dev-ci"]')
        self.assertEqual(
            job["uses"],
            "brainboxemb/tool.cad.ci/.github/workflows/"
            "reusable-branch-retirement.yml@" + RELEASE,
        )

    def test_merge_policy_is_version_4_and_copy_ready(self):
        wf = load_yaml(TEMPLATES / "merge-policy.yml")
        job = wf["jobs"]["merge"]
        self.assertEqual(
            job["permissions"],
            {
                "actions": "write",
                "contents": "write",
                "pull-requests": "write",
                "issues": "write",
                "checks": "read",
                "statuses": "read",
            },
        )
        self.assertEqual(job["with"]["stable_branch"], "main")
        self.assertEqual(job["with"]["development_branches"], '["dev-cad","dev-ci"]')
        self.assertIn("/merge-resolved", job["if"])
        self.assertEqual(
            job["uses"],
            "brainboxemb/tool.cad.ci/.github/workflows/"
            "reusable-merge-policy.yml@" + RELEASE,
        )


if __name__ == "__main__":
    unittest.main()
