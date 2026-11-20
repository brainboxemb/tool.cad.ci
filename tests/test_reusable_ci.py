"""Tests for the reusable GitHub Actions support shipped by tool.cad.ci."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_helper():
    """Load scripts/reusable_ci.py without making scripts a Python package."""

    path = ROOT / "scripts" / "reusable_ci.py"
    spec = importlib.util.spec_from_file_location("reusable_ci", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReusableCiHelperTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def test_incremental_selection_uses_exact_base_and_source(self):
        self.assertEqual(
            self.helper.selection_args(
                source_sha="b" * 40,
                base_sha="a" * 40,
                full_run=False,
            ),
            ["--base", "a" * 40, "--head", "b" * 40],
        )

    def test_full_run_has_no_git_selection_arguments(self):
        self.assertEqual(
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=True,
            ),
            [],
        )

    def test_incremental_selection_requires_base_and_source(self):
        with self.assertRaisesRegex(ValueError, "source_sha"):
            self.helper.selection_args(
                source_sha="",
                base_sha="a" * 40,
                full_run=False,
            )
        with self.assertRaisesRegex(ValueError, "base_sha"):
            self.helper.selection_args(
                source_sha="b" * 40,
                base_sha="",
                full_run=False,
            )

    def test_consumer_environment_accepts_domain_values(self):
        self.assertEqual(
            self.helper.consumer_environment(
                json.dumps(
                    {
                        "FORGE_RUNTIME_IMAGE": "ghcr.io/example/runtime:sha",
                        "MODEL_MODE": "verify",
                    }
                )
            ),
            {
                "FORGE_RUNTIME_IMAGE": "ghcr.io/example/runtime:sha",
                "MODEL_MODE": "verify",
            },
        )

    def test_consumer_environment_rejects_reserved_or_non_string_values(self):
        with self.assertRaisesRegex(ValueError, "reserved"):
            self.helper.consumer_environment(
                '{"GITHUB_TOKEN":"secret"}'
            )
        with self.assertRaisesRegex(ValueError, "must be a string"):
            self.helper.consumer_environment('{"COUNT":3}')

    def test_github_output_supports_compact_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "output"
            self.helper.write_github_output(
                target,
                "plan_json",
                '[{"id":"case-a"}]',
            )
            text = target.read_text(encoding="utf-8")
            self.assertIn("plan_json<<CAD_CI_OUTPUT_EOF", text)
            self.assertIn('[{"id":"case-a"}]', text)


class ReusableWorkflowTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (
            ROOT / ".github" / "workflows" / name
        ).read_text(encoding="utf-8")

    def test_plan_workflow_uses_caller_source_and_called_tool_revision(self):
        text = self.read("reusable-plan.yml")
        self.assertIn("workflow_call:", text)
        self.assertIn("Checkout caller source", text)
        self.assertIn("repository: ${{ job.workflow_repository }}", text)
        self.assertIn("ref: ${{ job.workflow_sha }}", text)
        self.assertIn("path: .cache/cad-ci-tool-source", text)
        self.assertEqual(text.count("scripts/reusable_ci.py plan"), 1)

    def test_run_workflow_uses_one_generic_run_without_persistent_cache(self):
        text = self.read("reusable-run.yml")
        self.assertIn("workflow_call:", text)
        self.assertIn("repository: ${{ job.workflow_repository }}", text)
        self.assertIn("ref: ${{ job.workflow_sha }}", text)
        self.assertEqual(text.count("scripts/reusable_ci.py run"), 1)
        self.assertNotIn("actions/cache/restore", text)
        self.assertNotIn("actions/cache/save", text)
        self.assertNotIn("cache-primary-key", text)
        self.assertNotIn("restore-keys:", text)


    def test_reusable_workflows_preserve_package_read_permission(self):
        """GHCR auth permission must survive both reusable workflow layers."""

        for name in ("reusable-ci.yml", "reusable-run.yml"):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("permissions:", text)
                self.assertIn("contents: read", text)
                self.assertIn("packages: read", text)

    def test_run_workflow_authenticates_ghcr_before_consumer_run(self):
        """Docker receives the workflow token without exposing image policy."""

        text = self.read("reusable-run.yml")
        login = "uses: docker/login-action@v3"
        run_step = "name: Run selected CAD CI graph"

        self.assertIn(login, text)
        self.assertIn("registry: ghcr.io", text)
        self.assertIn("username: ${{ github.actor }}", text)
        self.assertIn("password: ${{ github.token }}", text)
        self.assertLess(text.index(login), text.index(run_step))

        # Generic authentication must not select one consumer runtime image.
        self.assertNotIn("FORGE_RUNTIME_IMAGE", text)

    def test_free_environment_input_is_documented_as_non_secret(self):
        text = self.read("reusable-run.yml")
        self.assertIn(
            "Optional non-secret environment values for consumer commands.",
            text,
        )
    def test_high_level_workflow_cancels_same_caller_scope(self):
        """Only the high-level normal-consumer workflow owns concurrency."""

        high = self.read("reusable-ci.yml")
        self.assertIn("concurrency:", high)
        self.assertIn("cancel-in-progress: true", high)
        self.assertIn("github.repository", high)
        self.assertIn("github.workflow", high)
        self.assertIn(
            "github.event.pull_request.number || github.ref",
            high,
        )

        for name in ("reusable-plan.yml", "reusable-run.yml"):
            with self.subTest(name=name):
                lower = self.read(name)
                self.assertNotIn("concurrency:", lower)

    def test_high_level_workflow_delegates_to_one_generic_run(self):
        """Normal consumers should not reproduce generic setup locally."""

        text = self.read("reusable-ci.yml")
        call = "uses: ./.github/workflows/reusable-run.yml"
        self.assertIn("workflow_call:", text)
        self.assertEqual(text.count(call), 1)
        self.assertNotIn("actions/checkout@", text)
        self.assertNotIn("actions/setup-python@", text)
        self.assertNotIn("scripts/reusable_ci.py", text)
        self.assertIn("upload_build: ${{ inputs.upload_build }}", text)
        self.assertIn(
            "value: ${{ jobs.cad_ci.outputs.build_artifact_name }}",
            text,
        )

    def test_run_workflow_can_upload_build_with_hidden_evidence(self):
        text = self.read("reusable-run.yml")
        self.assertIn("upload_build:", text)
        self.assertIn("build_artifact_name:", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("path: build/", text)
        self.assertIn("include-hidden-files: true", text)
        self.assertIn("id: build_artifact", text)
        self.assertNotIn("id: build-artifact", text)
        self.assertIn(
            "build_artifact_name: ${{ steps.build_artifact.outputs.name }}",
            text,
        )
        self.assertIn(
            "value: ${{ jobs.run.outputs.build_artifact_name }}",
            text,
        )
        self.assertIn("id: build_artifact", text)
        self.assertIn(
            "build_artifact_name: ${{ steps.build_artifact.outputs.name }}",
            text,
        )


if __name__ == "__main__":
    unittest.main()
