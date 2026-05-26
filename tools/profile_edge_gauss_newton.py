#!/usr/bin/env python3
"""Gauss-Newton continuation with an edge-adapted outer-tail basis.

The extra basis is

    (1-q)^i * eta^j,    eta = b^2 / (1-b^2),

which is adapted to the indicial angular variable zeta^2 and has support
strength near the far compactified edge q=0.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_profile import CompactifiedProfile, Coeff, load_seed_json_profile
from profile_gauss_newton import (
    gaussian_solve,
    normal_step,
    rms,
    sample_edge_points_qb,
    sample_points,
    sample_points_qb,
)
from profile_optimize import build_basis


Label = tuple[str, str, int, int]


@dataclass
class Candidate:
    labels: list[Label]
    values: list[float]
    gamma: float

    def coeffs(self, kind: str, family: str) -> tuple[Coeff, ...]:
        return tuple(
            (i, j, value)
            for (basis_kind, basis_family, i, j), value in zip(self.labels, self.values)
            if basis_kind == kind and basis_family == family
        )

    def profile(self) -> CompactifiedProfile:
        return CompactifiedProfile(
            gamma=self.gamma,
            f_coeffs=self.coeffs("F", "mono"),
            g_coeffs=self.coeffs("G", "mono"),
            f_edge_coeffs=self.coeffs("F", "edge"),
            g_edge_coeffs=self.coeffs("G", "edge"),
        )

    def shifted(self, variable_indices: list[int], delta: list[float], scale: float) -> "Candidate":
        values = list(self.values)
        for index, update in zip(variable_indices, delta):
            values[index] += scale * update
        return Candidate(self.labels, values, self.gamma)


def build_labels(q_order: int, b_order: int, edge_q_order: int, edge_b_order: int) -> list[Label]:
    labels: list[Label] = []
    for kind, i, j in build_basis(q_order, b_order):
        labels.append((kind, "mono", i, j))
    for kind in ("F", "G"):
        for i in range(edge_q_order + 1):
            for j in range(edge_b_order + 1):
                labels.append((kind, "edge", i, j))
    return labels


def initial_values(labels: list[Label], seed_path: str) -> tuple[float, float, list[float]]:
    gamma, B, profile = load_seed_json_profile(seed_path)
    coeff_map: dict[Label, float] = {}
    for i, j, value in profile.f_coeffs:
        coeff_map[("F", "mono", i, j)] = value
    for i, j, value in profile.g_coeffs:
        coeff_map[("G", "mono", i, j)] = value
    for i, j, value in profile.f_edge_coeffs:
        coeff_map[("F", "edge", i, j)] = value
    for i, j, value in profile.g_edge_coeffs:
        coeff_map[("G", "edge", i, j)] = value
    values = []
    for label in labels:
        kind, family, i, j = label
        if label in coeff_map:
            values.append(coeff_map[label])
        elif family == "mono" and kind == "F" and i == 0 and j == 0:
            values.append(0.5)
        elif family == "mono" and kind == "G" and i == 0 and j == 0:
            values.append(B)
        else:
            values.append(0.0)
    return gamma, B, values


def residual_vector(candidate: Candidate, points: list[tuple[float, float]], h: float) -> list[float]:
    profile = candidate.profile()
    out: list[float] = []
    for r, z in points:
        res = residual_at(profile.psi, profile.swirl, candidate.gamma, r, z, h)
        out.append(res.e_psi)
        out.append(res.e_gamma)
    return out


def build_jacobian(
    candidate: Candidate,
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
        plus = Candidate(candidate.labels, plus_values, candidate.gamma)
        minus = Candidate(candidate.labels, minus_values, candidate.gamma)
        r_plus = residual_vector(plus, points, h)
        r_minus = residual_vector(minus, points, h)
        columns.append([(rp - rm) / (2.0 * step) for rp, rm in zip(r_plus, r_minus)])
    return columns


def variable_indices(labels: list[Label], freeze_monomial: bool, fix_constants: bool) -> list[int]:
    indices: list[int] = []
    for idx, label in enumerate(labels):
        kind, family, i, j = label
        if freeze_monomial and family == "mono":
            continue
        if fix_constants and family == "mono" and i == 0 and j == 0 and kind in ("F", "G"):
            continue
        indices.append(idx)
    return indices


def save_seed(path: str, candidate: Candidate, B: float, args: argparse.Namespace, score: float) -> None:
    profile = candidate.profile()
    data = {
        "gamma": candidate.gamma,
        "B": B,
        "q_order": args.q_order,
        "b_order": args.b_order,
        "edge_q_order": args.edge_q_order,
        "edge_b_order": args.edge_b_order,
        "f_coeffs": [[i, j, value] for i, j, value in profile.f_coeffs],
        "g_coeffs": [[i, j, value] for i, j, value in profile.g_coeffs],
        "f_edge_coeffs": [[i, j, value] for i, j, value in profile.f_edge_coeffs],
        "g_edge_coeffs": [[i, j, value] for i, j, value in profile.g_edge_coeffs],
        "edge_basis": "(1-q)^i * (b^2/(1-b^2))^j",
        "evidence": {
            "rms_residual": score,
            "h": args.h,
            "status": "approximate_non_validated_edge_basis_seed",
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def make_points(args: argparse.Namespace) -> list[tuple[float, float]]:
    if args.grid_mode == "rz":
        return sample_points(args.r_min, args.r_max, args.z_min, args.z_max, args.n, args.h)
    if args.grid_mode == "qb":
        points = sample_points_qb(
            args.q_min, args.q_max, args.b_min, args.b_max, args.n_q, args.n_b, args.h
        )
    else:
        rz_points = sample_points(args.r_min, args.r_max, args.z_min, args.z_max, args.n, args.h)
        qb_points = sample_points_qb(
            args.q_min, args.q_max, args.b_min, args.b_max, args.n_q, args.n_b, args.h
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
    return points


def solve(candidate: Candidate, points: list[tuple[float, float]], variables: list[int], args: argparse.Namespace) -> tuple[Candidate, float]:
    residuals = residual_vector(candidate, points, args.h)
    score = rms(residuals)
    damping = args.damping
    print(f"iter=-01 rms={score:.12e} damping={damping:.3e}")
    for iteration in range(args.iterations):
        jac = build_jacobian(candidate, variables, points, args.h, args.fd_step)
        step = normal_step(residuals, jac, damping)
        if step is None:
            damping *= 10.0
            print(f"iter={iteration:03d} singular normal matrix; damping={damping:.3e}")
            continue
        step_norm = math.sqrt(sum(x * x for x in step))
        if step_norm > args.max_update_norm:
            scale = args.max_update_norm / step_norm
            step = [scale * x for x in step]
            step_norm = args.max_update_norm
        accepted = False
        alpha = 1.0
        for _ in range(12):
            trial = candidate.shifted(variables, step, alpha)
            trial_residuals = residual_vector(trial, points, args.h)
            trial_score = rms(trial_residuals)
            if trial_score < score:
                candidate = trial
                residuals = trial_residuals
                score = trial_score
                damping = max(damping * 0.5, 1e-10)
                accepted = True
                print(
                    f"iter={iteration:03d} accepted alpha={alpha:.3e} "
                    f"step_norm={step_norm:.3e} rms={score:.12e} damping={damping:.3e}"
                )
                break
            alpha *= 0.5
        if not accepted:
            damping *= 10.0
            print(
                f"iter={iteration:03d} rejected step_norm={step_norm:.3e} "
                f"rms={score:.12e} damping={damping:.3e}"
            )
    return candidate, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", default="")
    parser.add_argument("--q-order", type=int, default=7)
    parser.add_argument("--b-order", type=int, default=6)
    parser.add_argument("--edge-q-order", type=int, default=3)
    parser.add_argument("--edge-b-order", type=int, default=3)
    parser.add_argument("--freeze-monomial", action="store_true")
    parser.add_argument("--free-constants", action="store_true")
    parser.add_argument("--grid-mode", choices=["rz", "qb", "hybrid"], default="hybrid")
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=17)
    parser.add_argument("--q-min", type=float, default=0.35)
    parser.add_argument("--q-max", type=float, default=0.9)
    parser.add_argument("--b-min", type=float, default=-0.8)
    parser.add_argument("--b-max", type=float, default=0.8)
    parser.add_argument("--n-q", type=int, default=15)
    parser.add_argument("--n-b", type=int, default=15)
    parser.add_argument("--edge-repeat", type=int, default=5)
    parser.add_argument("--corner-repeat", type=int, default=25)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--fd-step", type=float, default=1e-5)
    parser.add_argument("--damping", type=float, default=1e-3)
    parser.add_argument("--max-update-norm", type=float, default=0.05)
    args = parser.parse_args()

    labels = build_labels(args.q_order, args.b_order, args.edge_q_order, args.edge_b_order)
    gamma, B, values = initial_values(labels, args.seed_json)
    candidate = Candidate(labels, values, gamma)
    points = make_points(args)
    variables = variable_indices(labels, args.freeze_monomial, fix_constants=not args.free_constants)
    print(
        f"gamma={gamma} B={B} q_order={args.q_order} b_order={args.b_order} "
        f"edge_q_order={args.edge_q_order} edge_b_order={args.edge_b_order} "
        f"points={len(points)} variables={len(variables)} freeze_monomial={args.freeze_monomial}"
    )
    candidate, score = solve(candidate, points, variables, args)
    print(f"\nfinal rms={score:.12e}")
    if args.save_json:
        save_seed(args.save_json, candidate, B, args, score)
        print(f"saved seed json: {args.save_json}")


if __name__ == "__main__":
    main()
