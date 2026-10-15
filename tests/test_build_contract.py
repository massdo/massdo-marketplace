"""Validate Build documentation inputs and outputs, not server business rules.

Selection, ownership and progression behavior belongs to Journal's focused tests.
The captured schemas come from client.listTools(), shared with the Spec checks.
"""

import copy
import json
import re
import unittest

import yaml
from jsonschema import Draft202012Validator, ValidationError

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

    def test_obsolete_fields_and_malformed_credentials_are_rejected(self):
        reserve = next(example for example in examples()
                       if example["arguments"]["operation"] == "reserve")
        for patch in ({"operation": "start"}, {"targetBranch": "main"},
                      {"expectedVersion": "4"}, {"id": "bad ref"},
                      {"ownership": {"executionId": "short", "proof": "example-proof"}},
                      {"ownership": {"executionId": "abcdefghijklmnopqrstuv"}}):
            malformed = copy.deepcopy(reserve)
            malformed["arguments"].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                validate_example(malformed)

    def test_evidence_and_blockage_shapes_reject_missing_fields(self):
        complete = next(example for example in examples()
                        if example["arguments"]["operation"] == "complete")
        for field in ("criteria", "verifications", "commit", "pullRequest"):
            malformed = copy.deepcopy(complete)
            del malformed["arguments"]["completionEvidence"][field]
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_example(malformed)
        for field, replacement in (("commit", {"sha": "short", "pushed": False}),
                                   ("pullRequest", {"url": "https://example.com/pr/1",
                                                    "state": "closed", "verified": False}),
                                   ("criteria", []), ("verifications", [])):
            malformed = copy.deepcopy(complete)
            malformed["arguments"]["completionEvidence"][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_example(malformed)
        block = next(copy.deepcopy(example) for example in examples()
                     if example["arguments"]["operation"] == "block")
        del block["arguments"]["blockage"]["resumeCondition"]
        with self.assertRaises(ValidationError):
            validate_example(block)

    def test_reserve_response_shapes_and_consumed_fields_match_the_catalogue(self):
        documented = examples("result")
        self.assertTrue(documented)
        for example in documented:
            validator = Draft202012Validator(CATALOG["outputSchemas"][example["tool"]])
            response = example["result"]
            with self.subTest(item=response["item"]["type"]):
                validator.validate(response)
                for field in ("contextId", "selectionId", "taskIds"):
                    malformed = copy.deepcopy(response)
                    del malformed["reservation"][field]
                    with self.subTest(missing=field), self.assertRaises(ValidationError):
                        validator.validate(malformed)
                for field in ("executionId", "proof"):
                    malformed = copy.deepcopy(response)
                    del malformed["ownership"][field]
                    with self.subTest(credential=field), self.assertRaises(ValidationError):
                        validator.validate(malformed)
                for patch in ({"activeTaskId": "7TxA"}, {"tasks": []},
                              {"externalDependencies": []}, {"proof": "example-private-proof"}):
                    with self.subTest(patch=patch), self.assertRaises(ValidationError):
                        validator.validate(response | patch)
                malformed = copy.deepcopy(response)
                malformed["reservation"]["activeTaskId"] = "7TxA"
                with self.assertRaises(ValidationError):
                    validator.validate(malformed)

    def test_next_response_identifies_items_without_an_active_task_field(self):
        schema = CATALOG["outputSchemas"]["manage_build"]
        validator = Draft202012Validator(schema)
        response = {"operation": "next", "item": {"id": "7TxA", "type": "task",
                                                 "version": 2, "status": "building"},
                    "etag": "example-etag", "reservation": {
                        "contextId": "4W1R", "executionId": "abcdefghijklmnopqrstuv",
                        "selectionId": "4W1R", "taskIds": ["7TxA"],
                        "acquiredAt": "2026-10-14T10:00:00.000Z"}}
        validator.validate(response)
        with self.assertRaises(ValidationError):
            validator.validate(response | {"activeTaskId": "7TxA"})
        with self.assertRaises(ValidationError):
            validator.validate(response | {"proof": "example-private-proof"})

    def test_references_and_explicit_invocation_are_valid(self):
        self.assertEqual(skills.validate_skill(BUILD / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (BUILD / "SKILL.md").read_text(), re.DOTALL)
        self.assertIs(yaml.safe_load(frontmatter.group(1))["disable-model-invocation"], True)
        interface = yaml.safe_load((BUILD / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], False)
