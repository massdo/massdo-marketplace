"""Check documented requests against the captured MCP catalogue, not an agent.

MCP shapes come from client.listTools() on an isolated Journal server.
"""

import json
import re
import unittest

import yaml
from jsonschema import Draft202012Validator

from test_spec_contract import ROOT, skills

SKILL = ROOT / "plugins/nestor-beta/skills/next-tasks"
CATALOG = json.loads((ROOT / "tests/fixtures/next-tasks-catalog.json").read_text())


def documented_examples():
    return [json.loads(block) for path in SKILL.rglob("*.md")
            for block in re.findall(r"```json\n(.*?)\n```", path.read_text(), re.DOTALL)]


class NextTasksContract(unittest.TestCase):
    def test_documented_requests_match_catalogue_and_current_release(self):
        examples = documented_examples()
        self.assertTrue(examples)
        release = json.loads((ROOT / "plugins/nestor-beta/plugin-release.json").read_text())
        for example in examples:
            with self.subTest(tool=example["tool"]):
                self.assertEqual(set(example), {"tool", "arguments"})
                Draft202012Validator(CATALOG["inputSchemas"][example["tool"]]).validate(
                    example["arguments"])
                self.assertEqual(example["arguments"]["version_hash"],
                                 "2" + release["version_hash"])

    def test_skill_interface_remains_explicit(self):
        self.assertEqual(skills.validate_skill(SKILL / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (SKILL / "SKILL.md").read_text(), re.DOTALL)
        self.assertIs(yaml.safe_load(frontmatter.group(1))["disable-model-invocation"], True)
        interface = yaml.safe_load((SKILL / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$nestor-beta:next-tasks", interface["interface"]["default_prompt"])
