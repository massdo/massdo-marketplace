import re
import unittest

import yaml

from test_spec_contract import ROOT, skills

SKILL = ROOT / "plugins/massdo-skills/skills/delete-comment"


class DeleteCommentContract(unittest.TestCase):
    def test_skill_interface_remains_explicit(self):
        self.assertEqual(skills.validate_skill(SKILL / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (SKILL / "SKILL.md").read_text(), re.DOTALL)
        self.assertIs(yaml.safe_load(frontmatter.group(1))["disable-model-invocation"], True)
        interface = yaml.safe_load((SKILL / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$massdo-skills:delete-comment", interface["interface"]["default_prompt"])
