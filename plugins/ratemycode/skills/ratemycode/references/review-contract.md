# Review contract

Load this contract for every review. It is the canonical definition of targets, evidence, findings, vetoes, verdicts, and re-review identity. Role references add emphasis; they do not redefine this contract.

## Contents

- [Target ladder](#target-ladder)
- [Evidence states](#evidence-states)
- [Evidence lanes](#evidence-lanes)
- [Review record interfaces](#review-record-interfaces)
- [Plain-language verdict interface](#plain-language-verdict-interface)
- [Target-scoped veto contract](#target-scoped-veto-contract)
- [Decision order](#decision-order)
- [Re-review identity](#re-review-identity)

## Target ladder

| Target ID | Supported use | Minimum evidence expected |
|---|---|---|
| `internal-demo` | Controlled demonstration | Golden path runs and failure is recoverable in the controlled environment |
| `private-beta` | Limited real users | Critical journeys, access boundaries, and recovery are tested |
| `public-launch` | Public availability | Runtime evidence covers critical journeys, abuse boundaries, and operations |
| `real-money` | Money or sensitive data | Payment/data invariants, retries, authorization, recovery, and monitoring are verified |
| `high-stakes` | Regulated or consequential use | Domain review, compliance controls, rollback, auditability, and incident response are verified |
| `venture-case` | Venture judgment | Product and market evidence matches the diligence depth; do not treat this as a software release tier |

When even `internal-demo` is unsupported, say `no supported release tier` or describe the narrower fixture actually proven. Never rename an unrun golden path an internal demo.

## Evidence states

| State | Meaning | Typical support |
|---|---|---|
| `E3 REPRODUCED` | Direct, repeatable observation | Browser or network trace, database before/after, exact failing request, repeated runtime test |
| `E2 INSTRUMENTED` | Independent machine-produced support | Automated test, log, metric, trace, persisted state |
| `E1 STATIC` | Reachable code/configuration fact with runtime consequence still inferred | Missing ownership predicate, charge retry without an idempotency control |
| `E0 UNVERIFIED` | Claim, guess, generic concern, or unavailable evidence | Founder statement, documentation promise, checklist speculation |

Severity and evidence strength are independent. An E1 defect may fail a required check and make a target `NOT_READY`, but activate a runtime veto only with E3/E2 evidence or complete deployment evidence that rules out a compensating layer. An E3 cosmetic failure can remain low severity.

Evidence is fresh only when it was produced against the exact artifact or deployment manifest named by the verdict's immutable `sha256:<64 lowercase hex>` `release_ref`. A recent run against another revision is stale, and a mutable alias such as `latest` is not a release identity. Repository CI, JSON/schema validation, and fixture-shape checks prove structure only; never describe them as proof that the reviewed product or an LLM evaluator behaved correctly.

Calibrate severity by consequence: `BLOCKER` means an active veto or the target's core use is unsafe or impossible; `HIGH` means material user, money, data, or release harm; `MEDIUM` means a bounded but real product failure; `LOW` means limited impact that still has a concrete product consequence.

## Evidence lanes

Keep these four lanes separate in every verdict:

```text
EvidenceLane = {
  status: PASS | FAIL | UNVERIFIED | N/A,
  evidence_ids: unique E-###[],
  reason?: required only for N/A
}

EvidenceLanes = {
  deterministic-checks: EvidenceLane,
  critical-journey-e2e: EvidenceLane,
  probabilistic-eval: EvidenceLane,
  continuous-evidence: EvidenceLane
}
```

- Use `deterministic-checks` for current code, type, unit, contract, schema, or other exact checks.
- Use `critical-journey-e2e` only for an exercised user journey on the identified artifact, build, or deployment. Structural repository checks cannot pass it.
- Use `probabilistic-eval` only when the product contains LLM, agent, or RAG behavior. Require repeated runs; bind model, prompt, eval-set, judge, and applicable tool/retrieval configuration; and record pass-rate and variance thresholds before calling it `PASS`. Otherwise mark it `N/A` with a reason.
- Use `continuous-evidence` for logs, metrics, traces, or alerts from the identified running release.

`PASS` and `FAIL` require fresh reproducible evidence that explicitly declares the same lane. `PASS` cannot hide a cited or uncited fresh same-lane fail, mixed, or inconclusive result. `UNVERIFIED` and `N/A` carry no evidence IDs. Never reuse one evidence record across lanes or let one passing lane stand in for another. A failing required lane makes the release not ready; an unverified required lane limits the verdict to insufficient evidence.

## Review record interfaces

```text
Finding = {
  id: F-###,
  severity: BLOCKER | HIGH | MEDIUM | LOW,
  title,
  promise_or_invariant,
  preconditions,
  reproduction_steps,
  expected,
  actual,
  evidence: {id: E-###, state: E1 | E2 | E3, exact_artifact_or_observation}[1..],
  impact,
  suspected_cause: explicitly_labeled_inference,
  minimum_fix_or_agent_prompt,
  acceptance_test,
  adjacent_regression_check
}

Unknown = {
  id: U-###,
  unresolved_condition,
  why_it_matters,
  missing_evidence,
  resolving_test
}
```

A generic warning is not a `Finding`. Connect it to a reachable product state, an invariant, an observed or static fact, and a consequence. Keep hypotheses as `Unknown` until resolved.

## Plain-language verdict interface

```text
IssueLine = [severity · finding.id · optional_retest_status] what_happens: why_it_matters.
UnknownLine = [UNVERIFIED · unknown.id] what_is_not_yet_known: why_it_matters.

Verdict = {
  issues: {
    verified: IssueLine[],
    pending_verification: UnknownLine[]
  },
  evidence_lanes: EvidenceLanes,
  release_ref,
  requested_target,
  maximum_safe_target,
  decision,
  product_score?: numeric_score_only_if_requested,
  evidence_coverage,
  confidence,
  active_gates,
  blocking_gates,
  detailed_findings: Finding[],
  detailed_unknowns: Unknown[],
  priority_actions: Action[0..3],
  retest_plan
}
```

Render `issues` first, in the user's language. Begin every line with severity, then give the plain-language failure and its consequence; retain the stable ID after severity. Include every confirmed finding and every unknown; never cap, merge, or omit them for brevity. Sort confirmed items by `BLOCKER`, `HIGH`, `MEDIUM`, `LOW`, then stable ID. Each line is exactly one ordinary-language sentence describing what happens and why it matters; omit fixes, steps, evidence, causes, and jargon. Keep all unresolved items in the pending-verification group and phrase them as unresolved, not factual. Explicitly state when either group is empty. Show the four-lane evidence panel immediately after the issue list.

The three-item limit applies only to `priority_actions`. Keep distinct IDs when causes, fixes, or retests differ. `skeptical-vc` may replace the release-oriented body with its stage-aware body, but never the complete opening issue groups.

## Target-scoped veto contract

These gate IDs are fixed:

- `authorization-bypass`
- `sensitive-data-exposure`
- `irreversible-data-loss`
- `duplicate-real-charge`
- `critical-flow-false-success`

```text
Gate = {
  id: fixed_gate_id,
  state: active | fixed,
  evidence_ids: unique E-###[],
  retest_evidence_ids: unique E-###[],
  affected_targets?: nonempty_unique_target_id[]
}
```

`affected_targets` uses exact IDs from the target ladder. List every affected target explicitly; omission means all targets for backward compatibility. A gate blocks and caps only when it is active and the requested target is in its scope. Preserve out-of-scope active gates in the report because they may constrain another release target.

`active_gates` contains every active gate and its normalized scope; `blocking_gates` is the subset affecting the requested target.

Activate a gate only from fail/mixed evidence meeting the E3/E2 rule above or from complete deployment evidence with no plausible compensating layer. Gate evidence declares the matching gate ID. A fixed gate requires fresh passing runtime or test evidence bound to that same gate and reproduction path; an unrelated green test cannot close it. Do not waive or average away an in-scope active gate; explicit risk acceptance does not turn it into a technical pass.

## Decision order

Apply the first matching rule:

1. In-scope active gate → `BLOCKED`.
2. Failed required evidence lane or release check → `NOT_READY`.
3. Unverified required lane or check, or static/no runtime evidence for a non-VC release → `INSUFFICIENT_EVIDENCE`.
4. Readiness below the applicable threshold when scoring is requested → `NOT_READY`.
5. Optional gaps remain → `READY_WITH_CONDITIONS`.
6. Otherwise → `READY`.

Report the requested target and the maximum safe target separately. A high-quality artifact with weak evidence can have a strong product assessment and an insufficient-evidence release decision.

## Re-review identity

Preserve the prior target, every finding and unknown ID, reproduction steps, acceptance tests, rubric ID, dimension IDs, and weights. Re-run the same path and adjacent checks. Classify each prior record as `FIXED`, `PARTIALLY_FIXED`, `NOT_FIXED`, `REGRESSED`, or `UNVERIFIABLE`; place only `UNVERIFIABLE` under pending verification. Do not treat a code diff as proof or change the rubric to reward the new implementation.
