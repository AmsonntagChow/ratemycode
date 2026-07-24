# Product-lead review

Judge whether the product deserves to exist for its intended user and whether the current experience delivers the promised value. Treat engineering as a constraint on the product, not the center of the report.

## Product questions

1. Who is the specific user, in what moment, trying to make what progress?
2. Is the promise understandable before the user invests effort or trust?
3. How quickly does the user reach the first meaningful result?
4. Where does the core journey create confusion, friction, anxiety, or abandonment?
5. Does the result feel credible and worth returning for?
6. What completes the lifecycle after the first success: recovery, repeat use, cancellation, export, or sharing?
7. What observed behavior supports the product assumptions, and what remains imagined?

## Product-lead rubric

| Dimension | Weight | What to judge |
|---|---:|---|
| User and problem clarity | 15 | A specific user, moment, pain, and current alternative |
| Promise and differentiation | 15 | A legible outcome that is meaningfully better than the workaround |
| Time to first value | 20 | The shortest path from arrival to a result the user cares about |
| Core journey, trust, and recovery | 20 | Comprehension, confidence, error recovery, and accessibility |
| Repeat value and lifecycle | 15 | A credible reason to return plus complete ongoing states |
| Product evidence and learning | 10 | Behavior or experiments that can falsify the assumptions |
| Engineering constraints on value | 5 | Only technical limits that block trust, delivery, iteration, or release |

Apply all universal safety vetoes even though engineering has only 5% of this rubric. A cross-tenant leak or duplicate charge still blocks the affected release bar; it does not need a large rubric weight to matter.

## Output emphasis

Lead with:

- what the product helps the user accomplish
- whether the user reaches and trusts that value
- the largest product assumption still unsupported
- the three changes with the highest product leverage
- the one behavior or experiment that would most change the verdict

Do not lead with architecture, transactions, caching, observability, test counts, or code organization. Include them only when they explain a user-visible failure, invalidate a product claim, slow learning, or activate a release veto.
