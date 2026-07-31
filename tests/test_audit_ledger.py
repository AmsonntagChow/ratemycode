import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ratemycode" / "scripts" / "audit_ledger.py"
SPEC = importlib.util.spec_from_file_location("audit_ledger", SCRIPT)
audit_ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit_ledger)
def unswept_condition_sweep() -> dict:
    """The honest default: a defect class nobody has searched for yet."""
    return {
        "state": "unswept",
        "method": "none",
        "expression": None,
        "scope": None,
        "instances_found": 0,
        "instances_converted": 0,
        "closure": None,
        "closure_ref": None,
        "note": None,
    }


INITIAL_RELEASE = "sha256:" + ("a" * 64)
CURRENT_RELEASE = "sha256:" + ("b" * 64)


def base_finding():
    return {
        "id": "F-001",
        "severity": "HIGH",
        "title": "Checkout can report success before durable completion",
        "promise_or_invariant": "A paid result means the order is durably complete.",
        "preconditions": ["A user submits checkout."],
        "reproduction_steps": ["Submit an order while the durable write fails."],
        "expected": "The request fails or recovers without a success result.",
        "actual": "The response reports success before the durable write.",
        "evidence_ids": ["E-001"],
        "impact": "A user can believe an order exists when it does not",
        "suspected_cause": "Inference: the response is emitted before the write is confirmed.",
        "minimum_fix_or_agent_prompt": "Confirm the durable write before returning success.",
        "acceptance_test": "Force the write to fail and assert that checkout does not report success.",
        "adjacent_regression_check": "Run the successful checkout and retry paths.",
        "root_cause_id": None,
        "gate_id": None,
        "status": "open",
        "fix_authorization": None,
        "fix": None,
        "retest": None,
        "risk_acceptance": None,
        "blocker": None,
    }


def evidence(
    evidence_id,
    *,
    state,
    kind,
    lane,
    result,
    release_ref,
    subject_id,
    procedure,
    summary,
    locator,
    gate_id=None,
    workflow_blocker_id=None,
    release_check_id=None,
    venture_signal_id=None,
    deployment_coverage=None,
    runs=None,
    provenance=None,
    eval_metrics=None,
):
    record = {
        "id": evidence_id,
        "state": state,
        "kind": kind,
        "lane": lane,
        "result": result,
        "reproducible": True,
        "fresh": True,
        "release_ref": release_ref,
        "summary": summary,
        "locator": locator,
        "subject_id": subject_id,
        "procedure": procedure,
    }
    if gate_id is not None:
        record["gate_id"] = gate_id
    if workflow_blocker_id is not None:
        record["workflow_blocker_id"] = workflow_blocker_id
    if release_check_id is not None:
        record["release_check_id"] = release_check_id
    if venture_signal_id is not None:
        record["venture_signal_id"] = venture_signal_id
    if deployment_coverage is not None:
        record["deployment_coverage"] = deployment_coverage
    if runs is not None:
        record["runs"] = runs
    if provenance is not None:
        record["provenance"] = provenance
    if eval_metrics is not None:
        record["eval_metrics"] = eval_metrics
    return record


def base_payload():
    return {
        "schema_version": "3",
        "snapshot_index": 1,
        "recorded_at": None,
        "ledger_id": "RMC-test-001",
        "previous_ledger_ref": None,
        "artifact": {
            "name": "Test checkout",
            "initial_release_ref": INITIAL_RELEASE,
            "current_release_ref": INITIAL_RELEASE,
            "identity_method": "sha256-tree",
            "identity_scope": {
                "root": ".",
                "included": ["skills/ratemycode/**", "tests/**"],
                "excluded": [".git/**", ".ratemycode/**", "__pycache__/**"],
                "symlink_policy": "reject-all",
            },
        },
        "review": {
            "role": "staff-engineer",
            "degree": "strict-review",
            "requested_target": "private-beta",
            "rubric_id": "ratemycode/default-v1",
            "ai_behavior": "none",
        },
        "loop_mode": "report-only",
        "verdict": {
            "initial_decision": "NOT_READY",
            "current_decision": "NOT_READY",
            "maximum_safe_target": "internal-demo",
        },
        "workflow_blockers": [],
        "release_checks": [],
        "scoring": {
            "requested": False,
            "threshold_met": None,
            "scorecard_ref": None,
        },
        "venture_assessment": None,
        "root_causes": [],
        "evidence": [
            evidence(
                "E-001",
                state="E1",
                kind="code",
                lane="deterministic-checks",
                result="fail",
                release_ref=INITIAL_RELEASE,
                subject_id="F-001",
                procedure="reproduction",
                summary="The success response precedes durable completion.",
                locator="app.py:42",
            )
        ],
        "evidence_lanes": {
            "deterministic-checks": {
                "status": "FAIL",
                "evidence_ids": ["E-001"],
            },
            "critical-journey-e2e": {
                "status": "UNVERIFIED",
                "evidence_ids": [],
            },
            "probabilistic-eval": {
                "status": "N/A",
                "evidence_ids": [],
                "reason": "The product has no LLM, agent, or RAG behavior.",
            },
            "continuous-evidence": {
                "status": "UNVERIFIED",
                "evidence_ids": [],
            },
        },
        "gates": [],
        "findings": [base_finding()],
        "unknowns": [],
    }


class StaffFrontendEngineerRoleTests(unittest.TestCase):
    def test_staff_frontend_engineer_role_is_supported(self):
        payload = base_payload()
        payload["review"]["role"] = "staff-frontend-engineer"
        validated = audit_ledger.validate(payload)
        self.assertEqual(validated["review"]["role"], "staff-frontend-engineer")


def closed_condition_sweep() -> dict:
    """A defect class that was enumerated and fully converted."""
    return {
        "state": "closed",
        "method": "static-query",
        "expression": "rg -n 'durableWrite\\(' src/",
        "scope": "src/**/*.py write paths, excluding tests",
        "instances_found": 2,
        "instances_converted": 2,
        "closure": "converted",
        "closure_ref": None,
        "note": None,
    }


