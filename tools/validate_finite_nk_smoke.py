#!/usr/bin/env python3
"""Emit a finite-dimensional manufactured NK smoke certificate.

This is an infrastructure-only positive control for the finite-dimensional
Newton-Kantorovich ledger path.  It uses explicit 2D point-interval data,
computes the finite block bounds through the native C interval linear algebra
backend, and delegates only the scalar radii-polynomial gate to
``validators.radii_polynomial``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.finite_nk_bounds import finite_nk_bounds  # noqa: E402
from validators.radii_polynomial import validate_radii_polynomial  # noqa: E402


SCHEMA_VERSION = "nsproof-cert-v1"
CERTIFICATE_NAME = "finite_nk_smoke"
RADIUS_HELPER = "validators/radii_polynomial.py"
SCRIPT_PATH = "tools/validate_finite_nk_smoke.py"
DEFAULT_OUT = "certs/infrastructure/finite_nk_smoke.json"


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


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path: str, data: dict[str, Any]) -> None:
    full = resolve(path)
    out_dir = os.path.dirname(full)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def manufactured_problem() -> dict[str, Any]:
    residual = [1.0e-4, -8.0e-5]
    jacobian = [
        [2.0, 0.5],
        [0.25, 1.5],
    ]
    approximate_inverse = [
        [0.52, -0.17],
        [-0.09, 0.70],
    ]
    finite_bounds = finite_nk_bounds(residual, jacobian, approximate_inverse)
    return {
        "dimension": 2,
        "residual_vector_r": residual,
        "jacobian_J": jacobian,
        "approximate_inverse_A": approximate_inverse,
        "native_interval_products": finite_bounds,
        "Y0_infinity_norm_A_r": finite_bounds["Y0_infinity_norm_A_r"],
        "Z0_infinity_norm_B": finite_bounds["Z0_infinity_norm_B"],
        "Z2": 0.05,
        "radius_interval": [0.001, 0.01],
    }


def build_certificate(command: str) -> dict[str, Any]:
    problem = manufactured_problem()
    gate = validate_radii_polynomial(
        Y0=problem["Y0_infinity_norm_A_r"],
        Z0=problem["Z0_infinity_norm_B"],
        Z2=problem["Z2"],
        radius_lower=problem["radius_interval"][0],
        radius_upper=problem["radius_interval"][1],
    )
    helper_hash = sha256_file(resolve(RADIUS_HELPER))
    script_hash = sha256_file(resolve(SCRIPT_PATH))
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "pass": bool(gate["pass"]),
        "repo_commit": repo_commit(),
        "backend": "native-c-interval-linalg+decimal-scalar-radii-polynomial",
        "finite_block_backend": "native-c-outward-rounded-double-interval",
        "radii_polynomial_backend": gate["backend"],
        "precision_digits": gate["precision_digits"],
        "mathematical_statement": (
            "For the explicit 2D manufactured Newton problem with residual r, "
            "approximate inverse A, defect B=I-AJ, C-backed interval bounds "
            "Y0>=||A r||_inf and Z0>=||B||_inf, and Z2=0.05, the scalar "
            "radii polynomial p(rho)=Y0-(1-Z0)rho+Z2*rho^2 is strictly "
            "negative on the certified radius interval."
        ),
        "scope": "infrastructure-only finite-dimensional manufactured NK smoke",
        "note": (
            "Infrastructure-only positive control; this is not a final theorem "
            "manifest dependency."
        ),
        "final_theorem_manifest_dependency": False,
        "input_hashes": {
            RADIUS_HELPER: helper_hash,
            SCRIPT_PATH: script_hash,
            "validators/interval_backend.py": sha256_file(resolve("validators/interval_backend.py")),
            "validators/finite_nk_bounds.py": sha256_file(resolve("validators/finite_nk_bounds.py")),
            "native/c/nsproof_kernel.c": sha256_file(resolve("native/c/nsproof_kernel.c")),
        },
        "dependency_hashes": {
            RADIUS_HELPER: helper_hash,
            SCRIPT_PATH: script_hash,
            "validators/interval_backend.py": sha256_file(resolve("validators/interval_backend.py")),
            "validators/finite_nk_bounds.py": sha256_file(resolve("validators/finite_nk_bounds.py")),
            "native/c/nsproof_kernel.c": sha256_file(resolve("native/c/nsproof_kernel.c")),
        },
        "manufactured_finite_nk": problem,
        "radii_polynomial_validation": gate,
        "commands": [command],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    command = " ".join(sys.argv)
    cert = build_certificate(command)
    save_json(args.out, cert)
    print(f"certificate_name={cert['certificate_name']}")
    print(f"pass={cert['pass']}")
    print(f"Y0={cert['manufactured_finite_nk']['Y0_infinity_norm_A_r']:.17g}")
    print(f"Z0={cert['manufactured_finite_nk']['Z0_infinity_norm_B']:.17g}")
    print(
        "radii_polynomial_interval="
        f"{cert['radii_polynomial_validation']['radii_polynomial_interval']}"
    )
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
