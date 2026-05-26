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


def build_manifest() -> dict[str, Any]:
    gate_reports = []
    passed = 0
    for gate in GATES:
        dependencies = [dependency_status(path) for path in gate["dependencies"]]
        gate_pass = all(item["exists"] and item["pass"] for item in dependencies)
        if gate_pass:
            passed += 1
        gate_reports.append(
            {
                "gate_id": gate["gate_id"],
                "statement": gate["statement"],
                "pass": gate_pass,
                "dependencies": dependencies,
                "failure_reason": None
                if gate_pass
                else "one or more required interval/exact certificates are missing or failing",
            }
        )

    total = len(GATES)
    infrastructure = [dependency_status(path) for path in INFRASTRUCTURE_CERTIFICATES]
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "final_theorem_manifest",
        "pass": passed == total,
        "repo_commit": repo_commit(),
        "certified_stop_condition_gates": {
            "passed": passed,
            "total": total,
        },
        "final_theorem_certificate_percent": 100.0 * passed / max(total, 1),
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
        "failure_reason": None
        if passed == total
        else f"{passed}/{total} stop-condition gates are certified",
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
