#!/usr/bin/env python3
"""Refit origin Taylor blocks against exact rectangular mortar traces.

This is a discovery/representation repair tool.  It preserves the tail and
rectangular Chebyshev blocks, then solves only the origin Taylor coefficients
so that the origin chart matches the rectangular total profile in value and
q/x derivatives at selected interface samples.

It is not an interval smoothness proof.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from compactified_profile import grid
from profile_newton_cheb import (
    eval_origin_total,
    eval_rect_total_partial,
    load_json,
    origin_h_derivative,
    origin_x_factor_derivative,
    parse_q_values,
)


def save_json(path: str, data: dict[str, object]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def monomials_for_degree(degree: int) -> list[tuple[int, int]]:
    return [(a, total - a) for total in range(degree + 1) for a in range(total + 1)]


def existing_coefficients(origin: dict[str, object], monomials: list[tuple[int, int]]) -> list[float]:
    old: dict[tuple[int, int], float] = {}
    for entry in origin.get("basis", []):  # type: ignore[union-attr]
        old[(int(entry["R_power"]), int(entry["Z_power"]))] = float(entry["coeff"])
    return [old.get(item, 0.0) for item in monomials]


def origin_basis_partial(a: int, b: int, q: float, x: float, dq_order: int, dx_order: int) -> float:
    return origin_h_derivative(a + b, q, dq_order) * origin_x_factor_derivative(a, b, x, dx_order)


def derivative_specs(max_order: int, value_weight: float, d1_weight: float, d2_weight: float) -> list[tuple[int, int, float, str]]:
    specs: list[tuple[int, int, float, str]] = [(0, 0, value_weight, "value")]
    if max_order >= 1 and d1_weight > 0.0:
        specs.extend([(1, 0, d1_weight, "q"), (0, 1, d1_weight, "x")])
    if max_order >= 2 and d2_weight > 0.0:
        specs.extend([(2, 0, d2_weight, "qq"), (1, 1, d2_weight, "qx"), (0, 2, d2_weight, "xx")])
    return specs


def solve_normal(rows: list[list[float]], targets: list[float], old: list[float], ridge: float) -> list[float]:
    n = len(old)
    normal = [[0.0 for _ in range(n)] for _ in range(n)]
    rhs = [0.0 for _ in range(n)]
    for row, target in zip(rows, targets):
        for i in range(n):
            rhs[i] += row[i] * target
            for j in range(i, n):
                value = row[i] * row[j]
                normal[i][j] += value
                if j != i:
                    normal[j][i] += value
    if ridge > 0.0:
        for i in range(n):
            normal[i][i] += ridge
            rhs[i] += ridge * old[i]

    a = [row[:] + [rhs[i]] for i, row in enumerate(normal)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-30:
            raise ValueError("singular origin mortar normal equation")
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
    return [a[i][n] for i in range(n)]


def refit_component(
    data: dict[str, object],
    component: str,
    degree: int,
    q_values: tuple[float, ...],
    x_samples: int,
    specs: list[tuple[int, int, float, str]],
    ridge: float,
) -> tuple[dict[str, object], dict[str, object]]:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    blocks = data["blocks"]  # type: ignore[index]
    origin = blocks[key]  # type: ignore[index]
    q_min = float(origin["q_min"])  # type: ignore[index]
    monomials = monomials_for_degree(degree)
    old = existing_coefficients(origin, monomials)  # type: ignore[arg-type]
    rows: list[list[float]] = []
    targets: list[float] = []
    row_meta: list[dict[str, object]] = []
    for q in q_values:
        for x in grid(0.0, 1.0, x_samples):
            for dq_order, dx_order, weight, label in specs:
                scale = math.sqrt(weight)
                row = [
                    scale * origin_basis_partial(a, b, q, x, dq_order, dx_order)
                    for a, b in monomials
                ]
                target = scale * eval_rect_total_partial(data, component, q, x, dq_order, dx_order)
                rows.append(row)
                targets.append(target)
                row_meta.append(
                    {
                        "q": q,
                        "x": x,
                        "dq_order": dq_order,
                        "dx_order": dx_order,
                        "label": label,
                        "weight": weight,
                    }
                )
    coeffs = solve_normal(rows, targets, old, ridge)

    def origin_value(q: float, x: float, dq_order: int, dx_order: int) -> float:
        return sum(
            coeffs[index] * origin_basis_partial(a, b, q, x, dq_order, dx_order)
            for index, (a, b) in enumerate(monomials)
        )

    worst = {"abs": 0.0}
    total = 0.0
    for meta in row_meta:
        q = float(meta["q"])
        x = float(meta["x"])
        dq_order = int(meta["dq_order"])
        dx_order = int(meta["dx_order"])
        diff = origin_value(q, x, dq_order, dx_order) - eval_rect_total_partial(
            data, component, q, x, dq_order, dx_order
        )
        total += diff * diff
        if abs(diff) > float(worst["abs"]):
            worst = {**meta, "diff": diff, "abs": abs(diff)}

    value_worst = 0.0
    for q in q_values:
        for x in grid(0.0, 1.0, max(x_samples, 3)):
            diff = origin_value(q, x, 0, 0) - eval_rect_total_partial(data, component, q, x, 0, 0)
            value_worst = max(value_worst, abs(diff))

    rho2_max = max(0.0, 1.0 / (q_min * q_min) - 1.0)
    new_origin = {
        "enabled": True,
        "degree": degree,
        "q_min": q_min,
        "rho2_max": rho2_max,
        "basis": [
            {"R_power": a, "Z_power": b, "coeff": coeffs[index]}
            for index, (a, b) in enumerate(monomials)
        ],
        "sample_count": len(rows),
        "max_fit_error": value_worst,
        "worst_mortar_row": worst,
        "note": "Origin Taylor refit to exact rectangular Ck mortar traces; discovery scaffold, not interval validation.",
    }
    evidence = {
        "component": component,
        "degree": degree,
        "rows": len(rows),
        "q_values": list(q_values),
        "x_samples": x_samples,
        "ridge": ridge,
        "rms_unweighted_rows": math.sqrt(total / max(len(row_meta), 1)),
        "max_value_mismatch": value_worst,
        "worst_row": worst,
        "old_coeff_l2": math.sqrt(sum(value * value for value in old)),
        "new_coeff_l2": math.sqrt(sum(value * value for value in coeffs)),
    }
    return new_origin, evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--degree", type=int, default=-1, help="Origin Taylor degree; default keeps existing degree.")
    parser.add_argument("--q-values", default="0.9")
    parser.add_argument("--x-samples", type=int, default=9)
    parser.add_argument("--match-order", type=int, default=2)
    parser.add_argument("--value-weight", type=float, default=1.0)
    parser.add_argument("--d1-weight", type=float, default=0.05)
    parser.add_argument("--d2-weight", type=float, default=0.001)
    parser.add_argument("--ridge", type=float, default=1e-12)
    args = parser.parse_args()

    data = load_json(args.input)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError("input must be a transseries_cheb_projection_v1 JSON file")
    q_values = parse_q_values(args.q_values)
    if not q_values:
        raise ValueError("--q-values must contain at least one q value")
    if args.x_samples <= 0:
        raise ValueError("--x-samples must be positive")
    if args.match_order < 0 or args.match_order > 2:
        raise ValueError("--match-order must be 0, 1, or 2")
    specs = derivative_specs(args.match_order, args.value_weight, args.d1_weight, args.d2_weight)

    out = copy.deepcopy(data)
    evidence: list[dict[str, object]] = []
    for component in ("F", "G"):
        key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
        origin = out["blocks"][key]  # type: ignore[index]
        existing_degree = int(origin.get("degree", 0))  # type: ignore[union-attr]
        degree = existing_degree if args.degree < 0 else args.degree
        new_origin, component_evidence = refit_component(
            out,
            component,
            degree=degree,
            q_values=q_values,
            x_samples=args.x_samples,
            specs=specs,
            ridge=args.ridge,
        )
        out["blocks"][key] = new_origin  # type: ignore[index]
        evidence.append(component_evidence)

    out["origin_mortar_refit_evidence"] = {
        "status": "origin_mortar_refit_not_validated",
        "source": args.input,
        "q_values": list(q_values),
        "x_samples": args.x_samples,
        "match_order": args.match_order,
        "value_weight": args.value_weight,
        "d1_weight": args.d1_weight,
        "d2_weight": args.d2_weight,
        "ridge": args.ridge,
        "components": evidence,
    }
    save_json(args.out, out)
    print(f"input={args.input}")
    print(f"saved={args.out}")
    for item in evidence:
        print(
            f"{item['component']}: degree={item['degree']} rows={item['rows']} "
            f"max_value_mismatch={float(item['max_value_mismatch']):.12e} "
            f"rms_rows={float(item['rms_unweighted_rows']):.12e} "
            f"worst={item['worst_row']} "
            f"old_l2={float(item['old_coeff_l2']):.12e} new_l2={float(item['new_coeff_l2']):.12e}"
        )
    print("status=ORIGIN_MORTAR_REFIT_NOT_INTERVAL_VALIDATION")


if __name__ == "__main__":
    main()
