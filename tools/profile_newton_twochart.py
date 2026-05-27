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
import concurrent.futures
import copy
import ctypes
import importlib
import json
import math
import os
import sys
import time
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

_STAGE0_WORKER_DATA: dict[str, Any] | None = None
_STAGE0_WORKER_PROJECTION: Any = None
_STAGE0_WORKER_VARIABLES: list[Any] = []
_STAGE0_WORKER_RESIDUAL_KIND = "normalized-structural"
_STAGE0_WORKER_NATIVE_C = False


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


def parse_scan_names(raw: str) -> tuple[str, ...]:
    from validators.compactified_equations_twochart import SCAN_PRESETS

    names = tuple(item.strip() for item in raw.split(",") if item.strip())
    if not names:
        raise ValueError("scan list must contain at least one preset")
    unknown = [name for name in names if name not in SCAN_PRESETS]
    if unknown:
        raise ValueError(f"unknown scan preset(s): {', '.join(unknown)}")
    return names


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


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def parse_float_list(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def parse_coordinate_values(raw: str, name: str, lo: float, hi: float) -> list[float]:
    values = parse_float_list(raw)
    for value in values:
        if not math.isfinite(value):
            raise ValueError(f"{name} contains non-finite value {value!r}")
        if value < lo or value > hi:
            raise ValueError(f"{name} values must lie in [{lo}, {hi}]; got {value!r}")
    return values


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


def grid_values(start: float, stop: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("grid count must be positive")
    if count == 1:
        return [0.5 * (start + stop)]
    step = (stop - start) / float(count - 1)
    return [start + step * index for index in range(count)]


def dedupe_qb_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    seen: set[tuple[float, float]] = set()
    out: list[tuple[float, float]] = []
    for q, b in points:
        key = (round(float(q), 15), round(float(b), 15))
        if key in seen:
            continue
        seen.add(key)
        out.append((float(q), float(b)))
    return out


def qb_key(q: float, b: float) -> tuple[float, float]:
    return (round(float(q), 15), round(float(b), 15))


def generated_guard_qb_points(args: argparse.Namespace) -> list[tuple[float, float]]:
    if args.guard_grid == "none":
        return []
    q_values = grid_values(args.guard_q_min, args.guard_q_max, args.guard_q_samples)
    b_values = grid_values(args.guard_b_min, args.guard_b_max, args.guard_b_samples)
    return [(q, b) for q in q_values for b in b_values]


def generated_seam_guard_qb_points(args: argparse.Namespace) -> list[tuple[float, float]]:
    if args.guard_seam_sides == "none":
        return []
    if args.guard_seam_b_points.strip():
        b_values = parse_float_list(args.guard_seam_b_points)
    else:
        b_values = grid_values(args.guard_b_min, args.guard_b_max, args.guard_b_samples)
    if args.guard_seam_sides == "below":
        q_values = [args.guard_seam_q - args.guard_seam_eps]
    elif args.guard_seam_sides == "above":
        q_values = [args.guard_seam_q + args.guard_seam_eps]
    else:
        q_values = [args.guard_seam_q - args.guard_seam_eps, args.guard_seam_q + args.guard_seam_eps]
    return [(q, b) for q in q_values for b in b_values]


def guard_qb_points_from_args(args: argparse.Namespace) -> dict[str, Any]:
    explicit = parse_optional_qb_points(args.guard_qb_points)
    generated = generated_guard_qb_points(args)
    seam = generated_seam_guard_qb_points(args)
    combined = dedupe_qb_points(explicit + generated + seam)
    return {
        "explicit": explicit,
        "generated": generated,
        "seam": seam,
        "combined": combined,
    }


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
    if limit <= 0:
        return variables
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


def mortar_row_jacobian_norm(row: Any) -> float:
    return math.sqrt(sum(float(value) * float(value) for _var_index, value in row.jacobian))


def mortar_leverage_score(
    row: Any,
    jac_value: float,
    weight: float,
    normalization: str,
    row_norm: float | None = None,
) -> float:
    base = abs(weight * float(row.residual) * float(jac_value))
    if normalization == "row-norm":
        if row_norm is None:
            row_norm = mortar_row_jacobian_norm(row)
        return base / max(row_norm, 1e-300)
    return base


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


def _merge_native_stat(total: dict[str, Any], stat: dict[str, Any]) -> None:
    if not stat.get("enabled"):
        return
    total["enabled"] = True
    if stat.get("used"):
        total["used"] = int(total.get("used", 0)) + 1
    total["cases"] = int(total.get("cases", 0)) + int(stat.get("cases", 0))
    total["seconds"] = float(total.get("seconds", 0.0)) + float(stat.get("seconds", 0.0))


def residual_with_optional_native_tail_exact(
    data: dict[str, Any],
    projection: Any,
    q: float,
    b: float,
    residual_kind: str,
    use_native_c: bool,
) -> tuple[Any, dict[str, Any]]:
    from validators.compactified_equations import qb_to_rz, residual_with_kind

    if use_native_c:
        from validators.compactified_equations_twochart import native_tail_exact_residual_with_kind

        residual, stats = native_tail_exact_residual_with_kind(data, projection, q, b, residual_kind)
        if residual is not None:
            return residual, stats
    r, z = qb_to_rz(q, b)
    raw = projection.exact_residual_at(r, z)
    return residual_with_kind(raw, q, b, projection.p, residual_kind), {
        "enabled": bool(use_native_c),
        "used": False,
        "cases": 0,
        "seconds": 0.0,
    }


def native_stage0_prediction_scan(
    system: dict[str, Any],
    delta: list[float],
    alphas: list[float],
    max_update_norm: float,
) -> tuple[dict[float, dict[str, float]], dict[str, Any]]:
    if not alphas:
        return {}, {"enabled": True, "calls": 0, "cases": 0, "seconds": 0.0}
    from validators.twochart_mortar_jacobian import native_c_library

    residual_vector = [float(value) for value in system["residual_vector"]]
    jacobian_rows = [[float(value) for value in row] for row in system["jacobian_rows"]]
    row_count = len(residual_vector)
    column_count = len(delta)
    alpha_count = len(alphas)
    if row_count == 0 or column_count == 0:
        return {
            float(alpha): {"count": 0.0, "max_abs": 0.0, "rms": 0.0, "objective": 0.0, "l2": 0.0}
            for alpha in alphas
        }, {"enabled": True, "calls": 1, "cases": 0, "seconds": 0.0}

    norm = math.sqrt(sum(value * value for value in delta))
    trust_scale = 1.0
    if max_update_norm > 0.0 and norm > max_update_norm:
        trust_scale = max_update_norm / max(norm, 1e-300)
    applied = [float(alpha) * trust_scale for alpha in alphas]

    double_jacobian = ctypes.c_double * (row_count * column_count)
    double_rows = ctypes.c_double * row_count
    double_columns = ctypes.c_double * column_count
    double_alphas = ctypes.c_double * alpha_count
    int_alphas = ctypes.c_int * alpha_count
    flat_jacobian = [value for row in jacobian_rows for value in row]
    out_l2 = double_alphas()
    out_max_abs = double_alphas()
    out_objective = double_alphas()
    statuses = int_alphas()
    lib = native_c_library()
    start = time.perf_counter()
    rc = lib.nsproof_stage0_prediction_scan_batch(
        row_count,
        column_count,
        alpha_count,
        double_jacobian(*flat_jacobian),
        double_rows(*residual_vector),
        double_columns(*[float(value) for value in delta]),
        double_alphas(*applied),
        out_l2,
        out_max_abs,
        out_objective,
        statuses,
    )
    elapsed = time.perf_counter() - start
    if rc != 0:
        bad_statuses = sorted(set(int(statuses[index]) for index in range(alpha_count)))
        raise RuntimeError(f"native C prediction scan failed rc={rc} statuses={bad_statuses}")

    metrics: dict[float, dict[str, float]] = {}
    for index, alpha in enumerate(alphas):
        l2 = float(out_l2[index])
        metrics[float(alpha)] = {
            "count": float(row_count),
            "max_abs": float(out_max_abs[index]),
            "rms": l2 / math.sqrt(row_count),
            "objective": float(out_objective[index]),
            "l2": l2,
            "alpha_applied": applied[index],
        }
    return metrics, {
        "enabled": True,
        "calls": 1,
        "cases": row_count * column_count * alpha_count,
        "rows": row_count,
        "columns": column_count,
        "alphas": alpha_count,
        "seconds": elapsed,
    }


def guard_point_metrics(data: dict[str, Any], args: argparse.Namespace, points: list[tuple[float, float]]) -> dict[str, Any]:
    if not points:
        return {"enabled": False, **vector_metrics([])}
    from validators.compactified_equations import compactified_residual_defined
    from validators.compactified_equations_twochart import projection_from_twochart

    projection = projection_from_twochart(data)
    values: list[float] = []
    skipped = 0
    worst: dict[str, Any] = {"abs": -1.0}
    native_stats: dict[str, Any] = {"enabled": bool(args.native_c), "used": 0, "cases": 0, "seconds": 0.0}
    for q, b in points:
        if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
            skipped += 1
            continue
        residual, point_native = residual_with_optional_native_tail_exact(
            data,
            projection,
            q,
            b,
            args.residual_kind,
            bool(args.native_c),
        )
        _merge_native_stat(native_stats, point_native)
        for component, value in (("e_psi", residual.e_psi), ("e_gamma", residual.e_gamma)):
            values.append(value)
            if abs(value) > worst["abs"]:
                worst = {"q": q, "b": b, "component": component, "value": value, "abs": abs(value)}
    return {
        "enabled": True,
        "points_requested": len(points),
        "skipped": skipped,
        "worst": worst,
        "native_c_tail_exact": native_stats,
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


def _init_stage0_point_worker(data: dict[str, Any], variables: list[Any], residual_kind: str, native_c: bool) -> None:
    global _STAGE0_WORKER_DATA
    global _STAGE0_WORKER_PROJECTION
    global _STAGE0_WORKER_VARIABLES
    global _STAGE0_WORKER_RESIDUAL_KIND
    global _STAGE0_WORKER_NATIVE_C
    from validators.compactified_equations_twochart import projection_from_twochart

    _STAGE0_WORKER_DATA = data
    _STAGE0_WORKER_PROJECTION = projection_from_twochart(data)
    _STAGE0_WORKER_VARIABLES = variables
    _STAGE0_WORKER_RESIDUAL_KIND = residual_kind
    _STAGE0_WORKER_NATIVE_C = native_c


def _stage0_point_worker(task: tuple[float, float, float, str, str]) -> dict[str, Any]:
    if _STAGE0_WORKER_DATA is None or _STAGE0_WORKER_PROJECTION is None:
        raise RuntimeError("stage-0 point worker was not initialized")
    from validators.compactified_equations import Residual, compactified_residual_defined, qb_to_rz, residual_with_kind
    from validators.compactified_equations_twochart import (
        linearized_residual_with_kind,
        native_tail_linearized_residuals_with_kind,
    )

    q, b, weight, label, row_type = task
    projection = _STAGE0_WORKER_PROJECTION
    if not compactified_residual_defined(q, b, projection.p, _STAGE0_WORKER_RESIDUAL_KIND):
        return {"skipped": True, "q": q, "b": b, "label": label, "row_type": row_type}
    r, z = qb_to_rz(q, b)
    raw = projection.exact_residual_at(r, z)
    residual = residual_with_kind(raw, q, b, projection.p, _STAGE0_WORKER_RESIDUAL_KIND)
    native_tail_columns: dict[int, Any] = {}
    native_stats: dict[str, Any] = {"enabled": False, "cases": 0, "seconds": 0.0}
    if _STAGE0_WORKER_NATIVE_C:
        native_tail_columns, native_stats = native_tail_linearized_residuals_with_kind(
            _STAGE0_WORKER_DATA,
            projection,
            _STAGE0_WORKER_VARIABLES,
            q,
            b,
            _STAGE0_WORKER_RESIDUAL_KIND,
        )
    columns = []
    for variable in _STAGE0_WORKER_VARIABLES:
        if _STAGE0_WORKER_NATIVE_C and variable.chart == "tail":
            columns.append(native_tail_columns.get(variable.index, Residual(e_psi=0.0, e_gamma=0.0)))
        else:
            columns.append(
                linearized_residual_with_kind(
                    _STAGE0_WORKER_DATA,
                    projection,
                    variable,
                    q,
                    b,
                    _STAGE0_WORKER_RESIDUAL_KIND,
                )
            )
    return {
        "skipped": False,
        "q": q,
        "b": b,
        "label": label,
        "row_type": row_type,
        "weight": weight,
        "residuals": {"e_psi": residual.e_psi, "e_gamma": residual.e_gamma},
        "jacobian_rows": {
            "e_psi": [weight * column.e_psi for column in columns],
            "e_gamma": [weight * column.e_gamma for column in columns],
        },
        "native_c_pde": native_stats,
    }


def build_stage0_point_rows(
    data: dict[str, Any],
    projection: Any,
    selected: list[Any],
    points: list[tuple[float, float]],
    residual_kind: str,
    weight: float,
    label: str,
    row_type: str,
    workers: int,
    use_native_c: bool = False,
) -> list[dict[str, Any]]:
    from validators.compactified_equations import Residual, compactified_residual_defined, qb_to_rz, residual_with_kind
    from validators.compactified_equations_twochart import linearized_residual_with_kind

    if not points:
        return []
    if workers > 1 and len(points) > 1:
        tasks = [(float(q), float(b), float(weight), label, row_type) for q, b in points]
        try:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                initializer=_init_stage0_point_worker,
                initargs=(data, selected, residual_kind, use_native_c),
            ) as pool:
                return [item for item in pool.map(_stage0_point_worker, tasks) if not item.get("skipped")]
        except Exception as exc:  # noqa: BLE001 - fall back to serial diagnostics.
            return [
                {
                    "skipped": True,
                    "fallback_reason": f"{type(exc).__name__}: {exc}",
                    "q": float(points[0][0]),
                    "b": float(points[0][1]),
                    "label": label,
                    "row_type": row_type,
                }
            ] + build_stage0_point_rows(
                data,
                projection,
                selected,
                points,
                residual_kind,
                weight,
                label,
                row_type,
                workers=1,
                use_native_c=use_native_c,
            )

    rows: list[dict[str, Any]] = []
    for q, b in points:
        q = float(q)
        b = float(b)
        if not compactified_residual_defined(q, b, projection.p, residual_kind):
            continue
        r, z = qb_to_rz(q, b)
        raw = projection.exact_residual_at(r, z)
        residual = residual_with_kind(raw, q, b, projection.p, residual_kind)
        native_tail_columns: dict[int, Any] = {}
        native_stats: dict[str, Any] = {"enabled": False, "cases": 0, "seconds": 0.0}
        if use_native_c:
            from validators.compactified_equations_twochart import native_tail_linearized_residuals_with_kind

            native_tail_columns, native_stats = native_tail_linearized_residuals_with_kind(
                data,
                projection,
                selected,
                q,
                b,
                residual_kind,
            )
        columns = []
        for variable in selected:
            if use_native_c and variable.chart == "tail":
                columns.append(native_tail_columns.get(variable.index, Residual(e_psi=0.0, e_gamma=0.0)))
            else:
                columns.append(linearized_residual_with_kind(data, projection, variable, q, b, residual_kind))
        rows.append(
            {
                "skipped": False,
                "q": q,
                "b": b,
                "label": label,
                "row_type": row_type,
                "weight": weight,
                "residuals": {"e_psi": residual.e_psi, "e_gamma": residual.e_gamma},
                "jacobian_rows": {
                    "e_psi": [weight * column.e_psi for column in columns],
                    "e_gamma": [weight * column.e_gamma for column in columns],
                },
                "native_c_pde": native_stats,
            }
        )
    return rows


def build_stage0_system(data: dict[str, Any], args: argparse.Namespace, blocks: tuple[str, ...]) -> dict[str, Any]:
    from validators.compactified_equations import Residual, compactified_residual_defined, qb_to_rz, residual_with_kind
    from validators.compactified_equations_twochart import (
        linearized_residual_with_kind,
        native_tail_linearized_residuals_with_kind,
        projection_from_twochart,
    )
    from validators.twochart_mortar_jacobian import (
        build_rows,
        build_rz_rows,
        enumerate_coefficients,
        grid,
        native_c_rz_stats,
        reset_native_c_rz_stats,
    )

    projection = projection_from_twochart(data)
    reset_native_c_rz_stats()
    all_variables = enumerate_coefficients(data)
    all_variables_by_index = {variable.index: variable for variable in all_variables}
    manual_pde_points = [] if args.no_default_pde_points and not args.pde_qb_points.strip() else parse_qb_points(args.pde_qb_points)
    pde_scan_active_report = residual_scan_active_qb_points(data, args)
    pde_points = dedupe_qb_points(manual_pde_points + list(pde_scan_active_report.get("points", [])))
    variable_charts = parse_variable_charts(args.variable_charts)
    explicit_mortar_q_values = parse_coordinate_values(args.mortar_q_values, "--mortar-q-values", 0.0, 1.0)
    explicit_mortar_x_values = parse_coordinate_values(args.mortar_x_values, "--mortar-x-values", 0.0, 1.0)
    q_values = (
        explicit_mortar_q_values
        if "interface" in blocks and explicit_mortar_q_values
        else grid(args.overlap_q_min, args.overlap_q_max, args.mortar_q_samples)
        if "interface" in blocks
        else []
    )
    x_values = (
        explicit_mortar_x_values
        if "interface" in blocks and explicit_mortar_x_values
        else grid(0.0, 1.0, args.mortar_x_samples)
        if "interface" in blocks
        else []
    )
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
    pre_score_candidate_count = len(candidate_variables)
    candidate_variables = cap_candidate_pool(candidate_variables, args.candidate_pool_limit)
    candidate_by_index = {variable.index: variable for variable in candidate_variables}
    injected_mortar_candidates: list[dict[str, Any]] = []

    def build_mortar_rows(variables: list[Any]) -> list[Any]:
        if args.mortar_coordinates == "RZ":
            return build_rz_rows(data, variables, q_values, x_values, args.mortar_order, use_native_c=args.native_c)
        if args.mortar_coordinates == "qx":
            return build_rows(data, variables, q_values, x_values, args.mortar_order)
        return build_rows(data, variables, q_values, x_values, args.mortar_order) + build_rz_rows(
            data, variables, q_values, x_values, args.mortar_order, use_native_c=args.native_c
        )

    def build_mortar_audit_rows() -> list[Any]:
        if "interface" not in blocks or args.max_mortar_audit_growth <= 0.0:
            return []
        audit_order = args.line_search_mortar_audit_order
        if audit_order < 0:
            audit_order = args.mortar_order
        explicit_audit_q_values = parse_coordinate_values(
            args.line_search_mortar_audit_q_values,
            "--line-search-mortar-audit-q-values",
            0.0,
            1.0,
        )
        explicit_audit_x_values = parse_coordinate_values(
            args.line_search_mortar_audit_x_values,
            "--line-search-mortar-audit-x-values",
            0.0,
            1.0,
        )
        audit_q_samples = args.line_search_mortar_audit_q_samples or max(args.mortar_q_samples, 9)
        audit_x_samples = args.line_search_mortar_audit_x_samples or max(args.mortar_x_samples, 9)
        audit_q_values = (
            explicit_audit_q_values
            if explicit_audit_q_values
            else grid(args.overlap_q_min, args.overlap_q_max, audit_q_samples)
        )
        audit_x_values = explicit_audit_x_values if explicit_audit_x_values else grid(0.0, 1.0, audit_x_samples)
        if args.mortar_coordinates == "RZ":
            rows = build_rz_rows(data, [], audit_q_values, audit_x_values, audit_order, use_native_c=False)
        elif args.mortar_coordinates == "qx":
            rows = build_rows(data, [], audit_q_values, audit_x_values, audit_order)
        else:
            rows = build_rows(data, [], audit_q_values, audit_x_values, audit_order) + build_rz_rows(
                data, [], audit_q_values, audit_x_values, audit_order, use_native_c=False
            )
        if args.line_search_mortar_audit_active_count > 0 and len(rows) > args.line_search_mortar_audit_active_count:
            rows = sorted(rows, key=lambda row: abs(row.residual), reverse=True)[
                : args.line_search_mortar_audit_active_count
            ]
        return rows

    mortar_audit_rows = build_mortar_audit_rows()

    if "interface" in blocks and args.mortar_jacobian_candidate_count > 0:
        mortar_variable_pool = [
            variable
            for variable in all_variables
            if variable_allowed_for_blocks(variable, blocks)
            and variable_allowed_for_chart_filter(variable, variable_charts)
            and (args.include_origin_constants or not variable_is_origin_constant(variable))
            and variable_relevant_for_samples(data, variable, pde_points, mortar_points)
            and not tail_variable_is_gate_locked(data, variable)
        ]
        exploratory_rows = build_mortar_rows(mortar_variable_pool)
        if args.mortar_active_count > 0 and len(exploratory_rows) > args.mortar_active_count:
            exploratory_rows = sorted(exploratory_rows, key=lambda row: abs(row.residual), reverse=True)[
                : args.mortar_active_count
            ]
        highest_order_rows = [
            row for row in exploratory_rows if int(row.dq_order) + int(row.dx_order) == int(args.mortar_order)
        ]
        injection_rows = highest_order_rows or exploratory_rows
        injection_scores: dict[int, float] = {}
        injection_best: dict[int, tuple[str, float]] = {}
        row_local_records: list[tuple[float, Any, int, float]] = []
        for row in injection_rows:
            row_norm = mortar_row_jacobian_norm(row)
            best_by_chart: dict[str, tuple[float, int, float]] = {}
            for var_index, jac_value in row.jacobian:
                score = mortar_leverage_score(
                    row,
                    jac_value,
                    args.mortar_weight,
                    args.mortar_score_normalization,
                    row_norm=row_norm,
                )
                injection_scores[var_index] = injection_scores.get(var_index, 0.0) + score
                current_best = injection_best.get(var_index)
                if current_best is None or score > current_best[1]:
                    injection_best[var_index] = (row.derivative_label, score)
                variable = all_variables_by_index.get(var_index)
                if variable is None:
                    continue
                current_chart_best = best_by_chart.get(variable.chart)
                if current_chart_best is None or score > current_chart_best[0]:
                    best_by_chart[variable.chart] = (score, var_index, jac_value)
            for score, var_index, jac_value in best_by_chart.values():
                row_local_records.append((score, row, var_index, jac_value))

        injected_indexes: set[int] = set()
        for score, row, var_index, jac_value in sorted(row_local_records, key=lambda item: item[0], reverse=True):
            if len(injected_mortar_candidates) >= args.mortar_jacobian_candidate_count:
                break
            if var_index in candidate_by_index or var_index in injected_indexes:
                continue
            variable = all_variables_by_index[var_index]
            candidate_variables.append(variable)
            candidate_by_index[var_index] = variable
            injected_indexes.add(var_index)
            injected_mortar_candidates.append(
                {
                    "variable": variable.label,
                    "var_index": var_index,
                    "chart": variable.chart,
                    "component": variable.component,
                    "score": score,
                    "best_row_derivative": row.derivative_label,
                    "best_row_score": score,
                    "row_derivative": row.derivative_label,
                    "row_q": row.q,
                    "row_x": row.x,
                    "row_component": row.component,
                    "row_normalized_score": score,
                    "jacobian_value": jac_value,
                    "selection_mode": "row_local_chart",
                }
            )

        for var_index, score in sorted(injection_scores.items(), key=lambda item: item[1], reverse=True):
            if len(injected_mortar_candidates) >= args.mortar_jacobian_candidate_count:
                break
            if var_index in candidate_by_index or var_index in injected_indexes:
                continue
            variable = all_variables_by_index[var_index]
            candidate_variables.append(variable)
            candidate_by_index[var_index] = variable
            injected_indexes.add(var_index)
            derivative_label, best_score = injection_best[var_index]
            injected_mortar_candidates.append(
                {
                    "variable": variable.label,
                    "var_index": var_index,
                    "chart": variable.chart,
                    "component": variable.component,
                    "score": score,
                    "best_row_derivative": derivative_label,
                    "best_row_score": best_score,
                    "selection_mode": "global",
                }
            )

    pde_rows: list[dict[str, Any]] = []
    pde_component_selection: dict[tuple[float, float], set[str]] = {}
    pde_point_residuals: list[dict[str, Any]] = []
    for q, b in pde_points:
        if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
            continue
        r, z = qb_to_rz(q, b)
        raw = projection.exact_residual_at(r, z)
        residual = residual_with_kind(raw, q, b, projection.p, args.residual_kind)
        pde_point_residuals.append(
            {
                "q": q,
                "b": b,
                "e_psi": float(residual.e_psi),
                "e_gamma": float(residual.e_gamma),
                "worst_component": "e_psi"
                if abs(float(residual.e_psi)) >= abs(float(residual.e_gamma))
                else "e_gamma",
                "max_abs": max(abs(float(residual.e_psi)), abs(float(residual.e_gamma))),
            }
        )
    if args.pde_component_mode == "both":
        for record in pde_point_residuals:
            pde_component_selection[qb_key(record["q"], record["b"])] = {"e_psi", "e_gamma"}
    elif args.pde_component_mode == "worst-per-point":
        for record in pde_point_residuals:
            pde_component_selection[qb_key(record["q"], record["b"])] = {str(record["worst_component"])}
    elif args.pde_component_mode == "worst-global":
        if pde_point_residuals:
            worst_record = max(pde_point_residuals, key=lambda item: float(item["max_abs"]))
            pde_component_selection[qb_key(worst_record["q"], worst_record["b"])] = {
                str(worst_record["worst_component"])
            }
    else:  # pragma: no cover - argparse choices enforce this.
        raise ValueError(f"unknown pde component mode {args.pde_component_mode!r}")

    residual_by_point = {qb_key(record["q"], record["b"]): record for record in pde_point_residuals}
    injected_pde_candidates: list[dict[str, Any]] = []
    native_c_pde_injection = {"enabled": False, "cases": 0, "seconds": 0.0}
    if args.pde_jacobian_candidate_count > 0 and pde_component_selection:
        pde_variable_pool = [
            variable
            for variable in all_variables
            if variable_allowed_for_blocks(variable, blocks)
            and variable_allowed_for_chart_filter(variable, variable_charts)
            and (args.include_origin_constants or not variable_is_origin_constant(variable))
            and variable_relevant_for_samples(data, variable, pde_points, [])
            and variable_under_candidate_caps(variable, args)
            and not tail_variable_is_gate_locked(data, variable)
        ]
        injection_scores: dict[int, float] = {}
        injection_best: dict[int, dict[str, Any]] = {}
        row_local_records: dict[tuple[float, float, str], list[dict[str, Any]]] = {}
        for q, b in pde_points:
            key = qb_key(q, b)
            selected_components = pde_component_selection.get(key, set())
            record = residual_by_point.get(key)
            if not selected_components or record is None:
                continue
            native_tail_columns: dict[int, Any] = {}
            if args.native_c:
                native_tail_columns, native_stats = native_tail_linearized_residuals_with_kind(
                    data,
                    projection,
                    pde_variable_pool,
                    q,
                    b,
                    args.residual_kind,
                )
                if native_stats.get("enabled"):
                    native_c_pde_injection["enabled"] = True
                    native_c_pde_injection["cases"] += int(native_stats.get("cases", 0))
                    native_c_pde_injection["seconds"] += float(native_stats.get("seconds", 0.0))
            for variable in pde_variable_pool:
                if args.native_c and variable.chart == "tail":
                    column = native_tail_columns.get(variable.index, Residual(e_psi=0.0, e_gamma=0.0))
                else:
                    column = linearized_residual_with_kind(data, projection, variable, q, b, args.residual_kind)
                component_scores: list[tuple[str, float, float, float]] = []
                if "e_psi" in selected_components:
                    jac = float(column.e_psi)
                    score = abs(args.pde_weight * jac * float(record["e_psi"]))
                    component_scores.append(("e_psi", score, jac, float(record["e_psi"])))
                    if math.isfinite(score) and score > 0.0:
                        row_local_records.setdefault((float(q), float(b), "e_psi"), []).append(
                            {
                                "var_index": variable.index,
                                "score": score,
                                "q": float(q),
                                "b": float(b),
                                "component": "e_psi",
                                "jacobian_value": jac,
                                "residual": float(record["e_psi"]),
                            }
                        )
                if "e_gamma" in selected_components:
                    jac = float(column.e_gamma)
                    score = abs(args.pde_weight * jac * float(record["e_gamma"]))
                    component_scores.append(("e_gamma", score, jac, float(record["e_gamma"])))
                    if math.isfinite(score) and score > 0.0:
                        row_local_records.setdefault((float(q), float(b), "e_gamma"), []).append(
                            {
                                "var_index": variable.index,
                                "score": score,
                                "q": float(q),
                                "b": float(b),
                                "component": "e_gamma",
                                "jacobian_value": jac,
                                "residual": float(record["e_gamma"]),
                            }
                        )
                finite_scores = [item for item in component_scores if math.isfinite(item[1]) and item[1] > 0.0]
                if not finite_scores:
                    continue
                score_sum = sum(item[1] for item in finite_scores)
                injection_scores[variable.index] = injection_scores.get(variable.index, 0.0) + score_sum
                best_component = max(finite_scores, key=lambda item: item[1])
                current_best = injection_best.get(variable.index)
                if current_best is None or best_component[1] > float(current_best["score"]):
                    injection_best[variable.index] = {
                        "q": float(q),
                        "b": float(b),
                        "component": best_component[0],
                        "score": best_component[1],
                        "jacobian_value": best_component[2],
                        "residual": best_component[3],
                    }

        prioritized_pde_indexes: set[int] = set()

        def prioritize_pde_candidate(var_index: int, score: float, best: dict[str, Any], selection_mode: str) -> bool:
            if len(injected_pde_candidates) >= args.pde_jacobian_candidate_count:
                return False
            if var_index in prioritized_pde_indexes:
                return False
            variable = all_variables_by_index[var_index]
            if var_index not in candidate_by_index:
                candidate_variables.append(variable)
                candidate_by_index[var_index] = variable
            prioritized_pde_indexes.add(var_index)
            injected_pde_candidates.append(
                {
                    "variable": variable.label,
                    "var_index": var_index,
                    "chart": variable.chart,
                    "component": variable.component,
                    "block": variable.block,
                    "score": score,
                    "best_row_q": best.get("q"),
                    "best_row_b": best.get("b"),
                    "best_row_component": best.get("component"),
                    "best_row_score": best.get("score"),
                    "best_row_residual": best.get("residual"),
                    "jacobian_value": best.get("jacobian_value"),
                    "selection_mode": selection_mode,
                }
            )
            return True

        row_keys = sorted(
            row_local_records,
            key=lambda key: abs(float(row_local_records[key][0].get("residual", 0.0))) if row_local_records[key] else 0.0,
            reverse=True,
        )
        per_row_budget = max(1, args.pde_jacobian_candidate_count // max(1, len(row_keys))) if row_keys else 0
        for row_key in row_keys:
            added_for_row = 0
            for record in sorted(row_local_records[row_key], key=lambda item: float(item["score"]), reverse=True):
                if added_for_row >= per_row_budget:
                    break
                if prioritize_pde_candidate(
                    int(record["var_index"]),
                    float(record["score"]),
                    record,
                    "pde_jacobian_row_local",
                ):
                    added_for_row += 1

        for var_index, score in sorted(injection_scores.items(), key=lambda item: item[1], reverse=True):
            if len(injected_pde_candidates) >= args.pde_jacobian_candidate_count:
                break
            best = injection_best.get(var_index, {})
            prioritize_pde_candidate(var_index, score, best, "pde_jacobian_global")

    variable_scores = {variable.index: 0.0 for variable in candidate_variables}
    native_c_pde_prescore = {"enabled": False, "cases": 0, "seconds": 0.0}
    for q, b in pde_points:
        key = qb_key(q, b)
        record = residual_by_point.get(key)
        if record is None:
            continue
        selected_components = pde_component_selection.get(key, set())
        if not selected_components:
            continue
        for component in ("e_psi", "e_gamma"):
            if component in selected_components:
                pde_rows.append({"q": q, "b": b, "component": component, "residual": record[component]})
        native_tail_columns: dict[int, Any] = {}
        if args.native_c:
            native_tail_columns, native_stats = native_tail_linearized_residuals_with_kind(
                data,
                projection,
                candidate_variables,
                q,
                b,
                args.residual_kind,
            )
            if native_stats.get("enabled"):
                native_c_pde_prescore["enabled"] = True
                native_c_pde_prescore["cases"] += int(native_stats.get("cases", 0))
                native_c_pde_prescore["seconds"] += float(native_stats.get("seconds", 0.0))
        for variable in candidate_variables:
            if args.native_c and variable.chart == "tail":
                column = native_tail_columns.get(variable.index, Residual(e_psi=0.0, e_gamma=0.0))
            else:
                column = linearized_residual_with_kind(data, projection, variable, q, b, args.residual_kind)
            if "e_psi" in selected_components:
                variable_scores[variable.index] += abs(column.e_psi * float(record["e_psi"]))
            if "e_gamma" in selected_components:
                variable_scores[variable.index] += abs(column.e_gamma * float(record["e_gamma"]))

    mortar_rows = []
    mortar_rows_available = 0
    mortar_rows_unfiltered_max_abs = 0.0
    mortar_rows_unfiltered_worst: dict[str, Any] = {}
    if "interface" in blocks:
        mortar_rows_all = build_mortar_rows(candidate_variables)
        mortar_rows_available = len(mortar_rows_all)
        if mortar_rows_all:
            worst_mortar = max(mortar_rows_all, key=lambda row: abs(row.residual))
            mortar_rows_unfiltered_max_abs = abs(worst_mortar.residual)
            mortar_rows_unfiltered_worst = worst_mortar.as_json()
        mortar_rows = mortar_rows_all
        if args.mortar_active_count > 0 and len(mortar_rows) > args.mortar_active_count:
            mortar_rows = sorted(mortar_rows, key=lambda row: abs(row.residual), reverse=True)[
                : args.mortar_active_count
            ]
        candidate_indexes = {variable.index for variable in candidate_variables}
        for row in mortar_rows:
            row_norm = mortar_row_jacobian_norm(row)
            for var_index, jac_value in row.jacobian:
                if var_index in candidate_indexes:
                    variable_scores[var_index] += mortar_leverage_score(
                        row,
                        jac_value,
                        args.mortar_weight,
                        args.mortar_score_normalization,
                        row_norm=row_norm,
                    )

    pde_injected_priority = {
        int(record["var_index"]): len(injected_pde_candidates) - index
        for index, record in enumerate(injected_pde_candidates)
    }
    ranked = sorted(
        candidate_variables,
        key=lambda variable: (
            1 if variable.index in pde_injected_priority else 0,
            pde_injected_priority.get(variable.index, 0),
            variable_scores.get(variable.index, 0.0),
        ),
        reverse=True,
    )
    selected = [variable for variable in ranked if variable_scores.get(variable.index, 0.0) > 0.0]
    selected = select_active_variables(selected, args.max_variables, args.chart_balanced_selection)
    selected_index = {variable.index: column for column, variable in enumerate(selected)}
    if not selected:
        raise ValueError("no active variables selected for Stage-0 system")

    residual_vector: list[float] = []
    jacobian_rows: list[list[float]] = []
    row_labels: list[str] = []
    row_records: list[dict[str, Any]] = []
    row_groups: dict[str, int] = {"pde": 0, "mortar": 0, "active_guard": 0}
    parallel_fallbacks: list[dict[str, Any]] = []
    native_c_pde = dict(native_c_pde_prescore)
    if native_c_pde_injection.get("enabled"):
        native_c_pde["enabled"] = True
        native_c_pde["cases"] += int(native_c_pde_injection.get("cases", 0))
        native_c_pde["seconds"] += float(native_c_pde_injection.get("seconds", 0.0))

    pde_point_rows = build_stage0_point_rows(
        data,
        projection,
        selected,
        pde_points,
        args.residual_kind,
        args.pde_weight,
        "pde",
        "pde",
        args.stage0_workers,
        use_native_c=args.native_c,
    )
    for point_row in pde_point_rows:
        if point_row.get("skipped"):
            if point_row.get("fallback_reason"):
                parallel_fallbacks.append(point_row)
            continue
        point_native = point_row.get("native_c_pde", {})
        if point_native.get("enabled"):
            native_c_pde["enabled"] = True
            native_c_pde["cases"] += int(point_native.get("cases", 0))
            native_c_pde["seconds"] += float(point_native.get("seconds", 0.0))
        q = float(point_row["q"])
        b = float(point_row["b"])
        selected_components = pde_component_selection.get(qb_key(q, b), set())
        for component in ("e_psi", "e_gamma"):
            if component not in selected_components:
                continue
            residual_raw = float(point_row["residuals"][component])
            residual_vector.append(args.pde_weight * residual_raw)
            jacobian_rows.append(list(point_row["jacobian_rows"][component]))
            row_labels.append("pde")
            row_records.append(
                {
                    "row_id": f"pde:{len(row_records)}",
                    "label": "pde",
                    "row_type": "pde",
                    "q": q,
                    "b": b,
                    "component": component,
                    "residual_raw": residual_raw,
                    "weight": args.pde_weight,
                    "residual_weighted_before_scaling": args.pde_weight * residual_raw,
                }
            )
            row_groups["pde"] += 1

    objective_mortar_rows: list[Any] = []
    for row in mortar_rows:
        active_entries = [(selected_index[var_index], value) for var_index, value in row.jacobian if var_index in selected_index]
        if not active_entries:
            continue
        objective_mortar_rows.append(row)
        residual_raw = float(row.residual)
        residual_vector.append(args.mortar_weight * residual_raw)
        jac_row = [0.0 for _ in selected]
        for column_index, value in active_entries:
            jac_row[column_index] = args.mortar_weight * value
        jacobian_rows.append(jac_row)
        row_labels.append("mortar")
        row_records.append(
            {
                "row_id": f"mortar:{len(row_records)}",
                "label": "mortar",
                "row_type": "mortar",
                "component": row.component,
                "coordinate": row.coordinate,
                "q": row.q,
                "x": row.x,
                "derivative": row.derivative_label,
                "dq_order": row.dq_order,
                "dx_order": row.dx_order,
                "residual_raw": residual_raw,
                "weight": args.mortar_weight,
                "residual_weighted_before_scaling": args.mortar_weight * residual_raw,
                "jacobian_nnz_active": len(active_entries),
            }
        )
        row_groups["mortar"] += 1

    active_guard_points = guard_qb_points_from_args(args)["combined"] if args.active_guard_weight > 0.0 else []
    objective_active_guard_points: list[tuple[float, float]] = []
    active_guard_rows_added = 0
    if active_guard_points:
        guard_point_rows = build_stage0_point_rows(
            data,
            projection,
            selected,
            active_guard_points,
            args.residual_kind,
            args.active_guard_weight,
            "active_guard",
            "active_guard",
            args.stage0_workers,
            use_native_c=args.native_c,
        )
        for point_row in guard_point_rows:
            if point_row.get("skipped"):
                if point_row.get("fallback_reason"):
                    parallel_fallbacks.append(point_row)
                continue
            point_native = point_row.get("native_c_pde", {})
            if point_native.get("enabled"):
                native_c_pde["enabled"] = True
                native_c_pde["cases"] += int(point_native.get("cases", 0))
                native_c_pde["seconds"] += float(point_native.get("seconds", 0.0))
            q = float(point_row["q"])
            b = float(point_row["b"])
            objective_active_guard_points.append((q, b))
            for component in ("e_psi", "e_gamma"):
                residual_raw = float(point_row["residuals"][component])
                jacobian_rows.append(list(point_row["jacobian_rows"][component]))
                residual_vector.append(args.active_guard_weight * residual_raw)
                row_labels.append("active_guard")
                row_records.append(
                    {
                        "row_id": f"active_guard:{len(row_records)}",
                        "label": "active_guard",
                        "row_type": "active_guard",
                        "q": q,
                        "b": b,
                        "component": component,
                        "residual_raw": residual_raw,
                        "weight": args.active_guard_weight,
                        "residual_weighted_before_scaling": args.active_guard_weight * residual_raw,
                    }
                )
                active_guard_rows_added += 1
                row_groups["active_guard"] += 1
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
        "row_labels": row_labels,
        "row_records": row_records,
        "active_guard_rows": active_guard_rows_added,
        "active_guard_points": [[q, b] for q, b in objective_active_guard_points],
        "stage0_workers": args.stage0_workers,
        "parallel_fallbacks": parallel_fallbacks,
        "native_c_rz": native_c_rz_stats(),
        "native_c_pde": native_c_pde,
        "objective_pde_rows": pde_rows,
        "manual_pde_points": [[q, b] for q, b in manual_pde_points],
        "pde_points": [[q, b] for q, b in pde_points],
        "pde_component_mode": args.pde_component_mode,
        "pde_component_selection": [
            {"q": key[0], "b": key[1], "components": sorted(components)}
            for key, components in sorted(pde_component_selection.items())
        ],
        "pde_scan_active": {
            **pde_scan_active_report,
            "points": [[q, b] for q, b in pde_scan_active_report.get("points", [])],
        },
        "objective_mortar_rows": objective_mortar_rows,
        "objective_active_guard_points": objective_active_guard_points,
        "selected_by_chart": selected_by_chart,
        "selected_by_block": selected_by_block,
        "mortar_coordinates": args.mortar_coordinates,
        "mortar_rows_available": mortar_rows_available,
        "mortar_rows_active": len(mortar_rows),
        "mortar_rows_unfiltered_max_abs": mortar_rows_unfiltered_max_abs,
        "mortar_rows_unfiltered_worst": mortar_rows_unfiltered_worst,
        "mortar_audit_rows": mortar_audit_rows,
        "mortar_audit_rows_count": len(mortar_audit_rows),
        "pre_score_candidate_count": pre_score_candidate_count,
        "post_pool_candidate_count": len(candidate_variables),
        "injected_mortar_candidates": injected_mortar_candidates,
        "injected_pde_candidates": injected_pde_candidates,
        "native_c_pde_injection": native_c_pde_injection,
        "variable_score_preview": [
            {"variable": variable.label, "score": variable_scores.get(variable.index, 0.0)}
            for variable in selected[:12]
        ],
    }


def evaluate_stage0_objective_only(data: dict[str, Any], args: argparse.Namespace, system: dict[str, Any]) -> dict[str, Any]:
    from validators.compactified_equations import compactified_residual_defined
    from validators.compactified_equations_twochart import projection_from_twochart
    from validators.twochart_mortar_jacobian import residual_for_row

    projection = projection_from_twochart(data)
    values: list[float] = []
    native_stats: dict[str, Any] = {"enabled": bool(args.native_c), "used": 0, "cases": 0, "seconds": 0.0}
    for row in system["objective_pde_rows"]:
        q = float(row["q"])
        b = float(row["b"])
        if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
            continue
        residual, point_native = residual_with_optional_native_tail_exact(
            data,
            projection,
            q,
            b,
            args.residual_kind,
            bool(args.native_c),
        )
        _merge_native_stat(native_stats, point_native)
        component = str(row["component"])
        value = residual.e_psi if component == "e_psi" else residual.e_gamma
        values.append(args.pde_weight * value)
    for row in system["objective_mortar_rows"]:
        values.append(args.mortar_weight * residual_for_row(data, row))
    if args.active_guard_weight > 0.0:
        for q, b in system["objective_active_guard_points"]:
            if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
                continue
            residual, point_native = residual_with_optional_native_tail_exact(
                data,
                projection,
                q,
                b,
                args.residual_kind,
                bool(args.native_c),
            )
            _merge_native_stat(native_stats, point_native)
            values.append(args.active_guard_weight * residual.e_psi)
            values.append(args.active_guard_weight * residual.e_gamma)
    return {**vector_metrics(values), "native_c_tail_exact": native_stats}


def mortar_audit_metrics(data: dict[str, Any], rows: list[Any], use_native_c: bool = False) -> dict[str, Any]:
    if not rows:
        return {"enabled": False, **vector_metrics([])}
    from validators.twochart_mortar_jacobian import residuals_for_rows

    values, native_stats = residuals_for_rows(data, rows, use_native_c=use_native_c)
    worst_index, worst_value = max(enumerate(values), key=lambda item: abs(item[1]))
    worst_row = rows[worst_index]
    return {
        "enabled": True,
        "native_c_rz_mortar": native_stats,
        "worst": {
            "row_index": int(worst_index),
            "component": worst_row.component,
            "coordinate": worst_row.coordinate,
            "q": worst_row.q,
            "x": worst_row.x,
            "derivative": worst_row.derivative_label,
            "value": worst_value,
            "abs": abs(worst_value),
        },
        **vector_metrics(values),
    }


def residual_audit_point_records(
    data: dict[str, Any],
    args: argparse.Namespace,
    scan_raw: str,
    h: float,
) -> dict[str, Any]:
    from validators.compactified_equations import compactified_residual_defined, qb_to_rz
    from validators.compactified_equations_twochart import (
        SCAN_PRESETS,
        native_tail_exact_residuals_with_kind,
        projection_from_twochart,
    )

    projection = projection_from_twochart(data)
    scan_names = parse_scan_names(scan_raw)
    audit_points: list[dict[str, Any]] = []
    skipped_by_scan: list[int] = []
    for scan_index, name in enumerate(scan_names):
        spec = SCAN_PRESETS[name]
        skipped = 0
        for q in grid_values(float(spec["q_min"]), float(spec["q_max"]), int(spec["n_q"])):
            for b in grid_values(float(spec["b_min"]), float(spec["b_max"]), int(spec["n_b"])):
                r, z = qb_to_rz(q, b)
                if r <= 2.0 * h or r == 0.0:
                    skipped += 1
                    continue
                if not compactified_residual_defined(q, b, projection.p, args.residual_kind):
                    skipped += 1
                    continue
                audit_points.append(
                    {"scan_index": scan_index, "scan": name, "q": q, "b": b, "r": r, "z": z}
                )
        skipped_by_scan.append(skipped)

    native_residuals: dict[int, Any] = {}
    native_stats: dict[str, Any] = {
        "enabled": bool(args.native_c),
        "used": False,
        "points": 0,
        "cases": 0,
        "seconds": 0.0,
    }
    if args.native_c and audit_points:
        native_residuals, native_stats = native_tail_exact_residuals_with_kind(
            data,
            projection,
            [(float(point["q"]), float(point["b"])) for point in audit_points],
            args.residual_kind,
        )

    records: list[dict[str, Any]] = []
    values: list[float] = []
    scan_values_by_index: list[list[float]] = [[] for _name in scan_names]
    scan_points_by_index = [0 for _name in scan_names]
    scan_worst_by_index: list[dict[str, Any]] = [{} for _name in scan_names]
    worst: dict[str, Any] = {}
    for point_index, point in enumerate(audit_points):
        q = float(point["q"])
        b = float(point["b"])
        if point_index in native_residuals:
            residual = native_residuals[point_index]
        else:
            residual, point_native = residual_with_optional_native_tail_exact(
                data,
                projection,
                q,
                b,
                args.residual_kind,
                False,
            )
            _merge_native_stat(native_stats, point_native)
        scan_index = int(point["scan_index"])
        local_values = [float(residual.e_psi), float(residual.e_gamma)]
        local_max = max(abs(value) for value in local_values)
        record = {
            "scan": scan_names[scan_index],
            "q": q,
            "b": b,
            "r": float(point["r"]),
            "z": float(point["z"]),
            "e_psi": float(residual.e_psi),
            "e_gamma": float(residual.e_gamma),
            "max_abs": local_max,
        }
        records.append(record)
        scan_points_by_index[scan_index] += 1
        scan_values_by_index[scan_index].extend(local_values)
        values.extend(local_values)
        if local_max > float(scan_worst_by_index[scan_index].get("max_abs", -1.0)):
            scan_worst_by_index[scan_index] = dict(record)
        if local_max > float(worst.get("max_abs", -1.0)):
            worst = dict(record)

    scan_reports: list[dict[str, Any]] = []
    for scan_index, name in enumerate(scan_names):
        spec = SCAN_PRESETS[name]
        scan_reports.append(
            {
                "label": spec["label"],
                "chart": spec["chart"],
                "q_range": [spec["q_min"], spec["q_max"]],
                "b_range": [spec["b_min"], spec["b_max"]],
                "grid": {
                    "n_q": spec["n_q"],
                    "n_b": spec["n_b"],
                    "points": scan_points_by_index[scan_index],
                    "skipped": skipped_by_scan[scan_index],
                },
                "metrics": vector_metrics(scan_values_by_index[scan_index]),
                "worst": scan_worst_by_index[scan_index],
            }
        )
    return {
        "scan": ",".join(scan_names),
        "h": h,
        "native_c_tail_exact": native_stats,
        "scans": scan_reports,
        "records": records,
        "worst": worst,
        "metrics": vector_metrics(values),
    }


def residual_scan_active_qb_points(data: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    count = int(getattr(args, "pde_scan_active_count", 0))
    if count <= 0:
        return {"enabled": False, "points": [], "selected": []}
    scan_raw = str(getattr(args, "pde_scan_active_scan", "")).strip()
    if not scan_raw:
        scan_raw = args.line_search_residual_audit_scan.strip() or args.scan
    h = float(getattr(args, "pde_scan_active_h", args.line_search_residual_audit_h))
    audit = residual_audit_point_records(data, args, scan_raw, h)
    selected: list[dict[str, Any]] = []
    points: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for record in sorted(audit["records"], key=lambda item: float(item["max_abs"]), reverse=True):
        key = qb_key(float(record["q"]), float(record["b"]))
        if key in seen:
            continue
        seen.add(key)
        selected.append(record)
        points.append((float(record["q"]), float(record["b"])))
        if len(points) >= count:
            break
    return {
        "enabled": True,
        "requested_count": count,
        "scan": audit["scan"],
        "h": h,
        "points": points,
        "selected": selected,
        "source_worst": audit["worst"],
        "source_metrics": audit["metrics"],
        "native_c_tail_exact": audit["native_c_tail_exact"],
    }


def residual_audit_metrics(data: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.max_residual_audit_growth <= 0.0:
        return {"enabled": False, **vector_metrics([])}
    scan_raw = args.line_search_residual_audit_scan.strip() or args.scan
    h = float(args.line_search_residual_audit_h)
    audit = residual_audit_point_records(data, args, scan_raw, h)
    return {
        "enabled": True,
        "scan": audit["scan"],
        "h": h,
        "native_c_tail_exact": audit["native_c_tail_exact"],
        "scans": audit["scans"],
        "worst": audit["worst"],
        **audit["metrics"],
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


def parse_label_set(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def restricted_guarded_kkt_step(
    jacobian_rows: list[list[float]],
    residual_vector: list[float],
    row_labels: list[str],
    active_columns: list[int],
    total_columns: int,
    lm_lambda: float,
    primary_labels: set[str],
    constraint_labels: set[str],
    constraint_damping: float,
    max_constraints: int,
) -> tuple[list[float], dict[str, Any]]:
    if not active_columns:
        raise ValueError("empty active column set")
    primary_indexes = [index for index, label in enumerate(row_labels) if label in primary_labels]
    constraint_indexes = [index for index, label in enumerate(row_labels) if label in constraint_labels]
    if not primary_indexes:
        primary_indexes = [index for index, label in enumerate(row_labels) if label not in constraint_labels]
    if not primary_indexes:
        raise ValueError("guarded KKT has no primary rows")
    if max_constraints > 0 and len(constraint_indexes) > max_constraints:
        constraint_indexes = sorted(constraint_indexes, key=lambda index: abs(residual_vector[index]), reverse=True)[
            :max_constraints
        ]
    restricted_primary = [[jacobian_rows[index][column] for column in active_columns] for index in primary_indexes]
    primary_residuals = [residual_vector[index] for index in primary_indexes]
    if not constraint_indexes:
        delta, report = normal_step(restricted_primary, primary_residuals, lm_lambda)
        full_delta = [0.0 for _ in range(total_columns)]
        for local_index, column in enumerate(active_columns):
            full_delta[column] = delta[local_index]
        return full_delta, {
            **report,
            "method": "guarded-kkt-fallback-unconstrained",
            "active_columns": len(active_columns),
            "total_columns": total_columns,
            "primary_rows": len(primary_indexes),
            "constraint_rows": 0,
        }

    restricted_constraints = [
        [jacobian_rows[index][column] for column in active_columns] for index in constraint_indexes
    ]
    n = len(active_columns)
    m = len(restricted_constraints)
    column_norms = []
    all_rows = restricted_primary + restricted_constraints
    for column in range(n):
        norm = math.sqrt(sum(row[column] * row[column] for row in all_rows))
        column_norms.append(norm)
    scales = [1.0 / norm if norm > 1e-14 else 1.0 for norm in column_norms]
    primary_rows = [[value * scales[index] for index, value in enumerate(row)] for row in restricted_primary]
    constraint_rows = [[value * scales[index] for index, value in enumerate(row)] for row in restricted_constraints]
    hessian = [[0.0 for _ in range(n)] for _ in range(n)]
    gradient = [0.0 for _ in range(n)]
    for row, residual in zip(primary_rows, primary_residuals):
        for i, ji in enumerate(row):
            gradient[i] += ji * residual
            if ji == 0.0:
                continue
            for j in range(i, n):
                hessian[i][j] += ji * row[j]
    for i in range(n):
        for j in range(i):
            hessian[i][j] = hessian[j][i]
        hessian[i][i] += lm_lambda

    size = n + m
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for i in range(n):
        rhs[i] = -gradient[i]
        for j in range(n):
            matrix[i][j] = hessian[i][j]
    for constraint_index, row in enumerate(constraint_rows):
        kkt_row = n + constraint_index
        rhs[kkt_row] = 0.0
        for column, value in enumerate(row):
            matrix[column][kkt_row] = value
            matrix[kkt_row][column] = value
        matrix[kkt_row][kkt_row] = -constraint_damping
    solution = solve_linear(matrix, rhs)
    scaled_delta = solution[:n]
    delta = [value * scales[index] for index, value in enumerate(scaled_delta)]
    full_delta = [0.0 for _ in range(total_columns)]
    for local_index, column in enumerate(active_columns):
        full_delta[column] = delta[local_index]
    primary_change = [
        sum(jacobian_rows[index][column] * full_delta[column] for column in active_columns)
        for index in primary_indexes
    ]
    constraint_change = [
        sum(jacobian_rows[index][column] * full_delta[column] for column in active_columns)
        for index in constraint_indexes
    ]
    nonzero_norms = [value for value in column_norms if value > 0.0]
    return full_delta, {
        "method": "guarded-kkt-damped",
        "active_columns": len(active_columns),
        "total_columns": total_columns,
        "primary_rows": len(primary_indexes),
        "constraint_rows": len(constraint_indexes),
        "constraint_rows_available": len([index for index, label in enumerate(row_labels) if label in constraint_labels]),
        "constraint_damping": constraint_damping,
        "primary_labels": sorted(primary_labels),
        "constraint_labels": sorted(constraint_labels),
        "column_norm_min": min(nonzero_norms) if nonzero_norms else 0.0,
        "column_norm_max": max(column_norms) if column_norms else 0.0,
        "column_scale_min": min(scales) if scales else 0.0,
        "column_scale_max": max(scales) if scales else 0.0,
        "primary_residual_metrics": vector_metrics([residual_vector[index] for index in primary_indexes]),
        "constraint_residual_metrics": vector_metrics([residual_vector[index] for index in constraint_indexes]),
        "delta_metrics": vector_metrics(delta),
        "predicted_primary_change": vector_metrics(primary_change),
        "predicted_constraint_change": vector_metrics(constraint_change),
    }


def coefficient_penalty(variable: Any, args: argparse.Namespace) -> float:
    if args.coefficient_norm in {"euclidean", "column"}:
        return 1.0
    if variable.chart == "tail":
        kq = max(int(variable.kq or 0), 0)
        kx = max(int(variable.kx or 0), 0)
        log_weight = kq * math.log(args.tail_degree_weight) + kx * math.log(args.tail_angular_weight)
    elif variable.chart == "origin":
        degree = max(int(variable.r_power or 0) + int(variable.z_power or 0), 0)
        log_weight = degree * math.log(args.origin_degree_weight)
    else:
        log_weight = 0.0
    return min(math.exp(min(log_weight, 690.0)), 1e300)


def equilibrate_rows(
    rows: list[list[float]],
    residuals: list[float],
    enabled: bool,
) -> tuple[list[list[float]], list[float], dict[str, Any]]:
    if not enabled:
        return rows, residuals, {"enabled": False, "scale_min": 1.0, "scale_max": 1.0}
    scales: list[float] = []
    out_rows: list[list[float]] = []
    out_residuals: list[float] = []
    for row, residual in zip(rows, residuals):
        finite_row = [value if math.isfinite(value) else 0.0 for value in row]
        finite_residual = residual if math.isfinite(residual) else 0.0
        row_norm = math.hypot(*finite_row) if finite_row else 0.0
        denom = max(row_norm, abs(finite_residual), 1e-300)
        scale = 1.0 / denom if math.isfinite(denom) else 0.0
        scales.append(scale)
        out_rows.append([scale * value if math.isfinite(value) else 0.0 for value in row])
        out_residuals.append(scale * residual if math.isfinite(residual) else 0.0)
    return out_rows, out_residuals, {
        "enabled": True,
        "scale_min": min(scales) if scales else 0.0,
        "scale_max": max(scales) if scales else 0.0,
    }


def scale_columns(
    primary_rows: list[list[float]],
    constraint_rows: list[list[float]],
    active_variables: list[Any],
    args: argparse.Namespace,
) -> tuple[list[list[float]], list[list[float]], list[float], dict[str, Any]]:
    coefficient_scales = [1.0 / coefficient_penalty(variable, args) for variable in active_variables]
    pre_column_rows = [
        [value * coefficient_scales[index] for index, value in enumerate(row)]
        for row in primary_rows
    ]
    pre_column_constraints = [
        [value * coefficient_scales[index] for index, value in enumerate(row)]
        for row in constraint_rows
    ]
    column_equilibration_scales = [1.0 for _variable in active_variables]
    if args.active_set_column_equilibration or args.coefficient_norm == "column":
        all_rows = pre_column_rows + pre_column_constraints
        for column in range(len(active_variables)):
            values = [row[column] for row in all_rows if math.isfinite(row[column])]
            norm = math.hypot(*values) if values else 0.0
            column_equilibration_scales[column] = 1.0 / norm if math.isfinite(norm) and norm > 1e-14 else 1.0
    total_scales = [
        coefficient_scales[index] * column_equilibration_scales[index]
        for index in range(len(active_variables))
    ]
    scaled_primary = [
        [value * column_equilibration_scales[index] for index, value in enumerate(row)]
        for row in pre_column_rows
    ]
    scaled_constraints = [
        [value * column_equilibration_scales[index] for index, value in enumerate(row)]
        for row in pre_column_constraints
    ]
    coefficient_penalties = [1.0 / max(scale, 1e-300) for scale in coefficient_scales]
    return scaled_primary, scaled_constraints, total_scales, {
        "coefficient_norm": args.coefficient_norm,
        "coefficient_penalty_min": min(coefficient_penalties) if coefficient_penalties else 0.0,
        "coefficient_penalty_max": max(coefficient_penalties) if coefficient_penalties else 0.0,
        "coefficient_scale_min": min(coefficient_scales) if coefficient_scales else 0.0,
        "coefficient_scale_max": max(coefficient_scales) if coefficient_scales else 0.0,
        "column_equilibration_enabled": bool(args.active_set_column_equilibration or args.coefficient_norm == "column"),
        "column_equilibration_scale_min": min(column_equilibration_scales) if column_equilibration_scales else 0.0,
        "column_equilibration_scale_max": max(column_equilibration_scales) if column_equilibration_scales else 0.0,
        "total_scale_min": min(total_scales) if total_scales else 0.0,
        "total_scale_max": max(total_scales) if total_scales else 0.0,
    }


def restricted_guarded_ineq_kkt_step(
    jacobian_rows: list[list[float]],
    residual_vector: list[float],
    row_labels: list[str],
    variables: list[Any],
    args: argparse.Namespace,
    active_columns: list[int],
    total_columns: int,
    lm_lambda: float,
    primary_labels: set[str],
    constraint_labels: set[str],
    max_constraints: int,
    tolerance: float,
    max_active: int,
    target: str,
) -> tuple[list[float], dict[str, Any]]:
    if not active_columns:
        raise ValueError("empty active column set")
    primary_indexes = [index for index, label in enumerate(row_labels) if label in primary_labels]
    constraint_indexes = [index for index, label in enumerate(row_labels) if label in constraint_labels]
    if not primary_indexes:
        primary_indexes = [index for index, label in enumerate(row_labels) if label not in constraint_labels]
    if not primary_indexes:
        raise ValueError("guarded inequality KKT has no primary rows")
    if max_constraints > 0 and len(constraint_indexes) > max_constraints:
        constraint_indexes = sorted(constraint_indexes, key=lambda index: abs(residual_vector[index]), reverse=True)[
            :max_constraints
        ]

    n = len(active_columns)
    active_variables = [variables[column] for column in active_columns]
    restricted_primary = [[jacobian_rows[index][column] for column in active_columns] for index in primary_indexes]
    primary_residuals = [residual_vector[index] for index in primary_indexes]
    restricted_constraints = [
        [jacobian_rows[index][column] for column in active_columns] for index in constraint_indexes
    ]
    constraint_residuals = [residual_vector[index] for index in constraint_indexes]

    primary_rows, primary_residuals_scaled, primary_row_report = equilibrate_rows(
        restricted_primary,
        primary_residuals,
        args.active_set_row_equilibration,
    )
    constraint_rows, constraint_residuals_scaled, constraint_row_report = equilibrate_rows(
        restricted_constraints,
        constraint_residuals,
        args.active_set_row_equilibration,
    )
    primary_rows, constraint_rows, scales, column_report = scale_columns(
        primary_rows,
        constraint_rows,
        active_variables,
        args,
    )

    from validators.guarded_kkt_active_set import solve_guarded_active_set

    active_set_report = solve_guarded_active_set(
        primary_rows,
        primary_residuals_scaled,
        constraint_rows,
        constraint_residuals_scaled,
        lm_lambda=lm_lambda,
        max_active=max_active,
        tolerance=tolerance,
        target=target,
        svd_rcond=args.svd_rcond,
        max_step_norm=args.max_scaled_step_norm,
    )
    scaled_delta_raw = active_set_report.get("step", [])
    if len(scaled_delta_raw) != n:
        raise ValueError(
            "guarded inequality KKT did not return a full step"
            + (
                f": {active_set_report.get('failure_reason')}"
                if active_set_report.get("failure_reason")
                else ""
            )
        )
    scaled_delta = [float(value) for value in scaled_delta_raw]
    delta = [value * scales[index] for index, value in enumerate(scaled_delta)]
    full_delta = [0.0 for _ in range(total_columns)]
    for local_index, column in enumerate(active_columns):
        full_delta[column] = delta[local_index]

    primary_change = [
        sum(jacobian_rows[index][column] * full_delta[column] for column in active_columns)
        for index in primary_indexes
    ]
    constraint_change = [
        sum(jacobian_rows[index][column] * full_delta[column] for column in active_columns)
        for index in constraint_indexes
    ]
    signed_constraint_change = [
        (1.0 if residual_vector[index] >= 0.0 else -1.0) * change
        for index, change in zip(constraint_indexes, constraint_change)
    ]
    return full_delta, {
        "method": "guarded-ineq-kkt-active-set",
        "active_columns": len(active_columns),
        "total_columns": total_columns,
        "primary_rows": len(primary_indexes),
        "constraint_rows": len(constraint_indexes),
        "constraint_rows_available": len([index for index, label in enumerate(row_labels) if label in constraint_labels]),
        "primary_labels": sorted(primary_labels),
        "constraint_labels": sorted(constraint_labels),
        "target": target,
        "tolerance": tolerance,
        "max_active": max_active,
        "pass": bool(active_set_report.get("pass")),
        "failure_reason": active_set_report.get("failure_reason"),
        "backend": active_set_report.get("backend"),
        "active_constraint_count": len(active_set_report.get("active_constraints", [])),
        "active_set_report": active_set_report,
        "row_equilibration": {
            "primary": primary_row_report,
            "constraint": constraint_row_report,
        },
        "column_scaling": column_report,
        "column_scale_min": min(scales) if scales else 0.0,
        "column_scale_max": max(scales) if scales else 0.0,
        "primary_residual_metrics": vector_metrics(primary_residuals),
        "constraint_residual_metrics": vector_metrics(constraint_residuals),
        "delta_metrics": vector_metrics(delta),
        "predicted_primary_change": vector_metrics(primary_change),
        "predicted_constraint_change": vector_metrics(constraint_change),
        "signed_constraint_change": vector_metrics(signed_constraint_change),
    }


def guarded_kkt_rank_report(args: argparse.Namespace, system: dict[str, Any], iteration: int) -> dict[str, Any]:
    primary_labels = parse_label_set(args.guarded_kkt_primary_labels)
    active_primary_raw_max = 0.0
    for record in system["row_records"]:
        if str(record.get("label")) in primary_labels:
            active_primary_raw_max = max(active_primary_raw_max, abs(float(record.get("residual_raw", 0.0))))
    try:
        from validators.guarded_kkt_rank import compute_guarded_kkt_rank_report

        report = compute_guarded_kkt_rank_report(
            system["residual_vector"],
            system["jacobian_rows"],
            system["row_labels"],
            [variable.label for variable in system["variables"]],
            primary_labels,
            parse_label_set(args.guarded_kkt_constraint_labels),
            heldout_global_mortar_max=system.get("mortar_rows_unfiltered_max_abs", 0.0),
            active_primary_raw_max=active_primary_raw_max,
            coverage_min=args.rank_coverage_min,
        )
    except Exception as exc:
        report = {
            "status": "GUARDED_KKT_RANK_DIAGNOSTIC_UNAVAILABLE_NOT_PROOF",
            "diagnostic_vs_proof": "rank report failed before interval validation; no proof claim",
            "error": f"{type(exc).__name__}: {exc}",
            "coverage": {
                "active_primary_raw_max": active_primary_raw_max,
                "heldout_global_mortar_max": system.get("mortar_rows_unfiltered_max_abs", 0.0),
                "coverage": active_primary_raw_max / max(system.get("mortar_rows_unfiltered_max_abs", 0.0), 1e-300),
                "coverage_min": args.rank_coverage_min,
                "coverage_ok": False,
            },
        }
    report["iteration"] = iteration
    report["mortar_rows_unfiltered_worst"] = system.get("mortar_rows_unfiltered_worst", {})
    report["mortar_rows_active"] = system.get("mortar_rows_active", 0)
    report["mortar_rows_available"] = system.get("mortar_rows_available", 0)
    return report


def write_stage0_row_cache(args: argparse.Namespace, system: dict[str, Any], iteration: int) -> None:
    if not args.row_cache_out:
        return
    from validators.twochart_row_cache import build_stage0_row_cache, write_json

    cache = build_stage0_row_cache(
        profile_path=args.input,
        variables=system["variables"],
        row_records=system["row_records"],
        residual_vector=system["residual_vector"],
        jacobian_rows=system["jacobian_rows"],
        row_labels=system["row_labels"],
        row_scaling=system["row_scaling"],
        extra={
            "iteration": iteration,
            "solve_mode": args.solve_mode,
            "primary_labels": sorted(parse_label_set(args.guarded_kkt_primary_labels)),
            "constraint_labels": sorted(parse_label_set(args.guarded_kkt_constraint_labels)),
            "mortar_rows_unfiltered_max_abs": system.get("mortar_rows_unfiltered_max_abs", 0.0),
            "mortar_rows_unfiltered_worst": system.get("mortar_rows_unfiltered_worst", {}),
            "pde_points": system.get("pde_points", []),
            "pde_component_mode": system.get("pde_component_mode"),
            "pde_component_selection": system.get("pde_component_selection", []),
            "pde_scan_active": system.get("pde_scan_active", {}),
        },
    )
    write_json(args.row_cache_out, cache)


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


def line_search_accept_metric_value(
    metric: str,
    sampled_metrics: dict[str, Any],
    residual_audit_metrics: dict[str, Any],
    mortar_audit_metrics: dict[str, Any],
    base_residual_audit_metrics: dict[str, Any] | None = None,
    base_mortar_audit_metrics: dict[str, Any] | None = None,
) -> float:
    if metric == "objective":
        return float(sampled_metrics["objective"])
    if metric == "max-abs":
        return float(sampled_metrics["max_abs"])
    if metric == "residual-audit-max":
        if not residual_audit_metrics.get("enabled"):
            raise ValueError("--line-search-accept-metric residual-audit-max requires --max-residual-audit-growth > 0")
        return float(residual_audit_metrics["max_abs"])
    if metric == "mortar-audit-max":
        if not mortar_audit_metrics.get("enabled"):
            raise ValueError("--line-search-accept-metric mortar-audit-max requires --max-mortar-audit-growth > 0")
        return float(mortar_audit_metrics["max_abs"])
    if metric == "coupled-audit-max":
        report = coupled_audit_metric_report(
            residual_audit_metrics,
            mortar_audit_metrics,
            base_residual_audit_metrics or residual_audit_metrics,
            base_mortar_audit_metrics or mortar_audit_metrics,
        )
        if not report.get("enabled"):
            raise ValueError(
                "--line-search-accept-metric coupled-audit-max requires "
                "--max-residual-audit-growth > 0 and --max-mortar-audit-growth > 0"
            )
        return float(report["value"])
    raise ValueError(f"unknown line-search accept metric {metric!r}")


def coupled_audit_metric_report(
    residual_audit_metrics: dict[str, Any],
    mortar_audit_metrics: dict[str, Any],
    base_residual_audit_metrics: dict[str, Any],
    base_mortar_audit_metrics: dict[str, Any],
) -> dict[str, Any]:
    if not residual_audit_metrics.get("enabled") or not mortar_audit_metrics.get("enabled"):
        return {"enabled": False}
    base_residual = max(float(base_residual_audit_metrics["max_abs"]), 1e-300)
    base_mortar = max(float(base_mortar_audit_metrics["max_abs"]), 1e-300)
    residual_max_abs = float(residual_audit_metrics["max_abs"])
    mortar_max_abs = float(mortar_audit_metrics["max_abs"])
    residual_ratio = residual_max_abs / base_residual
    mortar_ratio = mortar_max_abs / base_mortar
    value = max(residual_ratio, mortar_ratio)
    return {
        "enabled": True,
        "mode": "normalized-minimax",
        "value": value,
        "limiting_audit": "residual" if residual_ratio >= mortar_ratio else "mortar",
        "residual_ratio": residual_ratio,
        "mortar_ratio": mortar_ratio,
        "residual_max_abs": residual_max_abs,
        "mortar_max_abs": mortar_max_abs,
        "base_residual_max_abs": base_residual,
        "base_mortar_max_abs": base_mortar,
    }


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
    rank_reports: list[dict[str, Any]] = []
    best_trial: dict[str, Any] | None = None
    best_trial_metrics: dict[str, Any] | None = None
    guard_point_report = guard_qb_points_from_args(args)
    guard_points = guard_point_report["combined"]
    for iteration in range(args.max_iter):
        system = build_stage0_system(current, args, blocks)
        if iteration == 0:
            write_stage0_row_cache(args, system, iteration)
        rank_report: dict[str, Any] | None = None
        if args.rank_report_out:
            rank_report = guarded_kkt_rank_report(args, system, iteration)
            rank_reports.append(rank_report)
        base_vec = system["residual_vector"]
        base_metrics = vector_metrics(base_vec)
        base_raw_metrics = system["raw_residual_metrics"]
        base_guard_metrics = guard_point_metrics(current, args, guard_points)
        base_mortar_audit_metrics = mortar_audit_metrics(
            current,
            system.get("mortar_audit_rows", []),
            use_native_c=bool(args.native_c),
        )
        base_residual_audit_metrics = residual_audit_metrics(current, args)
        base_coupled_audit_metric = coupled_audit_metric_report(
            base_residual_audit_metrics,
            base_mortar_audit_metrics,
            base_residual_audit_metrics,
            base_mortar_audit_metrics,
        )
        base_accept_metric_value = line_search_accept_metric_value(
            args.line_search_accept_metric,
            base_metrics,
            base_residual_audit_metrics,
            base_mortar_audit_metrics,
            base_residual_audit_metrics,
            base_mortar_audit_metrics,
        )
        block_specs = stage0_block_specs(system["variables"], args.solve_mode, args.block_search_labels)
        line_trials: list[dict[str, Any]] = []
        candidate_previews: list[dict[str, Any]] = []
        best_accepted: dict[str, Any] | None = None
        native_c_prediction = {"enabled": bool(args.native_c), "calls": 0, "cases": 0, "seconds": 0.0}
        accepted = False
        for block_spec in block_specs:
            try:
                if args.solve_mode == "guarded-kkt":
                    delta, scaling_report = restricted_guarded_kkt_step(
                        system["jacobian_rows"],
                        base_vec,
                        system["row_labels"],
                        list(block_spec["columns"]),
                        len(system["variables"]),
                        args.lm_lambda,
                        parse_label_set(args.guarded_kkt_primary_labels),
                        parse_label_set(args.guarded_kkt_constraint_labels),
                        args.guarded_kkt_constraint_damping,
                        args.guarded_kkt_max_constraints,
                    )
                elif args.solve_mode == "guarded-ineq-kkt":
                    delta, scaling_report = restricted_guarded_ineq_kkt_step(
                        system["jacobian_rows"],
                        base_vec,
                        system["row_labels"],
                        system["variables"],
                        args,
                        list(block_spec["columns"]),
                        len(system["variables"]),
                        args.lm_lambda,
                        parse_label_set(args.guarded_kkt_primary_labels),
                        parse_label_set(args.guarded_kkt_constraint_labels),
                        args.guarded_kkt_max_constraints,
                        args.guarded_ineq_tolerance,
                        args.guarded_ineq_max_active,
                        args.guarded_ineq_target,
                    )
                else:
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
                    "solver_report": scaling_report,
                    "column_scaling": scaling_report.get("column_scaling", scaling_report)
                    if isinstance(scaling_report, dict)
                    else scaling_report,
                }
            )
            native_predictions: dict[float, dict[str, float]] = {}
            if args.native_c:
                native_predictions, native_prediction_stats = native_stage0_prediction_scan(
                    system,
                    delta,
                    args.line_search,
                    args.trust,
                )
                native_c_prediction["calls"] += int(native_prediction_stats.get("calls", 0))
                native_c_prediction["cases"] += int(native_prediction_stats.get("cases", 0))
                native_c_prediction["seconds"] += float(native_prediction_stats.get("seconds", 0.0))
            for alpha in args.line_search:
                trial_data, update_metrics = apply_delta(current, system["variables"], delta, alpha, args.trust)
                tail_gate = attach_stage0_tail_gate(trial_data, args)
                trial_record: dict[str, Any] = {
                    "block": block_spec["label"],
                    "active_columns": len(block_spec["columns"]),
                    "alpha": alpha,
                    "delta_norm": delta_norm,
                    "solver_report": scaling_report,
                    "column_scaling": scaling_report.get("column_scaling", scaling_report)
                    if isinstance(scaling_report, dict)
                    else scaling_report,
                    "native_linear_prediction": native_predictions.get(float(alpha)),
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
                if args.line_search_eval == "objective-only":
                    trial_metrics = evaluate_stage0_objective_only(trial_data, args, system)
                    trial_raw_metrics = trial_metrics
                else:
                    trial_system = build_stage0_system(trial_data, args, blocks)
                    trial_metrics = vector_metrics(trial_system["residual_vector"])
                    trial_raw_metrics = trial_system["raw_residual_metrics"]
                trial_guard_metrics = guard_point_metrics(trial_data, args, guard_points)
                trial_mortar_audit_metrics = mortar_audit_metrics(
                    trial_data,
                    system.get("mortar_audit_rows", []),
                    use_native_c=bool(args.native_c),
                )
                trial_residual_audit_metrics = residual_audit_metrics(trial_data, args)
                trial_coupled_audit_metric = coupled_audit_metric_report(
                    trial_residual_audit_metrics,
                    trial_mortar_audit_metrics,
                    base_residual_audit_metrics,
                    base_mortar_audit_metrics,
                )
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
                mortar_audit_growth_ok = True
                if base_mortar_audit_metrics.get("enabled"):
                    mortar_audit_growth_ok = (
                        trial_mortar_audit_metrics["max_abs"]
                        <= args.max_mortar_audit_growth * max(base_mortar_audit_metrics["max_abs"], 1e-300)
                    )
                residual_audit_growth_ok = True
                if base_residual_audit_metrics.get("enabled"):
                    residual_audit_growth_ok = (
                        trial_residual_audit_metrics["max_abs"]
                        <= args.max_residual_audit_growth * max(base_residual_audit_metrics["max_abs"], 1e-300)
                    )
                trial_accept_metric_value = line_search_accept_metric_value(
                    args.line_search_accept_metric,
                    trial_metrics,
                    trial_residual_audit_metrics,
                    trial_mortar_audit_metrics,
                    base_residual_audit_metrics,
                    base_mortar_audit_metrics,
                )
                objective_decrease = base_metrics["objective"] - trial_metrics["objective"]
                accept_metric_decrease = base_accept_metric_value - trial_accept_metric_value
                required_decrease = max(
                    args.min_objective_decrease_abs,
                    args.min_objective_decrease_rel * max(abs(base_accept_metric_value), 1e-300),
                    args.min_accept_metric_decrease_abs,
                    args.min_accept_metric_decrease_rel * max(abs(base_accept_metric_value), 1e-300),
                )
                improved = accept_metric_decrease > required_decrease
                accepted_here = (
                    improved
                    and raw_growth_ok
                    and guard_growth_ok
                    and mortar_audit_growth_ok
                    and residual_audit_growth_ok
                )
                line_trials.append(
                    {
                        **trial_record,
                        **trial_metrics,
                        "objective_decrease": objective_decrease,
                        "accept_metric": args.line_search_accept_metric,
                        "base_accept_metric_value": base_accept_metric_value,
                        "trial_accept_metric_value": trial_accept_metric_value,
                        "accept_metric_decrease": accept_metric_decrease,
                        "required_objective_decrease": required_decrease,
                        "required_accept_metric_decrease": required_decrease,
                        "raw_objective": trial_raw_metrics["objective"],
                        "raw_max_abs": trial_raw_metrics["max_abs"],
                        "raw_growth_ok": raw_growth_ok,
                        "guard_metrics": trial_guard_metrics,
                        "guard_growth_ok": guard_growth_ok,
                        "mortar_audit_metrics": trial_mortar_audit_metrics,
                        "mortar_audit_growth_ok": mortar_audit_growth_ok,
                        "residual_audit_metrics": trial_residual_audit_metrics,
                        "residual_audit_growth_ok": residual_audit_growth_ok,
                        "coupled_audit_metric": trial_coupled_audit_metric,
                        "accepted": accepted_here,
                        "tail_gate": tail_gate,
                    }
                )
                if accepted_here and (
                    best_accepted is None
                    or trial_accept_metric_value < best_accepted["accept_metric_value"]
                ):
                    best_accepted = {
                        "block": block_spec["label"],
                        "trial_data": trial_data,
                        "trial_metrics": trial_metrics,
                        "accept_metric_value": trial_accept_metric_value,
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
                "base_accept_metric": {
                    "metric": args.line_search_accept_metric,
                    "value": base_accept_metric_value,
                },
                "solve_mode": args.solve_mode,
                "accepted_block": best_accepted["block"] if best_accepted is not None else "",
                "accepted_alpha": best_accepted["alpha"] if best_accepted is not None else 0.0,
                "block_candidate_previews": candidate_previews,
                "selected_variables": len(system["variables"]),
                "row_groups": system["row_groups"],
                "raw_residual_metrics": system["raw_residual_metrics"],
                "row_scaling": system["row_scaling"],
                "base_guard_metrics": base_guard_metrics,
                "base_mortar_audit_metrics": base_mortar_audit_metrics,
                "base_residual_audit_metrics": base_residual_audit_metrics,
                "base_coupled_audit_metric": base_coupled_audit_metric,
                "selected_by_chart": system["selected_by_chart"],
                "selected_by_block": system["selected_by_block"],
                "mortar_rows_available": system["mortar_rows_available"],
                "mortar_rows_active": system["mortar_rows_active"],
                "mortar_rows_unfiltered_max_abs": system["mortar_rows_unfiltered_max_abs"],
                "mortar_rows_unfiltered_worst": system["mortar_rows_unfiltered_worst"],
                "mortar_audit_rows_count": system.get("mortar_audit_rows_count", 0),
                "rank_report_summary": {
                    "coverage": rank_report.get("coverage", {}) if rank_report else {},
                    "constraint_space": rank_report.get("constraint_space", {}) if rank_report else {},
                    "angle": rank_report.get("angle", {}) if rank_report else {},
                }
                if rank_report
                else {},
                "active_guard_weight": args.active_guard_weight,
                "pde_points": system.get("pde_points", []),
                "pde_component_mode": system.get("pde_component_mode"),
                "pde_component_selection": system.get("pde_component_selection", []),
                "pde_scan_active": system.get("pde_scan_active", {}),
                "active_guard_rows": system["active_guard_rows"],
                "active_guard_points": system["active_guard_points"],
                "stage0_workers": system.get("stage0_workers", 1),
                "parallel_fallbacks": system.get("parallel_fallbacks", []),
                "native_c_rz": system.get("native_c_rz", {}),
                "native_c_pde": system.get("native_c_pde", {}),
                "native_c_prediction": native_c_prediction,
                "pre_score_candidate_count": system["pre_score_candidate_count"],
                "post_pool_candidate_count": system["post_pool_candidate_count"],
                "injected_mortar_candidates": system["injected_mortar_candidates"][:12],
                "injected_pde_candidates": system.get("injected_pde_candidates", [])[:12],
                "native_c_pde_injection": system.get("native_c_pde_injection", {}),
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
            "native_c": args.native_c,
            "mortar_q_samples": args.mortar_q_samples,
            "mortar_x_samples": args.mortar_x_samples,
            "mortar_q_values": parse_coordinate_values(args.mortar_q_values, "--mortar-q-values", 0.0, 1.0),
            "mortar_x_values": parse_coordinate_values(args.mortar_x_values, "--mortar-x-values", 0.0, 1.0),
            "mortar_active_count": args.mortar_active_count,
            "overlap_q_range": [args.overlap_q_min, args.overlap_q_max],
            "pde_qb_points": [
                [q, b]
                for q, b in (
                    []
                    if args.no_default_pde_points and not args.pde_qb_points.strip()
                    else parse_qb_points(args.pde_qb_points)
                )
            ],
            "no_default_pde_points": args.no_default_pde_points,
            "pde_component_mode": args.pde_component_mode,
            "pde_scan_active_count": args.pde_scan_active_count,
            "pde_scan_active_scan": args.pde_scan_active_scan,
            "pde_scan_active_h": args.pde_scan_active_h,
            "guard_qb_points": [[q, b] for q, b in guard_points],
            "guard_qb_points_explicit": [[q, b] for q, b in guard_point_report["explicit"]],
            "guard_qb_points_generated": [[q, b] for q, b in guard_point_report["generated"]],
            "guard_qb_points_seam": [[q, b] for q, b in guard_point_report["seam"]],
            "guard_grid": args.guard_grid,
            "guard_grid_q_range": [args.guard_q_min, args.guard_q_max],
            "guard_grid_b_range": [args.guard_b_min, args.guard_b_max],
            "guard_grid_samples": [args.guard_q_samples, args.guard_b_samples],
            "guard_seam_sides": args.guard_seam_sides,
            "guard_seam_q": args.guard_seam_q,
            "guard_seam_eps": args.guard_seam_eps,
            "guard_seam_b_points": parse_float_list(args.guard_seam_b_points)
            if args.guard_seam_b_points.strip()
            else [],
            "solve_mode": args.solve_mode,
            "block_search_labels": args.block_search_labels,
            "max_guard_objective_growth": args.max_guard_objective_growth,
            "max_guard_max_growth": args.max_guard_max_growth,
            "active_guard_weight": args.active_guard_weight,
            "min_objective_decrease_abs": args.min_objective_decrease_abs,
            "min_objective_decrease_rel": args.min_objective_decrease_rel,
            "min_accept_metric_decrease_abs": args.min_accept_metric_decrease_abs,
            "min_accept_metric_decrease_rel": args.min_accept_metric_decrease_rel,
            "guarded_kkt_primary_labels": args.guarded_kkt_primary_labels,
            "guarded_kkt_constraint_labels": args.guarded_kkt_constraint_labels,
            "guarded_kkt_constraint_damping": args.guarded_kkt_constraint_damping,
            "guarded_kkt_max_constraints": args.guarded_kkt_max_constraints,
            "guarded_ineq_tolerance": args.guarded_ineq_tolerance,
            "guarded_ineq_max_active": args.guarded_ineq_max_active,
            "guarded_ineq_target": args.guarded_ineq_target,
            "coefficient_norm": args.coefficient_norm,
            "tail_degree_weight": args.tail_degree_weight,
            "tail_angular_weight": args.tail_angular_weight,
            "origin_degree_weight": args.origin_degree_weight,
            "max_scaled_step_norm": args.max_scaled_step_norm,
            "svd_rcond": args.svd_rcond,
            "active_set_row_equilibration": args.active_set_row_equilibration,
            "active_set_column_equilibration": args.active_set_column_equilibration,
            "prediction_actual_report_out": args.prediction_actual_report_out,
            "stage0_workers": args.stage0_workers,
            "rank_report_out": args.rank_report_out,
            "rank_coverage_min": args.rank_coverage_min,
            "row_cache_out": args.row_cache_out,
            "max_iter": args.max_iter,
            "trust": args.trust,
            "lm_lambda": args.lm_lambda,
            "max_variables": args.max_variables,
            "candidate_kq_max": args.candidate_kq_max,
            "candidate_kx_max": args.candidate_kx_max,
            "candidate_origin_degree_max": args.candidate_origin_degree_max,
            "candidate_pool_limit": args.candidate_pool_limit,
            "mortar_jacobian_candidate_count": args.mortar_jacobian_candidate_count,
            "pde_jacobian_candidate_count": args.pde_jacobian_candidate_count,
            "mortar_score_normalization": args.mortar_score_normalization,
            "pde_weight": args.pde_weight,
            "mortar_weight": args.mortar_weight,
            "line_search": args.line_search,
            "line_search_eval": args.line_search_eval,
            "line_search_accept_metric": args.line_search_accept_metric,
            "include_origin_constants": args.include_origin_constants,
            "chart_balanced_selection": args.chart_balanced_selection,
            "row_normalization": args.row_normalization,
            "row_normalization_floor": args.row_normalization_floor,
            "row_scale_min": args.row_scale_min,
            "row_scale_max": args.row_scale_max,
            "max_raw_objective_growth": args.max_raw_objective_growth,
            "max_mortar_audit_growth": args.max_mortar_audit_growth,
            "line_search_mortar_audit_order": args.line_search_mortar_audit_order,
            "line_search_mortar_audit_q_samples": args.line_search_mortar_audit_q_samples,
            "line_search_mortar_audit_x_samples": args.line_search_mortar_audit_x_samples,
            "line_search_mortar_audit_q_values": parse_coordinate_values(
                args.line_search_mortar_audit_q_values,
                "--line-search-mortar-audit-q-values",
                0.0,
                1.0,
            ),
            "line_search_mortar_audit_x_values": parse_coordinate_values(
                args.line_search_mortar_audit_x_values,
                "--line-search-mortar-audit-x-values",
                0.0,
                1.0,
            ),
            "line_search_mortar_audit_active_count": args.line_search_mortar_audit_active_count,
            "max_residual_audit_growth": args.max_residual_audit_growth,
            "line_search_residual_audit_scan": args.line_search_residual_audit_scan,
            "line_search_residual_audit_h": args.line_search_residual_audit_h,
            "tail_gate_samples_per_patch": args.tail_gate_samples_per_patch,
            "forced_tol": args.forced_tol,
            "q2_tol": args.q2_tol,
        },
        "history": history,
        "rank_reports": rank_reports,
        "row_cache_out": args.row_cache_out,
        "candidate": final_data,
        "diagnostic_vs_proof": "floating sampled analytic Gauss-Newton run only; no interval proof",
    }


def prediction_actual_report(args: argparse.Namespace, run_report: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for history in run_report.get("history", []):
        base = history.get("base", {})
        for trial in history.get("line_trials", []):
            solver_report = trial.get("solver_report", {})
            if not isinstance(solver_report, dict):
                solver_report = trial.get("column_scaling", {})
            scaling = solver_report if isinstance(solver_report, dict) else {}
            predicted = scaling.get("active_set_report", {}).get("predicted_primary_metrics", {})
            predicted_delta = predicted.get("delta", {}) if isinstance(predicted, dict) else {}
            predicted_improvement = -float(predicted_delta.get("objective", 0.0) or 0.0)
            actual_improvement = float(trial.get("objective_decrease", 0.0) or 0.0)
            ratio = actual_improvement / predicted_improvement if predicted_improvement > 0.0 else None
            native_prediction = trial.get("native_linear_prediction")
            if not isinstance(native_prediction, dict):
                native_prediction = {}
            coupled_metric = trial.get("coupled_audit_metric")
            if not isinstance(coupled_metric, dict):
                coupled_metric = {}
            native_objective = native_prediction.get("objective")
            native_improvement = (
                float(base.get("objective", 0.0) or 0.0) - float(native_objective)
                if native_objective is not None
                else None
            )
            entries.append(
                {
                    "iteration": history.get("iteration"),
                    "block": trial.get("block"),
                    "alpha": trial.get("alpha"),
                    "alpha_applied": trial.get("alpha_applied"),
                    "accepted": trial.get("accepted", False),
                    "predicted_primary_objective_improvement": predicted_improvement,
                    "actual_sampled_objective_improvement": actual_improvement,
                    "actual_over_predicted": ratio,
                    "native_linear_objective": native_objective,
                    "native_linear_objective_improvement": native_improvement,
                    "native_linear_max_abs": native_prediction.get("max_abs"),
                    "raw_max_abs": trial.get("raw_max_abs"),
                    "guard_max_abs": trial.get("guard_metrics", {}).get("max_abs")
                    if isinstance(trial.get("guard_metrics"), dict)
                    else None,
                    "guard_growth_ok": trial.get("guard_growth_ok"),
                    "raw_growth_ok": trial.get("raw_growth_ok"),
                    "mortar_audit_max_abs": trial.get("mortar_audit_metrics", {}).get("max_abs")
                    if isinstance(trial.get("mortar_audit_metrics"), dict)
                    else None,
                    "mortar_audit_growth_ok": trial.get("mortar_audit_growth_ok"),
                    "residual_audit_max_abs": trial.get("residual_audit_metrics", {}).get("max_abs")
                    if isinstance(trial.get("residual_audit_metrics"), dict)
                    else None,
                    "residual_audit_growth_ok": trial.get("residual_audit_growth_ok"),
                    "accept_metric": trial.get("accept_metric"),
                    "base_accept_metric_value": trial.get("base_accept_metric_value"),
                    "trial_accept_metric_value": trial.get("trial_accept_metric_value"),
                    "accept_metric_decrease": trial.get("accept_metric_decrease"),
                    "required_accept_metric_decrease": trial.get("required_accept_metric_decrease"),
                    "coupled_audit_value": coupled_metric.get("value"),
                    "coupled_audit_limiter": coupled_metric.get("limiting_audit"),
                    "coupled_residual_ratio": coupled_metric.get("residual_ratio"),
                    "coupled_mortar_ratio": coupled_metric.get("mortar_ratio"),
                    "max_abs_update": trial.get("max_abs_update"),
                    "delta_norm": trial.get("delta_norm"),
                    "base_objective": base.get("objective"),
                    "trial_objective": trial.get("objective"),
                    "solver_method": scaling.get("method"),
                    "scaled_step_clip": scaling.get("active_set_report", {}).get("step_clip_scale")
                    if isinstance(scaling.get("active_set_report"), dict)
                    else None,
                }
            )
    accepted_entries = [entry for entry in entries if entry.get("accepted")]
    ratios = [
        float(entry["actual_over_predicted"])
        for entry in entries
        if entry.get("actual_over_predicted") is not None
    ]
    return {
        "format": "twochart_prediction_actual_report_v1",
        "status": run_report.get("status", ""),
        "diagnostic_vs_proof": "floating prediction-vs-actual line-search diagnostics only; no interval proof",
        "input": args.input,
        "out": args.out,
        "solve_mode": args.solve_mode,
        "coefficient_norm": args.coefficient_norm,
        "active_set_row_equilibration": args.active_set_row_equilibration,
        "active_set_column_equilibration": args.active_set_column_equilibration,
        "max_scaled_step_norm": args.max_scaled_step_norm,
        "svd_rcond": args.svd_rcond,
        "entry_count": len(entries),
        "accepted_entry_count": len(accepted_entries),
        "actual_over_predicted_min": min(ratios) if ratios else None,
        "actual_over_predicted_max": max(ratios) if ratios else None,
        "entries": entries,
    }


def build_plan(args: argparse.Namespace, data: dict[str, Any], hooks: HookReport) -> dict[str, Any]:
    blocks = parse_blocks(args.blocks)
    tail_legality = validate_hard_gates(data, args.q2_policy)
    guard_point_report = guard_qb_points_from_args(args)
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
            "mortar_q_values": parse_coordinate_values(args.mortar_q_values, "--mortar-q-values", 0.0, 1.0),
            "mortar_x_values": parse_coordinate_values(args.mortar_x_values, "--mortar-x-values", 0.0, 1.0),
            "chart_balanced_selection": args.chart_balanced_selection,
            "guard_qb_points": [[q, b] for q, b in guard_point_report["combined"]],
            "guard_qb_points_explicit": [[q, b] for q, b in guard_point_report["explicit"]],
            "guard_qb_points_generated": [[q, b] for q, b in guard_point_report["generated"]],
            "guard_qb_points_seam": [[q, b] for q, b in guard_point_report["seam"]],
            "guard_grid": args.guard_grid,
            "guard_grid_q_range": [args.guard_q_min, args.guard_q_max],
            "guard_grid_b_range": [args.guard_b_min, args.guard_b_max],
            "guard_grid_samples": [args.guard_q_samples, args.guard_b_samples],
            "guard_seam_sides": args.guard_seam_sides,
            "guard_seam_q": args.guard_seam_q,
            "guard_seam_eps": args.guard_seam_eps,
            "guard_seam_b_points": parse_float_list(args.guard_seam_b_points)
            if args.guard_seam_b_points.strip()
            else [],
            "active_guard_weight": args.active_guard_weight,
            "guarded_kkt_primary_labels": args.guarded_kkt_primary_labels,
            "guarded_kkt_constraint_labels": args.guarded_kkt_constraint_labels,
            "guarded_kkt_constraint_damping": args.guarded_kkt_constraint_damping,
            "guarded_kkt_max_constraints": args.guarded_kkt_max_constraints,
            "rank_report_out": args.rank_report_out,
            "rank_coverage_min": args.rank_coverage_min,
            "row_cache_out": args.row_cache_out,
            "row_normalization": args.row_normalization,
            "line_search_eval": args.line_search_eval,
            "min_objective_decrease_abs": args.min_objective_decrease_abs,
            "min_objective_decrease_rel": args.min_objective_decrease_rel,
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
    parser.add_argument("--rank-report-out", default="", help="Optional guarded-KKT rank/angle diagnostic JSON.")
    parser.add_argument("--row-cache-out", default="", help="Optional sampled row cache JSON for the first Stage-0 system.")
    parser.add_argument("--dry-run", action="store_true", help="Write the old solver plan without mutating coefficients.")
    parser.add_argument("--blocks", default="origin,interface", help="Comma list: tail,origin,interface.")
    parser.add_argument("--variable-charts", default="tail,origin", help="Comma list of mutable charts: tail,origin.")
    parser.add_argument("--gamma-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--B-fixed", action="store_true", default=True, help="Accepted planned flag; enforced true.")
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--q2-policy", choices=("zero",), default="zero")
    parser.add_argument("--mortar-order", type=positive_int, default=4)
    parser.add_argument("--mortar-coordinates", choices=("RZ", "qx", "both"), default="RZ")
    parser.add_argument(
        "--native-c",
        action="store_true",
        help="Use native C for R/Z tail coefficient Jacobian jets when mortar-coordinates includes RZ.",
    )
    parser.add_argument("--mortar-active-count", type=int, default=0)
    parser.add_argument("--mortar-q-samples", type=positive_int, default=3)
    parser.add_argument("--mortar-x-samples", type=positive_int, default=5)
    parser.add_argument(
        "--mortar-q-values",
        default="",
        help="Comma-separated explicit q values for objective mortar rows; overrides --mortar-q-samples when set.",
    )
    parser.add_argument(
        "--mortar-x-values",
        default="",
        help="Comma-separated explicit x values for objective mortar rows; overrides --mortar-x-samples when set.",
    )
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--pde-qb-points", default="")
    parser.add_argument(
        "--no-default-pde-points",
        action="store_true",
        help="When --pde-qb-points is empty, use no legacy default PDE points; intended for scan-selected rows.",
    )
    parser.add_argument(
        "--pde-component-mode",
        choices=("both", "worst-per-point", "worst-global"),
        default="both",
        help="Which PDE components become Stage-0 objective rows at selected q,b points.",
    )
    parser.add_argument(
        "--pde-scan-active-count",
        type=nonnegative_int,
        default=0,
        help="Add this many largest held-out PDE residual scan points to the Stage-0 objective rows.",
    )
    parser.add_argument(
        "--pde-scan-active-scan",
        default="",
        help=(
            "Comma-separated scan presets used to select automatic PDE objective points; "
            "empty reuses --line-search-residual-audit-scan, then --scan."
        ),
    )
    parser.add_argument(
        "--pde-scan-active-h",
        type=positive_float,
        default=1e-3,
        help="Axis skip radius h for automatic held-out PDE objective point selection.",
    )
    parser.add_argument("--guard-qb-points", default="", help="Semicolon-separated q,b points used only as line-search guards.")
    parser.add_argument(
        "--guard-grid",
        choices=("none", "edge", "box"),
        default="none",
        help=(
            "Generate an additional q,b guard grid. 'edge' and 'box' both use the "
            "explicit guard-q/b ranges; names are kept separate for report clarity."
        ),
    )
    parser.add_argument("--guard-q-min", type=float, default=0.84)
    parser.add_argument("--guard-q-max", type=float, default=0.92)
    parser.add_argument("--guard-b-min", type=float, default=0.10)
    parser.add_argument("--guard-b-max", type=float, default=0.98)
    parser.add_argument("--guard-q-samples", type=positive_int, default=5)
    parser.add_argument("--guard-b-samples", type=positive_int, default=7)
    parser.add_argument(
        "--guard-seam-sides",
        choices=("none", "below", "above", "both"),
        default="none",
        help=(
            "Generate extra guard points at q=guard-seam-q +/- guard-seam-eps "
            "using the guard b grid, or --guard-seam-b-points when provided."
        ),
    )
    parser.add_argument("--guard-seam-q", type=float, default=0.90)
    parser.add_argument("--guard-seam-eps", type=positive_float, default=1e-12)
    parser.add_argument(
        "--guard-seam-b-points",
        default="",
        help="Optional comma-separated b values for seam-limit guards; defaults to the guard b grid.",
    )
    parser.add_argument("--max-guard-objective-growth", type=positive_float, default=1.0)
    parser.add_argument("--max-guard-max-growth", type=positive_float, default=1.0)
    parser.add_argument(
        "--min-objective-decrease-abs",
        type=nonnegative_float,
        default=0.0,
        help="Require at least this absolute sampled-objective decrease for line-search acceptance.",
    )
    parser.add_argument(
        "--min-objective-decrease-rel",
        type=nonnegative_float,
        default=0.0,
        help="Require at least this relative sampled-objective decrease for line-search acceptance.",
    )
    parser.add_argument(
        "--min-accept-metric-decrease-abs",
        type=nonnegative_float,
        default=0.0,
        help=(
            "Require at least this absolute decrease in --line-search-accept-metric. "
            "Use this to prevent promotion of roundoff-scale residual-audit or mortar-audit changes."
        ),
    )
    parser.add_argument(
        "--min-accept-metric-decrease-rel",
        type=nonnegative_float,
        default=0.0,
        help="Require at least this relative decrease in --line-search-accept-metric.",
    )
    parser.add_argument(
        "--active-guard-weight",
        type=nonnegative_float,
        default=0.0,
        help=(
            "When positive, add the effective guard q,b points as weighted PDE "
            "rows after variable selection. This constrains trial directions "
            "without using the guard grid for expensive candidate scoring."
        ),
    )
    parser.add_argument("--solve-mode", choices=("full", "block-search", "guarded-kkt", "guarded-ineq-kkt"), default="full")
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
    parser.add_argument("--candidate-pool-limit", type=nonnegative_int, default=512, help="Pre-score candidate cap; 0 disables the cap.")
    parser.add_argument(
        "--mortar-jacobian-candidate-count",
        type=nonnegative_int,
        default=0,
        help="Inject this many extra variables by largest active mortar-row Jacobian score, ignoring degree caps.",
    )
    parser.add_argument(
        "--pde-jacobian-candidate-count",
        type=nonnegative_int,
        default=0,
        help=(
            "Inject this many extra variables by largest active PDE-row Jacobian score, "
            "bypassing --candidate-pool-limit while respecting degree caps and tail gates."
        ),
    )
    parser.add_argument(
        "--mortar-score-normalization",
        choices=("raw", "row-norm"),
        default="raw",
        help=(
            "Scoring geometry for mortar-driven variable ranking/injection. "
            "'row-norm' uses per-row Jacobian leverage so high-order tail columns do not bury coupled origin columns."
        ),
    )
    parser.add_argument("--line-search", type=parse_float_list, default=parse_float_list("1,0.5,0.25,0.125"))
    parser.add_argument(
        "--line-search-eval",
        choices=("full", "objective-only"),
        default="full",
        help=(
            "Use 'objective-only' to score line-search trials on the same sampled "
            "row set without rebuilding candidate selection/Jacobians. Requires "
            "--row-normalization none."
        ),
    )
    parser.add_argument(
        "--line-search-accept-metric",
        choices=("objective", "max-abs", "residual-audit-max", "mortar-audit-max", "coupled-audit-max"),
        default="objective",
        help=(
            "Scalar metric that must decrease for line-search acceptance. "
            "'coupled-audit-max' uses max(residual_audit/base_residual_audit, "
            "mortar_audit/base_mortar_audit), so both held-out defects must improve."
        ),
    )
    parser.add_argument(
        "--guarded-kkt-primary-labels",
        default="mortar",
        help="Comma-separated row labels used as the primary objective in --solve-mode guarded-kkt.",
    )
    parser.add_argument(
        "--guarded-kkt-constraint-labels",
        default="active_guard",
        help="Comma-separated row labels treated as first-order constraints in --solve-mode guarded-kkt.",
    )
    parser.add_argument(
        "--guarded-kkt-constraint-damping",
        type=positive_float,
        default=1e-8,
        help="Positive damping on KKT multipliers for rank-deficient guarded constraints.",
    )
    parser.add_argument(
        "--guarded-kkt-max-constraints",
        type=nonnegative_int,
        default=128,
        help="Keep this many largest-residual constraint rows in guarded KKT; 0 keeps all.",
    )
    parser.add_argument(
        "--guarded-ineq-tolerance",
        type=nonnegative_float,
        default=1e-10,
        help="Signed guard-growth tolerance for --solve-mode guarded-ineq-kkt.",
    )
    parser.add_argument(
        "--guarded-ineq-max-active",
        type=nonnegative_int,
        default=64,
        help="Maximum active guard inequalities for --solve-mode guarded-ineq-kkt.",
    )
    parser.add_argument(
        "--guarded-ineq-target",
        choices=("nonincrease",),
        default="nonincrease",
        help="Guard inequality target for --solve-mode guarded-ineq-kkt.",
    )
    parser.add_argument(
        "--coefficient-norm",
        choices=("euclidean", "analytic", "column"),
        default="euclidean",
        help=(
            "Coefficient geometry for --solve-mode guarded-ineq-kkt. "
            "'analytic' applies degree/angular penalties before solving; "
            "'column' uses only column equilibration."
        ),
    )
    parser.add_argument("--tail-degree-weight", type=positive_float, default=1.0)
    parser.add_argument("--tail-angular-weight", type=positive_float, default=1.0)
    parser.add_argument("--origin-degree-weight", type=positive_float, default=1.0)
    parser.add_argument(
        "--max-scaled-step-norm",
        type=nonnegative_float,
        default=0.0,
        help="Clip the active-set step in scaled variables before mapping back to coefficients; 0 disables.",
    )
    parser.add_argument(
        "--svd-rcond",
        type=nonnegative_float,
        default=0.0,
        help="rcond passed to NumPy lstsq inside guarded active-set KKT; 0 uses NumPy default.",
    )
    parser.add_argument("--active-set-row-equilibration", action="store_true")
    parser.add_argument("--active-set-column-equilibration", action="store_true")
    parser.add_argument(
        "--prediction-actual-report-out",
        default="",
        help="Optional JSON report summarizing predicted-vs-actual line-search behavior.",
    )
    parser.add_argument(
        "--stage0-workers",
        type=positive_int,
        default=1,
        help=(
            "CPU worker processes for Stage-0 PDE/active-guard row assembly. "
            "Values above 1 parallelize point rows while preserving the existing formulas."
        ),
    )
    parser.add_argument(
        "--rank-coverage-min",
        type=nonnegative_float,
        default=0.5,
        help="Minimum active-primary/raw-heldout mortar coverage expected before a rank report can be branch evidence.",
    )
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
    parser.add_argument(
        "--max-mortar-audit-growth",
        type=nonnegative_float,
        default=0.0,
        help=(
            "When positive, reject line-search steps whose held-out mortar-audit max grows by more than this factor. "
            "Uses a denser C0-Ck mortar grid and is intended to catch active-row overfit."
        ),
    )
    parser.add_argument(
        "--line-search-mortar-audit-order",
        type=int,
        default=-1,
        help="Mortar derivative order for line-search audit; -1 reuses --mortar-order.",
    )
    parser.add_argument(
        "--line-search-mortar-audit-q-samples",
        type=nonnegative_int,
        default=0,
        help="q sample count for line-search mortar audit; 0 uses max(--mortar-q-samples, 9).",
    )
    parser.add_argument(
        "--line-search-mortar-audit-x-samples",
        type=nonnegative_int,
        default=0,
        help="x sample count for line-search mortar audit; 0 uses max(--mortar-x-samples, 9).",
    )
    parser.add_argument(
        "--line-search-mortar-audit-q-values",
        default="",
        help=(
            "Comma-separated explicit q values for line-search mortar audit rows; "
            "overrides --line-search-mortar-audit-q-samples when set."
        ),
    )
    parser.add_argument(
        "--line-search-mortar-audit-x-values",
        default="",
        help=(
            "Comma-separated explicit x values for line-search mortar audit rows; "
            "overrides --line-search-mortar-audit-x-samples when set."
        ),
    )
    parser.add_argument(
        "--line-search-mortar-audit-active-count",
        type=nonnegative_int,
        default=0,
        help="Keep this many largest-residual held-out mortar audit rows during line search; 0 keeps all.",
    )
    parser.add_argument(
        "--max-residual-audit-growth",
        type=nonnegative_float,
        default=0.0,
        help=(
            "When positive, reject line-search steps whose held-out PDE residual-audit max grows by more "
            "than this factor. Uses scan presets and native C for tail exact residual points when available."
        ),
    )
    parser.add_argument(
        "--line-search-residual-audit-scan",
        default="",
        help="Comma-separated residual scan presets for line-search residual audit; empty reuses --scan.",
    )
    parser.add_argument(
        "--line-search-residual-audit-h",
        type=positive_float,
        default=1e-3,
        help="Axis skip radius h for line-search residual audit scans.",
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
    if args.line_search_mortar_audit_order < -1 or args.line_search_mortar_audit_order > 4:
        parser.error("--line-search-mortar-audit-order must be -1 or between 0 and 4")
    try:
        parse_scan_names(args.scan)
        if args.line_search_residual_audit_scan.strip():
            parse_scan_names(args.line_search_residual_audit_scan)
        if args.pde_scan_active_scan.strip():
            parse_scan_names(args.pde_scan_active_scan)
    except ValueError as exc:
        parser.error(str(exc))
    if not args.line_search or any(alpha <= 0.0 for alpha in args.line_search):
        parser.error("--line-search must contain positive floats")
    try:
        parse_coordinate_values(args.mortar_q_values, "--mortar-q-values", 0.0, 1.0)
        parse_coordinate_values(args.mortar_x_values, "--mortar-x-values", 0.0, 1.0)
        parse_coordinate_values(args.line_search_mortar_audit_q_values, "--line-search-mortar-audit-q-values", 0.0, 1.0)
        parse_coordinate_values(args.line_search_mortar_audit_x_values, "--line-search-mortar-audit-x-values", 0.0, 1.0)
    except ValueError as exc:
        parser.error(str(exc))
    if args.row_scale_min < 0.0:
        parser.error("--row-scale-min must be nonnegative")
    if args.row_scale_min > args.row_scale_max:
        parser.error("--row-scale-min must be <= --row-scale-max")
    if args.line_search_eval == "objective-only" and args.row_normalization != "none":
        parser.error("--line-search-eval objective-only requires --row-normalization none")
    if args.line_search_accept_metric == "residual-audit-max" and args.max_residual_audit_growth <= 0.0:
        parser.error("--line-search-accept-metric residual-audit-max requires --max-residual-audit-growth > 0")
    if args.line_search_accept_metric == "mortar-audit-max" and args.max_mortar_audit_growth <= 0.0:
        parser.error("--line-search-accept-metric mortar-audit-max requires --max-mortar-audit-growth > 0")
    if args.line_search_accept_metric == "coupled-audit-max" and (
        args.max_residual_audit_growth <= 0.0 or args.max_mortar_audit_growth <= 0.0
    ):
        parser.error(
            "--line-search-accept-metric coupled-audit-max requires "
            "--max-residual-audit-growth > 0 and --max-mortar-audit-growth > 0"
        )
    if args.guard_q_max <= args.guard_q_min:
        parser.error("--guard-q-max must be greater than --guard-q-min")
    if args.guard_b_max <= args.guard_b_min:
        parser.error("--guard-b-max must be greater than --guard-b-min")
    if args.guard_seam_sides in ("below", "both") and args.guard_seam_q - args.guard_seam_eps <= 0.0:
        parser.error("--guard-seam-q - --guard-seam-eps must be positive")
    if args.guard_seam_sides in ("above", "both") and args.guard_seam_q + args.guard_seam_eps >= 1.0:
        parser.error("--guard-seam-q + --guard-seam-eps must be less than 1")
    if args.guard_seam_b_points.strip():
        for b_value in parse_float_list(args.guard_seam_b_points):
            if b_value < 0.0 or b_value > 1.0:
                parser.error("--guard-seam-b-points values must lie in [0, 1]")

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
            if args.prediction_actual_report_out:
                save_json(args.prediction_actual_report_out, prediction_actual_report(args, run_report))
            if args.rank_report_out:
                save_json(
                    args.rank_report_out,
                    {
                        "format": "twochart_guarded_kkt_rank_reports_v1",
                        "status": run_report.get("status", ""),
                        "input": args.input,
                        "out": args.out,
                        "reports": run_report.get("rank_reports", []),
                        "diagnostic_vs_proof": "floating rank/angle diagnostics only; no interval proof",
                    },
                )
        else:
            save_json(args.out, result)
            if args.report_out:
                save_json(args.report_out, result)
            if args.prediction_actual_report_out:
                save_json(args.prediction_actual_report_out, prediction_actual_report(args, result))
            if args.rank_report_out:
                save_json(
                    args.rank_report_out,
                    {
                        "format": "twochart_guarded_kkt_rank_reports_v1",
                        "status": result.get("status", ""),
                        "input": args.input,
                        "out": args.out,
                        "reports": result.get("rank_reports", []),
                        "diagnostic_vs_proof": "floating rank/angle diagnostics only; no interval proof",
                    },
                )

    print(f"input={args.input}")
    print(f"saved={args.out}")
    if args.report_out:
        print(f"report_saved={args.report_out}")
    if args.rank_report_out:
        print(f"rank_report_saved={args.rank_report_out}")
    if args.row_cache_out:
        print(f"row_cache_saved={args.row_cache_out}")
    if args.prediction_actual_report_out:
        print(f"prediction_actual_report_saved={args.prediction_actual_report_out}")
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
            native_c_rz = last.get("native_c_rz", {})
            if native_c_rz.get("enabled"):
                print(
                    "native_c_rz="
                    f"cases:{native_c_rz.get('cases', 0)} "
                    f"calls:{native_c_rz.get('calls', 0)} "
                    f"seconds:{float(native_c_rz.get('seconds', 0.0)):.6f}"
                )
            native_c_pde = last.get("native_c_pde", {})
            if native_c_pde.get("enabled"):
                print(
                    "native_c_pde="
                    f"cases:{native_c_pde.get('cases', 0)} "
                    f"seconds:{float(native_c_pde.get('seconds', 0.0)):.6f}"
                )
            native_c_prediction = last.get("native_c_prediction", {})
            if native_c_prediction.get("enabled"):
                print(
                    "native_c_prediction="
                    f"cases:{native_c_prediction.get('cases', 0)} "
                    f"seconds:{float(native_c_prediction.get('seconds', 0.0)):.6f}"
                )
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
