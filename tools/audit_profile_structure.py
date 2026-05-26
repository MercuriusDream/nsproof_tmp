#!/usr/bin/env python3
"""Read-only structural audit for proof-native projected profiles.

This bundles the current non-interval checks that must pass before more solver
time is meaningful: formal tail metadata, exact patch/origin mortar, and
normalized residual topology.  It deliberately reports failures instead of
mutating coefficients.
"""

from __future__ import annotations

import argparse
import json
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
from profile_mortar_audit import constraint_diff, summarize
from profile_newton_cheb import (
    build_origin_matching_constraints,
    build_patch_continuity_constraints,
    load_json,
    parse_blocks,
    parse_q_values,
)
from validators.compactified_equations import (
    ProjectedProfile,
    RESIDUAL_KINDS,
    compactified_residual_defined,
    residual_with_kind,
)
from validators.tail_transseries import validate_projection


@dataclass(frozen=True)
class ResidualPoint:
    q: float
    b: float
    r: float
    z: float
    e_psi: float
    e_gamma: float

    @property
    def max_abs(self) -> float:
        return max(abs(self.e_psi), abs(self.e_gamma))


def scan_residuals(
    profile: ProjectedProfile,
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    residual_kind: str,
    h: float,
) -> tuple[list[ResidualPoint], int]:
    points: list[ResidualPoint] = []
    skipped = 0
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            if not compactified_residual_defined(q, b, profile.p, residual_kind):
                skipped += 1
                continue
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h:
                skipped += 1
                continue
            raw = profile.exact_residual_at(r, z)
            residual = residual_with_kind(raw, q, b, profile.p, residual_kind)
            points.append(ResidualPoint(q, b, r, z, residual.e_psi, residual.e_gamma))
    return points, skipped


def residual_summary(points: list[ResidualPoint], top: int, q_switch: float, switch_tol: float) -> dict[str, object]:
    if not points:
        return {
            "count": 0,
            "max_abs": 0.0,
            "rms": 0.0,
            "top": [],
            "top_at_switch": 0,
        }
    total = sum(point.e_psi * point.e_psi + point.e_gamma * point.e_gamma for point in points)
    selected = sorted(points, key=lambda point: point.max_abs, reverse=True)[:top]
    return {
        "count": len(points),
        "max_abs": max(point.max_abs for point in points),
        "rms": math.sqrt(total / (2 * len(points))),
        "top_at_switch": sum(1 for point in selected if abs(point.q - q_switch) <= switch_tol),
        "top": [
            {
                "q": point.q,
                "b": point.b,
                "r": point.r,
                "z": point.z,
                "e_psi": point.e_psi,
                "e_gamma": point.e_gamma,
                "max_abs": point.max_abs,
                "at_switch": abs(point.q - q_switch) <= switch_tol,
            }
            for point in selected
        ],
    }


