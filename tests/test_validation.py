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
        for name in ("check.sh", "check-ci.sh", "check-commit.sh", "validate.py", "validate_skills.py"):
            shutil.copy2(ROOT / "scripts" / name, self.root / "scripts" / name)
        self.write(".gitignore", "__pycache__/\n")
        self.write("README.md", "Fixture marketplace\n")
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

    def bump(self, *, changelog="Changed", version_hash="fedcba9876543210"):
        for ecosystem in ("codex", "claude", "cursor", "kimi"):
            path = f"plugins/demo/.{ecosystem}-plugin/plugin.json"
            data = json.loads((self.root / path).read_text())
            data["version"] = "1.1.0"
            self.json(path, data)
        self.json(self.release, {"version": "1.1.0", "version_hash": version_hash, "changelog": changelog})
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
