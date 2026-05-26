#!/usr/bin/env python3
"""First-pass finite-difference spectrum probe for a compactified profile.

This is a rough diagnostic scaffold, not a validator. It linearizes the
existing residual_at map on a small physical (r,z) tensor grid by perturbing
nodal psi/Gamma values with bilinear interpolation.
"""

from __future__ import annotations

import argparse
from typing import Any, Callable

from axisym_residual import Residual, residual_at
from compactified_profile import load_seed_json_profile


Field = Callable[[float, float], float]

WARNING = (
    "WARNING: this is only a bounded first-pass spectral sanity probe. "
    "Pressure projection and geometric-mode correctness are not handled yet; "
    "do not treat these eigenvalues as proof or validation data."
)


def require_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit(
            "numpy is required for tools/linearized_spectrum_probe.py; "
            "install numpy or run this probe in an environment where it is available."
        ) from exc
    return np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute a rough finite-difference spectrum of residual_at on a small physical grid."
    )
    parser.add_argument("--seed-json", required=True, help="compactified seed JSON profile")
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n-r", type=int, default=4)
    parser.add_argument("--n-z", type=int, default=4)
    parser.add_argument("--h", type=float, default=1e-3, help="residual_at finite-difference step")
    parser.add_argument(
        "--epsilon",
        type=float,
        default=1e-6,
        help="central perturbation size for nodal psi/Gamma values",
    )
    parser.add_argument("--top", type=int, default=8, help="number of rightmost eigenvalues to print")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.n_r < 2 or args.n_z < 2:
        raise SystemExit("--n-r and --n-z must both be at least 2")
    if args.r_min >= args.r_max:
        raise SystemExit("--r-min must be less than --r-max")
    if args.z_min >= args.z_max:
        raise SystemExit("--z-min must be less than --z-max")
    if args.h <= 0.0:
        raise SystemExit("--h must be positive")
    if args.epsilon <= 0.0:
        raise SystemExit("--epsilon must be positive")
    if args.top <= 0:
        raise SystemExit("--top must be positive")
    if args.r_min <= 2.0 * args.h:
        raise SystemExit("--r-min must be greater than 2*h so residual_at stays away from the axis")


def bilinear_value(np: Any, r_grid: Any, z_grid: Any, values: Any, r: float, z: float) -> float:
    if r < r_grid[0] or r > r_grid[-1] or z < z_grid[0] or z > z_grid[-1]:
        return 0.0

    i = int(np.searchsorted(r_grid, r, side="right") - 1)
    j = int(np.searchsorted(z_grid, z, side="right") - 1)
    i = min(max(i, 0), len(r_grid) - 2)
    j = min(max(j, 0), len(z_grid) - 2)

    r0 = float(r_grid[i])
    r1 = float(r_grid[i + 1])
    z0 = float(z_grid[j])
    z1 = float(z_grid[j + 1])
    tr = 0.0 if r1 == r0 else (r - r0) / (r1 - r0)
    tz = 0.0 if z1 == z0 else (z - z0) / (z1 - z0)

    v00 = values[i, j]
    v10 = values[i + 1, j]
    v01 = values[i, j + 1]
    v11 = values[i + 1, j + 1]
    return float(
        (1.0 - tr) * (1.0 - tz) * v00
        + tr * (1.0 - tz) * v10
        + (1.0 - tr) * tz * v01
        + tr * tz * v11
    )


def make_perturbed_field(
    np: Any,
    base: Field,
    r_grid: Any,
    z_grid: Any,
    values: Any,
    sign: float,
) -> Field:
    def field(r: float, z: float) -> float:
        return base(r, z) + sign * bilinear_value(np, r_grid, z_grid, values, r, z)

    return field


def residual_vector(np: Any, psi: Field, swirl: Field, gamma: float, points: list[tuple[float, float]], h: float) -> Any:
    out = np.empty(2 * len(points), dtype=float)
    for k, (r, z) in enumerate(points):
        res: Residual = residual_at(psi, swirl, gamma, r, z, h)
        out[2 * k] = res.e_psi
        out[2 * k + 1] = res.e_gamma
    return out


