"""Check the distributed manual probes' identity and response contract."""

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


class UpdateSkills(unittest.TestCase):
    def test_each_probe_declares_only_its_own_release_identity(self):
        for name, prefix, label in (("nestor", "1", "Nestor stable"),
                                    ("nestor-beta", "2", "Nestor Beta")):
            with self.subTest(plugin=name):
                plugin = ROOT / "plugins" / name
                release = json.loads((plugin / "plugin-release.json").read_text())
                text = (plugin / "skills/check-for-updates/SKILL.md").read_text()
                frontmatter = yaml.safe_load(text.split("---", 2)[1])
                self.assertIn(label, frontmatter["description"])
                self.assertEqual(re.findall(r'"version_hash": "([^"]+)"', text),
                                 [prefix + release["version_hash"]])
                self.assertIn("Call `probe_plugin_version`", text)
                self.assertIn(f"differs from `{name}`", text)

    def test_both_probes_keep_unproven_results_inconclusive_and_repeat_alerts(self):
        for name in ("nestor", "nestor-beta"):
            with self.subTest(plugin=name):
                text = (ROOT / "plugins" / name / "skills/check-for-updates/SKILL.md").read_text()
                unknown = next(line for line in text.splitlines() if line.startswith("- `unknown`:"))
                for diagnostic in ("hash_unrecognized", "catalog_unavailable", "catalog_behind"):
                    self.assertIn(diagnostic, unknown)
                self.assertIn("unverified declared version", unknown)
                update = next(line for line in text.splitlines() if line.startswith("- `update_available`:"))
                self.assertIn("every manual check", update)
                self.assertIn("second check", update)
