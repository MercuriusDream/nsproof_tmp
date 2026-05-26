#!/usr/bin/env python3
"""Project a compactified profile seed into a proof-native Chebyshev layout.

This is a projection scaffold, not a validated profile proof.  Its purpose is
to move diagnostic bump seeds into the representation demanded by the proof
program:

    F(q,x) = 1/2 + q^2 F_an(q,x) + q^(1/gamma) F_1(q,x) + ...
    G(q,x) = B   + q^2 G_an(q,x) + q^(1/gamma) G_1(q,x) + ...

where x=b^2.  The ordinary q^1 channel is structurally absent from the output
format.  Existing vanishing-edge coefficients with exponent 1/gamma are lifted
into the first fractional block; all remaining seed content is projected into
the analytic q^2 block on piecewise Chebyshev patches.

The output is intended as input for a future exact-residual Newton solver and
interval validator.  It also records tail leakage and reconstruction errors so
that projection failures are explicit.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from compactified_profile import CompactifiedProfile, load_seed_json_profile
from validators.tail_transseries import forced_qp_expected_coeffs


Coeff = tuple[int, int, float]
ChebTable = list[list[float]]


DEFAULT_Q_PATCHES = (0.0, 0.16, 0.34, 0.52, 0.72, 0.90, 1.0)
DEFAULT_X_PATCHES = (0.0, 0.04, 0.10, 0.20, 0.45, 0.75, 1.0)


@dataclass(frozen=True)
class Patch:
    q0: float
    q1: float
    x0: float
    x1: float
    coeffs: ChebTable


def parse_fraction_or_float(raw: str) -> float:
    text = raw.strip()
    if "/" in text:
        return float(Fraction(text))
    return float(text)


def parse_breaks(raw: str, defaults: tuple[float, ...]) -> tuple[float, ...]:
    if not raw.strip():
        return defaults
    values = tuple(float(item) for item in raw.split(","))
    if len(values) < 2:
        raise ValueError("patch break list must contain at least two values")
    if abs(values[0]) > 1e-15 or abs(values[-1] - 1.0) > 1e-15:
        raise ValueError("patch breaks must start at 0 and end at 1")
    for left, right in zip(values, values[1:]):
        if not left < right:
            raise ValueError("patch breaks must be strictly increasing")
    return values


def coeff_poly_at_q_power(coeffs: tuple[Coeff, ...], q_power: int, x: float) -> float:
    return sum(value * (x**j) for i, j, value in coeffs if i == q_power)


def x_poly_coeffs_at_q_power(coeffs: tuple[Coeff, ...], q_power: int) -> list[float]:
    degree = -1
    for i, j, _value in coeffs:
        if i == q_power:
            degree = max(degree, j)
    if degree < 0:
        return []
    out = [0.0 for _ in range(degree + 1)]
    for i, j, value in coeffs:
        if i == q_power:
            out[j] += value
    return out


def vanishing_trace_coeffs(coeffs: tuple[Coeff, ...]) -> list[float]:
    degree = -1
    for _i, j, _value in coeffs:
        degree = max(degree, j)
    if degree < 0:
        return []
    out = [0.0 for _ in range(degree + 1)]
    for _i, j, value in coeffs:
        out[j] += value
    return out


def bounded_edge_value(q: float, x: float, coeffs: tuple[Coeff, ...]) -> float:
    one_minus_q = 1.0 - q
    return sum(value * (one_minus_q**i) * (x**j) for i, j, value in coeffs)


def x_poly_value(coeffs: tuple[float, ...], x: float) -> float:
    return sum(value * (x**index) for index, value in enumerate(coeffs))


def cheb_lobatto_points(degree: int, left: float, right: float) -> list[float]:
    if degree < 1:
        return [0.5 * (left + right)]
    mid = 0.5 * (left + right)
    half = 0.5 * (right - left)
    return [mid + half * math.cos(math.pi * j / degree) for j in range(degree + 1)]


def cheb_lobatto_coeffs(values: list[float]) -> list[float]:
    degree = len(values) - 1
    if degree <= 0:
        return [values[0]]
    coeffs: list[float] = []
    for k in range(degree + 1):
        total = 0.0
        for j, value in enumerate(values):
            weight = 0.5 if j == 0 or j == degree else 1.0
            total += weight * value * math.cos(math.pi * k * j / degree)
        k_weight = 0.5 if k == 0 or k == degree else 1.0
        coeffs.append((2.0 / degree) * k_weight * total)
    return coeffs


def tensor_cheb_coeffs(samples: list[list[float]]) -> ChebTable:
    # samples[q_index][x_index] on tensor Chebyshev-Lobatto nodes.
    q_count = len(samples)
    x_count = len(samples[0]) if q_count else 0
    by_x = [cheb_lobatto_coeffs([samples[i][j] for j in range(x_count)]) for i in range(q_count)]
    out: ChebTable = []
    for lx in range(x_count):
        out.append(cheb_lobatto_coeffs([by_x[i][lx] for i in range(q_count)]))
    # Return coeffs[kq][kx], not coeffs[kx][kq].
    q_degree = q_count - 1
    x_degree = x_count - 1
    coeffs = [[0.0 for _ in range(x_degree + 1)] for _ in range(q_degree + 1)]
    for lx in range(x_degree + 1):
        for kq, value in enumerate(out[lx]):
            coeffs[kq][lx] = value
    return coeffs


def cheb_eval_1d(coeffs: list[float], t: float) -> float:
    if not coeffs:
        return 0.0
    b_k2 = 0.0
    b_k1 = 0.0
    for c in reversed(coeffs[1:]):
        b_k0 = 2.0 * t * b_k1 - b_k2 + c
        b_k2 = b_k1
        b_k1 = b_k0
    return coeffs[0] + t * b_k1 - b_k2


def cheb_eval_tensor(coeffs: ChebTable, q: float, x: float, q0: float, q1: float, x0: float, x1: float) -> float:
    tq = 0.0 if q1 == q0 else (2.0 * q - q0 - q1) / (q1 - q0)
    tx = 0.0 if x1 == x0 else (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = [cheb_eval_1d(row, tx) for row in coeffs]
    return cheb_eval_1d(q_values, tq)


def project_patch(
    func: Callable[[float, float], float],
    q0: float,
    q1: float,
    x0: float,
    x1: float,
    degree_q: int,
    degree_x: int,
) -> Patch:
    q_nodes = cheb_lobatto_points(degree_q, q0, q1)
    x_nodes = cheb_lobatto_points(degree_x, x0, x1)
    samples = [[func(q, x) for x in x_nodes] for q in q_nodes]
    return Patch(q0=q0, q1=q1, x0=x0, x1=x1, coeffs=tensor_cheb_coeffs(samples))


def patch_to_json(patch: Patch) -> dict[str, object]:
    return {
        "q_interval": [patch.q0, patch.q1],
        "x_interval": [patch.x0, patch.x1],
        "coeffs": patch.coeffs,
    }


def find_patch(patches: list[Patch], q: float, x: float) -> Patch:
    for patch in patches:
        q_ok = patch.q0 - 1e-15 <= q <= patch.q1 + 1e-15
        x_ok = patch.x0 - 1e-15 <= x <= patch.x1 + 1e-15
        if q_ok and x_ok:
            return patch
    raise ValueError(f"point outside patches q={q} x={x}")


def grid_values(start: float, stop: float, count: int) -> Iterable[float]:
    if count <= 1:
        yield 0.5 * (start + stop)
        return
    step = (stop - start) / (count - 1)
    for i in range(count):
        yield start + i * step


def solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-18:
            a[pivot][col] += 1e-14
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]
        if abs(pivot_value) < 1e-30:
            raise ValueError("singular normal equation in origin projection")
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


def origin_taylor_fit(
    func: Callable[[float, float], float],
    degree: int,
    q_min: float,
    ridge: float,
) -> dict[str, object]:
    if degree < 0:
        return {"enabled": False}
    rho2_max = max(0.0, 1.0 / (q_min * q_min) - 1.0)
    monomials = [(a, b) for total in range(degree + 1) for a in range(total + 1) for b in [total - a]]
    samples: list[tuple[list[float], float, tuple[float, float]]] = []
    count = max(2 * degree + 3, 7)
    for i in range(count):
        r_frac = i / (count - 1)
        for j in range(count):
            z_frac = j / (count - 1)
            R = rho2_max * r_frac
            Z = rho2_max * z_frac
            if R + Z > rho2_max + 1e-15:
                continue
            rho2 = R + Z
            if rho2 == 0.0:
                q = 1.0
                x = 0.0
            else:
                q = 1.0 / math.sqrt(1.0 + rho2)
                x = Z / rho2
            row = [(R**a) * (Z**b) for a, b in monomials]
            samples.append((row, func(q, x), (R, Z)))
    n = len(monomials)
    normal = [[0.0 for _ in range(n)] for _ in range(n)]
    rhs = [0.0 for _ in range(n)]
    for row, value, _point in samples:
        for a in range(n):
            rhs[a] += row[a] * value
            for b in range(n):
                normal[a][b] += row[a] * row[b]
    for i in range(n):
        normal[i][i] += ridge
    coeffs = solve_linear_system(normal, rhs)
    worst = 0.0
    worst_point = (0.0, 0.0)
    for row, value, point in samples:
        approx = sum(coeffs[i] * row[i] for i in range(n))
        err = abs(approx - value)
        if err > worst:
            worst = err
            worst_point = point
    return {
        "enabled": True,
        "degree": degree,
        "q_min": q_min,
        "rho2_max": rho2_max,
        "basis": [{"R_power": a, "Z_power": b, "coeff": coeffs[k]} for k, (a, b) in enumerate(monomials)],
        "sample_count": len(samples),
        "max_fit_error": worst,
        "worst_RZ": list(worst_point),
        "note": "Least-squares origin Taylor scaffold; not an interval smoothness certificate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "--seed-json", dest="seed_json", required=True)
    parser.add_argument("--out", "--save-json", dest="out_json", required=True)
    parser.add_argument("--gamma", default="", help="Override gamma; accepts decimals or fractions such as 9/20.")
    parser.add_argument("--B", type=float, default=None)
    parser.add_argument("--degree-q", type=int, default=8)
    parser.add_argument("--degree-x", type=int, default=8)
    parser.add_argument("--tail-blocks", type=int, default=1)
    parser.add_argument(
        "--forced-qp-mode",
        choices=("seed", "formal"),
        default="seed",
        help=(
            "Use the seed's lifted q^(1/gamma) block, or replace it by the "
            "formal first forced-tail recurrence coefficient."
        ),
    )
    parser.add_argument(
        "--forced-origin-cutoff-power",
        type=int,
        default=6,
        help="For --forced-qp-mode formal, multiply the forced trace by (1-q^2)^M.",
    )
    parser.add_argument("--q-patches", default="")
    parser.add_argument("--x-patches", default="")
    parser.add_argument("--origin-degree", type=int, default=4)
    parser.add_argument("--origin-q-min", type=float, default=0.90)
    parser.add_argument("--origin-ridge", type=float, default=1e-14)
    parser.add_argument("--check-n", type=int, default=17)
    args = parser.parse_args()
    if args.tail_blocks < 1:
        raise ValueError("--tail-blocks must be at least 1 because the forced q^(1/gamma) block is structural")

    seed_gamma, seed_B, profile = load_seed_json_profile(args.seed_json)
    gamma = parse_fraction_or_float(args.gamma) if args.gamma else seed_gamma
    B = args.B if args.B is not None else seed_B
    if abs(gamma - seed_gamma) > 1e-13:
        profile = CompactifiedProfile(
            gamma=gamma,
            f_coeffs=profile.f_coeffs,
            g_coeffs=profile.g_coeffs,
            f_edge_coeffs=profile.f_edge_coeffs,
            g_edge_coeffs=profile.g_edge_coeffs,
            f_bounded_edge_coeffs=profile.f_bounded_edge_coeffs,
            g_bounded_edge_coeffs=profile.g_bounded_edge_coeffs,
            f_vanishing_edge_coeffs=profile.f_vanishing_edge_coeffs,
            g_vanishing_edge_coeffs=profile.g_vanishing_edge_coeffs,
            vanishing_edge_power=profile.vanishing_edge_power,
            f_interior_bump_coeffs=profile.f_interior_bump_coeffs,
            g_interior_bump_coeffs=profile.g_interior_bump_coeffs,
            interior_bump_q_centers=profile.interior_bump_q_centers,
            interior_bump_b2_centers=profile.interior_bump_b2_centers,
            interior_bump_q_radius=profile.interior_bump_q_radius,
            interior_bump_b2_radius=profile.interior_bump_b2_radius,
            interior_bump_shape=profile.interior_bump_shape,
            interior_bump_q_flatness=profile.interior_bump_q_flatness,
        )

    p = 1.0 / gamma
    q_breaks = parse_breaks(args.q_patches, DEFAULT_Q_PATCHES)
    x_breaks = parse_breaks(args.x_patches, DEFAULT_X_PATCHES)
    lifts_vanishing = abs(profile.vanishing_edge_power - p) <= 1e-10
    expected_forced_f, expected_forced_g = forced_qp_expected_coeffs(gamma, B)
    if args.forced_origin_cutoff_power < 0:
        raise ValueError("--forced-origin-cutoff-power must be nonnegative")
    forced_qp_lifted = lifts_vanishing or args.forced_qp_mode == "formal"

    def f_source(q: float, x: float) -> float:
        return profile.F_total(q, math.sqrt(max(0.0, min(1.0, x))))

    def g_source(q: float, x: float) -> float:
        return profile.G_total(q, math.sqrt(max(0.0, min(1.0, x))))

    def f_frac_1(q: float, x: float) -> float:
        if args.forced_qp_mode == "formal":
            cutoff = (1.0 - q * q) ** args.forced_origin_cutoff_power
            return cutoff * x_poly_value(expected_forced_f, x)
        if not lifts_vanishing:
            return 0.0
        return bounded_edge_value(q, x, profile.f_vanishing_edge_coeffs)

    def g_frac_1(q: float, x: float) -> float:
        if args.forced_qp_mode == "formal":
            cutoff = (1.0 - q * q) ** args.forced_origin_cutoff_power
            return cutoff * x_poly_value(expected_forced_g, x)
        if not lifts_vanishing:
            return 0.0
        return bounded_edge_value(q, x, profile.g_vanishing_edge_coeffs)

    def f_an(q: float, x: float) -> float:
        if abs(q) < 1e-15:
            return coeff_poly_at_q_power(profile.f_coeffs, 2, x)
        return (f_source(q, x) - 0.5 - (q**p) * f_frac_1(q, x)) / (q * q)

    def g_an(q: float, x: float) -> float:
        if abs(q) < 1e-15:
            return coeff_poly_at_q_power(profile.g_coeffs, 2, x)
        return (g_source(q, x) - B - (q**p) * g_frac_1(q, x)) / (q * q)

    def project_all(func: Callable[[float, float], float]) -> list[Patch]:
        patches: list[Patch] = []
        for q0, q1 in zip(q_breaks, q_breaks[1:]):
            for x0, x1 in zip(x_breaks, x_breaks[1:]):
                patches.append(project_patch(func, q0, q1, x0, x1, args.degree_q, args.degree_x))
        return patches

    f_an_patches = project_all(f_an)
    g_an_patches = project_all(g_an)
    f_frac_patches = [project_all(f_frac_1)]
    g_frac_patches = [project_all(g_frac_1)]
    for _block in range(2, args.tail_blocks + 1):
        f_frac_patches.append(project_all(lambda _q, _x: 0.0))
        g_frac_patches.append(project_all(lambda _q, _x: 0.0))

    def eval_patches(patches: list[Patch], q: float, x: float) -> float:
        patch = find_patch(patches, q, x)
        return cheb_eval_tensor(patch.coeffs, q, x, patch.q0, patch.q1, patch.x0, patch.x1)

    worst_f = 0.0
    worst_g = 0.0
    worst_point_f = (0.0, 0.0)
    worst_point_g = (0.0, 0.0)
    for q in grid_values(0.0, 1.0, args.check_n):
        for x in grid_values(0.0, 1.0, args.check_n):
            f_recon = 0.5 + q * q * eval_patches(f_an_patches, q, x)
            g_recon = B + q * q * eval_patches(g_an_patches, q, x)
            for k, patches in enumerate(f_frac_patches, start=1):
                f_recon += (q ** (k * p)) * eval_patches(patches, q, x)
            for k, patches in enumerate(g_frac_patches, start=1):
                g_recon += (q ** (k * p)) * eval_patches(patches, q, x)
            f_err = abs(f_recon - f_source(q, x))
            g_err = abs(g_recon - g_source(q, x))
            if f_err > worst_f:
                worst_f = f_err
                worst_point_f = (q, x)
            if g_err > worst_g:
                worst_g = g_err
                worst_point_g = (q, x)

    f_origin = origin_taylor_fit(f_source, args.origin_degree, args.origin_q_min, args.origin_ridge)
    g_origin = origin_taylor_fit(g_source, args.origin_degree, args.origin_q_min, args.origin_ridge)

    out = {
        "format": "transseries_cheb_projection_v1",
        "status": "projection_scaffold_not_validated",
        "source_seed_json": args.seed_json,
        "gamma": gamma,
        "B": B,
        "p": p,
        "representation": {
            "x_variable": "x=b^2",
            "F": "1/2 + q^2 F_an(q,x) + sum_k q^(k/gamma) F_k(q,x)",
            "G": "B + q^2 G_an(q,x) + sum_k q^(k/gamma) G_k(q,x)",
            "ordinary_q1_channel": "structurally_absent_in_projection",
            "fractional_blocks": len(f_frac_patches),
            "origin_patch": "least_squares_RZ_Taylor_scaffold",
        },
        "patches": {
            "q_breaks": list(q_breaks),
            "x_breaks": list(x_breaks),
            "degree_q": args.degree_q,
            "degree_x": args.degree_x,
        },
        "tail_constraints": {
            "F0": 0.5,
            "G0": B,
            "ordinary_q1": {
                "F_coeffs": x_poly_coeffs_at_q_power(profile.f_coeffs, 1),
                "G_coeffs": x_poly_coeffs_at_q_power(profile.g_coeffs, 1),
                "F_max_abs": max(abs(c) for c in x_poly_coeffs_at_q_power(profile.f_coeffs, 1) or [0.0]),
                "G_max_abs": max(abs(c) for c in x_poly_coeffs_at_q_power(profile.g_coeffs, 1) or [0.0]),
            },
            "forced_qp": {
                "mode": args.forced_qp_mode,
                "lifted_from_vanishing_edge": forced_qp_lifted,
                "seed_lifted_from_vanishing_edge": lifts_vanishing,
                "seed_vanishing_edge_power": profile.vanishing_edge_power,
                "formal_origin_cutoff_power": args.forced_origin_cutoff_power
                if args.forced_qp_mode == "formal"
                else None,
                "F_trace_x_coeffs": list(expected_forced_f)
                if args.forced_qp_mode == "formal"
                else (vanishing_trace_coeffs(profile.f_vanishing_edge_coeffs) if lifts_vanishing else []),
                "G_trace_x_coeffs": list(expected_forced_g)
                if args.forced_qp_mode == "formal"
                else (vanishing_trace_coeffs(profile.g_vanishing_edge_coeffs) if lifts_vanishing else []),
                "note": (
                    "Trace is the formal first forced-tail recurrence coefficient."
                    if args.forced_qp_mode == "formal"
                    else "Trace is seed-derived and must be checked against the formal recurrence."
                ),
            },
        },
        "blocks": {
            "F_an": [patch_to_json(patch) for patch in f_an_patches],
            "G_an": [patch_to_json(patch) for patch in g_an_patches],
            "F_frac": [[patch_to_json(patch) for patch in block] for block in f_frac_patches],
            "G_frac": [[patch_to_json(patch) for patch in block] for block in g_frac_patches],
            "F_origin_taylor": f_origin,
            "G_origin_taylor": g_origin,
        },
        "projection_checks": {
            "check_grid": args.check_n,
            "max_F_reconstruction_error": worst_f,
            "max_F_error_qx": list(worst_point_f),
            "max_G_reconstruction_error": worst_g,
            "max_G_error_qx": list(worst_point_g),
            "acceptance_note": "Projection is only a discovery scaffold; interval proof still requires exact residual and NK validation.",
        },
    }

    out_dir = os.path.dirname(args.out_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"saved projection: {args.out_json}")
    print(f"gamma={gamma:.15g} B={B:.15g} p={p:.15g}")
    print(f"patches={(len(q_breaks)-1)}x{(len(x_breaks)-1)} degree={args.degree_q}x{args.degree_x}")
    print(f"ordinary_q1_F_max={out['tail_constraints']['ordinary_q1']['F_max_abs']:.12e}")
    print(f"ordinary_q1_G_max={out['tail_constraints']['ordinary_q1']['G_max_abs']:.12e}")
    print(f"forced_qp_lifted={forced_qp_lifted} mode={args.forced_qp_mode}")
    print(f"projection_F_error={worst_f:.12e} at q={worst_point_f[0]:.6f} x={worst_point_f[1]:.6f}")
    print(f"projection_G_error={worst_g:.12e} at q={worst_point_g[0]:.6f} x={worst_point_g[1]:.6f}")
    print(f"origin_F_fit_error={f_origin.get('max_fit_error', 0.0):.12e}")
    print(f"origin_G_fit_error={g_origin.get('max_fit_error', 0.0):.12e}")


if __name__ == "__main__":
    main()
