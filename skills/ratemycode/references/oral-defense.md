# Oral defense

Use oral defense only when explicitly requested. It is a modifier on an artifact review, not a substitute for testing and not a generic job interview.

## Protocol

1. Finish or substantially ground the product review first.
2. Select three to five questions from actual product decisions, findings, or unverified high-impact risks.
3. Ask one question at a time and wait for the answer.
4. Ask about a failure chain, tradeoff, or proof method rather than a dictionary definition.
5. Do not reveal the complete answer before the user attempts it.
6. If the user asks to learn, explain briefly, then ask a different but structurally similar scenario to test transfer.
7. Finish with a separate author-understanding result. Never revise the product verdict merely because an answer was weak or strong.

If the user requests both an audit and a defense, deliver the audit first, then use questions that require applying the disclosed principle to a new failure sequence rather than parroting the fix. If the user requests defense only, do not preview the relevant finding or answer before the first attempt.

Read `references/concept-probes.md` and choose only concepts reachable in this artifact.

## Question form

Prefer:

> A user double-clicks Pay, the first response times out, and the client retries. At which boundary does this product prevent a second order or charge, and what test would prove it?

Avoid:

> Define idempotency.

Each question should expose whether the author can:

- trace the real system path
- name the invariant
- identify the enforcement boundary
- distinguish prevention from detection and recovery
- propose evidence that would falsify the answer

## Separate result

Report:

```text
Author understanding: STRONG | WORKING | FRAGILE | INSUFFICIENT EVIDENCE
Strengths:
Blind spots:
One concept worth learning next:
Transfer check result:
```

Do not generate a numeric author score unless the user explicitly asks. Never subtract it from the product score.
