"""Exercise real Git commits/merges and the same entry points used in CI."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("validate_skills", ROOT / "scripts/validate_skills.py")
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)


class RepositoryValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="marketplace-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.bin = Path(self.temp.name) / "bin"
        self.bin.mkdir()
        # Only the CLI boundary is stubbed. Git and repository validation are real.
        self.claude = self.bin / "claude"
        self.claude.write_text(
            '#!/bin/sh\n[ "$1 $2 $4" = "plugin validate --strict" ] || exit 42\n'
            'exit "${TEST_CLAUDE_EXIT:-0}"\n'
        )
        self.claude.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            VALIDATION_PYTHON=sys.executable,
            GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
            CI="false", PYTHONDONTWRITEBYTECODE="1",
        )
        for directory in (".githooks", "scripts"):
            (self.root / directory).mkdir()
        for source in (ROOT / ".githooks").iterdir():
            shutil.copy2(source, self.root / ".githooks" / source.name)
        for name in ("check.sh", "check-ci.sh", "check-commit.sh", "validate.py", "validate_skills.py", "plugin_release_history.py"):
            shutil.copy2(ROOT / "scripts" / name, self.root / "scripts" / name)
        self.write(".gitignore", "__pycache__/\n")
        self.write("README.md", "Fixture marketplace\n")
        self.json("plugin-release-history.json", [])
        for ecosystem, catalog in (
            ("codex", ".agents/plugins/marketplace.json"),
            ("claude", ".claude-plugin/marketplace.json"),
            ("cursor", ".cursor-plugin/marketplace.json"),
            ("kimi", ".kimi-plugin/marketplace.json"),
        ):
            if ecosystem == "codex":
                source = {"source": "local", "path": "./plugins/demo"}
                entry, root = {"name": "demo", "source": source}, {"name": "fixture"}
            elif ecosystem == "kimi":
                # Kimi Code names its entries `id` and versions the catalog root.
                entry, root = {"id": "demo", "source": "./plugins/demo"}, {"version": "2"}
            else:
                entry, root = {"name": "demo", "source": "./plugins/demo"}, {"name": "fixture"}
            self.json(catalog, root | {"plugins": [entry]})
            manifest = {
                "name": "demo", "version": "1.0.0", "skills": "./skills/",
            }
            if ecosystem == "cursor":
                manifest["rules"] = "./rules/"
            self.json(f"plugins/demo/.{ecosystem}-plugin/plugin.json", manifest)
        self.release = "plugins/demo/plugin-release.json"
        self.json(self.release, {"version": "1.0.0", "version_hash": "0123456789abcdef", "changelog": "Initial release"})
        self.skill = "plugins/demo/skills/example/SKILL.md"
        self.write_skill()
        self.write("plugins/demo/rules/a.md", "a\n")
        self.write("plugins/demo/rules/b.md", "b\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Validation fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", ".githooks")
        self.commit("initial")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", self.base)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def json(self, path, data):
        self.write(path, json.dumps(data) + "\n")

    def write_skill(self, version_hash="0123456789abcdef", description="Fixture skill."):
        # A released plugin's skill declares its release's hash; None declares none.
        body = f'Pass `{{ "version_hash": "{version_hash}" }}`.\n' if version_hash else "Body.\n"
        self.write(self.skill, f"---\nname: example\ndescription: {description}\n---\n{body}")

    def run_command(self, *args, ok=True, env=None):
        result = subprocess.run(args, cwd=self.root, env=self.env | (env or {}),
                                text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def git(self, *args, **kwargs):
        return self.run_command("git", *args, **kwargs)

    def commit(self, message):
        self.git("add", ".")
        return self.git("commit", "-qm", message)

    def check(self, *args, **kwargs):
        return self.run_command("./scripts/check.sh", *args, **kwargs)

    def bump(self, *, changelog="Changed", version_hash="fedcba9876543210", version="1.1.0"):
        source = self.base
        previous = json.loads(self.git("show", f"{source}:{self.release}").stdout)
        history = json.loads((self.root / "plugin-release-history.json").read_text())
        if not any(entry["version_hash"] == previous["version_hash"] for entry in history):
            history.append({"name": "demo", "version": previous["version"],
                            "version_hash": previous["version_hash"], "commit": source,
                            "validation_run": "https://github.com/massdo/massdo-marketplace/actions/runs/1"})
            self.json("plugin-release-history.json", history)
        for ecosystem in ("codex", "claude", "cursor", "kimi"):
            path = f"plugins/demo/.{ecosystem}-plugin/plugin.json"
            data = json.loads((self.root / path).read_text())
            data["version"] = version
            self.json(path, data)
        self.json(self.release, {"version": version, "version_hash": version_hash, "changelog": changelog})
        self.write_skill(version_hash)

    def divergent_branches(self, conflict=False):
        self.git("switch", "-qc", "left")
        self.write("README.md" if conflict else "left.md", "left\n")
        self.commit("left")
        left = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("switch", "-qc", "right", self.base)
        self.write("README.md" if conflict else "right.md", "right\n")
        self.commit("right")
        self.git("switch", "-q", "left")
        return left

    def test_merge_of_individually_valid_branches_is_rejected(self):
        self.git("switch", "-qc", "left")
        self.git("rm", "plugins/demo/rules/a.md")
        self.commit("drop a")
        left = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("switch", "-qc", "right", self.base)
        self.git("rm", "plugins/demo/rules/b.md")
        self.commit("drop b")
        self.git("switch", "-q", "left")
        failed = self.git("merge", "--no-ff", "--no-edit", "right", ok=False)
        self.assertIn("missing", failed.stdout + failed.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), left)
        self.assertTrue((self.root / ".git/MERGE_HEAD").exists())

    def test_valid_merge_uses_first_parent_as_baseline(self):
        left = self.divergent_branches()
        self.git("merge", "--no-ff", "--no-edit", "right")
        self.assertEqual(self.git("rev-parse", "HEAD^1").stdout.strip(), left)
        self.assertEqual(len(self.git("rev-list", "--parents", "-n1", "HEAD").stdout.split()), 3)

    def test_manual_commit_after_no_commit_merge_runs_hook(self):
        left = self.divergent_branches()
        self.git("merge", "--no-ff", "--no-commit", "right")
        self.git("commit", "-qm", "merge", ok=False, env={"TEST_CLAUDE_EXIT": "1"})
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), left)
        self.git("commit", "-qm", "merge")

    def test_conflict_resolution_runs_pre_commit(self):
        self.divergent_branches(conflict=True)
        self.git("merge", "--no-ff", "--no-edit", "right", ok=False)
        self.write("README.md", "resolved\n")
        self.git("add", "README.md")
        self.git("commit", "-qm", "resolved", ok=False, env={"TEST_CLAUDE_EXIT": "1"})
        self.git("commit", "-qm", "resolved")

    def test_fast_forward_has_no_commit_hook(self):
        self.git("switch", "-qc", "feature")
        self.write("README.md", "change\n")
        self.commit("change")
        self.git("switch", "-q", "main")
        self.git("merge", "--ff-only", "feature", env={"TEST_CLAUDE_EXIT": "1"})

    def test_invalid_index_cannot_be_hidden_by_valid_worktree(self):
        path = "plugins/demo/.claude-plugin/plugin.json"
        original = (self.root / path).read_text()
        self.json(path, {"name": 123})
        self.git("add", path)
        self.write(path, original)
        staged = self.git("show", f":{path}").stdout
        self.git("commit", "-qm", "invalid", ok=False)
        self.assertEqual(self.git("show", f":{path}").stdout, staged)
        self.assertEqual((self.root / path).read_text(), original)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), self.base)

    def test_valid_index_preserves_invalid_unstaged_edit(self):
        self.write("README.md", "staged change\n")
        self.git("add", "README.md")
        self.write(self.skill, "unfinished unstaged skill\n")
        self.git("commit", "-qm", "valid index")
        self.assertEqual((self.root / self.skill).read_text(), "unfinished unstaged skill\n")
        self.assertIn("description:", self.git("show", f"HEAD:{self.skill}").stdout)

    def test_partial_commit_uses_temporary_git_index(self):
        path = "plugins/demo/.claude-plugin/plugin.json"
        self.json(path, {"name": 123})
        self.git("add", path)
        self.write("README.md", "only this change\n")
        self.git("commit", "--only", "-qm", "partial", "--", "README.md")
        self.assertEqual(json.loads(self.git("show", f"HEAD:{path}").stdout)["name"], "demo")
        self.assertEqual(json.loads(self.git("show", f":{path}").stdout)["name"], 123)

    def test_untracked_file_cannot_satisfy_declared_directory(self):
        self.git("rm", "plugins/demo/rules/a.md", "plugins/demo/rules/b.md")
        self.write("plugins/demo/rules/untracked.md", "not part of commit\n")
        self.git("commit", "-qm", "missing rules", ok=False)
        self.assertTrue((self.root / "plugins/demo/rules/untracked.md").exists())

    def test_command_wrapper_directory_is_rejected_without_manifest_declaration(self):
        self.write("plugins/demo/commands/example.md", "duplicate skill entry point\n")
        result = self.check(ok=False)
        self.assertIn("ships a commands/ directory", result.stderr)

    def test_command_declaration_is_rejected_in_each_manifest(self):
        for ecosystem in ("codex", "claude", "cursor", "kimi"):
            with self.subTest(ecosystem=ecosystem):
                path = f"plugins/demo/.{ecosystem}-plugin/plugin.json"
                original = (self.root / path).read_text()
                manifest = json.loads(original)
                manifest["commands"] = "./skills/"
                self.json(path, manifest)
                result = self.check(ok=False)
                self.assertIn(f"{ecosystem} manifest declares commands", result.stderr)
                self.write(path, original)

    def test_kimi_mcp_url_must_match_mcp_json(self):
        self.json("plugins/demo/mcp.json", {"mcpServers": {"journal": {"type": "http", "url": "https://a.example/mcp"}}})
        path = "plugins/demo/.kimi-plugin/plugin.json"
        manifest = json.loads((self.root / path).read_text())
        manifest["mcpServers"] = {"journal": {"url": "https://a.example/mcp"}}
        self.json(path, manifest)
        self.check()
        manifest["mcpServers"] = {"journal": {"url": "https://b.example/mcp"}}
        self.json(path, manifest)
        result = self.check(ok=False)
        self.assertIn("mcpServers.journal", result.stderr)

    def test_nestor_grouped_read_protection_is_required_in_body(self):
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        self.check()
        path = "plugins/nestor/skills/nestor/SKILL.md"
        original = (self.root / path).read_text()
        self.write(path, "\n".join(
            line for line in original.splitlines()
            if not line.startswith("- `get_item_burst`:")
        ) + "\n")
        result = self.check(ok=False)
        self.assertIn("omits antipattern 'get_item_burst'", result.stderr)

    def test_nestor_conflict_current_item_protection_is_required_in_body(self):
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        path = "plugins/nestor/skills/nestor/SKILL.md"
        original = (self.root / path).read_text()
        self.write(path, original.replace(
            "Take that current item from `details.current` when the conflict includes it.",
            "Take that current item from the conflict payload.",
        ).replace(
            "Call `get_item` once only when the rejection has no `details.current`",
            "Call `get_item` once after every rejected precondition",
        ))
        result = self.check(ok=False)
        self.assertIn("does not take the current item from a precondition conflict", result.stderr)
        self.assertIn("drops the empty-conflict get_item fallback", result.stderr)

    def test_nestor_distributed_resources_reject_obsolete_item_version_tool(self):
        for name in ("nestor", "nestor-beta"):
            shutil.copytree(ROOT / "plugins" / name, self.root / "plugins" / name)
        self.check()
        for name in ("nestor", "nestor-beta"):
            with self.subTest(plugin=name):
                path = f"plugins/{name}/skills/example/references/obsolete.md"
                self.write(path, "Use `get_item_version` to check freshness.\n")
                result = self.check(ok=False)
                self.assertIn("obsolete get_item_version instruction", result.stderr)
                (self.root / path).unlink()

    def test_nestor_conditional_read_examples_reject_invalid_mcp_inputs(self):
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        version_hash = "1" + json.loads((self.root / "plugins/nestor/plugin-release.json").read_text())["version_hash"]
        path = "plugins/nestor/skills/nestor/references/invalid.md"
        valid = {"ref": "brown_turtle", "known": None,
                 "scope": {"mode": "global"}, "version_hash": version_hash}
        cases = [
            ({key: value for key, value in valid.items() if key != "known"}, "omits known"),
            (valid | {"known": {"version": 3}}, "complete version/ETag pair"),
            (valid | {"known": {"version": True, "etag": "held"}}, "complete version/ETag pair"),
            (valid | {"known": {"version": 0, "etag": "held"}}, "complete version/ETag pair"),
            (valid | {"known": {"version": 3, "etag": ""}}, "complete version/ETag pair"),
            (valid | {"known": [None]}, "complete version/ETag pair"),
            (valid | {"ref": ["brown_turtle"], "known": None}, "known must align"),
            (valid | {"ref": ["brown_turtle", "brown_turtle"], "known": [None]}, "known must align"),
            (valid | {"ref": [], "known": []}, "needs 1 to 5 refs"),
            (valid | {"ref": ["brown_turtle"] * 6, "known": [None] * 6}, "needs 1 to 5 refs"),
            (valid | {"ref": [7], "known": [None]}, "refs must be strings"),
            (valid | {"version_hash": "not-the-release-hash"}, "version_hash does not match"),
            (valid | {"version_hash": version_hash[1:]}, "version_hash does not match"),
            (valid | {"version_hash": "2" + version_hash[1:]}, "version_hash does not match"),
            (valid | {"version_hash": "1ffffffffffffffff"}, "version_hash does not match"),
        ]
        for example, diagnostic in cases:
            with self.subTest(example=example):
                self.write(path, "```json\n" + json.dumps(example) + "\n```\n")
                result = self.check(ok=False)
                self.assertIn(diagnostic, result.stderr)
        self.write(path, "```json\n{invalid}\n```\n")
        self.assertIn("invalid JSON example", self.check(ok=False).stderr)

    def test_nestor_conditional_read_examples_accept_mixed_and_single_arrays(self):
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        version_hash = "1" + json.loads((self.root / "plugins/nestor/plugin-release.json").read_text())["version_hash"]
        path = "plugins/nestor/skills/nestor/references/grouped.md"
        pair = {"version": 3, "etag": "held"}
        for refs, known in ((["brown_turtle"], [None]),
                            (["brown_turtle", "gray_xerinae", "brown_turtle"], [pair, None, pair])):
            with self.subTest(refs=refs):
                example = {"ref": refs, "known": known,
                           "scope": {"mode": "global"}, "version_hash": version_hash}
                self.write(path, "```json\n" + json.dumps(example) + "\n```\n")
                self.check()

    def test_nestor_unchanged_examples_do_not_repeat_content_or_etag(self):
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        path = "plugins/nestor/skills/nestor/references/unchanged.md"
        for field in ("item", "title", "body", "tags", "relations", "etag"):
            with self.subTest(field=field):
                example = {"id": "DsoA", "version": 3, "unchanged": True, field: "repeated"}
                self.write(path, "```json\n" + json.dumps(example) + "\n```\n")
                result = self.check(ok=False)
                self.assertIn("must not repeat content or ETag", result.stderr)

    def test_missing_baseline_is_an_error(self):
        result = self.check("--baseline", "missing-ref", ok=False)
        self.assertIn("not an available commit", result.stderr)

    def test_release_absent_from_base_is_allowed(self):
        # A base from before the plugin published a release. The hook now refuses
        # that state, so the commit is built the way a clone without hooks would.
        self.git("rm", self.release)
        self.write_skill(None)
        self.git("add", ".")
        tree = self.git("write-tree").stdout.strip()
        base = subprocess.run(["git", "commit-tree", tree, "-p", self.base],
                              cwd=self.root, env=self.env, input="no release\n",
                              capture_output=True, text=True, check=True).stdout.strip()
        self.bump()
        self.check("--baseline", base)

    def test_version_bump_requires_new_changelog_and_hash(self):
        for field, value in (("changelog", "Initial release"), ("version_hash", "0123456789abcdef")):
            with self.subTest(field=field):
                self.bump(**{field: value})
                result = self.check("--baseline", self.base, ok=False)
                self.assertIn(f"{field} is unchanged", result.stderr)

    def test_release_gate_rejects_plugin_edits_additions_and_deletions(self):
        for path, content in (
            (self.skill, "changed instructions\n"),
            ("plugins/demo/skills/example/agents/openai.yaml", "interface: {}\n"),
            ("plugins/demo/rules/a.md", None),
        ):
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_text() if target.exists() else None
                if content is None:
                    target.unlink()
                elif path == self.skill:
                    self.write(path, original + content)
                else:
                    self.write(path, content)
                result = self.check("--baseline", self.base, "--require-release", ok=False)
                self.assertIn("demo: plugin files changed", result.stderr)
                self.assertIn("must increase", result.stderr)
                if original is None:
                    target.unlink()
                else:
                    self.write(path, original)

    def test_release_gate_accepts_complete_bump(self):
        self.bump()
        self.check("--baseline", self.base, "--require-release")

    def test_release_gate_rejects_unchanged_hash_or_changelog(self):
        for field, value in (("changelog", "Initial release"), ("version_hash", "0123456789abcdef")):
            with self.subTest(field=field):
                self.bump(**{field: value})
                result = self.check("--baseline", self.base, "--require-release", ok=False)
                self.assertIn(f"{field} is unchanged", result.stderr)

    def test_release_gate_rejects_version_rollback(self):
        self.bump(version="0.9.0")
        result = self.check("--baseline", self.base, "--require-release", ok=False)
        self.assertIn("must increase", result.stderr)

    def test_release_gate_allows_repository_only_changes_and_new_plugins(self):
        self.write("README.md", "Repository documentation changed\n")
        self.check("--baseline", self.base, "--require-release")
        shutil.copytree(ROOT / "plugins/nestor", self.root / "plugins/nestor")
        self.check("--baseline", self.base, "--require-release")

    def test_release_gate_requires_baseline(self):
        result = self.check("--require-release", ok=False)
        self.assertIn("--require-release requires --baseline", result.stderr)

    def test_release_gate_ci_requires_bump_only_for_main_pr(self):
        self.write_skill(description="Changed skill.")
        self.commit("work in progress")
        event = {"GITHUB_EVENT_NAME": "pull_request", "PR_BASE_SHA": self.base}
        result = self.run_command("./scripts/check-ci.sh", ok=False,
                                  env=event | {"PR_BASE_REF": "main"})
        self.assertIn("demo: plugin files changed", result.stderr)
        self.run_command("./scripts/check-ci.sh", env=event | {"PR_BASE_REF": "staging"})
        self.bump()
        self.run_command("./scripts/check-ci.sh", env=event | {"PR_BASE_REF": "main"})

    def test_release_gate_ci_checks_entire_main_push(self):
        self.write_skill(description="Changed skill.")
        self.commit("plugin change")
        self.write("README.md", "Later repository change\n")
        self.commit("repository change")
        event = {"GITHUB_EVENT_NAME": "push", "PUSH_BEFORE_SHA": self.base,
                 "PUSH_CREATED": "false", "GITHUB_REF": "refs/heads/main"}
        result = self.run_command("./scripts/check-ci.sh", ok=False, env=event)
        self.assertIn("demo: plugin files changed", result.stderr)

    def test_every_skill_must_declare_version_hash(self):
        self.write_skill(None)
        result = self.check(ok=False)
        self.assertIn("declares no version_hash", result.stderr)
        (self.root / self.release).unlink()
        result = self.check(ok=False)
        self.assertIn("declares no version_hash", result.stderr)
        self.write_skill()
        result = self.check(ok=False)
        self.assertIn("publishes no plugin-release.json", result.stderr)

    def test_independent_plugin_stays_hashless_on_later_releases(self):
        plugin = "plugins/massdo-skills"
        shutil.copytree(ROOT / plugin, self.root / plugin)
        self.check()
        self.commit("independent plugin")
        baseline = self.git("rev-parse", "HEAD").stdout.strip()
        path = f"{plugin}/plugin-release.json"
        release = json.loads((self.root / path).read_text())
        self.assertEqual(set(release), {"version", "changelog"})
        self.write(f"{plugin}/skills/answer-short/SKILL.md",
                   (self.root / plugin / "skills/answer-short/SKILL.md").read_text() + "\nNew instructions.\n")
        result = self.check("--baseline", baseline, "--require-release", ok=False)
        self.assertIn("massdo-skills: plugin files changed but version must increase", result.stderr)
        version_prefix, patch_version = release["version"].rsplit(".", 1)
        next_version = f"{version_prefix}.{int(patch_version) + 1}"
        for manifest in (self.root / plugin).glob(".*/plugin.json"):
            data = json.loads(manifest.read_text())
            data["version"] = next_version
            self.json(manifest, data)
        self.json(path, release | {"version": next_version})
        result = self.check("--baseline", baseline, "--require-release", ok=False)
        self.assertIn("changelog is unchanged", result.stderr)
        self.json(path, {"version": next_version, "changelog": "Updated standalone instructions."})
        self.check("--baseline", baseline, "--require-release")
        self.assertEqual(json.loads((self.root / "plugin-release-history.json").read_text()), [])
        (self.root / path).unlink()
        result = self.check("--baseline", baseline, "--require-release", ok=False)
        self.assertIn("massdo-skills: missing plugin-release.json", result.stderr)

    def test_independent_plugin_rejects_reintroduced_references_in_all_resources(self):
        plugin = "plugins/massdo-skills"
        shutil.copytree(ROOT / plugin, self.root / plugin)
        cases = (
            (f"{plugin}/skills/answer-short/SKILL.md", "\nCall NeStOr.\n"),
            (f"{plugin}/skills/articulate/agents/openai.yaml", "\n# nestor dependency\n"),
            (f"{plugin}/skills/extract-signal/references/input.md", 'Send {"version_hash": "0123456789abcdef"}.\n'),
            (f"{plugin}/mcp.json", '{"url":"https://journal.mcp-marketplace.org/mcp"}'),
            (f"{plugin}/nestor.txt", "External service.\n"),
        )
        for path, content in cases:
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_text() if target.exists() else None
                self.write(path, (original or "") + content)
                result = self.check(ok=False)
                self.assertIn("standalone plugin must not reference Nestor or version_hash", result.stderr)
                if original is None:
                    target.unlink()
                else:
                    self.write(path, original)
        path = f"{plugin}/plugin-release.json"
        release = json.loads((self.root / path).read_text())
        for change in ({"version_hash": "0123456789abcdef"}, {"changelog": "Install nestor-beta."}):
            with self.subTest(change=change):
                self.json(path, release | change)
                result = self.check(ok=False)
                self.assertIn("standalone plugin must not reference Nestor or version_hash", result.stderr)
        self.json(path, release)
        self.check()

    def test_history_source_must_match_the_published_release(self):
        self.json("plugin-release-history.json", [{
            "name": "demo", "version": "1.0.0", "version_hash": "ffffffffffffffff",
            "commit": self.base,
            "validation_run": "https://github.com/massdo/massdo-marketplace/actions/runs/1",
        }])
        result = self.check(ok=False)
        self.assertIn("release history disagrees with published source", result.stderr)

    def test_version_bump_must_keep_previous_release_in_history(self):
        self.bump()
        self.json("plugin-release-history.json", [])
        result = self.check("--baseline", self.base, ok=False)
        self.assertIn("must retain the previous release", result.stderr)

    def test_nestor_skills_require_their_own_prefix_and_release_hash(self):
        previous = "demo"
        for name, prefix in (("nestor", "1"), ("nestor-beta", "2")):
            (self.root / "plugins" / previous).rename(self.root / "plugins" / name)
            for path in self.root.rglob("*.json"):
                data = json.loads(path.read_text())
                if not isinstance(data, dict):
                    continue
                if data.get("name") == previous:
                    data["name"] = name
                for entry in data.get("plugins", []):
                    key = "id" if "id" in entry else "name"
                    entry[key] = name
                    if isinstance(entry["source"], dict):
                        entry["source"]["path"] = f"./plugins/{name}"
                    else:
                        entry["source"] = f"./plugins/{name}"
                self.json(path, data)
            self.skill = f"plugins/{name}/skills/example/SKILL.md"
            self.write_skill(prefix + "0123456789abcdef")
            self.check()
            for invalid in ("0123456789abcdef", ("2" if prefix == "1" else "1") + "0123456789abcdef", prefix + "ffffffffffffffff"):
                self.write_skill(invalid)
                result = self.check(ok=False)
                self.assertIn("version_hash does not match", result.stderr)
            previous = name

    def test_ci_compares_multi_commit_push_to_before_sha(self):
        self.bump(changelog="Initial release")
        # Simulate commits from a clone without hooks; no bypass of active hooks.
        self.git("add", ".")
        tree = self.git("write-tree").stdout.strip()
        bad = subprocess.run(["git", "commit-tree", tree, "-p", self.base],
                             cwd=self.root, env=self.env, input="bad release\n",
                             capture_output=True, text=True, check=True).stdout.strip()
        self.check("--baseline", bad)  # Comparing just the last commit misses it.
        result = self.run_command("./scripts/check-ci.sh", ok=False, env={
            "GITHUB_EVENT_NAME": "push", "PUSH_BEFORE_SHA": self.base, "PUSH_CREATED": "false",
        })
        self.assertIn("changelog is unchanged", result.stderr)

    def test_ci_pr_and_first_push_baselines(self):
        self.run_command("./scripts/check-ci.sh", env={"GITHUB_EVENT_NAME": "pull_request", "PR_BASE_SHA": self.base})
        zeros = "0" * 40
        self.run_command("./scripts/check-ci.sh", env={"GITHUB_EVENT_NAME": "push", "PUSH_BEFORE_SHA": zeros, "PUSH_CREATED": "true"})
        self.run_command("./scripts/check-ci.sh", ok=False, env={"GITHUB_EVENT_NAME": "push", "PUSH_BEFORE_SHA": zeros, "PUSH_CREATED": "false"})
        self.run_command("./scripts/check-ci.sh", ok=False, env={"GITHUB_EVENT_NAME": "pull_request", "PR_BASE_SHA": ""})

    def test_missing_claude_is_visible_locally_and_fails_ci(self):
        # Restrict PATH so a real installation cannot mask the missing CLI.
        git_path = shutil.which("git")
        (self.bin / "git").symlink_to(git_path)
        self.claude.unlink()
        env = {"PATH": str(self.bin)}
        local = self.check(env=env)
        self.assertIn("skipped", local.stdout)
        ci = self.check(ok=False, env=env | {"CI": "true"})
        self.assertIn("required in CI", ci.stderr)

    def test_claude_nonzero_exit_fails_check(self):
        self.check(ok=False, env={"TEST_CLAUDE_EXIT": "1"})
        self.check(ok=False, env={"TEST_CLAUDE_EXIT": "2"})

    def test_invalid_yaml_fails_common_entry_point(self):
        self.write_skill(description="Broken: YAML")
        result = self.check(ok=False)
        self.assertIn("invalid YAML", result.stderr)


class SkillFrontmatter(unittest.TestCase):
    def test_missing_yaml_dependency_fails_explicitly(self):
        result = subprocess.run(
            [sys.executable, "-S", str(ROOT / "scripts/validate_skills.py")],
            text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PyYAML is required", result.stderr)

    def validate(self, fields):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example/SKILL.md"
            path.parent.mkdir()
            path.write_text(f"---\n{fields}\n---\nBody\n")
            return skills.validate_skill(path)

    def test_main_and_migration_extensions_remain_accepted(self):
        shared = 'name: example\ndescription: Example.\nargument-hint: "[arg]"\ndisable-model-invocation: true'
        self.assertEqual(self.validate(shared + '\npluginVersion: 1.0.0\nantipattern:\n  - example'), [])
        self.assertEqual(self.validate(shared + '\nmetadata:\n  pluginVersion: "1.0.0"'), [])

    def test_invalid_shapes_are_rejected(self):
        for fields in (
            'name: example\nname: example\ndescription: Duplicate.',
            'name: other\ndescription: Mismatch.',
            'name: example\ndescription: 123',
            'name: example\ndescription: Valid.\nmetadata:\n  count: 1',
            'name: example\ndescription: Valid.\ndisable-model-invocation: "false"',
            'name: example\ndescription: Valid.\nargument-hint: [arg]',
            'name: example\ndescription: "' + 'x' * 1025 + '"',
            '- not-a-mapping',
        ):
            with self.subTest(fields=fields[:80]):
                self.assertTrue(self.validate(fields))


class OfficialClaudeValidator(unittest.TestCase):
    @unittest.skipUnless(shutil.which("claude"), "Claude CLI is optional locally")
    def test_real_cli_rejects_manifest_schema_error_without_authentication(self):
        with tempfile.TemporaryDirectory(prefix="marketplace-claude-") as directory:
            plugin = Path(directory) / "plugin"
            shutil.copytree(ROOT / "plugins/massdo-skills", plugin)
            env = {k: v for k, v in os.environ.items()
                   if k not in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")}
            env.update(CLAUDE_CONFIG_DIR=str(Path(directory) / "config"),
                       DISABLE_AUTOUPDATER="1", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
            command = [shutil.which("claude"), "plugin", "validate", str(plugin), "--strict"]
            valid = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            path = plugin / ".claude-plugin/plugin.json"
            manifest = json.loads(path.read_text())
            manifest["keywords"] = "must be an array"
            path.write_text(json.dumps(manifest))
            invalid = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertEqual(invalid.returncode, 1, invalid.stdout + invalid.stderr)


if __name__ == "__main__":
    unittest.main()
