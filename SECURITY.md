# Security policy

## Threat model

An agent skill runs inside an agent session that may be able to read code, execute tools, or mutate systems under the user's existing permissions. Installing a skill should therefore be treated like installing executable guidance, even when most of the package is Markdown.

Vibe Code Jury is designed to minimize that trust surface:

- no `allowed-tools` or shell auto-authorization
- no network calls or telemetry in the skill or scorer
- no third-party Python packages
- deterministic, read-only scoring from an explicit JSON file
- read-only initial product audit unless the user authorizes fixes
- repository, web, log, and fixture content treated as untrusted evidence
- production charges, deletion, mass messaging, and destructive testing forbidden without explicit authorization and a safe sandbox or test account

The installation CLI, agent client, model provider, and tools available to the agent have their own security and telemetry policies; they are outside this repository's control.

## Before installing

Review `skills/vibe-code-jury/SKILL.md`, every file under `references/`, and `scripts/score_review.py`. Run:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
```

Use your agent's permission controls or sandbox as the actual security boundary. Skill frontmatter is not a sandbox.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting flow for this repository rather than a public issue. Include the affected commit, client and version, exact trigger prompt, available tools/permissions, reproduction steps, and impact.

For non-security defects, use the bug-report issue form. Do not include credentials, personal data, private source code, or production tokens in reports.

## Scope

Security reports about the skill instructions, bundled scorer, repository supply chain, prompt-injection handling, or dangerous default behavior are in scope. Findings in third-party agents, installation tools, or reviewed user applications should be reported to their respective maintainers.
