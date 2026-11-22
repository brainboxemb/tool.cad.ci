from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "branch_cleanup.py"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("branch_cleanup", SCRIPT)
assert spec is not None and spec.loader is not None
branch_cleanup = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = branch_cleanup
spec.loader.exec_module(branch_cleanup)


class BranchCleanupTests(unittest.TestCase):
    def test_exact_merged_head_requires_same_ref_and_sha(self):
        merged = {("issue/1-a", "abc")}
        self.assertTrue(branch_cleanup.exact_merged_head("issue/1-a", "abc", merged))
        self.assertFalse(branch_cleanup.exact_merged_head("issue/1-a", "def", merged))
        self.assertFalse(branch_cleanup.exact_merged_head("issue/2-a", "abc", merged))

    @patch.object(branch_cleanup, "api")
    def test_integration_requires_positive_compare_status(self, api):
        api.side_effect = [{"status": "behind"}, {"status": "identical"}]
        self.assertTrue(
            branch_cleanup.is_integrated(
                "owner/repo", "issue/1-a", ("main", "dev-ci")
            )
        )

    @patch.object(branch_cleanup, "branch_sha")
    @patch.object(branch_cleanup, "is_integrated")
    @patch.object(branch_cleanup, "paged_list")
    @patch.object(branch_cleanup, "api")
    def test_moved_branch_is_never_deleted(
        self, api, paged_list, is_integrated, branch_sha
    ):
        paged_list.side_effect = [
            [{"name": "issue/1-a", "commit": {"sha": "old"}}],
            [],
            [],
        ]
        is_integrated.return_value = True
        branch_sha.return_value = "new"
        result = branch_cleanup.cleanup(
            repo="owner/repo",
            stable_ref="main",
            lane_refs=("dev-ci",),
            permanent_refs=("build",),
            temporary_prefixes=("issue/",),
        )
        self.assertEqual(result.deleted, [])
        self.assertEqual(result.moved, ["issue/1-a @ new (inspected old)"])
        self.assertFalse(any(call.args and call.args[0] == "DELETE" for call in api.call_args_list))

    @patch.object(branch_cleanup, "paged_list")
    def test_backup_and_permanent_refs_never_become_candidates(self, paged_list):
        paged_list.side_effect = [
            [
                {"name": "main", "commit": {"sha": "a"}},
                {"name": "dev-ci", "commit": {"sha": "b"}},
                {"name": "build", "commit": {"sha": "c"}},
                {"name": "backup/x", "commit": {"sha": "d"}},
            ],
            [],
            [],
        ]
        result = branch_cleanup.cleanup(
            repo="owner/repo",
            stable_ref="main",
            lane_refs=("dev-ci",),
            permanent_refs=("build",),
            temporary_prefixes=("issue/", "backup/"),
        )
        self.assertEqual(result, branch_cleanup.CleanupResult())


class ReusableBranchCleanupWorkflowTests(unittest.TestCase):
    def test_workflow_is_thin_and_uses_trusted_tool_revision(self):
        text = (
            ROOT / ".github" / "workflows" / "reusable-branch-cleanup.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        self.assertIn("inputs.command == '/cleanup-branches'", text)
        self.assertIn("job.workflow_repository", text)
        self.assertIn("job.workflow_sha", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("scripts/branch_cleanup.py", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("dev-cad", text)
        self.assertNotIn("dev-ci", text)


if __name__ == "__main__":
    unittest.main()
