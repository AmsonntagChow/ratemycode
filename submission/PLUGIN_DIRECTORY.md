# OpenAI Plugins Directory submission

Use this sheet with the [OpenAI plugin submission portal](https://platform.openai.com/plugins). Choose **Skills only** and upload `dist/ratemycode-plugin-1.2.0.zip`.

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

RateMyCode audits a real AI-built product, not just its code style. It first confirms one coherent product target from one or more linked artifacts such as a repository and deployment; an empty or genuinely ambiguous workspace stops before settings, scoring, or a verdict. Then choose a product lead, hostile user, Staff engineer focused on systems, Staff Frontend engineer, skeptical VC, or oral-defense professor and how hard to judge it. The frontend route tests browser behavior, async state, accessibility, performance, responsive support, component systems, and interaction craft. The plugin tests real flows when possible, separates four kinds of evidence, traces failures into the implementation, blocks unsafe launches, and returns every finding in one plain-language list. When explicitly authorized, it records scoped fixes, immutable release identities and scope, independent retests, blockers, release checks, venture signals, scoring metadata, and user-accepted risk in a durable JSON snapshot chain with generated English or Chinese Markdown reports.

## Starter prompts

1. As a Staff engineer focused on systems, audit this app for public launch: list every issue and name the three to fix first.
2. As a Staff Frontend engineer, test this app's browser behavior, accessibility, performance, responsive support, and interaction quality for public launch.
3. As a hostile user, strictly test signup, checkout, recovery, and cancellation.
4. As a skeptical VC, separate product evidence from founder claims and name the cheapest next test.

## Review tests

Enter the six positive and three negative cases from `submission/plugin-test-cases.json`. The public repository fixtures are disposable and require no authentication, private network, or external service.

## Release notes

Version 1.2.0 update. Adds a fail-closed artifact gate before settings; also includes experience-coherence review, convention persistence, concurrent-state probes, and independent fix-batch delta audits.

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
- Upload the final ZIP and square logo, then paste the three starter prompts and nine review tests.
- Complete release notes and policy attestations, then submit for review.
- Wait for security scanning and review. Approval does not publish automatically; return to the portal and choose **Publish**.
