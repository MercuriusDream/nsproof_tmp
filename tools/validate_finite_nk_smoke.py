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

from validators.interval_backend import (  # noqa: E402
    Interval,
    interval_matrix_inf_norm,
    interval_matvec,
    interval_sub,
    interval_vector_inf_norm,
)
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


def point_interval(value: float) -> Interval:
    return Interval(float(value), float(value))


def interval_repr(value: Interval) -> list[float]:
    return [value.lo, value.hi]


def interval_vector_repr(values: list[Interval]) -> list[list[float]]:
    return [interval_repr(value) for value in values]


def interval_matrix_repr(values: list[list[Interval]]) -> list[list[list[float]]]:
    return [interval_vector_repr(row) for row in values]


def point_interval_matrix(values: list[list[float]]) -> list[list[Interval]]:
    return [[point_interval(value) for value in row] for row in values]


def point_interval_vector(values: list[float]) -> list[Interval]:
    return [point_interval(value) for value in values]


def interval_matmul(lhs: list[list[Interval]], rhs: list[list[Interval]]) -> list[list[Interval]]:
    if not rhs:
        raise ValueError("right matrix must not be empty")
    width = len(rhs[0])
    if any(len(row) != width for row in rhs):
        raise ValueError("right matrix rows must have stable width")
    columns = [[rhs[row][column] for row in range(len(rhs))] for column in range(width)]
    column_products = [interval_matvec(lhs, column) for column in columns]
    return [
        [column_products[column][row] for column in range(width)]
        for row in range(len(lhs))
    ]


def interval_identity_minus(matrix: list[list[Interval]]) -> list[list[Interval]]:
    out: list[list[Interval]] = []
    for row_index, row in enumerate(matrix):
        out_row = []
        for column_index, value in enumerate(row):
            identity = point_interval(1.0 if row_index == column_index else 0.0)
            out_row.append(interval_sub([identity], [value])[0])
        out.append(out_row)
    return out


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
    residual_interval = point_interval_vector(residual)
    jacobian_interval = point_interval_matrix(jacobian)
    approximate_inverse_interval = point_interval_matrix(approximate_inverse)
    product_interval = interval_matmul(approximate_inverse_interval, jacobian_interval)
    defect_interval = interval_identity_minus(product_interval)
    correction_interval = interval_matvec(approximate_inverse_interval, residual_interval)
    Y0 = interval_vector_inf_norm(correction_interval)
    Z0 = interval_matrix_inf_norm(defect_interval)
    return {
        "dimension": 2,
        "residual_vector_r": residual,
        "jacobian_J": jacobian,
        "approximate_inverse_A": approximate_inverse,
        "native_interval_inputs": {
            "residual_vector_r": interval_vector_repr(residual_interval),
            "jacobian_J": interval_matrix_repr(jacobian_interval),
            "approximate_inverse_A": interval_matrix_repr(approximate_inverse_interval),
        },
        "native_interval_products": {
            "A_times_J": interval_matrix_repr(product_interval),
            "defect_matrix_B_equals_I_minus_AJ": interval_matrix_repr(defect_interval),
            "A_times_r": interval_vector_repr(correction_interval),
        },
        "Y0_infinity_norm_A_r": Y0,
        "Z0_infinity_norm_B": Z0,
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
            "native/c/nsproof_kernel.c": sha256_file(resolve("native/c/nsproof_kernel.c")),
        },
        "dependency_hashes": {
            RADIUS_HELPER: helper_hash,
            SCRIPT_PATH: script_hash,
            "validators/interval_backend.py": sha256_file(resolve("validators/interval_backend.py")),
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
