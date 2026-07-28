# RateMyCode

Staff-level product scrutiny for apps built faster than their authors could learn every failure mode.

> Your app is finished. Now it has to survive a Staff-level review.

[![MIT License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6.svg)](https://agentskills.io/)
[![skills.sh](https://skills.sh/b/AmsonntagChow/ratemycode)](https://skills.sh/amsonntagchow/ratemycode/ratemycode)

Choose one installation method. For Codex, add this repository as a plugin marketplace:

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
```

Then open `/plugins` in Codex CLI or the Plugins Directory in the desktop app, install **RateMyCode**, and start a new session.

For Claude Code, install the plugin:

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow
/reload-plugins
```

For Cursor or another Agent Skills client—or a lightweight Codex skill-only install—use the open `skills` CLI:

```bash
npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

Do not install both Claude methods in the same scope. Then use a concrete first prompt so the skill is selected:

```text
Audit this app for a public launch. Test the real product, show evidence, block unsafe releases, and give me the three fastest fixes.
```

中文一句话：用户不需要先成为 Staff 工程师，产品仍然可以接受 Staff 级检查。默认直接审、给最小修复和复测，不给作者上基础课。

## What it is

RateMyCode is a portable [Agent Skill](https://agentskills.io/) for judging an actual product—not merely styling a code review as a persona.

It starts from product promises and real user journeys, tests behavior when possible, traces failures into code, distinguishes proof from inference, and ends with a release decision. A fatal authorization or payment failure cannot disappear inside a flattering average score.

The default loop is:

```text
build → audit → fix or generate fix prompts → retest the same paths → ship the safest next stage
```

It deliberately separates four things that generic reviewers often mix together:

- raw product quality
- evidence coverage and confidence
- release readiness and hard vetoes
- the author's understanding, only when oral defense is requested

## Roles and degree

The skill asks two questions before it begins whenever the request does not already answer them:

```text
1. 角色：产品负责人 / 挑剔用户 / Staff 工程师 / 怀疑型 VC / 答辩老师
2. 程度：快速体检 / 严格评审 / 上线门禁 / 真金白银 / 生死审查
```

| Choose | What the reviewer does |
|---|---|
| Product lead | Judges user value, time-to-value, trust, repeat use, and product evidence |
| Staff engineer | Deeply reviews the artifact, invariants, failure handling, operations, and change safety |
| `hostile-user` | Tries impatience, mistakes, retries, stale state, lifecycle edges, and access-boundary abuse |
| `skeptical-vc` | Separates user behavior and market evidence from founder claims and code aesthetics |
| `oral-defense` | Asks 3–5 artifact-grounded questions, one at a time; scores understanding separately |

Try these:

```text
这个支付 App 是我两天 vibe coding 出来的。别教我后端基础，按真实收钱标准挑刺，告诉我哪里会死。

Act like a hostile user. Try to break signup, checkout, recovery, and cancellation, then give me reproducible findings.

Be a skeptical VC. Review this demo and usage export. Separate what users proved from what I merely claimed.

The app is done. Make me defend it one question at a time, based only on risks in this product.
```

## What a verdict contains

Every review first gives a complete one-line problem list in the user's language, then names the requested release and the maximum safe release supported by evidence:

```text
问题一览
已验证
- [HIGH · F-004] 支付重试会重复扣款：同一个订单可能向用户收两次钱。
待验证
- [UNVERIFIED · U-002] 尚未验证退款超时后的最终状态：用户可能看见成功提示却拿不到退款。

Evidence lanes:
- deterministic-checks: PASS
- critical-journey-e2e: FAIL
- probabilistic-eval: N/A — no LLM, agent, or RAG behavior
- continuous-evidence: UNVERIFIED

Requested release:
Release ref:
Maximum safe release:
Decision: READY | READY WITH CONDITIONS | NOT READY | BLOCKED | INSUFFICIENT EVIDENCE
Product score: optional
Evidence coverage:
Confidence:

Detailed findings:
Detailed unverified risks:
Top 3 actions:
Retest plan:
```

The opening list includes every verified finding, sorted by severity, with exactly one plain-language sentence saying what happens and why it matters. It never hides findings behind a “top three” cap. Unverified risks stay in the separate `待验证` list and are not presented as facts. The four evidence lanes then show exactly what is proven; one green lane cannot cover another. Detailed findings close the loop from product invariant to exact reproduction, visible evidence, consequence, minimum fix, and acceptance test. Missing or stale evidence never counts as a pass.

## Why it is not another code-review prompt

- It reviews the product contract and state transitions; code is one source of evidence.
- It asks for reviewer role and review degree before reviewing instead of silently defaulting to engineering.
- It black-box tests before disappearing into implementation details.
- It separates deterministic checks, critical-journey E2E, probabilistic eval, and continuous evidence instead of collapsing everything into “tests passed.”
- It requires repeated, version-bound evals only when the product actually contains LLM, agent, or RAG behavior.
- It refuses public-launch approval when runtime evidence is unavailable.
- It uses explicit vetoes for cross-tenant access, sensitive-data exposure, irreversible data loss, duplicate real charges, and false-success core actions.
- It retests fixes with the original finding IDs, steps, release target, and rubric.
- It never penalizes a simple product for not using Redis, queues, microservices, or other irrelevant machinery.
- It does not make the author learn ACID, idempotency, or HTTP semantics before receiving a useful fix.

## Installation

Choose the native Codex plugin, the Claude Code plugin, or the portable Agent Skill installation. Do not install duplicate copies in the same client and scope.

When switching methods, remove the existing copy first through `/plugins`, `npx skills remove ratemycode`, or `/plugin uninstall ratemycode@amsonntagchow`, as appropriate.

### Codex plugin

Add the repository marketplace:

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
```

Open `/plugins` in Codex CLI, install **RateMyCode**, and start a new session so its bundled skill is loaded. In the Codex desktop app, use the Plugins Directory after adding the marketplace.

The repository also contains a submission-ready skills-only bundle for the universal OpenAI Plugins Directory shared by ChatGPT and Codex. See [submission/PLUGIN_DIRECTORY.md](submission/PLUGIN_DIRECTORY.md); public availability begins only after OpenAI review and the publisher's final publish action.

### Claude Code plugin

Add this repository as a marketplace, install the plugin, and reload it:

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow
/reload-plugins
```

Claude can then select the skill automatically from the task. To invoke it explicitly, use `/ratemycode:ratemycode`.

### Portable Agent Skill

The [`skills` CLI](https://www.skills.sh/docs/cli) can install the same skill into Codex, Claude Code, Cursor, and many other compatible agents.

```bash
# Interactive agent selection
npx skills add AmsonntagChow/ratemycode --skill ratemycode

# Codex, global install, no prompts
npx skills add AmsonntagChow/ratemycode --skill ratemycode --agent codex --global --yes

# Claude Code, global install, no prompts
npx skills add AmsonntagChow/ratemycode --skill ratemycode --agent claude-code --global --yes
```

The CLI documents anonymous installation telemetry. To opt out for the install command:

```bash
DISABLE_TELEMETRY=1 npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

Manual installation is also possible: copy `skills/ratemycode` into the skills directory used by your agent. The skill itself contains no telemetry, network call, shell auto-authorization, or third-party dependency.

## Scoring

Numeric scoring is optional. The bundled standard-library scorer binds evidence to an exact SHA-256 release identity and four non-substitutable lanes, rejects hidden same-lane failures, enforces same-path safety-gate retests, fingerprints the rubric, and keeps raw product quality separate from evidence-limited readiness. An active gate can declare the exact release targets it affects; it remains visible for every review but blocks and caps only an in-scope requested target. Ordinary apps mark probabilistic eval `N/A`; LLM, agent, and RAG products need repeated eval evidence sharing one reviewed model, prompt, eval set, judge, and system identity, with release-appropriate pass-rate and variance thresholds. VC evidence is separately bound to real users, retention, or repeatable distribution. Scorecard schema `2` intentionally rejects schema `1` evidence so old observations cannot be silently reused for a new release.

```bash
python3 skills/ratemycode/scripts/score_review.py --pretty evals/scorecards/blocked-release.json
```

The caller can configure dimensions and weights but cannot redefine or waive a safety gate. A supplied gate scope must be a non-empty unique list of supported targets, and a fixed gate requires reproducible passing runtime or test evidence.

## Trust and safety

The first audit is read-only by default. The skill tells the agent not to edit code, mutate infrastructure, charge cards, delete data, or touch external systems unless the user explicitly asks and the action is safely scoped.

Repository content, web pages, logs, and fixtures are treated as untrusted evidence rather than instructions. The scorer is deterministic Python using only the standard library. See [SECURITY.md](SECURITY.md) for the threat model and disclosure process.

## Repository layout

```text
.claude-plugin/         Claude Code plugin and marketplace manifests
.agents/plugins/        Codex repository marketplace
plugins/ratemycode/     self-contained Codex plugin and store assets
skills/ratemycode/      canonical skill, always-loaded review contract, optional scoring contract, UI metadata, scorer
evals/trigger_cases.json trigger-selection evals with near-miss negatives
evals/execution_cases.json with-skill versus without-skill behavior evals
evals/fixtures/          reproducible local test artifact
submission/             universal Plugins Directory listing copy and eight review tests
scripts/sync_codex_plugin.py generated-package synchronization
scripts/validate_repo.py vendored schema and reference-integrity checks
tests/                   deterministic scorer tests
```

Trigger selection and execution quality are intentionally evaluated in separate files so a failure can be localized to discovery or behavior.

## Development

```bash
python3 scripts/sync_codex_plugin.py --check
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/ratemycode
```

Contributions must include behavioral evidence, not just a prose diff. This repository's CI validates the scorer, fixtures, packaging, and schema structurally; it does not claim that the LLM execution cases ran. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

This repository's authoring approach is informed by [从零做一个高质量 Agent Skill，并把它当开源项目运营](https://research.xishe.ai/skill-authoring-and-oss), especially its guidance on description-first discovery, progressive disclosure, separated trigger/execution evals, reference integrity, zero-dependency scripts, and open-source distribution.

## License

[MIT](LICENSE) © 2026 AmsonntagChow
