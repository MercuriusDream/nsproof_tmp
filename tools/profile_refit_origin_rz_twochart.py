#!/usr/bin/env python3
"""Refit two-chart origin Taylor blocks against physical R/Z mortar traces.

This is a diagnostic representation-repair tool.  It preserves the tail chart
and all formal tail gates, then solves only the origin Taylor coefficients so
that the origin chart matches the tail chart in physical ``R=r^2`` and
``Z=z^2`` derivatives on an overlap grid.

It is floating arithmetic and not an interval smoothness proof.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.origin_chart import derivative_indices, qx_to_rz  # noqa: E402
from validators.twochart_mortar_jacobian import (  # noqa: E402
    grid,
    tail_total_rz_jet,
)


STATUS = "TWOCHART_ORIGIN_RZ_REFIT_NOT_INTERVAL_VALIDATION"


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != "twochart_profile_projection_v1":
        raise ValueError(f"{path!r} is not a twochart_profile_projection_v1 JSON file")
    return data


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def monomials_for_degree(degree: int) -> list[tuple[int, int]]:
    return [(a, total - a) for total in range(degree + 1) for a in range(total + 1)]


def existing_coefficients(origin: dict[str, Any], monomials: list[tuple[int, int]]) -> list[float]:
    old: dict[tuple[int, int], float] = {}
    for entry in origin.get("basis", []):
        old[(int(entry["R_power"]), int(entry["Z_power"]))] = float(entry["coeff"])
    return [old.get(item, 0.0) for item in monomials]


def falling_int(power: int, order: int) -> float:
    if order > power:
        return 0.0
    out = 1.0
    for item in range(order):
        out *= power - item
    return out


def monomial_partial(a: int, b: int, R: float, Z: float, dR: int, dZ: int) -> float:
    if a < dR or b < dZ:
        return 0.0
    return falling_int(a, dR) * falling_int(b, dZ) * (R ** (a - dR)) * (Z ** (b - dZ))


def derivative_weight(dR: int, dZ: int, args: argparse.Namespace) -> float:
    total = dR + dZ
    if total == 0:
        return args.value_weight
    if total == 1:
        return args.d1_weight
    if total == 2:
        return args.d2_weight
    if total == 3:
        return args.d3_weight
    if total == 4:
        return args.d4_weight
    return 0.0


def solve_normal(rows: list[list[float]], targets: list[float], old: list[float], ridge: float) -> list[float]:
    n = len(old)
    normal = [[0.0 for _ in range(n)] for _ in range(n)]
    rhs = [0.0 for _ in range(n)]
    for row, target in zip(rows, targets):
        for i, ri in enumerate(row):
            rhs[i] += ri * target
            if ri == 0.0:
                continue
            for j in range(i, n):
                normal[i][j] += ri * row[j]
    for i in range(n):
        for j in range(i):
            normal[i][j] = normal[j][i]
        if ridge > 0.0:
            normal[i][i] += ridge
            rhs[i] += ridge * old[i]

    a = [row[:] + [rhs[i]] for i, row in enumerate(normal)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-30:
            raise ValueError("singular origin R/Z normal equation")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]
        for item in range(col, n + 1):
            a[col][item] /= pivot_value
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for item in range(col, n + 1):
                a[row][item] -= factor * a[col][item]
    return [a[index][n] for index in range(n)]


def parse_float_list(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def sample_x_values(args: argparse.Namespace) -> list[float]:
    if args.x_values.strip():
        values = parse_float_list(args.x_values)
    else:
        values = grid(args.x_min, args.x_max, args.x_samples)
    if not values:
        raise ValueError("no x sample values")
    if min(values) < 0.0 or max(values) > 1.0:
        raise ValueError("x values must lie in [0,1]")
    return values


def fit_component(
    data: dict[str, Any],
    component: str,
    degree: int,
    q_values: list[float],
    x_values: list[float],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["origin_chart"]["blocks"][key]
    monomials = monomials_for_degree(degree)
    old = existing_coefficients(origin, monomials)
    specs = [
        (dR, dZ, derivative_weight(dR, dZ, args))
        for dR, dZ in derivative_indices(args.match_order)
    ]
    specs = [(dR, dZ, weight) for dR, dZ, weight in specs if weight > 0.0]
    if not specs:
        raise ValueError("all derivative weights are zero")

    rows: list[list[float]] = []
    targets: list[float] = []
    meta: list[dict[str, Any]] = []
    for q in q_values:
        for x in x_values:
            R, Z = qx_to_rz(q, x)
            tail = tail_total_rz_jet(data, component, R, Z, args.match_order)
            for dR, dZ, weight in specs:
                scale = math.sqrt(weight)
                rows.append(
                    [
                        scale * monomial_partial(a, b, R, Z, dR, dZ)
                        for a, b in monomials
                    ]
                )
                targets.append(scale * tail.partial(dR, dZ))
                meta.append({"q": q, "x": x, "R": R, "Z": Z, "dR": dR, "dZ": dZ, "weight": weight})

    coeffs = solve_normal(rows, targets, old, args.ridge)

    def origin_partial(R: float, Z: float, dR: int, dZ: int) -> float:
        return sum(
            coeffs[index] * monomial_partial(a, b, R, Z, dR, dZ)
            for index, (a, b) in enumerate(monomials)
        )

    worst = {"abs_residual": -1.0}
    weighted_total = 0.0
    unweighted_total = 0.0
    for row_meta in meta:
        q = float(row_meta["q"])
        x = float(row_meta["x"])
        R = float(row_meta["R"])
        Z = float(row_meta["Z"])
        dR = int(row_meta["dR"])
        dZ = int(row_meta["dZ"])
        weight = float(row_meta["weight"])
        tail_value = tail_total_rz_jet(data, component, R, Z, args.match_order).partial(dR, dZ)
        origin_value = origin_partial(R, Z, dR, dZ)
        residual = tail_value - origin_value
        weighted_total += weight * residual * residual
        unweighted_total += residual * residual
        if abs(residual) > worst["abs_residual"]:
            worst = {
                **row_meta,
                "tail_value": tail_value,
                "origin_value": origin_value,
                "residual_tail_minus_origin": residual,
                "abs_residual": abs(residual),
            }

    rho2_max = max(0.0, float(origin.get("rho2_max", 0.0)))
    new_origin = {
        "enabled": True,
        "degree": degree,
        "q_min": origin.get("q_min"),
        "rho2_max": rho2_max,
        "basis": [
            {"R_power": a, "Z_power": b, "coeff": coeffs[index]}
            for index, (a, b) in enumerate(monomials)
        ],
        "sample_count": len(rows),
        "max_fit_error": worst["abs_residual"],
        "worst_mortar_row": worst,
        "note": "Origin Taylor refit to physical R/Z two-chart mortar traces; diagnostic, not interval validation.",
    }
    evidence = {
        "component": component,
        "degree": degree,
        "rows": len(rows),
        "q_values": q_values,
        "x_values": x_values,
        "match_order": args.match_order,
        "ridge": args.ridge,
        "rms_weighted": math.sqrt(weighted_total / max(len(rows), 1)),
        "rms_unweighted": math.sqrt(unweighted_total / max(len(rows), 1)),
        "max_abs_residual": worst["abs_residual"],
        "worst_row": worst,
        "old_coeff_l2": math.sqrt(sum(value * value for value in old)),
        "new_coeff_l2": math.sqrt(sum(value * value for value in coeffs)),
    }
    return new_origin, evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--degree", type=int, default=-1, help="Origin Taylor degree; default keeps existing degree.")
    parser.add_argument("--q-values", default="0.84,0.92")
    parser.add_argument("--x-values", default="")
    parser.add_argument("--x-min", type=float, default=0.0)
    parser.add_argument("--x-max", type=float, default=1.0)
    parser.add_argument("--x-samples", type=int, default=5)
    parser.add_argument("--match-order", type=int, default=2)
    parser.add_argument("--value-weight", type=float, default=1.0)
    parser.add_argument("--d1-weight", type=float, default=0.1)
    parser.add_argument("--d2-weight", type=float, default=0.01)
    parser.add_argument("--d3-weight", type=float, default=0.0)
    parser.add_argument("--d4-weight", type=float, default=0.0)
    parser.add_argument("--ridge", type=float, default=1e-12)
    args = parser.parse_args()

    if args.match_order < 0 or args.match_order > 4:
        raise ValueError("--match-order must be between 0 and 4")
    if args.x_samples <= 0:
        raise ValueError("--x-samples must be positive")
    if not 0.0 <= args.x_min <= args.x_max <= 1.0:
        raise ValueError("require 0 <= --x-min <= --x-max <= 1")
    if args.ridge < 0.0:
        raise ValueError("--ridge must be nonnegative")

    data = load_json(args.input)
    q_values = parse_float_list(args.q_values)
    if not q_values:
        raise ValueError("--q-values must contain at least one value")
    x_values = sample_x_values(args)

    out = copy.deepcopy(data)
    evidence: list[dict[str, Any]] = []
    for component in ("F", "G"):
        key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
        existing = out["origin_chart"]["blocks"][key]
        degree = int(existing.get("degree", 0)) if args.degree < 0 else args.degree
        new_origin, component_evidence = fit_component(out, component, degree, q_values, x_values, args)
        out["origin_chart"]["blocks"][key] = new_origin
        evidence.append(component_evidence)

    out["twochart_origin_rz_refit_evidence"] = {
        "status": STATUS,
        "source": args.input,
        "q_values": q_values,
        "x_values": x_values,
        "match_order": args.match_order,
        "value_weight": args.value_weight,
        "d1_weight": args.d1_weight,
        "d2_weight": args.d2_weight,
        "d3_weight": args.d3_weight,
        "d4_weight": args.d4_weight,
        "ridge": args.ridge,
        "components": evidence,
        "diagnostic_vs_proof": "floating origin-only R/Z least-squares refit; no interval proof",
    }
    save_json(args.out, out)

    print(f"input={args.input}")
    print(f"saved={args.out}")
    for item in evidence:
        print(
            f"{item['component']}: degree={item['degree']} rows={item['rows']} "
            f"max_abs={float(item['max_abs_residual']):.12e} "
            f"rms_unweighted={float(item['rms_unweighted']):.12e} "
            f"old_l2={float(item['old_coeff_l2']):.12e} new_l2={float(item['new_coeff_l2']):.12e}"
        )
    print(f"status={STATUS}")


if __name__ == "__main__":
    main()
