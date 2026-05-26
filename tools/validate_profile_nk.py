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

    blockers = list(exact_audit.get("blockers", []))
    blockers.extend(
        [
            "interval residual evaluator is not implemented",
            "validated approximate inverse hash is missing",
            (
                "profile finite residual/Jacobian/inverse export is missing; "
                "native finite-block Y0/Z0 backend is available but has no "
                "profile block to certify"
            ),
            "Z2/tail-complement interval bound is not available for this profile",
        ]
    )
    toy_radii = manufactured_zero_self_test()
    finite_backend = finite_nk_backend_report()
    cert = {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "profile_nk",
        "pass": False,
        "repo_commit": repo_commit(),
        "profile": exact_audit["profile"],
        "profile_hash_sha256": exact_audit["profile_hash_sha256"],
        "input_hashes": exact_audit["input_hashes"],
        "dependency_hashes": {
            "exact_residual_audit": stable_json_hash(exact_audit),
            "basis": exact_audit["basis_hash_sha256"],
            "tail_policy": exact_audit["tail_policy_hash_sha256"],
            "finite_nk_bounds": finite_backend["input_hashes"][FINITE_NK_BACKEND],
            "interval_backend": finite_backend["input_hashes"][INTERVAL_BACKEND],
            "native_interval_kernel": finite_backend["input_hashes"][NATIVE_INTERVAL_KERNEL],
        },
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
