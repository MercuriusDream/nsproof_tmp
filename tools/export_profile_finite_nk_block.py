#!/usr/bin/env python3
"""Export a sampled profile finite NK block from a two-chart row cache.

This is a bridge between Stage-0 discovery row caches and the profile NK
certificate path.  It reads a floating row cache containing sampled residuals
and sparse Jacobian rows, builds a dense finite block, constructs a ridge-SVD
approximate inverse, and evaluates the finite-block NK quantities through the
native C interval linalg backend.

The output is diagnostic only because the row cache itself is floating and the
infinite tail/complement bound is absent.  It is still useful: it proves that
the real profile-shaped block can be fed into the C-backed ``Y0/Z0`` machinery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any

import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.finite_nk_bounds import finite_nk_bounds  # noqa: E402


SCHEMA_VERSION = "nsproof-cert-v1"
STATUS = "PROFILE_FINITE_NK_BLOCK_FLOATING_NOT_PROOF"


def repo_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def relpath(path: str) -> str:
    return os.path.relpath(path, ROOT_DIR) if os.path.isabs(path) else path


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    arr = np.ascontiguousarray(values, dtype="<f8")
    return hashlib.sha256(arr.tobytes()).hexdigest()


def save_json(path: str, data: dict[str, Any]) -> None:
    full = resolve(path)
    out_dir = os.path.dirname(full)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def load_row_cache(path: str) -> dict[str, Any]:
    with open(resolve(path), "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("row cache must be a JSON object")
    if "rows" not in data or "column_count" not in data:
        raise ValueError("row cache missing rows/column_count")
    return data


def selected_rows(row_cache: dict[str, Any], labels: set[str] | None) -> list[dict[str, Any]]:
    rows = row_cache.get("rows", [])
    if labels is None:
        return rows
    return [row for row in rows if str(row.get("label")) in labels or str(row.get("row_type")) in labels]


def dense_block(rows: list[dict[str, Any]], column_count: int) -> tuple[np.ndarray, np.ndarray]:
    residual = np.zeros(len(rows), dtype=np.float64)
    jacobian = np.zeros((len(rows), column_count), dtype=np.float64)
    for row_index, row in enumerate(rows):
        residual[row_index] = float(row.get("residual_after_scaling", row.get("residual_raw", 0.0)))
        for column, value in row.get("jacobian_sparse_after_scaling", []):
            col = int(column)
            if col < 0 or col >= column_count:
                raise ValueError(f"row {row_index} has out-of-range column {col}")
            jacobian[row_index, col] = float(value)
    return residual, jacobian


def ridge_svd_inverse(jacobian: np.ndarray, ridge_relative: float, svd_rcond: float) -> tuple[np.ndarray, dict[str, Any]]:
    if ridge_relative < 0:
        raise ValueError("ridge_relative must be nonnegative")
    if svd_rcond < 0:
        raise ValueError("svd_rcond must be nonnegative")
    u, s, vt = np.linalg.svd(jacobian, full_matrices=False)
    if s.size == 0:
        raise ValueError("empty singular spectrum")
    cutoff = svd_rcond * float(s[0])
    s0 = float(s[0])
    ridge_abs = ridge_relative * s0 * s0
    keep = s > cutoff
    scaled_s = s / s0
    factors = np.zeros_like(s)
    factors[keep] = scaled_s[keep] / (s0 * (scaled_s[keep] * scaled_s[keep] + ridge_relative))
    # macOS Accelerate can emit spurious IEEE warnings in this small SVD
    # multiplication even when every input and output entry is finite.  We
    # check finiteness explicitly below, which is the property the exporter
    # needs before handing the block to the interval backend.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        approximate_inverse = vt.T @ (factors[:, None] * u.T)
    if not np.all(np.isfinite(approximate_inverse)):
        raise FloatingPointError("ridge-SVD approximate inverse has nonfinite entries")
    nonzero = s[s > 0]
    condition = float(s[0] / nonzero[-1]) if nonzero.size else float("inf")
    return approximate_inverse, {
        "singular_value_count": int(s.size),
        "rank_after_cutoff": int(np.count_nonzero(keep)),
        "svd_rcond": float(svd_rcond),
        "ridge_relative": float(ridge_relative),
        "ridge_absolute": float(ridge_abs),
        "singular_values": {
            "max": float(s[0]),
            "min_nonzero": float(nonzero[-1]) if nonzero.size else None,
            "condition_estimate": condition,
            "first_12": [float(value) for value in s[:12]],
            "last_12": [float(value) for value in s[-12:]],
        },
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cache = load_row_cache(args.row_cache)
    labels = None if args.row_labels == "all" else {item.strip() for item in args.row_labels.split(",") if item.strip()}
    rows = selected_rows(cache, labels)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    if not rows:
        raise ValueError("no rows selected")
    column_count = int(cache["column_count"])
    residual, jacobian = dense_block(rows, column_count)
    approximate_inverse, inverse_report = ridge_svd_inverse(jacobian, args.ridge_relative, args.svd_rcond)
    finite_bounds = finite_nk_bounds(residual.tolist(), jacobian.tolist(), approximate_inverse.tolist())
    residual_inf = float(np.max(np.abs(residual)))
    jacobian_inf = float(np.max(np.sum(np.abs(jacobian), axis=1)))
    inverse_inf = float(np.max(np.sum(np.abs(approximate_inverse), axis=1)))
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "profile_finite_nk_block",
        "pass": False,
        "status": STATUS,
        "repo_commit": repo_commit(),
        "diagnostic_vs_proof": (
            "Floating sampled row-cache finite block.  Uses native C interval "
            "linear algebra for finite Y0/Z0 arithmetic, but the row cache, "
            "Jacobian, inverse, and residual are not interval-certified and no "
            "Z2/tail-complement bound is supplied."
        ),
        "row_cache": relpath(args.row_cache),
        "row_cache_sha256": sha256_file(resolve(args.row_cache)),
        "profile": cache.get("profile"),
        "profile_hash_sha256": cache.get("profile_hash_sha256"),
        "row_selection": {
            "labels": "all" if labels is None else sorted(labels),
            "selected_row_count": len(rows),
            "available_row_count": int(cache.get("row_count", len(cache.get("rows", [])))),
            "column_count": column_count,
            "max_rows": args.max_rows,
        },
        "finite_block_hashes": {
            "residual_vector_float64": sha256_array(residual),
            "jacobian_float64": sha256_array(jacobian),
            "approximate_inverse_float64": sha256_array(approximate_inverse),
        },
        "floating_norms": {
            "residual_inf": residual_inf,
            "jacobian_row_sum_inf": jacobian_inf,
            "approximate_inverse_row_sum_inf": inverse_inf,
        },
        "approximate_inverse": inverse_report,
        "finite_nk_bounds": {
            "backend": finite_bounds["backend"],
            "residual_dimension": finite_bounds["residual_dimension"],
            "coefficient_dimension": finite_bounds["coefficient_dimension"],
            "Y0_infinity_norm_A_r": finite_bounds["Y0_infinity_norm_A_r"],
            "Z0_infinity_norm_B": finite_bounds["Z0_infinity_norm_B"],
        },
        "blockers": [
            "row cache is floating, not interval residual data",
            "approximate inverse is floating ridge-SVD, not validated",
            "Z2 and infinite complement bounds are missing",
            "profile residual/mortar is far above NK entry scale",
        ],
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-cache", required=True)
    parser.add_argument("--out", default="work/profile_finite_nk_block.json")
    parser.add_argument("--row-labels", default="all")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--ridge-relative", type=float, default=1e-8)
    parser.add_argument("--svd-rcond", type=float, default=1e-12)
    args = parser.parse_args()
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    report = build_report(args)
    save_json(args.out, report)
    bounds = report["finite_nk_bounds"]
    print(f"status={report['status']}")
    print(f"shape={bounds['residual_dimension']}x{bounds['coefficient_dimension']}")
    print(f"Y0={bounds['Y0_infinity_norm_A_r']:.12e}")
    print(f"Z0={bounds['Z0_infinity_norm_B']:.12e}")
    print(f"rank_after_cutoff={report['approximate_inverse']['rank_after_cutoff']}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