def origin_q_min(data: dict[str, object]) -> float:
    blocks = data["blocks"]  # type: ignore[index]
    values: list[float] = []
    for key in ("F_origin_taylor", "G_origin_taylor"):
        item = blocks.get(key, {})  # type: ignore[union-attr]
        if isinstance(item, dict) and item.get("enabled", False):
            values.append(float(item["q_min"]))
    return min(values) if values else 2.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--blocks", default="F_an,G_an,F_frac0,G_frac0")
    parser.add_argument("--continuity-samples", type=int, default=3)
    parser.add_argument("--continuity-derivative-order", type=int, default=2)
    parser.add_argument("--origin-match-q", default="0.9")
    parser.add_argument("--origin-match-x-samples", type=int, default=7)
    parser.add_argument("--origin-match-derivative-order", type=int, default=2)
    parser.add_argument("--residual-kind", choices=RESIDUAL_KINDS, default="normalized-structural")
    parser.add_argument("--q-min", type=float, default=0.88)
    parser.add_argument("--q-max", type=float, default=0.98)
    parser.add_argument("--b-min", type=float, default=0.05)
    parser.add_argument("--b-max", type=float, default=0.92)
    parser.add_argument("--n-q", type=int, default=41)
    parser.add_argument("--n-b", type=int, default=41)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--switch-tol", type=float, default=1e-12)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    data = load_json(args.profile)
    tail = validate_projection(args.profile, q1_tol=1e-14, forced_tol=1e-12)
    blocks = parse_blocks(args.blocks)
    constraints = tuple(
        build_patch_continuity_constraints(
            data,
            blocks,
            samples=args.continuity_samples,
            weight=1.0,
            derivative_order=args.continuity_derivative_order,
            derivative_weight=1.0,
            derivative_step=1e-4,
        )
        + build_origin_matching_constraints(
            data,
            q_values=parse_q_values(args.origin_match_q),
            x_samples=args.origin_match_x_samples,
            weight=1.0,
            derivative_order=args.origin_match_derivative_order,
            derivative_weight=1.0,
            derivative_step=1e-4,
        )
    )
    mortar_diffs = [constraint_diff(data, constraint) for constraint in constraints]
    mortar = summarize(constraints, mortar_diffs)
    q_switch = origin_q_min(data)
    profile = ProjectedProfile.load(args.profile)
    residual_points, skipped = scan_residuals(
        profile,
        q_min=args.q_min,
        q_max=args.q_max,
        b_min=args.b_min,
        b_max=args.b_max,
        n_q=args.n_q,
        n_b=args.n_b,
        residual_kind=args.residual_kind,
        h=args.h,
    )
    residual = residual_summary(residual_points, args.top, q_switch, args.switch_tol)
    report = {
        "profile": args.profile,
        "tail": {
            "in_wedge": tail.in_wedge,
            "ordinary_q1_F_max": tail.q1_f_max,
            "ordinary_q1_G_max": tail.q1_g_max,
            "forced_qp_coeff_error": tail.forced_qp_coeff_error,
            "tail_structural_ok": tail.tail_ok,
            "projection_sampling_ok": tail.projection_ok,
            "origin_taylor_ok": tail.origin_ok,
            "origin_F_fit_error": tail.origin_f_error,
            "origin_G_fit_error": tail.origin_g_error,
        },
        "mortar": mortar,
        "residual": {
            "kind": args.residual_kind,
            "q_range": [args.q_min, args.q_max],
            "b_range": [args.b_min, args.b_max],
            "grid": [args.n_q, args.n_b],
            "skipped": skipped,
            **residual,
        },
        "origin_switch_q": q_switch,
        "status": "STRUCTURE_AUDIT_NOT_INTERVAL_VALIDATION",
    }
    print(f"profile={args.profile}")
    print(f"tail_ok={tail.tail_ok} projection_ok={tail.projection_ok} origin_ok={tail.origin_ok}")
    print(f"q1_F={tail.q1_f_max:.12e} q1_G={tail.q1_g_max:.12e}")
    print(f"forced_qp_coeff_error={tail.forced_qp_coeff_error:.12e}")
    print(f"origin_fit_F={tail.origin_f_error:.12e} origin_fit_G={tail.origin_g_error:.12e}")
    print(f"mortar_constraints={mortar['count']} mortar_max_abs={mortar['max_abs']:.12e} mortar_rms={mortar['rms']:.12e}")
    print(f"mortar_worst={mortar['worst']}")
    print(
        f"residual_kind={args.residual_kind} residual_points={residual['count']} "
        f"skipped={skipped} max_abs={residual['max_abs']:.12e} rms={residual['rms']:.12e}"
    )
    print(f"origin_switch_q={q_switch:.12g} top_at_switch={residual['top_at_switch']}/{len(residual['top'])}")
    for index, point in enumerate(residual["top"], start=1):  # type: ignore[index]
        print(
            f"  top{index:02d} q={point['q']:.12g} b={point['b']:.12g} "
            f"e_psi={point['e_psi']:.12e} e_gamma={point['e_gamma']:.12e} "
            f"max_abs={point['max_abs']:.12e} at_switch={point['at_switch']}"
        )
    print("status=STRUCTURE_AUDIT_NOT_INTERVAL_VALIDATION")
    if args.json_out:
        out_dir = os.path.dirname(args.json_out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")


if __name__ == "__main__":
    main()
