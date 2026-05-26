#!/usr/bin/env python3
"""Sweep sampled profile finite NK blocks across row caches and ridge values."""

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

from tools.export_profile_finite_nk_block import (  # noqa: E402
    build_report,
    save_json,
)


SCHEMA_VERSION = "nsproof-cert-v1"
STATUS = "PROFILE_FINITE_NK_SWEEP_FLOATING_NOT_PROOF"


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


def parse_csv_floats(raw: str) -> list[float]:
    values = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("expected at least one floating value")
    return values


def compact_trial(report: dict[str, Any], ridge_relative: float, svd_rcond: float) -> dict[str, Any]:
    bounds = report["finite_nk_bounds"]
    inverse = report["approximate_inverse"]
    return {
        "row_cache": report["row_cache"],
        "profile": report.get("profile"),
        "profile_hash_sha256": report.get("profile_hash_sha256"),
        "ridge_relative": ridge_relative,
        "svd_rcond": svd_rcond,
        "selected_row_count": report["row_selection"]["selected_row_count"],
        "column_count": report["row_selection"]["column_count"],
        "residual_dimension": bounds["residual_dimension"],
        "coefficient_dimension": bounds["coefficient_dimension"],
        "Y0_infinity_norm_A_r": bounds["Y0_infinity_norm_A_r"],
        "Z0_infinity_norm_B": bounds["Z0_infinity_norm_B"],
        "rank_after_cutoff": inverse["rank_after_cutoff"],
        "condition_estimate": inverse["singular_values"]["condition_estimate"],
        "residual_inf": report["floating_norms"]["residual_inf"],
        "jacobian_row_sum_inf": report["floating_norms"]["jacobian_row_sum_inf"],
        "approximate_inverse_row_sum_inf": report["floating_norms"]["approximate_inverse_row_sum_inf"],
        "coefficient_coordinate_scaling": report.get("coefficient_coordinate_scaling"),
        "residual_row_scaling": report.get("residual_row_scaling"),
        "finite_block_hashes": report["finite_block_hashes"],
    }


def trial_sort_key(trial: dict[str, Any]) -> tuple[float, float]:
    return (
        float(trial["Z0_infinity_norm_B"]),
        float(trial["Y0_infinity_norm_A_r"]),
    )


