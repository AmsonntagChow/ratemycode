# Security policy

## Threat model

An agent skill runs inside an agent session that may be able to read code, execute tools, or mutate systems under the user's existing permissions. Installing a skill should therefore be treated like installing executable guidance, even when most of the package is Markdown.

RateMyCode is designed to minimize that trust surface:

- no `allowed-tools` or shell auto-authorization
- no network calls or telemetry in the skill, scorer, or audit-ledger tool
- no third-party Python packages
- deterministic, read-only scoring from an explicit JSON file
- deterministic ledger validation; Markdown is written only when an explicit output path is supplied
- read-only initial product audit unless the user authorizes fixes
- repository, web, log, and fixture content treated as untrusted evidence
- production charges, deletion, mass messaging, and destructive testing forbidden without explicit authorization and a safe sandbox or test account

The audit ledger is a workflow record, not a cryptographic identity or tamper-proof attestation system. Its artifact digests, identity scope, evidence, fixer IDs, reviewer IDs, and copied user statements are caller-provided; the validator checks their format and internal relationships but does not independently reproduce the reviewed artifact or authenticate the people named. `previous_ledger_ref` hashes the exact prior JSON bytes and detects replacement only when a trusted prior file or digest is retained separately. High-stakes governance needs externally signed artifact, CI, reviewer, and risk-owner evidence plus a trust store outside the reviewed repository.

The installation CLI, agent client, model provider, and tools available to the agent have their own security and telemetry policies; they are outside this repository's control.

## Before installing

Review `skills/ratemycode/SKILL.md`, every file under `references/`, and both files under its `scripts/` directory. Run:

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
