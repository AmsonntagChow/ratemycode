#!/usr/bin/env python3
"""Validate and score a RateMyCode review using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
POLICY_VERSION = "1"
MAX_INPUT_BYTES = 1_048_576
MAX_DIMENSIONS = 32
MAX_EVIDENCE = 512

MODES = {
    "ship-fast",
    "strict-professor",
    "hostile-user",
    "skeptical-vc",
    "oral-defense",
}
RELEASE_THRESHOLDS = {
    "internal-demo": Decimal("50"),
    "private-beta": Decimal("65"),
    "public-launch": Decimal("75"),
    "real-money": Decimal("85"),
    "high-stakes": Decimal("90"),
    "venture-case": Decimal("70"),
}
VERIFICATION_FACTORS = {
    "verified": Decimal("1"),
    "partial": Decimal("0.5"),
    "unverified": Decimal("0"),
}
EVIDENCE_KINDS = {
    "runtime",
    "test",
    "code",
    "log",
    "metric",
    "interview",
    "document",
    "claim",
}
EVIDENCE_RESULTS = {"pass", "fail", "mixed", "inconclusive"}
RUNTIME_LEVELS = {"e2e", "partial", "static", "none"}
RUNTIME_CONFIDENCE_CAP = {"e2e": "A", "partial": "B", "static": "C", "none": "D"}
CONFIDENCE_SCORE_CAP = {
    "A": Decimal("100"),
    "B": Decimal("89"),
    "C": Decimal("69"),
    "D": Decimal("49"),
}
SAFETY_GATES = {
    "authorization-bypass": Decimal("39"),
    "sensitive-data-exposure": Decimal("39"),
    "irreversible-data-loss": Decimal("39"),
    "duplicate-real-charge": Decimal("39"),
    "critical-flow-false-success": Decimal("39"),
}
VC_CAPS = {
    "real_users": Decimal("45"),
    "retention": Decimal("60"),
    "repeatable_distribution": Decimal("75"),
}
CONFIDENCE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


class ValidationError(Exception):
    def __init__(self, path: str, message: str) -> None:
        super().__init__(message)
        self.path = path
        self.message = message


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        emit_error("argument_error", "$", message)
        raise SystemExit(2)


def emit_error(code: str, path: str, message: str) -> None:
    payload = {"error": {"code": code, "message": message, "path": path}, "ok": False}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=sys.stderr)


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite number {value} is not allowed")


def load_payload(path: Path) -> Any:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ValidationError("$", f"cannot read input file: {exc.strerror or exc}") from exc
    if size > MAX_INPUT_BYTES:
        raise ValidationError("$", f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except UnicodeDecodeError as exc:
        raise ValidationError("$", f"input must be UTF-8: {exc}") from exc
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError("$", f"invalid JSON: {exc}") from exc


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(path, "must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(path, "must be an array")
    return value


def require_string(value: Any, path: str, allowed: set[str] | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(path, "must be a non-empty string")
    if allowed is not None and value not in allowed:
        raise ValidationError(path, f"must be one of {sorted(allowed)}; received {value!r}")
    return value


def require_bool(value: Any, path: str) -> bool:
    if type(value) is not bool:
        raise ValidationError(path, "must be true or false")
    return value


def require_int(value: Any, path: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ValidationError(path, f"must be an integer between {minimum} and {maximum}")
    if value < minimum or value > maximum:
        raise ValidationError(path, f"must be an integer between {minimum} and {maximum}; received {value}")
    return value


def reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise ValidationError(path, f"unexpected field(s): {', '.join(unknown)}")


def require_fields(obj: dict[str, Any], required: set[str], path: str) -> None:
    missing = sorted(required - set(obj))
    if missing:
        raise ValidationError(path, f"missing required field(s): {', '.join(missing)}")


def validate_evidence(items: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    values = require_list(items, "$.evidence")
    if len(values) > MAX_EVIDENCE:
        raise ValidationError("$.evidence", f"must contain at most {MAX_EVIDENCE} items")
    result: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    allowed = {"id", "kind", "result", "reproducible"}
    for index, raw in enumerate(values):
        path = f"$.evidence[{index}]"
        item = require_object(raw, path)
        reject_unknown(item, allowed, path)
        require_fields(item, allowed, path)
        evidence_id = require_string(item["id"], f"{path}.id")
        if evidence_id in by_id:
            raise ValidationError(f"{path}.id", f"duplicate evidence id {evidence_id!r}")
        normalized = {
            "id": evidence_id,
            "kind": require_string(item["kind"], f"{path}.kind", EVIDENCE_KINDS),
            "result": require_string(item["result"], f"{path}.result", EVIDENCE_RESULTS),
            "reproducible": require_bool(item["reproducible"], f"{path}.reproducible"),
        }
        by_id[evidence_id] = normalized
        result.append(normalized)
    return sorted(result, key=lambda item: item["id"]), by_id


def validate_evidence_ids(
    raw_ids: Any,
    path: str,
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    values = require_list(raw_ids, path)
    ids: list[str] = []
    for index, value in enumerate(values):
        evidence_id = require_string(value, f"{path}[{index}]")
        if evidence_id not in evidence_by_id:
            raise ValidationError(f"{path}[{index}]", f"unknown evidence id {evidence_id!r}")
        ids.append(evidence_id)
    if len(ids) != len(set(ids)):
        raise ValidationError(path, "must not contain duplicate evidence ids")
    return sorted(ids)


def has_reproducible_non_claim(ids: list[str], evidence: dict[str, dict[str, Any]]) -> bool:
    return any(evidence[item]["kind"] != "claim" and evidence[item]["reproducible"] for item in ids)


def validate_dimensions(
    items: Any,
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    values = require_list(items, "$.dimensions")
    if not values or len(values) > MAX_DIMENSIONS:
        raise ValidationError("$.dimensions", f"must contain between 1 and {MAX_DIMENSIONS} items")
    allowed = {"id", "weight", "score", "verification", "evidence_ids"}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_weight = 0
    for index, raw in enumerate(values):
        path = f"$.dimensions[{index}]"
        item = require_object(raw, path)
        reject_unknown(item, allowed, path)
        require_fields(item, allowed, path)
        dimension_id = require_string(item["id"], f"{path}.id")
        if dimension_id in seen:
            raise ValidationError(f"{path}.id", f"duplicate dimension id {dimension_id!r}")
        seen.add(dimension_id)
        weight = require_int(item["weight"], f"{path}.weight", 1, 100)
        score = require_int(item["score"], f"{path}.score", 0, 100)
        verification = require_string(
            item["verification"], f"{path}.verification", set(VERIFICATION_FACTORS)
        )
        evidence_ids = validate_evidence_ids(item["evidence_ids"], f"{path}.evidence_ids", evidence_by_id)
        if verification == "verified" and not has_reproducible_non_claim(evidence_ids, evidence_by_id):
            raise ValidationError(
                f"{path}.evidence_ids",
                "verified requires reproducible evidence whose kind is not claim",
            )
        if verification == "partial" and not evidence_ids:
            raise ValidationError(f"{path}.evidence_ids", "partial requires at least one evidence id")
        total_weight += weight
        result.append(
            {
                "id": dimension_id,
                "weight": weight,
                "score": score,
                "verification": verification,
                "evidence_ids": evidence_ids,
            }
        )
    if total_weight != 100:
        raise ValidationError("$.dimensions", f"weights must total 100; received {total_weight}")
    return sorted(result, key=lambda item: item["id"])


def validate_coverage(value: Any) -> dict[str, Any]:
    coverage = require_object(value, "$.coverage")
    allowed = {"runtime", "critical_paths"}
    reject_unknown(coverage, allowed, "$.coverage")
    require_fields(coverage, allowed, "$.coverage")
    runtime = require_string(coverage["runtime"], "$.coverage.runtime", RUNTIME_LEVELS)
    critical = require_object(coverage["critical_paths"], "$.coverage.critical_paths")
    reject_unknown(critical, {"total", "tested"}, "$.coverage.critical_paths")
    require_fields(critical, {"total", "tested"}, "$.coverage.critical_paths")
    total = require_int(critical["total"], "$.coverage.critical_paths.total", 0, 10_000)
    tested = require_int(critical["tested"], "$.coverage.critical_paths.tested", 0, 10_000)
    if tested > total:
        raise ValidationError("$.coverage.critical_paths.tested", f"must be <= total ({total}); received {tested}")
    if runtime in {"static", "none"} and tested != 0:
        raise ValidationError("$.coverage.critical_paths.tested", f"must be 0 when runtime is {runtime!r}")
    if runtime in {"partial", "e2e"} and total == 0:
        raise ValidationError("$.coverage.critical_paths.total", f"must be greater than 0 when runtime is {runtime!r}")
    return {"runtime": runtime, "critical_paths": {"total": total, "tested": tested}}


def validate_gates(
    items: Any,
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    values = require_list(items, "$.gates")
    allowed = {"id", "state", "evidence_ids", "retest_evidence_ids"}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        path = f"$.gates[{index}]"
        item = require_object(raw, path)
        reject_unknown(item, allowed, path)
        require_fields(item, allowed, path)
        gate_id = require_string(item["id"], f"{path}.id", set(SAFETY_GATES))
        if gate_id in seen:
            raise ValidationError(f"{path}.id", f"duplicate gate id {gate_id!r}")
        seen.add(gate_id)
        state = require_string(item["state"], f"{path}.state", {"active", "fixed"})
        evidence_ids = validate_evidence_ids(item["evidence_ids"], f"{path}.evidence_ids", evidence_by_id)
        retest_ids = validate_evidence_ids(
            item["retest_evidence_ids"], f"{path}.retest_evidence_ids", evidence_by_id
        )
        if state == "active":
            if not any(evidence_by_id[item_id]["result"] in {"fail", "mixed"} for item_id in evidence_ids):
                raise ValidationError(
                    f"{path}.evidence_ids", "active gate requires fail or mixed evidence"
                )
        else:
            valid_retest = any(
                evidence_by_id[item_id]["kind"] in {"runtime", "test"}
                and evidence_by_id[item_id]["result"] == "pass"
                and evidence_by_id[item_id]["reproducible"]
                for item_id in retest_ids
            )
            if not valid_retest:
                raise ValidationError(
                    f"{path}.retest_evidence_ids",
                    "fixed gate requires reproducible passing runtime or test evidence",
                )
        result.append(
            {
                "id": gate_id,
                "state": state,
                "evidence_ids": evidence_ids,
                "retest_evidence_ids": retest_ids,
            }
        )
    return sorted(result, key=lambda item: item["id"])


def validate_release_checks(
    items: Any,
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    values = require_list(items, "$.release_checks")
    if not values:
        raise ValidationError("$.release_checks", "must contain at least one explicit release check")
    allowed = {"id", "required", "status", "evidence_ids"}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        path = f"$.release_checks[{index}]"
        item = require_object(raw, path)
        reject_unknown(item, allowed, path)
        require_fields(item, allowed, path)
        check_id = require_string(item["id"], f"{path}.id")
        if check_id in seen:
            raise ValidationError(f"{path}.id", f"duplicate release check id {check_id!r}")
        seen.add(check_id)
        required = require_bool(item["required"], f"{path}.required")
        status = require_string(item["status"], f"{path}.status", {"pass", "fail", "unverified"})
        evidence_ids = validate_evidence_ids(item["evidence_ids"], f"{path}.evidence_ids", evidence_by_id)
        if status == "pass" and not has_reproducible_non_claim(evidence_ids, evidence_by_id):
            raise ValidationError(
                f"{path}.evidence_ids",
                "pass requires reproducible evidence whose kind is not claim",
            )
        if status == "fail" and not any(
            evidence_by_id[item_id]["result"] in {"fail", "mixed"} for item_id in evidence_ids
        ):
            raise ValidationError(f"{path}.evidence_ids", "fail requires fail or mixed evidence")
        result.append(
            {"id": check_id, "required": required, "status": status, "evidence_ids": evidence_ids}
        )
    return sorted(result, key=lambda item: item["id"])


def validate_vc_signals(
    value: Any,
    evidence_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    signals = require_object(value, "$.vc_signals")
    expected = set(VC_CAPS)
    reject_unknown(signals, expected, "$.vc_signals")
    require_fields(signals, expected, "$.vc_signals")
    result: dict[str, dict[str, Any]] = {}
    for key in sorted(expected):
        path = f"$.vc_signals.{key}"
        signal = require_object(signals[key], path)
        allowed = {"status", "evidence_ids"}
        reject_unknown(signal, allowed, path)
        require_fields(signal, allowed, path)
        status = require_string(signal["status"], f"{path}.status", {"present", "missing", "unknown"})
        ids = validate_evidence_ids(signal["evidence_ids"], f"{path}.evidence_ids", evidence_by_id)
        if status == "present" and not has_reproducible_non_claim(ids, evidence_by_id):
            raise ValidationError(
                f"{path}.evidence_ids",
                "present requires reproducible evidence whose kind is not claim",
            )
        result[key] = {"status": status, "evidence_ids": ids}
    return result


def validate(payload: Any) -> dict[str, Any]:
    root = require_object(payload, "$")
    required = {
        "schema_version",
        "mode",
        "rubric_id",
        "release_target",
        "dimensions",
        "evidence",
        "coverage",
        "gates",
        "release_checks",
    }
    allowed = required | {"vc_signals"}
    reject_unknown(root, allowed, "$")
    require_fields(root, required, "$")
    schema_version = require_string(root["schema_version"], "$.schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ValidationError("$.schema_version", f"must equal {SCHEMA_VERSION!r}; received {schema_version!r}")
    mode = require_string(root["mode"], "$.mode", MODES)
    rubric_id = require_string(root["rubric_id"], "$.rubric_id")
    release_target = require_string(root["release_target"], "$.release_target", set(RELEASE_THRESHOLDS))
    if mode == "skeptical-vc" and release_target != "venture-case":
        raise ValidationError("$.release_target", "skeptical-vc mode requires 'venture-case'")
    if mode != "skeptical-vc" and release_target == "venture-case":
        raise ValidationError("$.release_target", "'venture-case' requires skeptical-vc mode")
    evidence, evidence_by_id = validate_evidence(root["evidence"])
    dimensions = validate_dimensions(root["dimensions"], evidence_by_id)
    coverage = validate_coverage(root["coverage"])
    gates = validate_gates(root["gates"], evidence_by_id)
    release_checks = validate_release_checks(root["release_checks"], evidence_by_id)
    if mode == "skeptical-vc":
        if "vc_signals" not in root:
            raise ValidationError("$", "skeptical-vc mode requires vc_signals")
        vc_signals = validate_vc_signals(root["vc_signals"], evidence_by_id)
    else:
        if "vc_signals" in root:
            raise ValidationError("$.vc_signals", "is allowed only in skeptical-vc mode")
        vc_signals = None
    return {
        "schema_version": schema_version,
        "mode": mode,
        "rubric_id": rubric_id,
        "release_target": release_target,
        "dimensions": dimensions,
        "evidence": evidence,
        "coverage": coverage,
        "gates": gates,
        "release_checks": release_checks,
        "vc_signals": vc_signals,
    }


def quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def as_json_number(value: Decimal) -> int | float:
    value = quantize(value)
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def confidence_for(evidence_percent: Decimal, critical_percent: Decimal, runtime: str) -> str:
    if evidence_percent >= 85 and critical_percent >= 80:
        base = "A"
    elif evidence_percent >= 65 and critical_percent >= 50:
        base = "B"
    elif evidence_percent >= 40:
        base = "C"
    else:
        base = "D"
    runtime_cap = RUNTIME_CONFIDENCE_CAP[runtime]
    return base if CONFIDENCE_ORDER[base] >= CONFIDENCE_ORDER[runtime_cap] else runtime_cap


def compute(data: dict[str, Any]) -> dict[str, Any]:
    dimensions_output: list[dict[str, Any]] = []
    raw_score = Decimal("0")
    evidence_percent = Decimal("0")
    for dimension in data["dimensions"]:
        score = Decimal(dimension["score"])
        weight = Decimal(dimension["weight"])
        contribution = score * weight / Decimal("100")
        raw_score += contribution
        evidence_percent += weight * VERIFICATION_FACTORS[dimension["verification"]]
        dimensions_output.append(
            {
                "contribution": as_json_number(contribution),
                "id": dimension["id"],
                "score": dimension["score"],
                "verification": dimension["verification"],
                "weight": dimension["weight"],
            }
        )

    critical = data["coverage"]["critical_paths"]
    critical_percent = (
        Decimal(critical["tested"]) * Decimal("100") / Decimal(critical["total"])
        if critical["total"]
        else Decimal("0")
    )
    confidence = confidence_for(evidence_percent, critical_percent, data["coverage"]["runtime"])
    applied_caps: list[dict[str, Any]] = [
        {"id": f"confidence-{confidence.lower()}", "source": "evidence-confidence", "value": as_json_number(CONFIDENCE_SCORE_CAP[confidence])}
    ]
    active_gates: list[dict[str, Any]] = []
    for gate in data["gates"]:
        if gate["state"] == "active":
            cap = SAFETY_GATES[gate["id"]]
            active_gates.append({"cap": as_json_number(cap), "id": gate["id"]})
            applied_caps.append({"id": gate["id"], "source": "safety-gate", "value": as_json_number(cap)})

    if data["vc_signals"] is not None:
        for signal_id, signal in data["vc_signals"].items():
            if signal["status"] != "present":
                cap = VC_CAPS[signal_id]
                applied_caps.append(
                    {"id": f"vc-{signal_id}", "source": "venture-evidence", "value": as_json_number(cap)}
                )

    readiness_score = min([raw_score] + [Decimal(str(item["value"])) for item in applied_caps])
    threshold = RELEASE_THRESHOLDS[data["release_target"]]
    required_failed = [
        item["id"] for item in data["release_checks"] if item["required"] and item["status"] == "fail"
    ]
    required_unverified = [
        item["id"]
        for item in data["release_checks"]
        if item["required"] and item["status"] == "unverified"
    ]
    optional_gaps = [
        item["id"]
        for item in data["release_checks"]
        if not item["required"] and item["status"] != "pass"
    ]
    runtime_insufficient = data["mode"] != "skeptical-vc" and data["coverage"]["runtime"] in {
        "static",
        "none",
    }

    if active_gates:
        decision = "BLOCKED"
    elif required_failed:
        decision = "NOT_READY"
    elif required_unverified or runtime_insufficient:
        decision = "INSUFFICIENT_EVIDENCE"
    elif readiness_score < threshold:
        decision = "NOT_READY"
    elif optional_gaps:
        decision = "READY_WITH_CONDITIONS"
    else:
        decision = "READY"

    fingerprint_payload = {
        "dimensions": [{"id": item["id"], "weight": item["weight"]} for item in data["dimensions"]],
        "mode": data["mode"],
        "release_target": data["release_target"],
        "rubric_id": data["rubric_id"],
    }
    fingerprint_bytes = json.dumps(
        fingerprint_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    fingerprint = "sha256:" + hashlib.sha256(fingerprint_bytes).hexdigest()

    return {
        "active_gates": active_gates,
        "applied_caps": sorted(applied_caps, key=lambda item: (item["value"], item["id"])),
        "coverage": {
            "confidence": confidence,
            "critical_paths_percent": as_json_number(critical_percent),
            "evidence_percent": as_json_number(evidence_percent),
            "runtime": data["coverage"]["runtime"],
        },
        "decision": decision,
        "dimensions": dimensions_output,
        "mode": data["mode"],
        "ok": True,
        "policy_version": POLICY_VERSION,
        "release_checks": {
            "failed_required": required_failed,
            "optional_gaps": optional_gaps,
            "unverified_required": required_unverified,
        },
        "release_target": data["release_target"],
        "release_threshold": as_json_number(threshold),
        "rubric_fingerprint": fingerprint,
        "rubric_id": data["rubric_id"],
        "schema_version": SCHEMA_VERSION,
        "scores": {
            "raw_product": as_json_number(raw_score),
            "readiness": as_json_number(readiness_score),
        },
        "vetoed": bool(active_gates),
    }


def render(result: dict[str, Any], pretty: bool) -> str:
    if pretty:
        return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    return json.dumps(
        result,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="pretty-print deterministic JSON")
    parser.add_argument("input", type=Path, help="path to a scorecard JSON file")
    args = parser.parse_args(argv)
    try:
        result = compute(validate(load_payload(args.input)))
    except ValidationError as exc:
        emit_error("validation_error", exc.path, exc.message)
        return 1
    sys.stdout.write(render(result, args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