def verified_payload():
    payload = base_payload()
    payload["artifact"]["current_release_ref"] = CURRENT_RELEASE
    payload["loop_mode"] = "fix-and-retest"
    # A verified-fixed finding has to hang off a root cause now, so its defect
    # class carries a sweep instead of quietly skipping one.
    payload["findings"][0]["root_cause_id"] = "RC-001"
    payload["root_causes"] = [
        {
            "id": "RC-001",
            "title": "Unchecked durable write",
            "summary": "Write results were assumed rather than confirmed.",
            "finding_ids": ["F-001"],
            "condition_sweep": closed_condition_sweep(),
            "cause_sweep": None,
        }
    ]
    payload["verdict"]["current_decision"] = "READY"
    payload["verdict"]["maximum_safe_target"] = "private-beta"
    payload["evidence"].extend(
        [
            evidence(
                "E-002",
                state="E2",
                kind="test",
                lane="deterministic-checks",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id="F-001",
                procedure="acceptance",
                summary="The original durable-write failure now passes.",
                locator="tests/test_checkout.py::test_write_failure",
            ),
            evidence(
                "E-003",
                state="E2",
                kind="test",
                lane="deterministic-checks",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id="F-001",
                procedure="adjacent-regression",
                summary="Successful checkout and retry behavior still pass.",
                locator="tests/test_checkout.py::test_retry",
            ),
            evidence(
                "E-004",
                state="E2",
                kind="test",
                lane="deterministic-checks",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id="F-001",
                procedure="mutation",
                summary="The acceptance suite kills premature-success mutation.",
                locator="tests/test_checkout.py::test_premature_success_mutation",
            ),
            evidence(
                "E-005",
                state="E3",
                kind="runtime",
                lane="critical-journey-e2e",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id=None,
                procedure="release-lane",
                summary="The complete checkout journey succeeds durably.",
                locator="runtime trace checkout-e2e-001",
            ),
        ]
    )
    payload["evidence_lanes"]["deterministic-checks"] = {
        "status": "PASS",
        "evidence_ids": ["E-002", "E-003", "E-004"],
    }
    payload["evidence_lanes"]["critical-journey-e2e"] = {
        "status": "PASS",
        "evidence_ids": ["E-005"],
    }
    finding = payload["findings"][0]
    finding["status"] = "verified-fixed"
    finding["fix_authorization"] = {
        "authorized_by": "user",
        "statement": "Fix F-001 and retest it.",
        "scope": "F-001 and its tests",
    }
    finding["fix"] = {
        "origin": "authorized-agent",
        "actor_id": "agent:fix-pass-1",
        "change_ref": "git:0123456789abcdef0123456789abcdef01234567",
        "summary": "Return success only after the durable write.",
    }
    finding["retest"] = {
        "classification": "FIXED",
        "reviewer_id": "agent:retest-pass-2",
        "reviewer_context": "independent-agent",
        "release_ref": CURRENT_RELEASE,
        "evidence_ids": ["E-002", "E-003", "E-004"],
        "acceptance_test": "pass",
        "adjacent_regression_check": "pass",
        "mutation_test": {"status": "killed"},
    }
    return payload


def active_gate_payload(*, deployment_evidence=False):
    payload = base_payload()
    payload["review"]["degree"] = "real-stakes"
    payload["review"]["requested_target"] = "real-money"
    payload["verdict"]["initial_decision"] = "BLOCKED"
    payload["verdict"]["current_decision"] = "BLOCKED"
    record = payload["evidence"][0]
    record["gate_id"] = "duplicate-real-charge"
    if deployment_evidence:
        record["deployment_coverage"] = {
            "scope_complete": True,
            "compensating_layer_ruled_out": True,
        }
    else:
        record.update(
            {
                "state": "E3",
                "kind": "runtime",
                "lane": "critical-journey-e2e",
            }
        )
        payload["evidence_lanes"]["deterministic-checks"] = {
            "status": "UNVERIFIED",
            "evidence_ids": [],
        }
        payload["evidence_lanes"]["critical-journey-e2e"] = {
            "status": "FAIL",
            "evidence_ids": ["E-001"],
        }
    payload["findings"][0]["gate_id"] = "duplicate-real-charge"
    payload["gates"] = [
        {
            "id": "duplicate-real-charge",
            "state": "active",
            "evidence_ids": ["E-001"],
            "retest_evidence_ids": [],
            "affected_targets": ["real-money", "high-stakes"],
            "finding_ids": ["F-001"],
        }
    ]
    return payload


def fixed_gate_payload():
    payload = verified_payload()
    payload["findings"][0]["gate_id"] = "critical-flow-false-success"
    payload["evidence"][0].update(
        {
            "state": "E3",
            "kind": "runtime",
            "lane": "other",
            "gate_id": "critical-flow-false-success",
        }
    )
    payload["evidence"][1]["gate_id"] = "critical-flow-false-success"
    payload["gates"] = [
        {
            "id": "critical-flow-false-success",
            "state": "fixed",
            "evidence_ids": ["E-001"],
            "retest_evidence_ids": ["E-002"],
            "affected_targets": ["private-beta"],
            "finding_ids": ["F-001"],
        }
    ]
    return payload


def unverifiable_payload(*, maximum_safe_target="internal-demo"):
    payload = verified_payload()
    payload["verdict"]["current_decision"] = "INSUFFICIENT_EVIDENCE"
    payload["verdict"]["maximum_safe_target"] = maximum_safe_target
    finding = payload["findings"][0]
    finding["status"] = "unverifiable"
    finding["retest"] = {
        "classification": "UNVERIFIABLE",
        "reviewer_id": "agent:retest-pass-2",
        "reviewer_context": "independent-agent",
        "release_ref": CURRENT_RELEASE,
        "evidence_ids": [],
        "acceptance_test": "unverified",
        "adjacent_regression_check": "unverified",
        "mutation_test": {
            "status": "not-applicable",
            "reason": "No executable retest environment is available.",
        },
    }
    return payload


def workflow_blocker_payload(status):
    payload = verified_payload()
    evidence_ids = []
    if status == "active":
        payload["verdict"]["current_decision"] = "BLOCKED"
        payload["verdict"]["maximum_safe_target"] = "internal-demo"
    else:
        payload["evidence"].append(
            evidence(
                "E-006",
                state="E3",
                kind="runtime",
                lane="other",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id=None,
                procedure="release-lane",
                summary="The payment sandbox is available and replayable.",
                locator="runtime trace sandbox-readiness-001",
                workflow_blocker_id="B-001",
            )
        )
        evidence_ids = ["E-006"]
    payload["workflow_blockers"] = [
        {
            "id": "B-001",
            "status": status,
            "reason": "The payment sandbox was unavailable.",
            "missing_requirement": "A reproducible payment failure environment.",
            "resolving_action": "Restore the sandbox and replay checkout.",
            "resolution_evidence_ids": evidence_ids,
        }
    ]
    return payload


def release_check_payload():
    payload = verified_payload()
    payload["evidence"].append(
        evidence(
            "E-006",
            state="E3",
            kind="runtime",
            lane="other",
            result="pass",
            release_ref=CURRENT_RELEASE,
            subject_id=None,
            procedure="release-lane",
            summary="Operations can roll back the release.",
            locator="runtime trace rollback-drill-001",
            release_check_id="rollback-readiness-v1",
        )
    )
    payload["release_checks"] = [
        {
            "id": "rollback-readiness-v1",
            "required": True,
            "status": "pass",
            "evidence_ids": ["E-006"],
        }
    ]
    return payload


def eval_evidence(evidence_id, *, runs=1, system=False):
    provenance = {
        "model": "model:gpt-5-v1",
        "prompt": "prompt:checkout-v2",
        "eval_set": "eval-set:2026-07-28",
        "judge": "judge:rubric-v3",
    }
    if system:
        provenance["system"] = "checkout-agent:v4"
    return evidence(
        evidence_id,
        state="E2",
        kind="eval",
        lane="probabilistic-eval",
        result="pass",
        release_ref=CURRENT_RELEASE,
        subject_id=None,
        procedure="release-lane",
        summary="Repeated checkout-agent evaluation passed.",
        locator=f"eval run {evidence_id}",
        runs=runs,
        provenance=provenance,
        eval_metrics={
            "minimum_pass_rate": 70,
            "observed_pass_rate": 85,
            "maximum_standard_deviation": 20,
            "observed_standard_deviation": 10,
        },
    )


