#!/usr/bin/env python3
"""Rank/angle diagnostics for guarded two-chart KKT systems.

This module is floating linear-algebra infrastructure.  It diagnoses whether a
selected guarded Stage-0 tangent system contains a seam-reduction direction; it
does not validate a profile or prove an obstruction.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Iterable

try:
    import numpy as np
except ImportError:  # pragma: no cover - depends on the local Python env.
    np = None  # type: ignore[assignment]


STATUS = "GUARDED_KKT_RANK_DIAGNOSTIC_NOT_PROOF"
FINITE_CAP = 1e100


def require_numpy() -> Any:
    if np is None:
        raise RuntimeError(
            "numpy is required for validators/guarded_kkt_rank.py; "
            "install numpy or run this helper in an environment where numpy is available."
        )
    return np


def _as_float(value: Any) -> float:
    out = float(value)
    if math.isnan(out) or math.isinf(out):
        return out
    return out


def _json_float(value: Any) -> float | str:
    out = _as_float(value)
    if math.isnan(out):
        return "nan"
    if math.isinf(out):
        return "inf" if out > 0 else "-inf"
    return out


def _finite_float(value: Any, cap: float = FINITE_CAP) -> float:
    out = float(value)
    if math.isnan(out):
        return 0.0
    if math.isinf(out):
        return cap if out > 0.0 else -cap
    if out > cap:
        return cap
    if out < -cap:
        return -cap
    return out


def _finite_array(array: Any, cap: float = FINITE_CAP) -> Any:
    require_numpy()
    return np.clip(
        np.nan_to_num(np.asarray(array, dtype=float), nan=0.0, posinf=cap, neginf=-cap),
        -cap,
        cap,
    )


def _metrics(values: Iterable[float]) -> dict[str, Any]:
    raw = [_finite_float(value) for value in values]
    if not raw:
        return {"count": 0, "max_abs": 0.0, "rms": 0.0, "l2": 0.0}
    l2 = math.hypot(*raw)
    return {
        "count": int(len(raw)),
        "max_abs": max(abs(value) for value in raw),
        "rms": float(l2 / math.sqrt(float(len(raw)))),
        "l2": l2,
    }


def label_set(raw: str | set[str] | list[str] | tuple[str, ...]) -> set[str]:
    if isinstance(raw, str):
        return {item.strip() for item in raw.split(",") if item.strip()}
    return {str(item).strip() for item in raw if str(item).strip()}


def _label_matches(label: str, selectors: set[str]) -> bool:
    if label in selectors:
        return True
    for selector in selectors:
        if (
            label.startswith(selector + ":")
            or label.startswith(selector + "/")
            or label.startswith(selector + ".")
            or label.startswith(selector + "|")
        ):
            return True
    return False


def _selected_indexes(row_labels: list[str], labels: set[str]) -> list[int]:
    return [index for index, label in enumerate(row_labels) if _label_matches(label, labels)]


def _norm(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _linf(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def _mat_vec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def _mat_mat(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    if not left or not right:
        return [[] for _ in left]
    right_t = _transpose(right)
    return [[sum(a * b for a, b in zip(row, column)) for column in right_t] for row in left]


def _rank_py(matrix: list[list[float]], tolerance: float = 1e-10) -> int:
    if not matrix or not matrix[0]:
        return 0
    work = [row[:] for row in matrix]
    rows = len(work)
    columns = len(work[0])
    rank = 0
    pivot_row = 0
    for column in range(columns):
        pivot = max(range(pivot_row, rows), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= tolerance:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row][column]
            if abs(factor) <= tolerance:
                continue
            work[row] = [value - factor * pivot_value for value, pivot_value in zip(work[row], work[pivot_row])]
        rank += 1
        pivot_row += 1
        if pivot_row == rows:
            break
    return rank


def _rref_py(matrix: list[list[float]], tolerance: float = 1e-10) -> tuple[list[list[float]], list[int]]:
    if not matrix:
        return [], []
    work = [row[:] for row in matrix]
    rows = len(work)
    columns = len(work[0]) if rows else 0
    pivots: list[int] = []
    pivot_row = 0
    for column in range(columns):
        pivot = max(range(pivot_row, rows), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= tolerance:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row][column]
            if abs(factor) <= tolerance:
                continue
            work[row] = [value - factor * pivot_value for value, pivot_value in zip(work[row], work[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    return work, pivots


def _nullspace_py(matrix: list[list[float]], columns: int, tolerance: float = 1e-10) -> list[list[float]]:
    if not matrix:
        return [[1.0 if row == column else 0.0 for column in range(columns)] for row in range(columns)]
    reduced, pivots = _rref_py(matrix, tolerance)
    pivot_set = set(pivots)
    free_columns = [column for column in range(columns) if column not in pivot_set]
    basis_columns: list[list[float]] = []
    for free_column in free_columns:
        vector = [0.0 for _ in range(columns)]
        vector[free_column] = 1.0
        for row_index, pivot_column in enumerate(pivots):
            vector[pivot_column] = -reduced[row_index][free_column]
        basis_columns.append(vector)
    return _transpose(basis_columns) if basis_columns else [[] for _ in range(columns)]


def _solve_square_py(matrix: list[list[float]], rhs: list[float], tolerance: float = 1e-12) -> list[float]:
    size = len(matrix)
    if size == 0:
        return []
    work = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= tolerance:
            raise ValueError("singular matrix")
        work[column], work[pivot] = work[pivot], work[column]
        pivot_value = work[column][column]
        for row in range(column + 1, size):
            factor = work[row][column] / pivot_value
            if abs(factor) <= tolerance:
                continue
            for item in range(column, size + 1):
                work[row][item] -= factor * work[column][item]
    solution = [0.0 for _ in range(size)]
    for row in range(size - 1, -1, -1):
        residual = work[row][size] - sum(work[row][column] * solution[column] for column in range(row + 1, size))
        solution[row] = residual / work[row][row]
    return solution


def _least_squares_py(matrix: list[list[float]], rhs: list[float], ridge: float = 1e-10) -> list[float]:
    if not matrix or not matrix[0]:
        return []
    mt = _transpose(matrix)
    normal = _mat_mat(mt, matrix)
    for index in range(len(normal)):
        normal[index][index] += ridge
    normal_rhs = _mat_vec(mt, rhs)
    return _solve_square_py(normal, normal_rhs)


def _metrics_py(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "max_abs": 0.0, "rms": 0.0, "l2": 0.0}
    l2 = _norm(values)
    return {"count": len(values), "max_abs": _linf(values), "rms": l2 / math.sqrt(len(values)), "l2": l2}


def _compute_guarded_kkt_rank_report_python(
    residual_vector: list[float],
    jacobian_rows: list[list[float]],
    row_labels: list[str],
    variable_labels: list[str],
    primary_labels: str | set[str] | list[str],
    constraint_labels: str | set[str] | list[str],
    *,
    heldout_global_mortar_max: float | None = None,
    active_primary_raw_max: float | None = None,
    coverage_min: float = 0.5,
    top_n: int = 12,
) -> dict[str, Any]:
    primary_set = label_set(primary_labels)
    constraint_set = label_set(constraint_labels)
    primary_indexes = _selected_indexes(row_labels, primary_set)
    constraint_indexes = _selected_indexes(row_labels, constraint_set)
    if not primary_indexes:
        primary_indexes = [
            index for index, label in enumerate(row_labels) if not _label_matches(label, constraint_set)
        ]
    columns = len(variable_labels)
    jm = [jacobian_rows[index] for index in primary_indexes]
    rm = [float(residual_vector[index]) for index in primary_indexes]
    c = [jacobian_rows[index] for index in constraint_indexes]
    n_basis = _nullspace_py(c, columns)
    jmn = _mat_mat(jm, n_basis) if n_basis and n_basis[0] else [[] for _ in jm]
    target = [-value for value in rm]
    if jmn and jmn[0]:
        z = _least_squares_py(jmn, target)
        projected_change = _mat_vec(jmn, z)
        feasible_step = _mat_vec(n_basis, z)
    else:
        projected_change = [0.0 for _ in rm]
        feasible_step = [0.0 for _ in range(columns)]
    gradient = _mat_vec(_transpose(jm), rm) if jm else [0.0 for _ in range(columns)]
    if n_basis and n_basis[0]:
        ntg = _mat_vec(_transpose(n_basis), gradient)
        projected_gradient = _mat_vec(n_basis, ntg)
    else:
        projected_gradient = [0.0 for _ in range(columns)]
    best_residual = [a + b for a, b in zip(rm, projected_change)]
    heldout = None if heldout_global_mortar_max is None else float(heldout_global_mortar_max)
    active_raw = active_primary_raw_max if active_primary_raw_max is not None else _linf(rm)
    coverage = active_raw / heldout if heldout is not None and heldout > 0.0 else None
    top_items = []
    for index, label in enumerate(variable_labels):
        score = max(abs(gradient[index]), abs(projected_gradient[index]), abs(feasible_step[index]))
        top_items.append(
            {
                "column": index,
                "variable": label,
                "gradient": gradient[index],
                "projected_gradient": projected_gradient[index],
                "step": feasible_step[index],
                "score": score,
            }
        )
    top_items.sort(key=lambda item: float(item["score"]), reverse=True)
    return {
        "status": STATUS,
        "diagnostic_vs_proof": "floating guarded-KKT rank/angle diagnostic only; no interval proof",
        "linear_algebra_backend": "pure_python_rref_normal_equations",
        "rank_obstruction": bool(
            _norm(projected_change) / max(_norm(rm), 1e-300) <= 1e-8
            and _norm(projected_gradient) / max(_norm(gradient), 1e-300) <= 1e-8
            and _linf(best_residual) / max(_linf(rm), 1e-300) >= 0.99
        ),
        "row_space_note": "fallback backend uses rank-revealing elimination and normal equations, not SVD",
        "primary_labels": sorted(primary_set),
        "constraint_labels": sorted(constraint_set),
        "rows": {"total": len(row_labels), "primary": len(primary_indexes), "constraints": len(constraint_indexes)},
        "columns": columns,
        "coverage": {
            "active_primary_raw_max": active_raw,
            "heldout_global_mortar_max": heldout,
            "coverage": coverage,
            "coverage_min": coverage_min,
            "coverage_ok": coverage >= coverage_min if coverage is not None else None,
            "note": "coverage uses unweighted raw residual metadata when provided",
        },
        "constraint_space": {
            "rank": _rank_py(c),
            "nullity": columns - _rank_py(c),
            "singular_values": [],
            "residual_metrics": _metrics_py([residual_vector[index] for index in constraint_indexes]),
        },
        "primary_space": {
            "rank": _rank_py(jm),
            "singular_values": [],
            "rank_projected": _rank_py(jmn),
            "singular_values_projected": [],
            "residual_metrics": _metrics_py(rm),
        },
        "angle": {
            "rho_range": _norm(projected_change) / max(_norm(rm), 1e-300),
            "rho_grad": _norm(projected_gradient) / max(_norm(gradient), 1e-300),
            "predicted_best_factor_inf": _linf(best_residual) / max(_linf(rm), 1e-300),
            "projected_change_metrics": _metrics_py(projected_change),
            "best_feasible_step_metrics": _metrics_py(feasible_step),
        },
        "provided_step": {"present": False, "metrics": _metrics_py([]), "constraint_change_metrics": _metrics_py([])},
        "top_variables": top_items[:top_n],
    }


def _rank_from_svd(singular_values: np.ndarray, tol: float | None = None) -> int:
    if singular_values.size == 0:
        return 0
    if tol is None:
        tol = float(max(singular_values.shape[0], 1) * np.max(singular_values) * np.finfo(float).eps * 100.0)
    return int(np.sum(singular_values > tol))


def _nullspace(matrix: np.ndarray, tol: float | None = None) -> tuple[np.ndarray, np.ndarray, int]:
    if matrix.size == 0:
        columns = matrix.shape[1] if matrix.ndim == 2 else 0
        return np.eye(columns), np.asarray([], dtype=float), 0
    _u, singular_values, vt = np.linalg.svd(matrix, full_matrices=True)
    rank = _rank_from_svd(singular_values, tol)
    return vt[rank:].T.copy(), singular_values, rank


def _top_variables(
    variable_labels: list[str],
    gradient: np.ndarray,
    projected_gradient: np.ndarray,
    step: np.ndarray | None,
    leverage: np.ndarray,
    top_n: int,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, label in enumerate(variable_labels):
        step_value = 0.0 if step is None or index >= step.size else float(step[index])
        leverage_value = 0.0 if index >= leverage.size else float(leverage[index])
        score = max(
            abs(float(gradient[index])),
            abs(float(projected_gradient[index])),
            abs(step_value),
            abs(leverage_value),
        )
        items.append(
            {
                "column": index,
                "variable": label,
                "gradient": float(gradient[index]),
                "projected_gradient": float(projected_gradient[index]),
                "leverage": leverage_value,
                "step": step_value,
                "score": score,
            }
        )
    items.sort(key=lambda item: float(item["score"]), reverse=True)
    return items[:top_n]


def compute_guarded_kkt_rank_report(
    residual_vector: list[float] | np.ndarray,
    jacobian_rows: list[list[float]] | np.ndarray,
    row_labels: list[str],
    variable_labels: list[str],
    primary_labels: str | set[str] | list[str],
    constraint_labels: str | set[str] | list[str],
    *,
    heldout_global_mortar_max: float | None = None,
    active_primary_raw_max: float | None = None,
    coverage_min: float = 0.5,
    step: list[float] | np.ndarray | None = None,
    top_n: int = 12,
) -> dict[str, Any]:
    """Return a JSON-serializable guarded KKT rank/angle report.

    The linear algebra is performed on the rows passed in.  If the caller uses
    row-scaled Stage-0 rows, the report is a post-scaling tangent diagnostic.
    Coverage should be computed from unweighted raw mortar residual metadata.
    """

    if np is None:
        return _compute_guarded_kkt_rank_report_python(
            [float(value) for value in residual_vector],
            [[float(entry) for entry in row] for row in jacobian_rows],
            row_labels,
            variable_labels,
            primary_labels,
            constraint_labels,
            heldout_global_mortar_max=heldout_global_mortar_max,
            active_primary_raw_max=active_primary_raw_max,
            coverage_min=coverage_min,
            top_n=top_n,
        )

    require_numpy()
    r = _finite_array(residual_vector)
    j = _finite_array(jacobian_rows)
    if j.ndim != 2:
        raise ValueError("jacobian_rows must be a 2D array")
    if r.ndim != 1 or r.size != j.shape[0]:
        raise ValueError("residual_vector length must match jacobian row count")
    if len(row_labels) != j.shape[0]:
        raise ValueError("row_labels length must match row count")
    if len(variable_labels) != j.shape[1]:
        raise ValueError("variable_labels length must match column count")

    primary_set = label_set(primary_labels)
    constraint_set = label_set(constraint_labels)
    primary_indexes = _selected_indexes(row_labels, primary_set)
    constraint_indexes = _selected_indexes(row_labels, constraint_set)
    if not primary_indexes:
        primary_indexes = [
            index for index, label in enumerate(row_labels) if not _label_matches(label, constraint_set)
        ]
    if not primary_indexes:
        raise ValueError("rank report has no primary rows")

    jm = _finite_array(j[primary_indexes, :])
    rm = _finite_array(r[primary_indexes])
    c = _finite_array(j[constraint_indexes, :]) if constraint_indexes else np.zeros((0, j.shape[1]))
    jm_singular = np.linalg.svd(jm, compute_uv=False) if jm.size else np.asarray([], dtype=float)
    jm_rank = _rank_from_svd(jm_singular)
    n_basis, c_singular, c_rank = _nullspace(c)
    n_basis = _finite_array(n_basis)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        jmn = _finite_array(jm @ n_basis) if n_basis.size else np.zeros((jm.shape[0], 0))
    jmn_singular = np.linalg.svd(jmn, compute_uv=False) if jmn.size else np.asarray([], dtype=float)
    jmn_rank = _rank_from_svd(jmn_singular)

    target = -rm
    if jmn.size and jmn.shape[1] > 0:
        z, *_ = np.linalg.lstsq(jmn, target, rcond=None)
        z = _finite_array(z)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            projected_change = _finite_array(jmn @ z)
            feasible_step = _finite_array(n_basis @ z)
    else:
        projected_change = np.zeros_like(rm)
        feasible_step = np.zeros(j.shape[1])

    rm_l2 = float(np.linalg.norm(rm))
    rm_max = float(np.max(np.abs(rm))) if rm.size else 0.0
    projected_l2 = float(np.linalg.norm(projected_change))
    rho_range = projected_l2 / max(rm_l2, 1e-300)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        gradient = _finite_array(jm.T @ rm)
    if n_basis.size:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            projected_gradient = _finite_array(n_basis @ (n_basis.T @ gradient))
    else:
        projected_gradient = np.zeros_like(gradient)
    rho_grad = float(np.linalg.norm(projected_gradient)) / max(float(np.linalg.norm(gradient)), 1e-300)
    residual_after_best = rm + projected_change
    predicted_best_factor = (
        float(np.max(np.abs(residual_after_best))) / max(rm_max, 1e-300) if rm.size else 0.0
    )

    step_array = _finite_array(step) if step is not None else None
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        constraint_change = _finite_array(c @ step_array) if step_array is not None and c.size else np.asarray([], dtype=float)
    signed_constraint_growth = (
        np.sign(r[constraint_indexes]) * constraint_change
        if constraint_change.size and constraint_indexes
        else np.asarray([], dtype=float)
    )
    positive_growth_count = int(np.sum(signed_constraint_growth > 0.0)) if signed_constraint_growth.size else 0
    predicted_constraint = (
        r[constraint_indexes] + constraint_change if constraint_change.size and constraint_indexes else np.asarray([])
    )
    leverage = np.linalg.norm(jm, axis=0) if jm.size else np.zeros(j.shape[1])
    heldout = None if heldout_global_mortar_max is None else float(heldout_global_mortar_max)
    active_raw = (
        float(active_primary_raw_max)
        if active_primary_raw_max is not None
        else (float(np.max(np.abs(rm))) if rm.size else 0.0)
    )
    coverage = None
    coverage_ok = None
    if heldout is not None and heldout > 0.0:
        coverage = active_raw / heldout
        coverage_ok = coverage >= coverage_min

    return {
        "status": STATUS,
        "diagnostic_vs_proof": "floating guarded-KKT rank/angle diagnostic only; no interval proof",
        "linear_algebra_backend": "numpy_svd_lstsq",
        "rank_obstruction": bool(rho_range <= 1e-8 and rho_grad <= 1e-8 and predicted_best_factor >= 0.99),
        "row_space_note": "uses the residual/Jacobian rows supplied by the caller, typically post row-scaling",
        "primary_labels": sorted(primary_set),
        "constraint_labels": sorted(constraint_set),
        "rows": {
            "total": int(j.shape[0]),
            "primary": len(primary_indexes),
            "constraints": len(constraint_indexes),
        },
        "columns": int(j.shape[1]),
        "coverage": {
            "active_primary_raw_max": active_raw,
            "heldout_global_mortar_max": heldout,
            "coverage": coverage,
            "coverage_min": coverage_min,
            "coverage_ok": coverage_ok,
            "note": "coverage uses unweighted raw residual metadata when provided",
        },
        "constraint_space": {
            "rank": c_rank,
            "nullity": int(j.shape[1] - c_rank),
            "singular_values": [_json_float(value) for value in c_singular[: min(24, c_singular.size)]],
            "residual_metrics": _metrics(r[constraint_indexes]),
        },
        "primary_space": {
            "rank": jm_rank,
            "singular_values": [_json_float(value) for value in jm_singular[: min(24, jm_singular.size)]],
            "rank_projected": jmn_rank,
            "singular_values_projected": [_json_float(value) for value in jmn_singular[: min(24, jmn_singular.size)]],
            "residual_metrics": _metrics(rm),
        },
        "angle": {
            "rho_range": rho_range,
            "rho_grad": rho_grad,
            "predicted_best_factor_inf": predicted_best_factor,
            "projected_change_metrics": _metrics(projected_change),
            "best_feasible_step_metrics": _metrics(feasible_step),
        },
        "provided_step": {
            "present": step_array is not None,
            "metrics": _metrics(step_array if step_array is not None else []),
            "constraint_change_metrics": _metrics(constraint_change),
            "signed_constraint_growth_metrics": _metrics(signed_constraint_growth),
            "positive_signed_constraint_growth_count": positive_growth_count,
            "max_signed_constraint_growth": (
                float(np.max(signed_constraint_growth)) if signed_constraint_growth.size else 0.0
            ),
            "predicted_constraint_metrics": _metrics(predicted_constraint),
        },
        "top_variables": _top_variables(variable_labels, gradient, projected_gradient, step_array, leverage, top_n),
    }


def compute_rank_report(
    r: list[float] | np.ndarray,
    J: list[list[float]] | np.ndarray,
    row_labels: list[str],
    selected_variable_names: list[str],
    primary_labels: str | set[str] | list[str],
    constraint_labels: str | set[str] | list[str],
    *,
    heldout_global_mortar_max: float | None = None,
    h: list[float] | np.ndarray | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Alias with the shorter argument names used in handoff prompts."""

    return compute_guarded_kkt_rank_report(
        r,
        J,
        row_labels,
        selected_variable_names,
        primary_labels,
        constraint_labels,
        heldout_global_mortar_max=heldout_global_mortar_max,
        step=h,
        **kwargs,
    )


