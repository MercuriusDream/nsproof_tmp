#!/usr/bin/env python3
"""Run the standard residual gates for a compactified profile seed.

This is a reporting harness, not a solver. It keeps the profile checks used in
the proof ledger reproducible and compact:

  * wide compactified edge grid,
  * interior compactified grid,
  * local physical rectangle.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from compactified_collocation import scan_qb
from compactified_profile import load_seed_json_profile, scan_residual


@dataclass(frozen=True)
class Gate:
    name: str
    h: float
    max_abs: float
    rms: float
    e_psi: float
    e_gamma: float
    where: str


def parse_h_values(raw: str) -> list[float]:
    values = [float(item) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one h value is required")
    return values


def run_gates(args: argparse.Namespace, h: float) -> list[Gate]:
    gamma, _B, profile = load_seed_json_profile(args.seed_json)

    wide_worst, wide_point, wide_rms, _ = scan_qb(
        profile,
        gamma=gamma,
        q_min=args.wide_q_min,
        q_max=args.wide_q_max,
        b_min=args.wide_b_min,
        b_max=args.wide_b_max,
        n_q=args.wide_n_q,
        n_b=args.wide_n_b,
        h=h,
    )
    wq, wb, wr, wz = wide_point

    interior_worst, interior_point, interior_rms, _ = scan_qb(
        profile,
        gamma=gamma,
        q_min=args.interior_q_min,
        q_max=args.interior_q_max,
        b_min=args.interior_b_min,
        b_max=args.interior_b_max,
        n_q=args.interior_n_q,
        n_b=args.interior_n_b,
        h=h,
    )
    iq, ib, ir, iz = interior_point

    local_worst, local_point, local_rms = scan_residual(
        profile,
        gamma=gamma,
        r_min=args.local_r_min,
        r_max=args.local_r_max,
        z_min=args.local_z_min,
        z_max=args.local_z_max,
        n=args.local_n,
        h=h,
    )
    lr, lz = local_point

    return [
        Gate(
            name="wide",
            h=h,
            max_abs=wide_worst.max_abs,
            rms=wide_rms,
            e_psi=wide_worst.e_psi,
            e_gamma=wide_worst.e_gamma,
            where=f"q={wq:.6f} b={wb:.6f} r={wr:.6f} z={wz:.6f}",
        ),
        Gate(
            name="interior",
            h=h,
            max_abs=interior_worst.max_abs,
            rms=interior_rms,
            e_psi=interior_worst.e_psi,
            e_gamma=interior_worst.e_gamma,
            where=f"q={iq:.6f} b={ib:.6f} r={ir:.6f} z={iz:.6f}",
        ),
        Gate(
            name="local",
            h=h,
            max_abs=local_worst.max_abs,
            rms=local_rms,
            e_psi=local_worst.e_psi,
            e_gamma=local_worst.e_gamma,
            where=f"r={lr:.6f} z={lz:.6f}",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--h-values", default="1e-3")
    parser.add_argument("--wide-q-min", type=float, default=0.35)
    parser.add_argument("--wide-q-max", type=float, default=0.9)
    parser.add_argument("--wide-b-min", type=float, default=-0.8)
    parser.add_argument("--wide-b-max", type=float, default=0.8)
    parser.add_argument("--wide-n-q", type=int, default=15)
    parser.add_argument("--wide-n-b", type=int, default=15)
    parser.add_argument("--interior-q-min", type=float, default=0.45)
    parser.add_argument("--interior-q-max", type=float, default=0.85)
    parser.add_argument("--interior-b-min", type=float, default=-0.65)
    parser.add_argument("--interior-b-max", type=float, default=0.65)
    parser.add_argument("--interior-n-q", type=int, default=15)
    parser.add_argument("--interior-n-b", type=int, default=15)
    parser.add_argument("--local-r-min", type=float, default=0.8)
    parser.add_argument("--local-r-max", type=float, default=2.0)
    parser.add_argument("--local-z-min", type=float, default=-1.0)
    parser.add_argument("--local-z-max", type=float, default=1.0)
    parser.add_argument("--local-n", type=int, default=23)
    args = parser.parse_args()

    print(f"seed={args.seed_json}")
    print("gate,h,max_abs,rms,e_psi,e_gamma,where")
    for h in parse_h_values(args.h_values):
        for gate in run_gates(args, h):
            print(
                f"{gate.name},{gate.h:.6e},{gate.max_abs:.12e},{gate.rms:.12e},"
                f"{gate.e_psi:.12e},{gate.e_gamma:.12e},{gate.where}"
            )


if __name__ == "__main__":
    main()