def probabilistic_payload(*, ai_behavior="llm"):
    payload = verified_payload()
    payload["review"]["ai_behavior"] = ai_behavior
    records = [
        eval_evidence("E-006", system=ai_behavior in {"agent", "rag", "mixed"}),
        eval_evidence("E-007", system=ai_behavior in {"agent", "rag", "mixed"}),
    ]
    payload["evidence"].extend(records)
    payload["evidence_lanes"]["probabilistic-eval"] = {
        "status": "PASS",
        "evidence_ids": [record["id"] for record in records],
    }
    return payload


def venture_payload(statuses, decision):
    payload = base_payload()
    payload["review"].update(
        {
            "role": "skeptical-vc",
            "requested_target": "venture-case",
            "ai_behavior": "none",
        }
    )
    payload["verdict"].update(
        {
            "initial_decision": "NOT_INVESTABLE_YET",
            "current_decision": decision,
            "maximum_safe_target": "not-assessed",
        }
    )
    payload["findings"] = []
    payload["evidence"] = []
    payload["evidence_lanes"] = {
        lane_id: {
            "status": "N/A",
            "evidence_ids": [],
            "reason": "Venture signals are assessed separately from software release lanes.",
        }
        for lane_id in (
            "deterministic-checks",
            "critical-journey-e2e",
            "probabilistic-eval",
            "continuous-evidence",
        )
    }
    signal_kinds = {
        "real_users": "runtime",
        "retention": "metric",
        "repeatable_distribution": "document",
    }
    signals = {}
    for index, signal_id in enumerate(
        ("real_users", "retention", "repeatable_distribution"), start=10
    ):
        status = statuses[signal_id]
        evidence_ids = []
        if status == "present":
            evidence_id = f"E-{index:03d}"
            evidence_ids.append(evidence_id)
            payload["evidence"].append(
                evidence(
                    evidence_id,
                    state="E3",
                    kind=signal_kinds[signal_id],
                    lane="other",
                    result="pass",
                    release_ref=INITIAL_RELEASE,
                    subject_id=None,
                    procedure="release-lane",
                    summary=f"Current behavioral evidence supports {signal_id}.",
                    locator=f"venture evidence {signal_id}",
                    venture_signal_id=signal_id,
                )
            )
        signals[signal_id] = {"status": status, "evidence_ids": evidence_ids}
    payload["venture_assessment"] = {
        "stage": "structured-diligence",
        "evidence_maturity": {
            0: "claims-only",
            1: "single-signal",
            2: "multi-signal",
            3: "complete",
        }[sum(status == "present" for status in statuses.values())],
        "strongest_proven_signal": next(
            (
                signal_id
                for signal_id in (
                    "real_users",
                    "retention",
                    "repeatable_distribution",
                )
                if statuses[signal_id] == "present"
            ),
            "none",
        ),
        "largest_unsupported_leap": "repeatable distribution",
        "signals": signals,
    }
    return payload


