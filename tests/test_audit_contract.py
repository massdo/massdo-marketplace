"""Check the audit skill's invocation policy in every client that reads it."""

import re
import sys
import unittest
from pathlib import Path

import yaml

# `python3 -m unittest tests.test_audit_contract` runs from the root, where the sibling module is not importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_spec_contract import ROOT, skills

SKILL = ROOT / "plugins/nestor-beta/skills/audit"


class AuditContract(unittest.TestCase):
    def test_an_agent_can_invoke_the_skill(self):
        self.assertEqual(skills.validate_skill(SKILL / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (SKILL / "SKILL.md").read_text(), re.DOTALL)
        self.assertNotIn("disable-model-invocation", yaml.safe_load(frontmatter.group(1)))
        interface = yaml.safe_load((SKILL / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], True)
        self.assertIn("$nestor-beta:audit", interface["interface"]["default_prompt"])
