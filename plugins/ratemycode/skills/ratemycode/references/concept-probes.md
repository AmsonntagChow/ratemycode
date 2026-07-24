# Product-grounded concept probes

Use this router only for oral defense or when a finding needs a short explanation. Pick from actual system paths; never march through the list as a curriculum.

| Product signal | Probe the author with |
|---|---|
| Multi-step database change | What invariant must commit atomically? What happens halfway through? What is outside the database transaction? |
| Retryable state-changing request | Where is the idempotency key created, stored, scoped, and expired? What would a duplicate prove? |
| Concurrent update | Which operation is atomic? Can check-then-act race? How is a lost update detected? |
| External payment or API | What does timeout mean? How are unknown outcomes reconciled? Which system is authoritative? |
| Authentication and ownership | Where is identity established, and where is authorization rechecked for the specific object? |
| Cookie, session, or JWT | What state lives on the client versus server? How are expiry, revocation, and role changes handled? |
| HTTP API | Which operations are safe or idempotent? What does a transport 200 fail to prove about business success? |
| Index or slow query | Which query shape and data distribution justify the index? What does the query plan show? |
| Cache | What stale state is acceptable? What invalidates it? What happens on miss, stampede, or outage? |
| Queue or background job | What delivery semantics are assumed? How does the consumer handle duplicates, ordering, and poison work? |
| Frontend async state | Which response wins after overlap or navigation? What prevents stale UI or duplicate submit? |
| Optimistic UI | How is failure rolled back or reconciled with server truth? |
| Client-side secret or permission check | Why is the browser not a trust boundary? Where is enforcement on the server? |
| File upload or rich input | How are type, size, storage path, parsing, and later rendering constrained? |
| Accessibility-critical flow | Can keyboard, focus, labels, status announcements, and error recovery complete the same journey? |
| Deployment and migration | Can old and new versions coexist? How is rollback handled after a schema change? |
| Logs and metrics | Can an operator distinguish user error, dependency failure, and partial success without exposing sensitive data? |
| Backup claim | When was restore last proven, to what recovery point, and with what missing dependencies? |

## Probe pattern

Ask in this order:

1. “What must remain true?”
2. “Where is that enforced in this product?”
3. “How could the enforcement fail?”
4. “What observation or test would prove your answer wrong?”

This tests transferable understanding without requiring memorized terminology. If the user can reason correctly without naming the textbook concept, credit the understanding.
