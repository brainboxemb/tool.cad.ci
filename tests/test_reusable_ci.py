"""Tests for the reusable GitHub Actions support shipped by tool.cad.ci."""

from __future__ import annotations

import importlib.util
import json
import sys
from types import SimpleNamespace
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

    def test_durable_semantics_are_owned_by_library(self):
        text = (ROOT / "scripts" / "reusable_ci.py").read_text(encoding="utf-8")
        self.assertIn("from cad_ci.durable import", text)
        for forbidden in (
            "build.json",
            "def durable_scope(value",
            "def resolve_durable_state",
            "def fetch_durable_state",
            '"update-main"',
            '"update-named"',
            '"prepare-named"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_durable_resolve_command_delegates_to_library(self):
        state = SimpleNamespace(
            scope="main",
            base_sha="a" * 40,
            full_run=False,
            exists=True,
        )
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(
                 self.helper,
                 "fetch_durable_scope_state",
                 return_value=state,
             ) as resolve, \
             patch.object(self.helper, "write_github_output") as output, \
             patch.object(
                 sys,
                 "argv",
                 [
                     "reusable_ci.py",
                     "durable-resolve",
                     "--repo", tmp,
                     "--scope", "main",
                     "--source-sha", "b" * 40,
                     "--generated-build", str(Path(tmp) / "generated"),
                     "--github-output", str(Path(tmp) / "output"),
                 ],
             ):
            self.assertEqual(self.helper.main(), 0)

        resolve.assert_called_once_with(
            repo=Path(tmp),
            generated_build=Path(tmp) / "generated",
            scope="main",
            source_sha="b" * 40,
        )
        values = {call.args[1]: call.args[2] for call in output.call_args_list}
        self.assertEqual(values["scope"], "main")
        self.assertEqual(values["base_sha"], "a" * 40)
        self.assertEqual(values["full_run"], "false")
        self.assertEqual(values["scope_exists"], "true")

    def test_durable_publish_command_delegates_to_library(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(
                 self.helper,
                 "publish_durable_scope",
                 return_value="c" * 40,
             ) as publish, \
             patch.object(self.helper, "write_github_output") as output, \
             patch.object(
                 sys,
                 "argv",
                 [
                     "reusable_ci.py",
                     "durable-publish",
                     "--repo", tmp,
                     "--scope", "dev-cad",
                     "--source-sha", "b" * 40,
                     "--source-ref", "dev-cad",
                     "--base-sha", "a" * 40,
                     "--scope-exists", "true",
                     "--full-run", "false",
                     "--generated-build", str(Path(tmp) / "generated"),
                     "--candidate-root", str(Path(tmp) / "build"),
                     "--prepared-scope", str(Path(tmp) / "prepared"),
                     "--github-output", str(Path(tmp) / "output"),
                 ],
             ):
            self.assertEqual(self.helper.main(), 0)

        kwargs = publish.call_args.kwargs
        self.assertEqual(kwargs["repo"], Path(tmp))
        self.assertEqual(kwargs["source_sha"], "b" * 40)
        self.assertEqual(kwargs["source_ref"], "dev-cad")
        state = kwargs["state"]
        self.assertEqual(state.scope, "dev-cad")
        self.assertEqual(state.base_sha, "a" * 40)
        self.assertFalse(state.full_run)
        self.assertTrue(state.exists)
        values = {call.args[1]: call.args[2] for call in output.call_args_list}
        self.assertEqual(values["build_commit"], "c" * 40)
        self.assertEqual(values["prepared_scope"], str((Path(tmp) / "prepared").resolve()))

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


    def test_pr_policy_validates_lane_configuration(self):
        policy = self.helper.parse_pr_policy(
            '{"stable_ref":"main","lane_refs":["dev-cad","dev-ci"],'
            '"docs_only_prefixes":["docs/"]}'
        )
        self.assertEqual(policy["stable_ref"], "main")
        self.assertEqual(policy["lane_refs"], ("dev-cad", "dev-ci"))
        self.assertEqual(policy["docs_only_prefixes"], ("docs/",))

        for value in (
            '{"stable_ref":"main","lane_refs":[]}',
            '{"stable_ref":"main","lane_refs":["main"]}',
            '{"stable_ref":"main","lane_refs":["dev-ci","dev-ci"]}',
            '{"stable_ref":"main","lane_refs":["../dev-ci"]}',
            '{"stable_ref":"main","lane_refs":["dev-ci"],"unknown":true}',
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.helper.parse_pr_policy(value)

    def test_pr_policy_promotes_exact_lane_to_full_run(self):
        with patch.object(self.helper, "git_changed_paths") as changed:
            result = self.helper.resolve_pr_policy(
                repo=Path("."),
                policy_json=(
                    '{"stable_ref":"main","lane_refs":["dev-cad","dev-ci"],'
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

    def test_pr_policy_skips_only_nonempty_docs_only_lane_diff(self):
        policy = (
            '{"stable_ref":"main","lane_refs":["dev-cad","dev-ci"],'
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
                    '{"stable_ref":"main","lane_refs":["dev-cad","dev-ci"],'
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

    def test_action_owns_generic_run_and_optional_durable_build_only(self):
        text = self.read()
        self.assertIn("github_token:", text)
        self.assertIn("docker login ghcr.io", text)
        self.assertIn("CAD_CI_CONSUMER_ENV_JSON", text)
        self.assertIn("durable_scope:", text)
        self.assertIn("source_ref:", text)
        self.assertIn("durable-resolve", text)
        self.assertIn("durable-publish", text)
        self.assertNotIn("FORGE_RUNTIME_IMAGE", text)
        self.assertNotIn("site/build.py", text)
        self.assertNotIn("publish pages", text)

    def test_action_keeps_durable_work_on_same_composite_runner(self):
        text = self.read()
        self.assertIn("using: composite", text)
        self.assertEqual(text.count('scripts/reusable_ci.py" run'), 1)
        self.assertEqual(text.count("durable-resolve"), 1)
        self.assertEqual(text.count("durable-publish"), 1)
        self.assertNotIn("actions/upload-artifact", text)
        self.assertNotIn("actions/download-artifact", text)
        self.assertNotIn("runs-on:", text)

    def test_action_exposes_durable_outputs_for_later_same_runner_steps(self):
        text = self.read()
        for name in (
            "scope:",
            "base_sha:",
            "full_run:",
            "scope_exists:",
            "build_commit:",
            "prepared_scope:",
        ):
            with self.subTest(name=name):
                self.assertIn(name, text)
        self.assertIn(
            "value: ${{ steps.durable_publish.outputs.build_commit }}",
            text,
        )
        self.assertIn(
            "value: ${{ steps.durable_publish.outputs.prepared_scope }}",
            text,
        )

    def test_action_durable_mode_resolves_selection_before_one_run(self):
        text = self.read()
        resolve = "name: Resolve durable build scope"
        fetch = "name: Fetch exact base commit"
        run = "name: Run selected CAD CI graph"
        publish = "name: Publish durable build scope"
        for value in (resolve, fetch, run, publish):
            self.assertIn(value, text)
        self.assertLess(text.index(resolve), text.index(fetch))
        self.assertLess(text.index(fetch), text.index(run))
        self.assertLess(text.index(run), text.index(publish))

    def test_action_exposes_and_validates_bounded_jobs(self):
        text = self.read()
        self.assertIn("jobs:", text)
        self.assertIn('default: "1"', text)
        self.assertIn("jobs must be a positive integer", text)
        self.assertIn('CAD_CI_JOBS_INPUT: ${{ inputs.jobs }}', text)
        self.assertIn('--jobs "$CAD_CI_JOBS_INPUT"', text)

    def test_action_clears_git_token_before_run_only_consumer_commands(self):
        text = self.read()
        fetch = "name: Fetch exact base commit"
        scrub = "name: Remove Git checkout credentials before run-only execution"
        run = "name: Run selected CAD CI graph"
        self.assertIn(scrub, text)
        self.assertIn("if: inputs.durable_scope == ''", text)
        self.assertLess(text.index(fetch), text.index(scrub))
        self.assertLess(text.index(scrub), text.index(run))
        self.assertIn("persist-credentials: false", text)

    def test_action_validates_incremental_vs_full_run_contract(self):
        text = self.read()
        self.assertIn("full_run must be true or false", text)
        self.assertIn("incremental CAD CI requires base_sha", text)
        self.assertIn(
            "durable mode resolves base_sha and full_run automatically",
            text,
        )
        self.assertIn("durable mode requires source_ref", text)
        self.assertIn(
            "if: steps.selection.outputs.full_run == 'false'",
            text,
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
        self.assertIn("pr_policy_json:", text)
        self.assertIn("pr_policy_json: ${{ inputs.pr_policy_json }}", text)
        self.assertIn("upload_build: ${{ inputs.upload_build }}", text)
        self.assertIn(
            "value: ${{ jobs.cad_ci.outputs.build_artifact_name }}",
            text,
        )

    def test_lane_policy_runs_on_same_runner_before_cad_bootstrap(self):
        run = self.read("reusable-run.yml")
        for value in (
            "pr_policy_json:",
            "Classify configured development-lane pull request",
            'scripts/reusable_ci.py" pr-policy',
            "Resolve effective CAD CI selection",
            "Report docs-only lane validation",
        ):
            self.assertIn(value, run)
        self.assertLess(
            run.index("Fetch exact base revision for incremental selection"),
            run.index("Classify configured development-lane pull request"),
        )
        self.assertLess(
            run.index("Classify configured development-lane pull request"),
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
