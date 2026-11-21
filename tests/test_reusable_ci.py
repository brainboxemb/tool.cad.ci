"""Tests for the reusable GitHub Actions support shipped by tool.cad.ci."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


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

    def test_positive_jobs_validation(self):
        self.assertEqual(self.helper.positive_int("1"), 1)
        self.assertEqual(self.helper.positive_int("4"), 4)
        for value in ("0", "-1", "no"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    self.helper.positive_int(value)

    def test_run_helper_forwards_exact_jobs_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch.object(self.helper.subprocess, "run") as run:
                self.helper.run_ci(
                    repo=repo,
                    source_sha="b" * 40,
                    base_sha="a" * 40,
                    full_run=False,
                    environment_json="{}",
                    jobs=3,
                )
            command = run.call_args.args[0]
            jobs_index = command.index("--jobs")
            self.assertEqual(command[jobs_index + 1], "3")

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

    def test_library_revision_reads_exact_pyproject_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                '[project]\n'
                'dependencies = ['
                '"brainboxemb-cad-ci-lib @ '
                'git+https://github.com/brainboxemb/lib.py.cad.ci.git@'
                + "a" * 40
                + '"]\n',
                encoding="utf-8",
            )
            self.assertEqual(self.helper.library_revision(root), "a" * 40)

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


class SameRunnerActionTests(unittest.TestCase):
    def read(self) -> str:
        return (ROOT / "action.yml").read_text(encoding="utf-8")

    def test_action_runs_exact_source_stack_once_and_leaves_cli_available(self):
        text = self.read()
        self.assertIn("using: composite", text)
        self.assertIn("name: Checkout caller source", text)
        self.assertIn("ref: ${{ inputs.source_sha }}", text)
        self.assertIn("fetch-depth: 1", text)
        self.assertIn("git fetch --no-tags --depth=1 origin", text)
        self.assertIn("library-revision", text)
        self.assertIn("repository: brainboxemb/lib.py.cad.ci", text)
        self.assertIn("ref: ${{ steps.library.outputs.revision }}", text)
        self.assertIn("CAD_CI_TOOL_ROOT=$GITHUB_ACTION_PATH", text)
        self.assertIn("CAD_CI_LIB_ROOT=$GITHUB_WORKSPACE/.cache/cad-ci-lib-source", text)
        self.assertIn("PYTHONPATH=", text)
        self.assertEqual(text.count('scripts/reusable_ci.py" run'), 1)

    def test_action_does_not_install_own_packages_or_transport_build_artifacts(self):
        text = self.read()
        self.assertNotIn("pip install -e", text)
        self.assertNotIn("pip install .", text)
        self.assertIn("--no-deps --no-compile", text)
        self.assertIn('"PyYAML>=6.0" "SCons==4.11.1"', text)
        self.assertNotIn("actions/upload-artifact", text)
        self.assertNotIn("actions/download-artifact", text)

    def test_action_owns_only_generic_setup_authentication_and_run(self):
        text = self.read()
        self.assertIn("github_token:", text)
        self.assertIn("docker login ghcr.io", text)
        self.assertIn("CAD_CI_CONSUMER_ENV_JSON", text)
        self.assertNotIn("FORGE_RUNTIME_IMAGE", text)
        self.assertNotIn("site/build.py", text)
        self.assertNotIn("publish pages", text)
        self.assertNotIn("publish build", text)

    def test_action_exposes_and_validates_bounded_jobs(self):
        text = self.read()
        self.assertIn("jobs:", text)
        self.assertIn('default: "1"', text)
        self.assertIn("jobs must be a positive integer", text)
        self.assertIn('CAD_CI_JOBS_INPUT: ${{ inputs.jobs }}', text)
        self.assertIn('--jobs "$CAD_CI_JOBS_INPUT"', text)

    def test_action_validates_incremental_vs_full_run_contract(self):
        text = self.read()
        self.assertIn("full_run must be true or false", text)
        self.assertIn("incremental CAD CI requires base_sha", text)
        self.assertIn("if: ${{ inputs.full_run == 'false' }}", text)


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


    def test_run_surfaces_expose_and_forward_bounded_jobs(self):
        run = self.read("reusable-run.yml")
        self.assertIn("jobs:", run)
        self.assertIn("type: number", run)
        self.assertIn("default: 1", run)
        self.assertIn('--jobs "${{ inputs.jobs }}"', run)

        high = self.read("reusable-ci.yml")
        self.assertIn("jobs:", high)
        self.assertIn("jobs: ${{ inputs.jobs }}", high)

        pr = self.read("reusable-pr.yml")
        self.assertIn("jobs:", pr)
        self.assertIn("type: number", pr)
        self.assertIn("default: 1", pr)
        self.assertIn('--jobs "${{ inputs.jobs }}"', pr)

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
        self.assertIn("name: Check materialized build output", text)
        self.assertIn("id: build_output", text)
        self.assertIn("find build -mindepth 1 -print -quit", text)
        self.assertEqual(
            text.count(
                "if: inputs.upload_build && "
                "steps.build_output.outputs.available == 'true'"
            ),
            2,
        )
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

    def test_pr_workflow_runs_and_publishes_on_one_runner(self):
        text = self.read("reusable-pr.yml")
        self.assertIn("workflow_call:", text)
        self.assertEqual(text.count("runs-on: ubuntu-latest"), 1)
        self.assertIn('scripts/reusable_ci.py" run', text)
        self.assertIn("python -m cad_ci_tool build prepare-pr", text)
        self.assertIn("python -m cad_ci_tool publish build", text)
        self.assertIn("python -m cad_ci_tool publish build-cleanup", text)
        self.assertNotIn("actions/upload-artifact", text)
        self.assertNotIn("actions/download-artifact", text)

    def test_pr_workflow_does_not_build_or_install_own_packages(self):
        text = self.read("reusable-pr.yml")
        self.assertIn("Checkout called tool revision", text)
        self.assertIn("Checkout pinned CAD CI library source", text)
        self.assertIn("PYTHONPATH:", text)
        self.assertNotIn("pip install -e", text)
        self.assertNotIn("pip install .cache/cad-ci-tool-source", text)
        self.assertIn('"PyYAML>=6.0" "SCons==4.11.1"', text)

    def test_pr_workflow_uses_shallow_head_and_exact_base_fetch(self):
        text = self.read("reusable-pr.yml")
        self.assertNotIn("fetch-depth: 0", text)
        self.assertIn("name: Fetch exact PR base commit", text)
        self.assertIn('git fetch --no-tags --depth=1 origin "$CAD_CI_BASE_SHA"', text)
        self.assertIn("!inputs.full_run", text)

    def test_pr_workflow_uses_direct_ghcr_login(self):
        text = self.read("reusable-pr.yml")
        self.assertNotIn("docker/login-action", text)
        self.assertIn("GHCR_TOKEN: ${{ github.token }}", text)
        self.assertIn('docker login ghcr.io -u "${{ github.actor }}" --password-stdin', text)

    def test_pr_external_dependencies_skip_resolution_and_precompile(self):
        text = self.read("reusable-pr.yml")
        self.assertIn("--no-deps --no-compile", text)

    def test_pr_workflow_cancels_superseded_pr_run(self):
        text = self.read("reusable-pr.yml")
        self.assertIn("concurrency:", text)
        self.assertIn("github.event.pull_request.number", text)
        self.assertIn("cancel-in-progress: true", text)


if __name__ == "__main__":
    unittest.main()
