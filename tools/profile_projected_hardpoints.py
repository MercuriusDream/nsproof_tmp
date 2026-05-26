#!/usr/bin/env python3
"""Find hard collocation points for projected transseries-Chebyshev profiles.

This implements the adaptive-sampling idea from the unstable-singularity
workflow in a deterministic, scriptable form: scan a compactified validation
grid, rank points by the selected residual quotient, and emit a
`--active-qb-points` string for `profile_newton_cheb.py`.

It is a discovery helper, not a proof validator.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from compactified_collocation import qb_to_rz
from compactified_profile import grid
from validators.compactified_equations import (
    ProjectedProfile,
    RESIDUAL_KINDS,
    compactified_residual_defined,
    residual_with_kind,
)


@dataclass(frozen=True)
class HardPoint:
    q: float
    b: float
    r: float
    z: float
    e_psi: float
    e_gamma: float

    @property
    def max_abs(self) -> float:
        return max(abs(self.e_psi), abs(self.e_gamma))


def separated(point: HardPoint, selected: list[HardPoint], min_dq: float, min_db: float) -> bool:
    for old in selected:
        if abs(point.q - old.q) < min_dq and abs(point.b - old.b) < min_db:
            return False
    return True


def scan_points(args: argparse.Namespace) -> tuple[ProjectedProfile, list[HardPoint], int]:
    profile = ProjectedProfile.load(args.profile)
    points: list[HardPoint] = []
    skipped = 0
    for q in grid(args.q_min, args.q_max, args.n_q):
        for b in grid(args.b_min, args.b_max, args.n_b):
            if not compactified_residual_defined(q, b, profile.p, args.residual_kind):
                skipped += 1
                continue
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * args.h:
                skipped += 1
                continue
            raw = profile.exact_residual_at(r, z)
            residual = residual_with_kind(raw, q, b, profile.p, args.residual_kind)
            points.append(
                HardPoint(
                    q=q,
                    b=b,
                    r=r,
                    z=z,
                    e_psi=residual.e_psi,
                    e_gamma=residual.e_gamma,
                )
            )
    return profile, points, skipped


def choose_points(points: list[HardPoint], top: int, min_dq: float, min_db: float) -> list[HardPoint]:
    selected: list[HardPoint] = []
    for point in sorted(points, key=lambda item: item.max_abs, reverse=True):
        if separated(point, selected, min_dq, min_db):
            selected.append(point)
        if len(selected) >= top:
            break
    return selected


def active_string(points: list[HardPoint], base_weight: float, power: float, min_weight: float) -> str:
    if not points:
        return ""
    max_value = max(point.max_abs for point in points)
    items: list[str] = []
    for point in points:
        ratio = point.max_abs / max(max_value, 1e-300)
        weight = max(min_weight, base_weight * (ratio**power))
        items.append(f"{point.q:.12g},{point.b:.12g},{weight:.12g}")
    return ";".join(items)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--q-min", type=float, default=0.12)
    parser.add_argument("--q-max", type=float, default=0.98)
    parser.add_argument("--b-min", type=float, default=0.03)
    parser.add_argument("--b-max", type=float, default=0.92)
    parser.add_argument("--n-q", type=int, default=31)
    parser.add_argument("--n-b", type=int, default=31)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--residual-kind", choices=RESIDUAL_KINDS, default="normalized-structural")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--min-dq", type=float, default=0.015)
    parser.add_argument("--min-db", type=float, default=0.015)
    parser.add_argument("--base-weight", type=float, default=4.0)
    parser.add_argument("--weight-power", type=float, default=2.0)
    parser.add_argument("--min-weight", type=float, default=1.0)
    args = parser.parse_args()

    profile, points, skipped = scan_points(args)
    selected = choose_points(points, args.top, args.min_dq, args.min_db)
    print(f"profile={args.profile}")
    print(f"gamma={profile.gamma:.15g} B={profile.B:.15g} p={profile.p:.15g}")
    print(
        f"grid={args.n_q}x{args.n_b} points={len(points)} skipped={skipped} "
        f"q=[{args.q_min},{args.q_max}] b=[{args.b_min},{args.b_max}] "
        f"residual_kind={args.residual_kind}"
    )
    print("top separated hard points:")
    for index, point in enumerate(selected, start=1):
        print(
            f"  {index:02d} q={point.q:.12g} b={point.b:.12g} "
            f"r={point.r:.12g} z={point.z:.12g} "
            f"e_psi={point.e_psi:.12e} e_gamma={point.e_gamma:.12e} "
            f"max_abs={point.max_abs:.12e}"
        )
    print("active_qb_points=" + active_string(selected, args.base_weight, args.weight_power, args.min_weight))
    print("status=HARDPOINT_DISCOVERY_NOT_VALIDATION")


if __name__ == "__main__":
    main()
