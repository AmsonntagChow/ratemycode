#!/usr/bin/env python3
"""Validate the portable skill, references, and separated eval files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "vibe-code-jury"
SKILL_FILE = SKILL_DIR / "SKILL.md"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_PATTERN = re.compile(r"`((?:references|scripts)/[A-Za-z0-9_.-]+)`")
REQUIRED_REPO_FILES = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/skill-bug.yml",
    ".github/workflows/ci.yml",
    "evals/trigger_cases.json",
    "evals/execution_cases.json",
]


def parse_frontmatter(text: str, errors: list[str]) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append("SKILL.md must start with YAML frontmatter")
        return {}, text
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append("SKILL.md frontmatter has no closing delimiter")
        return {}, text
    fields: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:end], start=2):
        if ":" not in line:
            errors.append(f"SKILL.md:{line_number}: invalid frontmatter line")
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key or key in fields:
            errors.append(f"SKILL.md:{line_number}: empty or duplicate frontmatter key")
            continue
        if raw_value.startswith('"'):
            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                errors.append(f"SKILL.md:{line_number}: invalid quoted value: {exc}")
                continue
        else:
            value = raw_value
        if not isinstance(value, str):
            errors.append(f"SKILL.md:{line_number}: frontmatter values must be strings")
            continue
        fields[key] = value
    return fields, "\n".join(lines[end + 1 :])


def validate_skill(errors: list[str]) -> None:
    if not SKILL_FILE.is_file():
        errors.append(f"missing {SKILL_FILE.relative_to(ROOT)}")
        return
    text = SKILL_FILE.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text, errors)
    if set(fields) != {"name", "description"}:
        errors.append(
            "SKILL.md frontmatter must contain exactly name and description; "
            f"received {sorted(fields)}"
        )
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME_PATTERN.fullmatch(name):
        errors.append("skill name must be lowercase hyphen-case")
    if name != SKILL_DIR.name:
        errors.append(f"skill name {name!r} must equal parent directory {SKILL_DIR.name!r}")
    if not 1 <= len(description) <= 1024:
        errors.append(f"description must contain 1–1024 characters; received {len(description)}")
    if "<" in description or ">" in description:
        errors.append("description must not contain angle brackets")
    body_lines = len(body.splitlines())
    if body_lines > 500:
        errors.append(f"SKILL.md body exceeds 500 lines; received {body_lines}")

    references = sorted((SKILL_DIR / "references").glob("*.md"))
    for path in references:
        relative = f"references/{path.name}"
        mentions = text.count(relative)
        if mentions < 2:
            errors.append(f"{relative} must be mentioned at least twice in SKILL.md; received {mentions}")

    linked_paths = sorted(set(PATH_PATTERN.findall(text)))
    for relative in linked_paths:
        if not (SKILL_DIR / relative).is_file():
            errors.append(f"SKILL.md references missing path {relative}")
    for path in references:
        relative = f"references/{path.name}"
        if relative not in linked_paths:
            errors.append(f"unreachable reference file {relative}")
    for path in sorted((SKILL_DIR / "scripts").glob("*")):
        if path.is_file() and f"scripts/{path.name}" not in linked_paths:
            errors.append(f"unreachable script file scripts/{path.name}")

    metadata_path = SKILL_DIR / "agents" / "openai.yaml"
    if not metadata_path.is_file():
        errors.append("missing agents/openai.yaml")
    elif "$vibe-code-jury" not in metadata_path.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml default prompt must mention $vibe-code-jury")


def load_json(relative: str, errors: list[str]):
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{relative}: invalid JSON: {exc}")
        return None


def validate_trigger_evals(errors: list[str]) -> None:
    payload = load_json("evals/trigger_cases.json", errors)
    if not isinstance(payload, dict):
        return
    cases = payload.get("cases")
    if not isinstance(cases, list):
        errors.append("evals/trigger_cases.json: cases must be an array")
        return
    if len(cases) != 20:
        errors.append(f"trigger evals must contain 20 cases; received {len(cases)}")
    ids: set[str] = set()
    positives = negatives = train = holdout = 0
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"trigger case {index} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"trigger case {index} has invalid id")
        elif case_id in ids:
            errors.append(f"duplicate trigger case id {case_id!r}")
        else:
            ids.add(case_id)
        if case.get("should_trigger") is True:
            positives += 1
        elif case.get("should_trigger") is False:
            negatives += 1
        else:
            errors.append(f"trigger case {case_id!r} should_trigger must be boolean")
        if case.get("split") == "train":
            train += 1
        elif case.get("split") == "holdout":
            holdout += 1
        else:
            errors.append(f"trigger case {case_id!r} split must be train or holdout")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"trigger case {case_id!r} must have a non-empty prompt")
    if (positives, negatives) != (10, 10):
        errors.append(f"trigger evals must contain 10 positive and 10 negative cases; received {positives}/{negatives}")
    if (train, holdout) != (12, 8):
        errors.append(f"trigger eval split must be 60/40 (12/8); received {train}/{holdout}")


def validate_execution_evals(errors: list[str]) -> None:
    payload = load_json("evals/execution_cases.json", errors)
    if not isinstance(payload, dict):
        return
    method = payload.get("method")
    if not isinstance(method, dict) or method.get("arms") != ["with_skill", "without_skill"]:
        errors.append("execution evals must define with_skill and without_skill arms")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        errors.append("execution evals must contain at least three cases")
        return
    ids: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"execution case {index} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"execution case {index} has invalid id")
        elif case_id in ids:
            errors.append(f"duplicate execution case id {case_id!r}")
        else:
            ids.add(case_id)
        assertions = case.get("skill_specific_assertions")
        if not isinstance(assertions, list) or len(assertions) < 2:
            errors.append(f"execution case {case_id!r} needs at least two skill-specific assertions")


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_REPO_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required repository file {relative}")
    license_path = ROOT / "LICENSE"
    if license_path.is_file() and "MIT License" not in license_path.read_text(encoding="utf-8"):
        errors.append("LICENSE must contain the MIT License")
    validate_skill(errors)
    validate_trigger_evals(errors)
    validate_execution_evals(errors)
    for relative in ["evals/scorecards/blocked-release.json"]:
        load_json(relative, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
