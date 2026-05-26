#!/usr/bin/env python3
"""Probe the native q/x Chebyshev kernel against a Stage-0 row-cache shape.

This does not wire C into Stage-0 and does not change solver semantics.  It
loads an existing Stage-0 row cache, extracts the active tail coefficient/point
shape, and times the current C q/x weighted coefficient partial batch ABI on the
inner partials that a future RZ/PDE C path would need.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from benchmark_native_c_kernel import compile_library, load_library  # noqa: E402
from validators.twochart_mortar_jacobian import (  # noqa: E402
    patch_interval,
    weighted_cheb_coeff_partial,
)


STATUS = "NSPROOF_STAGE0_C_PATH_PROBE_FLOATING_NOT_PROOF"
DEFAULT_ROW_CACHE = ROOT / "work" / "twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_rows.json"
DEFAULT_REPORT = ROOT / "work" / "twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_report.json"

NEXT_C_SIGNATURES = [
    (
        "int nsproof_rz_weighted_coeff_partials_batch("
        "int count, int max_order, const double *q, const double *x, "
        "const double *q0, const double *q1, const double *x0, const double *x1, "
        "const double *alpha, const int *kq, const int *kx, "
        "double *out_rz_partials, int *out_status);"
    ),
    (
        "int nsproof_pde_linearized_columns_batch("
        "int point_count, int variable_count, const double *q, const double *b, "
        "int residual_kind, const struct nsproof_profile_view *profile, "
        "const struct nsproof_variable_desc *variables, "
        "double *out_e_psi, double *out_e_gamma, int *out_status);"
    ),
    (
        "int nsproof_stage0_prediction_scan_batch("
        "int row_count, int column_count, int alpha_count, const double *rows, "
        "const double *residuals, const double *step, const double *alphas, "
        "double *out_l2, double *out_max_abs, int *out_status);"
    ),
]


@dataclass(frozen=True)
class WeightedCase:
    source: str
    patch_key: tuple[float, float, float, float]
    alpha: float
    q: float
    x: float
    kq: int
    kx: int
    dq_order: int
    dx_order: int


@dataclass
class PackedCGroup:
    patch_key: tuple[float, float, float, float]
    alpha: Any
    q: Any
    x: Any
    kq: Any
    kx: Any
    dq_order: Any
    dx_order: Any
    out: Any
    count: int


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def resolve_path(raw: str | Path, base: Path = ROOT) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    direct = Path.cwd() / path
    if direct.exists():
        return direct.resolve()
    return (base / path).resolve()


def derivative_orders(max_total: int) -> list[tuple[int, int]]:
    if max_total < 0 or max_total > 4:
        raise ValueError("partial proxy order must be between 0 and 4")
    return [(dq, total - dq) for total in range(max_total + 1) for dq in range(total + 1)]


def point_in_patch(patch: dict[str, Any], q: float, x: float) -> bool:
    q0, q1, x0, x1 = patch_interval(patch)
    return q0 - 1e-14 <= q <= q1 + 1e-14 and x0 - 1e-14 <= x <= x1 + 1e-14


def tail_patch(profile: dict[str, Any], variable: dict[str, Any]) -> dict[str, Any]:
    blocks = profile["tail_chart"]["blocks"]
    block = str(variable["block"])
    patch_index = int(variable["patch_index"])
    frac_index = variable.get("frac_index")
    if frac_index is None:
        return blocks[block][patch_index]
    return blocks[block][int(frac_index) - 1][patch_index]


def sparse_tail_columns(row: dict[str, Any], variables_by_col: dict[int, dict[str, Any]]) -> set[int]:
    out: set[int] = set()
    for item in row.get("jacobian_sparse_after_scaling", []):
        if not isinstance(item, list) or len(item) != 2:
            continue
        column = int(item[0])
        variable = variables_by_col.get(column)
        if variable is not None and variable.get("chart") == "tail":
            out.add(column)
    return out


def add_weighted_cases(
    *,
    cases: dict[tuple[Any, ...], WeightedCase],
    patch_by_key: dict[tuple[float, float, float, float], dict[str, Any]],
    source: str,
    profile: dict[str, Any],
    variable: dict[str, Any],
    q: float,
    x: float,
    orders: Iterable[tuple[int, int]],
) -> None:
    patch = tail_patch(profile, variable)
    if not point_in_patch(patch, q, x):
        return
    pkey = tuple(float(value) for value in patch_interval(patch))
    patch_by_key[pkey] = patch
    for dq_order, dx_order in orders:
        case = WeightedCase(
            source=source,
            patch_key=pkey,
            alpha=float(variable["alpha"]),
            q=float(q),
            x=float(x),
            kq=int(variable["kq"]),
            kx=int(variable["kx"]),
            dq_order=int(dq_order),
            dx_order=int(dx_order),
        )
        key = (
            case.source,
            case.patch_key,
            case.alpha,
            case.q,
            case.x,
            case.kq,
            case.kx,
            case.dq_order,
            case.dx_order,
        )
        cases.setdefault(key, case)


def build_weighted_partial_cases(
    profile: dict[str, Any],
    row_cache: dict[str, Any],
    pde_proxy_order: int,
    rz_proxy_order: int | None,
    sources: set[str],
) -> tuple[list[WeightedCase], dict[tuple[float, float, float, float], dict[str, Any]], dict[str, Any]]:
    variables_by_col = {
        int(variable["local_column"]): variable
        for variable in row_cache.get("variables", [])
        if isinstance(variable, dict) and "local_column" in variable
    }
    cases: dict[tuple[Any, ...], WeightedCase] = {}
    patch_by_key: dict[tuple[float, float, float, float], dict[str, Any]] = {}

    point_columns: dict[tuple[str, float, float], set[int]] = defaultdict(set)
    rz_mortar_columns: dict[tuple[str, float, float], set[int]] = defaultdict(set)
    rz_mortar_order: dict[tuple[str, float, float], int] = defaultdict(int)
    qx_mortar_rows: list[dict[str, Any]] = []

    row_counts = Counter()
    for row in row_cache.get("rows", []):
        if not isinstance(row, dict):
            continue
        row_type = str(row.get("row_type") or row.get("label") or "")
        row_counts[row_type] += 1
        tail_columns = sparse_tail_columns(row, variables_by_col)
        if not tail_columns:
            continue
        if row_type in {"pde", "active_guard"} and row_type in sources:
            q = float(row["q"])
            b = float(row["b"])
            point_columns[(row_type, q, b)].update(tail_columns)
            continue
        if row_type == "mortar" and "mortar" in sources:
            coordinate = str(row.get("coordinate") or "qx")
            if coordinate == "RZ":
                key = (str(row["component"]), float(row["q"]), float(row["x"]))
                rz_mortar_columns[key].update(tail_columns)
                rz_mortar_order[key] = max(
                    rz_mortar_order[key],
                    int(row.get("total_order", int(row.get("dq_order", 0)) + int(row.get("dx_order", 0)))),
                )
            else:
                qx_mortar_rows.append(row)

    point_orders = derivative_orders(pde_proxy_order)
    for (row_type, q, b), columns in sorted(point_columns.items()):
        x = b * b
        for column in sorted(columns):
            variable = variables_by_col[column]
            add_weighted_cases(
                cases=cases,
                patch_by_key=patch_by_key,
                source=row_type,
                profile=profile,
                variable=variable,
                q=q,
                x=x,
                orders=point_orders,
            )

    for (component, q, x), columns in sorted(rz_mortar_columns.items()):
        order = rz_mortar_order[(component, q, x)] if rz_proxy_order is None else rz_proxy_order
        orders = derivative_orders(order)
        for column in sorted(columns):
            variable = variables_by_col[column]
            if variable.get("component") != component:
                continue
            add_weighted_cases(
                cases=cases,
                patch_by_key=patch_by_key,
                source="mortar_rz_proxy",
                profile=profile,
                variable=variable,
                q=q,
                x=x,
                orders=orders,
            )

    for row in qx_mortar_rows:
        q = float(row["q"])
        x = float(row["x"])
        component = str(row["component"])
        orders = [(int(row.get("dq_order", 0)), int(row.get("dx_order", 0)))]
        for column in sorted(sparse_tail_columns(row, variables_by_col)):
            variable = variables_by_col[column]
            if variable.get("component") != component:
                continue
            add_weighted_cases(
                cases=cases,
                patch_by_key=patch_by_key,
                source="mortar_qx_exact",
                profile=profile,
                variable=variable,
                q=q,
                x=x,
                orders=orders,
            )

    source_counts = Counter(case.source for case in cases.values())
    meta = {
        "row_counts": dict(sorted(row_counts.items())),
        "active_tail_columns": len(
            {
                column
                for row in row_cache.get("rows", [])
                if isinstance(row, dict)
                for column in sparse_tail_columns(row, variables_by_col)
            }
        ),
        "pde_active_guard_point_count": len(point_columns),
        "rz_mortar_point_component_count": len(rz_mortar_columns),
        "qx_mortar_row_count": len(qx_mortar_rows),
        "source_case_counts": dict(sorted(source_counts.items())),
        "patch_group_count": len(patch_by_key),
    }
    return sorted(cases.values(), key=lambda item: (item.source, item.patch_key, item.q, item.x, item.kq, item.kx, item.dq_order, item.dx_order)), patch_by_key, meta


def cap_cases(cases: list[WeightedCase], max_cases: int) -> tuple[list[WeightedCase], bool]:
    if max_cases <= 0 or len(cases) <= max_cases:
        return cases, False
    if max_cases == 1:
        return [cases[0]], True
    step = (len(cases) - 1) / float(max_cases - 1)
    return [cases[round(index * step)] for index in range(max_cases)], True


def py_eval_case(case: WeightedCase, patch_by_key: dict[tuple[float, float, float, float], dict[str, Any]]) -> float:
    return weighted_cheb_coeff_partial(
        patch_by_key[case.patch_key],
        case.alpha,
        case.q,
        case.x,
        case.kq,
        case.kx,
        case.dq_order,
        case.dx_order,
    )


def pack_groups(cases: list[WeightedCase]) -> list[PackedCGroup]:
    grouped: dict[tuple[float, float, float, float], list[WeightedCase]] = defaultdict(list)
    for case in cases:
        grouped[case.patch_key].append(case)

    groups: list[PackedCGroup] = []
    for patch_key, group_cases in sorted(grouped.items()):
        count = len(group_cases)
        groups.append(
            PackedCGroup(
                patch_key=patch_key,
                alpha=(ctypes.c_double * count)(*[case.alpha for case in group_cases]),
                q=(ctypes.c_double * count)(*[case.q for case in group_cases]),
                x=(ctypes.c_double * count)(*[case.x for case in group_cases]),
                kq=(ctypes.c_int * count)(*[case.kq for case in group_cases]),
                kx=(ctypes.c_int * count)(*[case.kx for case in group_cases]),
                dq_order=(ctypes.c_int * count)(*[case.dq_order for case in group_cases]),
                dx_order=(ctypes.c_int * count)(*[case.dx_order for case in group_cases]),
                out=(ctypes.c_double * count)(),
                count=count,
            )
        )
    return groups


def c_run_groups(lib: ctypes.CDLL, groups: list[PackedCGroup]) -> float:
    acc = 0.0
    for group in groups:
        q0, q1, x0, x1 = group.patch_key
        status = lib.nsproof_weighted_cheb_coeff_partial_array(
            group.count,
            q0,
            q1,
            x0,
            x1,
            group.alpha,
            group.q,
            group.x,
            group.kq,
            group.kx,
            group.dq_order,
            group.dx_order,
            group.out,
        )
        if status != 0:
            raise RuntimeError(f"C batch status {status} for patch {group.patch_key}")
        acc += sum(group.out)
    return acc


def validate_c_against_python(
    lib: ctypes.CDLL,
    cases: list[WeightedCase],
    patch_by_key: dict[tuple[float, float, float, float], dict[str, Any]],
    groups: list[PackedCGroup],
) -> dict[str, float]:
    py_values = [py_eval_case(case, patch_by_key) for case in cases]

    c_values: list[float] = []
    case_offset_by_patch: dict[tuple[float, float, float, float], int] = {}
    ordered_group_values: dict[tuple[float, float, float, float], list[float]] = {}
    for group in groups:
        c_run_groups(lib, [group])
        ordered_group_values[group.patch_key] = list(group.out)
        case_offset_by_patch[group.patch_key] = 0
    for case in cases:
        offset = case_offset_by_patch[case.patch_key]
        c_values.append(ordered_group_values[case.patch_key][offset])
        case_offset_by_patch[case.patch_key] = offset + 1

    max_abs = 0.0
    max_rel = 0.0
    for py_value, c_value in zip(py_values, c_values):
        diff = abs(py_value - c_value)
        max_abs = max(max_abs, diff)
        max_rel = max(max_rel, diff / max(1.0, abs(py_value)))
    if max_rel > 1e-9 and max_abs > 1e-9:
        raise AssertionError(f"C/Python validation failed: max_abs={max_abs} max_rel={max_rel}")
    return {
        "max_abs_diff": max_abs,
        "max_relative_diff": max_rel,
        "python_accumulator_once": sum(py_values),
        "c_accumulator_once": sum(c_values),
    }


def benchmark_python(
    cases: list[WeightedCase],
    patch_by_key: dict[tuple[float, float, float, float], dict[str, Any]],
    repeats: int,
) -> tuple[float, float]:
    t0 = time.perf_counter()
    acc = 0.0
    for _ in range(repeats):
        for case in cases:
            acc += py_eval_case(case, patch_by_key)
    return time.perf_counter() - t0, acc


def benchmark_c(lib: ctypes.CDLL, groups: list[PackedCGroup], repeats: int) -> tuple[float, float]:
    t0 = time.perf_counter()
    acc = 0.0
    for _ in range(repeats):
        acc += c_run_groups(lib, groups)
    return time.perf_counter() - t0, acc


def summarize_row_cache(row_cache: dict[str, Any]) -> dict[str, Any]:
    variables = [item for item in row_cache.get("variables", []) if isinstance(item, dict)]
    rows = [item for item in row_cache.get("rows", []) if isinstance(item, dict)]
    return {
        "row_count": int(row_cache.get("row_count", len(rows))),
        "column_count": int(row_cache.get("column_count", len(variables))),
        "variables_by_chart": dict(sorted(Counter(str(var.get("chart")) for var in variables).items())),
        "variables_by_chart_block": dict(
            sorted(Counter(f"{var.get('chart')}.{var.get('block')}" for var in variables).items())
        ),
        "rows_by_label": dict(sorted(Counter(str(row.get("label")) for row in rows).items())),
        "rows_by_coordinate": dict(sorted(Counter(str(row.get("coordinate", "")) for row in rows).items())),
    }


def parse_sources(raw: str) -> set[str]:
    sources = {item.strip() for item in raw.split(",") if item.strip()}
    allowed = {"pde", "active_guard", "mortar"}
    unknown = sources - allowed
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown source(s): {', '.join(sorted(unknown))}")
    if not sources:
        raise argparse.ArgumentTypeError("--sources must include at least one of pde,active_guard,mortar")
    return sources


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    row_cache_path = resolve_path(args.row_cache)
    row_cache = load_json(row_cache_path)
    profile_path = resolve_path(args.profile or row_cache.get("profile", ""))
    profile = load_json(profile_path)
    report_path = resolve_path(args.report) if args.report else None
    report = load_json(report_path) if report_path and report_path.exists() else {}

    cases, patch_by_key, case_meta = build_weighted_partial_cases(
        profile,
        row_cache,
        pde_proxy_order=args.pde_proxy_order,
        rz_proxy_order=args.rz_proxy_order,
        sources=args.sources,
    )
    full_case_count = len(cases)
    cases, capped = cap_cases(cases, args.max_cases)
    if not cases:
        raise RuntimeError("no q/x weighted coefficient partial cases were extracted")
    groups = pack_groups(cases)

    with tempfile.TemporaryDirectory(prefix="nsproof-c-path-probe-") as tmp:
        lib = load_library(compile_library(Path(tmp)))
        validation = validate_c_against_python(lib, cases, patch_by_key, groups)
        py_time, py_acc = benchmark_python(cases, patch_by_key, args.repeats)
        c_time, c_acc = benchmark_c(lib, groups, args.repeats)

    acc_diff = abs(py_acc - c_acc)
    acc_scale = max(1.0, abs(py_acc))
    if acc_diff > 1e-8 * acc_scale:
        raise AssertionError(f"timing accumulator mismatch: python={py_acc} c={c_acc}")

    group_sizes = [group.count for group in groups]
    requested_solver = report.get("requested_solver", {}) if isinstance(report.get("requested_solver"), dict) else {}
    return {
        "status": STATUS,
        "diagnostic_vs_proof": "floating kernel timing only; no Stage-0 solve and no interval proof",
        "profile": os.path.relpath(profile_path, ROOT),
        "row_cache": os.path.relpath(row_cache_path, ROOT),
        "report": os.path.relpath(report_path, ROOT) if report_path else "",
        "row_cache_shape": summarize_row_cache(row_cache),
        "requested_solver_excerpt": {
            key: requested_solver.get(key)
            for key in (
                "max_variables",
                "solve_mode",
                "mortar_coordinates",
                "mortar_order",
                "mortar_active_count",
                "active_guard_weight",
                "stage0_workers",
                "line_search_eval",
            )
            if key in requested_solver
        },
        "case_inventory": {
            **case_meta,
            "full_case_count": full_case_count,
            "benchmarked_case_count": len(cases),
            "case_cap_applied": capped,
            "batch_group_count": len(groups),
            "batch_group_size_min": min(group_sizes),
            "batch_group_size_max": max(group_sizes),
            "batch_group_size_mean": sum(group_sizes) / len(group_sizes),
            "pde_proxy_order": args.pde_proxy_order,
            "rz_proxy_order": args.rz_proxy_order,
            "sources": sorted(args.sources),
        },
        "validation": validation,
        "benchmark": {
            "repeats": args.repeats,
            "python_seconds": py_time,
            "c_batch_seconds": c_time,
            "c_batch_speedup_vs_python": py_time / c_time if c_time > 0.0 else math.inf,
            "python_accumulator": py_acc,
            "c_batch_accumulator": c_acc,
        },
        "interpretation": {
            "current_128_exact_c_accelerable_without_solver_changes": False,
            "currently_c_accelerable": (
                "q/x weighted Chebyshev coefficient partial batches only; this is an inner kernel/proxy for "
                "tail coefficient basis derivatives."
            ),
            "not_currently_c_accelerable": (
                "RZ mortar row assembly, PDE residual/Jacobian rows, active-guard rows, guarded active-set "
                "KKT/SVD, and prediction-vs-actual objective scans."
            ),
            "exact_current_qx_mortar_note": (
                "If Stage-0 is run with qx mortar rows, the existing C batch ABI can replace the tail side "
                "weighted_cheb_coeff_partial calls after grouping by patch interval. The cached 128 run uses RZ rows."
            ),
        },
        "next_c_function_signatures": NEXT_C_SIGNATURES,
    }


def print_summary(result: dict[str, Any]) -> None:
    shape = result["row_cache_shape"]
    inventory = result["case_inventory"]
    bench = result["benchmark"]
    interp = result["interpretation"]
    print(f"status={result['status']}")
    print(f"profile={result['profile']}")
    print(f"row_cache={result['row_cache']}")
    print(f"rows={shape['row_count']} columns={shape['column_count']}")
    print(f"rows_by_label={shape['rows_by_label']}")
    print(f"variables_by_chart={shape['variables_by_chart']}")
    print(f"source_case_counts={inventory['source_case_counts']}")
    print(
        "weighted_partial_cases="
        f"{inventory['benchmarked_case_count']} "
        f"(full={inventory['full_case_count']} capped={inventory['case_cap_applied']})"
    )
    print(
        "batch_groups="
        f"{inventory['batch_group_count']} "
        f"size_min={inventory['batch_group_size_min']} "
        f"size_max={inventory['batch_group_size_max']} "
        f"size_mean={inventory['batch_group_size_mean']:.2f}"
    )
    print(
        "validation="
        f"max_abs={result['validation']['max_abs_diff']:.3e} "
        f"max_rel={result['validation']['max_relative_diff']:.3e}"
    )
    print(f"repeats={bench['repeats']}")
    print(f"python_seconds={bench['python_seconds']:.6f}")
    print(f"c_batch_seconds={bench['c_batch_seconds']:.6f}")
    print(f"c_batch_speedup_vs_python={bench['c_batch_speedup_vs_python']:.2f}x")
    print(f"current_128_exact_c_accelerable_without_solver_changes={interp['current_128_exact_c_accelerable_without_solver_changes']}")
    print(f"currently_c_accelerable={interp['currently_c_accelerable']}")
    print(f"not_currently_c_accelerable={interp['not_currently_c_accelerable']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-cache", default=str(DEFAULT_ROW_CACHE), help="Stage-0 row cache JSON to probe")
    parser.add_argument("--profile", default="", help="Two-chart profile JSON; defaults to row_cache['profile']")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Optional Stage-0 report JSON for metadata")
    parser.add_argument("--out", default="", help="Optional JSON output path for the probe report")
    parser.add_argument("--repeats", type=int, default=5, help="Timing repeats over the extracted case set")
    parser.add_argument("--max-cases", type=int, default=0, help="Deterministic cap on extracted cases; 0 keeps all")
    parser.add_argument(
        "--pde-proxy-order",
        type=int,
        default=3,
        help="q/x partial order used as the PDE/active-guard inner-kernel proxy",
    )
    parser.add_argument(
        "--rz-proxy-order",
        type=int,
        default=None,
        help="q/x partial order used as the RZ mortar inner-kernel proxy; default uses each cached row order",
    )
    parser.add_argument(
        "--sources",
        type=parse_sources,
        default=parse_sources("pde,active_guard,mortar"),
        help="Comma-separated case sources: pde,active_guard,mortar",
    )
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    if args.max_cases < 0:
        parser.error("--max-cases must be nonnegative")

    result = build_result(args)
    if args.out:
        out_path = resolve_path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write("\n")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
