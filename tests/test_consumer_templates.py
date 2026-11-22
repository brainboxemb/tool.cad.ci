"""Contract tests for shipped consumer workflow templates."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates"
WORKFLOW_ROOT = TEMPLATE_ROOT / "github" / "workflows"
MANIFEST = TEMPLATE_ROOT / "manifest.json"
RELEASE_MARKER = "TOOL_CAD_CI_RELEASE_SHA"


def load_yaml(path: Path) -> dict:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected mapping")
    return value


class ConsumerTemplateTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.templates = self.manifest["templates"]

    def test_manifest_is_versioned_and_covers_every_workflow_template(self):
        self.assertEqual(self.manifest["schema"], 1)
        actual = {
            str(path.relative_to(TEMPLATE_ROOT))
            for path in WORKFLOW_ROOT.glob("*.yml")
        }
        self.assertEqual(set(self.templates), actual)
        for relative, entry in self.templates.items():
            with self.subTest(template=relative):
                self.assertRegex(entry["id"], r"^tool\.cad\.ci/[a-z0-9-]+$")
                self.assertIsInstance(entry["version"], int)
                self.assertGreater(entry["version"], 0)
                self.assertTrue(entry["surface"])

    def test_headers_match_manifest_id_and_version(self):
        for relative, entry in self.templates.items():
            path = TEMPLATE_ROOT / relative
            text = path.read_text(encoding="utf-8")
            with self.subTest(template=relative):
                self.assertIn(f"# template: {entry['id']}", text)
                self.assertIn(f"# template-version: {entry['version']}", text)
                self.assertEqual(text.count("# template:"), 1)
                self.assertEqual(text.count("# template-version:"), 1)

    def test_templates_pin_one_release_marker_and_supported_surface(self):
        expected = {
            "github/workflows/cad-ci.yml":
                "brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@"
                + RELEASE_MARKER,
            "github/workflows/cad-ci-lanes.yml":
                "brainboxemb/tool.cad.ci/.github/workflows/reusable-ci.yml@"
                + RELEASE_MARKER,
            "github/workflows/cad-ci-pr.yml":
                "brainboxemb/tool.cad.ci/.github/workflows/reusable-pr.yml@"
                + RELEASE_MARKER,
            "github/workflows/cad-ci-same-runner.yml":
                "brainboxemb/tool.cad.ci@" + RELEASE_MARKER,
            "github/workflows/merge-policy.yml":
                "brainboxemb/tool.cad.ci/.github/workflows/"
                "reusable-merge-policy.yml@" + RELEASE_MARKER,
        }
        for relative, reference in expected.items():
            text = (TEMPLATE_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(template=relative):
                self.assertEqual(text.count(RELEASE_MARKER), 2)
                self.assertIn(reference, text)

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
        for relative in self.templates:
            text = (TEMPLATE_ROOT / relative).read_text(encoding="utf-8").lower()
            with self.subTest(template=relative):
                for value in forbidden:
                    self.assertNotIn(value, text)

    def test_templates_do_not_encode_existing_consumer_names(self):
        forbidden = ("forge", "solidcraft", "2026-011-02", "cad.yml")
        for relative in self.templates:
            text = (TEMPLATE_ROOT / relative).read_text(encoding="utf-8").lower()
            with self.subTest(template=relative):
                for value in forbidden:
                    self.assertNotIn(value, text)

    def test_run_only_template_is_a_thin_public_workflow_call(self):
        wf = load_yaml(WORKFLOW_ROOT / "cad-ci.yml")
        job = wf["jobs"]["cad-ci"]
        self.assertNotIn("runs-on", job)
        self.assertIn("reusable-ci.yml@" + RELEASE_MARKER, job["uses"])
        self.assertEqual(wf["permissions"]["contents"], "read")
        self.assertEqual(wf["permissions"]["packages"], "read")

    def test_pr_template_uses_complete_one_runner_public_api(self):
        wf = load_yaml(WORKFLOW_ROOT / "cad-ci-pr.yml")
        job = wf["jobs"]["cad-ci"]
        self.assertNotIn("runs-on", job)
        self.assertIn("reusable-pr.yml@" + RELEASE_MARKER, job["uses"])
        self.assertEqual(wf["permissions"]["contents"], "write")
        self.assertEqual(wf["permissions"]["packages"], "read")

    def test_same_runner_template_calls_root_action_inside_one_job(self):
        wf = load_yaml(WORKFLOW_ROOT / "cad-ci-same-runner.yml")
        job = wf["jobs"]["cad-ci"]
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        action_steps = [
            step for step in job["steps"]
            if step.get("uses", "").startswith("brainboxemb/tool.cad.ci@")
        ]
        self.assertEqual(len(action_steps), 1)
        self.assertEqual(
            action_steps[0]["uses"],
            "brainboxemb/tool.cad.ci@" + RELEASE_MARKER,
        )
        self.assertIn("durable_scope", action_steps[0]["with"])
        self.assertIn("source_ref", action_steps[0]["with"])

    def test_lane_template_delegates_policy_without_local_classifier(self):
        wf = load_yaml(WORKFLOW_ROOT / "cad-ci-lanes.yml")
        job = wf["jobs"]["cad-ci"]
        self.assertNotIn("runs-on", job)
        self.assertIn("reusable-ci.yml@" + RELEASE_MARKER, job["uses"])
        self.assertEqual(
            job["with"]["pr_policy_json"],
            '{"stable_ref":"main","lane_refs":["dev-cad","dev-ci"],'
            '"docs_only_prefixes":["docs/"]}',
        )
        text = (WORKFLOW_ROOT / "cad-ci-lanes.yml").read_text(encoding="utf-8")
        for forbidden in ("gh api", "git diff", "docs_only=true", "full_run:"):
            self.assertNotIn(forbidden, text)

    def test_merge_template_supplies_required_permission_ceiling_and_policy(self):
        wf = load_yaml(WORKFLOW_ROOT / "merge-policy.yml")
        entry = self.templates["github/workflows/merge-policy.yml"]
        self.assertEqual(entry["version"], 2)
        job = wf["jobs"]["merge"]
        self.assertNotIn("runs-on", job)
        self.assertIn("reusable-merge-policy.yml@" + RELEASE_MARKER, job["uses"])
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
        self.assertEqual(job["with"]["stable_ref"], "main")
        self.assertEqual(job["with"]["lane_refs_json"], '["dev-cad","dev-ci"]')
        self.assertNotIn("integration_workflow", job["with"])


if __name__ == "__main__":
    unittest.main()
