#!/usr/bin/env python3
"""Stage-0 CLI for hard-constrained two-chart Newton diagnostics.

This command now has a bounded production path: it assembles analytic PDE and
overlap-mortar rows for a controlled variable subset, solves a damped least
squares correction, and writes a candidate only if a line-search step improves
the same sampled objective.  It is still discovery infrastructure, not an
interval proof or a final Newton-Kantorovich validator.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.tail_transseries import forced_qp_expected_coeffs  # noqa: E402


STATUS = "TWOCHART_NEWTON_STAGE0_DRY_RUN_ONLY"
RUN_STATUS = "TWOCHART_NEWTON_STAGE0_ANALYTIC_GN_NOT_PROOF"
MISSING_HOOK_STATUS = "REFUSED_REAL_NEWTON_MISSING_TWOCHART_RESIDUAL_JACOBIAN_HOOKS"
SUPPORTED_FORMATS = {
    "twochart_profile_projection_v1",
    "twochart_profile_v1",
    "compactified_twochart_profile_v1",
}
REQUIRED_HOOKS = ("eval_residual_and_jacobian",)


class NewtonNoImprovement(RuntimeError):
    pass


@dataclass(frozen=True)
class HookReport:
    module: str
    available: bool
    missing_hooks: tuple[str, ...]
    required_hooks: tuple[str, ...]
    import_error: str


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def parse_blocks(raw: str) -> tuple[str, ...]:
    blocks = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"tail", "origin", "interface"}
    unknown = [block for block in blocks if block not in allowed]
    if unknown:
        raise ValueError(f"unknown --blocks item(s): {', '.join(unknown)}")
    if not blocks:
        raise ValueError("--blocks must name at least one of tail,origin,interface")
    return blocks


def parse_variable_charts(raw: str) -> tuple[str, ...]:
    charts = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"tail", "origin"}
    unknown = [chart for chart in charts if chart not in allowed]
    if unknown:
        raise ValueError(f"unknown --variable-charts item(s): {', '.join(unknown)}")
    if not charts:
        raise ValueError("--variable-charts must name tail and/or origin")
    return charts


def hook_report() -> HookReport:
    module_name = "validators.compactified_equations_twochart"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exact import error is environment-specific.
        return HookReport(
            module=module_name,
            available=False,
            missing_hooks=REQUIRED_HOOKS,
            required_hooks=REQUIRED_HOOKS,
            import_error=f"{type(exc).__name__}: {exc}",
        )
    missing = tuple(name for name in REQUIRED_HOOKS if not callable(getattr(module, name, None)))
    return HookReport(
        module=module_name,
        available=not missing,
        missing_hooks=missing,
        required_hooks=REQUIRED_HOOKS,
        import_error="",
    )


def validate_input_schema(data: dict[str, Any], path: str) -> None:
    fmt = data.get("format")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"{path} must be a two-chart profile JSON; got format={fmt!r}. "
            "Run tools/profile_project_twochart.py first."
        )
    if not isinstance(data.get("tail_chart"), dict):
        raise ValueError(f"{path} is missing tail_chart")
    if not isinstance(data.get("origin_chart"), dict):
        raise ValueError(f"{path} is missing origin_chart")


def validate_hard_gates(data: dict[str, Any], q2_policy: str) -> dict[str, Any]:
    if q2_policy != "zero":
        raise ValueError("hard-constrained two-chart Newton requires --q2-policy zero")
    tail_legality = data.get("tail_legality")
    if not isinstance(tail_legality, dict):
        raise ValueError("input profile is missing tail_legality report")
    if tail_legality.get("q2_policy") != "zero":
        raise ValueError(f"input tail_legality q2_policy must be zero; got {tail_legality.get('q2_policy')!r}")
    if tail_legality.get("all_ok") is not True:
        raise ValueError(f"tail_legality gate is not all_ok: status={tail_legality.get('status')!r}")
    return tail_legality


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def parse_float_list(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def parse_qb_points(raw: str) -> list[tuple[float, float]]:
    if not raw.strip():
        return [(0.45, 0.30), (0.61, 0.24), (0.93, 0.35), (0.90, 0.95)]
    points: list[tuple[float, float]] = []
    for item in raw.split(";"):
        if not item.strip():
            continue
        q_raw, b_raw = item.split(",", 1)
        points.append((float(q_raw), float(b_raw)))
    if not points:
        raise ValueError("--pde-qb-points did not contain any points")
    return points


def parse_optional_qb_points(raw: str) -> list[tuple[float, float]]:
    if not raw.strip():
        return []
    points: list[tuple[float, float]] = []
    for item in raw.split(";"):
        if not item.strip():
            continue
        q_raw, b_raw = item.split(",", 1)
        points.append((float(q_raw), float(b_raw)))
    return points


def variable_allowed_for_blocks(variable: Any, blocks: tuple[str, ...]) -> bool:
    if variable.chart == "origin":
        return "origin" in blocks or "interface" in blocks
    if variable.chart == "tail":
        return "tail" in blocks or "interface" in blocks
    return False


def variable_allowed_for_chart_filter(variable: Any, charts: tuple[str, ...]) -> bool:
    return variable.chart in charts


def variable_is_origin_constant(variable: Any) -> bool:
    return variable.chart == "origin" and int(variable.r_power or 0) == 0 and int(variable.z_power or 0) == 0


def tail_variable_patch(data: dict[str, Any], variable: Any) -> dict[str, Any]:
    blocks = data["tail_chart"]["blocks"]
    if variable.frac_index is None:
        return blocks[variable.block][variable.patch_index]
    return blocks[variable.block][variable.frac_index - 1][variable.patch_index]


def patch_contains_point(patch: dict[str, Any], q: float, x: float) -> bool:
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    return (
        float(q0) - 1e-14 <= q <= float(q1) + 1e-14
        and float(x0) - 1e-14 <= x <= float(x1) + 1e-14
    )


def variable_relevant_for_samples(
    data: dict[str, Any],
    variable: Any,
    pde_points: list[tuple[float, float]],
    mortar_points: list[tuple[float, float]],
) -> bool:
    if variable.chart == "origin":
        return True
    if variable.chart != "tail":
        return False
    patch = tail_variable_patch(data, variable)
    for q, b in pde_points:
        if patch_contains_point(patch, q, b * b):
            return True
    for q, x in mortar_points:
        if patch_contains_point(patch, q, x):
            return True
    return False


def variable_under_candidate_caps(variable: Any, args: argparse.Namespace) -> bool:
    if variable.chart == "origin":
        return int(variable.r_power or 0) + int(variable.z_power or 0) <= args.candidate_origin_degree_max
    if variable.chart == "tail":
        return int(variable.kq or 0) <= args.candidate_kq_max and int(variable.kx or 0) <= args.candidate_kx_max
    return False


def tail_variable_is_gate_locked(data: dict[str, Any], variable: Any) -> bool:
    if variable.chart != "tail":
        return False
    patch = tail_variable_patch(data, variable)
    q0, _q1 = patch["q_interval"]
    return abs(float(q0)) <= 1e-15


def cap_candidate_pool(variables: list[Any], limit: int) -> list[Any]:
    if len(variables) <= limit:
        return variables
    groups: dict[tuple[str, str, str], list[Any]] = {}
    for variable in variables:
        key = (variable.chart, variable.component, variable.block)
        groups.setdefault(key, []).append(variable)
    for group in groups.values():
        group.sort(
            key=lambda variable: (
                int(variable.r_power or 0) + int(variable.z_power or 0),
                int(variable.kq or 0) + int(variable.kx or 0),
                int(variable.kq or 0),
                int(variable.kx or 0),
                variable.label,
            )
        )
    capped: list[Any] = []
    keys = sorted(groups)
    while len(capped) < limit and keys:
        next_keys: list[tuple[str, str, str]] = []
        for key in keys:
            group = groups[key]
            if group and len(capped) < limit:
                capped.append(group.pop(0))
            if group:
                next_keys.append(key)
        keys = next_keys
    return capped


def select_active_variables(ranked: list[Any], max_variables: int, chart_balanced: bool) -> list[Any]:
    if not chart_balanced:
        return ranked[:max_variables]
    groups: dict[str, list[Any]] = {"tail": [], "origin": []}
    for variable in ranked:
        groups.setdefault(variable.chart, []).append(variable)
    selected: list[Any] = []
    keys = [key for key in ("tail", "origin") if groups.get(key)]
    while len(selected) < max_variables and keys:
        next_keys: list[str] = []
        for key in keys:
            group = groups[key]
            if group and len(selected) < max_variables:
                selected.append(group.pop(0))
            if group:
                next_keys.append(key)
        keys = next_keys
    return selected


def cheb_eval_1d(coeffs: list[float], t: float) -> float:
    if not coeffs:
        return 0.0
    b_k2 = 0.0
    b_k1 = 0.0
    for coeff in reversed(coeffs[1:]):
        b_k0 = 2.0 * t * b_k1 - b_k2 + float(coeff)
        b_k2 = b_k1
        b_k1 = b_k0
    return float(coeffs[0]) + t * b_k1 - b_k2


def cheb_eval_tensor(
    coeffs: list[list[float]],
    q: float,
    x: float,
    q0: float,
    q1: float,
    x0: float,
    x1: float,
) -> float:
    tq = 0.0 if q1 == q0 else (2.0 * q - q0 - q1) / (q1 - q0)
    tx = 0.0 if x1 == x0 else (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = [cheb_eval_1d([float(value) for value in row], tx) for row in coeffs]
    return cheb_eval_1d(q_values, tq)


def q0_trace_sample_max(
    patches: list[dict[str, Any]],
    expected: Any,
    samples_per_patch: int,
) -> float:
    worst = 0.0
    for patch in patches:
        q0, q1 = patch["q_interval"]
        x0, x1 = patch["x_interval"]
        q0f = float(q0)
        if abs(q0f) > 1e-15:
            continue
        count = max(samples_per_patch, 2)
        for index in range(count):
            x = float(x0) + (float(x1) - float(x0)) * index / (count - 1)
            value = cheb_eval_tensor(patch["coeffs"], q0f, x, q0f, float(q1), float(x0), float(x1))
            target = expected(x) if callable(expected) else float(expected)
            worst = max(worst, abs(value - target))
    return worst


def tail_gate_report_twochart(data: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    blocks = data["tail_chart"]["blocks"]
    expected_f, expected_g = forced_qp_expected_coeffs(float(data["gamma"]), float(data["B"]))
    q2_f = q0_trace_sample_max(blocks["F_an"], 0.0, args.tail_gate_samples_per_patch)
    q2_g = q0_trace_sample_max(blocks["G_an"], 0.0, args.tail_gate_samples_per_patch)
    forced_f = q0_trace_sample_max(
        blocks.get("F_frac", [[]])[0],
        lambda x: expected_f[0] + expected_f[1] * x,
        args.tail_gate_samples_per_patch,
    )
    forced_g = q0_trace_sample_max(
        blocks.get("G_frac", [[]])[0],
        lambda x: expected_g[0] + expected_g[1] * x,
        args.tail_gate_samples_per_patch,
    )
    forced_error = max(forced_f, forced_g)
    q2_ok = q2_f <= args.q2_tol and q2_g <= args.q2_tol
    forced_ok = forced_error <= args.forced_tol
    all_ok = q2_ok and forced_ok
    return {
        "status": "TAIL_FORMAL_RECURRENCE_GATE_OK_NOT_INTERVAL"
        if all_ok
        else "TAIL_FORMAL_RECURRENCE_GATE_FAILED_NOT_INTERVAL",
        "all_ok": all_ok,
        "q1_f_max": 0.0,
        "q1_g_max": 0.0,
        "forced_qp_coeff_error": forced_error,
        "forced_qp_F_sample_error": forced_f,
        "forced_qp_G_sample_error": forced_g,
        "q2_f_trace_max": q2_f,
        "q2_g_trace_max": q2_g,
        "q2_policy": args.q2_policy,
        "q2_ok": q2_ok,
        "samples_per_patch": args.tail_gate_samples_per_patch,
        "note": "Floating structural two-chart tail gate; this is not interval validation.",
    }


def solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-28:
            raise ValueError("singular damped normal matrix")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]
        for item in range(col, n + 1):
            a[col][item] /= pivot_value
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for item in range(col, n + 1):
                a[row][item] -= factor * a[col][item]
    return [a[i][n] for i in range(n)]


def set_path(data: dict[str, Any], path: tuple[Any, ...], value: float) -> None:
    node: Any = data
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value


def get_path(data: dict[str, Any], path: tuple[Any, ...]) -> float:
    node: Any = data
    for part in path:
        node = node[part]
    return float(node)


def apply_delta(
    data: dict[str, Any],
    variables: list[Any],
    delta: list[float],
    alpha: float,
    max_update_norm: float,
) -> tuple[dict[str, Any], dict[str, float]]:
    norm = math.sqrt(sum(value * value for value in delta))
    trust_scale = 1.0
    if max_update_norm > 0.0 and norm > max_update_norm:
        trust_scale = max_update_norm / max(norm, 1e-300)
    scale = alpha * trust_scale
    out = copy.deepcopy(data)
    max_abs = 0.0
    for variable, value in zip(variables, delta):
        update = scale * value
        set_path(out, variable.path, get_path(out, variable.path) + update)
        max_abs = max(max_abs, abs(update))
    out["twochart_newton_stage0_evidence"] = {
        "status": RUN_STATUS,
        "alpha_requested": alpha,
        "alpha_applied": scale,
        "delta_norm": norm,
        "max_abs_update": max_abs,
        "note": "Floating sampled analytic Gauss-Newton update; not a proof certificate.",
    }
    return out, {"alpha_applied": scale, "delta_norm": norm, "max_abs_update": max_abs}


def vector_metrics(vec: list[float]) -> dict[str, float]:
    if not vec:
        return {"count": 0.0, "max_abs": 0.0, "rms": 0.0, "objective": 0.0}
    total = sum(value * value for value in vec)
    return {
        "count": float(len(vec)),
        "max_abs": max(abs(value) for value in vec),
        "rms": math.sqrt(total / len(vec)),
        "objective": 0.5 * total,
    }


def guard_point_metrics(data: dict[str, Any], args: argparse.Namespace, points: list[tuple[float, float]]) -> dict[str, Any]:
    if not points:
        return {"enabled": False, **vector_metrics([])}
    from validators.compactified_equations import compactified_residual_defined, qb_to_rz, residual_with_kind
    from validators.compactified_equations_twochart import projection_from_twochart

    projection = projection_from_twochart(data)
    values: list[float] = []
    skipped = 0
    worst: dict[str, Any] = {"abs": -1.0}
    for q, b in points:
        if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
            skipped += 1
            continue
        r, z = qb_to_rz(q, b)
        raw = projection.exact_residual_at(r, z)
        residual = residual_with_kind(raw, q, b, projection.p, args.residual_kind)
        for component, value in (("e_psi", residual.e_psi), ("e_gamma", residual.e_gamma)):
            values.append(value)
            if abs(value) > worst["abs"]:
                worst = {"q": q, "b": b, "component": component, "value": value, "abs": abs(value)}
    return {
        "enabled": True,
        "points_requested": len(points),
        "skipped": skipped,
        "worst": worst,
        **vector_metrics(values),
    }


def stage0_row_scaling(
    jacobian_rows: list[list[float]],
    residual_vector: list[float],
    row_labels: list[str],
    args: argparse.Namespace,
) -> tuple[list[list[float]], list[float], dict[str, Any]]:
    if args.row_normalization == "none":
        return jacobian_rows, residual_vector, {
            "row_normalization": "none",
            "scale_min": 1.0,
            "scale_max": 1.0,
            "groups": {},
        }

    scaled_rows: list[list[float]] = []
    scaled_residuals: list[float] = []
    scales: list[float] = []
    by_group: dict[str, dict[str, float]] = {}
    for row, residual, label in zip(jacobian_rows, residual_vector, row_labels):
        jac_norm = math.sqrt(sum(value * value for value in row))
        if args.row_normalization == "jacobian":
            denom = jac_norm
        elif args.row_normalization == "residual-jacobian":
            denom = math.sqrt(jac_norm * jac_norm + residual * residual)
        else:  # pragma: no cover - argparse choices enforce this.
            raise ValueError(f"unknown row normalization {args.row_normalization!r}")
        denom = max(denom, args.row_normalization_floor)
        scale = 1.0 / denom
        scale = min(scale, args.row_scale_max)
        if args.row_scale_min > 0.0:
            scale = max(scale, args.row_scale_min)
        scales.append(scale)
        scaled_rows.append([scale * value for value in row])
        scaled_residuals.append(scale * residual)
        group = by_group.setdefault(
            label,
            {
                "count": 0.0,
                "raw_residual_l2": 0.0,
                "scaled_residual_l2": 0.0,
                "raw_residual_max": 0.0,
                "scaled_residual_max": 0.0,
                "jac_norm_min": float("inf"),
                "jac_norm_max": 0.0,
                "scale_min": float("inf"),
                "scale_max": 0.0,
            },
        )
        group["count"] += 1.0
        group["raw_residual_l2"] += residual * residual
        group["scaled_residual_l2"] += (scale * residual) * (scale * residual)
        group["raw_residual_max"] = max(group["raw_residual_max"], abs(residual))
        group["scaled_residual_max"] = max(group["scaled_residual_max"], abs(scale * residual))
        group["jac_norm_min"] = min(group["jac_norm_min"], jac_norm)
        group["jac_norm_max"] = max(group["jac_norm_max"], jac_norm)
        group["scale_min"] = min(group["scale_min"], scale)
        group["scale_max"] = max(group["scale_max"], scale)

    for group in by_group.values():
        count = max(group["count"], 1.0)
        group["raw_residual_rms"] = math.sqrt(group.pop("raw_residual_l2") / count)
        group["scaled_residual_rms"] = math.sqrt(group.pop("scaled_residual_l2") / count)
        if group["jac_norm_min"] == float("inf"):
            group["jac_norm_min"] = 0.0
        if group["scale_min"] == float("inf"):
            group["scale_min"] = 0.0

    return scaled_rows, scaled_residuals, {
        "row_normalization": args.row_normalization,
        "row_normalization_floor": args.row_normalization_floor,
        "row_scale_min_limit": args.row_scale_min,
        "row_scale_max_limit": args.row_scale_max,
        "scale_min": min(scales) if scales else 0.0,
        "scale_max": max(scales) if scales else 0.0,
        "groups": by_group,
    }


def build_stage0_system(data: dict[str, Any], args: argparse.Namespace, blocks: tuple[str, ...]) -> dict[str, Any]:
    from validators.compactified_equations import compactified_residual_defined, qb_to_rz, residual_with_kind
    from validators.compactified_equations_twochart import (
        linearized_residual_with_kind,
        projection_from_twochart,
    )
    from validators.twochart_mortar_jacobian import build_rows, build_rz_rows, enumerate_coefficients, grid

    projection = projection_from_twochart(data)
    all_variables = enumerate_coefficients(data)
    pde_points = parse_qb_points(args.pde_qb_points)
    variable_charts = parse_variable_charts(args.variable_charts)
    q_values = grid(args.overlap_q_min, args.overlap_q_max, args.mortar_q_samples) if "interface" in blocks else []
    x_values = grid(0.0, 1.0, args.mortar_x_samples) if "interface" in blocks else []
    mortar_points = [(q, x) for q in q_values for x in x_values]
    candidate_variables = [
        variable
        for variable in all_variables
        if variable_allowed_for_blocks(variable, blocks)
        and variable_allowed_for_chart_filter(variable, variable_charts)
        and (args.include_origin_constants or not variable_is_origin_constant(variable))
        and variable_relevant_for_samples(data, variable, pde_points, mortar_points)
        and variable_under_candidate_caps(variable, args)
        and not tail_variable_is_gate_locked(data, variable)
    ]
    candidate_variables = cap_candidate_pool(candidate_variables, args.candidate_pool_limit)

    pde_rows: list[dict[str, Any]] = []
    variable_scores = {variable.index: 0.0 for variable in candidate_variables}
    for q, b in pde_points:
        if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
            continue
        r, z = qb_to_rz(q, b)
        raw = projection.exact_residual_at(r, z)
        residual = residual_with_kind(raw, q, b, projection.p, args.residual_kind)
        pde_rows.append({"q": q, "b": b, "component": "e_psi", "residual": residual.e_psi})
        pde_rows.append({"q": q, "b": b, "component": "e_gamma", "residual": residual.e_gamma})
        for variable in candidate_variables:
            column = linearized_residual_with_kind(data, projection, variable, q, b, args.residual_kind)
            variable_scores[variable.index] += abs(column.e_psi * residual.e_psi) + abs(column.e_gamma * residual.e_gamma)

    mortar_rows = []
    mortar_rows_available = 0
    if "interface" in blocks:
        if args.mortar_coordinates == "RZ":
            mortar_rows = build_rz_rows(data, candidate_variables, q_values, x_values, args.mortar_order)
        elif args.mortar_coordinates == "qx":
            mortar_rows = build_rows(data, candidate_variables, q_values, x_values, args.mortar_order)
        else:
            mortar_rows = build_rows(data, candidate_variables, q_values, x_values, args.mortar_order) + build_rz_rows(
                data, candidate_variables, q_values, x_values, args.mortar_order
            )
        mortar_rows_available = len(mortar_rows)
        if args.mortar_active_count > 0 and len(mortar_rows) > args.mortar_active_count:
            mortar_rows = sorted(mortar_rows, key=lambda row: abs(row.residual), reverse=True)[
                : args.mortar_active_count
            ]
        candidate_indexes = {variable.index for variable in candidate_variables}
        for row in mortar_rows:
            for var_index, jac_value in row.jacobian:
                if var_index in candidate_indexes:
                    variable_scores[var_index] += abs(args.mortar_weight * jac_value * row.residual)

    ranked = sorted(candidate_variables, key=lambda variable: variable_scores.get(variable.index, 0.0), reverse=True)
    selected = [variable for variable in ranked if variable_scores.get(variable.index, 0.0) > 0.0]
    selected = select_active_variables(selected, args.max_variables, args.chart_balanced_selection)
    selected_index = {variable.index: column for column, variable in enumerate(selected)}
    if not selected:
        raise ValueError("no active variables selected for Stage-0 system")

    residual_vector: list[float] = []
    jacobian_rows: list[list[float]] = []
    row_labels: list[str] = []
    row_groups: dict[str, int] = {"pde": 0, "mortar": 0}

    for row in pde_rows:
        q = float(row["q"])
        b = float(row["b"])
        component = str(row["component"])
        residual_vector.append(args.pde_weight * float(row["residual"]))
        jac_row: list[float] = []
        for variable in selected:
            column = linearized_residual_with_kind(data, projection, variable, q, b, args.residual_kind)
            jac_row.append(args.pde_weight * (column.e_psi if component == "e_psi" else column.e_gamma))
        jacobian_rows.append(jac_row)
        row_labels.append("pde")
        row_groups["pde"] += 1

    for row in mortar_rows:
        active_entries = [(selected_index[var_index], value) for var_index, value in row.jacobian if var_index in selected_index]
        if not active_entries:
            continue
        residual_vector.append(args.mortar_weight * row.residual)
        jac_row = [0.0 for _ in selected]
        for column_index, value in active_entries:
            jac_row[column_index] = args.mortar_weight * value
        jacobian_rows.append(jac_row)
        row_labels.append("mortar")
        row_groups["mortar"] += 1

    raw_metrics = vector_metrics(residual_vector)
    jacobian_rows, residual_vector, row_scaling = stage0_row_scaling(jacobian_rows, residual_vector, row_labels, args)
    selected_by_chart: dict[str, int] = {}
    selected_by_block: dict[str, int] = {}
    for variable in selected:
        selected_by_chart[variable.chart] = selected_by_chart.get(variable.chart, 0) + 1
        key = f"{variable.chart}.{variable.block}"
        selected_by_block[key] = selected_by_block.get(key, 0) + 1

    return {
        "variables": selected,
        "residual_vector": residual_vector,
        "jacobian_rows": jacobian_rows,
        "raw_residual_metrics": raw_metrics,
        "row_scaling": row_scaling,
        "row_groups": row_groups,
        "selected_by_chart": selected_by_chart,
        "selected_by_block": selected_by_block,
        "mortar_coordinates": args.mortar_coordinates,
        "mortar_rows_available": mortar_rows_available,
        "mortar_rows_active": len(mortar_rows),
        "variable_score_preview": [
            {"variable": variable.label, "score": variable_scores.get(variable.index, 0.0)}
            for variable in selected[:12]
        ],
    }


def normal_step(
    jacobian_rows: list[list[float]],
    residual_vector: list[float],
    lm_lambda: float,
) -> tuple[list[float], dict[str, float]]:
    if not jacobian_rows:
        raise ValueError("empty Jacobian")
    n = len(jacobian_rows[0])
    column_norms = []
    for column in range(n):
        norm = math.sqrt(sum(row[column] * row[column] for row in jacobian_rows))
        column_norms.append(norm)
    scales = [1.0 / norm if norm > 1e-14 else 1.0 for norm in column_norms]
    normal = [[0.0 for _ in range(n)] for _ in range(n)]
    rhs = [0.0 for _ in range(n)]
    for row, residual in zip(jacobian_rows, residual_vector):
        scaled_row = [value * scales[index] for index, value in enumerate(row)]
        for i, ji in enumerate(scaled_row):
            rhs[i] -= ji * residual
            if ji == 0.0:
                continue
            for j in range(i, n):
                normal[i][j] += ji * scaled_row[j]
    for i in range(n):
        for j in range(i):
            normal[i][j] = normal[j][i]
        normal[i][i] += lm_lambda
    scaled_delta = solve_linear(normal, rhs)
    delta = [value * scales[index] for index, value in enumerate(scaled_delta)]
    nonzero_norms = [value for value in column_norms if value > 0.0]
    return delta, {
        "column_norm_min": min(nonzero_norms) if nonzero_norms else 0.0,
        "column_norm_max": max(column_norms) if column_norms else 0.0,
        "column_scale_min": min(scales) if scales else 0.0,
        "column_scale_max": max(scales) if scales else 0.0,
    }


def restricted_normal_step(
    jacobian_rows: list[list[float]],
    residual_vector: list[float],
    active_columns: list[int],
    total_columns: int,
    lm_lambda: float,
) -> tuple[list[float], dict[str, Any]]:
    if not active_columns:
        raise ValueError("empty active column set")
    restricted_rows = [[row[column] for column in active_columns] for row in jacobian_rows]
    restricted_delta, report = normal_step(restricted_rows, residual_vector, lm_lambda)
    full_delta = [0.0 for _ in range(total_columns)]
    for local_index, column in enumerate(active_columns):
        full_delta[column] = restricted_delta[local_index]
    return full_delta, {
        **report,
        "active_columns": len(active_columns),
        "total_columns": total_columns,
    }


def stage0_block_specs(variables: list[Any], solve_mode: str, labels_raw: str = "") -> list[dict[str, Any]]:
    if solve_mode == "full":
        return [{"label": "full", "columns": list(range(len(variables)))}]
    requested = {item.strip() for item in labels_raw.split(",") if item.strip()}
    specs: list[dict[str, Any]] = [{"label": "full", "columns": list(range(len(variables)))}]
    seen = {"full"}

    def add(label: str, predicate: Any) -> None:
        if label in seen:
            return
        columns = [index for index, variable in enumerate(variables) if predicate(variable)]
        if not columns:
            return
        specs.append({"label": label, "columns": columns})
        seen.add(label)

    for chart in ("tail", "origin"):
        add(f"chart:{chart}", lambda variable, chart=chart: variable.chart == chart)
    for component in ("F", "G"):
        add(f"component:{component}", lambda variable, component=component: variable.component == component)
    for chart in ("tail", "origin"):
        for component in ("F", "G"):
            add(
                f"{chart}.{component}",
                lambda variable, chart=chart, component=component: variable.chart == chart and variable.component == component,
            )
    for block in sorted({str(variable.block) for variable in variables}):
        add(f"block:{block}", lambda variable, block=block: str(variable.block) == block)
    if requested:
        specs = [spec for spec in specs if spec["label"] in requested]
        missing = sorted(requested - {str(spec["label"]) for spec in specs})
        if missing:
            raise ValueError(f"--block-search-labels requested unavailable block(s): {', '.join(missing)}")
        if not specs:
            raise ValueError("--block-search-labels removed every block candidate")
    return specs


def attach_stage0_tail_gate(data: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    report = tail_gate_report_twochart(data, args)
    data["tail_legality"] = {
        **data.get("tail_legality", {}),
        **report,
    }
    return report


def run_stage0(args: argparse.Namespace, data: dict[str, Any], hooks: HookReport) -> dict[str, Any]:
    if not hooks.available:
        return build_plan(args, data, hooks)
    blocks = parse_blocks(args.blocks)
    tail_legality = validate_hard_gates(data, args.q2_policy)

    current = copy.deepcopy(data)
    history: list[dict[str, Any]] = []
    best_trial: dict[str, Any] | None = None
    best_trial_metrics: dict[str, Any] | None = None
    guard_points = parse_optional_qb_points(args.guard_qb_points)
    for iteration in range(args.max_iter):
        system = build_stage0_system(current, args, blocks)
        base_vec = system["residual_vector"]
        base_metrics = vector_metrics(base_vec)
        base_raw_metrics = system["raw_residual_metrics"]
        base_guard_metrics = guard_point_metrics(current, args, guard_points)
        block_specs = stage0_block_specs(system["variables"], args.solve_mode, args.block_search_labels)
        line_trials: list[dict[str, Any]] = []
        candidate_previews: list[dict[str, Any]] = []
        best_accepted: dict[str, Any] | None = None
        accepted = False
        for block_spec in block_specs:
            try:
                delta, scaling_report = restricted_normal_step(
                    system["jacobian_rows"],
                    base_vec,
                    list(block_spec["columns"]),
                    len(system["variables"]),
                    args.lm_lambda,
                )
            except ValueError as exc:
                line_trials.append(
                    {
                        "block": block_spec["label"],
                        "rejected_by_solver": True,
                        "error": str(exc),
                    }
                )
                continue
            delta_norm = math.sqrt(sum(value * value for value in delta))
            candidate_previews.append(
                {
                    "block": block_spec["label"],
                    "active_columns": len(block_spec["columns"]),
                    "delta_norm": delta_norm,
                    "column_scaling": scaling_report,
                }
            )
            for alpha in args.line_search:
                trial_data, update_metrics = apply_delta(current, system["variables"], delta, alpha, args.trust)
                tail_gate = attach_stage0_tail_gate(trial_data, args)
                trial_record: dict[str, Any] = {
                    "block": block_spec["label"],
                    "active_columns": len(block_spec["columns"]),
                    "alpha": alpha,
                    "delta_norm": delta_norm,
                    "column_scaling": scaling_report,
                    **update_metrics,
                }
                if not tail_gate["all_ok"]:
                    line_trials.append(
                        {
                            **trial_record,
                            "rejected_by_tail_gate": True,
                            "tail_gate": tail_gate,
                        }
                    )
                    continue
                trial_system = build_stage0_system(trial_data, args, blocks)
                trial_metrics = vector_metrics(trial_system["residual_vector"])
                trial_raw_metrics = trial_system["raw_residual_metrics"]
                trial_guard_metrics = guard_point_metrics(trial_data, args, guard_points)
                raw_growth_ok = trial_raw_metrics["objective"] <= args.max_raw_objective_growth * max(
                    base_raw_metrics["objective"], 1e-300
                )
                guard_growth_ok = True
                if guard_points:
                    guard_growth_ok = (
                        trial_guard_metrics["objective"]
                        <= args.max_guard_objective_growth * max(base_guard_metrics["objective"], 1e-300)
                        and trial_guard_metrics["max_abs"]
                        <= args.max_guard_max_growth * max(base_guard_metrics["max_abs"], 1e-300)
                    )
                improved = trial_metrics["objective"] < base_metrics["objective"]
                accepted_here = improved and raw_growth_ok and guard_growth_ok
                line_trials.append(
                    {
                        **trial_record,
                        **trial_metrics,
                        "raw_objective": trial_raw_metrics["objective"],
                        "raw_max_abs": trial_raw_metrics["max_abs"],
                        "raw_growth_ok": raw_growth_ok,
                        "guard_metrics": trial_guard_metrics,
                        "guard_growth_ok": guard_growth_ok,
                        "accepted": accepted_here,
                        "tail_gate": tail_gate,
                    }
                )
                if accepted_here and (
                    best_accepted is None
                    or trial_metrics["objective"] < best_accepted["trial_metrics"]["objective"]
                ):
                    best_accepted = {
                        "block": block_spec["label"],
                        "trial_data": trial_data,
                        "trial_metrics": trial_metrics,
                        "update_metrics": update_metrics,
                        "alpha": alpha,
                    }
            if args.solve_mode == "full":
                break
        if best_accepted is not None:
            current = best_accepted["trial_data"]
            best_trial = current
            best_trial_metrics = best_accepted["trial_metrics"]
            accepted = True
        history.append(
            {
                "iteration": iteration,
                "base": base_metrics,
                "solve_mode": args.solve_mode,
                "accepted_block": best_accepted["block"] if best_accepted is not None else "",
                "accepted_alpha": best_accepted["alpha"] if best_accepted is not None else 0.0,
                "block_candidate_previews": candidate_previews,
                "selected_variables": len(system["variables"]),
                "row_groups": system["row_groups"],
                "raw_residual_metrics": system["raw_residual_metrics"],
                "row_scaling": system["row_scaling"],
                "base_guard_metrics": base_guard_metrics,
                "selected_by_chart": system["selected_by_chart"],
                "selected_by_block": system["selected_by_block"],
                "mortar_rows_available": system["mortar_rows_available"],
                "mortar_rows_active": system["mortar_rows_active"],
                "variable_score_preview": system["variable_score_preview"],
                "line_trials": line_trials,
                "accepted": accepted,
            }
        )
        if not accepted:
            break
    final_data = best_trial if best_trial is not None else current
    final_tail_gate = attach_stage0_tail_gate(final_data, args)
    final_metrics = best_trial_metrics if best_trial_metrics is not None else (history[-1]["base"] if history else {})
    final_data["twochart_newton_stage0_summary"] = {
        "status": RUN_STATUS if best_trial is not None else "TWOCHART_NEWTON_STAGE0_NO_IMPROVEMENT_NOT_PROOF",
        "newton_executed": True,
        "accepted_any_step": best_trial is not None,
        "iterations_requested": args.max_iter,
        "iterations_run": len(history),
        "final_metrics": final_metrics,
        "final_tail_gate": final_tail_gate,
        "row_definition": (
            "sampled PDE normalized residual rows plus sampled C0-Ck overlap "
            f"{args.mortar_coordinates} mortar rows"
        ),
        "diagnostic_vs_proof": "floating analytic Gauss-Newton diagnostic only; no interval proof",
    }
    return {
        "format": "twochart_newton_stage0_run_v1",
        "status": final_data["twochart_newton_stage0_summary"]["status"],
        "newton_executed": True,
        "optimization_faked": False,
        "input": args.input,
        "out": args.out,
        "accepted_any_step": best_trial is not None,
        "tail_legality": tail_legality,
        "requested_solver": {
            "blocks": list(blocks),
            "variable_charts": list(parse_variable_charts(args.variable_charts)),
            "residual_kind": args.residual_kind,
            "q2_policy": args.q2_policy,
            "mortar_order": args.mortar_order,
            "mortar_coordinates": args.mortar_coordinates,
            "mortar_q_samples": args.mortar_q_samples,
            "mortar_x_samples": args.mortar_x_samples,
            "mortar_active_count": args.mortar_active_count,
            "overlap_q_range": [args.overlap_q_min, args.overlap_q_max],
            "pde_qb_points": [[q, b] for q, b in parse_qb_points(args.pde_qb_points)],
            "guard_qb_points": [[q, b] for q, b in guard_points],
            "solve_mode": args.solve_mode,
            "block_search_labels": args.block_search_labels,
            "max_guard_objective_growth": args.max_guard_objective_growth,
            "max_guard_max_growth": args.max_guard_max_growth,
            "max_iter": args.max_iter,
            "trust": args.trust,
            "lm_lambda": args.lm_lambda,
            "max_variables": args.max_variables,
            "candidate_kq_max": args.candidate_kq_max,
            "candidate_kx_max": args.candidate_kx_max,
            "candidate_origin_degree_max": args.candidate_origin_degree_max,
            "candidate_pool_limit": args.candidate_pool_limit,
            "pde_weight": args.pde_weight,
            "mortar_weight": args.mortar_weight,
            "line_search": args.line_search,
            "include_origin_constants": args.include_origin_constants,
            "chart_balanced_selection": args.chart_balanced_selection,
            "row_normalization": args.row_normalization,
            "row_normalization_floor": args.row_normalization_floor,
            "row_scale_min": args.row_scale_min,
            "row_scale_max": args.row_scale_max,
            "max_raw_objective_growth": args.max_raw_objective_growth,
            "tail_gate_samples_per_patch": args.tail_gate_samples_per_patch,
            "forced_tol": args.forced_tol,
            "q2_tol": args.q2_tol,
        },
        "history": history,
        "candidate": final_data,
        "diagnostic_vs_proof": "floating sampled analytic Gauss-Newton run only; no interval proof",
    }


def build_plan(args: argparse.Namespace, data: dict[str, Any], hooks: HookReport) -> dict[str, Any]:
    blocks = parse_blocks(args.blocks)
    tail_legality = validate_hard_gates(data, args.q2_policy)
    hard_newton_schema = data.get("hard_newton_schema", {})
    residual_blocks = []
    unknown_blocks = []
    if isinstance(hard_newton_schema, dict):
        residual_blocks = hard_newton_schema.get("residual_blocks", [])  # type: ignore[assignment]
        unknown_blocks = hard_newton_schema.get("unknown_blocks", [])  # type: ignore[assignment]

    return {
        "format": "twochart_newton_stage0_dryrun_v1",
        "status": STATUS,
        "refusal_status": MISSING_HOOK_STATUS if not hooks.available else "",
        "dry_run": True,
        "newton_executed": False,
        "optimization_faked": False,
        "input": args.input,
        "out": args.out,
        "source_profile": {
            "format": data.get("format"),
            "status": data.get("status"),
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "source_profile_json": data.get("source_profile_json"),
        },
        "requested_solver": {
            "blocks": list(blocks),
            "variable_charts": list(parse_variable_charts(args.variable_charts)),
            "gamma_fixed": True,
            "B_fixed": True,
            "residual_kind": args.residual_kind,
            "q2_policy": args.q2_policy,
            "mortar_order": args.mortar_order,
            "mortar_coordinates": args.mortar_coordinates,
            "mortar_active_count": args.mortar_active_count,
            "chart_balanced_selection": args.chart_balanced_selection,
            "row_normalization": args.row_normalization,
            "max_iter": args.max_iter,
            "trust": args.trust,
            "lm_lambda": args.lm_lambda,
            "scan": args.scan,
            "solve_mode": args.solve_mode,
        },
        "hard_constraints": {
            "q2_policy": "zero",
            "tail_legality_all_ok": tail_legality.get("all_ok"),
            "tail_legality_status": tail_legality.get("status"),
            "gamma_B_policy": "fixed_until_twochart_solver_is_implemented",
            "interface_policy": "hard rows, not hidden penalties",
            "no_coefficient_finite_difference_jacobian": True,
        },
        "tail_legality": tail_legality,
        "planned_unknown_blocks": unknown_blocks,
        "planned_residual_blocks": residual_blocks,
        "planned_stages": [
            {
                "name": "stage0",
                "active_blocks": list(blocks),
                "goal": "assemble hard-constrained origin/interface Newton system",
                "execution": "blocked_until_residual_jacobian_hooks_exist",
            }
        ],
        "required_validator_hooks": asdict(hooks),
        "refusal_reason": (
            "Real Newton is disabled until validators/compactified_equations_twochart.py "
            "provides callable residual/Jacobian hooks."
        )
        if not hooks.available
        else "",
        "diagnostic_vs_proof": "dry-run solver plan only; no interval proof and no coefficient update",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Two-chart profile JSON.")
    parser.add_argument("--out", required=True, help="Candidate/profile JSON to write, or dry-run plan with --dry-run.")
    parser.add_argument("--report-out", default="", help="Optional full Stage-0 run report JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Write the old solver plan without mutating coefficients.")
    parser.add_argument("--blocks", default="origin,interface", help="Comma list: tail,origin,interface.")
    parser.add_argument("--variable-charts", default="tail,origin", help="Comma list of mutable charts: tail,origin.")
    parser.add_argument("--gamma-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--B-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--q2-policy", choices=("zero",), default="zero")
    parser.add_argument("--mortar-order", type=positive_int, default=4)
    parser.add_argument("--mortar-coordinates", choices=("RZ", "qx", "both"), default="RZ")
    parser.add_argument("--mortar-active-count", type=int, default=0)
    parser.add_argument("--mortar-q-samples", type=positive_int, default=3)
    parser.add_argument("--mortar-x-samples", type=positive_int, default=5)
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--pde-qb-points", default="")
    parser.add_argument("--guard-qb-points", default="", help="Semicolon-separated q,b points used only as line-search guards.")
    parser.add_argument("--max-guard-objective-growth", type=positive_float, default=1.0)
    parser.add_argument("--max-guard-max-growth", type=positive_float, default=1.0)
    parser.add_argument("--solve-mode", choices=("full", "block-search"), default="full")
    parser.add_argument(
        "--block-search-labels",
        default="",
        help="Comma list of block-search candidates to evaluate, e.g. full,chart:tail,chart:origin.",
    )
    parser.add_argument("--pde-weight", type=positive_float, default=1.0)
    parser.add_argument("--mortar-weight", type=positive_float, default=1e-6)
    parser.add_argument("--forced-tol", type=positive_float, default=1e-12)
    parser.add_argument("--q2-tol", type=positive_float, default=1e-12)
    parser.add_argument("--tail-gate-samples-per-patch", type=positive_int, default=9)
    parser.add_argument("--max-variables", type=positive_int, default=32)
    parser.add_argument("--candidate-kq-max", type=int, default=6)
    parser.add_argument("--candidate-kx-max", type=int, default=6)
    parser.add_argument("--candidate-origin-degree-max", type=int, default=6)
    parser.add_argument("--candidate-pool-limit", type=positive_int, default=512)
    parser.add_argument("--line-search", type=parse_float_list, default=parse_float_list("1,0.5,0.25,0.125"))
    parser.add_argument("--include-origin-constants", action="store_true")
    parser.add_argument("--chart-balanced-selection", action="store_true")
    parser.add_argument("--row-normalization", choices=("none", "jacobian", "residual-jacobian"), default="none")
    parser.add_argument("--row-normalization-floor", type=positive_float, default=1e-12)
    parser.add_argument("--row-scale-min", type=float, default=0.0)
    parser.add_argument("--row-scale-max", type=positive_float, default=1e6)
    parser.add_argument(
        "--max-raw-objective-growth",
        type=positive_float,
        default=1.0,
        help="Reject line-search steps whose unnormalized sampled objective grows by more than this factor.",
    )
    parser.add_argument("--max-iter", type=positive_int, default=20)
    parser.add_argument("--trust", type=positive_float, default=0.05)
    parser.add_argument("--lm-lambda", type=positive_float, default=1e-8)
    parser.add_argument("--scan", default="standard,focused,secondary,origin,edge")
    args = parser.parse_args()
    if args.overlap_q_max <= args.overlap_q_min:
        parser.error("--overlap-q-max must be greater than --overlap-q-min")
    if args.mortar_active_count < 0:
        parser.error("--mortar-active-count must be nonnegative")
    if args.candidate_kq_max < 0 or args.candidate_kx_max < 0 or args.candidate_origin_degree_max < 0:
        parser.error("candidate degree caps must be nonnegative")
    if not args.line_search or any(alpha <= 0.0 for alpha in args.line_search):
        parser.error("--line-search must contain positive floats")
    if args.row_scale_min < 0.0:
        parser.error("--row-scale-min must be nonnegative")
    if args.row_scale_min > args.row_scale_max:
        parser.error("--row-scale-min must be <= --row-scale-max")

    data = load_json(args.input)
    validate_input_schema(data, args.input)
    hooks = hook_report()

    if args.dry_run:
        result = build_plan(args, data, hooks)
        save_json(args.out, result)
    else:
        result = run_stage0(args, data, hooks)
        if result.get("newton_executed"):
            candidate = result["candidate"]
            run_report = {key: value for key, value in result.items() if key != "candidate"}
            candidate["twochart_newton_stage0_run_report"] = run_report
            save_json(args.out, candidate)
            if args.report_out:
                save_json(args.report_out, run_report)
        else:
            save_json(args.out, result)
            if args.report_out:
                save_json(args.report_out, result)

    print(f"input={args.input}")
    print(f"saved={args.out}")
    if args.report_out:
        print(f"report_saved={args.report_out}")
    print(f"status={result['status']}")
    print(f"newton_executed={result['newton_executed']}")
    print(f"q2_policy={args.q2_policy}")
    if result.get("newton_executed"):
        print(f"accepted_any_step={result['accepted_any_step']}")
        if result.get("history"):
            first = result["history"][0]
            last = result["history"][-1]
            print(f"iterations_run={len(result['history'])}")
            print(f"row_groups={last['row_groups']}")
            print(f"row_normalization={args.row_normalization}")
            print(f"solve_mode={args.solve_mode}")
            print(f"accepted_block={last.get('accepted_block', '')}")
            print(f"selected_by_chart={last.get('selected_by_chart', {})}")
            print(f"selected_variables={last['selected_variables']}")
            print(f"base_objective_first={first['base']['objective']:.12e}")
            final_metrics = result["candidate"]["twochart_newton_stage0_summary"].get("final_metrics", {})
            if final_metrics:
                print(f"final_objective={final_metrics.get('objective', float('nan')):.12e}")
                print(f"final_max_abs={final_metrics.get('max_abs', float('nan')):.12e}")
    else:
        print(f"tail_legality_all_ok={result['hard_constraints']['tail_legality_all_ok']}")
    print(f"hook_module={hooks.module}")
    print(f"hook_available={hooks.available}")
    if not hooks.available:
        print(f"refusal_status={result['refusal_status']}")
        print(f"missing_hooks={','.join(hooks.missing_hooks)}")


if __name__ == "__main__":
    main()
