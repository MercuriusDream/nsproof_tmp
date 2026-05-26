#!/usr/bin/env python3
"""Split a transseries-Chebyshev diagnostic profile into tail/origin charts.

This is a schema generator for a future hard Newton solve, not a proof or an
interval validator.  It preserves the q1-zero and q2-zero diagnostic metadata
from the source profile and records sampled overlap defects between the
rectangular tail chart (q,x) and the origin Taylor chart (R,Z).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from compactified_profile import grid
from profile_newton_cheb import load_json, total_partial_value
from validators.tail_formal_recurrence import parse_fraction_or_float, validate_tail_formal_recurrence


DEFAULT_INPUT = "work/v117_transcheb_formal_origin_refit_c2_d6_a_q2zero.json"
FALLBACK_INPUT = "work/v117_transcheb_formal_forced_q2zero.json"
DEFAULT_OUTPUT = "work/twochart_projection_v1.json"


@dataclass(frozen=True)
class DiffSpec:
    label: str
    dq_order: int
    dx_order: int


DIFF_SPECS = (
    DiffSpec("value", 0, 0),
    DiffSpec("dq", 1, 0),
    DiffSpec("dx", 0, 1),
    DiffSpec("dqq", 2, 0),
    DiffSpec("dqx", 1, 1),
    DiffSpec("dxx", 0, 2),
)


def save_json(path: str, data: dict[str, object]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def choose_default_input() -> str:
    if os.path.exists(DEFAULT_INPUT):
        return DEFAULT_INPUT
    return FALLBACK_INPUT


def rho2_from_q(q: float) -> float:
    return max(0.0, 1.0 / (q * q) - 1.0)


def qx_to_rz(q: float, x: float) -> tuple[float, float]:
    rho2 = rho2_from_q(q)
    return rho2 * (1.0 - x), rho2 * x


def origin_degree(origin: object) -> int | None:
    if not isinstance(origin, dict):
        return None
    degree = origin.get("degree")
    if isinstance(degree, int):
        return degree
    basis = origin.get("basis", [])
    if not isinstance(basis, list):
        return None
    max_degree = 0
    for entry in basis:
        if not isinstance(entry, dict):
            continue
        max_degree = max(max_degree, int(entry.get("R_power", 0)) + int(entry.get("Z_power", 0)))
    return max_degree


def block_patch_count(block: object) -> int:
    if not isinstance(block, list):
        return 0
    if block and isinstance(block[0], list):
        return sum(len(item) for item in block if isinstance(item, list))
    return len(block)


def active_tail_patches(patches: list[dict[str, object]], q_upper: float) -> int:
    count = 0
    for patch in patches:
        q0, _q1 = patch["q_interval"]  # type: ignore[index]
        if float(q0) <= q_upper + 1e-15:
            count += 1
    return count


def iter_diff_specs(max_order: int) -> Iterable[DiffSpec]:
    for spec in DIFF_SPECS:
        if spec.dq_order + spec.dx_order <= max_order:
            yield spec


def overlap_diagnostics(
    data: dict[str, object],
    q_min: float,
    q_max: float,
    q_samples: int,
    x_samples: int,
    derivative_order: int,
) -> dict[str, object]:
    groups: dict[str, dict[str, object]] = {}
    worst: dict[str, object] = {}
    total_sq = 0.0
    count = 0
    sample_points: list[dict[str, object]] = []
    worst_abs = 0.0
    for q in grid(q_min, q_max, q_samples):
        for x in grid(0.0, 1.0, x_samples):
            r_coord, z_coord = qx_to_rz(q, x)
            if len(sample_points) < 12:
                sample_points.append({"q": q, "x": x, "R": r_coord, "Z": z_coord})
            for component in ("F", "G"):
                for spec in iter_diff_specs(derivative_order):
                    rect = total_partial_value(data, component, q, x, spec.dq_order, spec.dx_order, "rect")
                    origin = total_partial_value(data, component, q, x, spec.dq_order, spec.dx_order, "origin")
                    diff = rect - origin
                    abs_diff = abs(diff)
                    key = f"{component}:{spec.label}"
                    group = groups.setdefault(
                        key,
                        {
                            "component": component,
                            "derivative": spec.label,
                            "dq_order": spec.dq_order,
                            "dx_order": spec.dx_order,
                            "count": 0,
                            "max_abs": 0.0,
                            "rms_sum": 0.0,
                        },
                    )
                    group["count"] = int(group["count"]) + 1
                    group["max_abs"] = max(float(group["max_abs"]), abs_diff)
                    group["rms_sum"] = float(group["rms_sum"]) + diff * diff
                    total_sq += diff * diff
                    count += 1
                    if abs_diff > worst_abs:
                        worst_abs = abs_diff
                        worst = {
                            "component": component,
                            "derivative": spec.label,
                            "dq_order": spec.dq_order,
                            "dx_order": spec.dx_order,
                            "q": q,
                            "x": x,
                            "R": r_coord,
                            "Z": z_coord,
                            "rect": rect,
                            "origin": origin,
                            "diff": diff,
                            "abs": abs_diff,
                        }
    group_items: list[dict[str, object]] = []
    for key, group in groups.items():
        group_count = int(group["count"])
        group_items.append(
            {
                "key": key,
                "component": group["component"],
                "derivative": group["derivative"],
                "dq_order": group["dq_order"],
                "dx_order": group["dx_order"],
                "count": group_count,
                "max_abs": float(group["max_abs"]),
                "rms": math.sqrt(float(group["rms_sum"]) / max(group_count, 1)),
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    return {
        "q_band": [q_min, q_max],
        "rho2_band": [rho2_from_q(q_max), rho2_from_q(q_min)],
        "sample_shape": {"q_samples": q_samples, "x_samples": x_samples},
        "derivative_order": derivative_order,
        "sample_count": count,
        "max_abs": worst_abs,
        "rms": math.sqrt(total_sq / max(count, 1)),
        "worst": worst,
        "groups": group_items,
        "sample_points_preview": sample_points,
        "note": "Sampled tail-origin differences only; no interval or Newton-Kantorovich validation.",
    }


def metadata_summary(data: dict[str, object]) -> dict[str, object]:
    tail_constraints = data.get("tail_constraints", {})
    ordinary_q1 = {}
    if isinstance(tail_constraints, dict):
        ordinary_q1 = tail_constraints.get("ordinary_q1", {})  # type: ignore[assignment]
    q2_evidence = data.get("q2_trace_zeroing_evidence", {})
    return {
        "tail_constraints": tail_constraints,
        "ordinary_q1_zero": ordinary_q1,
        "q2_trace_zeroing_evidence": q2_evidence,
        "origin_mortar_refit_evidence": data.get("origin_mortar_refit_evidence", {}),
        "projection_checks": data.get("projection_checks", {}),
    }


def build_hard_newton_schema(
    data: dict[str, object],
    q_min: float,
    q_max: float,
    q2_policy: str,
) -> dict[str, object]:
    blocks = data["blocks"]  # type: ignore[index]
    return {
        "schema_status": "future_solver_contract_not_implemented",
        "unknown_blocks": [
            {
                "name": "tail.F_an",
                "source_block": "blocks.F_an",
                "component": "F",
                "chart": "tail",
                "layout": "patch Chebyshev coeffs[kq][kx]",
            },
            {
                "name": "tail.G_an",
                "source_block": "blocks.G_an",
                "component": "G",
                "chart": "tail",
                "layout": "patch Chebyshev coeffs[kq][kx]",
            },
            {
                "name": "tail.F_frac",
                "source_block": "blocks.F_frac",
                "component": "F",
                "chart": "tail",
                "layout": "fractional_block -> patch Chebyshev coeffs[kq][kx]",
            },
            {
                "name": "tail.G_frac",
                "source_block": "blocks.G_frac",
                "component": "G",
                "chart": "tail",
                "layout": "fractional_block -> patch Chebyshev coeffs[kq][kx]",
            },
            {
                "name": "origin.F_origin_taylor",
                "source_block": "blocks.F_origin_taylor.basis",
                "component": "F",
                "chart": "origin",
                "layout": "monomial entries in R=rho2*(1-x), Z=rho2*x",
                "degree": origin_degree(blocks.get("F_origin_taylor")),  # type: ignore[union-attr]
            },
            {
                "name": "origin.G_origin_taylor",
                "source_block": "blocks.G_origin_taylor.basis",
                "component": "G",
                "chart": "origin",
                "layout": "monomial entries in R=rho2*(1-x), Z=rho2*x",
                "degree": origin_degree(blocks.get("G_origin_taylor")),  # type: ignore[union-attr]
            },
        ],
        "fixed_constraints": [
            "F0=1/2 and G0=B",
            "ordinary q^1 channel remains structurally absent",
            f"ordinary q^2 tail policy is {q2_policy}",
            "forced q^(1/gamma) trace metadata is preserved from the source profile",
        ],
        "residual_blocks": [
            {"name": "tail_equation_residual", "chart": "tail", "domain_q": [0.0, q_max]},
            {"name": "origin_equation_residual", "chart": "origin", "domain_q": [q_min, 1.0]},
            {"name": "overlap_value_mortar", "chart_pair": ["tail", "origin"], "domain_q": [q_min, q_max]},
            {
                "name": "overlap_derivative_mortar",
                "chart_pair": ["tail", "origin"],
                "domain_q": [q_min, q_max],
                "orders": ["dq", "dx", "dqq", "dqx", "dxx"],
            },
            {"name": "tail_patch_internal_mortar", "chart": "tail"},
        ],
        "normalization": {
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "do_not_claim": "This JSON is a solver schema and sampled projection diagnostic, not a proof.",
        },
    }


def tail_legality_report(source_path: str, args: argparse.Namespace) -> dict[str, object]:
    if args.q2_policy != "zero":
        raise ValueError("profile_project_twochart currently enforces --q2-policy zero")
    gamma = parse_fraction_or_float(args.gamma) if args.gamma else None
    b_value = parse_fraction_or_float(args.B) if args.B else None
    report = validate_tail_formal_recurrence(
        source_path,
        gamma=gamma,
        B=b_value,
        q2_policy=args.q2_policy,
        samples_per_patch=args.tail_samples_per_patch,
    )
    result = asdict(report)
    result["note"] = (
        "Formal tail recurrence gate only: q1-zero, first forced q^(1/gamma), "
        "and zero ordinary q^2 trace are checked. This is not an interval proof."
    )
    if not report.all_ok:
        raise ValueError(f"tail formal recurrence gate failed: {report.status}")
    return result


def overlap_summary(overlap: dict[str, object]) -> dict[str, object]:
    groups = overlap.get("groups", [])
    top_groups = groups[:6] if isinstance(groups, list) else []
    return {
        "q_band": overlap.get("q_band"),
        "sample_shape": overlap.get("sample_shape"),
        "derivative_order": overlap.get("derivative_order"),
        "sample_count": overlap.get("sample_count"),
        "max_abs": overlap.get("max_abs"),
        "rms": overlap.get("rms"),
        "worst": overlap.get("worst"),
        "top_groups": top_groups,
        "status": "SAMPLED_OVERLAP_MORTAR_NOT_VALIDATED",
    }


def build_twochart(
    data: dict[str, object],
    source_path: str,
    args: argparse.Namespace,
    tail_legality: dict[str, object],
) -> dict[str, object]:
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError("input must have format transseries_cheb_projection_v1")
    blocks = data["blocks"]  # type: ignore[index]
    patches = data.get("patches", {})
    if not isinstance(blocks, dict):
        raise ValueError("input blocks must be an object")
    q_breaks = []
    x_breaks = []
    if isinstance(patches, dict):
        q_breaks = patches.get("q_breaks", [])  # type: ignore[assignment]
        x_breaks = patches.get("x_breaks", [])  # type: ignore[assignment]
    origin_q_min = None
    f_origin = blocks.get("F_origin_taylor", {})
    if isinstance(f_origin, dict) and "q_min" in f_origin:
        origin_q_min = f_origin["q_min"]
    overlap = overlap_diagnostics(
        data,
        args.overlap_q_min,
        args.overlap_q_max,
        args.q_samples,
        args.x_samples,
        args.derivative_order,
    )
    return {
        "format": "twochart_profile_projection_v1",
        "status": "diagnostic_twochart_projection_not_validated",
        "gamma": tail_legality["gamma"],
        "B": tail_legality["B"],
        "p": tail_legality["p"],
        "tail_legality": tail_legality,
        "source_profile_json": source_path,
        "requested_options": {
            "origin_chart": args.origin_chart,
            "q2_policy": args.q2_policy,
            "forced_qp": args.forced_qp,
            "gamma_override": args.gamma or None,
            "B_override": args.B or None,
        },
        "source_profile": {
            "format": data.get("format"),
            "status": data.get("status"),
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "source_seed_json": data.get("source_seed_json"),
        },
        "coordinate_maps": {
            "tail_chart": {
                "coordinates": ["q", "x"],
                "x_definition": "x=b^2",
                "active_domain": {"q": [0.0, args.overlap_q_max], "x": [0.0, 1.0]},
            },
            "origin_chart": {
                "coordinates": ["R", "Z"],
                "definitions": {
                    "rho2": "q^-2 - 1",
                    "R": "rho2*(1-x)",
                    "Z": "rho2*x",
                    "q": "(1+R+Z)^(-1/2)",
                    "x": "Z/(R+Z), with x=0 at R=Z=0 by convention",
                },
                "active_domain": {
                    "q": [args.overlap_q_min, 1.0],
                    "R_plus_Z": [0.0, rho2_from_q(args.overlap_q_min)],
                },
                "source_origin_q_min": origin_q_min,
            },
            "overlap": {
                "q_band": [args.overlap_q_min, args.overlap_q_max],
                "rho2_band": [rho2_from_q(args.overlap_q_max), rho2_from_q(args.overlap_q_min)],
            },
        },
        "tail_chart": {
            "representation": data.get("representation", {}),
            "patch_layout": patches,
            "active_patch_counts": {
                "F_an": active_tail_patches(blocks.get("F_an", []), args.overlap_q_max),  # type: ignore[arg-type]
                "G_an": active_tail_patches(blocks.get("G_an", []), args.overlap_q_max),  # type: ignore[arg-type]
                "F_frac_total": block_patch_count(blocks.get("F_frac", [])),
                "G_frac_total": block_patch_count(blocks.get("G_frac", [])),
            },
            "blocks": {
                "F_an": blocks.get("F_an", []),
                "G_an": blocks.get("G_an", []),
                "F_frac": blocks.get("F_frac", []),
                "G_frac": blocks.get("G_frac", []),
            },
        },
        "origin_chart": {
            "coordinate_choice": args.origin_chart,
            "basis": "Taylor monomials R^a Z^b",
            "blocks": {
                "F_origin_taylor": blocks.get("F_origin_taylor", {}),
                "G_origin_taylor": blocks.get("G_origin_taylor", {}),
            },
        },
        "preserved_metadata": metadata_summary(data),
        "overlap_mortar_metadata": overlap,
        "overlap_mortar_summary": overlap_summary(overlap),
        "hard_newton_schema": build_hard_newton_schema(
            data,
            args.overlap_q_min,
            args.overlap_q_max,
            args.q2_policy,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=choose_default_input())
    parser.add_argument("--out", default=DEFAULT_OUTPUT)
    parser.add_argument("--gamma", default="", help="Optional gamma override for tail-legality validation.")
    parser.add_argument("--B", default="", help="Optional B override for tail-legality validation.")
    parser.add_argument("--origin-chart", choices=("RZ",), default="RZ")
    parser.add_argument("--q2-policy", choices=("zero",), default="zero")
    parser.add_argument("--forced-qp", choices=("formal", "source"), default="formal")
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--q-samples", type=int, default=5)
    parser.add_argument("--x-samples", type=int, default=9)
    parser.add_argument("--derivative-order", type=int, choices=(0, 1, 2), default=2)
    parser.add_argument("--tail-samples-per-patch", type=int, default=9)
    args = parser.parse_args()
    if not (0.0 < args.overlap_q_min < args.overlap_q_max < 1.0):
        raise ValueError("overlap q band must satisfy 0 < min < max < 1")
    if args.q_samples <= 0 or args.x_samples <= 0:
        raise ValueError("sample counts must be positive")
    if args.tail_samples_per_patch <= 0:
        raise ValueError("--tail-samples-per-patch must be positive")

    data = load_json(args.input)
    source_forced_qp = data.get("tail_constraints", {})
    if isinstance(source_forced_qp, dict):
        forced = source_forced_qp.get("forced_qp", {})
        if args.forced_qp == "formal" and isinstance(forced, dict) and forced.get("mode") != "formal":
            raise ValueError("--forced-qp formal requested but source forced_qp metadata is not formal")
    tail_legality = tail_legality_report(args.input, args)
    out = build_twochart(data, args.input, args, tail_legality)
    save_json(args.out, out)

    overlap = out["overlap_mortar_metadata"]  # type: ignore[index]
    preserved = out["preserved_metadata"]  # type: ignore[index]
    ordinary_q1 = preserved["ordinary_q1_zero"]  # type: ignore[index]
    q2 = preserved["q2_trace_zeroing_evidence"]  # type: ignore[index]
    print(f"input={args.input}")
    print(f"saved={args.out}")
    print(f"status={out['status']}")
    print(f"gamma={out.get('gamma')} B={out.get('B')} p={out.get('p')}")
    print(f"tail_legality_status={tail_legality['status']}")
    print(f"tail_legality_all_ok={tail_legality['all_ok']}")
    print(f"overlap_q_band=[{args.overlap_q_min}, {args.overlap_q_max}]")
    print(f"overlap_max_abs={overlap['max_abs']:.12e}")  # type: ignore[index]
    print(f"overlap_rms={overlap['rms']:.12e}")  # type: ignore[index]
    print(f"ordinary_q1_F_max={ordinary_q1.get('F_max_abs', 'missing')}")
    print(f"ordinary_q1_G_max={ordinary_q1.get('G_max_abs', 'missing')}")
    print(f"q2_zero_status={q2.get('status', 'missing') if isinstance(q2, dict) else 'missing'}")
    print("status=DIAGNOSTIC_TWOCHART_PROJECTION_NOT_VALIDATED")


if __name__ == "__main__":
    main()
