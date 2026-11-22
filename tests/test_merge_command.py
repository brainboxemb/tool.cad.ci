"""Behavioral contracts for GitHub merge orchestration (offline fixtures)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("merge_command", ROOT / "scripts" / "merge_command.py")
assert spec and spec.loader
command = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = command
spec.loader.exec_module(command)


class MergeCommandTests(unittest.TestCase):
    def test_unknown_mergeability_retries_then_accepts(self):
        pr = {"state": "open", "draft": False, "mergeable": None}
        ready = dict(pr, mergeable=True)
        with patch.object(command, "api", side_effect=[pr, ready]) as call, \
             patch.object(command.time, "sleep") as sleep:
            self.assertIs(command.ready_pr("owner/repo", 11), ready)
            self.assertEqual(call.call_count, 2)
            sleep.assert_called_once()

    def test_mergeability_remains_unknown_fails_closed(self):
        with patch.object(command, "api", return_value={
            "state": "open", "draft": False, "mergeable": None,
        }), patch.object(command.time, "sleep"):
            with self.assertRaisesRegex(command.Refused, "unknown"):
                command.ready_pr("owner/repo", 11, retries=3)

    def test_pages_fetches_all_pages(self):
        checks = [{"id": i} for i in range(101)]
        with patch.object(command, "api", side_effect=[
            {"total_count": 101, "check_runs": checks[:100]},
            {"total_count": 101, "check_runs": checks[100:]},
        ]) as api:
            self.assertEqual(command.pages("repos/o/r/commits/a/check-runs", "check_runs"), checks)
            self.assertEqual(api.call_count, 2)
            self.assertIn("page=2", api.call_args.args[1])

    def test_incomplete_paginated_result_fails_closed(self):
        with patch.object(command, "api", side_effect=[
            {"total_count": 101, "workflow_runs": [{"id": i} for i in range(100)]},
            {"total_count": 101, "workflow_runs": []},
        ]):
            with self.assertRaisesRegex(command.Refused, "incomplete"):
                command.pages("repos/o/r/actions/runs", "workflow_runs")

    def test_check_identity_includes_app(self):
        checks = [
            {"name": "verify", "id": 1, "app": {"id": 1}, "status": "completed",
             "conclusion": "success", "started_at": "2026-11-20T00:00:00Z"},
            {"name": "verify", "id": 2, "app": {"id": 2}, "status": "completed",
             "conclusion": "failure", "started_at": "2026-11-21T00:00:00Z"},
        ]
        with self.assertRaisesRegex(command.Refused, "checks are not green"):
            command.validated_checks(checks, [])

    def test_old_command_run_excluded_but_failed_pr_check_blocks(self):
        checks = [
            {"name": "merge", "id": 1, "app": {"id": 1}, "status": "completed",
             "conclusion": "failure",
             "details_url": "https://github.com/o/r/actions/runs/42/job/100"},
            {"name": "verify", "id": 2, "app": {"id": 1}, "status": "completed",
             "conclusion": "failure"},
        ]
        with self.assertRaisesRegex(command.Refused, "verify"):
            command.validated_checks(checks, [{"id": 42}])

    def test_only_404_means_missing_ref(self):
        with patch.object(command, "api", side_effect=command.GitHubError("ref", 404, "missing")):
            self.assertFalse(command.ref_state("owner/repo", "lane"))
        with patch.object(command, "api", side_effect=command.GitHubError("ref", 503, "down")):
            with self.assertRaises(command.GitHubError):
                command.ref_state("owner/repo", "lane")

    def test_post_merge_failure_is_reported_and_not_called_refused(self):
        args = SimpleNamespace(command="/merge", repository="owner/repo",
            pull_request_number=7, actor="owner", repository_owner="owner",
            stable_ref="main", lane_refs_json='["dev-cad"]',
            permanent_refs_json='["build","gh-pages"]',
            temporary_prefixes_json='["issue/"]', integration_workflow="ci.yml")
        pr = {"base": {"ref": "main", "sha": "c" * 40}, "head": {"ref": "dev-cad",
            "sha": "a" * 40, "repo": {"full_name": "owner/repo"}}}
        with patch.object(command, "ready_pr", return_value=pr), \
             patch.object(command, "pages", return_value=[]), \
             patch.object(command, "validated_checks"), \
             patch.object(command, "api", side_effect=[
                {"statuses": [], "state": "success"},
                dict(pr, mergeable=True, draft=False, state="open"),
                {"merged": True, "sha": "b" * 40},
             ]), patch.object(command, "post_merge",
                return_value=command.PostMergeResult(lifecycle="FAILED",
                    dispatched=["main"], errors=["branch lifecycle: 503 down"])), \
             patch.object(command, "comment") as comment:
            self.assertEqual(command.run(args), 1)
            body = comment.call_args.args[2]
            self.assertIn("PR merged at", body)
            self.assertIn("post-merge processing FAILED", body)
            self.assertIn("b" * 40, body)

    def test_gh_response_headers_are_not_parsed_as_json(self):
        completed = SimpleNamespace(
            stdout='HTTP/2.0 200 OK\r\ncontent-type: application/json\r\n\r\n{"ok": true}\n',
            stderr="", returncode=0,
        )
        with patch.object(command.subprocess, "run", return_value=completed) as subprocess:
            self.assertEqual(command.api("GET", "repos/o/r"), {"ok": True})
            self.assertIn("-i", subprocess.call_args.args[0])

    def test_gh_204_response_is_valid(self):
        completed = SimpleNamespace(
            stdout='HTTP/2.0 204 No Content\r\ncontent-length: 0\r\n\r\n',
            stderr="", returncode=0,
        )
        with patch.object(command.subprocess, "run", return_value=completed):
            self.assertEqual(command.api("DELETE", "repos/o/r/refs/x"), {})

    def test_ref_patch_uses_typed_false(self):
        completed = SimpleNamespace(
            stdout='HTTP/2.0 200 OK\r\n\r\n{}',
            stderr="", returncode=0,
        )
        with patch.object(command.subprocess, "run", return_value=completed) as subprocess:
            command.api("PATCH", "repos/o/r/refs/heads/lane",
                        fields={"sha": "a" * 40, "force": "false"})
            self.assertIn("-F", subprocess.call_args.args[0])
            self.assertIn("force=false", subprocess.call_args.args[0])

    def test_cleanup_ref_advanced_since_merge_is_refused(self):
        from merge_policy import evaluate
        policy = evaluate(base="main", head="issue/3",
                          stable_ref="main", lane_refs=("dev-cad",))
        with patch.object(command, "api", return_value={
            "object": {"sha": "new-commit"},
        }) as api:
            result = command.post_merge("o/r", "main", "issue/3", "merge-sha",
                                        policy, "o/r", "old-pr-head", "")
            self.assertEqual(result.lifecycle, "FAILED")
            self.assertIn("moved", result.errors[0])
            self.assertEqual(api.call_count, 1)

    def test_api_failure_after_put_is_ambiguous_not_refused(self):
        args = SimpleNamespace(command="/merge", repository="owner/repo",
            pull_request_number=7, actor="owner", repository_owner="owner",
            stable_ref="main", lane_refs_json='["dev-cad"]',
            permanent_refs_json='["build","gh-pages"]',
            temporary_prefixes_json='["issue/"]', integration_workflow="")
        pr = {"base": {"ref": "main", "sha": "c" * 40}, "head": {"ref": "dev-cad",
            "sha": "a" * 40, "repo": {"full_name": "owner/repo"}}}
        with patch.object(command, "ready_pr", return_value=pr), \
             patch.object(command, "pages", return_value=[]), \
             patch.object(command, "validated_checks"), \
             patch.object(command, "api", side_effect=[
                {"statuses": [], "state": "success"},
                dict(pr, mergeable=True, draft=False, state="open"),
                command.GitHubError("merge", 502, "bad gateway"),
             ]):
            with self.assertRaisesRegex(command.MergeOutcomeUnknown, "may have completed"):
                command.run(args)

    def test_lifecycle_failure_does_not_prevent_stable_dispatch(self):
        from merge_policy import evaluate
        policy = evaluate(base="main", head="dev-cad",
                          stable_ref="main", lane_refs=("dev-cad",))
        with patch.object(command, "apply_lifecycle",
                          side_effect=command.GitHubError("PATCH", 503, "down")), \
             patch.object(command, "api", return_value={}) as api:
            result = command.post_merge("o/r", "main", "dev-cad", "merge-sha",
                                       policy, "o/r", "old-head", "ci.yml")
            self.assertEqual(result.lifecycle, "FAILED")
            self.assertEqual(result.dispatched, ["main"])
            self.assertEqual(len(result.errors), 1)
            self.assertEqual(api.call_count, 1)

    def test_one_dispatch_failure_does_not_hide_other_dispatch_result(self):
        from merge_policy import evaluate
        policy = evaluate(base="main", head="dev-cad",
                          stable_ref="main", lane_refs=("dev-cad",))
        with patch.object(command, "apply_lifecycle", return_value="advanced"), \
             patch.object(command, "api", side_effect=[
                command.GitHubError("dispatch main", 502, "unavailable"), {}
             ]):
            result = command.post_merge("o/r", "main", "dev-cad", "merge-sha",
                                       policy, "o/r", "old-head", "ci.yml")
            self.assertEqual(result.dispatched, ["dev-cad"])
            self.assertIn("dispatch main", result.errors[0])
    def test_premerge_base_update_blocks_before_mutation(self):
        original = {"state": "open", "draft": False,
                    "base": {"ref": "main", "sha": "a" * 40},
                    "head": {"ref": "feature/x", "sha": "h" * 40}}
        changed = {"state": "open", "draft": False,
                   "base": {"ref": "main", "sha": "b" * 40},
                   "head": {"ref": "feature/x", "sha": "h" * 40}}
        with patch.object(command, "api", return_value=changed) as api:
            with self.assertRaisesRegex(command.Refused, "base changed"):
                command.verify_fresh_pr("owner/repo", 12, original)
            api.assert_called_once_with("GET", "repos/owner/repo/pulls/12")

    def test_premerge_head_update_blocks_before_mutation(self):
        original = {"state": "open", "draft": False,
                    "base": {"ref": "main", "sha": "a" * 40},
                    "head": {"ref": "feature/x", "sha": "h" * 40}}
        changed = {"state": "open", "draft": False,
                   "base": {"ref": "main", "sha": "a" * 40},
                   "head": {"ref": "feature/x", "sha": "n" * 40}}
        with patch.object(command, "api", return_value=changed):
            with self.assertRaisesRegex(command.Refused, "head changed"):
                command.verify_fresh_pr("owner/repo", 12, original)

if __name__ == "__main__":
    unittest.main()
