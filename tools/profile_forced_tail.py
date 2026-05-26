#!/usr/bin/env python3
"""Construct the first forced non-integer tail correction.

For the natural tail exponent, the leading linear transport terms cancel for
the q=0 trace.  The first nonlinear self-interaction of that trace appears at
order q^(1/gamma).  This script solves the decoupled least-squares angular
problems for a q^(1/gamma) correction that cancels that leading source.

The output is only an asymptotic diagnostic seed.  It is not expected to solve
the finite-box profile equations by itself.
"""

from __future__ import annotations

import argparse
import json
import math

from compactified_profile import grid
from profile_gauss_newton import gaussian_solve
from profile_tail_series import (
    gamma_poly,
    h_poly_for_exponent,
    poly_deriv,
    poly_eval,
    stream_poly,
)


def source_values(gamma: float, B: float, b_values: list[float]) -> tuple[list[float], list[float]]:
    m = 1.0 / gamma
    s = 3.0 - m
    t = 2.0 - m
    f0 = {0: 0.5}
    g0 = {0: B}
    p = stream_poly(f0)
    q = gamma_poly(g0)
    p1 = poly_deriv(p)
    h = h_poly_for_exponent(s, p)
    h1 = poly_deriv(h)
    q1 = poly_deriv(q)

    psi_source: list[float] = []
    gamma_source: list[float] = []
    for b in b_values:
        one_minus_b2 = 1.0 - b * b
        p_value = poly_eval(p, b)
        p_prime = poly_eval(p1, b)
        h_value = poly_eval(h, b)
        h_prime = poly_eval(h1, b)
        q_value = poly_eval(q, b)
        q_prime = poly_eval(q1, b)

        x = s * p_value - b * p_prime
        y = b * s * p_value + one_minus_b2 * p_prime
        u = (s - 2.0) * h_value - b * h_prime
        v = b * (s - 2.0) * h_value + one_minus_b2 * h_prime
        z = b * t * q_value + one_minus_b2 * q_prime
        rr = t * q_value - b * q_prime
        swirl_sq_z = b * (2.0 * t) * q_value * q_value + one_minus_b2 * 2.0 * q_value * q_prime

        psi_source.append(one_minus_b2 * (x * v - y * u) + 2.0 * y * h_value + swirl_sq_z)
        gamma_source.append(x * z - y * rr)
    return psi_source, gamma_source


def linear_psi_value(gamma: float, order: float, j: int, b: float) -> float:
    m = 1.0 / gamma
    k = 3.0 - m - order
    h = h_poly_for_exponent(k, stream_poly({2 * j: 1.0}))
    return -gamma * order * (1.0 - b * b) * poly_eval(h, b)


def linear_gamma_value(gamma: float, order: float, j: int, b: float) -> float:
    q = gamma_poly({2 * j: 1.0})
    return -gamma * order * poly_eval(q, b)


def solve_least_squares(rows: list[list[float]], rhs: list[float], ridge: float) -> list[float]:
    cols = len(rows[0])
    lhs = [[0.0 for _ in range(cols)] for _ in range(cols)]
    normal_rhs = [0.0 for _ in range(cols)]
    for row, value in zip(rows, rhs):
        for i, row_i in enumerate(row):
            normal_rhs[i] += row_i * value
            for j, row_j in enumerate(row):
                lhs[i][j] += row_i * row_j
    for i in range(cols):
        lhs[i][i] += ridge
    solution = gaussian_solve(lhs, normal_rhs)
    if solution is None:
        raise ValueError("singular least-squares normal matrix")
    return solution


