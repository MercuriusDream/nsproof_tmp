#!/usr/bin/env python3
"""Build the final theorem certificate manifest.

The manifest is deliberately binary at the gate level: every stop-condition
gate must be backed by existing certificate JSON files with ``pass=true``.
Floating diagnostics, native speedups, and scaffold reports are recorded only
as failing or missing dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.exact_profile_residual import SCHEMA_VERSION, save_json, sha256_file  # noqa: E402


GATES: tuple[dict[str, Any], ...] = (
    {
        "gate_id": "exact_profile_equation",
        "statement": "Exact profile equation F_gamma(U_*,P_*) = 0",
        "dependencies": [
            "certs/profile/profile_nk.json",
            "certs/profile/pressure_reconstruction.json",
        ],
    },
    {
        "gate_id": "validated_exponent",
        "statement": "Validated exponent 2/5 < gamma < 1/2 linked to an admissible profile",
        "dependencies": [
            "certs/profile/exponent_admissibility.json",
            "certs/profile/profile_nk.json",
            "certs/tail/tail_recurrence.json",
        ],
    },
    {
        "gate_id": "natural_tail_indicial",
        "statement": "Natural tail, exact transseries, and indicial certification",
        "dependencies": [
            "certs/tail/tail_recurrence.json",
            "certs/tail/indicial_pluecker_cover.json",
            "certs/profile/matching_determinant.json",
        ],
    },
    {
        "gate_id": "finite_unstable_projection",
        "statement": "Finite unstable projection rank P_+ < infinity",
        "dependencies": [
            "certs/spectrum/projected_spectrum.json",
        ],
    },
    {
        "gate_id": "stable_complement_gap",
        "statement": "Stable-complement spectral gap sigma(L_s) subset {Re z <= -c < 0}",
        "dependencies": [
            "certs/spectrum/high_frequency_exclusion.json",
            "certs/spectrum/stable_semigroup.json",
        ],
    },
)

INFRASTRUCTURE_CERTIFICATES: tuple[str, ...] = (
    "certs/infrastructure/interval_backend_smoke.json",
    "certs/infrastructure/bernstein_backend_smoke.json",
    "certs/infrastructure/manufactured_nk.json",
    "certs/infrastructure/finite_nk_smoke.json",
    "certs/profile/interval_residual_rows.json",
)


def repo_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return out.strip()


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def load_certificate(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def dependency_status(path: str) -> dict[str, Any]:
    full = resolve(path)
    if not os.path.exists(full):
        return {
            "path": path,
            "exists": False,
            "pass": False,
            "sha256": None,
            "certificate_name": None,
            "failure_reason": "missing certificate file",
        }
    try:
        data = load_certificate(full)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "path": path,
            "exists": True,
            "pass": False,
            "sha256": sha256_file(full),
            "certificate_name": None,
            "failure_reason": f"could not parse certificate: {exc}",
        }
    return {
        "path": path,
        "exists": True,
        "pass": bool(data.get("pass", False)),
        "sha256": sha256_file(full),
        "schema_version": data.get("schema_version"),
        "certificate_name": data.get("certificate_name"),
        "profile_hash_sha256": data.get("profile_hash_sha256"),
        "failure_reason": data.get("failure_reason"),
    }


def profile_hashes(dependencies: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(item["profile_hash_sha256"])
            for item in dependencies
            if item.get("profile_hash_sha256")
        }
    )


def profile_hash_consistency(dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = profile_hashes(dependencies)
    return {
        "pass": len(hashes) <= 1,
        "hashes": hashes,
    }


def short_failure_reason(item: dict[str, Any], fallback: str) -> str:
    reason = item.get("failure_reason") or fallback
    if not isinstance(reason, str):
        reason = str(reason)
    first_clause = reason.split("; ", 1)[0].strip()
    if len(first_clause) <= 180:
        return first_clause
    return first_clause[:177].rstrip() + "..."


def blocking_certificates(
    gate_reports: list[dict[str, Any]],
    global_hash_consistent: bool,
) -> list[dict[str, Any]]:
    blockers: dict[str, dict[str, Any]] = {}

    def add(item: dict[str, Any], gate_id: str, reason: str) -> None:
        path = str(item["path"])
        blocker = blockers.setdefault(
            path,
            {
                "path": path,
                "certificate_name": item.get("certificate_name"),
                "pass": bool(item.get("pass", False)),
                "failure_reason": reason,
                "gate_ids": [],
            },
        )
        if gate_id not in blocker["gate_ids"]:
            blocker["gate_ids"].append(gate_id)
        if not blocker["failure_reason"]:
            blocker["failure_reason"] = reason

    for gate in gate_reports:
        gate_id = str(gate["gate_id"])
        for item in gate["dependencies"]:
            if not item.get("exists"):
                add(item, gate_id, "missing certificate file")
            elif not item.get("pass"):
                add(item, gate_id, short_failure_reason(item, "certificate pass=false"))
            elif (
                not gate["profile_hash_consistency"]["pass"]
                and item.get("profile_hash_sha256")
            ):
                add(item, gate_id, f"profile hash mismatch within gate {gate_id}")

    if not global_hash_consistent:
        for gate in gate_reports:
            gate_id = str(gate["gate_id"])
            for item in gate["dependencies"]:
                if item.get("profile_hash_sha256"):
                    add(item, gate_id, "profile hash mismatch across theorem dependencies")

    return [blockers[path] for path in sorted(blockers)]


def build_manifest() -> dict[str, Any]:
    gate_reports = []
    passed = 0
    for gate in GATES:
        dependencies = [dependency_status(path) for path in gate["dependencies"]]
        gate_profile_hash_consistency = profile_hash_consistency(dependencies)
        gate_pass = (
            all(item["exists"] and item["pass"] for item in dependencies)
            and gate_profile_hash_consistency["pass"]
        )
        if gate_pass:
            passed += 1
        failure_reason = None
        if not gate_pass:
            reasons = []
            if not all(item["exists"] and item["pass"] for item in dependencies):
                reasons.append("one or more required interval/exact certificates are missing or failing")
            if not gate_profile_hash_consistency["pass"]:
                reasons.append("gate dependencies refer to different profile hashes")
            failure_reason = "; ".join(reasons)
        gate_reports.append(
            {
                "gate_id": gate["gate_id"],
                "statement": gate["statement"],
                "pass": gate_pass,
                "dependencies": dependencies,
                "profile_hash_consistency": gate_profile_hash_consistency,
                "failure_reason": failure_reason,
            }
        )

    total = len(GATES)
    global_dependencies_by_path = {
        item["path"]: item
        for gate in gate_reports
        for item in gate["dependencies"]
    }
    global_profile_hash_consistency = profile_hash_consistency(
        list(global_dependencies_by_path.values())
    )
    all_gates_pass = passed == total
    manifest_pass = all_gates_pass and global_profile_hash_consistency["pass"]
    failure_reasons = []
    if not all_gates_pass:
        failure_reasons.append(f"{passed}/{total} stop-condition gates are certified")
    if not global_profile_hash_consistency["pass"]:
        failure_reasons.append("theorem dependencies refer to different profile hashes")
    infrastructure = [dependency_status(path) for path in INFRASTRUCTURE_CERTIFICATES]
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "final_theorem_manifest",
        "pass": manifest_pass,
        "repo_commit": repo_commit(),
        "certified_stop_condition_gates": {
            "passed": passed,
            "total": total,
        },
        "final_theorem_certificate_percent": 100.0 * passed / max(total, 1),
        "profile_hash_consistency": global_profile_hash_consistency,
        "blocking_certificates": blocking_certificates(
            gate_reports,
            bool(global_profile_hash_consistency["pass"]),
        ),
        "gates": gate_reports,
        "infrastructure_certificates": {
            "note": (
                "These are proof-engineering smoke certificates. They are useful "
                "for backend readiness but do not count toward theorem gate pass/fail."
            ),
            "passed": sum(1 for item in infrastructure if item["exists"] and item["pass"]),
            "total": len(infrastructure),
            "items": infrastructure,
        },
        "mathematical_statement": (
            "All stop-condition gates for the final theorem are hash-linked to "
            "passing interval/exact certificates."
        ),
        "failure_reason": None if manifest_pass else "; ".join(failure_reasons),
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="certs/final_theorem_manifest.json")
    args = parser.parse_args()
    manifest = build_manifest()
    save_json(args.out, manifest)
    passed = manifest["certified_stop_condition_gates"]["passed"]
    total = manifest["certified_stop_condition_gates"]["total"]
    print(f"pass={manifest['pass']}")
    print(f"certified_stop_condition_gates={passed}/{total}")
    print(f"final_theorem_certificate_percent={manifest['final_theorem_certificate_percent']:.1f}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
