#!/usr/bin/env python3
"""Validate shared skill YAML without rejecting intentional client extensions."""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit(
        "FAIL PyYAML is required; install scripts/requirements-validation.txt "
        "in the Python environment used for validation."
    )


class UniqueKeyLoader(yaml.SafeLoader):
    """Duplicate keys otherwise silently replace the field being checked."""

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise yaml.constructor.ConstructorError(
                    None, None, "mapping keys must be unique strings", key_node.start_mark
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def validate_skill(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, re.DOTALL)
    if frontmatter is None:
        return ["frontmatter is missing"]
    try:
        data = yaml.load(frontmatter.group(1), Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        return [f"invalid YAML: {error}"]
    if not isinstance(data, dict):
        return ["frontmatter must be a mapping"]

    errors = []
    name = data.get("name")
    if not isinstance(name, str) or not 1 <= len(name) <= 64:
        errors.append("name must be a string of 1 to 64 characters")
    else:
        if (name != name.lower() or name.startswith("-") or name.endswith("-")
                or "--" in name or not all(c.isalnum() or c == "-" for c in name)):
            errors.append("name must contain lowercase letters, digits and single hyphens")
        if name != path.parent.name:
            errors.append(f"name {name!r} must match directory {path.parent.name!r}")
    description = data.get("description")
    if (not isinstance(description, str) or not description.strip()
            or len(description) > 1024):
        errors.append("description must be a non-empty string of at most 1024 characters")
    if "metadata" in data:
        metadata = data["metadata"]
        if not isinstance(metadata, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
        ):
            errors.append("metadata must map string keys to string values")
    if "argument-hint" in data and not isinstance(data["argument-hint"], str):
        errors.append("argument-hint must be a string")
    for key in ("disable-model-invocation", "user-invocable"):
        if key in data and not isinstance(data[key], bool):
            errors.append(f"{key} must be a boolean")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    skills = sorted((root / "plugins").rglob("SKILL.md"))
    errors = [f"{path.relative_to(root)}: {error}"
              for path in skills for error in validate_skill(path)]
    if not skills:
        errors.append("plugins/ contains no SKILL.md")
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"YAML validation passed for {len(skills)} skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
