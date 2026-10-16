"""Check documentary exchanges and expected outlines, not an agent or a renderer.

MCP shapes come from client.listTools() on an isolated Journal server. The outline
fixtures are authored expectations checked for identity, relations, order and coverage.
"""

import copy
import json
import re
import unittest

import yaml
from jsonschema import Draft202012Validator, ValidationError

from test_spec_contract import ROOT, skills

SKILL = ROOT / "plugins/nestor-beta/skills/next-tasks"
CATALOG = json.loads((ROOT / "tests/fixtures/next-tasks-catalog.json").read_text())
CASES = json.loads((ROOT / "tests/fixtures/next-tasks-cases.json").read_text())


def parent(item):
    if item["type"] == "plan":
        return item.get("parentPlanId")
    return item.get("planId", item.get("parentTaskId"))


def documented_examples():
    return [json.loads(block) for path in SKILL.rglob("*.md")
            for block in re.findall(r"```json\n(.*?)\n```", path.read_text(), re.DOTALL)]


class NextTasksContract(unittest.TestCase):
    def test_skyline_core_stays_under_its_refactoring_plan(self):
        case = next(case for case in CASES if case["name"] == "skyline_plan_core")
        items = case["calls"][0]["result"]["items"]
        core = next(item for item in items if item["slug"] == "scarlet_tiglon")
        plan = next(item for item in items if item["slug"] == "silver_whitefish")
        self.assertEqual(core["planId"], plan["id"])
        self.assertIn("core/API", core["excerpt"])
        self.assertEqual([(row["id"], row["parent"]) for row in case["presentation"]["outline"]],
                         [(plan["id"], None), (core["id"], plan["id"])])

    def test_capture_has_source_and_valid_published_schemas(self):
        source = CATALOG["source"]
        self.assertEqual(source["repository"], "massdo/journal")
        self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")
        self.assertIn("client.listTools()", source["method"])
        self.assertIn("isolated", source["method"])
        for direction in ("inputSchemas", "outputSchemas"):
            self.assertEqual(set(CATALOG[direction]),
                             {"list_items", "get_item", "get_project", "search_project"})
            for schema in CATALOG[direction].values():
                Draft202012Validator.check_schema(schema)

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

    def test_exchange_requests_and_responses_match_the_captured_contract(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                for call in case["calls"]:
                    tool, arguments = call["tool"], call["arguments"]
                    self.assertIn(tool, CATALOG["inputSchemas"])
                    Draft202012Validator(CATALOG["inputSchemas"][tool]).validate(arguments)
                    if "result" in call:
                        validator = Draft202012Validator(CATALOG["outputSchemas"][tool])
                        if call.get("compatibilityInput"):
                            self.assertIn("counter", call["compatibilityInput"])
                            with self.assertRaises(ValidationError):
                                validator.validate(call["result"])
                        else:
                            validator.validate(call["result"])
                    else:
                        self.assertTrue(call["failure"])
                    if tool == "list_items":
                        self.assertNotIn("filters", arguments)
                        self.assertNotIn("sort", arguments)
                        self.assertNotIn("limit", arguments)
                        if "cursor" not in arguments:
                            self.assertEqual(arguments["scope"],
                                             {"mode": "project", "projectId": "QYQi"})
                        if arguments.get("view") == "backlog":
                            self.assertTrue(case["userAskedBacklog"])
                    elif tool == "get_item":
                        self.assertEqual(arguments["scope"],
                                         {"mode": "project", "projectId": "QYQi"})
                        self.assertIsInstance(arguments["ref"], list)
                        self.assertLessEqual(len(arguments["ref"]), 5)
                        self.assertEqual(len(arguments["known"]), len(arguments["ref"]))

    def test_expected_outlines_preserve_items_relations_and_states_without_duplicates(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                selected, ancestors, errors = {}, {}, set()
                for call in case["calls"]:
                    if "result" not in call:
                        continue
                    if call["tool"] == "list_items":
                        selected.update((item["id"], item) for item in call["result"]["items"])
                    elif call["tool"] == "get_item":
                        for result in call["result"]["results"]:
                            if "error" in result:
                                errors.add(result["ref"])
                            else:
                                ancestors[result["item"]["id"]] = result["item"]
                items = selected | ancestors
                outline = case["presentation"]["outline"]
                identifiers = [row["id"] for row in outline]
                self.assertEqual(len(identifiers), len(set(identifiers)))
                self.assertEqual(set(identifiers), set(items))
                unresolved = set()
                for row in outline:
                    item = items[row["id"]]
                    self.assertEqual(row["parent"], parent(item))
                    self.assertEqual(row["context"], row["id"] not in selected)
                    if parent(item) in items:
                        self.assertLess(identifiers.index(parent(item)), identifiers.index(row["id"]))
                    elif parent(item) is not None:
                        unresolved.add(parent(item))
                    if item["type"] == "task":
                        self.assertEqual(row["kind"], "Task")
                        self.assertEqual(row["status"], item["status"])
                        self.assertNotIn("progress", row)
                    else:
                        self.assertEqual(row["kind"], "sub-plan" if parent(item) else "Plan")
                        self.assertEqual(row["progress"], item["progress"])
                        approval = item.get("approval")
                        expected = ("none recorded" if approval is None else "current"
                                    if approval["workRevision"] == item["workRevision"] else "older")
                        self.assertEqual(row["approval"], expected)
                        self.assertNotIn("status", row)
                        self.assertNotIn("backlog", item)
                self.assertEqual(set(case["presentation"]["unresolvedParents"]), unresolved)
                self.assertEqual(unresolved, errors)
                if errors:
                    self.assertTrue(case["presentation"]["partial"])
                self.assertNotIn("hiddenDescendantCount", case["presentation"])

    def test_expected_sibling_and_group_order_uses_server_encounter_order(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                selected = [item for call in case["calls"]
                            if call["tool"] == "list_items" and "result" in call
                            for item in call["result"]["items"]]
                rows = case["presentation"]["outline"]
                for sibling_parent in {parent(item) for item in selected}:
                    if sibling_parent is not None:
                        self.assertEqual([row["id"] for row in rows
                                          if row["parent"] == sibling_parent and not row["context"]],
                                         [item["id"] for item in selected
                                          if parent(item) == sibling_parent])
                # Check the declared group order against ancestry, without producing a tree.
                by_id = {row["id"]: row for row in rows}
                first_seen_groups = []
                for item in selected:
                    root = item["id"]
                    seen = set()
                    while by_id[root]["parent"] in by_id:
                        self.assertNotIn(root, seen)
                        seen.add(root)
                        root = by_id[root]["parent"]
                    if root not in first_seen_groups:
                        first_seen_groups.append(root)
                self.assertEqual([row["id"] for row in rows if row["parent"] not in by_id],
                                 first_seen_groups)

    def test_empty_partial_pagination_and_backlog_expectations(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                pages = [call["result"] for call in case["calls"]
                         if call["tool"] == "list_items" and "result" in call]
                last, first = pages[-1], pages[0]
                presentation = case["presentation"]
                partial = last["hasMore"] or bool(presentation["unresolvedParents"])
                self.assertEqual(presentation["partial"], partial)
                self.assertEqual(presentation["empty"], not partial and not presentation["outline"]
                                 and last["totalCount"] == 0)
                if not partial:
                    self.assertEqual(sum(len(page["items"]) for page in pages), last["totalCount"])
                calls = case["calls"]
                for index, call in enumerate(calls):
                    if call["tool"] == "list_items" and "cursor" in call["arguments"]:
                        earlier = [entry["result"] for entry in calls[:index]
                                   if entry["tool"] == "list_items" and "result" in entry]
                        self.assertTrue(earlier[-1]["hasMore"])
                        self.assertEqual(call["arguments"]["cursor"], earlier[-1]["nextCursor"])
                offer = presentation["backlogOffer"]
                if presentation["empty"] and first["view"] == "active":
                    count = last.get("taskViewCounts", {}).get("backlog")
                    self.assertEqual(offer, False if count == 0 else {"count": count})
                else:
                    self.assertIs(offer, False)
                if not case["userAskedBacklog"]:
                    self.assertFalse(any(call["arguments"].get("view") == "backlog"
                                         for call in calls))

    def test_malformed_relations_and_task_fields_on_plans_are_rejected(self):
        example = documented_examples()[0]
        request = copy.deepcopy(example["arguments"])
        request["filters"] = {"parentPlanId": 42}
        with self.assertRaises(ValidationError):
            Draft202012Validator(CATALOG["inputSchemas"]["list_items"]).validate(request)
        plan_case = next(case for case in CASES if case["name"] == "skyline_plan_core")
        malformed = copy.deepcopy(plan_case["calls"][0]["result"])
        plan = next(item for item in malformed["items"] if item["type"] == "plan")
        plan["status"] = "todo"
        with self.assertRaises(ValidationError):
            Draft202012Validator(CATALOG["outputSchemas"]["list_items"]).validate(malformed)
        plan.pop("status")
        plan["backlog"] = True
        with self.assertRaises(ValidationError):
            Draft202012Validator(CATALOG["outputSchemas"]["list_items"]).validate(malformed)

    def test_fixture_coverage_and_skill_interface_remain_explicit(self):
        self.assertEqual({case["name"] for case in CASES}, {
            "skyline_plan_core", "autonomous_tasks", "plan_with_tasks", "nested_subplan",
            "historical_task_parent", "ancestors_outside_view", "unresolved_ancestor",
            "plan_alone_zero_tasks", "plan_progress_and_approval", "empty_with_backlog",
            "empty_without_backlog", "missing_counters", "empty_missing_counters",
            "relations_across_pages", "partial_page", "requested_backlog_context"})
        self.assertEqual(skills.validate_skill(SKILL / "SKILL.md"), [])
        frontmatter = re.match(r"---\n(.*?)\n---", (SKILL / "SKILL.md").read_text(), re.DOTALL)
        self.assertIs(yaml.safe_load(frontmatter.group(1))["disable-model-invocation"], True)
        interface = yaml.safe_load((SKILL / "agents/openai.yaml").read_text())
        self.assertIs(interface["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$nestor-beta:next-tasks", interface["interface"]["default_prompt"])
