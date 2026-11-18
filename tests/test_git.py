from pathlib import Path
import subprocess
import tempfile
import unittest

from cad_ci.git import changed_files


class GitTests(unittest.TestCase):
    def test_changed_files_uses_exact_revisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "CI Test"], cwd=repo, check=True)
            (repo / "a.txt").write_text("one\n")
            subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "first"], cwd=repo, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "a.txt").write_text("two\n")
            (repo / "b.txt").write_text("new\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "second"], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            self.assertEqual(changed_files(repo, base, head), ("a.txt", "b.txt"))


if __name__ == "__main__":
    unittest.main()
