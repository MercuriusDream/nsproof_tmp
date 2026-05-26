#!/usr/bin/env python3
"""Floating active-set KKT helper for guarded two-chart discovery.

This module is discovery infrastructure only.  It solves a local linearized
least-squares problem with first-order guard non-growth constraints

    sign(g_i) J_g_i h <= 0.

It does not validate a profile, prove feasibility of the nonlinear problem, or
replace interval certificates.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
except ImportError:  # pragma: no cover - depends on the local Python env.
    np = None  # type: ignore[assignment]


STATUS = "GUARDED_ACTIVE_SET_KKT_FLOATING_NOT_PROOF"


def _json_float(value: Any) -> float | str:
    out = float(value)
    if math.isnan(out):
        return "nan"
    if math.isinf(out):
        return "inf" if out > 0 else "-inf"
    return out


def _json_list(values: Iterable[Any]) -> list[float | str]:
    return [_json_float(value) for value in values]


def _metrics(values: Iterable[float]) -> dict[str, Any]:
    raw = [float(value) for value in values]
    if not raw:
        return {"count": 0, "max_abs": 0.0, "min": 0.0, "max": 0.0, "l2": 0.0, "rms": 0.0}
    l2 = math.sqrt(sum(value * value for value in raw))
    return {
        "count": len(raw),
        "max_abs": max(abs(value) for value in raw),
        "min": min(raw),
        "max": max(raw),
        "l2": l2,
        "rms": l2 / math.sqrt(len(raw)),
    }


def _positive_metrics(values: Iterable[float], tolerance: float) -> dict[str, Any]:
    raw = [float(value) for value in values]
    positives = [value for value in raw if value > tolerance]
    return {
        "positive_count": len(positives),
        "max_positive": max(positives) if positives else 0.0,
        "tolerance": float(tolerance),
    }


def _shape_matrix(matrix: Iterable[Iterable[Any]], name: str) -> tuple[list[list[float]], int, int]:
    rows = [[float(value) for value in row] for row in matrix]
    if not rows:
        return [], 0, 0
    columns = len(rows[0])
    for index, row in enumerate(rows):
        if len(row) != columns:
            raise ValueError(f"{name} row {index} has length {len(row)}; expected {columns}")
    return rows, len(rows), columns


def _shape_vector(vector: Iterable[Any], name: str, expected: int | None = None) -> list[float]:
    values = [float(value) for value in vector]
    if expected is not None and len(values) != expected:
        raise ValueError(f"{name} has length {len(values)}; expected {expected}")
    return values


def _sign(value: float) -> float:
    return 1.0 if value >= 0.0 else -1.0


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def _mat_vec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [_dot(row, vector) for row in matrix]


def _mat_mat(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    if not left:
        return []
    if not right:
        return [[] for _ in left]
    right_t = _transpose(right)
    return [[_dot(row, column) for column in right_t] for row in left]


def _add_identity(matrix: list[list[float]], value: float) -> list[list[float]]:
    out = [row[:] for row in matrix]
    for index in range(min(len(out), len(out[0]) if out else 0)):
        out[index][index] += value
    return out


def _solve_square_py(matrix: list[list[float]], rhs: list[float], tolerance: float = 1e-14) -> list[float]:
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


def _least_squares_py(matrix: list[list[float]], rhs: list[float], ridge: float = 1e-12) -> list[float]:
    if not matrix:
        return []
    columns = len(matrix[0]) if matrix[0] else 0
    if columns == 0:
        return []
    mt = _transpose(matrix)
    normal = _mat_mat(mt, matrix)
    for index in range(columns):
        normal[index][index] += ridge
    normal_rhs = _mat_vec(mt, rhs)
    return _solve_square_py(normal, normal_rhs)


def _solve_kkt_python(
    primary_jacobian: list[list[float]],
    primary_residual: list[float],
    signed_guard_jacobian: list[list[float]],
    active: list[int],
    lm_lambda: float,
) -> tuple[list[float], list[float]]:
    columns = len(primary_jacobian[0]) if primary_jacobian else (
        len(signed_guard_jacobian[0]) if signed_guard_jacobian else 0
    )
    if columns == 0:
        return [], []

    jt = _transpose(primary_jacobian)
    hessian = _mat_mat(jt, primary_jacobian)
    for index in range(columns):
        hessian[index][index] += float(lm_lambda)
    gradient = _mat_vec(jt, primary_residual)
    rhs_top = [-value for value in gradient]

    active_matrix = [signed_guard_jacobian[index] for index in active]
    if not active_matrix:
        try:
            return _solve_square_py(hessian, rhs_top), []
        except ValueError:
            return _least_squares_py(hessian, rhs_top), []

    active_t = _transpose(active_matrix)
    kkt: list[list[float]] = []
    for row_index in range(columns):
        kkt.append(hessian[row_index] + active_t[row_index])
    for row in active_matrix:
        kkt.append(row[:] + [0.0 for _ in active])
    rhs = rhs_top + [0.0 for _ in active]
    try:
        solution = _solve_square_py(kkt, rhs)
    except ValueError:
        solution = _least_squares_py(kkt, rhs, ridge=1e-12)
    return solution[:columns], solution[columns:]


def _solve_kkt_numpy(
    primary_jacobian: list[list[float]],
    primary_residual: list[float],
    signed_guard_jacobian: list[list[float]],
    active: list[int],
    lm_lambda: float,
) -> tuple[list[float], list[float]]:
    assert np is not None
    jp = np.asarray(primary_jacobian, dtype=float)
    rp = np.asarray(primary_residual, dtype=float)
    columns = int(jp.shape[1]) if jp.size else (
        len(signed_guard_jacobian[0]) if signed_guard_jacobian else 0
    )
    if columns == 0:
        return [], []
    if jp.size:
        hessian = jp.T @ jp
        gradient = jp.T @ rp
    else:
        hessian = np.zeros((columns, columns), dtype=float)
        gradient = np.zeros(columns, dtype=float)
    hessian = hessian + float(lm_lambda) * np.eye(columns)
    rhs_top = -gradient
    if not active:
        step = np.linalg.lstsq(hessian, rhs_top, rcond=None)[0]
        return _json_list(step), []
    c = np.asarray([signed_guard_jacobian[index] for index in active], dtype=float)
    top = np.concatenate([hessian, c.T], axis=1)
    bottom = np.concatenate([c, np.zeros((len(active), len(active)), dtype=float)], axis=1)
    kkt = np.concatenate([top, bottom], axis=0)
    rhs = np.concatenate([rhs_top, np.zeros(len(active), dtype=float)])
    solution = np.linalg.lstsq(kkt, rhs, rcond=None)[0]
    return _json_list(solution[:columns]), _json_list(solution[columns:])


def _predicted(primary_jacobian: list[list[float]], primary_residual: list[float], step: list[float]) -> list[float]:
    return [residual + _dot(row, step) for row, residual in zip(primary_jacobian, primary_residual)]


def _objective(primary_values: list[float], step: list[float], lm_lambda: float) -> float:
    return 0.5 * sum(value * value for value in primary_values) + 0.5 * float(lm_lambda) * sum(value * value for value in step)


def _build_guard_data(
    guard_jacobian: list[list[float]],
    guard_residual: list[float],
    target: str,
) -> tuple[list[list[float]], list[float], list[float]]:
    if target != "nonincrease":
        raise ValueError(f"unsupported target {target!r}; supported target is 'nonincrease'")
    signs = [_sign(value) for value in guard_residual]
    signed_guard_jacobian = [
        [signs[row_index] * value for value in row]
        for row_index, row in enumerate(guard_jacobian)
    ]
    rhs = [0.0 for _ in guard_residual]
    return signed_guard_jacobian, rhs, signs


def solve_guarded_active_set(
    primary_jacobian: Iterable[Iterable[Any]],
    primary_residual: Iterable[Any],
    guard_jacobian: Iterable[Iterable[Any]],
    guard_residual: Iterable[Any],
    lm_lambda: float = 1e-8,
    max_active: int = 64,
    tolerance: float = 1e-10,
    target: str = "nonincrease",
) -> dict[str, Any]:
    """Solve a floating guarded least-squares step by active-set KKT.

    The returned report is JSON-serializable.  `pass=true` means the final
    linearized step satisfies all guard inequalities up to `tolerance`; it is
    not a nonlinear acceptance test.
    """

    try:
        jp, primary_rows, primary_columns = _shape_matrix(primary_jacobian, "primary_jacobian")
        rp = _shape_vector(primary_residual, "primary_residual", primary_rows)
        jg, guard_rows, guard_columns = _shape_matrix(guard_jacobian, "guard_jacobian")
        rg = _shape_vector(guard_residual, "guard_residual", guard_rows)
        if primary_columns == 0 and guard_columns == 0:
            columns = 0
        elif primary_columns == 0:
            columns = guard_columns
        elif guard_columns == 0:
            columns = primary_columns
        elif primary_columns == guard_columns:
            columns = primary_columns
        else:
            raise ValueError(
                f"primary_jacobian has {primary_columns} columns but guard_jacobian has {guard_columns}"
            )
        if primary_columns == 0 and primary_rows:
            jp = [[] for _ in range(primary_rows)]
        if guard_columns == 0 and guard_rows:
            jg = [[] for _ in range(guard_rows)]
        signed_jg, guard_rhs, guard_signs = _build_guard_data(jg, rg, target)
        backend = "numpy_lstsq" if np is not None else "python_fallback"
        active: list[int] = []
        iterations: list[dict[str, Any]] = []
        step = [0.0 for _ in range(columns)]
        multipliers: list[float] = []
        status = STATUS
        failure_reason: str | None = None
        max_iterations = max(1, int(max_active) + guard_rows + 1)
        for iteration in range(max_iterations):
            if np is not None:
                step, multipliers = _solve_kkt_numpy(jp, rp, signed_jg, active, lm_lambda)
            else:
                step, multipliers = _solve_kkt_python(jp, rp, signed_jg, active, lm_lambda)
            signed_growth = [
                _dot(row, step) - guard_rhs[index]
                for index, row in enumerate(signed_jg)
            ]
            inactive = [index for index in range(guard_rows) if index not in set(active)]
            worst_index: int | None = None
            worst_violation = 0.0
            for index in inactive:
                violation = signed_growth[index]
                if violation > worst_violation:
                    worst_violation = violation
                    worst_index = index
            predicted_primary = _predicted(jp, rp, step)
            iterations.append(
                {
                    "iteration": iteration,
                    "active_count": len(active),
                    "added_constraint": worst_index if worst_violation > tolerance else None,
                    "max_violation": _json_float(worst_violation),
                    "primary_max_abs": _json_float(_metrics(predicted_primary)["max_abs"]),
                    "step_l2": _json_float(math.sqrt(sum(value * value for value in step))),
                }
            )
            if worst_violation <= tolerance:
                break
            if len(active) >= int(max_active):
                failure_reason = "max_active_reached"
                break
            if worst_index is None:
                break
            active.append(worst_index)
        else:
            failure_reason = "max_iterations_reached"

        signed_growth = [_dot(row, step) - guard_rhs[index] for index, row in enumerate(signed_jg)]
        guard_predicted = [residual + _dot(row, step) for row, residual in zip(jg, rg)]
        primary_predicted = _predicted(jp, rp, step)
        primary_before_metrics = _metrics(rp)
        primary_after_metrics = _metrics(primary_predicted)
        objective_before = _objective(rp, [0.0 for _ in step], lm_lambda)
        objective_after = _objective(primary_predicted, step, lm_lambda)
        max_guard_violation = max((value for value in signed_growth), default=0.0)
        guard_pass = max_guard_violation <= tolerance
        report_pass = guard_pass and failure_reason is None
        if not guard_pass and failure_reason is None:
            failure_reason = "guard_violation"

        active_constraints = [
            {
                "index": index,
                "guard_residual": _json_float(rg[index]),
                "sign": _json_float(guard_signs[index]),
                "signed_growth": _json_float(signed_growth[index]),
                "predicted_guard_residual": _json_float(guard_predicted[index]),
                "multiplier": _json_float(multipliers[position]) if position < len(multipliers) else None,
            }
            for position, index in enumerate(active)
        ]
        return {
            "status": status,
            "pass": bool(report_pass),
            "failure_reason": failure_reason,
            "backend": backend,
            "target": target,
            "parameters": {
                "lm_lambda": float(lm_lambda),
                "max_active": int(max_active),
                "tolerance": float(tolerance),
            },
            "dimensions": {
                "primary_rows": primary_rows,
                "guard_rows": guard_rows,
                "columns": columns,
            },
            "step": _json_list(step),
            "active_constraints": active_constraints,
            "iterations": iterations,
            "predicted_primary_metrics": {
                "before": primary_before_metrics,
                "after": primary_after_metrics,
                "delta": {
                    "max_abs": primary_after_metrics["max_abs"] - primary_before_metrics["max_abs"],
                    "l2": primary_after_metrics["l2"] - primary_before_metrics["l2"],
                    "objective": objective_after - objective_before,
                },
                "factor": {
                    "max_abs": (
                        primary_after_metrics["max_abs"] / primary_before_metrics["max_abs"]
                        if primary_before_metrics["max_abs"] > 0
                        else 0.0
                    ),
                    "l2": (
                        primary_after_metrics["l2"] / primary_before_metrics["l2"]
                        if primary_before_metrics["l2"] > 0
                        else 0.0
                    ),
                    "objective": objective_after / objective_before if objective_before > 0 else 0.0,
                },
                "objective_before": objective_before,
                "objective_after": objective_after,
            },
            "signed_guard_growth_metrics": {
                "all": _metrics(signed_growth),
                "positive": _positive_metrics(signed_growth, tolerance),
                "max_violation": max_guard_violation,
            },
            "guard_abs_metrics": {
                "before": _metrics([abs(value) for value in rg]),
                "after": _metrics([abs(value) for value in guard_predicted]),
            },
            "guard_predictions": [
                {
                    "index": index,
                    "guard_residual": _json_float(rg[index]),
                    "sign": _json_float(guard_signs[index]),
                    "signed_growth": _json_float(signed_growth[index]),
                    "predicted_guard_residual": _json_float(guard_predicted[index]),
                    "violates": bool(signed_growth[index] > tolerance),
                }
                for index in range(guard_rows)
            ],
        }
    except Exception as exc:  # noqa: BLE001 - this helper must fail as JSON.
        return {
            "status": "GUARDED_ACTIVE_SET_KKT_FAILURE",
            "pass": False,
            "failure_reason": str(exc),
            "backend": "numpy_lstsq" if np is not None else "python_fallback",
            "target": target,
            "parameters": {
                "lm_lambda": float(lm_lambda),
                "max_active": int(max_active),
                "tolerance": float(tolerance),
            },
        }


def self_test() -> dict[str, Any]:
    constrained = solve_guarded_active_set(
        primary_jacobian=[[1.0, 0.0], [0.0, 1.0]],
        primary_residual=[-2.0, -1.0],
        guard_jacobian=[[1.0, 0.0], [0.0, 1.0]],
        guard_residual=[3.0, -4.0],
        lm_lambda=1e-10,
        max_active=4,
        tolerance=1e-9,
    )
    unconstrained = solve_guarded_active_set(
        primary_jacobian=[[1.0, 0.0], [0.0, 1.0]],
        primary_residual=[-1.0, -0.5],
        guard_jacobian=[[-1.0, 0.0]],
        guard_residual=[2.0],
        lm_lambda=1e-10,
        max_active=4,
        tolerance=1e-9,
    )
    constrained_step = [float(value) for value in constrained.get("step", [])]
    unconstrained_step = [float(value) for value in unconstrained.get("step", [])]
    constrained_ok = (
        bool(constrained.get("pass"))
        and len(constrained_step) == 2
        and abs(constrained_step[0]) <= 1e-6
        and abs(constrained_step[1] - 1.0) <= 1e-6
        and constrained["signed_guard_growth_metrics"]["positive"]["positive_count"] == 0
        and len(constrained.get("active_constraints", [])) >= 1
    )
    unconstrained_ok = (
        bool(unconstrained.get("pass"))
        and len(unconstrained_step) == 2
        and abs(unconstrained_step[0] - 1.0) <= 1e-6
        and abs(unconstrained_step[1] - 0.5) <= 1e-6
        and len(unconstrained.get("active_constraints", [])) == 0
    )
    return {
        "status": "GUARDED_ACTIVE_SET_KKT_SELFTEST",
        "ok": bool(constrained_ok and unconstrained_ok),
        "numpy_available": bool(np is not None),
        "constrained_case": constrained,
        "unconstrained_case": unconstrained,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run deterministic active-set tests")
    parser.add_argument("--out", help="write JSON report to this path")
    args = parser.parse_args()
    if not args.self_test:
        parser.print_help()
        return 2
    report = self_test()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
