#!/usr/bin/env python3
"""Probe compactified profile residuals along far-tail q-slices.

The admissible vanishing-edge corrections preserve the exact q=0 conical
trace, but finite-box solves can still hide a defect by pushing it farther into
the tail. This diagnostic scans fixed-q slices, records the worst angular
location, and fits a log-log slope for the slice maxima.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_collocation import qb_to_rz
from compactified_profile import grid, load_seed_json_profile


@dataclass(frozen=True)
class SliceMetric:
    q: float
    b: float
    r: float
    z: float
    e_psi: float
    e_gamma: float
    rms: float

    @property
    def max_abs(self) -> float:
        return max(abs(self.e_psi), abs(self.e_gamma))


def slice_metric(
    profile,
    gamma: float,
    q: float,
    b_min: float,
    b_max: float,
    n_b: int,
    h: float,
) -> SliceMetric:
    worst: SliceMetric | None = None
    total = 0.0
    count = 0
    for b in grid(b_min, b_max, n_b):
        r, z = qb_to_rz(q, b)
        if r <= 2.0 * h:
            continue
        residual = residual_at(profile.psi, profile.swirl, gamma, r, z, h)
        total += residual.e_psi * residual.e_psi + residual.e_gamma * residual.e_gamma
        count += 2
        metric = SliceMetric(
            q=q,
            b=b,
            r=r,
            z=z,
            e_psi=residual.e_psi,
            e_gamma=residual.e_gamma,
            rms=0.0,
        )
        if worst is None or metric.max_abs > worst.max_abs:
            worst = metric
    if worst is None:
        raise ValueError(f"no valid points for q={q}")
    return SliceMetric(
        q=worst.q,
        b=worst.b,
        r=worst.r,
        z=worst.z,
        e_psi=worst.e_psi,
        e_gamma=worst.e_gamma,
        rms=math.sqrt(total / max(count, 1)),
    )


def fit_log_slope(metrics: list[SliceMetric]) -> tuple[float, float]:
    pairs = [(math.log(item.q), math.log(item.max_abs)) for item in metrics if item.max_abs > 0.0]
    if len(pairs) < 2:
        return math.nan, math.nan
    mean_x = sum(x for x, _y in pairs) / len(pairs)
    mean_y = sum(y for _x, y in pairs) / len(pairs)
    var_x = sum((x - mean_x) ** 2 for x, _y in pairs)
    if var_x == 0.0:
        return math.nan, math.nan
    slope = sum((x - mean_x) * (y - mean_y) for x, y in pairs) / var_x
    intercept = mean_y - slope * mean_x
    return slope, intercept


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--q-min", type=float, default=0.14)
    parser.add_argument("--q-max", type=float, default=0.30)
    parser.add_argument("--n-q", type=int, default=17)
    parser.add_argument("--b-min", type=float, default=-0.90)
    parser.add_argument("--b-max", type=float, default=0.90)
    parser.add_argument("--n-b", type=int, default=37)
    parser.add_argument("--h", type=float, default=1e-3)
    args = parser.parse_args()

    gamma, B, profile = load_seed_json_profile(args.seed_json)
    metrics = [
        slice_metric(profile, gamma, q, args.b_min, args.b_max, args.n_b, args.h)
        for q in grid(args.q_min, args.q_max, args.n_q)
    ]
    slope, intercept = fit_log_slope(metrics)

    print(f"seed={args.seed_json}")
    print(
        f"gamma={gamma} B={B} q=[{args.q_min},{args.q_max}] "
        f"n_q={args.n_q} b=[{args.b_min},{args.b_max}] n_b={args.n_b} h={args.h:.3e}"
    )
    print("q,max_abs,rms,b,r,z,e_psi,e_gamma")
    for metric in metrics:
        print(
            f"{metric.q:.12e},{metric.max_abs:.12e},{metric.rms:.12e},"
            f"{metric.b:.12e},{metric.r:.12e},{metric.z:.12e},"
            f"{metric.e_psi:.12e},{metric.e_gamma:.12e}"
        )
    print(f"loglog_slope={slope:.12e}")
    print(f"loglog_intercept={intercept:.12e}")


if __name__ == "__main__":
    main()