class AuditLedgerTests(unittest.TestCase):
    def validate(self, payload):
        return audit_ledger.validate(copy.deepcopy(payload))

    def run_cli(self, command, payload, *args):
        return self.run_cli_text(command, json.dumps(payload), *args)

    def run_cli_text(self, command, ledger_text, *args):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text(ledger_text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), command, *args, str(ledger_path)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_open_report_only_ledger_is_valid(self):
        data = self.validate(base_payload())
        self.assertEqual(data["findings"][0]["status"], "open")
        self.assertEqual(audit_ledger.summary(data)["unresolved"], 1)

    def test_verified_fix_requires_independent_fresh_machine_evidence(self):
        data = self.validate(verified_payload())
        self.assertEqual(data["findings"][0]["status"], "verified-fixed")
        self.assertEqual(audit_ledger.summary(data)["verified_fixed"], 1)

    def test_fixer_cannot_verify_own_change(self):
        payload = verified_payload()
        payload["findings"][0]["retest"]["reviewer_id"] = "agent:fix-pass-1"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.reviewer_id")

    def test_principal_ids_cannot_fake_independence_with_whitespace(self):
        payload = verified_payload()
        payload["findings"][0]["retest"]["reviewer_id"] = " agent:fix-pass-1"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.reviewer_id")

    def test_verified_fix_rejects_stale_release_evidence(self):
        payload = verified_payload()
        payload["evidence"][1]["release_ref"] = INITIAL_RELEASE
        payload["evidence_lanes"]["deterministic-checks"]["evidence_ids"] = [
            "E-003",
            "E-004",
        ]
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.evidence_ids")

    def test_verified_fix_rejects_static_only_retest(self):
        payload = verified_payload()
        payload["evidence"][1]["kind"] = "code"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.evidence_ids")

    def test_verified_fix_rejects_surviving_mutation(self):
        payload = verified_payload()
        payload["findings"][0]["retest"]["mutation_test"] = {"status": "survived"}
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.mutation_test.status")

    def test_not_applicable_mutation_requires_reason(self):
        payload = verified_payload()
        payload["findings"][0]["retest"]["mutation_test"] = {"status": "not-applicable"}
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.mutation_test")

    def test_e0_cannot_verify_a_fix(self):
        payload = verified_payload()
        payload["evidence"][1]["state"] = "E0"
        payload["evidence_lanes"]["deterministic-checks"]["evidence_ids"] = [
            "E-003",
            "E-004",
        ]
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].retest.evidence_ids")

    def test_e0_cannot_satisfy_a_required_release_lane(self):
        payload = verified_payload()
        payload["evidence"][4]["state"] = "E0"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path,
            "$.evidence[4].state",
        )

    def test_agent_cannot_accept_risk(self):
        payload = base_payload()
        finding = payload["findings"][0]
        finding["status"] = "accepted-risk"
        finding["risk_acceptance"] = {
            "accepted_by": "agent",
            "statement": "This is probably fine.",
            "scope": "F-001",
            "rationale": "Ship faster.",
        }
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].risk_acceptance.accepted_by")

    def test_accepted_risk_cannot_hide_a_fixed_retest_classification(self):
        payload = verified_payload()
        finding = payload["findings"][0]
        finding["status"] = "accepted-risk"
        finding["risk_acceptance"] = {
            "accepted_by": "user",
            "statement": "Stop work on F-001.",
            "scope": "F-001",
        }
        payload["verdict"]["current_decision"] = "READY_WITH_CONDITIONS"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path, "$.findings[0].retest.classification"
        )

    def test_active_in_scope_gate_remains_blocked_after_user_accepts_risk(self):
        payload = active_gate_payload()
        finding = payload["findings"][0]
        finding["status"] = "accepted-risk"
        finding["risk_acceptance"] = {
            "accepted_by": "user",
            "statement": "I accept F-001 for this release.",
            "scope": "F-001 on real-money",
            "rationale": "A compensating manual reconciliation is in place.",
        }
        data = self.validate(payload)
        self.assertEqual(data["verdict"]["current_decision"], "BLOCKED")
        self.assertEqual(data["gates"][0]["state"], "active")

    def test_active_in_scope_gate_rejects_ready_verdict(self):
        payload = active_gate_payload()
        payload["verdict"]["current_decision"] = "READY"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_fixed_gate_requires_gate_bound_retest(self):
        payload = fixed_gate_payload()
        self.validate(payload)
        payload["evidence"][1].pop("gate_id")
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].retest_evidence_ids")

    def test_fixed_gate_rejects_concurrent_current_failure(self):
        payload = fixed_gate_payload()
        payload["evidence"].append(
            evidence(
                "E-006",
                state="E3",
                kind="runtime",
                lane="other",
                result="fail",
                release_ref=CURRENT_RELEASE,
                subject_id="F-001",
                procedure="reproduction",
                summary="A current runtime replay still reports premature success.",
                locator="runtime trace checkout-gate-regression",
                gate_id="critical-flow-false-success",
            )
        )
        payload["gates"][0]["evidence_ids"].append("E-006")
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertIn(
            context.exception.path,
            {"$.findings[0].retest.evidence_ids", "$.gates[0].state"},
        )

    def test_orphan_gate_bound_evidence_is_rejected(self):
        payload = base_payload()
        payload["evidence"][0]["gate_id"] = "critical-flow-false-success"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence[E-001].gate_id")

    def test_complete_deployment_evidence_can_activate_gate(self):
        payload = active_gate_payload(deployment_evidence=True)
        data = self.validate(payload)
        self.assertEqual(data["gates"][0]["state"], "active")
        self.assertEqual(
            data["evidence"][0]["deployment_coverage"],
            {
                "scope_complete": True,
                "compensating_layer_ruled_out": True,
            },
        )

    def test_e0_complete_deployment_record_cannot_activate_gate(self):
        record = {
            "state": "E0",
            "kind": "code",
            "result": "fail",
            "fresh": True,
            "reproducible": True,
            "release_ref": INITIAL_RELEASE,
            "gate_id": "duplicate-real-charge",
            "deployment_coverage": {
                "scope_complete": True,
                "compensating_layer_ruled_out": True,
            },
        }
        self.assertFalse(
            audit_ledger.qualifies_gate_failure(record, "duplicate-real-charge")
        )

    def test_proven_gate_stays_active_after_change_until_independent_retest(self):
        payload = active_gate_payload()
        payload["artifact"]["current_release_ref"] = CURRENT_RELEASE
        payload["loop_mode"] = "fix-and-retest"
        payload["evidence_lanes"]["critical-journey-e2e"] = {
            "status": "UNVERIFIED",
            "evidence_ids": [],
        }
        finding = payload["findings"][0]
        finding["status"] = "fixed-pending-retest"
        finding["fix_authorization"] = {
            "authorized_by": "user",
            "statement": "Fix F-001, then keep the gate closed until independent retest.",
            "scope": "F-001",
        }
        finding["fix"] = {
            "origin": "authorized-agent",
            "actor_id": "agent:gate-fix",
            "change_ref": "git:abcdef0123456789abcdef0123456789abcdef01",
            "summary": "Changed the duplicate-charge path.",
        }
        data = self.validate(payload)
        self.assertEqual(data["gates"][0]["state"], "active")
        self.assertEqual(data["verdict"]["current_decision"], "BLOCKED")

    def test_recorded_fix_requires_a_new_release_identity(self):
        payload = verified_payload()
        payload["artifact"]["current_release_ref"] = INITIAL_RELEASE
        payload["findings"][0]["retest"]["release_ref"] = INITIAL_RELEASE
        for record in payload["evidence"][1:]:
            record["release_ref"] = INITIAL_RELEASE
        payload["evidence"][0]["fresh"] = False
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.artifact.current_release_ref")

    def test_fix_rejects_mutable_change_reference(self):
        payload = verified_payload()
        payload["findings"][0]["fix"]["change_ref"] = "git:main"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0].fix.change_ref")

    def test_degree_and_target_must_match(self):
        payload = base_payload()
        payload["review"]["requested_target"] = "public-launch"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.review.requested_target")

    def test_ready_decisions_require_every_target_lane_to_pass(self):
        for decision in ("READY", "READY_WITH_CONDITIONS"):
            with self.subTest(decision=decision):
                payload = verified_payload()
                payload["verdict"]["current_decision"] = decision
                payload["evidence_lanes"]["critical-journey-e2e"] = {
                    "status": "UNVERIFIED",
                    "evidence_ids": [],
                }
                with self.assertRaises(audit_ledger.ValidationError) as context:
                    self.validate(payload)
                self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_decision_order_prefers_failed_lane_over_unverified_lane(self):
        payload = base_payload()
        payload["verdict"]["current_decision"] = "INSUFFICIENT_EVIDENCE"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_unverified_required_lane_requires_insufficient_evidence(self):
        payload = verified_payload()
        payload["evidence_lanes"]["critical-journey-e2e"] = {
            "status": "UNVERIFIED",
            "evidence_ids": [],
        }
        payload["verdict"]["current_decision"] = "NOT_READY"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_blocked_decision_requires_gate_or_named_blocker(self):
        payload = verified_payload()
        payload["verdict"]["current_decision"] = "BLOCKED"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_ready_rejects_user_accepted_risk(self):
        payload = base_payload()
        payload["verdict"]["current_decision"] = "READY"
        finding = payload["findings"][0]
        finding["status"] = "accepted-risk"
        finding["risk_acceptance"] = {
            "accepted_by": "user",
            "statement": "I accept F-001 for this private beta.",
            "scope": "F-001 for private-beta",
            "rationale": "The beta group has a manual recovery path.",
        }
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_root_cause_links_are_bidirectional(self):
        payload = base_payload()
        payload["findings"][0]["root_cause_id"] = "RC-001"
        payload["root_causes"] = [
            {
                "id": "RC-001",
                "title": "Premature success",
                "summary": "State is acknowledged before completion.",
                "finding_ids": ["F-001"],
                "condition_sweep": unswept_condition_sweep(),
                "cause_sweep": None,
            }
        ]
        self.validate(payload)
        payload["root_causes"][0]["finding_ids"] = ["F-999"]
        with self.assertRaises(audit_ledger.ValidationError):
            self.validate(payload)

    def _closing_root_cause_payload(self, degree="strict-review"):
        """A fix loop where the only filed finding of RC-001 is verified fixed.

        This is the shape that used to read as a finished root cause while the
        defect class was still open everywhere else.
        """
        payload = verified_payload()
        payload["review"]["degree"] = degree
        # degree and requested_target are coupled; move both or the review gate
        # rejects the payload before it ever reaches the sweep rules.
        payload["review"]["requested_target"] = {
            "quick-check": "internal-demo",
            "strict-review": "private-beta",
            "launch-gate": "public-launch",
            "real-stakes": "real-money",
            "life-or-death": "high-stakes",
        }[degree]
        # A launch gate demands runtime release evidence this fixture does not
        # carry, so the decision engine lands on INSUFFICIENT_EVIDENCE there.
        if degree == "launch-gate":
            payload["verdict"]["current_decision"] = "INSUFFICIENT_EVIDENCE"
            payload["verdict"]["maximum_safe_target"] = "internal-demo"
        else:
            payload["verdict"]["maximum_safe_target"] = payload["review"]["requested_target"]
        payload["findings"][0]["root_cause_id"] = "RC-001"
        payload["root_causes"] = [
            {
                "id": "RC-001",
                "title": "Missing ownership predicate",
                "summary": "Lookups trust an identifier without checking the owner.",
                "finding_ids": [payload["findings"][0]["id"]],
                "condition_sweep": unswept_condition_sweep(),
                "cause_sweep": None,
            }
        ]
        return payload

    def _swept(self, **overrides):
        sweep = {
            "state": "closed",
            "method": "static-query",
            "expression": "rg -n 'findById' src/",
            "scope": "src/**/*.ts",
            "instances_found": 3,
            "instances_converted": 3,
            "closure": "converted",
            "closure_ref": None,
            "note": None,
        }
        sweep.update(overrides)
        return sweep

    def test_closing_a_root_cause_requires_the_class_to_have_been_searched(self):
        payload = self._closing_root_cause_payload()
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path, "$.root_causes[0].condition_sweep.state"
        )
        payload["root_causes"][0]["condition_sweep"] = self._swept()
        self.validate(payload)

    def test_unswept_class_is_allowed_while_findings_remain_open(self):
        payload = self._closing_root_cause_payload()
        payload["findings"][0]["status"] = "fixed-pending-retest"
        payload["findings"][0]["retest"] = None
        # An unverified fix cannot be READY, and the sweep rule must not fire here.
        payload["verdict"]["current_decision"] = "NOT_READY"
        payload["verdict"]["maximum_safe_target"] = "internal-demo"
        self.validate(payload)

    def test_converted_closure_cannot_leave_instances_behind(self):
        payload = self._closing_root_cause_payload()
        payload["root_causes"][0]["condition_sweep"] = self._swept(instances_converted=1)
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path, "$.root_causes[0].condition_sweep.instances_converted"
        )

    def test_ratchet_closure_carries_the_enforcing_location(self):
        payload = self._closing_root_cause_payload()
        payload["root_causes"][0]["condition_sweep"] = self._swept(
            closure="ratchet", instances_converted=1
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path, "$.root_causes[0].condition_sweep.closure_ref"
        )
        payload["root_causes"][0]["condition_sweep"]["closure_ref"] = "tools/ratchets/own.tsv"
        self.validate(payload)

    def test_swept_state_cannot_claim_a_closure(self):
        payload = self._closing_root_cause_payload()
        payload["root_causes"][0]["condition_sweep"] = self._swept(state="swept")
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.root_causes[0].condition_sweep.closure")

    def test_unswept_state_cannot_carry_counts(self):
        payload = self._closing_root_cause_payload()
        payload["findings"][0]["status"] = "open"
        payload["findings"][0]["fix"] = None
        payload["findings"][0]["fix_authorization"] = None
        payload["findings"][0]["retest"] = None
        sweep = unswept_condition_sweep()
        sweep["instances_found"] = 4
        payload["root_causes"][0]["condition_sweep"] = sweep
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.root_causes[0].condition_sweep.state")

    def test_unsweepable_class_must_say_why(self):
        payload = self._closing_root_cause_payload()
        payload["root_causes"][0]["condition_sweep"] = self._swept(
            state="unsweepable",
            method="none",
            expression=None,
            instances_found=0,
            instances_converted=0,
            closure=None,
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.root_causes[0].condition_sweep.note")

    def test_launch_gate_refuses_to_close_an_unenumerable_class(self):
        payload = self._closing_root_cause_payload(degree="launch-gate")
        payload["root_causes"][0]["condition_sweep"] = self._swept(
            state="unsweepable",
            method="none",
            expression=None,
            instances_found=0,
            instances_converted=0,
            closure=None,
            note="No mechanical predicate distinguishes the unsafe call sites.",
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.root_causes[0].condition_sweep.state")

    def test_launch_gate_requires_the_extent_of_cause_review(self):
        payload = self._closing_root_cause_payload(degree="launch-gate")
        payload["root_causes"][0]["condition_sweep"] = self._swept()
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.root_causes[0].cause_sweep")
        payload["root_causes"][0]["cause_sweep"] = {
            "state": "done",
            "summary": "Checked the export job and the GraphQL resolvers.",
            "finding_ids": [],
        }
        self.validate(payload)

    def test_verified_fix_cannot_skip_the_class_by_having_no_root_cause(self):
        """The lone observed instance is the likeliest to have siblings."""
        payload = verified_payload()
        payload["findings"][0]["root_cause_id"] = None
        payload["root_causes"] = []
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[F-001].root_cause_id")

    def test_progress_reports_unconverted_instances_above_the_root_cause_detail(self):
        """A reader of the top of the report must see what is still out there."""
        payload = verified_payload()
        payload["root_causes"][0]["condition_sweep"] = {
            "state": "closed",
            "method": "text-search",
            "expression": "rg -n 'durableWrite' src/",
            "scope": "src/**/*.py",
            "instances_found": 7,
            "instances_converted": 1,
            "closure": "ratchet",
            "closure_ref": "tools/ratchets/durable-write.tsv",
            "note": "Six call sites remain under an enforced, decreasing count.",
        }
        report = audit_ledger.render_markdown(self.validate(payload), "en")
        progress = report.index("## Progress")
        detail = report.index("## Root causes")
        self.assertIn("**6** instance(s) of a filed defect still unconverted", report)
        self.assertLess(report.index("still unconverted"), detail)
        self.assertGreater(report.index("still unconverted"), progress)

    def test_quick_check_may_close_with_the_remainder_accepted(self):
        payload = self._closing_root_cause_payload(degree="quick-check")
        payload["root_causes"][0]["condition_sweep"] = self._swept(
            instances_converted=1,
            closure="accepted-risk",
            note="Two call sites remain; the user accepted them for an internal demo.",
        )
        self.validate(payload)

    def test_external_change_can_be_retested_without_prior_authorization(self):
        payload = verified_payload()
        payload["findings"][0]["fix_authorization"] = None
        payload["findings"][0]["fix"]["origin"] = "external-change"
        payload["findings"][0]["fix"]["actor_id"] = "developer:checkout-owner"
        data = self.validate(payload)
        self.assertIsNone(data["findings"][0]["fix_authorization"])
        self.assertEqual(data["findings"][0]["fix"]["origin"], "external-change")

    def test_blocked_finding_requires_named_blocker(self):
        payload = base_payload()
        payload["findings"][0]["status"] = "blocked"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.findings[0]")

        payload["findings"][0]["blocker"] = {
            "reason": "The payment sandbox is unavailable.",
            "missing_requirement": "A reproducible payment failure environment.",
            "resolving_action": "Restore the sandbox and rerun the acceptance path.",
        }
        payload["verdict"]["current_decision"] = "BLOCKED"
        data = self.validate(payload)
        self.assertEqual(data["findings"][0]["status"], "blocked")

    def test_workflow_blocker_active_and_resolved_states_require_bound_evidence(self):
        active = self.validate(workflow_blocker_payload("active"))
        self.assertEqual(active["verdict"]["current_decision"], "BLOCKED")
        self.assertEqual(active["workflow_blockers"][0]["resolution_evidence_ids"], [])

        resolved_payload = workflow_blocker_payload("resolved")
        resolved = self.validate(resolved_payload)
        self.assertEqual(resolved["workflow_blockers"][0]["status"], "resolved")
        self.assertEqual(
            resolved["evidence"][-1]["workflow_blocker_id"], "B-001"
        )

        resolved_payload["evidence"][-1].pop("workflow_blocker_id")
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(resolved_payload)
        self.assertEqual(
            context.exception.path,
            "$.workflow_blockers[0].resolution_evidence_ids",
        )

    def test_workflow_blocker_continuity_rejects_deletion_and_reopen(self):
        previous = self.validate(workflow_blocker_payload("resolved"))
        prior_ref = "sha256:" + ("c" * 64)

        deleted = copy.deepcopy(previous)
        deleted["previous_ledger_ref"] = prior_ref
        deleted["snapshot_index"] = 2
        deleted["workflow_blockers"] = []
        with self.assertRaises(audit_ledger.ValidationError) as context:
            audit_ledger.validate_continuity(previous, deleted, prior_ref)
        self.assertEqual(context.exception.path, "$.workflow_blockers")

        reopened = copy.deepcopy(previous)
        reopened["previous_ledger_ref"] = prior_ref
        reopened["snapshot_index"] = 2
        reopened["workflow_blockers"][0]["status"] = "active"
        reopened["workflow_blockers"][0]["resolution_evidence_ids"] = []
        with self.assertRaises(audit_ledger.ValidationError) as context:
            audit_ledger.validate_continuity(previous, reopened, prior_ref)
        self.assertEqual(
            context.exception.path,
            "$.workflow_blockers[B-001].status",
        )

    def test_release_check_evidence_binding_orphans_and_hidden_failures(self):
        self.validate(release_check_payload())

        mismatched = release_check_payload()
        mismatched["evidence"][-1]["release_check_id"] = "other-check-v1"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(mismatched)
        self.assertEqual(context.exception.path, "$.release_checks[0].evidence_ids")

        orphaned = verified_payload()
        orphaned["evidence"].append(
            evidence(
                "E-006",
                state="E3",
                kind="runtime",
                lane="other",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id=None,
                procedure="release-lane",
                summary="An orphaned rollback drill.",
                locator="runtime trace orphaned-check",
                release_check_id="orphan-check-v1",
            )
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(orphaned)
        self.assertEqual(
            context.exception.path,
            "$.evidence[E-006].release_check_id",
        )

        hidden_failure = release_check_payload()
        hidden_failure["evidence"].append(
            evidence(
                "E-007",
                state="E3",
                kind="runtime",
                lane="other",
                result="fail",
                release_ref=CURRENT_RELEASE,
                subject_id=None,
                procedure="release-lane",
                summary="The same-release rollback drill failed.",
                locator="runtime trace rollback-drill-002",
                release_check_id="rollback-readiness-v1",
            )
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(hidden_failure)
        self.assertEqual(context.exception.path, "$.release_checks[0].status")

    def test_scoring_threshold_controls_decision(self):
        payload = verified_payload()
        payload["scoring"] = {
            "requested": True,
            "threshold_met": False,
            "scorecard_ref": "sha256:" + ("d" * 64),
        }
        payload["verdict"].update(
            {
                "current_decision": "NOT_READY",
                "maximum_safe_target": "internal-demo",
            }
        )
        data = self.validate(payload)
        self.assertFalse(data["scoring"]["threshold_met"])

        payload["verdict"]["current_decision"] = "READY"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.verdict.current_decision")

    def test_non_venture_maximum_target_must_match_decision_scope(self):
        for maximum in ("internal-demo", "no-supported-release-tier"):
            with self.subTest(valid=maximum):
                self.validate(unverifiable_payload(maximum_safe_target=maximum))

        for maximum in ("not-assessed", "private-beta"):
            with self.subTest(invalid=maximum):
                with self.assertRaises(audit_ledger.ValidationError) as context:
                    self.validate(
                        unverifiable_payload(maximum_safe_target=maximum)
                    )
                self.assertEqual(
                    context.exception.path, "$.verdict.maximum_safe_target"
                )

        above_request = verified_payload()
        above_request["verdict"]["maximum_safe_target"] = "public-launch"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(above_request)
        self.assertEqual(context.exception.path, "$.verdict.maximum_safe_target")

    def test_venture_case_has_exact_decisions_and_separate_release_lanes(self):
        cases = [
            (
                {
                    "real_users": "present",
                    "retention": "present",
                    "repeatable_distribution": "present",
                },
                "INVESTABLE",
            ),
            (
                {
                    "real_users": "present",
                    "retention": "missing",
                    "repeatable_distribution": "missing",
                },
                "INTERESTING_BUT_UNPROVEN",
            ),
            (
                {
                    "real_users": "missing",
                    "retention": "missing",
                    "repeatable_distribution": "missing",
                },
                "NOT_INVESTABLE_YET",
            ),
            (
                {
                    "real_users": "unknown",
                    "retention": "missing",
                    "repeatable_distribution": "missing",
                },
                "INSUFFICIENT_EVIDENCE",
            ),
        ]
        for statuses, decision in cases:
            with self.subTest(decision=decision):
                data = self.validate(venture_payload(statuses, decision))
                self.assertEqual(data["verdict"]["current_decision"], decision)
                self.assertEqual(
                    data["verdict"]["maximum_safe_target"], "not-assessed"
                )
                self.assertTrue(
                    all(
                        lane["status"] == "N/A"
                        for lane in data["evidence_lanes"].values()
                    )
                )

    def test_venture_assessment_derives_stage_maturity_and_strongest_signal(self):
        statuses = {
            "real_users": "present",
            "retention": "missing",
            "repeatable_distribution": "missing",
        }
        valid = venture_payload(statuses, "INTERESTING_BUT_UNPROVEN")
        data = self.validate(valid)
        self.assertEqual(data["venture_assessment"]["stage"], "structured-diligence")
        self.assertEqual(data["venture_assessment"]["evidence_maturity"], "single-signal")
        self.assertEqual(data["venture_assessment"]["strongest_proven_signal"], "real_users")

        mutations = {
            "stage": "screening",
            "evidence_maturity": "complete",
            "strongest_proven_signal": "retention",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                payload = copy.deepcopy(valid)
                payload["venture_assessment"][field] = value
                with self.assertRaises(audit_ledger.ValidationError) as context:
                    self.validate(payload)
                self.assertEqual(
                    context.exception.path, f"$.venture_assessment.{field}"
                )

    def test_probabilistic_eval_requires_runs_provenance_system_and_thresholds(self):
        data = self.validate(probabilistic_payload(ai_behavior="agent"))
        cited = data["evidence_lanes"]["probabilistic-eval"]["evidence_ids"]
        self.assertEqual(sum(item["runs"] for item in data["evidence"] if item["id"] in cited), 2)
        self.assertTrue(
            all(
                "system" in item["provenance"]
                for item in data["evidence"]
                if item["id"] in cited
            )
        )

        invalid_payloads = {}
        too_few_runs = probabilistic_payload()
        too_few_runs["evidence_lanes"]["probabilistic-eval"]["evidence_ids"] = ["E-006"]
        invalid_payloads["runs"] = too_few_runs

        mixed_provenance = probabilistic_payload()
        mixed_provenance["evidence"][-1]["provenance"]["model"] = "model:gpt-5-v2"
        invalid_payloads["provenance"] = mixed_provenance

        missing_system = probabilistic_payload(ai_behavior="agent")
        for record in missing_system["evidence"][-2:]:
            record["provenance"].pop("system")
        invalid_payloads["system"] = missing_system

        weak_threshold = probabilistic_payload()
        for record in weak_threshold["evidence"][-2:]:
            record["eval_metrics"]["minimum_pass_rate"] = 60
        invalid_payloads["threshold"] = weak_threshold

        permissive_variance = probabilistic_payload()
        for record in permissive_variance["evidence"][-2:]:
            record["eval_metrics"]["maximum_standard_deviation"] = 30
        invalid_payloads["variance-policy"] = permissive_variance

        observed_variance = probabilistic_payload()
        for record in observed_variance["evidence"][-2:]:
            record["eval_metrics"]["observed_standard_deviation"] = 21
        invalid_payloads["observed-variance"] = observed_variance

        for case, payload in invalid_payloads.items():
            with self.subTest(case=case), self.assertRaises(
                audit_ledger.ValidationError
            ) as context:
                self.validate(payload)
            self.assertEqual(
                context.exception.path,
                "$.evidence_lanes.probabilistic-eval.evidence_ids",
            )

    def test_probabilistic_fail_requires_an_observed_threshold_failure(self):
        payload = probabilistic_payload()
        payload["evidence"][-2]["result"] = "fail"
        payload["evidence_lanes"]["probabilistic-eval"]["status"] = "FAIL"
        payload["verdict"].update(
            {
                "current_decision": "NOT_READY",
                "maximum_safe_target": "internal-demo",
            }
        )
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(
            context.exception.path,
            "$.evidence_lanes.probabilistic-eval.status",
        )

        payload["evidence"][-2]["eval_metrics"]["observed_pass_rate"] = 60
        data = self.validate(payload)
        self.assertEqual(data["evidence_lanes"]["probabilistic-eval"]["status"], "FAIL")

    def test_cleared_unknown_requires_current_passing_evidence(self):
        payload = verified_payload()
        payload["evidence"].append(
            evidence(
                "E-006",
                state="E3",
                kind="runtime",
                lane="other",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id="U-001",
                procedure="unknown-resolution",
                summary="Interrupted checkout resumes without losing progress.",
                locator="runtime trace recovery-001",
            )
        )
        payload["unknowns"] = [
            {
                "id": "U-001",
                "unresolved_condition": "Recovery behavior was unknown.",
                "why_it_matters": "Users could lose progress.",
                "missing_evidence": "A recovery-path run.",
                "resolving_test": "Interrupt and resume checkout.",
                "status": "cleared",
                "resolution_evidence_ids": ["E-006"],
                "finding_id": None,
            }
        ]
        self.validate(payload)
        payload["evidence"][5]["result"] = "fail"
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.unknowns[0]")

    def test_e0_cannot_clear_an_unknown(self):
        payload = verified_payload()
        payload["evidence"].append(
            evidence(
                "E-006",
                state="E0",
                kind="runtime",
                lane="other",
                result="pass",
                release_ref=CURRENT_RELEASE,
                subject_id="U-001",
                procedure="unknown-resolution",
                summary="A claim says recovery succeeds, without observed execution.",
                locator="unverified recovery claim",
            )
        )
        payload["unknowns"] = [
            {
                "id": "U-001",
                "unresolved_condition": "Recovery behavior was unknown.",
                "why_it_matters": "Users could lose progress.",
                "missing_evidence": "A recovery-path run.",
                "resolving_test": "Interrupt and resume checkout.",
                "status": "cleared",
                "resolution_evidence_ids": ["E-006"],
                "finding_id": None,
            }
        ]
        with self.assertRaises(audit_ledger.ValidationError) as context:
            self.validate(payload)
        self.assertEqual(context.exception.path, "$.unknowns[0]")

    def test_continuity_rejects_bad_hash_deleted_finding_and_identity_mutation(self):
        prior_payload = base_payload()
        with tempfile.TemporaryDirectory() as temp_dir:
            prior_path = Path(temp_dir) / "prior.json"
            prior_path.write_text(
                json.dumps(prior_payload, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            prior_ref = audit_ledger.ledger_file_ref(prior_path)
            previous = self.validate(prior_payload)
            current_payload = verified_payload()
            current_payload["previous_ledger_ref"] = prior_ref
            current_payload["snapshot_index"] = 2
            current = self.validate(current_payload)
            audit_ledger.validate_continuity(previous, current, prior_ref)

            wrong_hash = copy.deepcopy(current)
            wrong_hash["previous_ledger_ref"] = "sha256:" + ("c" * 64)
            wrong_hash["snapshot_index"] = 2
            with self.subTest(case="hash"), self.assertRaises(
                audit_ledger.ValidationError
            ) as context:
                audit_ledger.validate_continuity(previous, wrong_hash, prior_ref)
            self.assertEqual(context.exception.path, "$.previous_ledger_ref")

            deleted = copy.deepcopy(current)
            deleted["findings"] = []
            with self.subTest(case="deleted"), self.assertRaises(
                audit_ledger.ValidationError
            ) as context:
                audit_ledger.validate_continuity(previous, deleted, prior_ref)
            self.assertEqual(context.exception.path, "$.findings")

            mutated = copy.deepcopy(current)
            mutated["findings"][0]["impact"] = "A rewritten impact hides the original scope."
            with self.subTest(case="mutated"), self.assertRaises(
                audit_ledger.ValidationError
            ) as context:
                audit_ledger.validate_continuity(previous, mutated, prior_ref)
            self.assertEqual(context.exception.path, "$.findings[F-001]")

    def test_continuity_preserves_root_causes_and_gate_evidence_history(self):
        prior_path = ROOT / "evals" / "ledgers" / "initial.json"
        current_path = ROOT / "evals" / "ledgers" / "closed-loop.json"
        prior_ref = audit_ledger.ledger_file_ref(prior_path)
        previous = audit_ledger.load_ledger(prior_path)
        current = audit_ledger.load_ledger(current_path)
        audit_ledger.validate_continuity(previous, current, prior_ref)

        rewritten_root = copy.deepcopy(current)
        rewritten_root["root_causes"][0]["summary"] = "History rewritten."
        with self.assertRaises(audit_ledger.ValidationError) as context:
            audit_ledger.validate_continuity(previous, rewritten_root, prior_ref)
        self.assertEqual(context.exception.path, "$.root_causes[RC-001]")

        dropped_gate_evidence = copy.deepcopy(current)
        dropped_gate_evidence["gates"][0]["evidence_ids"] = []
        with self.assertRaises(audit_ledger.ValidationError) as context:
            audit_ledger.validate_continuity(previous, dropped_gate_evidence, prior_ref)
        self.assertEqual(
            context.exception.path, "$.gates[authorization-bypass].evidence_ids"
        )

    def test_renderer_surfaces_decision_evidence_and_assessment_details(self):
        gate_payload = active_gate_payload(deployment_evidence=True)
        finding = gate_payload["findings"][0]
        finding["status"] = "accepted-risk"
        finding["risk_acceptance"] = {
            "accepted_by": "user",
            "statement": "Accept this issue for the restricted rollout.",
            "scope": "F-001 on real-money",
            "rationale": "Manual reconciliation remains available.",
        }
        gate_markdown = audit_ledger.render_markdown(
            self.validate(gate_payload), "en"
        )
        self.assertIn("Risk scope: F-001 on real-money", gate_markdown)
        self.assertIn("**duplicate-real-charge · active**", gate_markdown)
        self.assertIn("failure evidence: E-001", gate_markdown)
        self.assertIn("retest evidence: None.", gate_markdown)
        self.assertIn(
            "deployment coverage=scope_complete:true,"
            "compensating_layer_ruled_out:true",
            gate_markdown,
        )

        mutation_markdown = audit_ledger.render_markdown(
            self.validate(unverifiable_payload()), "en"
        )
        self.assertIn(
            "Mutation reason: No executable retest environment is available.",
            mutation_markdown,
        )

        release_payload = release_check_payload()
        release_payload["scoring"] = {
            "requested": True,
            "threshold_met": True,
            "scorecard_ref": "sha256:" + ("d" * 64),
        }
        release_markdown = audit_ledger.render_markdown(
            self.validate(release_payload), "en"
        )
        self.assertIn("## Release checks", release_markdown)
        self.assertIn("**rollback-readiness-v1 · pass**", release_markdown)
        self.assertIn("## Scoring", release_markdown)
        self.assertIn("Threshold met: `true`", release_markdown)
        self.assertIn("Scorecard: `sha256:" + ("d" * 64) + "`", release_markdown)

        venture_markdown = audit_ledger.render_markdown(
            self.validate(
                venture_payload(
                    {
                        "real_users": "present",
                        "retention": "missing",
                        "repeatable_distribution": "missing",
                    },
                    "INTERESTING_BUT_UNPROVEN",
                )
            ),
            "en",
        )
        self.assertIn("## Venture assessment", venture_markdown)
        self.assertIn("Stage: structured-diligence", venture_markdown)
        self.assertIn("`real_users`: **present** (E-010)", venture_markdown)

    def test_renderer_leads_with_issues_then_lanes_and_keeps_unverifiable_pending(self):
        markdown = audit_ledger.render_markdown(
            self.validate(unverifiable_payload()), "en"
        )
        self.assertTrue(
            markdown.startswith(
                "# RateMyCode audit ledger\n\n## One-line problem list\n"
            )
        )
        issues_index = markdown.index("## One-line problem list")
        lanes_index = markdown.index("## Evidence lanes")
        identity_index = markdown.index("## Review identity")
        self.assertLess(issues_index, lanes_index)
        self.assertLess(lanes_index, identity_index)

        pending = markdown[
            markdown.index("### Pending verification") : lanes_index
        ]
        self.assertNotIn("### Unresolved", markdown)
        self.assertNotIn("### Verified fixed", markdown)
        self.assertIn("- [HIGH · F-001 · UNVERIFIED]", pending)

    def test_renderer_escapes_untrusted_markdown_and_html(self):
        payload = base_payload()
        payload["findings"][0]["title"] = "<script>alert(1)</script> ![pixel](https://evil)"
        payload["evidence"][0]["locator"] = "app.py:`danger`"
        markdown = audit_ledger.render_markdown(self.validate(payload), "en")
        self.assertNotIn("<script>", markdown)
        self.assertNotIn("![pixel]", markdown)
        self.assertIn(r"\<script\>", markdown)
        self.assertIn("`` app.py:`danger` ``", markdown)

    def test_cli_validate_emits_machine_readable_summary(self):
        result = self.run_cli("validate", base_payload())
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertTrue(summary["valid"])
        self.assertEqual(summary["unresolved"], 1)

    def test_snapshot_index_marks_the_root_and_detects_a_lost_round(self):
        # A root snapshot is the only one allowed to be unlinked.
        orphan = base_payload()
        orphan["snapshot_index"] = 2
        result = self.run_cli("validate", orphan)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be 1 exactly when previous_ledger_ref is null", result.stderr)

        # A chained snapshot may not claim index 1.
        chained = verified_payload()
        chained["previous_ledger_ref"] = "sha256:" + ("c" * 64)
        chained["snapshot_index"] = 1
        result = self.run_cli("validate", chained)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be 1 exactly when previous_ledger_ref is null", result.stderr)

    def test_recorded_at_is_optional_but_must_be_rfc3339_utc(self):
        payload = base_payload()
        payload["recorded_at"] = "2026-07-31T04:05:06Z"
        self.assertEqual(self.run_cli("validate", payload).returncode, 0)
        payload["recorded_at"] = "31/07/2026 04:05"
        result = self.run_cli("validate", payload)
        self.assertEqual(result.returncode, 2)
        self.assertIn("RFC 3339 UTC timestamp", result.stderr)

    def test_cli_requires_prior_file_for_a_chained_snapshot(self):
        payload = verified_payload()
        payload["previous_ledger_ref"] = "sha256:" + ("c" * 64)
        payload["snapshot_index"] = 2
        result = self.run_cli("validate", payload)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be validated or rendered with --prior", result.stderr)

    def test_cli_renders_complete_chinese_issue_sections(self):
        result = self.run_cli("render", verified_payload(), "--language", "zh-CN")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# RateMyCode 审计台账", result.stdout)
        self.assertIn("## 一句话问题清单", result.stdout)
        self.assertNotIn("### 已验证修复", result.stdout)
        self.assertIn("- [HIGH · F-001 · 已验证修复]", result.stdout)
        self.assertIn("已验证闭环", result.stdout)

    def test_cli_refuses_to_overwrite_ledger_with_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            original = json.dumps(base_payload())
            ledger_path.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    "--output",
                    str(ledger_path),
                    str(ledger_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(ledger_path.read_text(encoding="utf-8"), original)

    def test_cli_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text(
                '{"schema_version":"1","schema_version":"2"}', encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(ledger_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate JSON object key", result.stderr)

    def test_cli_rejects_control_characters_in_values_and_object_keys(self):
        value_payload = base_payload()
        value_payload["findings"][0]["title"] = "unsafe\x1b[31m title"
        value_result = self.run_cli("validate", value_payload)
        self.assertEqual(value_result.returncode, 2)
        self.assertIn("must not contain terminal, control, or bidirectional", value_result.stderr)
        self.assertNotIn("Traceback", value_result.stderr)

        bidi_payload = base_payload()
        bidi_payload["artifact"]["name"] = "safe\u202eforged"
        bidi_result = self.run_cli("validate", bidi_payload)
        self.assertEqual(bidi_result.returncode, 2)
        self.assertIn("bidirectional override characters", bidi_result.stderr)
        self.assertNotIn("Traceback", bidi_result.stderr)

        key_payload = base_payload()
        key_payload["\x01hidden"] = "value"
        key_result = self.run_cli("validate", key_payload)
        self.assertEqual(key_result.returncode, 2)
        self.assertIn("JSON object keys must not contain control", key_result.stderr)
        self.assertNotIn("Traceback", key_result.stderr)

    def test_cli_reports_deep_json_recursion_without_traceback(self):
        result = self.run_cli_text("validate", "[" * 5000 + "0" + "]" * 5000)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("ERROR: $:"), result.stderr)
        self.assertTrue(
            "invalid UTF-8 JSON" in result.stderr or "must be an object" in result.stderr,
            result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
