#!/usr/bin/env python3
"""Emit the profile Newton-Kantorovich certificate ledger.

This is the first proof-path command for the profile gate.  For the current
candidate it must fail honestly: we do not have outward-rounded interval
bounds, a validated approximate inverse, or small enough residual/mortar
defects.  The output is still useful because it gives the final certificate
schema, hashes the residual map, and records the exact blockers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.exact_profile_residual import (  # noqa: E402
    SCHEMA_VERSION,
    build_exact_residual_audit,
    repo_commit,
    save_json,
    sha256_file,
    stable_json_hash,
)
from validators.radii_polynomial import manufactured_zero_self_test  # noqa: E402


FINITE_NK_BACKEND = "validators/finite_nk_bounds.py"
INTERVAL_BACKEND = "validators/interval_backend.py"
NATIVE_INTERVAL_KERNEL = "native/c/nsproof_kernel.c"


def rel_hash(path: str) -> str:
    return sha256_file(os.path.join(ROOT_DIR, path))


def finite_nk_backend_report() -> dict[str, Any]:
    return {
        "status": "available_for_finite_blocks",
        "backend": "native-c-outward-rounded-double-interval",
        "scope": (
            "Computes finite-dimensional Y0=||A r||_inf and "
            "Z0=||I-AJ||_inf once a profile residual vector, Jacobian block, "
            "and approximate inverse are exported as interval data."
        ),
        "profile_block_status": "not_available_for_current_profile",
        "input_hashes": {
            FINITE_NK_BACKEND: rel_hash(FINITE_NK_BACKEND),
            INTERVAL_BACKEND: rel_hash(INTERVAL_BACKEND),
            NATIVE_INTERVAL_KERNEL: rel_hash(NATIVE_INTERVAL_KERNEL),
        },
    }


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def load_optional_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    full = resolve(path)
    if not os.path.exists(full):
        raise FileNotFoundError(f"finite block report not found: {path}")
    with open(full, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"finite block report must be a JSON object: {path}")
    data = dict(data)
    data["_path"] = path
    data["_sha256"] = sha256_file(full)
    return data


def finite_block_blockers(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return [
            (
                "profile finite residual/Jacobian/inverse export is missing; "
                "native finite-block Y0/Z0 backend is available but has no "
                "profile block to certify"
            )
        ]
    blockers = [f"finite-block report is diagnostic-only: {report.get('status')}"]
    bounds = report.get("finite_nk_bounds", {})
    z0 = bounds.get("Z0_infinity_norm_B")
    if z0 is None:
        blockers.append("finite-block report does not contain Z0")
    elif float(z0) >= 1.0:
        blockers.append(f"finite-block sampled Z0={float(z0):.12e} is >= 1")
    if not report.get("pass", False):
        blockers.extend(str(item) for item in report.get("blockers", []))
    return blockers


def finite_sweep_blockers(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return []
    blockers = [f"finite-block sweep is diagnostic-only: {report.get('status')}"]
    best = report.get("best_overall") or {}
    z0 = best.get("Z0_infinity_norm_B")
    if z0 is None:
        blockers.append("finite-block sweep does not contain a best Z0")
    elif float(z0) >= 1.0:
        blockers.append(f"best sampled finite-block sweep Z0={float(z0):.12e} is >= 1")
    if not report.get("pass", False):
        blockers.extend(str(item) for item in report.get("blockers", []))
    return blockers


def build_profile_nk_certificate(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    exact_audit = build_exact_residual_audit(
        profile=args.profile,
        residual_kind=args.residual_kind,
        scans=args.scan,
        h=args.h,
        mortar_order=args.mortar_order,
        mortar_q_samples=args.mortar_q_samples,
        mortar_x_samples=args.mortar_x_samples,
        overlap_q_min=args.overlap_q_min,
        overlap_q_max=args.overlap_q_max,
        residual_threshold=args.residual_threshold,
        mortar_threshold=args.mortar_threshold,
        use_native_c=args.native_c,
    )
    exact_audit["commands"] = [" ".join(sys.argv)]

    finite_block_report = load_optional_json(args.finite_block_report)
    finite_sweep_report = load_optional_json(args.finite_sweep_report)
    blockers = list(exact_audit.get("blockers", []))
    blockers.extend(
        [
            "interval residual evaluator is not implemented",
            "validated approximate inverse hash is missing",
            "Z2/tail-complement interval bound is not available for this profile",
        ]
    )
    blockers.extend(finite_block_blockers(finite_block_report))
    blockers.extend(finite_sweep_blockers(finite_sweep_report))
    toy_radii = manufactured_zero_self_test()
    finite_backend = finite_nk_backend_report()
    if finite_block_report is not None or finite_sweep_report is not None:
        finite_backend["profile_block_status"] = "floating_profile_block_attached_not_certified"
    dependency_hashes = {
        "exact_residual_audit": stable_json_hash(exact_audit),
        "basis": exact_audit["basis_hash_sha256"],
        "tail_policy": exact_audit["tail_policy_hash_sha256"],
        "finite_nk_bounds": finite_backend["input_hashes"][FINITE_NK_BACKEND],
        "interval_backend": finite_backend["input_hashes"][INTERVAL_BACKEND],
        "native_interval_kernel": finite_backend["input_hashes"][NATIVE_INTERVAL_KERNEL],
    }
    if finite_block_report is not None:
        dependency_hashes["sampled_finite_block_report"] = finite_block_report["_sha256"]
    if finite_sweep_report is not None:
        dependency_hashes["sampled_finite_block_sweep"] = finite_sweep_report["_sha256"]
    cert = {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "profile_nk",
        "pass": False,
        "repo_commit": repo_commit(),
        "profile": exact_audit["profile"],
        "profile_hash_sha256": exact_audit["profile_hash_sha256"],
        "input_hashes": exact_audit["input_hashes"],
        "dependency_hashes": dependency_hashes,
        "basis_hash_sha256": exact_audit["basis_hash_sha256"],
        "residual_map_hash_sha256": exact_audit["residual_map_hash_sha256"],
        "tail_policy_hash_sha256": exact_audit["tail_policy_hash_sha256"],
        "gamma_interval": [str(exact_audit["parameters"]["gamma"]), str(exact_audit["parameters"]["gamma"])],
        "B_interval": [str(exact_audit["parameters"]["B"]), str(exact_audit["parameters"]["B"])],
        "backend": "floating-audit+native-finite-block-nk-pending-profile-data",
        "precision_bits": None,
        "rounding_mode": None,
        "mathematical_statement": (
            "There exists a zero of the pressure-eliminated two-chart profile "
            "residual map inside a Newton-Kantorovich ball around the supplied profile."
        ),
        "exact_residual_audit": exact_audit,
        "Y0_interval": None,
        "Z0_interval": None,
        "Z2_interval": None,
        "finite_nk_backend": finite_backend,
        "sampled_finite_block_report": None
        if finite_block_report is None
        else {
            "path": finite_block_report["_path"],
            "sha256": finite_block_report["_sha256"],
            "status": finite_block_report.get("status"),
            "pass": bool(finite_block_report.get("pass", False)),
            "diagnostic_vs_proof": finite_block_report.get("diagnostic_vs_proof"),
            "row_selection": finite_block_report.get("row_selection"),
            "floating_norms": finite_block_report.get("floating_norms"),
            "approximate_inverse": finite_block_report.get("approximate_inverse"),
            "finite_nk_bounds": finite_block_report.get("finite_nk_bounds"),
        },
        "sampled_finite_block_sweep": None
        if finite_sweep_report is None
        else {
            "path": finite_sweep_report["_path"],
            "sha256": finite_sweep_report["_sha256"],
            "status": finite_sweep_report.get("status"),
            "pass": bool(finite_sweep_report.get("pass", False)),
            "diagnostic_vs_proof": finite_sweep_report.get("diagnostic_vs_proof"),
            "trial_count": finite_sweep_report.get("trial_count"),
            "failure_count": finite_sweep_report.get("failure_count"),
            "best_overall": finite_sweep_report.get("best_overall"),
            "best_by_cache": finite_sweep_report.get("best_by_cache"),
        },
        "radius_interval": None,
        "radii_polynomial_interval": None,
        "radii_polynomial_helper_self_test": toy_radii,
        "patch_mortar_order": args.mortar_order,
        "tail_inverse_bound": None,
        "commands": [" ".join(sys.argv)],
        "failure_reason": "; ".join(blockers),
        "blockers": blockers,
        "interval_widths": {
            "max": None,
            "median": None,
        },
    }
    return cert, exact_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--out", default="certs/profile/profile_nk.json")
    parser.add_argument("--exact-residual-out", default="certs/profile/exact_residual_twochart_audit.json")
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--scan", default="standard,focused,secondary,origin,edge,overlap")
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--mortar-order", type=int, default=4)
    parser.add_argument("--mortar-q-samples", type=int, default=9)
    parser.add_argument("--mortar-x-samples", type=int, default=9)
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--residual-threshold", type=float, default=1e-8)
    parser.add_argument("--mortar-threshold", type=float, default=1e-8)
    parser.add_argument("--native-c", action="store_true")
    parser.add_argument("--finite-block-report")
    parser.add_argument("--finite-sweep-report")
    args = parser.parse_args()

    cert, exact_audit = build_profile_nk_certificate(args)
    save_json(args.exact_residual_out, exact_audit)
    save_json(args.out, cert)
    print(f"profile={cert['profile']}")
    print(f"pass={cert['pass']}")
    print(f"residual_max={exact_audit['residual_blocks']['max_abs']:.12e}")
    print(f"mortar_max={exact_audit['mortar']['summary']['max_abs']:.12e}")
    print(f"profile_nk_saved={args.out}")
    print(f"exact_residual_saved={args.exact_residual_out}")
    print(f"failure_reason={cert['failure_reason']}")


if __name__ == "__main__":
    main()
