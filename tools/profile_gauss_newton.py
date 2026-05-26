#!/usr/bin/env python3
"""Damped Gauss-Newton solver for the compactified profile scaffold.

This is the first real nonlinear least-squares engine for the tail-factored
axisymmetric profile residual. It deliberately keeps the normalization
F_00=1/2 and G_00=B fixed by default to avoid converging to the trivial zero
solution. It is not a proof validator.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_profile import CompactifiedProfile, Coeff, grid, load_seed_json, parse_coeffs
from profile_optimize import Basis, build_basis, initial_values


@dataclass
class Candidate:
    basis: Basis
    values: list[float]
    gamma: float

    def coeffs(self, kind: str) -> tuple[Coeff, ...]:
        return tuple(
            (i, j, value)
            for (basis_kind, i, j), value in zip(self.basis, self.values)
            if basis_kind == kind
        )

    def profile(self) -> CompactifiedProfile:
        return CompactifiedProfile(
            gamma=self.gamma,
            f_coeffs=self.coeffs("F"),
            g_coeffs=self.coeffs("G"),
        )

    def shifted(self, variable_indices: list[int], delta: list[float], scale: float) -> "Candidate":
        values = list(self.values)
        for index, update in zip(variable_indices, delta):
            values[index] += scale * update
        return Candidate(self.basis, values, self.gamma)


def sample_points(
    r_min: float,
    r_max: float,
    z_min: float,
    z_max: float,
    n: int,
    h: float,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for r in grid(r_min, r_max, n):
        if r <= 2.0 * h:
            continue
        for z in grid(z_min, z_max, n):
            points.append((r, z))
    return points


def sample_points_qb(
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if not (0.0 < q_min <= q_max < 1.0):
        raise ValueError("Require 0 < q_min <= q_max < 1.")
    if not (-1.0 < b_min <= b_max < 1.0):
        raise ValueError("Require -1 < b_min <= b_max < 1.")
    for q in grid(q_min, q_max, n_q):
        rho = math.sqrt(1.0 / (q * q) - 1.0)
        for b in grid(b_min, b_max, n_b):
            r = rho * math.sqrt(max(0.0, 1.0 - b * b))
            z = rho * b
            if r > 2.0 * h:
                points.append((r, z))
    return points


def sample_edge_points_qb(
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
    edge_repeat: int,
    corner_repeat: int,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if edge_repeat <= 0 and corner_repeat <= 0:
        return points
    q_values = list(grid(q_min, q_max, n_q))
    b_values = list(grid(b_min, b_max, n_b))
    for iq, q in enumerate(q_values):
        rho = math.sqrt(1.0 / (q * q) - 1.0)
        for ib, b in enumerate(b_values):
            on_q_edge = iq == 0 or iq == len(q_values) - 1
            on_b_edge = ib == 0 or ib == len(b_values) - 1
            if not (on_q_edge or on_b_edge):
                continue
            repeat = edge_repeat
            if on_q_edge and on_b_edge:
                repeat += corner_repeat
            r = rho * math.sqrt(max(0.0, 1.0 - b * b))
            z = rho * b
            if r <= 2.0 * h:
                continue
            for _ in range(repeat):
                points.append((r, z))
    return points


def residual_vector(candidate: Candidate, points: list[tuple[float, float]], h: float) -> list[float]:
    profile = candidate.profile()
    out: list[float] = []
    for r, z in points:
        res = residual_at(profile.psi, profile.swirl, candidate.gamma, r, z, h)
        out.append(res.e_psi)
        out.append(res.e_gamma)
    return out


def rms(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values) / max(len(values), 1))


def gaussian_solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    n = len(b)
    aug = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-14:
            return None
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= scale
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def build_jacobian(
    candidate: Candidate,
    base: list[float],
    variable_indices: list[int],
    points: list[tuple[float, float]],
    h: float,
    fd_step: float,
) -> list[list[float]]:
    columns: list[list[float]] = []
    for index in variable_indices:
        step = fd_step * max(1.0, abs(candidate.values[index]))
        plus_values = list(candidate.values)
        minus_values = list(candidate.values)
        plus_values[index] += step
        minus_values[index] -= step
        plus = Candidate(candidate.basis, plus_values, candidate.gamma)
        minus = Candidate(candidate.basis, minus_values, candidate.gamma)
        r_plus = residual_vector(plus, points, h)
        r_minus = residual_vector(minus, points, h)
        columns.append([(rp - rm) / (2.0 * step) for rp, rm in zip(r_plus, r_minus)])
    return columns


def normal_step(
    residuals: list[float],
    jac_columns: list[list[float]],
    damping: float,
) -> list[float] | None:
    p = len(jac_columns)
    lhs = [[0.0 for _ in range(p)] for _ in range(p)]
    rhs = [0.0 for _ in range(p)]
    for i in range(p):
        col_i = jac_columns[i]
        rhs[i] = -sum(j_i * r_i for j_i, r_i in zip(col_i, residuals))
        for j in range(i, p):
            value = sum(j_i * j_j for j_i, j_j in zip(col_i, jac_columns[j]))
            lhs[i][j] = value
            lhs[j][i] = value
    for i in range(p):
        lhs[i][i] += damping * max(lhs[i][i], 1.0)
    return gaussian_solve(lhs, rhs)


def variable_indices(basis: Basis, fix_constants: bool) -> list[int]:
    indices: list[int] = []
    for idx, label in enumerate(basis):
        if fix_constants and (label == ("F", 0, 0) or label == ("G", 0, 0)):
            continue
        indices.append(idx)
    return indices


def values_from_initial_coeffs(
    basis: Basis,
    B: float,
    init_f: str,
    init_g: str,
) -> list[float]:
    values = initial_values(basis, B)
    coeff_map: dict[tuple[str, int, int], float] = {}
    if init_f:
        for i, j, value in parse_coeffs(init_f):
            coeff_map[("F", i, j)] = value
    if init_g:
        for i, j, value in parse_coeffs(init_g):
            coeff_map[("G", i, j)] = value
    for idx, label in enumerate(basis):
        if label in coeff_map:
            values[idx] = coeff_map[label]
    return values


def values_from_seed_json(basis: Basis, B: float, seed_json: str) -> tuple[float, float, list[float]]:
    gamma, seed_B, f_coeffs, g_coeffs = load_seed_json(seed_json)
    values = initial_values(basis, B if B is not None else seed_B)
    coeff_map: dict[tuple[str, int, int], float] = {}
    for i, j, value in f_coeffs:
        coeff_map[("F", i, j)] = value
    for i, j, value in g_coeffs:
        coeff_map[("G", i, j)] = value
    for idx, label in enumerate(basis):
        if label in coeff_map:
            values[idx] = coeff_map[label]
    return gamma, seed_B, values


def save_seed_json(
    path: str,
    candidate: Candidate,
    B: float,
    q_order: int,
    b_order: int,
    score: float,
    grid_n: int,
    h: float,
) -> None:
    data = {
        "gamma": candidate.gamma,
        "B": B,
        "q_order": q_order,
        "b_order": b_order,
        "f_coeffs": [[i, j, value] for i, j, value in candidate.coeffs("F")],
        "g_coeffs": [[i, j, value] for i, j, value in candidate.coeffs("G")],
        "evidence": {
            "training_grid_n": grid_n,
            "h": h,
            "rms_residual": score,
            "status": "approximate_non_validated_seed",
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def gauss_newton(
    candidate: Candidate,
    points: list[tuple[float, float]],
    h: float,
    variables: list[int],
    iterations: int,
    fd_step: float,
    damping: float,
    max_update_norm: float,
) -> tuple[Candidate, float]:
    residuals = residual_vector(candidate, points, h)
    score = rms(residuals)
    print(f"iter=-01 rms={score:.12e} damping={damping:.3e}")
    for iteration in range(iterations):
        jac = build_jacobian(candidate, residuals, variables, points, h, fd_step)
        step = normal_step(residuals, jac, damping)
        if step is None:
            damping *= 10.0
            print(f"iter={iteration:03d} singular normal matrix; damping={damping:.3e}")
            continue
        step_norm = math.sqrt(sum(x * x for x in step))
        if step_norm > max_update_norm:
            scale = max_update_norm / step_norm
            step = [scale * x for x in step]
            step_norm = max_update_norm

        accepted = False
        best_trial = candidate
        best_residuals = residuals
        best_score = score
        alpha = 1.0
        for _ in range(12):
            trial = candidate.shifted(variables, step, alpha)
            trial_residuals = residual_vector(trial, points, h)
            trial_score = rms(trial_residuals)
            if trial_score < best_score:
                accepted = True
                best_trial = trial
                best_residuals = trial_residuals
                best_score = trial_score
                break
            alpha *= 0.5

        if accepted:
            candidate = best_trial
            residuals = best_residuals
            score = best_score
            damping = max(damping * 0.5, 1e-10)
            print(
                f"iter={iteration:03d} accepted alpha={alpha:.3e} "
                f"step_norm={step_norm:.3e} rms={score:.12e} damping={damping:.3e}"
            )
        else:
            damping *= 10.0
            print(
                f"iter={iteration:03d} rejected step_norm={step_norm:.3e} "
                f"rms={score:.12e} damping={damping:.3e}"
            )
    return candidate, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--q-order", type=int, default=2)
    parser.add_argument("--b-order", type=int, default=1)
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--grid-mode", choices=["rz", "qb", "hybrid"], default="rz")
    parser.add_argument("--q-min", type=float, default=0.35)
    parser.add_argument("--q-max", type=float, default=0.9)
    parser.add_argument("--b-min", type=float, default=-0.8)
    parser.add_argument("--b-max", type=float, default=0.8)
    parser.add_argument("--n-q", type=int, default=9)
    parser.add_argument("--n-b", type=int, default=9)
    parser.add_argument("--edge-repeat", type=int, default=0)
    parser.add_argument("--corner-repeat", type=int, default=0)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--fd-step", type=float, default=1e-5)
    parser.add_argument("--damping", type=float, default=1e-3)
    parser.add_argument("--max-update-norm", type=float, default=2.0)
    parser.add_argument("--free-constants", action="store_true")
    parser.add_argument("--init-f", default="")
    parser.add_argument("--init-g", default="")
    parser.add_argument("--seed-json", default="")
    parser.add_argument("--save-json", default="")
    args = parser.parse_args()

    basis = build_basis(args.q_order, args.b_order)
    gamma = args.gamma
    B = args.B
    if args.seed_json:
        seed_gamma, seed_B, values = values_from_seed_json(basis, B, args.seed_json)
        gamma = seed_gamma
        B = seed_B
    else:
        values = values_from_initial_coeffs(basis, B, args.init_f, args.init_g)
    candidate = Candidate(basis=basis, values=values, gamma=gamma)
    if args.grid_mode == "rz":
        points = sample_points(args.r_min, args.r_max, args.z_min, args.z_max, args.n, args.h)
        grid_label = f"rz n={args.n}"
    elif args.grid_mode == "qb":
        points = sample_points_qb(
            args.q_min,
            args.q_max,
            args.b_min,
            args.b_max,
            args.n_q,
            args.n_b,
            args.h,
        )
        points.extend(
            sample_edge_points_qb(
                args.q_min,
                args.q_max,
                args.b_min,
                args.b_max,
                args.n_q,
                args.n_b,
                args.h,
                args.edge_repeat,
                args.corner_repeat,
            )
        )
        grid_label = f"qb n_q={args.n_q} n_b={args.n_b}"
    else:
        rz_points = sample_points(args.r_min, args.r_max, args.z_min, args.z_max, args.n, args.h)
        qb_points = sample_points_qb(
            args.q_min,
            args.q_max,
            args.b_min,
            args.b_max,
            args.n_q,
            args.n_b,
            args.h,
        )
        seen = set()
        points = []
        for point in rz_points + qb_points:
            key = (round(point[0], 12), round(point[1], 12))
            if key not in seen:
                seen.add(key)
                points.append(point)
        points.extend(
            sample_edge_points_qb(
                args.q_min,
                args.q_max,
                args.b_min,
                args.b_max,
                args.n_q,
                args.n_b,
                args.h,
                args.edge_repeat,
                args.corner_repeat,
            )
        )
        grid_label = f"hybrid rz n={args.n} qb n_q={args.n_q} n_b={args.n_b}"
    variables = variable_indices(basis, fix_constants=not args.free_constants)
    print(
        f"gamma={gamma} B={B} q_order={args.q_order} "
        f"b_order={args.b_order} {grid_label} points={len(points)} variables={len(variables)}"
    )
    candidate, score = gauss_newton(
        candidate,
        points=points,
        h=args.h,
        variables=variables,
        iterations=args.iterations,
        fd_step=args.fd_step,
        damping=args.damping,
        max_update_norm=args.max_update_norm,
    )
    print(f"\nfinal rms={score:.12e}")
    print("F coefficients:")
    for i, j, value in candidate.coeffs("F"):
        print(f"  {i},{j},{value:+.12e}")
    print("G coefficients:")
    for i, j, value in candidate.coeffs("G"):
        print(f"  {i},{j},{value:+.12e}")
    if args.save_json:
        save_seed_json(
            args.save_json,
            candidate=candidate,
            B=B,
            q_order=args.q_order,
            b_order=args.b_order,
            score=score,
            grid_n=args.n,
            h=args.h,
        )
        print(f"saved seed json: {args.save_json}")


if __name__ == "__main__":
    main()
