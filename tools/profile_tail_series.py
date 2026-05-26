#!/usr/bin/env python3
"""Analyze the q=0 tail series of compactified profile seeds.

For the tail-factored ansatz

    psi = r^2 z q^(1/gamma) F(q,b),
    Gamma = r^2 q^(1/gamma) G(q,b),

integer q-corrections are not automatically admissible at infinity.  If
``F_n(b) q^n`` or ``G_n(b) q^n`` is present, the linear transport part produces
a tail coefficient proportional to ``n`` unless the angular streamfunction
piece is harmonic and the Gamma piece vanishes.  The nonlinear self-interaction
of the leading trace appears at the non-integer order ``q^(1/gamma)``.

This diagnostic expands the stored polynomial/edge basis near q=0 and reports
which tail coefficients are feeding the residual before running another finite
box solve.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from math import comb

from compactified_profile import grid


Poly = dict[int, float]


@dataclass(frozen=True)
class OrderReport:
    order: float
    f_max: float
    g_max: float
    psi_linear_max: float
    psi_linear_rms: float
    psi_linear_b: float
    gamma_linear_max: float
    gamma_linear_rms: float
    gamma_linear_b: float


def poly_add(left: Poly, right: Poly, scale: float = 1.0) -> Poly:
    out = dict(left)
    for power, value in right.items():
        out[power] = out.get(power, 0.0) + scale * value
        if abs(out[power]) < 1e-16:
            del out[power]
    return out


def poly_mul_monomial(poly: Poly, power_shift: int, scale: float) -> Poly:
    return {power + power_shift: scale * value for power, value in poly.items()}


def poly_deriv(poly: Poly) -> Poly:
    return {power - 1: power * value for power, value in poly.items() if power > 0}


def poly_eval(poly: Poly, b: float) -> float:
    return sum(value * (b**power) for power, value in poly.items())


def poly_max(poly: Poly, b_min: float, b_max: float, n_b: int) -> float:
    return max(abs(poly_eval(poly, b)) for b in grid(b_min, b_max, n_b))


def add_to_series(series: dict[int, Poly], order: int, b_power: int, value: float) -> None:
    if order < 0:
        raise ValueError("negative q-order is not supported")
    poly = series.setdefault(order, {})
    poly[b_power] = poly.get(b_power, 0.0) + value
    if abs(poly[b_power]) < 1e-16:
        del poly[b_power]


def expand_coefficients(data: dict[str, object], key: str, max_order: int) -> dict[int, Poly]:
    series: dict[int, Poly] = {}

    for i, j, value in data.get(key, []):  # type: ignore[union-attr]
        order = int(i)
        if order <= max_order:
            add_to_series(series, order, 2 * int(j), float(value))

    bounded_key = key.replace("_coeffs", "_bounded_edge_coeffs")
    for i, j, value in data.get(bounded_key, []):  # type: ignore[union-attr]
        i_int = int(i)
        for order in range(min(i_int, max_order) + 1):
            add_to_series(
                series,
                order,
                2 * int(j),
                float(value) * comb(i_int, order) * ((-1.0) ** order),
            )

    vanishing_key = key.replace("_coeffs", "_vanishing_edge_coeffs")
    sigma = float(data.get("vanishing_edge_power", 1.0))
    sigma_round = round(sigma)
    if abs(sigma - sigma_round) <= 1e-12:
        sigma_int = int(sigma_round)
        for i, j, value in data.get(vanishing_key, []):  # type: ignore[union-attr]
            i_int = int(i)
            for offset in range(i_int + 1):
                order = sigma_int + offset
                if order > max_order:
                    break
                add_to_series(
                    series,
                    order,
                    2 * int(j),
                    float(value) * comb(i_int, offset) * ((-1.0) ** offset),
                )
    else:
        # Non-integer q^sigma terms are intentionally not folded into integer
        # coefficients; they need their own indicial treatment.
        pass

    return series


def expand_fractional_vanishing_leading(data: dict[str, object], key: str) -> tuple[float, Poly] | None:
    sigma = float(data.get("vanishing_edge_power", 1.0))
    if abs(sigma - round(sigma)) <= 1e-12:
        return None
    vanishing_key = key.replace("_coeffs", "_vanishing_edge_coeffs")
    poly: Poly = {}
    for _i, j, value in data.get(vanishing_key, []):  # type: ignore[union-attr]
        power = 2 * int(j)
        poly[power] = poly.get(power, 0.0) + float(value)
    return sigma, poly


def stream_poly(f_poly: Poly) -> Poly:
    # P(b) = b(1-b^2)F(b)
    return poly_add(poly_mul_monomial(f_poly, 1, 1.0), poly_mul_monomial(f_poly, 3, -1.0))


def gamma_poly(g_poly: Poly) -> Poly:
    # Q(b) = (1-b^2)G(b)
    return poly_add(g_poly, poly_mul_monomial(g_poly, 2, -1.0))


def h_poly_for_exponent(k: float, p_poly: Poly) -> Poly:
    p2 = poly_deriv(poly_deriv(p_poly))
    h = poly_mul_monomial(p_poly, 0, k * (k - 1.0))
    h = poly_add(h, p2)
    h = poly_add(h, poly_mul_monomial(p2, 2, -1.0))
    return h


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(len(values), 1))


def order_report(
    order: float,
    gamma: float,
    m: float,
    f_poly: Poly,
    g_poly: Poly,
    b_min: float,
    b_max: float,
    n_b: int,
) -> OrderReport:
    p_poly = stream_poly(f_poly)
    q_poly = gamma_poly(g_poly)
    k = 3.0 - m - order
    h_poly = h_poly_for_exponent(k, p_poly)

    psi_values: list[tuple[float, float]] = []
    gamma_values: list[tuple[float, float]] = []
    for b in grid(b_min, b_max, n_b):
        psi_values.append((b, -gamma * order * (1.0 - b * b) * poly_eval(h_poly, b)))
        gamma_values.append((b, -gamma * order * poly_eval(q_poly, b)))

    psi_worst_b, psi_worst = max(psi_values, key=lambda item: abs(item[1]))
    gamma_worst_b, gamma_worst = max(gamma_values, key=lambda item: abs(item[1]))
    return OrderReport(
        order=order,
        f_max=poly_max(f_poly, b_min, b_max, n_b),
        g_max=poly_max(g_poly, b_min, b_max, n_b),
        psi_linear_max=abs(psi_worst),
        psi_linear_rms=rms([value for _b, value in psi_values]),
        psi_linear_b=psi_worst_b,
        gamma_linear_max=abs(gamma_worst),
        gamma_linear_rms=rms([value for _b, value in gamma_values]),
        gamma_linear_b=gamma_worst_b,
    )


def leading_nonlinear_source(
    gamma: float,
    f0: Poly,
    g0: Poly,
    b_min: float,
    b_max: float,
    n_b: int,
) -> tuple[float, float, float, float, float, float]:
    m = 1.0 / gamma
    s = 3.0 - m
    t = 2.0 - m
    p = stream_poly(f0)
    q = gamma_poly(g0)
    p1 = poly_deriv(p)
    h = h_poly_for_exponent(s, p)
    h1 = poly_deriv(h)
    q1 = poly_deriv(q)

    psi_values: list[tuple[float, float]] = []
    gamma_values: list[tuple[float, float]] = []
    for b in grid(b_min, b_max, n_b):
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

        psi_source = one_minus_b2 * (x * v - y * u) + 2.0 * y * h_value + swirl_sq_z
        gamma_source = x * z - y * rr
        psi_values.append((b, psi_source))
        gamma_values.append((b, gamma_source))

    psi_b, psi_worst = max(psi_values, key=lambda item: abs(item[1]))
    gamma_b, gamma_worst = max(gamma_values, key=lambda item: abs(item[1]))
    return (
        abs(psi_worst),
        rms([value for _b, value in psi_values]),
        psi_b,
        abs(gamma_worst),
        rms([value for _b, value in gamma_values]),
        gamma_b,
    )


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--max-order", type=int, default=6)
    parser.add_argument("--b-min", type=float, default=-0.95)
    parser.add_argument("--b-max", type=float, default=0.95)
    parser.add_argument("--n-b", type=int, default=121)
    args = parser.parse_args()

    data = load_data(args.seed_json)
    gamma = float(data["gamma"])
    B = float(data.get("B", 1.0))
    m = 1.0 / gamma
    f_series = expand_coefficients(data, "f_coeffs", args.max_order)
    g_series = expand_coefficients(data, "g_coeffs", args.max_order)

    print(f"seed={args.seed_json}")
    print(
        f"gamma={gamma} B={B} m=1/gamma={m:.12e} "
        f"orders=0..{args.max_order} b=[{args.b_min},{args.b_max}] n_b={args.n_b}"
    )
    print("order,F_n_max,G_n_max,psi_linear_max,psi_linear_rms,psi_b,gamma_linear_max,gamma_linear_rms,gamma_b")
    for order in range(args.max_order + 1):
        report = order_report(
            order,
            gamma,
            m,
            f_series.get(order, {}),
            g_series.get(order, {}),
            args.b_min,
            args.b_max,
            args.n_b,
        )
        print(
            f"{report.order},{report.f_max:.12e},{report.g_max:.12e},"
            f"{report.psi_linear_max:.12e},{report.psi_linear_rms:.12e},"
            f"{report.psi_linear_b:.12e},{report.gamma_linear_max:.12e},"
            f"{report.gamma_linear_rms:.12e},{report.gamma_linear_b:.12e}"
        )

    fractional_f = expand_fractional_vanishing_leading(data, "f_coeffs")
    fractional_g = expand_fractional_vanishing_leading(data, "g_coeffs")
    if fractional_f is not None or fractional_g is not None:
        sigma = (
            fractional_f[0]
            if fractional_f is not None
            else fractional_g[0]  # type: ignore[index]
        )
        f_poly = fractional_f[1] if fractional_f is not None else {}
        g_poly = fractional_g[1] if fractional_g is not None else {}
        report = order_report(
            sigma,
            gamma,
            m,
            f_poly,
            g_poly,
            args.b_min,
            args.b_max,
            args.n_b,
        )
        print("fractional_leading_vanishing_order:")
        print(
            "order,F_sigma_max,G_sigma_max,psi_linear_max,psi_linear_rms,"
            "psi_b,gamma_linear_max,gamma_linear_rms,gamma_b="
            f"{report.order:.12e},{report.f_max:.12e},{report.g_max:.12e},"
            f"{report.psi_linear_max:.12e},{report.psi_linear_rms:.12e},"
            f"{report.psi_linear_b:.12e},{report.gamma_linear_max:.12e},"
            f"{report.gamma_linear_rms:.12e},{report.gamma_linear_b:.12e}"
        )

    nonlinear = leading_nonlinear_source(
        gamma,
        f_series.get(0, {}),
        g_series.get(0, {}),
        args.b_min,
        args.b_max,
        args.n_b,
    )
    print("leading_trace_nonlinear_source_at_order_q^m:")
    print(
        "psi_max,psi_rms,psi_b,gamma_max,gamma_rms,gamma_b="
        f"{nonlinear[0]:.12e},{nonlinear[1]:.12e},{nonlinear[2]:.12e},"
        f"{nonlinear[3]:.12e},{nonlinear[4]:.12e},{nonlinear[5]:.12e}"
    )


if __name__ == "__main__":
    main()
