"""Parse and check the public Actions API inventory, not YAML text fragments.

These are schema/documentation checks. Behavioral acceptance is separate.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CALLABLE = (
    "reusable-ci.yml",
    "reusable-pr.yml",
    "reusable-plan.yml",
    "reusable-run.yml",
    "reusable-merge-policy.yml",
)


def load_yaml(path: Path) -> dict:
    """BaseLoader preserves GitHub Actions 'on' as a string, not YAML 1.1 True."""
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected mapping")
    return value


class WorkflowApiContractTests(unittest.TestCase):
    def test_workflow_index_covers_every_workflow(self):
        index = (WORKFLOWS / "README.md").read_text(encoding="utf-8")
        api = (ROOT / "docs" / "api.md").read_text(encoding="utf-8")
        for path in WORKFLOWS.glob("*.yml"):
            with self.subTest(path=path.name):
                self.assertIn(f"`{path.name}`", index)
                self.assertIn(f"`{path.name}`", api)

    def test_every_callable_surface_declares_inputs_and_permission_boundary(self):
        for filename in CALLABLE:
            with self.subTest(filename=filename):
                wf = load_yaml(WORKFLOWS / filename)
                self.assertIn("workflow_call", wf["on"])
                contract = wf["on"]["workflow_call"]
                self.assertIn("inputs", contract)
                for name, entry in contract["inputs"].items():
                    self.assertIn("description", entry, (filename, name))
                    self.assertIn("type", entry, (filename, name))
                self.assertTrue(wf.get("permissions") or all(
                    "permissions" in job for job in wf.get("jobs", {}).values()
                ))

    def test_merge_api_is_declared_once_and_implementation_is_not_inline_yaml(self):
        wf = load_yaml(WORKFLOWS / "reusable-merge-policy.yml")
        contract = wf["on"]["workflow_call"]
        self.assertEqual(
            set(contract["inputs"]),
            {"command", "pull_request_number", "stable_ref", "lane_refs_json",
             "permanent_refs_json", "temporary_prefixes_json", "integration_workflow"},
        )
        self.assertEqual(set(wf["jobs"]), {"merge"})
        job = wf["jobs"]["merge"]
        self.assertEqual(job["concurrency"]["cancel-in-progress"], "false")
        self.assertIn("github.repository", job["concurrency"]["group"])
        self.assertNotIn("pull_request_number", job["concurrency"]["group"])
        self.assertEqual(job["timeout-minutes"], "10")
        self.assertEqual(job["permissions"]["contents"], "write")
        self.assertEqual(job["permissions"]["actions"], "write")
        steps = job["steps"]
        checkout = next(step for step in steps if "uses" in step)
        self.assertEqual(len(checkout["uses"].split("@")[-1]), 40)
        self.assertEqual(checkout["with"]["persist-credentials"], "false")
        cmd = next(step for step in steps if "run" in step)
        self.assertIn("scripts/merge_command.py", cmd["run"])
        self.assertNotIn("gh api", cmd["run"])

    def test_pr_workflow_rejects_unsupported_event_before_checkout(self):
        wf = load_yaml(WORKFLOWS / "reusable-pr.yml")
        self.assertEqual(set(wf["jobs"]), {"pr"})
        steps = wf["jobs"]["pr"]["steps"]
        guard = steps[0]
        self.assertEqual(guard["name"], "Validate caller pull_request context")
        self.assertIn("EVENT_NAME", guard["env"])
        self.assertIn("requires a pull_request event", guard["run"])
        self.assertIn("opened|reopened|synchronize|closed", guard["run"])
        self.assertEqual(steps[1]["name"], "Checkout caller source")

    def test_pr_workflow_single_runner_and_no_artifact_transport(self):
        wf = load_yaml(WORKFLOWS / "reusable-pr.yml")
        self.assertEqual(set(wf["jobs"]), {"pr"})
        pr = wf["jobs"]["pr"]
        self.assertEqual(pr["runs-on"], "ubuntu-latest")
        self.assertEqual(wf["permissions"]["contents"], "write")
        self.assertEqual(
            wf["on"]["workflow_call"]["inputs"]["publish_build"]["default"], "true"
        )
        steps = pr["steps"]
        self.assertEqual(
            sum(step.get("name") == "Run selected CAD CI graph" for step in steps), 1
        )
        self.assertEqual(
            sum(step.get("name") == "Publish affected PR build scope" for step in steps), 1
        )
        self.assertEqual(
            sum(step.get("name") == "Remove closed PR build scope" for step in steps), 1
        )
        self.assertFalse(any("upload-artifact" in step.get("uses", "")
                             or "download-artifact" in step.get("uses", "")
                             for step in steps))
        self.assertLess(
            next(i for i, step in enumerate(steps) if step.get("name") == "Run selected CAD CI graph"),
            next(i for i, step in enumerate(steps) if step.get("name") == "Publish affected PR build scope"),
        )

    def test_all_external_github_actions_use_immutable_40_character_shas(self):
        """Release reproducibility must not depend on moving action tags."""

        paths = [ROOT / "action.yml", *WORKFLOWS.glob("*.yml")]
        for path in paths:
            data = load_yaml(path)
            step_groups = [data.get("runs", {}).get("steps", [])]
            step_groups.extend(job.get("steps", [])
                               for job in data.get("jobs", {}).values())
            for steps in step_groups:
                for step in steps:
                    reference = step.get("uses", "")
                    if not reference or reference.startswith("./"):
                        continue
                    with self.subTest(file=path.name, action=reference):
                        self.assertRegex(
                            reference,
                            r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$",
                        )

    def test_same_runner_action_has_documented_public_inputs_outputs(self):
        action = load_yaml(ROOT / "action.yml")
        self.assertEqual(action["runs"]["using"], "composite")
        for group in ("inputs", "outputs"):
            for name, entry in action[group].items():
                with self.subTest(group=group, name=name):
                    self.assertTrue(entry.get("description"))


if __name__ == "__main__":
    unittest.main()
