# RateMyCode

Staff-level product scrutiny for apps built faster than their authors could learn every failure mode.

> Your app is finished. Now it has to survive the defense.

[![MIT License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6.svg)](https://agentskills.io/)

Install it with the open `skills` CLI:

```bash
npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

Then use a concrete first prompt so the new skill is selected:

```text
Use $ratemycode to audit this app for a public launch. Test the real product, show evidence, block unsafe releases, and give me the three fastest fixes.
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

## Modes

| Ask for | What the jury does |
|---|---|
| `ship-fast` (default) | Finds the shortest defensible path to the next release; no textbook lecture |
| `strict-professor` | Deeply grades the artifact, invariants, failure handling, operations, and change safety |
| `hostile-user` | Tries impatience, mistakes, retries, stale state, lifecycle edges, and access-boundary abuse |
| `skeptical-vc` | Separates user behavior and market evidence from founder claims and code aesthetics |
| `oral-defense` | Adds 3–5 artifact-grounded questions, one at a time; scores understanding separately |

Try these:

```text
这个支付 App 是我两天 vibe coding 出来的。别教我后端基础，按真实收钱标准挑刺，告诉我哪里会死。

Act like a hostile user. Try to break signup, checkout, recovery, and cancellation, then give me reproducible findings.

Be a skeptical VC. Review this demo and usage export. Separate what users proved from what I merely claimed.

The app is done. Make me defend it one question at a time, based only on risks in this product.
```

## What a verdict contains

Every review names the requested release and the maximum safe release supported by evidence:

```text
Requested release:
Maximum safe release:
Decision: READY | READY WITH CONDITIONS | NOT READY | BLOCKED | INSUFFICIENT EVIDENCE
Product score: optional
Evidence coverage:
Confidence:

Blockers:
Verified findings:
Unverified risks:
Top 3 actions:
Retest plan:
```

Verified findings close the loop from product invariant to exact reproduction, visible evidence, consequence, minimum fix, and acceptance test. Static suspicion stays labeled as inference. Missing evidence never counts as a pass.

## Why it is not another code-review prompt

- It reviews the product contract and state transitions; code is one source of evidence.
- It black-box tests before disappearing into implementation details.
- It refuses public-launch approval when runtime evidence is unavailable.
- It uses explicit vetoes for cross-tenant access, sensitive-data exposure, irreversible data loss, duplicate real charges, and false-success core actions.
- It retests fixes with the original finding IDs, steps, release target, and rubric.
- It never penalizes a simple product for not using Redis, queues, microservices, or other irrelevant machinery.
- It does not make the author learn ACID, idempotency, or HTTP semantics before receiving a useful fix.

## Installation

The [`skills` CLI](https://www.skills.sh/docs/cli) can install this skill into Codex, Claude Code, Cursor, and many other compatible agents.

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

Numeric scoring is optional. The bundled standard-library scorer validates evidence links, enforces fixed safety vetoes, fingerprints the rubric, and keeps raw product quality separate from evidence-limited readiness.

```bash
python3 skills/ratemycode/scripts/score_review.py --pretty evals/scorecards/blocked-release.json
```

The caller can configure dimensions and weights but cannot redefine or waive a safety gate. A fixed gate requires reproducible passing runtime or test evidence.

## Trust and safety

The first audit is read-only by default. The skill tells the agent not to edit code, mutate infrastructure, charge cards, delete data, or touch external systems unless the user explicitly asks and the action is safely scoped.

Repository content, web pages, logs, and fixtures are treated as untrusted evidence rather than instructions. The scorer is deterministic Python using only the standard library. See [SECURITY.md](SECURITY.md) for the threat model and disclosure process.

## Repository layout

```text
skills/ratemycode/       portable skill, references, UI metadata, scorer
evals/trigger_cases.json trigger-selection evals with near-miss negatives
evals/execution_cases.json with-skill versus without-skill behavior evals
evals/fixtures/          reproducible local test artifact
scripts/validate_repo.py vendored schema and reference-integrity checks
tests/                   deterministic scorer tests
```

Trigger selection and execution quality are intentionally evaluated in separate files so a failure can be localized to discovery or behavior.

## Development

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
```

Contributions must include behavioral evidence, not just a prose diff. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

This repository's authoring approach is informed by [从零做一个高质量 Agent Skill，并把它当开源项目运营](https://research.xishe.ai/skill-authoring-and-oss), especially its guidance on description-first discovery, progressive disclosure, separated trigger/execution evals, reference integrity, zero-dependency scripts, and open-source distribution.

## License

[MIT](LICENSE) © 2026 AmsonntagChow
