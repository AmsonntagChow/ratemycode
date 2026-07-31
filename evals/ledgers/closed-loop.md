# RateMyCode audit ledger

## One-line problem list

- [BLOCKER · F-001 · verified-fixed] Any signed-in user can read another user's order: A customer can expose another customer's purchase data.
- [MEDIUM · F-002 · accepted-risk] Timeout recovery does not explain when to retry: Some customers may retry unnecessarily or contact support.

### Pending verification

None.

## Evidence lanes

- `deterministic-checks`: **PASS** (E-004, E-005)
- `critical-journey-e2e`: **PASS** (E-003, E-006)
- `probabilistic-eval`: **N/A** — The fixture has no LLM, agent, or RAG behavior.
- `continuous-evidence`: **PASS** (E-007)

## Workflow blockers

None.

## Release checks

None.

## Scoring

not requested.

## Review identity

- Ledger: `RMC-checkout-example-001`
- Prior ledger: `sha256:7608292c061118acdc254efb49f3f5f58e1d04b559b14399237fc4fb8d69b534`
- Artifact: Disposable checkout fixture
- Initial release: `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Current release: `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`
- Identity method: `sha256-tree`
- Identity scope: root=`.`; included=fixture-src/\*\*; fixture-tests/\*\*; excluded=.git/\*\*; .ratemycode/\*\*; build/\*\*; cache/\*\*; secrets/\*\*; symlink policy=`reject-all`
- Review: `staff-engineer` / `launch-gate` / `public-launch` / `ratemycode/staff-engineer/launch-gate/v1` / `none`
- Loop mode: `fix-and-retest`
- Current verdict: **READY_WITH_CONDITIONS**
- Maximum safe target: `public-launch`

## Progress

- Workflow state: **stopped-with-accepted-risk**
- Technical closure: **NOT CLOSED**

| Status | Count |
|---|---:|
| accepted-risk | 1 |
| verified-fixed | 1 |

## Root causes

- **RC-001 · Missing ownership enforcement** — The order lookup trusted an object identifier without checking the authenticated owner. (verified-fixed 1)
  - Extent of condition: `closed` — 4/4 instances converted, closed by `converted` · `rg -n --type ts 'repo\\.(findById\|getById)\\(' src/ \| rg -v 'ownerId\|tenantId'` over src/\*\*/\*.ts route handlers and data access, excluding tests and fixtures
  - Extent of cause: `done` — The same missing-owner-predicate habit was checked against the GraphQL resolvers and the export job; both already scope by owner.
- **RC-002 · Unbounded retry experience** — The retry path is safe but does not explain how long recovery can take. (accepted-risk 1)
  - Extent of condition: `closed` — 1/7 instances converted, closed by `ratchet` (tools/ratchets/retry-copy.tsv) · `rg -n 'retrying…\|Please wait' src/components/` over src/components/\*\*/\*.tsx user-facing retry and recovery copy
  - Extent of cause: `done` — No other surface makes an open-ended waiting promise; the same cause produced no second defect class.

## Safety gates

- **authorization-bypass · fixed** — targets: high-stakes, private-beta, public-launch, real-money; findings: F-001; failure evidence: E-001; retest evidence: E-003

## Detailed findings

### F-001 · Any signed-in user can read another user's order

- Severity: `BLOCKER`
- Status: `verified-fixed`
- Promise/invariant: A user can read only orders they own.
- Preconditions: Alice and Bob each have an order; Alice is signed in
- Reproduction: Request Bob's order ID using Alice's session
- Expected: The service denies or hides Bob's order.
- Actual: The service returned Bob's complete order.
- Impact: A customer can expose another customer's purchase data
- Suspected cause (inference): Inference: the lookup filters by order ID but not authenticated owner.
- Minimum fix / prompt: Bind every order read to both order ID and authenticated owner.
- Acceptance test: Repeat the cross-owner request and require 404, then confirm same-owner access succeeds.
- Adjacent regression check: Exercise list, detail, and receipt routes for both owners.
- Evidence: E-001
- Fix authorization: Fix F-001 in the disposable fixture and retest it. (scope: F-001 and ownership regression tests)
- Change origin: `authorized-agent`
- Change: `git:0123456789abcdef0123456789abcdef01234567` · by `agent:fix-context-001` — Added the authenticated owner to every order lookup.
- Retest: `FIXED` · by `agent:independent-retest-002` (independent-agent); Acceptance test `pass`, Adjacent regression check `pass`, Mutation check `killed`; Evidence E-003, E-004, E-005

### F-002 · Timeout recovery does not explain when to retry

- Severity: `MEDIUM`
- Status: `accepted-risk`
- Promise/invariant: A timed-out customer can understand the order state and next action.
- Preconditions: Checkout times out after the order is accepted
- Reproduction: Refresh the order page immediately after the timeout
- Expected: The page explains the pending state and a safe retry horizon.
- Actual: The page shows a generic pending label without timing guidance.
- Impact: Some customers may retry unnecessarily or contact support
- Suspected cause (inference): Inference: the recovery UI has no product copy for delayed completion.
- Minimum fix / prompt: Add pending-state guidance and a safe retry horizon without changing order semantics.
- Acceptance test: A timed-out checkout displays the pending reason, safe next action, and retry horizon.
- Adjacent regression check: Successful and failed checkouts retain their existing terminal messages.
- Evidence: E-002
- Risk acceptance: I accept F-002 for this public launch and will fix the copy next week.; Risk scope: F-002 for public-launch only — The order itself recovers correctly and support will monitor confusion.

## Detailed unknowns

### U-001 · cleared

- Condition: The final state after a client timeout has not been exercised.
- Why it matters: A customer could lose confidence or repeat a completed order.
- Missing evidence: A timeout, refresh, and resume runtime trace.
- Resolving test: Interrupt checkout after acceptance, refresh, and inspect the recovered state.
- Resolution evidence: E-006

## Evidence

- **E-001 · E3 · fail** — Alice retrieved Bob's paid order by changing the order ID. (`runtime trace ownership-before-001`; `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`; `runtime` / `critical-journey-e2e`; `F-001`; `reproduction`; fresh=true; reproducible=true; gate_id=`authorization-bypass`)
- **E-002 · E1 · fail** — The recovery response has no pending-state explanation or retry horizon. (`app.py:88`; `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`; `code` / `deterministic-checks`; `F-002`; `reproduction`; fresh=true; reproducible=true)
- **E-003 · E3 · pass** — Cross-owner reads now return 404 while same-owner reads still succeed. (`runtime trace ownership-after-002`; `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`; `runtime` / `critical-journey-e2e`; `F-001`; `acceptance`; fresh=true; reproducible=true; gate_id=`authorization-bypass`)
- **E-004 · E2 · pass** — Owner-scoped list, detail, and receipt regression tests pass. (`tests/test_orders.py::test_owner_routes`; `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`; `test` / `deterministic-checks`; `F-001`; `adjacent-regression`; fresh=true; reproducible=true)
- **E-005 · E2 · pass** — The ownership acceptance suite kills a missing-owner-check mutation. (`tests/test_orders.py::test_owner_mutation`; `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`; `test` / `deterministic-checks`; `F-001`; `mutation`; fresh=true; reproducible=true)
- **E-006 · E3 · pass** — Refreshing after a timeout preserves the order and displays its final state. (`runtime trace recovery-after-003`; `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`; `runtime` / `critical-journey-e2e`; `U-001`; `unknown-resolution`; fresh=true; reproducible=true)
- **E-007 · E2 · pass** — The identified release emits owner-denial and timeout-recovery events to the launch monitor. (`launch monitor sample window-004`; `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`; `log` / `continuous-evidence`; `release`; `release-lane`; fresh=true; reproducible=true)
