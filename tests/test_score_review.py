import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ratemycode" / "scripts" / "score_review.py"
SPEC = importlib.util.spec_from_file_location("score_review", SCRIPT)
score_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(score_review)
RELEASE_REF = "sha256:" + ("a" * 64)
OLD_RELEASE_REF = "sha256:" + ("b" * 64)


def base_payload():
    evidence = [
        {
            "id": "e-runtime",
            "kind": "runtime",
            "lane": "critical-journey-e2e",
            "result": "pass",
            "reproducible": True,
            "fresh": True,
            "release_ref": RELEASE_REF,
        },
        {
            "id": "e-test",
            "kind": "test",
            "lane": "deterministic-checks",
            "result": "pass",
            "reproducible": True,
            "fresh": True,
            "release_ref": RELEASE_REF,
        },
        {
            "id": "e-log",
            "kind": "log",
            "lane": "continuous-evidence",
            "result": "pass",
            "reproducible": True,
            "fresh": True,
            "release_ref": RELEASE_REF,
        },
    ]
    return {
        "schema_version": "2",
        "mode": "ship-fast",
        "rubric_id": "test/default-v1",
        "release_target": "public-launch",
        "release_ref": RELEASE_REF,
        "ai_behavior": "none",
        "dimensions": [
            {"id": "flows", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-runtime"]},
            {"id": "integrity", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-test"]},
            {"id": "security", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-test"]},
            {"id": "operations", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-runtime"]},
        ],
        "evidence": evidence,
        "evidence_lanes": {
            "deterministic-checks": {"status": "PASS", "evidence_ids": ["e-test"]},
            "critical-journey-e2e": {"status": "PASS", "evidence_ids": ["e-runtime"]},
            "probabilistic-eval": {
                "status": "N/A",
                "evidence_ids": [],
                "reason": "The product has no LLM, agent, or RAG behavior.",
            },
            "continuous-evidence": {"status": "PASS", "evidence_ids": ["e-log"]},
        },
        "coverage": {"runtime": "e2e", "critical_paths": {"total": 4, "tested": 4}},
        "gates": [],
        "release_checks": [
            {"id": "critical-flow", "required": True, "status": "pass", "evidence_ids": ["e-runtime"]}
        ],
    }


class ScoreReviewTests(unittest.TestCase):
    def compute(self, payload):
        return score_review.compute(score_review.validate(payload))

    def run_cli(self, payload_text=None, extra_args=None):
        extra_args = extra_args or []
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scorecard.json"
            if payload_text is not None:
                path.write_text(payload_text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), *extra_args, str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_verified_product_is_ready(self):
        result = self.compute(base_payload())
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["scores"], {"raw_product": 90, "readiness": 90})
        self.assertEqual(result["coverage"]["confidence"], "A")
        self.assertEqual(result["policy_version"], "3")
        self.assertEqual(result["evidence_lanes"]["probabilistic-eval"]["status"], "N/A")

    def test_staff_engineer_mode_is_supported(self):
        payload = base_payload()
        payload["mode"] = "staff-engineer"
        result = self.compute(payload)
        self.assertEqual(result["mode"], "staff-engineer")

    def test_active_gate_blocks_and_cannot_be_averaged_away(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-auth",
                "kind": "runtime",
                "lane": "other",
                "gate_id": "authorization-bypass",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-auth"],
                "retest_evidence_ids": [],
            }
        ]
        result = self.compute(payload)
        self.assertEqual(result["scores"]["raw_product"], 90)
        self.assertEqual(result["scores"]["readiness"], 39)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertTrue(result["vetoed"])
        self.assertEqual(result["active_gates"], result["blocking_gates"])
        self.assertEqual(
            result["active_gates"][0]["affected_targets"],
            sorted(score_review.RELEASE_THRESHOLDS),
        )

    def test_active_gate_outside_requested_target_is_reported_but_does_not_block(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-auth",
                "kind": "runtime",
                "lane": "other",
                "gate_id": "authorization-bypass",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-auth"],
                "retest_evidence_ids": [],
                "affected_targets": ["real-money", "high-stakes"],
            }
        ]
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["scores"]["readiness"], 90)
        self.assertEqual(len(result["active_gates"]), 1)
        self.assertEqual(result["blocking_gates"], [])
        self.assertFalse(result["vetoed"])
        self.assertFalse(any(item["source"] == "safety-gate" for item in result["applied_caps"]))

    def test_active_gate_inside_requested_target_blocks(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-auth",
                "kind": "runtime",
                "lane": "other",
                "gate_id": "authorization-bypass",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-auth"],
                "retest_evidence_ids": [],
                "affected_targets": ["private-beta", "public-launch"],
            }
        ]
        result = self.compute(payload)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["scores"]["readiness"], 39)
        self.assertEqual(result["active_gates"], result["blocking_gates"])
        self.assertTrue(result["vetoed"])

    def test_active_gate_rejects_weak_or_static_only_evidence(self):
        invalid_evidence = (
            {"kind": "claim", "lane": "other", "result": "fail", "reproducible": True},
            {
                "kind": "runtime",
                "lane": "other",
                "result": "fail",
                "reproducible": False,
            },
            {
                "kind": "code",
                "lane": "other",
                "result": "fail",
                "reproducible": True,
            },
        )
        for evidence in invalid_evidence:
            with self.subTest(evidence=evidence):
                payload = base_payload()
                payload["evidence"].append(
                    {"id": "e-weak", "fresh": True, "release_ref": RELEASE_REF, **evidence}
                )
                payload["gates"] = [
                    {
                        "id": "authorization-bypass",
                        "state": "active",
                        "evidence_ids": ["e-weak"],
                        "retest_evidence_ids": [],
                    }
                ]
                with self.assertRaises(score_review.ValidationError) as context:
                    score_review.validate(payload)
                self.assertEqual(context.exception.path, "$.gates[0].evidence_ids")

    def test_active_gate_rejects_evidence_from_another_release(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-old-failure",
                "kind": "runtime",
                "lane": "other",
                "gate_id": "authorization-bypass",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": OLD_RELEASE_REF,
            }
        )
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-old-failure"],
                "retest_evidence_ids": [],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].evidence_ids")

    def test_gate_scope_must_not_be_empty(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-runtime"],
                "retest_evidence_ids": [],
                "affected_targets": [],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].affected_targets")

    def test_gate_scope_rejects_unknown_target(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-runtime"],
                "retest_evidence_ids": [],
                "affected_targets": ["production"],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].affected_targets[0]")

    def test_gate_scope_rejects_duplicates(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "authorization-bypass",
                "state": "active",
                "evidence_ids": ["e-runtime"],
                "retest_evidence_ids": [],
                "affected_targets": ["public-launch", "public-launch"],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].affected_targets")

    def test_static_review_preserves_raw_score_but_cannot_approve_release(self):
        payload = base_payload()
        payload["evidence"] = [
            {
                "id": "e-code",
                "kind": "code",
                "lane": "deterministic-checks",
                "result": "mixed",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        ]
        for dimension in payload["dimensions"]:
            dimension["verification"] = "partial"
            dimension["evidence_ids"] = ["e-code"]
        payload["coverage"] = {"runtime": "static", "critical_paths": {"total": 4, "tested": 0}}
        payload["evidence_lanes"] = {
            "deterministic-checks": {"status": "UNVERIFIED", "evidence_ids": []},
            "critical-journey-e2e": {"status": "UNVERIFIED", "evidence_ids": []},
            "probabilistic-eval": {
                "status": "N/A",
                "evidence_ids": [],
                "reason": "The product has no LLM, agent, or RAG behavior.",
            },
            "continuous-evidence": {"status": "UNVERIFIED", "evidence_ids": []},
        }
        payload["release_checks"] = [
            {"id": "critical-flow", "required": True, "status": "unverified", "evidence_ids": []}
        ]
        result = self.compute(payload)
        self.assertEqual(result["scores"]["raw_product"], 90)
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["coverage"]["confidence"], "C")

    def test_fixed_gate_requires_retest(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "duplicate-real-charge",
                "state": "fixed",
                "evidence_ids": [],
                "retest_evidence_ids": [],
            }
        ]
        with self.assertRaises(score_review.ValidationError):
            score_review.validate(payload)

    def test_fixed_gate_accepts_reproducible_test(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-charge-retest",
                "kind": "test",
                "lane": "deterministic-checks",
                "gate_id": "duplicate-real-charge",
                "result": "pass",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["gates"] = [
            {
                "id": "duplicate-real-charge",
                "state": "fixed",
                "evidence_ids": [],
                "retest_evidence_ids": ["e-charge-retest"],
            }
        ]
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertFalse(result["vetoed"])

    def test_fixed_gate_rejects_unrelated_passing_test(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "duplicate-real-charge",
                "state": "fixed",
                "evidence_ids": [],
                "retest_evidence_ids": ["e-test"],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.gates[0].retest_evidence_ids")

    def test_weights_must_total_100(self):
        payload = base_payload()
        payload["dimensions"][0]["weight"] = 24
        with self.assertRaises(score_review.ValidationError):
            score_review.validate(payload)

    def test_boolean_is_not_an_integer_score(self):
        payload = base_payload()
        payload["dimensions"][0]["score"] = True
        with self.assertRaises(score_review.ValidationError):
            score_review.validate(payload)

    def test_required_failed_check_is_not_ready(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-failure",
                "kind": "runtime",
                "lane": "other",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["release_checks"] = [
            {"id": "recovery", "required": True, "status": "fail", "evidence_ids": ["e-failure"]}
        ]
        self.assertEqual(self.compute(payload)["decision"], "NOT_READY")

    def test_passing_release_check_rejects_failing_evidence(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-failing-check",
                "kind": "runtime",
                "lane": "other",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["release_checks"] = [
            {
                "id": "critical-flow",
                "required": True,
                "status": "pass",
                "evidence_ids": ["e-failing-check"],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.release_checks[0].evidence_ids")

    def test_failed_release_check_rejects_evidence_from_another_release(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-old-failure",
                "kind": "runtime",
                "lane": "critical-journey-e2e",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": OLD_RELEASE_REF,
            }
        )
        payload["release_checks"] = [
            {
                "id": "recovery",
                "required": True,
                "status": "fail",
                "evidence_ids": ["e-old-failure"],
            }
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.release_checks[0].evidence_ids")

    def test_stale_evidence_cannot_pass_release_check(self):
        payload = base_payload()
        next(item for item in payload["evidence"] if item["id"] == "e-runtime")["fresh"] = False
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_evidence_from_another_release_cannot_pass_a_lane(self):
        payload = base_payload()
        next(item for item in payload["evidence"] if item["id"] == "e-runtime")["release_ref"] = OLD_RELEASE_REF
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_evidence_from_another_release_cannot_verify_a_dimension(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-stale-dimension",
                "kind": "code",
                "lane": "deterministic-checks",
                "result": "pass",
                "reproducible": True,
                "fresh": True,
                "release_ref": OLD_RELEASE_REF,
            }
        )
        payload["dimensions"][0]["evidence_ids"] = ["e-stale-dimension"]

        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.dimensions[0].evidence_ids")

    def test_structural_test_cannot_substitute_for_e2e(self):
        payload = base_payload()
        payload["evidence_lanes"]["critical-journey-e2e"]["evidence_ids"] = ["e-test"]
        payload["evidence_lanes"]["deterministic-checks"] = {
            "status": "UNVERIFIED",
            "evidence_ids": [],
        }
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_runtime_smoke_declared_outside_e2e_cannot_substitute_for_e2e(self):
        payload = base_payload()
        next(item for item in payload["evidence"] if item["id"] == "e-runtime")["lane"] = "other"
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_lane_pass_cannot_hide_a_cited_failure(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-runtime-failure",
                "kind": "runtime",
                "lane": "critical-journey-e2e",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["evidence_lanes"]["critical-journey-e2e"]["evidence_ids"].append(
            "e-runtime-failure"
        )
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_lane_pass_cannot_hide_an_uncited_same_release_failure(self):
        payload = base_payload()
        payload["evidence"].append(
            {
                "id": "e-hidden-runtime-failure",
                "kind": "runtime",
                "lane": "critical-journey-e2e",
                "result": "fail",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.critical-journey-e2e.evidence_ids")

    def test_one_evidence_item_cannot_substitute_across_lanes(self):
        payload = base_payload()
        payload["evidence_lanes"]["continuous-evidence"]["evidence_ids"] = ["e-runtime"]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.continuous-evidence.evidence_ids")

    def test_ai_product_cannot_mark_probabilistic_eval_not_applicable(self):
        payload = base_payload()
        payload["ai_behavior"] = "agent"
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.status")

    def test_ai_product_requires_repeated_version_bound_eval(self):
        payload = base_payload()
        payload["ai_behavior"] = "agent"
        payload["evidence"].append(
            {
                "id": "e-eval",
                "kind": "eval",
                "lane": "probabilistic-eval",
                "result": "pass",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
                "runs": 1,
                "provenance": {
                    "model": "model:v1",
                    "prompt": "prompt:sha256:abc",
                    "eval_set": "eval-set:v2",
                    "judge": "deterministic-rubric:v1",
                    "system": "tools-and-retrieval:sha256:def",
                },
                "eval_metrics": {
                    "minimum_pass_rate": 80,
                    "observed_pass_rate": 90,
                    "maximum_standard_deviation": 10,
                    "observed_standard_deviation": 5,
                },
            }
        )
        payload["evidence_lanes"]["probabilistic-eval"] = {
            "status": "PASS",
            "evidence_ids": ["e-eval"],
        }
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.evidence_ids")

        payload["evidence"][-1]["runs"] = 2
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["evidence_lanes"]["probabilistic-eval"]["status"], "PASS")

        payload["evidence"][-1]["eval_metrics"]["observed_pass_rate"] = 79
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.evidence_ids")

        payload["evidence"][-1]["eval_metrics"]["observed_pass_rate"] = 90
        payload["evidence"][-1]["eval_metrics"]["observed_standard_deviation"] = 11
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.evidence_ids")

    def test_ai_eval_rejects_weak_thresholds_and_mixed_identities(self):
        payload = base_payload()
        payload["ai_behavior"] = "agent"
        eval_item = {
            "id": "e-eval-one",
            "kind": "eval",
            "lane": "probabilistic-eval",
            "result": "pass",
            "reproducible": True,
            "fresh": True,
            "release_ref": RELEASE_REF,
            "runs": 2,
            "provenance": {
                "model": "model:v1",
                "prompt": "prompt:sha256:abc",
                "eval_set": "eval-set:v2",
                "judge": "deterministic-rubric:v1",
                "system": "tools-and-retrieval:sha256:def",
            },
            "eval_metrics": {
                "minimum_pass_rate": 1,
                "observed_pass_rate": 100,
                "maximum_standard_deviation": 100,
                "observed_standard_deviation": 0,
            },
        }
        payload["evidence"].append(eval_item)
        payload["evidence_lanes"]["probabilistic-eval"] = {
            "status": "PASS",
            "evidence_ids": ["e-eval-one"],
        }
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.evidence_ids")

        eval_item["eval_metrics"]["minimum_pass_rate"] = 80
        eval_item["eval_metrics"]["maximum_standard_deviation"] = 10
        eval_item["runs"] = 1
        second = copy.deepcopy(eval_item)
        second["id"] = "e-eval-two"
        second["provenance"]["model"] = "model:v2"
        payload["evidence"].append(second)
        payload["evidence_lanes"]["probabilistic-eval"]["evidence_ids"] = [
            "e-eval-one",
            "e-eval-two",
        ]
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.evidence_lanes.probabilistic-eval.evidence_ids")

    def test_mutable_release_alias_is_rejected(self):
        payload = base_payload()
        payload["release_ref"] = "latest"
        for item in payload["evidence"]:
            item["release_ref"] = "latest"
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.release_ref")

    def test_e2e_coverage_requires_every_declared_critical_path(self):
        payload = base_payload()
        payload["release_target"] = "private-beta"
        payload["coverage"]["critical_paths"]["tested"] = 0
        with self.assertRaises(score_review.ValidationError) as context:
            score_review.validate(payload)
        self.assertEqual(context.exception.path, "$.coverage.critical_paths.tested")

    def test_unverified_required_lane_limits_readiness(self):
        payload = base_payload()
        payload["release_target"] = "private-beta"
        payload["evidence_lanes"]["deterministic-checks"] = {
            "status": "UNVERIFIED",
            "evidence_ids": [],
        }
        result = self.compute(payload)
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(
            result["release_checks"]["unverified_evidence_lanes"], ["deterministic-checks"]
        )

    def test_missing_vc_signals_cap_readiness(self):
        payload = base_payload()
        payload["mode"] = "skeptical-vc"
        payload["release_target"] = "venture-case"
        payload["vc_signals"] = {
            "real_users": {"status": "missing", "evidence_ids": []},
            "retention": {"status": "unknown", "evidence_ids": []},
            "repeatable_distribution": {"status": "unknown", "evidence_ids": []},
        }
        result = self.compute(payload)
        self.assertEqual(result["scores"]["raw_product"], 90)
        self.assertEqual(result["scores"]["readiness"], 45)
        self.assertEqual(result["decision"], "NOT_READY")

    def test_present_vc_signals_require_and_accept_evidence(self):
        payload = base_payload()
        payload["mode"] = "skeptical-vc"
        payload["release_target"] = "venture-case"
        payload["evidence"].extend(
            [
                {
                    "id": "e-real-users",
                    "kind": "runtime",
                    "lane": "vc-real-users",
                    "result": "pass",
                    "reproducible": True,
                    "fresh": True,
                    "release_ref": RELEASE_REF,
                },
                {
                    "id": "e-retention",
                    "kind": "metric",
                    "lane": "vc-retention",
                    "result": "pass",
                    "reproducible": True,
                    "fresh": True,
                    "release_ref": RELEASE_REF,
                },
                {
                    "id": "e-distribution",
                    "kind": "metric",
                    "lane": "vc-repeatable-distribution",
                    "result": "pass",
                    "reproducible": True,
                    "fresh": True,
                    "release_ref": RELEASE_REF,
                },
            ]
        )
        payload["vc_signals"] = {
            "real_users": {"status": "present", "evidence_ids": ["e-real-users"]},
            "retention": {"status": "present", "evidence_ids": ["e-retention"]},
            "repeatable_distribution": {
                "status": "present",
                "evidence_ids": ["e-distribution"],
            },
        }
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertFalse(any(item["source"] == "venture-evidence" for item in result["applied_caps"]))

    def test_vc_signals_reject_cross_signal_evidence_substitution(self):
        payload = base_payload()
        payload["mode"] = "skeptical-vc"
        payload["release_target"] = "venture-case"
        payload["evidence"].append(
            {
                "id": "e-users",
                "kind": "runtime",
                "lane": "vc-real-users",
                "result": "pass",
                "reproducible": True,
                "fresh": True,
                "release_ref": RELEASE_REF,
            }
        )
        payload["vc_signals"] = {
            "real_users": {"status": "present", "evidence_ids": ["e-users"]},
            "retention": {"status": "present", "evidence_ids": ["e-users"]},
            "repeatable_distribution": {"status": "unknown", "evidence_ids": []},
        }
        with self.assertRaises(score_review.ValidationError):
            score_review.validate(payload)

    def test_unknown_gate_is_rejected(self):
        payload = base_payload()
        payload["gates"] = [
            {
                "id": "caller-invented-gate",
                "state": "active",
                "evidence_ids": ["e-runtime"],
                "retest_evidence_ids": [],
            }
        ]
        with self.assertRaises(score_review.ValidationError):
            score_review.validate(payload)

    def test_input_order_does_not_change_output(self):
        payload = base_payload()
        first = score_review.render(self.compute(payload), pretty=False)
        reordered = copy.deepcopy(payload)
        reordered["dimensions"].reverse()
        reordered["evidence"].reverse()
        second = score_review.render(self.compute(reordered), pretty=False)
        self.assertEqual(first, second)

    def test_cli_success_uses_stdout_only(self):
        result = self.run_cli(json.dumps(base_payload()))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_cli_invalid_json_exits_one_and_uses_stderr(self):
        result = self.run_cli("{not-json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["error"]["code"], "validation_error")

    def test_cli_argument_error_exits_two(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--unknown"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["error"]["code"], "argument_error")


if __name__ == "__main__":
    unittest.main()
