"""Tests for the reusable GitHub Actions support shipped by tool.cad.ci."""

from __future__ import annotations

import importlib.util
import json
import sys
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

    def test_targeted_item_selection_bypasses_git_diff(self):
        self.assertEqual(
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=False,
                item="simple-box",
            ),
            ["--item", "simple-box"],
        )

    def test_targeted_changed_paths_select_multiple_affected_items(self):
        self.assertEqual(
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=False,
                changed_paths=json.dumps(
                    [
                        "examples/simple-box/ci.yml",
                        "examples/components/ci.yml",
                    ]
                ),
            ),
            [
                "--changed",
                "examples/simple-box/ci.yml",
                "examples/components/ci.yml",
            ],
        )

    def test_targeted_selection_is_mutually_exclusive_and_cannot_narrow_full_run(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=False,
                item="simple-box",
                changed_paths=json.dumps(["examples/components/ci.yml"]),
            )
        with self.assertRaisesRegex(ValueError, "cannot be combined with full_run"):
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=True,
                item="simple-box",
            )

    def test_changed_paths_reject_parent_escape(self):
        with self.assertRaisesRegex(ValueError, "repository-relative"):
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=False,
                changed_paths=json.dumps(["../outside/ci.yml"]),
            )

    def test_changed_paths_requires_json_list(self):
        with self.assertRaisesRegex(ValueError, "JSON list"):
            self.helper.selection_args(
                source_sha="",
                base_sha="",
                full_run=False,
                changed_paths="examples/simple-box/ci.yml",
            )

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

    def test_incremental_selection_rejects_non_sha_revisions(self):
        for base, head in (("main", "b" * 40), ("a" * 40, "HEAD")):
            with self.subTest(base=base, head=head):
                with self.assertRaisesRegex(ValueError, "exactly 40"):
                    self.helper.selection_args(
                        source_sha=head, base_sha=base, full_run=False
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
        for name in ("CAD_CI_OUTPUT", "PYTHONPATH", "PATH", "DOCKER_CONFIG",
                     "GH_TOKEN", "PIP_INDEX_URL", "LD_PRELOAD"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "reserved"):
                self.helper.consumer_environment(json.dumps({name: "override"}))


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


    def test_pr_policy_validates_development_branch_configuration(self):
        policy = self.helper.parse_pr_policy(
            '{"stable_branch":"main","development_branches":["dev-cad","dev-ci"],'
            '"docs_only_prefixes":["docs/"]}'
        )
        self.assertEqual(policy["stable_branch"], "main")
        self.assertEqual(policy["development_branches"], ("dev-cad", "dev-ci"))
        self.assertEqual(policy["docs_only_prefixes"], ("docs/",))

        for value in (
            '{"stable_ref":"main","lane_refs":["dev-ci"]}',
            '{"stable_branch":"main","development_branches":[]}',
            '{"stable_branch":"main","development_branches":["main"]}',
            '{"stable_branch":"main","development_branches":["dev-ci","dev-ci"]}',
            '{"stable_branch":"main","development_branches":["../dev-ci"]}',
            '{"stable_branch":"main","development_branches":["dev-ci"],"unknown":true}',
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.helper.parse_pr_policy(value)

    def test_pr_policy_promotes_exact_development_branch_to_full_run(self):
        with patch.object(self.helper, "git_changed_paths") as changed:
            result = self.helper.resolve_pr_policy(
                repo=Path("."),
                policy_json=(
                    '{"stable_branch":"main","development_branches":["dev-cad","dev-ci"],'
                    '"docs_only_prefixes":["docs/"]}'
                ),
                event_name="pull_request",
                base_ref="main",
                head_ref="dev-ci",
                base_sha="a" * 40,
                source_sha="b" * 40,
                explicit_full_run=False,
            )
        self.assertEqual(
            result,
            {
                "run_cad": True,
                "full_run": True,
                "classification": "lane-promotion",
            },
        )
        changed.assert_not_called()

    def test_pr_policy_skips_only_nonempty_docs_only_development_branch_diff(self):
        policy = (
            '{"stable_branch":"main","development_branches":["dev-cad","dev-ci"],'
            '"docs_only_prefixes":["docs/"]}'
        )
        with patch.object(
            self.helper,
            "git_changed_paths",
            return_value=("docs/plan.md", "docs/design.md"),
        ):
            docs = self.helper.resolve_pr_policy(
                repo=Path("."),
                policy_json=policy,
                event_name="pull_request",
                base_ref="dev-ci",
                head_ref="issue/docs",
                base_sha="a" * 40,
                source_sha="b" * 40,
                explicit_full_run=False,
            )
        self.assertEqual(docs["run_cad"], False)
        self.assertEqual(docs["classification"], "docs-only")

        for changed_paths in (
            (),
            ("docs/plan.md", "cad-ci.yml"),
        ):
            with patch.object(
                self.helper,
                "git_changed_paths",
                return_value=changed_paths,
            ):
                result = self.helper.resolve_pr_policy(
                    repo=Path("."),
                    policy_json=policy,
                    event_name="pull_request",
                    base_ref="dev-ci",
                    head_ref="issue/mixed",
                    base_sha="a" * 40,
                    source_sha="b" * 40,
                    explicit_full_run=False,
                )
            self.assertTrue(result["run_cad"])
            self.assertFalse(result["full_run"])
            self.assertEqual(result["classification"], "lane-incremental")

    def test_pr_policy_explicit_full_run_wins_without_diff(self):
        with patch.object(self.helper, "git_changed_paths") as changed:
            result = self.helper.resolve_pr_policy(
                repo=Path("."),
                policy_json=(
                    '{"stable_branch":"main","development_branches":["dev-cad","dev-ci"],'
                    '"docs_only_prefixes":["docs/"]}'
                ),
                event_name="pull_request",
                base_ref="dev-ci",
                head_ref="issue/docs",
                base_sha="a" * 40,
                source_sha="b" * 40,
                explicit_full_run=True,
            )
        self.assertTrue(result["run_cad"])
        self.assertTrue(result["full_run"])
        self.assertEqual(result["classification"], "explicit-full")
        changed.assert_not_called()


    def test_durable_state_delegates_to_library(self):
        from cad_ci.publication.durable import DurableScopeState

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            generated = root / "generated"
            with patch(
                "cad_ci.publication.durable.fetch_durable_scope_state",
                return_value=DurableScopeState(
                    scope="dev-ci",
                    base_sha="a" * 40,
                    full_run=False,
                    exists=True,
                ),
            ) as resolve:
                result = self.helper.durable_state(
                    repo=repo,
                    generated_build=generated,
                    scope="dev-ci",
                    source_sha="b" * 40,
                    build_branch="test-output/build",
                )

        self.assertEqual(
            result,
            {
                "scope": "dev-ci",
                "base_sha": "a" * 40,
                "full_run": False,
                "exists": True,
            },
        )
        resolve.assert_called_once()
        self.assertEqual(
            resolve.call_args.kwargs["branch"],
            "test-output/build",
        )

    def test_durable_publish_delegates_build_then_pages(self):
        from cad_ci.publication.durable import DurableScopeState

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            generated = root / "generated"
            prepared = root / "prepared"
            candidate = root / "build"

            with (
                patch(
                    "cad_ci.publication.durable.publish_durable_scope",
                    return_value="c" * 40,
                ) as build,
                patch(
                    "cad_ci.publication.durable.publish_durable_pages",
                    return_value="d" * 40,
                ) as pages,
            ):
                result = self.helper.durable_publish(
                    repo=repo,
                    generated_build=generated,
                    prepared_scope=prepared,
                    candidate_root=candidate,
                    scope="main",
                    base_sha="a" * 40,
                    full_run=False,
                    exists=True,
                    source_sha="b" * 40,
                    source_ref="main",
                    build_branch="test-output/build",
                    pages_branch="test-output/gh-pages",
                )

        self.assertEqual(result, ("c" * 40, "d" * 40))
        state = build.call_args.kwargs["state"]
        self.assertIsInstance(state, DurableScopeState)
        self.assertEqual(state.scope, "main")
        self.assertEqual(state.base_sha, "a" * 40)
        self.assertFalse(state.full_run)
        self.assertTrue(state.exists)
        self.assertEqual(
            build.call_args.kwargs["build_branch"],
            "test-output/build",
        )
        self.assertEqual(
            pages.call_args.kwargs["build_commit"],
            "c" * 40,
        )
        self.assertEqual(
            pages.call_args.kwargs["pages_branch"],
            "test-output/gh-pages",
        )

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
        self.assertEqual(text.count('scripts/reusable_ci.py" run'), 1)
        self.assertNotIn("actions/cache/restore", text)
        self.assertNotIn("actions/cache/save", text)
        self.assertNotIn("cache-primary-key", text)
        self.assertNotIn("restore-keys:", text)


    def test_run_surfaces_expose_targeted_selection(self):
        run = self.read("reusable-run.yml")
        self.assertIn("item:", run)
        self.assertIn("changed_paths:", run)
        self.assertIn('CAD_CI_TARGET_ITEM: ${{ inputs.item }}', run)
        self.assertIn(
            'CAD_CI_CHANGED_PATHS_INPUT: ${{ inputs.changed_paths }}',
            run,
        )
        self.assertIn('--item "$CAD_CI_TARGET_ITEM"', run)
        self.assertIn('--changed-paths "$CAD_CI_CHANGED_PATHS_INPUT"', run)

        high = self.read("reusable-ci.yml")
        self.assertIn("item: ${{ inputs.item }}", high)
        self.assertIn("changed_paths: ${{ inputs.changed_paths }}", high)

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
        """No separate login action bootstrap; token arrives in step env."""

        text = self.read("reusable-run.yml")
        login = "name: Authenticate Docker to GHCR"
        run_step = "name: Run selected CAD CI graph"
        self.assertIn(login, text)
        self.assertIn("GHCR_TOKEN: ${{ github.token }}", text)
        self.assertIn('docker login ghcr.io -u "${{ github.actor }}" --password-stdin', text)
        self.assertNotIn("docker/login-action@", text)
        self.assertLess(text.index(login), text.index(run_step)
        )
        self.assertNotIn("FORGE_RUNTIME_IMAGE", text)

    def test_plan_and_run_use_exact_shallow_tool_and_library(self):
        """Both lower-level workflows share the released source-stack contract."""

        for name in ("reusable-plan.yml", "reusable-run.yml"):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("job.workflow_sha", text)
                self.assertIn("library-revision", text)
                self.assertIn("ref: ${{ steps.library.outputs.revision }}", text)
                self.assertIn("PYTHONPATH:", text)
                self.assertIn("Fetch exact base revision for incremental selection", text)
                self.assertIn("git fetch --no-tags --depth=1 origin", text)
                self.assertIn("--no-deps --no-compile", text)
                self.assertIn("persist-credentials: true", text)
                self.assertIn("persist-credentials: false", text)
                scrub = (
                    "Drop caller Git credentials before consumer execution"
                    if name == "reusable-plan.yml"
                    else "Drop caller Git credentials after exact base fetch"
                )
                self.assertIn(scrub, text)
                self.assertLess(
                    text.index("Fetch exact base revision for incremental selection"),
                    text.index(scrub),
                )
                self.assertLess(
                    text.index(scrub),
                    text.index(
                        "Record source revisions" if name == "reusable-plan.yml"
                        else "Authenticate Docker to GHCR"
                    ),
                )
                self.assertNotIn("pip install -e", text)
                self.assertNotIn("fetch-depth: 0", text)

    def test_free_environment_input_is_documented_as_non_secret(self):
        text = self.read("reusable-run.yml")
        self.assertIn(
            "Optional JSON object of non-secret string environment values for consumer commands.",
            text,
        )
        self.assertIn("command_environment:", text)
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
        self.assertIn("pull_request_policy:", text)
        self.assertIn("pull_request_policy: ${{ inputs.pull_request_policy }}", text)
        self.assertIn("upload_build: ${{ inputs.upload_build }}", text)
        self.assertIn(
            "value: ${{ jobs.cad_ci.outputs.build_artifact_name }}",
            text,
        )

    def test_development_branch_policy_runs_on_same_runner_before_cad_bootstrap(self):
        run = self.read("reusable-run.yml")
        for value in (
            "pull_request_policy:",
            "Classify configured development-branch pull request",
            'scripts/reusable_ci.py" pr-policy',
            "Resolve effective CAD CI selection",
            "Report docs-only development-branch validation",
        ):
            self.assertIn(value, run)
        self.assertLess(
            run.index("Fetch exact base revision for incremental selection"),
            run.index("Classify configured development-branch pull request"),
        )
        self.assertLess(
            run.index("Classify configured development-branch pull request"),
            run.index("actions/setup-python@"),
        )
        self.assertIn(
            "if: steps.selection.outputs.run_cad == 'true'",
            run,
        )
        self.assertIn(
            '--full-run "${{ steps.selection.outputs.full_run }}"',
            run,
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
                "steps.selection.outputs.run_cad == 'true' && "
                "inputs.upload_build && "
                "steps.build_output.outputs.available == 'true'"
            ),
            2,
        )
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
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

    def test_pr_workflow_uses_one_runner_for_verification_and_publication(self):
        """One job/workspace, no artifact transfer or repeated Python setup."""

        text = self.read("reusable-pr.yml")
        self.assertIn("workflow_call:", text)
        self.assertEqual(text.count("runs-on: ubuntu-latest"), 1)
        self.assertIn("  pr:", text)
        self.assertNotIn("  publish:", text)
        self.assertNotIn("  verify:", text)
        self.assertNotIn("actions/upload-artifact@", text)
        self.assertNotIn("actions/download-artifact@", text)
        self.assertEqual(text.count("Run selected CAD CI graph"), 1)
        self.assertEqual(text.count("Checkout called tool revision"), 1)
        self.assertEqual(text.count("Install external CAD CI runtime dependencies"), 1)
        self.assertIn("python -m cad_ci_tool build prepare-pr", text)
        self.assertIn("python -m cad_ci_tool publish build", text)
        self.assertIn("python -m cad_ci_tool publish build-cleanup", text)
        self.assertIn("publish_build:", text)
        self.assertIn("default: true", text)

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