def build_sweep(args: argparse.Namespace) -> dict[str, Any]:
    ridges = parse_csv_floats(args.ridge_relative)
    rconds = parse_csv_floats(args.svd_rcond)
    trials: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    column_scaling_modes = args.column_scaling
    row_scaling_modes = args.row_scaling
    for row_cache in args.row_cache:
        for row_scaling_mode in row_scaling_modes:
            for column_scaling_mode in column_scaling_modes:
                for ridge in ridges:
                    for rcond in rconds:
                        trial_args = argparse.Namespace(
                            row_cache=row_cache,
                            row_labels=args.row_labels,
                            max_rows=args.max_rows,
                            ridge_relative=ridge,
                            svd_rcond=rcond,
                            summary_only=True,
                            column_scaling=column_scaling_mode,
                            column_scale_floor=args.column_scale_floor,
                            row_scaling=row_scaling_mode,
                            row_scale_floor=args.row_scale_floor,
                        )
                        try:
                            report = build_report(trial_args)
                            trials.append(compact_trial(report, ridge, rcond))
                        except Exception as exc:  # noqa: BLE001 - diagnostic sweep should keep going.
                            failures.append(
                                {
                                    "row_cache": row_cache,
                                    "row_scaling": row_scaling_mode,
                                    "column_scaling": column_scaling_mode,
                                    "ridge_relative": str(ridge),
                                    "svd_rcond": str(rcond),
                                    "error": repr(exc),
                                }
                            )
    best_by_cache: dict[str, dict[str, Any]] = {}
    best_by_scaling: dict[str, dict[str, Any]] = {}
    best_by_row_scaling: dict[str, dict[str, Any]] = {}
    best_by_scaling_pair: dict[str, dict[str, Any]] = {}
    for trial in trials:
        key = str(trial["row_cache"])
        current = best_by_cache.get(key)
        if current is None or trial_sort_key(trial) < trial_sort_key(current):
            best_by_cache[key] = trial
        column_scaling_key = str((trial.get("coefficient_coordinate_scaling") or {}).get("mode"))
        row_scaling_key = str((trial.get("residual_row_scaling") or {}).get("mode"))
        pair_key = f"row:{row_scaling_key}|column:{column_scaling_key}"
        current_scaling = best_by_scaling.get(column_scaling_key)
        if current_scaling is None or trial_sort_key(trial) < trial_sort_key(current_scaling):
            best_by_scaling[column_scaling_key] = trial
        current_row_scaling = best_by_row_scaling.get(row_scaling_key)
        if current_row_scaling is None or trial_sort_key(trial) < trial_sort_key(current_row_scaling):
            best_by_row_scaling[row_scaling_key] = trial
        current_pair = best_by_scaling_pair.get(pair_key)
        if current_pair is None or trial_sort_key(trial) < trial_sort_key(current_pair):
            best_by_scaling_pair[pair_key] = trial
    best_overall = min(trials, key=trial_sort_key) if trials else None
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "profile_finite_nk_sweep",
        "pass": False,
        "status": STATUS,
        "repo_commit": repo_commit(),
        "diagnostic_vs_proof": (
            "Floating sampled row-cache sweep. Finite Y0/Z0 arithmetic uses "
            "the native C interval backend, but row caches and inverses are "
            "floating diagnostics and no Z2/tail-complement bound is supplied."
        ),
        "row_caches": args.row_cache,
        "ridge_relative_values": ridges,
        "svd_rcond_values": rconds,
        "row_labels": args.row_labels,
        "max_rows": args.max_rows,
        "column_scaling_modes": column_scaling_modes,
        "column_scale_floor": args.column_scale_floor,
        "row_scaling_modes": row_scaling_modes,
        "row_scale_floor": args.row_scale_floor,
        "trial_count": len(trials),
        "failure_count": len(failures),
        "best_overall": best_overall,
        "best_by_cache": best_by_cache,
        "best_by_scaling": best_by_scaling,
        "best_by_row_scaling": best_by_row_scaling,
        "best_by_scaling_pair": best_by_scaling_pair,
        "trials": sorted(trials, key=trial_sort_key),
        "failures": failures,
        "blockers": [
            "sweep is floating and sampled, not interval residual validation",
            "approximate inverses are floating ridge-SVD diagnostics",
            "Z2 and infinite complement bounds are missing",
            "profile residual/mortar is far above NK entry scale",
        ],
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-cache", action="append", required=True)
    parser.add_argument("--out", default="work/profile_finite_nk_sweep.json")
    parser.add_argument("--row-labels", default="all")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--ridge-relative", default="1e-6,1e-8,1e-10,1e-12")
    parser.add_argument("--svd-rcond", default="1e-10,1e-12")
    parser.add_argument(
        "--column-scaling",
        action="append",
        choices=("none", "l2", "inf"),
        default=None,
    )
    parser.add_argument("--column-scale-floor", type=float, default=1e-30)
    parser.add_argument(
        "--row-scaling",
        action="append",
        choices=("none", "l2", "inf", "residual", "combined-inf"),
        default=None,
    )
    parser.add_argument("--row-scale-floor", type=float, default=1e-30)
    args = parser.parse_args()
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    if args.column_scaling is None:
        args.column_scaling = ["none"]
    if args.row_scaling is None:
        args.row_scaling = ["none"]
    report = build_sweep(args)
    save_json(args.out, report)
    best = report["best_overall"]
    print(f"status={report['status']}")
    print(f"trials={report['trial_count']} failures={report['failure_count']}")
    if best:
        print(f"best_cache={best['row_cache']}")
        print(f"best_shape={best['residual_dimension']}x{best['coefficient_dimension']}")
        print(f"best_Y0={best['Y0_infinity_norm_A_r']:.12e}")
        print(f"best_Z0={best['Z0_infinity_norm_B']:.12e}")
        print(f"best_ridge={best['ridge_relative']:.12e} best_rcond={best['svd_rcond']:.12e}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
