# OpenAI Plugins Directory submission

Use this sheet with the [OpenAI plugin submission portal](https://platform.openai.com/plugins). Choose **Skills only** and upload `dist/ratemycode-plugin-1.1.0.zip`.

The public directory is universal: one approved listing can appear in ChatGPT and Codex. Public availability begins only after OpenAI review and the publisher's separate **Publish** action.

## Listing

- **Plugin name:** RateMyCode
- **Short description:** Find blockers before you ship
- **Category:** Productivity
- **Developer:** AmsonntagChow
- **Website:** https://github.com/AmsonntagChow/ratemycode
- **Support:** https://github.com/AmsonntagChow/ratemycode/issues
- **Privacy:** https://github.com/AmsonntagChow/ratemycode/blob/main/PRIVACY.md
- **Terms:** https://github.com/AmsonntagChow/ratemycode/blob/main/TERMS.md
- **Logo and composer icon:** `plugins/ratemycode/assets/logo.png`

**Long description**

RateMyCode audits a real AI-built product, not just its code style. Choose a product lead, hostile user, Staff engineer, skeptical VC, or oral-defense professor, then choose how hard to judge it. The plugin tests real flows when possible, separates four kinds of evidence, traces failures into the implementation, blocks unsafe launches, and returns every finding in one plain-language list. When explicitly authorized, it records scoped fixes, immutable release identities and scope, independent retests, blockers, release checks, venture signals, scoring metadata, and user-accepted risk in a durable JSON snapshot chain with generated English or Chinese Markdown reports.

## Starter prompts

1. As a Staff engineer, audit this app for a public launch: list every issue and name the three to fix first.
2. As a hostile user, strictly test signup, checkout, recovery, and cancellation.
3. As a skeptical VC, separate product evidence from founder claims and name the cheapest next test.

## Review tests

Enter the five positive and three negative cases from `submission/plugin-test-cases.json`. The public repository fixtures are disposable and require no authentication, private network, or external service.

## Release notes

Version 1.1.0 update. Adds a persistent, SHA-256-linked JSON audit ledger and bilingual Markdown report; a complete severity-sorted one-line problem list; report-only, fix-prompts, and authorized fix-and-retest routes; structured artifact scope; evidence-bound workflow blockers, release checks, scoring, and VC signals; repeated probabilistic-eval provenance and thresholds; independent same-path retests; and fail-closed release or investability decisions. It rejects hidden same-release failures, rewritten history, self-review, unrelated proof, stale or static-only fix claims, survived mutations, and agent-authored risk acceptance while keeping accepted risk technically unresolved and active gates unwaived.

## Package contents

The ZIP contains exactly one plugin root:

```text
.codex-plugin/plugin.json
assets/logo.png
assets/logo.svg
skills/ratemycode/SKILL.md
skills/ratemycode/agents/openai.yaml
skills/ratemycode/references/*.md
skills/ratemycode/scripts/*.py
```

It deliberately excludes repository marketplaces, `.git`, README files, tests, fixtures, screenshots, MCP configuration, and app configuration.

## Before submitting

- Select the verified individual or business identity matching `AmsonntagChow` and confirm Apps Management write access.
- Choose only the countries or regions where you are prepared to publish and support the plugin.
- Upload the final ZIP and square logo, then paste the three starter prompts and eight review tests.
- Complete release notes and policy attestations, then submit for review.
- Wait for security scanning and review. Approval does not publish automatically; return to the portal and choose **Publish**.
