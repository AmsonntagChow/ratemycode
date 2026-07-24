import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "vibe-code-jury" / "scripts" / "score_review.py"
SPEC = importlib.util.spec_from_file_location("score_review", SCRIPT)
score_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(score_review)


def base_payload():
    evidence = [
        {"id": "e-runtime", "kind": "runtime", "result": "pass", "reproducible": True},
        {"id": "e-test", "kind": "test", "result": "pass", "reproducible": True},
    ]
    return {
        "schema_version": "1",
        "mode": "ship-fast",
        "rubric_id": "test/default-v1",
        "release_target": "public-launch",
        "dimensions": [
            {"id": "flows", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-runtime"]},
            {"id": "integrity", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-test"]},
            {"id": "security", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-test"]},
            {"id": "operations", "weight": 25, "score": 90, "verification": "verified", "evidence_ids": ["e-runtime"]},
        ],
        "evidence": evidence,
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

    def test_active_gate_blocks_and_cannot_be_averaged_away(self):
        payload = base_payload()
        payload["evidence"].append(
            {"id": "e-auth", "kind": "runtime", "result": "fail", "reproducible": True}
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

    def test_static_review_preserves_raw_score_but_cannot_approve_release(self):
        payload = base_payload()
        payload["evidence"] = [
            {"id": "e-code", "kind": "code", "result": "mixed", "reproducible": True}
        ]
        for dimension in payload["dimensions"]:
            dimension["verification"] = "partial"
            dimension["evidence_ids"] = ["e-code"]
        payload["coverage"] = {"runtime": "static", "critical_paths": {"total": 4, "tested": 0}}
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
        payload["gates"] = [
            {
                "id": "duplicate-real-charge",
                "state": "fixed",
                "evidence_ids": [],
                "retest_evidence_ids": ["e-test"],
            }
        ]
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertFalse(result["vetoed"])

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
            {"id": "e-failure", "kind": "runtime", "result": "fail", "reproducible": True}
        )
        payload["release_checks"] = [
            {"id": "recovery", "required": True, "status": "fail", "evidence_ids": ["e-failure"]}
        ]
        self.assertEqual(self.compute(payload)["decision"], "NOT_READY")

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
        payload["vc_signals"] = {
            key: {"status": "present", "evidence_ids": ["e-runtime"]}
            for key in ("real_users", "retention", "repeatable_distribution")
        }
        result = self.compute(payload)
        self.assertEqual(result["decision"], "READY")
        self.assertFalse(any(item["source"] == "venture-evidence" for item in result["applied_caps"]))

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
