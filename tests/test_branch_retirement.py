from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "branch_retirement.py"

spec = importlib.util.spec_from_file_location("branch_retirement", SCRIPT)
assert spec is not None and spec.loader is not None
branch_retirement = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = branch_retirement
spec.loader.exec_module(branch_retirement)


class BranchRetirementTests(unittest.TestCase):
    def test_command_requires_multiline_exact_sha_pairs(self):
        command = "/retire-branches\nissue/73-final-plan " + "a" * 40
        self.assertEqual(
            branch_retirement.parse_command(command),
            (("issue/73-final-plan", "a" * 40),),
        )
        for invalid in (
            "/retire-branches",
            "/retire-branches\nissue/73 only-two",
            "/cleanup-branches\nissue/73 " + "a" * 40,
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(branch_retirement.Refused):
                    branch_retirement.parse_command(invalid)

    @patch.object(branch_retirement, "paged_list", return_value=[])
    @patch.object(branch_retirement, "_current_sha")
    @patch.object(branch_retirement, "api")
    def test_exact_reviewed_sha_is_deleted_after_second_read(
        self, api, current_sha, _paged
    ):
        current_sha.side_effect = ["a" * 40, "a" * 40]
        result = branch_retirement.retire(
            repo="owner/repo",
            reviewed=(("issue/73", "a" * 40),),
            stable_ref="main",
            lane_refs=("dev-ci",),
            permanent_refs=("build",),
        )
        self.assertEqual(result.retired, ["issue/73 @ " + "a" * 40])
        api.assert_called_once()
        self.assertEqual(api.call_args.args[0], "DELETE")

    @patch.object(branch_retirement, "paged_list", return_value=[])
    @patch.object(branch_retirement, "_current_sha")
    @patch.object(branch_retirement, "api")
    def test_moved_after_preflight_is_kept(self, api, current_sha, _paged):
        current_sha.side_effect = ["a" * 40, "b" * 40]
        result = branch_retirement.retire(
            repo="owner/repo",
            reviewed=(("issue/73", "a" * 40),),
            stable_ref="main",
            lane_refs=("dev-ci",),
            permanent_refs=("build",),
        )
        self.assertEqual(result.retired, [])
        self.assertEqual(len(result.moved), 1)
        api.assert_not_called()

    @patch.object(branch_retirement, "paged_list", return_value=[])
    def test_protected_ref_is_refused_before_mutation(self, _paged):
        with self.assertRaisesRegex(branch_retirement.Refused, "protected"):
            branch_retirement.retire(
                repo="owner/repo",
                reviewed=(("main", "a" * 40),),
                stable_ref="main",
                lane_refs=("dev-ci",),
                permanent_refs=("build",),
            )

    @patch.object(branch_retirement, "paged_list")
    def test_open_pr_head_is_refused(self, paged):
        paged.return_value = [{
            "head": {
                "ref": "issue/73",
                "repo": {"full_name": "owner/repo"},
            }
        }]
        with self.assertRaisesRegex(branch_retirement.Refused, "open PR"):
            branch_retirement.retire(
                repo="owner/repo",
                reviewed=(("issue/73", "a" * 40),),
                stable_ref="main",
                lane_refs=("dev-ci",),
                permanent_refs=("build",),
            )


class ReusableRetirementWorkflowTests(unittest.TestCase):
    def test_workflow_is_thin_and_uses_trusted_tool_revision(self):
        text = (
            ROOT / ".github" / "workflows" / "reusable-branch-retirement.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        self.assertIn("startsWith(inputs.command, '/retire-branches')", text)
        self.assertIn("job.workflow_repository", text)
        self.assertIn("job.workflow_sha", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("scripts/branch_retirement.py", text)
        self.assertNotIn("gh api", text)


if __name__ == "__main__":
    unittest.main()
