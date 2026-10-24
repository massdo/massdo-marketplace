"""Check example inputs against a snapshot of the delivered MCP catalogue.

These checks validate documentation shapes, not approval or build policies. The
domain's behavior is exercised by Journal's focused approval/selection tests.
"""

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "plugins/nestor-beta/skills/spec"
CATALOG = json.loads((ROOT / "tests/fixtures/nestor-spec-catalog.json").read_text())
module = importlib.util.spec_from_file_location("validate_skills", ROOT / "scripts/validate_skills.py")
skills = importlib.util.module_from_spec(module)
module.loader.exec_module(skills)


def examples():
    return [json.loads(block) for path in SPEC.rglob("*.md")
            for block in re.findall(r"```json\n(.*?)\n```", path.read_text(), re.DOTALL)]


def validate_example(example):
    if set(example) != {"tool", "arguments"}:
        raise ValueError("Example must name its tool and arguments")
    schema = CATALOG["inputSchemas"].get(example["tool"])
    if schema is None:
        raise ValueError("Tool is absent from the published catalogue snapshot")
    Draft202012Validator(schema).validate(example["arguments"])
    release = json.loads((ROOT / "plugins/nestor-beta/plugin-release.json").read_text())
    if example["arguments"]["version_hash"] != "2" + release["version_hash"]:
        raise ValueError("Example version_hash does not match its plugin release")


class SpecContract(unittest.TestCase):
    def test_documented_examples_match_published_inputs(self):
        self.assertTrue(examples())
        for example in examples():
            with self.subTest(tool=example["tool"]):
                validate_example(example)

    def test_local_references_resolve_and_missing_references_fail(self):
        self.assertEqual(skills.validate_skill(SPEC / "SKILL.md"), [])
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "demo"
            skill.mkdir()
            entry = skill / "SKILL.md"
            entry.write_text('---\nname: demo\ndescription: Fixture.\n---\n'
                             '[Contract](references/contract.md#inputs)\n'
                             'Example: [PR title](URL)\n'
                             '[External](https://example.com/docs)\n')
            self.assertEqual(skills.validate_skill(entry),
                             ["reference does not exist: references/contract.md"])
            (skill / "references").mkdir()
            (skill / "references/contract.md").write_text("# Inputs\n")
            self.assertEqual(skills.validate_skill(entry), [])

    def test_explicit_invocation_is_preserved_in_both_clients(self):
        frontmatter = re.match(r"---\n(.*?)\n---", (SPEC / "SKILL.md").read_text(), re.DOTALL)
        self.assertIs(yaml.safe_load(frontmatter.group(1))["disable-model-invocation"], True)
        policy = yaml.safe_load((SPEC / "agents/openai.yaml").read_text())
        self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