def _write_json(path: str, data: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def self_test() -> dict[str, Any]:
    # x0 moves the primary row; x1 is constrained.  The nullspace still has a
    # seam direction, so rho_range should be close to one.
    residual = [10.0, 0.0]
    jacobian = [[1.0, 1.0], [0.0, 1.0]]
    report = compute_guarded_kkt_rank_report(
        residual,
        jacobian,
        ["mortar", "active_guard"],
        ["x0", "x1"],
        {"mortar"},
        {"active_guard"},
        heldout_global_mortar_max=10.0,
        active_primary_raw_max=10.0,
    )
    if report["coverage"]["coverage_ok"] is not True:
        raise RuntimeError("coverage self-test failed")
    if float(report["angle"]["rho_range"]) < 0.99:
        raise RuntimeError("rho_range self-test failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("only --self-test is currently supported")
    try:
        report = self_test()
    except RuntimeError as exc:
        report = {
            "status": STATUS,
            "diagnostic_vs_proof": "floating guarded-KKT rank/angle diagnostic only; no interval proof",
            "error": str(exc),
            "self_test": {"ok": False, "error": str(exc)},
        }
    if args.out:
        _write_json(args.out, report)
    print(f"status={report['status']}")
    if "error" in report:
        print(f"error={report['error']}")
        print(f"self_test_ok={report['self_test']['ok']}")
    else:
        print(f"coverage={report['coverage']['coverage']:.12e}")
        print(f"rho_range={report['angle']['rho_range']:.12e}")


if __name__ == "__main__":
    main()
