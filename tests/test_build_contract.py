"""Validate Build documentation inputs and outputs, not server business rules.

Selection, ownership and progression behavior belongs to Journal's focused tests.
The captured schemas come from client.listTools(), shared with the Spec checks.
"""

import json
import re
import unittest

import yaml
from jsonschema import Draft202012Validator

from test_spec_contract import CATALOG, ROOT, skills, validate_example

BUILD = ROOT / "plugins/nestor-beta/skills/build"


def examples(field="arguments"):
    documented = [json.loads(block) for path in BUILD.rglob("*.md")
                  for block in re.findall(r"```json\n(.*?)\n```", path.read_text(), re.DOTALL)]
    for example in documented:
        if set(example) not in ({"tool", "arguments"}, {"tool", "result"}):
            raise ValueError("Example must name its tool and arguments or result")
    return [example for example in documented if field in example]


class BuildContract(unittest.TestCase):
    def test_examples_cover_the_published_operations(self):
        documented = examples()
        operations = CATALOG["inputSchemas"]["manage_build"]["properties"]["operation"]["enum"]
        self.assertEqual({example["arguments"]["operation"] for example in documented
                          if example["tool"] == "manage_build"}, set(operations))
        for example in documented:
            with self.subTest(tool=example["tool"], operation=example["arguments"]["operation"]):
                validate_example(example)

    def test_documented_responses_match_the_catalogue(self):
        documented = examples("result")
        self.assertTrue(documented)
        for example in documented:
            validator = Draft202012Validator(CATALOG["outputSchemas"][example["tool"]])
            response = example["result"]
            with self.subTest(item=response["item"]["type"]):
                validator.validate(response)

    def test_references_are_valid_and_an_agent_can_invoke_the_skill(self):
        self.assertEqual(skills.validate_skill(BUILD / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (BUILD / "SKILL.md").read_text(), re.DOTALL)
        self.assertNotIn("disable-model-invocation", yaml.safe_load(frontmatter.group(1)))
        interface = yaml.safe_load((BUILD / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], True)
        self.assertIn("$nestor-beta:build", interface["interface"]["default_prompt"])
