import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CommentRule(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="comments-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in (".githooks", "scripts", "tests"):
            (self.root / directory).mkdir()
        shutil.copy2(ROOT / "scripts/check_comments.py", self.root / "scripts/check_comments.py")
        self.baseline = self.root / "scripts/comments-baseline.json"

    def write(self, name, text):
        (self.root / name).write_text(text)

    def run_rule(self, *args):
        return subprocess.run([sys.executable, "-B", "scripts/check_comments.py", *args],
                              cwd=self.root, capture_output=True, text=True)

    def test_functional_comments_pass(self):
        self.write("scripts/tool.py", '#!/usr/bin/env python3\n"""Usage."""\nprint(__doc__)\nvalue = 1  # type: ignore\n')
        self.write("install.sh", "#!/usr/bin/env bash\n# shellcheck disable=SC2086\necho \"${#}\" '#' http://example.test/#top\n")
        self.write("install.ps1", "#requires -Version 5.1\nWrite-Output 'done'\n")
        self.write(".githooks/pre-commit", "#!/bin/sh\nexit 0\n")
        result = self.run_rule()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_language_reports_its_comments(self):
        self.write("scripts/tool.py", 'def run():\n    """Run."""\n    return 1  # one\n')
        self.write("uninstall.sh", "#!/usr/bin/env bash\n# why\ntrue # trailing\n")
        self.write("tests/launcher.cs", "// why\nclass Launcher { } // trailing\n/* block */\n")
        self.write("install.ps1", "<# block\n#>\nWrite-Output 'done'\n")
        result = self.run_rule()
        self.assertEqual(result.returncode, 1)
        for location in ("scripts/tool.py:2:", "scripts/tool.py:3:", "uninstall.sh:2:", "uninstall.sh:3:",
                         "tests/launcher.cs:1:", "tests/launcher.cs:2:", "tests/launcher.cs:3:",
                         "install.ps1:1:"):
            self.assertIn(location, result.stderr)

    def test_baseline_only_goes_down(self):
        self.write("scripts/tool.py", "# kept\nvalue = 1\n")
        self.baseline.write_text(json.dumps({"scripts/tool.py": {"# kept": 1}}))
        self.assertEqual(self.run_rule().returncode, 0)

        self.write("scripts/tool.py", "# replaced\nvalue = 1\n")
        result = self.run_rule()
        self.assertEqual(result.returncode, 1)
        self.assertIn("scripts/tool.py:1: comment not allowed", result.stderr)
        self.assertIn("--lower-baseline", result.stderr)

        self.assertEqual(self.run_rule("--lower-baseline").returncode, 0)
        self.assertFalse(self.baseline.exists())
        result = self.run_rule()
        self.assertEqual(result.returncode, 1)
        self.assertIn("scripts/tool.py:1: comment not allowed", result.stderr)

        self.write("scripts/tool.py", "value = 1\n")
        self.assertEqual(self.run_rule().returncode, 0)
