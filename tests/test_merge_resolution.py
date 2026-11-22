from __future__ import annotations

import unittest

from scripts.merge_resolution import parse_resolution_command, verify_merge_object


class ResolutionCommandTests(unittest.TestCase):
    def command(self) -> str:
        return "\n".join([
            "/merge-resolved",
            "base " + "a" * 40,
            "head " + "b" * 40,
            "resolution-pr 201",
            "resolution resolve/pr-200 " + "c" * 40 + " " + "d" * 40,
        ])

    def test_parse_binds_parents_review_pr_commit_and_tree(self):
        value = parse_resolution_command(self.command(), "resolve/")
        self.assertEqual(value.base_sha, "a" * 40)
        self.assertEqual(value.head_sha, "b" * 40)
        self.assertEqual(value.resolution_pr, 201)
        self.assertEqual(value.resolution_ref, "resolve/pr-200")
        self.assertEqual(value.resolution_sha, "c" * 40)
        self.assertEqual(value.resolution_tree, "d" * 40)

    def test_parse_rejects_non_resolution_prefix_and_non_exact_sha(self):
        bad_ref = self.command().replace("resolve/pr-200", "issue/pr-200")
        with self.assertRaisesRegex(ValueError, "configured prefix"):
            parse_resolution_command(bad_ref, "resolve/")

        bad_sha = self.command().replace("base " + "a" * 40, "base abc")
        with self.assertRaisesRegex(ValueError, "40-character"):
            parse_resolution_command(bad_sha, "resolve/")

    def test_parse_rejects_extra_or_missing_review_fields(self):
        with self.assertRaises(ValueError):
            parse_resolution_command("/merge-resolved", "resolve/")
        with self.assertRaises(ValueError):
            parse_resolution_command(self.command() + "\nextra value", "resolve/")

    def test_verify_merge_object_requires_exact_tree_and_parent_order(self):
        payload = {
            "sha": "e" * 40,
            "tree": {"sha": "d" * 40},
            "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
        }
        self.assertEqual(
            verify_merge_object(
                payload,
                expected_tree="d" * 40,
                expected_parents=("a" * 40, "b" * 40),
            ),
            "e" * 40,
        )

        reversed_parents = dict(payload)
        reversed_parents["parents"] = [
            {"sha": "b" * 40},
            {"sha": "a" * 40},
        ]
        with self.assertRaisesRegex(ValueError, "parents mismatch"):
            verify_merge_object(
                reversed_parents,
                expected_tree="d" * 40,
                expected_parents=("a" * 40, "b" * 40),
            )


if __name__ == "__main__":
    unittest.main()
