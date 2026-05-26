#!/usr/bin/env python3
"""Gauss-Newton continuation with an axis-regular far-edge basis.

The legacy edge basis

    (1-q)^i * (b^2/(1-b^2))^j

is useful inside a truncated angular box but is singular as |b| -> 1. This
solver uses the bounded replacement

    (1-q)^i * b^(2j),

which remains regular on the full angular interval. It can initialize the
bounded coefficients by least-squares projection of an older singular-edge
seed, then discard the singular edge terms before residual optimization.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_collocation import qb_to_rz
from compactified_profile import CompactifiedProfile, Coeff, grid, load_seed_json_profile
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
    vanishing_edge_power: float = 1.0
    interior_bump_q_centers: tuple[float, ...] = ()
    interior_bump_b2_centers: tuple[float, ...] = ()
    interior_bump_q_radius: float = 0.14
    interior_bump_b2_radius: float = 0.10
    interior_bump_shape: str = "compact"
    interior_bump_q_flatness: float = 1.0

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
            f_bounded_edge_coeffs=self.coeffs("F", "bounded"),
            g_bounded_edge_coeffs=self.coeffs("G", "bounded"),
            f_vanishing_edge_coeffs=self.coeffs("F", "vanishing"),
            g_vanishing_edge_coeffs=self.coeffs("G", "vanishing"),
            vanishing_edge_power=self.vanishing_edge_power,
            f_interior_bump_coeffs=self.coeffs("F", "interior_bump"),
            g_interior_bump_coeffs=self.coeffs("G", "interior_bump"),
            interior_bump_q_centers=self.interior_bump_q_centers,
            interior_bump_b2_centers=self.interior_bump_b2_centers,
            interior_bump_q_radius=self.interior_bump_q_radius,
            interior_bump_b2_radius=self.interior_bump_b2_radius,
            interior_bump_shape=self.interior_bump_shape,
            interior_bump_q_flatness=self.interior_bump_q_flatness,
        )

    def shifted(self, variable_indices: list[int], delta: list[float], scale: float) -> "Candidate":
        values = list(self.values)
        for index, update in zip(variable_indices, delta):
            values[index] += scale * update
        return Candidate(
            self.labels,
            values,
            self.gamma,
            self.vanishing_edge_power,
            self.interior_bump_q_centers,
            self.interior_bump_b2_centers,
            self.interior_bump_q_radius,
            self.interior_bump_b2_radius,
            self.interior_bump_shape,
            self.interior_bump_q_flatness,
        )


def build_labels(
    q_order: int,
    b_order: int,
    edge_q_order: int,
    edge_b_order: int,
    edge_family: str,
    interior_bump_q_count: int,
    interior_bump_b2_count: int,
    interior_bump_kinds: tuple[str, ...],
) -> list[Label]:
    labels: list[Label] = []
    for kind, i, j in build_basis(q_order, b_order):
        labels.append((kind, "mono", i, j))
    for kind in ("F", "G"):
        for i in range(edge_q_order + 1):
            for j in range(edge_b_order + 1):
                labels.append((kind, edge_family, i, j))
    for kind in interior_bump_kinds:
        for i in range(interior_bump_q_count):
            for j in range(interior_bump_b2_count):
                labels.append((kind, "interior_bump", i, j))
    return labels


def edge_basis_value(
    family: str,
    q: float,
    b: float,
    i: int,
    j: int,
    vanishing_edge_power: float,
) -> float:
    value = ((1.0 - q) ** i) * ((b * b) ** j)
    if family == "vanishing":
        return (q ** vanishing_edge_power) * value
    return value


def fit_bounded_edge(
    labels: list[Label],
    kind: str,
    family: str,
    vanishing_edge_power: float,
    source: CompactifiedProfile,
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    ridge: float,
) -> dict[Label, float]:
    active = [label for label in labels if label[0] == kind and label[1] == family]
    lhs = [[0.0 for _ in active] for _ in active]
    rhs = [0.0 for _ in active]
    edge_coeffs = source.f_edge_coeffs if kind == "F" else source.g_edge_coeffs
    bounded_coeffs = source.f_bounded_edge_coeffs if kind == "F" else source.g_bounded_edge_coeffs
    vanishing_coeffs = (
        source.f_vanishing_edge_coeffs if kind == "F" else source.g_vanishing_edge_coeffs
    )
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            target = source.edge_poly(q, b, edge_coeffs) + source.bounded_edge_poly(
                q, b, bounded_coeffs
            ) + source.vanishing_edge_poly(q, b, vanishing_coeffs)
            row = [
                edge_basis_value(family, q, b, i, j, vanishing_edge_power)
                for _, _, i, j in active
            ]
            for col_i, value_i in enumerate(row):
                rhs[col_i] += value_i * target
                for col_j, value_j in enumerate(row):
                    lhs[col_i][col_j] += value_i * value_j
    for idx in range(len(active)):
        lhs[idx][idx] += ridge
    solution = gaussian_solve(lhs, rhs)
    if solution is None:
        return {}
    return {label: value for label, value in zip(active, solution)}


def parse_float_list(raw: str) -> tuple[float, ...]:
    if not raw.strip():
        return ()
    return tuple(float(item) for item in raw.split(",") if item.strip())


def parse_kind_list(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ("F", "G")
    kinds = tuple(item.strip().upper() for item in raw.split(",") if item.strip())
    if not kinds or any(kind not in ("F", "G") for kind in kinds):
        raise ValueError("--interior-bump-kinds must contain F, G, or F,G")
    return kinds


def parse_active_points(raw: str, expected: int) -> list[tuple[float, ...]]:
    points: list[tuple[float, ...]] = []
    if not raw.strip():
        return points
    for item in raw.split(";"):
        if not item.strip():
            continue
        parts = tuple(float(part) for part in item.split(",") if part.strip())
        if len(parts) != expected:
            raise ValueError(f"bad active point {item!r}; expected {expected} comma-separated fields")
        points.append(parts)
    return points


def initial_values(labels: list[Label], seed_path: str, args: argparse.Namespace) -> tuple[float, float, list[float]]:
    gamma, B, profile = load_seed_json_profile(seed_path)
    coeff_map: dict[Label, float] = {}
    for i, j, value in profile.f_coeffs:
        coeff_map[("F", "mono", i, j)] = value
    for i, j, value in profile.g_coeffs:
        coeff_map[("G", "mono", i, j)] = value
    for i, j, value in profile.f_bounded_edge_coeffs:
        coeff_map[("F", "bounded", i, j)] = value
    for i, j, value in profile.g_bounded_edge_coeffs:
        coeff_map[("G", "bounded", i, j)] = value
    for i, j, value in profile.f_vanishing_edge_coeffs:
        coeff_map[("F", "vanishing", i, j)] = value
    for i, j, value in profile.g_vanishing_edge_coeffs:
        coeff_map[("G", "vanishing", i, j)] = value
    for i, j, value in profile.f_interior_bump_coeffs:
        coeff_map[("F", "interior_bump", i, j)] = value
    for i, j, value in profile.g_interior_bump_coeffs:
        coeff_map[("G", "interior_bump", i, j)] = value
    if args.zero_tail_angular:
        for kind in ("F", "G"):
            for label in list(coeff_map):
                label_kind, family, i, j = label
                if label_kind == kind and family == "mono" and i == 0 and j > 0:
                    coeff_map[label] = 0.0
    if args.fit_seed_edge:
        coeff_map.update(
            fit_bounded_edge(
                labels,
                "F",
                args.edge_family,
                args.vanishing_edge_power,
                profile,
                args.fit_q_min,
                args.fit_q_max,
                args.fit_b_min,
                args.fit_b_max,
                args.fit_n_q,
                args.fit_n_b,
                args.fit_ridge,
            )
        )
        coeff_map.update(
            fit_bounded_edge(
                labels,
                "G",
                args.edge_family,
                args.vanishing_edge_power,
                profile,
                args.fit_q_min,
                args.fit_q_max,
                args.fit_b_min,
                args.fit_b_max,
                args.fit_n_q,
                args.fit_n_b,
                args.fit_ridge,
            )
        )
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
        plus = Candidate(
            candidate.labels,
            plus_values,
            candidate.gamma,
            candidate.vanishing_edge_power,
            candidate.interior_bump_q_centers,
            candidate.interior_bump_b2_centers,
            candidate.interior_bump_q_radius,
            candidate.interior_bump_b2_radius,
            candidate.interior_bump_shape,
            candidate.interior_bump_q_flatness,
        )
        minus = Candidate(
            candidate.labels,
            minus_values,
            candidate.gamma,
            candidate.vanishing_edge_power,
            candidate.interior_bump_q_centers,
            candidate.interior_bump_b2_centers,
            candidate.interior_bump_q_radius,
            candidate.interior_bump_b2_radius,
            candidate.interior_bump_shape,
            candidate.interior_bump_q_flatness,
        )
        r_plus = residual_vector(plus, points, h)
        r_minus = residual_vector(minus, points, h)
        columns.append([(rp - rm) / (2.0 * step) for rp, rm in zip(r_plus, r_minus)])
    return columns


def variable_indices(
    labels: list[Label],
    freeze_monomial: bool,
    freeze_edge_coeffs: bool,
    fix_constants: bool,
    bounded_shell_min: int,
    freeze_tail_angular: bool,
    monomial_min_q_order: int,
    freeze_interior_bumps: bool,
) -> list[int]:
    indices: list[int] = []
    for idx, label in enumerate(labels):
        kind, family, i, j = label
        if freeze_monomial and family == "mono":
            continue
        if freeze_edge_coeffs and family in ("bounded", "vanishing"):
            continue
        if freeze_interior_bumps and family == "interior_bump":
            continue
        if family == "mono" and i < monomial_min_q_order:
            continue
        if fix_constants and family == "mono" and i == 0 and j == 0 and kind in ("F", "G"):
            continue
        if freeze_tail_angular and family == "mono" and i == 0 and j > 0:
            continue
        if family in ("bounded", "vanishing") and bounded_shell_min >= 0 and i < bounded_shell_min and j < bounded_shell_min:
            continue
        indices.append(idx)
    return indices


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
    for q, b, repeat in parse_active_points(args.active_qb_points, 3):
        r, z = qb_to_rz(q, b)
        if r <= 2.0 * args.h:
            continue
        for _ in range(max(0, int(round(repeat)))):
            points.append((r, z))
    for r, z, repeat in parse_active_points(args.active_rz_points, 3):
        if r <= 2.0 * args.h:
            continue
        for _ in range(max(0, int(round(repeat)))):
            points.append((r, z))
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


def save_seed(path: str, candidate: Candidate, B: float, args: argparse.Namespace, score: float) -> None:
    profile = candidate.profile()
    data = {
        "gamma": candidate.gamma,
        "B": B,
        "q_order": args.q_order,
        "b_order": args.b_order,
        "bounded_edge_q_order": args.edge_q_order,
        "bounded_edge_b_order": args.edge_b_order,
        "f_coeffs": [[i, j, value] for i, j, value in profile.f_coeffs],
        "g_coeffs": [[i, j, value] for i, j, value in profile.g_coeffs],
        "f_bounded_edge_coeffs": [
            [i, j, value] for i, j, value in profile.f_bounded_edge_coeffs
        ],
        "g_bounded_edge_coeffs": [
            [i, j, value] for i, j, value in profile.g_bounded_edge_coeffs
        ],
        "f_vanishing_edge_coeffs": [
            [i, j, value] for i, j, value in profile.f_vanishing_edge_coeffs
        ],
        "g_vanishing_edge_coeffs": [
            [i, j, value] for i, j, value in profile.g_vanishing_edge_coeffs
        ],
        "f_interior_bump_coeffs": [
            [i, j, value] for i, j, value in profile.f_interior_bump_coeffs
        ],
        "g_interior_bump_coeffs": [
            [i, j, value] for i, j, value in profile.g_interior_bump_coeffs
        ],
        "interior_bump_basis": "C_infty tensor bumps in q and b^2, compactly supported away from q=0",
        "interior_bump_q_centers": list(profile.interior_bump_q_centers),
        "interior_bump_b2_centers": list(profile.interior_bump_b2_centers),
        "interior_bump_q_radius": profile.interior_bump_q_radius,
        "interior_bump_b2_radius": profile.interior_bump_b2_radius,
        "interior_bump_shape": profile.interior_bump_shape,
        "interior_bump_q_flatness": profile.interior_bump_q_flatness,
        "bounded_edge_basis": "(1-q)^i * b^(2j)",
        "vanishing_edge_basis": "q^vanishing_edge_power * (1-q)^i * b^(2j)",
        "vanishing_edge_power": args.vanishing_edge_power,
        "edge_family": args.edge_family,
        "dropped_singular_edge_basis": True,
        "evidence": {
            "rms_residual": score,
            "h": args.h,
            "status": "approximate_non_validated_bounded_edge_basis_seed",
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", default="")
    parser.add_argument("--q-order", type=int, default=7)
    parser.add_argument("--b-order", type=int, default=6)
    parser.add_argument("--edge-q-order", type=int, default=10)
    parser.add_argument("--edge-b-order", type=int, default=10)
    parser.add_argument("--edge-family", choices=["bounded", "vanishing"], default="bounded")
    parser.add_argument("--vanishing-edge-power", type=float, default=1.0)
    parser.add_argument(
        "--interior-bump-q-centers",
        default="",
        help="Comma-separated q centers for compact interior bumps.",
    )
    parser.add_argument(
        "--interior-bump-b2-centers",
        default="",
        help="Comma-separated b^2 centers for compact interior bumps.",
    )
    parser.add_argument("--interior-bump-q-radius", type=float, default=0.14)
    parser.add_argument("--interior-bump-b2-radius", type=float, default=0.10)
    parser.add_argument(
        "--interior-bump-shape",
        choices=["compact", "flat_gaussian"],
        default="compact",
    )
    parser.add_argument("--interior-bump-q-flatness", type=float, default=1.0)
    parser.add_argument(
        "--interior-bump-kinds",
        default="F,G",
        help="Comma-separated profile components allowed to use interior bumps: F, G, or F,G.",
    )
    parser.add_argument("--freeze-interior-bumps", action="store_true")
    parser.add_argument("--freeze-monomial", action="store_true")
    parser.add_argument(
        "--freeze-edge-coeffs",
        action="store_true",
        help="Keep all bounded/vanishing edge-family coefficients fixed.",
    )
    parser.add_argument(
        "--monomial-min-q-order",
        type=int,
        default=0,
        help=(
            "Only vary monomial coefficients with q-order at least this value. "
            "Use 2 to preserve the q=0 trace and freeze the q^1 tail channel."
        ),
    )
    parser.add_argument("--zero-tail-angular", action="store_true")
    parser.add_argument("--freeze-tail-angular", action="store_true")
    parser.add_argument(
        "--bounded-shell-min",
        type=int,
        default=-1,
        help=(
            "Only vary bounded-edge coefficients with i >= this value or j >= this "
            "value. Use this to test a newly added outer shell while keeping lower "
            "bounded coefficients fixed."
        ),
    )
    parser.add_argument("--free-constants", action="store_true")
    parser.add_argument("--fit-seed-edge", action="store_true")
    parser.add_argument("--fit-q-min", type=float, default=0.30)
    parser.add_argument("--fit-q-max", type=float, default=0.90)
    parser.add_argument("--fit-b-min", type=float, default=-0.85)
    parser.add_argument("--fit-b-max", type=float, default=0.85)
    parser.add_argument("--fit-n-q", type=int, default=19)
    parser.add_argument("--fit-n-b", type=int, default=19)
    parser.add_argument("--fit-ridge", type=float, default=1e-10)
    parser.add_argument("--grid-mode", choices=["rz", "qb", "hybrid"], default="hybrid")
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=17)
    parser.add_argument("--q-min", type=float, default=0.30)
    parser.add_argument("--q-max", type=float, default=0.9)
    parser.add_argument("--b-min", type=float, default=-0.85)
    parser.add_argument("--b-max", type=float, default=0.85)
    parser.add_argument("--n-q", type=int, default=15)
    parser.add_argument("--n-b", type=int, default=15)
    parser.add_argument("--edge-repeat", type=int, default=6)
    parser.add_argument("--corner-repeat", type=int, default=35)
    parser.add_argument(
        "--active-qb-points",
        default="",
        help=(
            "Semicolon-separated q,b,repeat triples appended to the training set. "
            "This gives active max-gate points additional least-squares weight."
        ),
    )
    parser.add_argument(
        "--active-rz-points",
        default="",
        help="Semicolon-separated r,z,repeat triples appended to the training set.",
    )
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--fd-step", type=float, default=1e-5)
    parser.add_argument("--damping", type=float, default=1e-3)
    parser.add_argument("--max-update-norm", type=float, default=0.05)
    args = parser.parse_args()

    if args.vanishing_edge_power <= 0.0:
        raise SystemExit("--vanishing-edge-power must be positive")
    interior_bump_q_centers = parse_float_list(args.interior_bump_q_centers)
    interior_bump_b2_centers = parse_float_list(args.interior_bump_b2_centers)
    interior_bump_kinds = parse_kind_list(args.interior_bump_kinds)
    if args.interior_bump_q_radius <= 0.0:
        raise SystemExit("--interior-bump-q-radius must be positive")
    if args.interior_bump_b2_radius <= 0.0:
        raise SystemExit("--interior-bump-b2-radius must be positive")

    labels = build_labels(
        args.q_order,
        args.b_order,
        args.edge_q_order,
        args.edge_b_order,
        args.edge_family,
        len(interior_bump_q_centers),
        len(interior_bump_b2_centers),
        interior_bump_kinds,
    )
    gamma, B, values = initial_values(labels, args.seed_json, args)
    candidate = Candidate(
        labels,
        values,
        gamma,
        args.vanishing_edge_power,
        interior_bump_q_centers,
        interior_bump_b2_centers,
        args.interior_bump_q_radius,
        args.interior_bump_b2_radius,
        args.interior_bump_shape,
        args.interior_bump_q_flatness,
    )
    points = make_points(args)
    variables = variable_indices(
        labels,
        args.freeze_monomial,
        args.freeze_edge_coeffs,
        fix_constants=not args.free_constants,
        bounded_shell_min=args.bounded_shell_min,
        freeze_tail_angular=args.freeze_tail_angular,
        monomial_min_q_order=args.monomial_min_q_order,
        freeze_interior_bumps=args.freeze_interior_bumps,
    )
    print(
        f"gamma={gamma} B={B} q_order={args.q_order} b_order={args.b_order} "
        f"bounded_edge_q_order={args.edge_q_order} bounded_edge_b_order={args.edge_b_order} "
        f"edge_family={args.edge_family} vanishing_edge_power={args.vanishing_edge_power} "
        f"points={len(points)} variables={len(variables)} freeze_monomial={args.freeze_monomial} "
        f"freeze_edge_coeffs={args.freeze_edge_coeffs} "
        f"zero_tail_angular={args.zero_tail_angular} "
        f"freeze_tail_angular={args.freeze_tail_angular} "
        f"monomial_min_q_order={args.monomial_min_q_order} "
        f"bounded_shell_min={args.bounded_shell_min} "
        f"interior_bump_q_count={len(interior_bump_q_centers)} "
        f"interior_bump_b2_count={len(interior_bump_b2_centers)} "
        f"interior_bump_kinds={','.join(interior_bump_kinds)} "
        f"interior_bump_shape={args.interior_bump_shape} "
        f"freeze_interior_bumps={args.freeze_interior_bumps} "
        f"fit_seed_edge={args.fit_seed_edge}"
    )
    candidate, score = solve(candidate, points, variables, args)
    print(f"\nfinal rms={score:.12e}")
    if args.save_json:
        save_seed(args.save_json, candidate, B, args, score)
        print(f"saved seed json: {args.save_json}")


if __name__ == "__main__":
    main()