def max_rms(values: list[float]) -> tuple[float, float]:
    return max(abs(value) for value in values), math.sqrt(
        sum(value * value for value in values) / max(len(values), 1)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--b-order", type=int, default=8)
    parser.add_argument("--b-min", type=float, default=-0.95)
    parser.add_argument("--b-max", type=float, default=0.95)
    parser.add_argument("--n-b", type=int, default=161)
    parser.add_argument("--ridge", type=float, default=1e-10)
    parser.add_argument(
        "--cutoff-power",
        type=int,
        default=0,
        help=(
            "Store the forced tail as q^(1/gamma) * (1-q)^cutoff_power. "
            "This preserves the q=0 asymptotic coefficient while damping the "
            "correction near the origin q=1."
        ),
    )
    parser.add_argument("--save-json", default="")
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2).")
    if args.cutoff_power < 0:
        raise SystemExit("--cutoff-power must be nonnegative")

    order = 1.0 / args.gamma
    b_values = list(grid(args.b_min, args.b_max, args.n_b))
    psi_source, gamma_source = source_values(args.gamma, args.B, b_values)
    psi_rows = [
        [linear_psi_value(args.gamma, order, j, b) for j in range(args.b_order + 1)]
        for b in b_values
    ]
    gamma_rows = [
        [linear_gamma_value(args.gamma, order, j, b) for j in range(args.b_order + 1)]
        for b in b_values
    ]
    f_solution = solve_least_squares(psi_rows, [-value for value in psi_source], args.ridge)
    g_solution = solve_least_squares(gamma_rows, [-value for value in gamma_source], args.ridge)

    psi_after = [
        src + sum(row[j] * f_solution[j] for j in range(args.b_order + 1))
        for src, row in zip(psi_source, psi_rows)
    ]
    gamma_after = [
        src + sum(row[j] * g_solution[j] for j in range(args.b_order + 1))
        for src, row in zip(gamma_source, gamma_rows)
    ]
    psi_before_max, psi_before_rms = max_rms(psi_source)
    psi_after_max, psi_after_rms = max_rms(psi_after)
    gamma_before_max, gamma_before_rms = max_rms(gamma_source)
    gamma_after_max, gamma_after_rms = max_rms(gamma_after)

    print(
        f"gamma={args.gamma} B={args.B} forced_order={order:.12e} "
        f"b_order={args.b_order} b=[{args.b_min},{args.b_max}] n_b={args.n_b}"
    )
    print(
        f"psi source before max={psi_before_max:.12e} rms={psi_before_rms:.12e}; "
        f"after max={psi_after_max:.12e} rms={psi_after_rms:.12e}"
    )
    print(
        f"Gamma source before max={gamma_before_max:.12e} rms={gamma_before_rms:.12e}; "
        f"after max={gamma_after_max:.12e} rms={gamma_after_rms:.12e}"
    )
    print("F forced coefficients:")
    for j, value in enumerate(f_solution):
        print(f"  j={j} coeff={value:.12e}")
    print("G forced coefficients:")
    for j, value in enumerate(g_solution):
        print(f"  j={j} coeff={value:.12e}")

    if args.save_json:
        data = {
            "gamma": args.gamma,
            "B": args.B,
            "q_order": 0,
            "b_order": 0,
            "bounded_edge_q_order": 0,
            "forced_tail_cutoff_power": args.cutoff_power,
            "bounded_edge_b_order": args.b_order,
            "edge_family": "vanishing",
            "vanishing_edge_power": order,
            "vanishing_edge_basis": "q^vanishing_edge_power * (1-q)^i * b^(2j)",
            "f_coeffs": [[0, 0, 0.5]],
            "g_coeffs": [[0, 0, args.B]],
            "f_bounded_edge_coeffs": [],
            "g_bounded_edge_coeffs": [],
            "f_vanishing_edge_coeffs": [
                [args.cutoff_power, j, value]
                for j, value in enumerate(f_solution)
                if abs(value) > 1e-14
            ],
            "g_vanishing_edge_coeffs": [
                [args.cutoff_power, j, value]
                for j, value in enumerate(g_solution)
                if abs(value) > 1e-14
            ],
            "evidence": {
                "status": "asymptotic_forced_tail_diagnostic_seed",
                "forced_order": order,
                "psi_source_before_max": psi_before_max,
                "psi_source_after_max": psi_after_max,
                "gamma_source_before_max": gamma_before_max,
                "gamma_source_after_max": gamma_after_max,
            },
        }
        with open(args.save_json, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"saved forced-tail seed: {args.save_json}")


if __name__ == "__main__":
    main()
