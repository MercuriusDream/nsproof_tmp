#!/usr/bin/env python3
"""Blend two compactified profile seeds and evaluate profile gates.

This is a diagnostic for admissible profile continuation.  It is useful when
one seed has better finite-box residuals and another seed has better far-tail
residuals: both can preserve the same q=0 conical trace, and a convex blend
may reveal whether the tradeoff is smooth or whether one endpoint dominates.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

from compactified_collocation import scan_qb
from compactified_profile import CompactifiedProfile, Coeff, load_seed_json_profile, scan_residual


@dataclass(frozen=True)
class BlendMetrics:
    t: float
    standard: float
    standard_rms: float
    extreme: float
    extreme_rms: float
    farther: float
    farther_rms: float
    interior: float
    interior_rms: float
    local: float
    local_rms: float

    @property
    def max_all(self) -> float:
        return max(self.standard, self.extreme, self.farther, self.interior, self.local)

    @property
    def max_no_farther(self) -> float:
        return max(self.standard, self.extreme, self.interior, self.local)


def coeff_map(raw: list[list[object]]) -> dict[tuple[int, int], float]:
    return {(int(i), int(j)): float(value) for i, j, value in raw}


def coeff_list(items: dict[tuple[int, int], float]) -> list[list[float]]:
    return [[i, j, items[(i, j)]] for i, j in sorted(items)]


def blend_maps(
    left: dict[tuple[int, int], float],
    right: dict[tuple[int, int], float],
    t: float,
) -> dict[tuple[int, int], float]:
    out: dict[tuple[int, int], float] = {}
    for key in sorted(set(left) | set(right)):
        out[key] = (1.0 - t) * left.get(key, 0.0) + t * right.get(key, 0.0)
    return out


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def blend_data(path_left: str, path_right: str, t: float) -> dict[str, object]:
    left = load_data(path_left)
    right = load_data(path_right)
    gamma = float(left["gamma"])
    B = float(left.get("B", 1.0))
    if abs(gamma - float(right["gamma"])) > 1e-14:
        raise ValueError("cannot blend seeds with different gamma")
    if abs(B - float(right.get("B", 1.0))) > 1e-14:
        raise ValueError("cannot blend seeds with different B")
    power_left = float(left.get("vanishing_edge_power", 1.0))
    power_right = float(right.get("vanishing_edge_power", 1.0))
    if abs(power_left - power_right) > 1e-14:
        raise ValueError("cannot blend seeds with different vanishing_edge_power")
    bump_q_centers = left.get("interior_bump_q_centers", right.get("interior_bump_q_centers", []))
    bump_b2_centers = left.get("interior_bump_b2_centers", right.get("interior_bump_b2_centers", []))
    if not bump_q_centers:
        bump_q_centers = right.get("interior_bump_q_centers", [])
    if not bump_b2_centers:
        bump_b2_centers = right.get("interior_bump_b2_centers", [])
    if left.get("interior_bump_q_centers", bump_q_centers) != bump_q_centers:
        raise ValueError("cannot blend seeds with different interior_bump_q_centers")
    if right.get("interior_bump_q_centers", bump_q_centers) != bump_q_centers:
        raise ValueError("cannot blend seeds with different interior_bump_q_centers")
    if left.get("interior_bump_b2_centers", bump_b2_centers) != bump_b2_centers:
        raise ValueError("cannot blend seeds with different interior_bump_b2_centers")
    if right.get("interior_bump_b2_centers", bump_b2_centers) != bump_b2_centers:
        raise ValueError("cannot blend seeds with different interior_bump_b2_centers")
    bump_q_radius = float(left.get("interior_bump_q_radius", right.get("interior_bump_q_radius", 0.14)))
    bump_b2_radius = float(left.get("interior_bump_b2_radius", right.get("interior_bump_b2_radius", 0.10)))
    bump_shape = str(left.get("interior_bump_shape", right.get("interior_bump_shape", "compact")))
    bump_flatness = float(left.get("interior_bump_q_flatness", right.get("interior_bump_q_flatness", 1.0)))
    if abs(float(right.get("interior_bump_q_radius", bump_q_radius)) - bump_q_radius) > 1e-14:
        raise ValueError("cannot blend seeds with different interior_bump_q_radius")
    if abs(float(right.get("interior_bump_b2_radius", bump_b2_radius)) - bump_b2_radius) > 1e-14:
        raise ValueError("cannot blend seeds with different interior_bump_b2_radius")
    if str(right.get("interior_bump_shape", bump_shape)) != bump_shape:
        raise ValueError("cannot blend seeds with different interior_bump_shape")
    if abs(float(right.get("interior_bump_q_flatness", bump_flatness)) - bump_flatness) > 1e-14:
        raise ValueError("cannot blend seeds with different interior_bump_q_flatness")

    data: dict[str, object] = {
        "gamma": gamma,
        "B": B,
        "q_order": max(int(left.get("q_order", 0)), int(right.get("q_order", 0))),
        "b_order": max(int(left.get("b_order", 0)), int(right.get("b_order", 0))),
        "bounded_edge_q_order": max(
            int(left.get("bounded_edge_q_order", 0)),
            int(right.get("bounded_edge_q_order", 0)),
        ),
        "bounded_edge_b_order": max(
            int(left.get("bounded_edge_b_order", 0)),
            int(right.get("bounded_edge_b_order", 0)),
        ),
        "edge_family": left.get("edge_family", right.get("edge_family", "vanishing")),
        "vanishing_edge_power": power_left,
        "bounded_edge_basis": "(1-q)^i * b^(2j)",
        "vanishing_edge_basis": "q^vanishing_edge_power * (1-q)^i * b^(2j)",
        "interior_bump_basis": "tail-flat or compact tensor bumps in q and b^2",
        "interior_bump_q_centers": bump_q_centers,
        "interior_bump_b2_centers": bump_b2_centers,
        "interior_bump_q_radius": bump_q_radius,
        "interior_bump_b2_radius": bump_b2_radius,
        "interior_bump_shape": bump_shape,
        "interior_bump_q_flatness": bump_flatness,
        "dropped_singular_edge_basis": True,
        "blend": {
            "left": path_left,
            "right": path_right,
            "t": t,
            "formula": "(1-t)*left + t*right",
        },
    }

    for key in (
        "f_coeffs",
        "g_coeffs",
        "f_bounded_edge_coeffs",
        "g_bounded_edge_coeffs",
        "f_vanishing_edge_coeffs",
        "g_vanishing_edge_coeffs",
        "f_interior_bump_coeffs",
        "g_interior_bump_coeffs",
    ):
        data[key] = coeff_list(
            blend_maps(
                coeff_map(left.get(key, [])),  # type: ignore[arg-type]
                coeff_map(right.get(key, [])),  # type: ignore[arg-type]
                t,
            )
        )
    return data


def profile_from_data(data: dict[str, object]) -> CompactifiedProfile:
    def tuples(key: str) -> tuple[Coeff, ...]:
        return tuple((int(i), int(j), float(v)) for i, j, v in data.get(key, []))  # type: ignore[union-attr]

    return CompactifiedProfile(
        gamma=float(data["gamma"]),
        f_coeffs=tuples("f_coeffs"),
        g_coeffs=tuples("g_coeffs"),
        f_bounded_edge_coeffs=tuples("f_bounded_edge_coeffs"),
        g_bounded_edge_coeffs=tuples("g_bounded_edge_coeffs"),
        f_vanishing_edge_coeffs=tuples("f_vanishing_edge_coeffs"),
        g_vanishing_edge_coeffs=tuples("g_vanishing_edge_coeffs"),
        vanishing_edge_power=float(data.get("vanishing_edge_power", 1.0)),
        f_interior_bump_coeffs=tuples("f_interior_bump_coeffs"),
        g_interior_bump_coeffs=tuples("g_interior_bump_coeffs"),
        interior_bump_q_centers=tuple(float(x) for x in data.get("interior_bump_q_centers", [])),  # type: ignore[union-attr]
        interior_bump_b2_centers=tuple(float(x) for x in data.get("interior_bump_b2_centers", [])),  # type: ignore[union-attr]
        interior_bump_q_radius=float(data.get("interior_bump_q_radius", 0.14)),
        interior_bump_b2_radius=float(data.get("interior_bump_b2_radius", 0.10)),
        interior_bump_shape=str(data.get("interior_bump_shape", "compact")),
        interior_bump_q_flatness=float(data.get("interior_bump_q_flatness", 1.0)),
    )


def evaluate(data: dict[str, object], h: float) -> BlendMetrics:
    profile = profile_from_data(data)
    gamma = float(data["gamma"])

    standard, _point, standard_rms, _count = scan_qb(
        profile, gamma, 0.35, 0.90, -0.80, 0.80, 15, 15, h
    )
    extreme, _point, extreme_rms, _count = scan_qb(
        profile, gamma, 0.25, 0.90, -0.90, 0.90, 15, 15, h
    )
    farther, _point, farther_rms, _count = scan_qb(
        profile, gamma, 0.18, 0.30, -0.90, 0.90, 9, 17, h
    )
    interior, _point, interior_rms, _count = scan_qb(
        profile, gamma, 0.45, 0.85, -0.65, 0.65, 15, 15, h
    )
    local, _point, local_rms = scan_residual(
        profile, gamma, 0.8, 2.0, -1.0, 1.0, 23, h
    )
    return BlendMetrics(
        t=float(data.get("blend", {}).get("t", math.nan)),  # type: ignore[union-attr]
        standard=standard.max_abs,
        standard_rms=standard_rms,
        extreme=extreme.max_abs,
        extreme_rms=extreme_rms,
        farther=farther.max_abs,
        farther_rms=farther_rms,
        interior=interior.max_abs,
        interior_rms=interior_rms,
        local=local.max_abs,
        local_rms=local_rms,
    )


def scan_values(count: int) -> list[float]:
    if count <= 1:
        return [0.0]
    return [i / (count - 1) for i in range(count)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--count", type=int, default=21)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--save-best", default="")
    parser.add_argument(
        "--best-by",
        choices=["max-all", "max-no-farther", "farther"],
        default="max-all",
    )
    args = parser.parse_args()

    print(
        "t,standard,standard_rms,extreme,extreme_rms,farther,farther_rms,"
        "interior,interior_rms,local,local_rms,max_all,max_no_farther"
    )
    rows: list[tuple[float, BlendMetrics, dict[str, object]]] = []
    for t in scan_values(args.count):
        data = blend_data(args.left, args.right, t)
        metrics = evaluate(data, args.h)
        if args.best_by == "max-all":
            score = metrics.max_all
        elif args.best_by == "max-no-farther":
            score = metrics.max_no_farther
        else:
            score = metrics.farther
        rows.append((score, metrics, data))
        print(
            f"{t:.12e},{metrics.standard:.12e},{metrics.standard_rms:.12e},"
            f"{metrics.extreme:.12e},{metrics.extreme_rms:.12e},"
            f"{metrics.farther:.12e},{metrics.farther_rms:.12e},"
            f"{metrics.interior:.12e},{metrics.interior_rms:.12e},"
            f"{metrics.local:.12e},{metrics.local_rms:.12e},"
            f"{metrics.max_all:.12e},{metrics.max_no_farther:.12e}"
        )

    best_score, best_metrics, best_data = min(rows, key=lambda item: item[0])
    print(
        f"\nBest by {args.best_by}: t={best_metrics.t:.12e} "
        f"score={best_score:.12e} max_all={best_metrics.max_all:.12e} "
        f"max_no_farther={best_metrics.max_no_farther:.12e} "
        f"farther={best_metrics.farther:.12e}"
    )
    if args.save_best:
        best_data["evidence"] = {
            "status": "approximate_non_validated_blended_admissible_seed",
            "blend_score_kind": args.best_by,
            "blend_score": best_score,
            "h": args.h,
        }
        with open(args.save_best, "w", encoding="utf-8") as fh:
            json.dump(best_data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"saved best blend: {args.save_best}")


if __name__ == "__main__":
    main()
