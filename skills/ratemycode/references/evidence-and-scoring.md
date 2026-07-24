# Evidence, scoring, and release decisions

Use this protocol in every mode. The score is an aid; the release decision is the product of evidence, required checks, and vetoes.

## Release ladder

| Target | Minimum evidence expected | Default readiness threshold |
|---|---|---:|
| Internal demo | Golden path runs in a controlled environment; failure is recoverable | 50 |
| Private beta | Critical journeys work; access boundaries and recovery are tested | 65 |
| Public launch | Runtime evidence covers critical journeys, abuse boundaries, and operations | 75 |
| Real money or sensitive data | Payment/data invariants, retries, authorization, recovery, and monitoring are verified | 85 |
| High-stakes or regulated | Domain review, compliance controls, rollback, auditability, and incident response are verified | 90 |

These are default calibration points, not universal laws. State any adjustment and never lower a threshold to turn an existing failure into a pass.

When even the internal-demo bar is not supported, say `no supported release tier` or `local fixture with synthetic data only`. Do not stretch “internal demo” to imply that a golden path has run when it has not.

## Evidence levels

| Level | Meaning | Examples |
|---|---|---|
| E3 — reproduced | Direct, repeatable observation | browser/network trace, database before/after, exact failing request, repeatable runtime test |
| E2 — instrumented | Independent machine-produced support | automated test, log, metric, trace, persisted state |
| E1 — static fact, inferred consequence | A concrete reachable code or configuration fact, not yet executed | missing ownership predicate on a route, retry without idempotency on a charge path |
| E0 — claim or guess | Documentation, founder statement, generic concern, or unavailable evidence | “users love it,” “probably safe,” checklist speculation |

Keep severity independent from evidence strength. A catastrophic E1 path is not a runtime-confirmed vulnerability, but a directly established implementation defect may be reported as a `STATIC` finding. State exactly which fact is proven and which consequence remains inferred. Such evidence may fail a required release check and justify `NOT READY`; reserve an active veto and `BLOCKED` for reproduced or independently instrumented evidence, or complete deployment evidence that leaves no plausible compensating layer. An E3 cosmetic defect is still low severity.

## Closed-loop finding

Use this schema for every verified issue:

```text
[F-###] [BLOCKER|HIGH|MEDIUM|LOW] Short title
Promise/invariant:
Preconditions:
Reproduction:
Expected:
Actual:
Evidence: E# — exact artifact or observation
Impact:
Suspected cause: explicitly mark inference
Minimum fix:
Acceptance test:
Adjacent regression check:
```

A warning such as “add transactions” or “there may be a race” is not a finding until it is connected to a reachable product state and consequence.

## Universal product rubric

Use this weighting for `ship-fast` unless the artifact makes a dimension inapplicable. If a dimension is removed, explain why and redistribute its weight before scoring.

| Dimension | Weight | What earns credit |
|---|---:|---|
| Product promise and scope | 10 | The built behavior matches the claimed job and release target |
| Critical user journeys | 20 | Golden, failure, retry, refresh, and recovery paths close correctly |
| UX and accessibility | 10 | Users can understand, operate, recover, and use core flows with relevant assistive needs |
| Data and state integrity | 15 | Invariants survive duplicate, concurrent, partial, and out-of-order actions |
| Security and privacy | 15 | Identity, role, ownership, tenant, secret, and data boundaries hold |
| Reliability and operations | 10 | Timeouts, dependencies, deployment, rollback, monitoring, and support are proportionate |
| Change safety | 10 | The design is understandable, testable, and appropriate for the current product stage |
| Verification quality | 10 | Tests and evidence target actual risks rather than vanity coverage |

Score each dimension from 0–100 using these anchors:

- 90–100: independently verified, resilient, and appropriate for the release target
- 75–89: credible with bounded conditions or minor gaps
- 60–74: usable for a narrower target; material risks remain
- 40–59: fragile, substantially unverified, or missing a critical property
- 0–39: broken, misleading, or unsafe in this dimension

## Vetoes

The following verified conditions block the affected release target regardless of weighted score:

- `authorization-bypass`: a user can act on or read another user's or tenant's protected resource
- `sensitive-data-exposure`: material secret, credential, or personal data is exposed beyond its intended boundary
- `irreversible-data-loss`: a realistic action can destroy user data without an adequate recovery path
- `duplicate-real-charge`: retry, concurrency, or repeated input can cause duplicate financial effect
- `critical-flow-false-success`: the UI or API reports success while the core state change did not happen

Do not “waive” a veto inside the scorecard. It remains active until a same-path retest supplies reproducible passing evidence. A user may consciously accept risk, but that does not convert the verified condition into a technical pass.

## Scorecard and deterministic scorer

Create a JSON file and run `scripts/score_review.py`. The scorer reports:

- `raw_product_score`: weighted artifact quality before evidence limits
- `readiness_score`: score after evidence-confidence and policy caps
- evidence and critical-path coverage
- active vetoes and applied caps
- release decision for the requested target
- rubric fingerprint for same-rubric re-review

Minimal shape:

```json
{
  "schema_version": "1",
  "mode": "ship-fast",
  "rubric_id": "ratemycode/default-v1",
  "release_target": "public-launch",
  "dimensions": [
    {
      "id": "critical-user-journeys",
      "weight": 20,
      "score": 72,
      "verification": "partial",
      "evidence_ids": ["e-checkout"]
    }
  ],
  "evidence": [
    {
      "id": "e-checkout",
      "kind": "runtime",
      "result": "mixed",
      "reproducible": true
    }
  ],
  "coverage": {
    "runtime": "partial",
    "critical_paths": {"total": 4, "tested": 2}
  },
  "gates": []
}
```

All dimension weights must total 100. `verified` dimensions require reproducible non-claim evidence; `partial` dimensions require at least one evidence item. Supported evidence kinds are `runtime`, `test`, `code`, `log`, `metric`, `interview`, `document`, and `claim`.

The confidence ceiling limits only `readiness_score`, not `raw_product_score`. This prevents a static review from masquerading as launch approval while preserving the artifact assessment. Always explain missing evidence in prose.

## Re-review

Preserve the prior scorecard, rubric ID, release target, dimension IDs, and weights. Re-run the exact reproduction and acceptance tests. Use the rubric fingerprint to detect accidental rubric drift. Show raw-product and readiness deltas separately; an evidence gain can raise readiness without changing code quality.