def nodal_values(np: Any, n_r: int, n_z: int, flat_index: int, epsilon: float) -> Any:
    values = np.zeros((n_r, n_z), dtype=float)
    i = flat_index // n_z
    j = flat_index % n_z
    values[i, j] = epsilon
    return values


def build_linearization(
    np: Any,
    profile: Any,
    gamma: float,
    r_grid: Any,
    z_grid: Any,
    h: float,
    epsilon: float,
) -> Any:
    n_r = len(r_grid)
    n_z = len(z_grid)
    point_count = n_r * n_z
    size = 2 * point_count
    matrix = np.empty((size, size), dtype=float)
    points = [(float(r), float(z)) for r in r_grid for z in z_grid]
    zeros = np.zeros((n_r, n_z), dtype=float)
    psi_base: Field = profile.psi
    swirl_base: Field = profile.swirl

    psi_zero = make_perturbed_field(np, psi_base, r_grid, z_grid, zeros, 1.0)
    swirl_zero = make_perturbed_field(np, swirl_base, r_grid, z_grid, zeros, 1.0)
    base_residual = residual_vector(np, psi_zero, swirl_zero, gamma, points, h)

    for col in range(size):
        nodal_index = col // 2
        is_swirl_column = col % 2 == 1
        values = nodal_values(np, n_r, n_z, nodal_index, epsilon)

        if is_swirl_column:
            psi_plus = psi_zero
            psi_minus = psi_zero
            swirl_plus = make_perturbed_field(np, swirl_base, r_grid, z_grid, values, 1.0)
            swirl_minus = make_perturbed_field(np, swirl_base, r_grid, z_grid, values, -1.0)
        else:
            psi_plus = make_perturbed_field(np, psi_base, r_grid, z_grid, values, 1.0)
            psi_minus = make_perturbed_field(np, psi_base, r_grid, z_grid, values, -1.0)
            swirl_plus = swirl_zero
            swirl_minus = swirl_zero

        plus = residual_vector(np, psi_plus, swirl_plus, gamma, points, h)
        minus = residual_vector(np, psi_minus, swirl_minus, gamma, points, h)
        matrix[:, col] = (plus - minus) / (2.0 * epsilon)

    base_norm = float(np.linalg.norm(base_residual, ord=np.inf))
    return matrix, base_norm, points


def format_eigenvalue(value: complex) -> str:
    sign = "+" if value.imag >= 0.0 else "-"
    return f"{value.real:.12e} {sign} {abs(value.imag):.12e}i"


def main() -> None:
    args = parse_args()
    validate_args(args)
    np = require_numpy()

    gamma, B, profile = load_seed_json_profile(args.seed_json)
    r_grid = np.linspace(args.r_min, args.r_max, args.n_r)
    z_grid = np.linspace(args.z_min, args.z_max, args.n_z)

    matrix, base_norm, points = build_linearization(
        np=np,
        profile=profile,
        gamma=gamma,
        r_grid=r_grid,
        z_grid=z_grid,
        h=args.h,
        epsilon=args.epsilon,
    )
    eigvals = np.linalg.eigvals(matrix)
    order = np.argsort(eigvals.real)[::-1]
    top = min(args.top, len(eigvals))

    print(WARNING)
    print(f"seed={args.seed_json}")
    print(f"gamma={gamma} B={B}")
    print(
        f"grid r=[{args.r_min}, {args.r_max}] n-r={args.n_r}; "
        f"z=[{args.z_min}, {args.z_max}] n-z={args.n_z}; points={len(points)}"
    )
    print(f"h={args.h:.12e} epsilon={args.epsilon:.12e}")
    print(f"matrix_shape={matrix.shape[0]}x{matrix.shape[1]} base_residual_inf={base_norm:.12e}")
    print(f"rightmost_eigenvalues top={top}")
    for rank, idx in enumerate(order[:top], start=1):
        print(f"  {rank:2d}: {format_eigenvalue(complex(eigvals[idx]))}")


if __name__ == "__main__":
    main()
