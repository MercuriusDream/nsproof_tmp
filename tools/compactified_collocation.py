#!/usr/bin/env python3
"""Evaluate profile residuals on compactified (q,b) collocation grids."""

from __future__ import annotations

import argparse
import math

from axisym_residual import Residual, residual_at
from compactified_profile import CompactifiedProfile, load_seed_json_profile, grid


def qb_to_rz(q: float, b: float) -> tuple[float, float]:
    rho = math.sqrt(1.0 / (q * q) - 1.0)
    r = rho * math.sqrt(max(0.0, 1.0 - b * b))
    z = rho * b
    return r, z


def scan_qb(
    profile: CompactifiedProfile,
    gamma: float,
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
) -> tuple[Residual, tuple[float, float, float, float], float, int]:
    worst = Residual(0.0, 0.0)
    worst_point = (q_min, b_min, 0.0, 0.0)
    total = 0.0
    count = 0
    point_count = 0
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h:
                continue
            res = residual_at(profile.psi, profile.swirl, gamma, r, z, h)
            total += res.e_psi * res.e_psi + res.e_gamma * res.e_gamma
            count += 2
            point_count += 1
            if res.max_abs > worst.max_abs:
                worst = res
                worst_point = (q, b, r, z)
    rms = math.sqrt(total / max(count, 1))
    return worst, worst_point, rms, point_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--q-min", type=float, default=0.35)
    parser.add_argument("--q-max", type=float, default=0.9)
    parser.add_argument("--b-min", type=float, default=-0.8)
    parser.add_argument("--b-max", type=float, default=0.8)
    parser.add_argument("--n-q", type=int, default=9)
    parser.add_argument("--n-b", type=int, default=9)
    parser.add_argument("--h", type=float, default=1e-3)
    args = parser.parse_args()

    gamma, B, profile = load_seed_json_profile(args.seed_json)
    worst, point, rms, point_count = scan_qb(
        profile,
        gamma=gamma,
        q_min=args.q_min,
        q_max=args.q_max,
        b_min=args.b_min,
        b_max=args.b_max,
        n_q=args.n_q,
        n_b=args.n_b,
        h=args.h,
    )
    q, b, r, z = point
    print(f"seed={args.seed_json}")
    print(f"gamma={gamma} B={B} q-grid={args.n_q} b-grid={args.n_b} points={point_count}")
    print(f"q in [{args.q_min}, {args.q_max}], b in [{args.b_min}, {args.b_max}]")
    print(f"worst q={q:.6f} b={b:.6f} r={r:.6f} z={z:.6f}")
    print(f"  psi-equation residual   = {worst.e_psi:.12e}")
    print(f"  Gamma-equation residual = {worst.e_gamma:.12e}")
    print(f"  max abs residual        = {worst.max_abs:.12e}")
    print(f"  RMS residual            = {rms:.12e}")


if __name__ == "__main__":
    main()
