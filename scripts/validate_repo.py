#!/usr/bin/env python3
"""Validate distribution packages, skill references, and separated eval files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "ratemycode"
SKILL_FILE = SKILL_DIR / "SKILL.md"
CODEX_PLUGIN_DIR = ROOT / "plugins" / "ratemycode"
PACKAGED_SKILL_DIR = CODEX_PLUGIN_DIR / "skills" / "ratemycode"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_PATTERN = re.compile(r"`((?:references|scripts)/[A-Za-z0-9_.-]+)`")
REQUIRED_REPO_FILES = [
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "PRIVACY.md",
    "TERMS.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "plugins/ratemycode/.codex-plugin/plugin.json",
    "plugins/ratemycode/assets/logo.png",
    "plugins/ratemycode/assets/logo.svg",
    "plugins/ratemycode/skills/ratemycode/SKILL.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/skill-bug.yml",
    ".github/workflows/ci.yml",
    "evals/trigger_cases.json",
    "evals/execution_cases.json",
    "evals/fixtures/documentation-drift/internal-api-keys.md",
    "evals/fixtures/documentation-drift/llms.txt",
    "evals/fixtures/documentation-drift/live-api-keys-docs.md",
    "evals/fixtures/documentation-byte-exact/canonical.txt",
    "evals/fixtures/documentation-byte-exact/generated-mirror.txt",
    "evals/fixtures/frontend-dashboard/product.md",
    "evals/fixtures/frontend-dashboard/index.html",
    "evals/fixtures/frontend-dashboard/styles.css",
    "evals/fixtures/frontend-dashboard/app.js",
    "evals/scorecards/blocked-release.json",
    "evals/ledgers/initial.json",
    "evals/ledgers/closed-loop.json",
    "evals/ledgers/closed-loop.md",
    "skills/ratemycode/references/audit-ledger.md",
    "skills/ratemycode/references/review-contract.md",
    "skills/ratemycode/references/numeric-scoring.md",
    "skills/ratemycode/scripts/score_review.py",
    "skills/ratemycode/scripts/audit_ledger.py",
    "scripts/sync_codex_plugin.py",
    "tests/test_score_review.py",
    "tests/test_audit_ledger.py",
    "submission/PLUGIN_DIRECTORY.md",
    "submission/plugin-test-cases.json",
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
    if (SKILL_DIR / "references" / "evidence-and-scoring.md").exists():
        errors.append("legacy references/evidence-and-scoring.md must be split into direct review and scoring references")

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
    elif "$ratemycode" not in metadata_path.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml default prompt must mention $ratemycode")


def load_json(relative: str, errors: list[str]):
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{relative}: invalid JSON: {exc}")
        return None


def validate_claude_plugin(errors: list[str]) -> None:
    manifest = load_json(".claude-plugin/plugin.json", errors)
    if not isinstance(manifest, dict):
        return
    if manifest.get("name") != "ratemycode":
        errors.append("Claude plugin manifest name must be 'ratemycode'")
    if manifest.get("displayName") != "RateMyCode":
        errors.append("Claude plugin displayName must be 'RateMyCode'")
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version
    ):
        errors.append("Claude plugin version must use three-part semantic versioning")
    if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
        errors.append("Claude plugin manifest needs a non-empty description")
    if manifest.get("repository") != "https://github.com/AmsonntagChow/ratemycode":
        errors.append("Claude plugin manifest repository must point to this repository")
    if manifest.get("license") != "MIT":
        errors.append("Claude plugin manifest license must be MIT")
    keywords = manifest.get("keywords")
    if (
        not isinstance(keywords, list)
        or not keywords
        or not all(isinstance(item, str) for item in keywords)
    ):
        errors.append("Claude plugin manifest keywords must be a non-empty string array")

    marketplace = load_json(".claude-plugin/marketplace.json", errors)
    if not isinstance(marketplace, dict):
        return
    if marketplace.get("name") != "amsonntagchow-ratemycode":
        errors.append("Claude marketplace name must be 'amsonntagchow-ratemycode'")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        errors.append("Claude marketplace plugins must be an array")
        return
    matches = [
        item for item in plugins if isinstance(item, dict) and item.get("name") == "ratemycode"
    ]
    if len(matches) != 1:
        errors.append("Claude marketplace must contain exactly one ratemycode plugin entry")
        return
    if matches[0].get("source") not in {".", "./"}:
        errors.append("Claude marketplace ratemycode source must point to the repository root")
    if matches[0].get("version") != manifest.get("version"):
        errors.append("Claude marketplace and plugin manifest versions must match")


def directory_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.relative_to(root).parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def validate_codex_plugin(errors: list[str]) -> None:
    manifest = load_json("plugins/ratemycode/.codex-plugin/plugin.json", errors)
    if not isinstance(manifest, dict):
        return
    claude_manifest = load_json(".claude-plugin/plugin.json", errors)
    if manifest.get("name") != "ratemycode":
        errors.append("Codex plugin manifest name must be 'ratemycode'")
    name = manifest.get("name")
    if not isinstance(name, str) or len(name) > 64 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        errors.append("Codex plugin name must use 1–64 letters, digits, underscores, or hyphens")
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version
    ):
        errors.append("Codex plugin version must use three-part semantic versioning")
    if not isinstance(manifest.get("description"), str) or not 1 <= len(manifest["description"]) <= 1024:
        errors.append("Codex plugin description must contain 1–1,024 characters")
    if isinstance(claude_manifest, dict) and manifest.get("version") != claude_manifest.get("version"):
        errors.append("Codex and Claude plugin versions must match")
    if manifest.get("skills") != "./skills/":
        errors.append("Codex plugin skills path must be './skills/'")
    if manifest.get("repository") != "https://github.com/AmsonntagChow/ratemycode":
        errors.append("Codex plugin repository must point to this repository")
    if manifest.get("license") != "MIT":
        errors.append("Codex plugin license must be MIT")
    if any(field in manifest for field in ("apps", "mcpServers", "screenshots")):
        errors.append("Codex public ZIP must remain skills-only")
    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != "AmsonntagChow":
        errors.append("Codex plugin author must be AmsonntagChow")
    author_name = author.get("name") if isinstance(author, dict) else None

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("Codex plugin interface must be an object")
    else:
        if interface.get("displayName") != "RateMyCode":
            errors.append("Codex plugin displayName must be 'RateMyCode'")
        display_name = interface.get("displayName")
        if isinstance(display_name, str) and (
            len(display_name) > 30 or "\n" in display_name or "\r" in display_name
        ):
            errors.append("Codex plugin displayName must be one line and at most 30 characters")
        for field in ("shortDescription", "longDescription", "developerName", "category"):
            if not isinstance(interface.get(field), str) or not interface[field].strip():
                errors.append(f"Codex plugin interface.{field} must be non-empty")
        short_description = interface.get("shortDescription")
        if isinstance(short_description, str) and (
            len(short_description) > 30 or "\n" in short_description or "\r" in short_description
        ):
            errors.append("Codex plugin shortDescription must be one line and at most 30 characters")
        long_description = interface.get("longDescription")
        if isinstance(long_description, str) and len(long_description) > 4000:
            errors.append("Codex plugin longDescription must be at most 4,000 characters")
        if interface.get("developerName") != author_name:
            errors.append("Codex developerName and author.name must match")
        capabilities = interface.get("capabilities")
        if (
            not isinstance(capabilities, list)
            or not capabilities
            or len(capabilities) > 20
            or not all(
                isinstance(item, str)
                and item.strip()
                and len(item) <= 120
                and "\n" not in item
                and "\r" not in item
                for item in capabilities
            )
        ):
            errors.append("Codex plugin capabilities must contain 1–20 non-empty single-line strings")
        prompts = interface.get("defaultPrompt")
        if (
            not isinstance(prompts, list)
            or not 1 <= len(prompts) <= 3
            or not all(isinstance(prompt, str) and 1 <= len(prompt) <= 128 for prompt in prompts)
        ):
            errors.append("Codex plugin defaultPrompt must contain 1–3 strings of at most 128 characters")
        elif any("\n" in prompt or "\r" in prompt or "@" in prompt for prompt in prompts):
            errors.append("Codex plugin prompts must be single-line and must not contain @mentions")
        elif len({" ".join(prompt.lower().split()) for prompt in prompts}) != len(prompts):
            errors.append("Codex plugin prompts must be unique after normalization")
        for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
            value = interface.get(field)
            if not isinstance(value, str) or not value.startswith("https://"):
                errors.append(f"Codex plugin interface.{field} must be an HTTPS URL")
        for field in ("composerIcon", "logo"):
            value = interface.get(field)
            if not isinstance(value, str) or not value.startswith("./"):
                errors.append(f"Codex plugin interface.{field} must be a relative asset path")
            elif not (CODEX_PLUGIN_DIR / value[2:]).is_file():
                errors.append(f"Codex plugin interface.{field} points to a missing asset")
        if "screenshots" in interface:
            errors.append("skills-only Codex plugin must not define interface.screenshots")
        brand_color = interface.get("brandColor")
        if not isinstance(brand_color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", brand_color):
            errors.append("Codex plugin brandColor must be a six-digit hex color")

    manifest_files = directory_files(CODEX_PLUGIN_DIR / ".codex-plugin")
    if manifest_files != [Path("plugin.json")]:
        errors.append(".codex-plugin must contain only plugin.json")
    forbidden_package_files = [
        path.relative_to(CODEX_PLUGIN_DIR)
        for path in CODEX_PLUGIN_DIR.rglob("*")
        if path.is_file() and (path.name in {".mcp.json", ".app.json"} or path.name == ".DS_Store")
    ]
    if forbidden_package_files:
        errors.append(f"skills-only package contains forbidden files: {forbidden_package_files}")

    logo_path = CODEX_PLUGIN_DIR / "assets" / "logo.png"
    if logo_path.is_file():
        data = logo_path.read_bytes()
        if len(data) > 5 * 1024 * 1024:
            errors.append("Codex plugin logo must be at most 5 MiB")
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append("Codex plugin logo.png must be a valid PNG")
        else:
            width = int.from_bytes(data[16:20], "big")
            height = int.from_bytes(data[20:24], "big")
            if not 48 <= width <= 4096 or not 48 <= height <= 4096 or width != height:
                errors.append("Codex plugin logo must be square and 48–4096 pixels per side")

    marketplace = load_json(".agents/plugins/marketplace.json", errors)
    if not isinstance(marketplace, dict):
        return
    if marketplace.get("name") != "ratemycode":
        errors.append("Codex marketplace name must be 'ratemycode'")
    marketplace_interface = marketplace.get("interface")
    if not isinstance(marketplace_interface, dict) or marketplace_interface.get("displayName") != "RateMyCode":
        errors.append("Codex marketplace displayName must be 'RateMyCode'")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        errors.append("Codex marketplace plugins must be an array")
    else:
        matches = [item for item in plugins if isinstance(item, dict) and item.get("name") == "ratemycode"]
        if len(matches) != 1:
            errors.append("Codex marketplace must contain exactly one ratemycode entry")
        else:
            source = matches[0].get("source")
            if source != {"source": "local", "path": "./plugins/ratemycode"}:
                errors.append("Codex marketplace must point to ./plugins/ratemycode")
            if matches[0].get("policy") != {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            }:
                errors.append("Codex marketplace policy must make the plugin available on install")

    source_files = directory_files(SKILL_DIR)
    packaged_files = directory_files(PACKAGED_SKILL_DIR)
    if source_files != packaged_files:
        errors.append("packaged Codex skill file list differs from canonical skill; run sync_codex_plugin.py")
    for relative in sorted(set(source_files) & set(packaged_files)):
        if (SKILL_DIR / relative).read_bytes() != (PACKAGED_SKILL_DIR / relative).read_bytes():
            errors.append(f"packaged Codex skill differs at {relative}; run sync_codex_plugin.py")


def validate_plugin_submission(errors: list[str]) -> None:
    payload = load_json("submission/plugin-test-cases.json", errors)
    if not isinstance(payload, dict):
        return
    positive = payload.get("positive")
    negative = payload.get("negative")
    if not isinstance(positive, list) or len(positive) != 6:
        errors.append("Plugin submission must contain exactly six positive test cases")
        positive = []
    if not isinstance(negative, list) or len(negative) != 3:
        errors.append("Plugin submission must contain exactly three negative test cases")
        negative = []
    required = {
        "positive": ("id", "prompt", "expected_behavior", "expected_result_shape", "fixture"),
        "negative": ("id", "prompt", "expected_safe_fallback", "reason"),
    }
    for kind, cases in (("positive", positive), ("negative", negative)):
        ids: set[str] = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                errors.append(f"Plugin {kind} test case {index} must be an object")
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id or case_id in ids:
                errors.append(f"Plugin {kind} test case {index} has an invalid or duplicate id")
            else:
                ids.add(case_id)
            for field in required[kind]:
                if not isinstance(case.get(field), str) or not case[field].strip():
                    errors.append(f"Plugin {kind} test case {case_id!r} needs {field}")

    positive_ids = {
        case.get("id")
        for case in positive
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    if "artifact-gate-empty-workspace" not in positive_ids:
        errors.append("Plugin submission must include the empty-workspace artifact-gate test")


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

    cases_by_id = {
        case.get("id"): case
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    missing_target = cases_by_id.get("p03")
    if not isinstance(missing_target, dict) or (
        missing_target.get("should_trigger") is not True
        or missing_target.get("expected_route") != "artifact-gate"
    ):
        errors.append("trigger case 'p03' must select the artifact gate when review intent exists without a target")
    idea_only = cases_by_id.get("n06")
    if not isinstance(idea_only, dict) or idea_only.get("should_trigger") is not False:
        errors.append("trigger case 'n06' must remain a non-trigger for idea-only fundraising help")
    docs_consistency = cases_by_id.get("p01")
    if not isinstance(docs_consistency, dict) or (
        docs_consistency.get("should_trigger") is not True
        or docs_consistency.get("expected_route") != "documentation-consistency"
    ):
        errors.append("trigger case 'p01' must select documentation consistency")
    copy_edit = cases_by_id.get("n10")
    if not isinstance(copy_edit, dict) or copy_edit.get("should_trigger") is not False:
        errors.append("trigger case 'n10' must remain a non-trigger for stylistic copy editing")
    frontend_audit = cases_by_id.get("p08")
    if not isinstance(frontend_audit, dict) or (
        frontend_audit.get("should_trigger") is not True
        or frontend_audit.get("expected_route") != "staff-frontend-engineer"
    ):
        errors.append("trigger case 'p08' must select the staff-frontend-engineer route")
    isolated_component = cases_by_id.get("n07")
    if not isinstance(isolated_component, dict) or isolated_component.get("should_trigger") is not False:
        errors.append("trigger case 'n07' must remain a non-trigger for isolated component review")


def validate_execution_evals(errors: list[str]) -> None:
    payload = load_json("evals/execution_cases.json", errors)
    if not isinstance(payload, dict):
        return
    method = payload.get("method")
    if not isinstance(method, dict) or method.get("arms") != ["with_skill", "without_skill"]:
        errors.append("execution evals must define with_skill and without_skill arms")
    elif (
        method.get("repository_validation") != "structure-only"
        or not isinstance(method.get("behavioral_proof"), str)
        or not method["behavioral_proof"].strip()
    ):
        errors.append("execution evals must state that repository validation is structural, not behavioral proof")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        errors.append("execution evals must be a list of cases")
        return
    if len(cases) < 16:
        errors.append(f"execution evals must contain at least sixteen cases; received {len(cases)}")
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

    required_execution_routes = {
        "missing-artifact-gate": "artifact-gate",
        "missing-explicit-target": "artifact-gate",
        "linked-surfaces-one-subject": "artifact-gate+settings-gate",
        "static-only-release-claim": "staff-engineer",
        "staff-frontend-engineer-browser-audit": "staff-frontend-engineer",
        "cross-document-fact-consistency": "staff-engineer+documentation-consistency",
        "byte-exact-document-mirror": "staff-engineer+documentation-consistency",
        "unavailable-private-document-surface": "staff-engineer+documentation-consistency",
    }
    cases_by_id = {
        case.get("id"): case
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    for case_id, route in required_execution_routes.items():
        case = cases_by_id.get(case_id)
        if case is None:
            errors.append(f"execution evals must include required route coverage {case_id!r}")
        elif case.get("route") != route:
            errors.append(f"execution case {case_id!r} must use route {route!r}")

    documentation_case = cases_by_id.get("cross-document-fact-consistency")
    if isinstance(documentation_case, dict):
        assertions = documentation_case.get("skill_specific_assertions")
        joined = " ".join(assertions) if isinstance(assertions, list) else ""
        for required_phrase in ("atomic facts", "E1 document evidence", "Unknown"):
            if required_phrase not in joined:
                errors.append(
                    "cross-document-fact-consistency assertions must cover "
                    f"{required_phrase!r}"
                )

    byte_case = cases_by_id.get("byte-exact-document-mirror")
    if isinstance(byte_case, dict):
        assertions = byte_case.get("skill_specific_assertions")
        joined = " ".join(assertions) if isinstance(assertions, list) else ""
        for required_phrase in ("byte-exact mode", "unequal hashes", "semantic contradiction"):
            if required_phrase not in joined:
                errors.append(
                    f"byte-exact-document-mirror assertions must cover {required_phrase!r}"
                )

    unavailable_case = cases_by_id.get("unavailable-private-document-surface")
    if isinstance(unavailable_case, dict):
        assertions = unavailable_case.get("skill_specific_assertions")
        joined = " ".join(assertions) if isinstance(assertions, list) else ""
        for required_phrase in ("coverage partial", "Unknown", "signed URL parameters"):
            if required_phrase not in joined:
                errors.append(
                    "unavailable-private-document-surface assertions must cover "
                    f"{required_phrase!r}"
                )

    frontend_case = cases_by_id.get("staff-frontend-engineer-browser-audit")
    if isinstance(frontend_case, dict):
        assertions = frontend_case.get("skill_specific_assertions")
        joined = " ".join(assertions) if isinstance(assertions, list) else ""
        for required_phrase in (
            "keyboard",
            "out-of-order request",
            "320 CSS-pixel",
            "without requiring animation",
            "Does not claim accessibility",
        ):
            if required_phrase not in joined:
                errors.append(
                    "staff-frontend-engineer-browser-audit assertions must cover "
                    f"{required_phrase!r}"
                )


def validate_scorecard(errors: list[str]) -> None:
    command = [
        sys.executable,
        str(SKILL_DIR / "scripts" / "score_review.py"),
        str(ROOT / "evals" / "scorecards" / "blocked-release.json"),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown scorer failure"
        errors.append(f"blocked-release scorecard is invalid: {detail}")
        return
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"score_review.py emitted invalid JSON: {exc}")
        return
    if payload.get("decision") != "BLOCKED":
        errors.append("blocked-release scorecard must exercise a BLOCKED decision")
    expected_lanes = {
        "deterministic-checks",
        "critical-journey-e2e",
        "probabilistic-eval",
        "continuous-evidence",
    }
    lanes = payload.get("evidence_lanes")
    if not isinstance(lanes, dict) or set(lanes) != expected_lanes:
        errors.append("blocked-release scorecard must emit all four evidence lanes")


def validate_audit_ledger(errors: list[str]) -> None:
    initial_path = ROOT / "evals" / "ledgers" / "initial.json"
    closed_path = ROOT / "evals" / "ledgers" / "closed-loop.json"
    initial_result = subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "audit_ledger.py"),
            "validate",
            str(initial_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if initial_result.returncode != 0:
        detail = (
            initial_result.stderr.strip()
            or initial_result.stdout.strip()
            or "unknown initial-ledger failure"
        )
        errors.append(f"initial audit ledger is invalid: {detail}")
        return
    command = [
        sys.executable,
        str(SKILL_DIR / "scripts" / "audit_ledger.py"),
        "validate",
        "--prior",
        str(initial_path),
        str(closed_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown ledger failure"
        errors.append(f"closed-loop audit ledger is invalid: {detail}")
        return
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"audit_ledger.py emitted invalid JSON: {exc}")
        return
    expected = {
        "valid": True,
        "findings": 2,
        "verified_fixed": 1,
        "accepted_risk": 1,
        "unresolved": 0,
        "open_unknowns": 0,
        "current_decision": "READY_WITH_CONDITIONS",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            errors.append(
                f"closed-loop audit ledger summary {key!r} must be {value!r}; "
                f"received {payload.get(key)!r}"
            )
    render_command = [
        sys.executable,
        str(SKILL_DIR / "scripts" / "audit_ledger.py"),
        "render",
        "--language",
        "en",
        "--prior",
        str(initial_path),
        str(closed_path),
    ]
    rendered = subprocess.run(render_command, capture_output=True, text=True, check=False)
    if rendered.returncode != 0:
        detail = rendered.stderr.strip() or rendered.stdout.strip() or "unknown render failure"
        errors.append(f"closed-loop audit ledger cannot render: {detail}")
    else:
        expected_report = ROOT / "evals" / "ledgers" / "closed-loop.md"
        if rendered.stdout != expected_report.read_text(encoding="utf-8"):
            errors.append(
                "evals/ledgers/closed-loop.md is stale; regenerate it with audit_ledger.py"
            )


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_REPO_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required repository file {relative}")
    license_path = ROOT / "LICENSE"
    if license_path.is_file() and "MIT License" not in license_path.read_text(encoding="utf-8"):
        errors.append("LICENSE must contain the MIT License")
    validate_skill(errors)
    validate_claude_plugin(errors)
    validate_codex_plugin(errors)
    validate_plugin_submission(errors)
    validate_trigger_evals(errors)
    validate_execution_evals(errors)
    validate_scorecard(errors)
    validate_audit_ledger(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
