#!/usr/bin/env python3
"""Audit exact patch and origin mortar mismatches for projected profiles.

This is a deterministic discovery/QA tool, not an interval smoothness proof.
It uses the same analytic Chebyshev/Taylor derivative evaluators as
`profile_newton_cheb.py` so derivative mortar defects are visible without
running a Newton step.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from profile_newton_cheb import (
    ContinuityConstraint,
    as_patch_items,
    build_origin_matching_constraints,
    build_patch_continuity_constraints,
    load_json,
    parse_blocks,
    parse_q_values,
    patch_partial_value,
    total_partial_value,
)


def constraint_diff(data: dict[str, object], constraint: ContinuityConstraint) -> float:
    if constraint.kind == "origin-match":
        return total_partial_value(
            data,
            constraint.component,
            constraint.q,
            constraint.x,
            constraint.dq_order,
            constraint.dx_order,
            "rect",
        ) - total_partial_value(
            data,
            constraint.component,
            constraint.q,
            constraint.x,
            constraint.dq_order,
            constraint.dx_order,
            "origin",
        )
    patches = as_patch_items(data, constraint.component)
    diff = patch_partial_value(
        patches[constraint.left],
        constraint.q,
        constraint.x,
        constraint.dq_order,
        constraint.dx_order,
    ) - patch_partial_value(
        patches[constraint.right],
        constraint.q,
        constraint.x,
        constraint.dq_order,
        constraint.dx_order,
    )
    return diff


def summarize(constraints: tuple[ContinuityConstraint, ...], diffs: list[float]) -> dict[str, object]:
    groups: dict[str, dict[str, object]] = {}
    total_sq = 0.0
    worst_index = -1
    worst_abs = 0.0
    for index, (constraint, diff) in enumerate(zip(constraints, diffs)):
        key = f"{constraint.kind}:{constraint.component}:d{constraint.derivative_order}:{constraint.derivative_direction or 'value'}"
        group = groups.setdefault(
            key,
            {
                "count": 0,
                "max_abs": 0.0,
                "rms_sum": 0.0,
                "kind": constraint.kind,
                "component": constraint.component,
                "derivative_order": constraint.derivative_order,
                "derivative_direction": constraint.derivative_direction,
                "dq_order": constraint.dq_order,
                "dx_order": constraint.dx_order,
            },
        )
        abs_diff = abs(diff)
        group["count"] = int(group["count"]) + 1
        group["max_abs"] = max(float(group["max_abs"]), abs_diff)
        group["rms_sum"] = float(group["rms_sum"]) + diff * diff
        total_sq += diff * diff
        if abs_diff > worst_abs:
            worst_abs = abs_diff
            worst_index = index
    group_items: list[dict[str, object]] = []
    for key, group in groups.items():
        count = int(group["count"])
        group_items.append(
            {
                "key": key,
                "count": count,
                "max_abs": float(group["max_abs"]),
                "rms": math.sqrt(float(group["rms_sum"]) / max(count, 1)),
                "kind": group["kind"],
                "component": group["component"],
                "derivative_order": group["derivative_order"],
                "derivative_direction": group["derivative_direction"],
                "dq_order": group["dq_order"],
                "dx_order": group["dx_order"],
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    worst: dict[str, object] = {}
    if worst_index >= 0:
        constraint = constraints[worst_index]
        worst = {
            "kind": constraint.kind,
            "component": constraint.component,
            "q": constraint.q,
            "x": constraint.x,
            "left": constraint.left,
            "right": constraint.right,
            "derivative_order": constraint.derivative_order,
            "derivative_direction": constraint.derivative_direction,
            "dq_order": constraint.dq_order,
            "dx_order": constraint.dx_order,
            "diff": diffs[worst_index],
            "abs": abs(diffs[worst_index]),
        }
    return {
        "count": len(diffs),
        "max_abs": worst_abs,
        "rms": math.sqrt(total_sq / max(len(diffs), 1)),
        "worst": worst,
        "groups": group_items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--blocks", default="F_an,G_an,F_frac0,G_frac0")
    parser.add_argument("--continuity-samples", type=int, default=3)
    parser.add_argument("--continuity-derivative-order", type=int, default=1)
    parser.add_argument("--origin-match-q", default="0.9")
    parser.add_argument("--origin-match-x-samples", type=int, default=7)
    parser.add_argument("--origin-match-derivative-order", type=int, default=1)
    parser.add_argument("--mortar-derivative-step", type=float, default=1e-4)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    data = load_json(args.profile)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError("profile must be a transseries_cheb_projection_v1 JSON file")
    blocks = parse_blocks(args.blocks)
    constraints = tuple(
        build_patch_continuity_constraints(
            data,
            blocks,
            samples=args.continuity_samples,
            weight=1.0,
            derivative_order=args.continuity_derivative_order,
            derivative_weight=1.0,
            derivative_step=args.mortar_derivative_step,
        )
        + build_origin_matching_constraints(
            data,
            q_values=parse_q_values(args.origin_match_q),
            x_samples=args.origin_match_x_samples,
            weight=1.0,
            derivative_order=args.origin_match_derivative_order,
            derivative_weight=1.0,
            derivative_step=args.mortar_derivative_step,
        )
    )
    diffs = [constraint_diff(data, constraint) for constraint in constraints]
    summary = summarize(constraints, diffs)
    print(f"profile={args.profile}")
    print(f"constraints={summary['count']}")
    print(f"max_abs={summary['max_abs']:.12e}")
    print(f"rms={summary['rms']:.12e}")
    print(f"worst={summary['worst']}")
    print("top_groups:")
    for group in summary["groups"][:12]:  # type: ignore[index]
        print(
            f"  {group['key']} count={group['count']} "
            f"max_abs={float(group['max_abs']):.12e} rms={float(group['rms']):.12e}"
        )
    print("status=EXACT_MORTAR_AUDIT_NOT_INTERVAL_VALIDATION")
    if args.json_out:
        out_dir = os.path.dirname(args.json_out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "profile": args.profile,
                    "blocks": list(blocks),
                    "summary": summary,
                    "status": "EXACT_MORTAR_AUDIT_NOT_INTERVAL_VALIDATION",
                },
                fh,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")


if __name__ == "__main__":
    main()
