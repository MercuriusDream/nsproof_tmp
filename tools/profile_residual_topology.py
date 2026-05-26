#!/usr/bin/env python3
"""Inspect where compactified profile residuals concentrate.

The gate runner reports one worst point.  This diagnostic keeps the top
residuals and slice maxima in ``(q,b)`` so the next basis change is guided by
the observed defect geometry instead of a single grid point.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_collocation import qb_to_rz
from compactified_profile import grid, load_seed_json_profile


@dataclass(frozen=True)
class PointResidual:
    q: float
    b: float
    r: float
    z: float
    e_psi: float
    e_gamma: float

    @property
    def max_abs(self) -> float:
        return max(abs(self.e_psi), abs(self.e_gamma))


def scan_points(args: argparse.Namespace) -> tuple[float, float, list[PointResidual]]:
    gamma, B, profile = load_seed_json_profile(args.seed_json)
    points: list[PointResidual] = []
    for q in grid(args.q_min, args.q_max, args.n_q):
        for b in grid(args.b_min, args.b_max, args.n_b):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * args.h:
                continue
            residual = residual_at(profile.psi, profile.swirl, gamma, r, z, args.h)
            points.append(
                PointResidual(
                    q=q,
                    b=b,
                    r=r,
                    z=z,
                    e_psi=residual.e_psi,
                    e_gamma=residual.e_gamma,
                )
            )
    return gamma, B, points


def rms(points: list[PointResidual]) -> float:
    total = sum(point.e_psi * point.e_psi + point.e_gamma * point.e_gamma for point in points)
    return math.sqrt(total / max(2 * len(points), 1))


def print_point(prefix: str, point: PointResidual) -> None:
    print(
        f"{prefix} q={point.q:.6f} b={point.b:.6f} "
        f"r={point.r:.6f} z={point.z:.6f} "
        f"e_psi={point.e_psi:.12e} e_gamma={point.e_gamma:.12e} "
        f"max={point.max_abs:.12e}"
    )


def slice_maxima(points: list[PointResidual], axis: str) -> list[PointResidual]:
    buckets: dict[float, PointResidual] = {}
    for point in points:
        key = point.q if axis == "q" else point.b
        old = buckets.get(key)
        if old is None or point.max_abs > old.max_abs:
            buckets[key] = point
    return [buckets[key] for key in sorted(buckets)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--q-min", type=float, default=0.25)
    parser.add_argument("--q-max", type=float, default=0.90)
    parser.add_argument("--b-min", type=float, default=-0.90)
    parser.add_argument("--b-max", type=float, default=0.90)
    parser.add_argument("--n-q", type=int, default=17)
    parser.add_argument("--n-b", type=int, default=17)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--slice-top", type=int, default=8)
    args = parser.parse_args()

    gamma, B, points = scan_points(args)
    points_by_size = sorted(points, key=lambda point: point.max_abs, reverse=True)
    print(f"seed={args.seed_json}")
    print(
        f"gamma={gamma} B={B} q=[{args.q_min},{args.q_max}] "
        f"b=[{args.b_min},{args.b_max}] grid={args.n_q}x{args.n_b} "
        f"points={len(points)} h={args.h:.3e}"
    )
    print(f"rms={rms(points):.12e}")
    print("top residual points:")
    for index, point in enumerate(points_by_size[: args.top], start=1):
        print_point(f"  {index:02d}", point)

    print("worst by q-slice:")
    q_slices = sorted(slice_maxima(points, "q"), key=lambda point: point.max_abs, reverse=True)
    for index, point in enumerate(q_slices[: args.slice_top], start=1):
        print_point(f"  {index:02d}", point)

    print("worst by b-slice:")
    b_slices = sorted(slice_maxima(points, "b"), key=lambda point: point.max_abs, reverse=True)
    for index, point in enumerate(b_slices[: args.slice_top], start=1):
        print_point(f"  {index:02d}", point)


if __name__ == "__main__":
    main()
