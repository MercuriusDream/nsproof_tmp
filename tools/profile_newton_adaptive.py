#!/usr/bin/env python3
"""Adaptive hard-point driver for projected Chebyshev profile discovery.

This wraps two existing discovery tools:

* `profile_projected_hardpoints.py` logic to find current hard points in
  several compactified regions;
* `profile_newton_cheb.py` to run one constrained coefficient-space
  Gauss-Newton pass.

The important detail is that hard points are selected per region.  Otherwise
the origin/high-|b| edge can monopolize all active samples and the solver
forgets the low-|b| and secondary ridges.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from profile_projected_hardpoints import active_string, choose_points, scan_points


@dataclass(frozen=True)
class Region:
    name: str
    q_min: float
    q_max: float
    b_min: float
    b_max: float
    n_q: int
    n_b: int
    top: int
    base_weight: float


DEFAULT_REGIONS = (
    "origin:0.90,0.98,0.05,0.92,17,17,5,2.0;"
    "edge:0.12,0.89,0.55,0.92,23,17,5,2.0;"
    "focused:0.345,0.495,0.18,0.38,17,17,4,2.0;"
    "secondary:0.57,0.64,0.20,0.27,13,13,4,2.0"
)


def parse_regions(raw: str) -> tuple[Region, ...]:
    regions: list[Region] = []
    for item in raw.split(";"):
        if not item.strip():
            continue
        if ":" not in item:
            raise ValueError(f"bad region {item!r}; expected name:q0,q1,b0,b1,nq,nb,top,weight")
        name, spec = item.split(":", 1)
        parts = [part.strip() for part in spec.split(",") if part.strip()]
        if len(parts) != 8:
            raise ValueError(f"bad region {item!r}; expected 8 comma-separated values")
        regions.append(
            Region(
                name=name.strip(),
                q_min=float(parts[0]),
                q_max=float(parts[1]),
                b_min=float(parts[2]),
                b_max=float(parts[3]),
                n_q=int(parts[4]),
                n_b=int(parts[5]),
                top=int(parts[6]),
                base_weight=float(parts[7]),
            )
        )
    if not regions:
        raise ValueError("at least one region is required")
    return tuple(regions)


def hardpoints_for_region(args: argparse.Namespace, profile_path: str, region: Region) -> str:
    scan_args = argparse.Namespace(
        profile=profile_path,
        q_min=region.q_min,
        q_max=region.q_max,
        b_min=region.b_min,
        b_max=region.b_max,
        n_q=region.n_q,
        n_b=region.n_b,
        h=args.h,
        residual_kind=args.residual_kind,
        top=region.top,
        min_dq=args.min_dq,
        min_db=args.min_db,
        base_weight=region.base_weight,
        weight_power=args.weight_power,
        min_weight=args.min_weight,
    )
    _profile, points, skipped = scan_points(scan_args)
    selected = choose_points(points, region.top, args.min_dq, args.min_db)
    print(
        f"region={region.name} grid={region.n_q}x{region.n_b} points={len(points)} "
        f"skipped={skipped} selected={len(selected)}"
    )
    for index, point in enumerate(selected, start=1):
        print(
            f"  {index:02d} q={point.q:.12g} b={point.b:.12g} "
            f"max_abs={point.max_abs:.12e}"
        )
    return active_string(selected, region.base_weight, args.weight_power, args.min_weight)


def append_points(*chunks: str) -> str:
    items: list[str] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        if not chunk.strip():
            continue
        for item in chunk.split(";"):
            if not item.strip():
                continue
            parts = item.split(",")
            if len(parts) < 2:
                continue
            key = (parts[0], parts[1])
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return ";".join(items)


def run_newton(args: argparse.Namespace, input_path: str, output_path: str, active_points: str) -> None:
    cmd = [
        sys.executable,
        os.path.join(TOOLS_DIR, "profile_newton_cheb.py"),
        "--input",
        input_path,
        "--out",
        output_path,
        "--blocks",
        args.blocks,
        "--q-min",
        str(args.q_min),
        "--q-max",
        str(args.q_max),
        "--b-min",
        str(args.b_min),
        "--b-max",
        str(args.b_max),
        "--n-q",
        str(args.n_q),
        "--n-b",
        str(args.n_b),
        "--active-qb-points",
        active_points,
        "--var-q-min",
        str(args.var_q_min),
        "--var-q-max",
        str(args.var_q_max),
        "--var-x-min",
        str(args.var_x_min),
        "--var-x-max",
        str(args.var_x_max),
        "--max-mode-q",
        str(args.max_mode_q),
        "--max-mode-x",
        str(args.max_mode_x),
        "--max-variables",
        str(args.max_variables),
        "--iterations",
        str(args.inner_iterations),
        "--fd-step",
        str(args.fd_step),
        "--damping",
        str(args.damping),
        "--max-update-norm",
        str(args.max_update_norm),
        "--line-search",
        args.line_search,
        "--residual-kind",
        args.residual_kind,
        "--continuity-weight",
        str(args.continuity_weight),
        "--continuity-samples",
        str(args.continuity_samples),
        "--origin-match-weight",
        str(args.origin_match_weight),
        "--origin-match-q",
        args.origin_match_q,
        "--origin-match-x-samples",
        str(args.origin_match_x_samples),
        "--d1-weight",
        str(args.d1_weight),
        "--d2-weight",
        str(args.d2_weight),
        "--derivative-step-q",
        str(args.derivative_step_q),
        "--derivative-step-b",
        str(args.derivative_step_b),
    ]
    if args.include_constant:
        cmd.append("--include-constant")
    print("running_newton=" + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-prefix", required=True)
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--regions", default=DEFAULT_REGIONS)
    parser.add_argument("--baseline-active-qb-points", default="")
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--min-dq", type=float, default=0.015)
    parser.add_argument("--min-db", type=float, default=0.015)
    parser.add_argument("--weight-power", type=float, default=2.0)
    parser.add_argument("--min-weight", type=float, default=1.0)
    parser.add_argument("--blocks", default="F_an,G_an,F_frac0,G_frac0,F_origin,G_origin")
    parser.add_argument("--q-min", type=float, default=0.38)
    parser.add_argument("--q-max", type=float, default=0.89)
    parser.add_argument("--b-min", type=float, default=0.18)
    parser.add_argument("--b-max", type=float, default=0.92)
    parser.add_argument("--n-q", type=int, default=5)
    parser.add_argument("--n-b", type=int, default=5)
    parser.add_argument("--var-q-min", type=float, default=0.34)
    parser.add_argument("--var-q-max", type=float, default=1.0)
    parser.add_argument("--var-x-min", type=float, default=0.0)
    parser.add_argument("--var-x-max", type=float, default=1.0)
    parser.add_argument("--max-mode-q", type=int, default=2)
    parser.add_argument("--max-mode-x", type=int, default=2)
    parser.add_argument("--include-constant", action="store_true")
    parser.add_argument("--max-variables", type=int, default=96)
    parser.add_argument("--inner-iterations", type=int, default=1)
    parser.add_argument("--fd-step", type=float, default=1e-6)
    parser.add_argument("--damping", type=float, default=0.2)
    parser.add_argument("--max-update-norm", type=float, default=0.1)
    parser.add_argument("--line-search", default="1,0.5,0.25,0.125,0.0625")
    parser.add_argument("--continuity-weight", type=float, default=0.25)
    parser.add_argument("--continuity-samples", type=int, default=2)
    parser.add_argument("--origin-match-weight", type=float, default=0.25)
    parser.add_argument("--origin-match-q", default="0.9")
    parser.add_argument("--origin-match-x-samples", type=int, default=5)
    parser.add_argument("--d1-weight", type=float, default=0.0)
    parser.add_argument("--d2-weight", type=float, default=0.0)
    parser.add_argument("--derivative-step-q", type=float, default=0.005)
    parser.add_argument("--derivative-step-b", type=float, default=0.005)
    args = parser.parse_args()

    regions = parse_regions(args.regions)
    current = args.input
    for round_index in range(args.rounds):
        print(f"adaptive_round={round_index} input={current}")
        chunks = [args.baseline_active_qb_points]
        for region in regions:
            chunks.append(hardpoints_for_region(args, current, region))
        active_points = append_points(*chunks)
        print("active_qb_points=" + active_points)
        output = f"{args.out_prefix}-round{round_index + 1}.json"
        run_newton(args, current, output, active_points)
        current = output
    print(f"final_profile={current}")
    print("status=ADAPTIVE_DISCOVERY_NOT_VALIDATION")


if __name__ == "__main__":
    main()
