from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "scripts" / "merge_policy.py"

spec = importlib.util.spec_from_file_location("merge_policy", POLICY_PATH)
assert spec is not None and spec.loader is not None
merge_policy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = merge_policy
spec.loader.exec_module(merge_policy)


class MergePolicyTests(unittest.TestCase):
    def test_configured_lane_promotion_uses_merge(self):
        lanes = ("cad-work", "ci-work")
        for head in lanes:
            with self.subTest(head=head):
                value = merge_policy.evaluate(
                    base="stable",
                    head=head,
                    stable_ref="stable",
                    lane_refs=lanes,
                    permanent_refs=("build", "pages"),
                )
                self.assertEqual(value.merge_method, "merge")
                self.assertTrue(value.direct_lane_promotion)
                self.assertFalse(value.direct_lane_synchronization)
                self.assertFalse(value.cleanup_head)
                self.assertTrue(value.integrate_base)

    def test_stable_to_configured_lane_sync_uses_merge(self):
        lanes = ("cad-work", "ci-work")
        for base in lanes:
            with self.subTest(base=base):
                value = merge_policy.evaluate(
                    base=base,
                    head="stable",
                    stable_ref="stable",
                    lane_refs=lanes,
                    permanent_refs=("build", "pages"),
                )
                self.assertEqual(value.merge_method, "merge")
                self.assertFalse(value.direct_lane_promotion)
                self.assertTrue(value.direct_lane_synchronization)
                self.assertFalse(value.cleanup_head)
                self.assertTrue(value.integrate_base)

    def test_lane_to_lane_remains_squash_without_cleanup(self):
        value = merge_policy.evaluate(
            base="cad-work",
            head="ci-work",
            stable_ref="stable",
            lane_refs=("cad-work", "ci-work"),
        )
        self.assertEqual(value.merge_method, "squash")
        self.assertFalse(value.direct_lane_promotion)
        self.assertFalse(value.direct_lane_synchronization)
        self.assertFalse(value.cleanup_head)
        self.assertTrue(value.integrate_base)

    def test_all_other_merges_are_squash(self):
        value = merge_policy.evaluate(
            base="cad-work",
            head="feature/x",
            stable_ref="stable",
            lane_refs=("cad-work", "ci-work"),
        )
        self.assertEqual(value.merge_method, "squash")
        self.assertFalse(value.direct_lane_promotion)
        self.assertFalse(value.direct_lane_synchronization)
        self.assertTrue(value.cleanup_head)
        self.assertTrue(value.integrate_base)

    def test_cleanup_is_explicit_allow_list_and_never_permanent(self):
        kwargs = dict(
            stable_ref="stable",
            lane_refs=("cad-work", "ci-work"),
            permanent_refs=("build", "pages"),
            temporary_prefixes=("issue/", "feature/"),
        )
        self.assertTrue(
            merge_policy.is_cleanup_eligible("issue/123", **kwargs)
        )
        for head in (
            "stable",
            "cad-work",
            "ci-work",
            "build",
            "pages",
            "backup/stable-before-change",
            "release/1.0",
            "unexpected",
        ):
            with self.subTest(head=head):
                self.assertFalse(
                    merge_policy.is_cleanup_eligible(head, **kwargs)
                )

    def test_non_durable_base_does_not_request_integration(self):
        value = merge_policy.evaluate(
            base="experiment",
            head="feature/x",
            stable_ref="stable",
            lane_refs=("cad-work", "ci-work"),
        )
        self.assertFalse(value.integrate_base)

    def test_json_list_validation_is_fail_closed(self):
        for raw in ('{}', '["x","x"]', '[""]', 'not-json'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                merge_policy._strings(raw, "values")


class ReusableMergePolicyWorkflowTests(unittest.TestCase):
    def test_workflow_is_thin_and_calls_versioned_helper(self):
        text = (
            ROOT / ".github" / "workflows" / "reusable-merge-policy.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        self.assertIn("inputs.command == '/merge'", text)
        self.assertIn("job.workflow_repository", text)
        self.assertIn("job.workflow_sha", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("timeout-minutes: 10", text)
        self.assertIn("scripts/merge_command.py", text)
        self.assertIn("--lane-refs-json", text)
        self.assertIn("--integration-workflow", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("gh api -X PUT", text)
        self.assertNotIn("dev-cad", text)
        self.assertNotIn("dev-ci", text)

    def test_workflow_does_not_accept_arbitrary_merge_method(self):
        text = (
            ROOT / ".github" / "workflows" / "reusable-merge-policy.yml"
        ).read_text(encoding="utf-8")
        inputs = text.split("inputs:", 1)[1].split("permissions:", 1)[0]
        self.assertNotIn("merge_method:", inputs)
        self.assertIn("--stable-ref", text)
        self.assertIn("--lane-refs-json", text)


if __name__ == "__main__":
    unittest.main()
