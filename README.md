# RateMyCode

English | [简体中文](README.zh-CN.md)

Staff-level product scrutiny for apps built faster than their authors could learn every failure mode.

> Your app is finished. Now it has to survive a Staff-level review.

Ask for one review and you get one verdict:

```text
Audit this app for a public launch. Test the real product, show evidence, block unsafe releases, list every issue, and name the three I should act on first.
```

Attach a durable session goal (`/goal` in Codex; the same sentence as a first message in Claude Code) and the same skill stays on that target across many turns:

```text
/goal use ratemycode to get this app to a defensible public launch
```

You do not have to define done. It will not sign off on its own fix — a change has to survive a fresh retest first. And whatever is still open, it says so.

[![MIT License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6.svg)](https://agentskills.io/)
[![ratemy.sh](https://img.shields.io/badge/ratemy.sh-code-C4500F.svg)](https://code.ratemy.sh/)
[![skills.sh](https://skills.sh/b/AmsonntagChow/ratemycode)](https://skills.sh/amsonntagchow/ratemycode/ratemycode)

Choose one installation method. The `skills` CLI is the shortest and works in Codex, Claude Code, Cursor, and every other Agent Skills client:

```bash
npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

For Claude Code as a plugin instead, run exactly this one command — `/plugin` takes everything after it as a single argument, so a multi-line paste is read as one malformed repository name:

```text
/plugin marketplace add AmsonntagChow/ratemycode
```

Then open `/plugins`, install **RateMyCode** from the menu, and start a new session.

For Codex as a plugin, add this repository as a marketplace:

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
codex plugin add ratemycode@amsonntagchow-ratemycode
```

Then start a new session. In the Codex desktop app, install from the Plugins Directory instead of running the second command.

Do not install both Claude methods in the same scope. No method updates itself: to move to a newer release, run the install again. Then open with either prompt above so the skill is selected.

## What it is

RateMyCode is a portable [Agent Skill](https://agentskills.io/) for judging an actual product—not merely styling a code review as a persona.

It starts from product promises and real user journeys, tests behavior when possible, compares overlapping facts across internal docs, `llms.txt`, schemas, examples, UI copy, and live documentation, traces failures into code, distinguishes proof from inference, and ends with a release decision. A fatal authorization or payment failure cannot disappear inside a flattering average score.

The default loop is:

```text
build → audit → complete verdict
                  ├─ report only (default; no edits)
                  ├─ copy-ready fix prompts (no edits)
                  └─ authorized fixes → same-path + adjacent retests → updated audit ledger
```

It deliberately separates four things that generic reviewers often mix together:

- raw product quality
- evidence coverage and confidence
- release readiness and hard vetoes
- the author's understanding, only when oral defense is requested

Before asking about role or degree, RateMyCode performs a minimal read-only artifact gate. It resolves one coherent product target while allowing linked surfaces such as its repository, deployment, logs, analytics, and documentation. If the current workspace is empty or unrelated, a supplied target is missing, or several independent products are ambiguous, it asks for a project path, repository, deployment URL, attachment, or product-evidence file and stops without inspecting, scoring, or issuing a verdict. An existing project that cannot run still proceeds as a clearly limited static review.

## Roles and degree

After one audit target is resolved, the skill asks two questions before it begins whenever the request does not already answer them:

```text
1. Role: Product lead / Hostile user / Staff engineer (systems/backend) / Staff Frontend engineer / Skeptical VC / Oral-defense examiner
2. Degree: Quick checkup (default) / Strict review / Launch gate / Real-revenue tier / Life-or-death review
```

| Choose | What the reviewer does |
|---|---|
| Product lead | Judges user value, time-to-value, trust, repeat use, and product evidence |
| Staff engineer (systems/backend) | Deeply reviews invariants, security boundaries, concurrency, failure handling, operations, and change safety |
| Staff Frontend engineer | Tests real browser behavior, async state, accessibility, performance, responsive support, component systems, and interaction craft |
| `hostile-user` | Tries impatience, mistakes, retries, stale state, lifecycle edges, and access-boundary abuse |
| `skeptical-vc` | Separates user behavior and market evidence from founder claims and code aesthetics |
| `oral-defense` | Asks 3–5 artifact-grounded questions, one at a time; scores understanding separately |

### Start with the quick checkup

A full-degree audit runs your product, traces failures through the implementation, and re-runs checks. It costs
several times a quick checkup in both time and tokens. If you are on a metered or fixed-quota plan — most
Claude Code, Codex, and Cursor subscriptions are — that cost competes with your actual work, so the quick
checkup is the default: it spends the review on the handful of checks that most often decide whether something
is safe to ship, and stops there.

What you give up is the **floor of assurance** — fewer things get reached — not the honesty of the report.
Every issue found is still reported in full, and everything not reached becomes an explicit unknown with the
one test that would settle it. Escalate when the stakes actually demand it: real money, private data, public
users, or a decision you cannot walk back.

```text
Quick checkup on this app. Tell me the few things that would stop me shipping it, and what you did not check.
```

Try these:

```text
I vibe-coded this payments app in two days. Do not teach me backend basics. Review it against the real-revenue standard and tell me what could kill it.

As a Staff Frontend engineer at launch-gate depth, audit this dashboard in a real browser. Check keyboard and screen-reader use, async state, mobile layouts, performance, and interaction quality.

Act like a hostile user. Try to break signup, checkout, recovery, and cancellation, then give me reproducible findings.

Be a skeptical VC. Review this demo and usage export. Separate what users proved from what I merely claimed.

The app is done. Make me defend it one question at a time, based only on risks in this product.
```

## What a verdict contains

Every review first gives a complete one-line problem list in the user's language, then names the requested release and the maximum safe release supported by evidence:

```text
One-line problem list
- [HIGH · F-004 · open] Payment retries cause duplicate charges: the same order may charge a user twice.
- [HIGH · F-006 · open] API-key expiry differs between the internal doc, llms.txt, and /api-keys/docs: integrators cannot know when credentials will stop working.
- [MEDIUM · F-007 · verified-fixed] Checkout reported success before saving the order: the user could pay for an order that did not exist.

Pending verification
- [UNKNOWN · U-002 · UNVERIFIED] The final state after a refund timeout has not been verified: users may see a success message but never receive the refund.

Evidence lanes:
- deterministic-checks: PASS
- critical-journey-e2e: FAIL
- probabilistic-eval: N/A — no LLM, agent, or RAG behavior
- continuous-evidence: UNVERIFIED

Requested release:
Release ref:
Maximum safe release:
Decision: READY | READY_WITH_CONDITIONS | NOT_READY | BLOCKED | INSUFFICIENT_EVIDENCE
Product score: optional
Evidence coverage:
Confidence:

Detailed findings:
Detailed unverified risks:
Top 3 actions:
Retest plan:
```

The opening list includes every confirmed finding—open, in progress, accepted, or independently fixed—in one severity-sorted view, with exactly one plain-language sentence saying what happens and why it matters. It never hides findings behind a “top three” cap. Unverifiable fixes, open unknowns, and active workflow blockers stay under `Pending verification` and are not presented as resolved facts. The four evidence lanes then show exactly what is proven; one green lane cannot cover another. Detailed findings close the loop from product invariant to exact reproduction, visible evidence, consequence, minimum fix, and acceptance test. Missing or stale evidence never counts as a pass.

When documentation surfaces overlap, the default comparison is fact-level rather than byte-level: wording may differ, but endpoints, permissions, defaults, limits, expiry, errors, and lifecycle rules must remain compatible in the same version and environment. Byte-exact comparison is used only when explicitly requested or required by a generated-mirror contract. A confirmed textual contradiction becomes a normal finding in the opening list. An inaccessible private document or live page stays explicitly unknown; it is never silently counted as consistent, and documentation alone is never treated as proof of runtime behavior.

## Audit ledger and fix loop

When you ask to save the audit or authorize direct fixes, RateMyCode stores a canonical JSON ledger and generates a readable English or Chinese Markdown view. JSON remains the source of truth. The generated report starts with the complete one-line problem list, immediately shows all four evidence lanes, then exposes workflow blockers, release checks, optional scoring, venture evidence when applicable, review identity, progress, root causes, gates, detailed findings, unknowns, and evidence. An `unverifiable` re-review stays in pending verification rather than being presented as fixed.

Ledgers form a snapshot chain. The first file has `previous_ledger_ref: null`; every later file records the SHA-256 of the exact prior JSON bytes and is validated with `--prior`. Prior evidence and record identities cannot be silently deleted or rewritten. The artifact is bound with `sha256-file`, `sha256-tree`, or `sha256-deployment-manifest`, plus a structured `identity_scope` that explicitly names the root, inclusions, exclusions, and symlink policy. Tree identities use a deterministic, sorted file-digest manifest and exclude the ledger itself. The initial release identity, hash method, scope, role, degree, target, rubric ID, and AI-behavior classification remain fixed across the chain.

For non-VC reviews, degree and target are paired exactly: quick check → internal demo, strict review → private beta, launch gate → public launch, real-revenue tier → real money, and life-or-death → high stakes. VC reviews use `venture-case`; their five degrees map to screening, structured diligence, partner review, full diligence, and investment committee. `ai_behavior` is one of `none`, `llm`, `agent`, `rag`, or `mixed`.

Evidence is bound to a stable subject and procedure: reproduction, acceptance, adjacent regression, and mutation records name an `F-###`; unknown-resolution records name a `U-###`; release-lane records have no subject. Workflow-blocker, release-check, and venture-signal proof must also name the exact record it supports, so one favorable result cannot silently stand in for several decisions. Complete code or document inspection may activate a gate only when `deployment_coverage` says the entire deployed scope was checked and a compensating layer was ruled out. It cannot close a gate, clear an unknown, or prove a fix. E0 claims never count as proof.

For non-VC reviews, required evidence lanes fail closed: critical-journey E2E is required at every software tier, deterministic checks from private beta upward, continuous evidence from public launch upward, and repeated probabilistic eval for any LLM, agent, RAG, or mixed behavior. The decision order is active in-scope gate or named blocker → `BLOCKED`; failed required lane/check or unresolved Blocker/High finding → `NOT_READY`; unverified required lane/check, unverifiable finding, or open unknown → `INSUFFICIENT_EVIDENCE`; below-threshold readiness → `NOT_READY`; optional gaps only → `READY_WITH_CONDITIONS`; otherwise → `READY`. VC ledgers mark all software lanes `N/A` and separately derive `INVESTABLE`, `INTERESTING_BUT_UNPROVEN`, `NOT_INVESTABLE_YET`, or `INSUFFICIENT_EVIDENCE` from real users, retention, repeatable distribution, blockers, unknowns, and optional scoring.

The ledger keeps every finding and unknown, shared root causes, exact release identities, user authorization, change references, retest evidence, and one of these states:

```text
open → fixing → fixed-pending-retest → verified-fixed
                                   ├→ partially-fixed / not-fixed / regressed / unverifiable
external-change ─────→ fixed-pending-retest
any work or verification state → blocked (named reason, missing requirement, resolving action)
any technically unresolved state → accepted-risk (only from an explicit user statement)
```

A direct Agent fix uses `origin: authorized-agent` and preserves the user's exact bounded authorization. A change made elsewhere uses `origin: external-change` and leaves authorization `null`; RateMyCode can retest it without inventing retroactive permission. A diff is never enough to claim a fix. `verified-fixed` requires separate current-release acceptance and adjacent-regression evidence in an independent agent or fresh review context. A mutation check must catch the reintroduced failure when practical. Only the user can accept risk; the rationale is optional, the statement and scope are required, and accepted risk remains technically unresolved. A gate whose scope was omitted in the review contract is expanded to an explicit sorted `affected_targets` list in the ledger and cannot be waived by risk acceptance.

The bundled standard-library tool validates the ledger and generates English or Chinese Markdown:

```bash
python3 skills/ratemycode/scripts/audit_ledger.py validate evals/ledgers/initial.json
python3 skills/ratemycode/scripts/audit_ledger.py validate --prior evals/ledgers/initial.json evals/ledgers/closed-loop.json
python3 skills/ratemycode/scripts/audit_ledger.py render --prior evals/ledgers/initial.json --language zh-CN --output audit-report.md evals/ledgers/closed-loop.json
```

The validator enforces structural consistency, release and procedure binding, requires `--prior` for every chained snapshot, verifies continuity, and requires distinct fixer/reviewer IDs. It is not a cryptographic identity, signature, trusted timestamp, or tamper-proof audit system; high-stakes governance still needs externally signed attestations stored outside the reviewed repository. The complete schema and identity procedure are documented in [`audit-ledger.md`](skills/ratemycode/references/audit-ledger.md).

## Why it is not another code-review prompt

- It reviews the product contract and state transitions; code is one source of evidence.
- It asks for reviewer role and review degree before reviewing instead of silently defaulting to engineering.
- It black-box tests before disappearing into implementation details.
- It compares actionable facts across internal docs, `llms.txt`, schemas, examples, UI copy, and live documentation without flagging harmless wording differences.
- It separates deterministic checks, critical-journey E2E, probabilistic eval, and continuous evidence instead of collapsing everything into “tests passed.”
- It requires repeated, version-bound evals only when the product actually contains LLM, agent, or RAG behavior.
- It refuses public-launch approval when runtime evidence is unavailable.
- It uses explicit vetoes for cross-tenant access, sensitive-data exposure, irreversible data loss, duplicate real charges, and false-success core actions.
- It retests fixes with the original finding IDs, steps, release target, and rubric.
- It never penalizes a simple product for not using Redis, queues, microservices, or other irrelevant machinery.
- It does not make the author learn ACID, idempotency, or HTTP semantics before receiving a useful fix.

## Installation

Choose the native Codex plugin, the Claude Code plugin, or the portable Agent Skill installation. Do not install duplicate copies in the same client and scope.

When switching methods, remove the existing copy first through `/plugins`, `npx skills remove ratemycode`, or `/plugin uninstall ratemycode@amsonntagchow-ratemycode`, as appropriate.

### Codex plugin

Add the repository marketplace:

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
codex plugin add ratemycode@amsonntagchow-ratemycode
```

Start a new session so its bundled skill is loaded. In the Codex desktop app, use the Plugins Directory instead of running the second command.

The repository also contains a submission-ready skills-only bundle for the universal OpenAI Plugins Directory shared by ChatGPT and Codex. See [submission/PLUGIN_DIRECTORY.md](submission/PLUGIN_DIRECTORY.md); public availability begins only after OpenAI review and the publisher's final publish action.

### Claude Code plugin

Add this repository as a marketplace, install the plugin, and reload it:

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow-ratemycode
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

Repository content, web pages, logs, and fixtures are treated as untrusted evidence rather than instructions. The scorer and audit-ledger renderer are deterministic Python using only the standard library. See [SECURITY.md](SECURITY.md) for the threat model and disclosure process.

## Repository layout

```text
.claude-plugin/         Claude Code plugin and marketplace manifests
.agents/plugins/        Codex repository marketplace
plugins/ratemycode/     self-contained Codex plugin and store assets
skills/ratemycode/      canonical skill, review/ledger/scoring contracts, UI metadata, validators and renderers
evals/trigger_cases.json trigger-selection evals with near-miss negatives
evals/execution_cases.json with-skill versus without-skill behavior evals
evals/fixtures/          reproducible local test artifact
evals/ledgers/           validated audit-to-fix loop example
submission/             universal Plugins Directory listing copy and eight review tests
scripts/sync_codex_plugin.py generated-package synchronization
scripts/validate_repo.py vendored schema and reference-integrity checks
tests/                   deterministic scorer and audit-ledger tests
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

This repository's authoring approach is informed by [Building a High-Quality Agent Skill from Scratch and Running It as an Open-Source Project](https://research.xishe.ai/skill-authoring-and-oss), especially its guidance on description-first discovery, progressive disclosure, separated trigger/execution evals, reference integrity, zero-dependency scripts, and open-source distribution.

## License

[MIT](LICENSE) © 2026 AmsonntagChow
