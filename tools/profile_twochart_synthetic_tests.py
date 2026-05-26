#!/usr/bin/env python3
"""Synthetic guarded-KKT tests for the two-chart profile solver.

This is a lightweight algebra harness.  It does not evaluate the Euler profile,
the two-chart residual, or any interval proof object.  The cases here exercise
only small deterministic matrices that model the row/constraint geometry used
by guarded Stage-0 experiments.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sys
from typing import Any


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

PASS_STATUS = "SYNTHETIC_GUARDED_KKT_PASS_NOT_PROOF"
FAIL_STATUS = "SYNTHETIC_GUARDED_KKT_FAIL_NOT_PROOF"

Vector = list[float]
Matrix = list[list[float]]


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def parse_bool(raw: str) -> bool:
    lowered = raw.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean, got {raw!r}")


def dot(left: Vector, right: Vector) -> float:
    return sum(a * b for a, b in zip(left, right))


def add_vectors(left: Vector, right: Vector) -> Vector:
    return [a + b for a, b in zip(left, right)]


def scale_vector(scale: float, values: Vector) -> Vector:
    return [scale * value for value in values]


def norm2(values: Vector) -> float:
    return math.sqrt(sum(value * value for value in values))


def linf(values: Vector) -> float:
    return max((abs(value) for value in values), default=0.0)


def transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def mat_vec(matrix: Matrix, vector: Vector) -> Vector:
    return [dot(row, vector) for row in matrix]


def mat_mat(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right:
        return [[] for _ in left]
    right_t = transpose(right)
    return [[dot(row, column) for column in right_t] for row in left]


def identity(size: int) -> Matrix:
    return [[1.0 if row == column else 0.0 for column in range(size)] for row in range(size)]


def add_diagonal(matrix: Matrix, value: float) -> Matrix:
    out = [row[:] for row in matrix]
    for index in range(min(len(out), len(out[0]) if out else 0)):
        out[index][index] += value
    return out


def vector_metrics(values: Vector) -> dict[str, float]:
    if not values:
        return {"count": 0.0, "l2": 0.0, "linf": 0.0, "mean_abs": 0.0}
    return {
        "count": float(len(values)),
        "l2": norm2(values),
        "linf": linf(values),
        "mean_abs": sum(abs(value) for value in values) / len(values),
    }


def matrix_rank(matrix: Matrix, tolerance: float = 1e-10) -> int:
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


def rref(matrix: Matrix, tolerance: float = 1e-10) -> tuple[Matrix, list[int]]:
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


def nullspace(matrix: Matrix, columns: int, tolerance: float = 1e-10) -> Matrix:
    if not matrix:
        return identity(columns)
    reduced, pivots = rref(matrix, tolerance)
    pivot_set = set(pivots)
    free_columns = [column for column in range(columns) if column not in pivot_set]
    basis_columns: list[Vector] = []
    for free_column in free_columns:
        vector = [0.0 for _ in range(columns)]
        vector[free_column] = 1.0
        for row_index, pivot_column in enumerate(pivots):
            vector[pivot_column] = -reduced[row_index][free_column]
        basis_columns.append(vector)
    if not basis_columns:
        return [[] for _ in range(columns)]
    return transpose(basis_columns)


def solve_square(matrix: Matrix, rhs: Vector, tolerance: float = 1e-14) -> Vector:
    size = len(matrix)
    if size == 0:
        return []
    if any(len(row) != size for row in matrix) or len(rhs) != size:
        raise ValueError("solve_square requires a square matrix and matching rhs")
    work = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) <= tolerance:
            raise ValueError("singular matrix in synthetic solve")
        work[column], work[pivot] = work[pivot], work[column]
        pivot_value = work[column][column]
        for row in range(column + 1, size):
            factor = work[row][column] / pivot_value
            if abs(factor) <= tolerance:
                continue
            for entry in range(column, size + 1):
                work[row][entry] -= factor * work[column][entry]
    solution = [0.0 for _ in range(size)]
    for row in range(size - 1, -1, -1):
        residual = work[row][size] - sum(work[row][column] * solution[column] for column in range(row + 1, size))
        solution[row] = residual / work[row][row]
    return solution


def solve_least_squares(matrix: Matrix, rhs: Vector, ridge: float = 1e-12) -> Vector:
    if not matrix:
        return []
    columns = len(matrix[0]) if matrix[0] else 0
    if columns == 0:
        return []
    matrix_t = transpose(matrix)
    normal = add_diagonal(mat_mat(matrix_t, matrix), ridge)
    normal_rhs = mat_vec(matrix_t, rhs)
    return solve_square(normal, normal_rhs)


def guarded_kkt_step(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    constraint_jacobian: Matrix,
    lm_lambda: float,
) -> tuple[Vector, dict[str, Any]]:
    if not primary_jacobian:
        raise ValueError("guarded KKT requires primary rows")
    variable_count = len(primary_jacobian[0])
    primary_t = transpose(primary_jacobian)
    hessian = add_diagonal(mat_mat(primary_t, primary_jacobian), lm_lambda)
    gradient = mat_vec(primary_t, primary_residual)
    if constraint_jacobian:
        constraint_count = len(constraint_jacobian)
        top = [row[:] + [constraint_jacobian[crow][column] for crow in range(constraint_count)] for column, row in enumerate(hessian)]
        bottom = [constraint_jacobian[row][:] + [0.0 for _ in range(constraint_count)] for row in range(constraint_count)]
        kkt_matrix = top + bottom
        rhs = scale_vector(-1.0, gradient) + [0.0 for _ in range(constraint_count)]
    else:
        kkt_matrix = hessian
        rhs = scale_vector(-1.0, gradient)
    try:
        solution = solve_square(kkt_matrix, rhs)
    except ValueError:
        solution = solve_least_squares(kkt_matrix, rhs)
    step = solution[:variable_count]
    primary_change = mat_vec(primary_jacobian, step)
    constraint_change = mat_vec(constraint_jacobian, step) if constraint_jacobian else []
    return step, {
        "method": "synthetic-guarded-kkt-equality",
        "variables": variable_count,
        "primary_rows": len(primary_jacobian),
        "constraint_rows": len(constraint_jacobian),
        "lm_lambda": lm_lambda,
        "kkt_rank": matrix_rank(kkt_matrix),
        "primary_change_metrics": vector_metrics(primary_change),
        "constraint_change_metrics": vector_metrics(constraint_change),
        "step_metrics": vector_metrics(step),
    }


def objective_value(jacobian: Matrix, residual: Vector, step: Vector, lm_lambda: float) -> float:
    updated = add_vectors(residual, mat_vec(jacobian, step))
    return 0.5 * dot(updated, updated) + 0.5 * lm_lambda * dot(step, step)


def sign_value(value: float) -> float:
    return 1.0 if value >= 0.0 else -1.0


def signed_guard_jacobian(guard_jacobian: Matrix, guard_residual: Vector) -> Matrix:
    return [
        scale_vector(sign_value(guard_residual[index]), row_values)
        for index, row_values in enumerate(guard_jacobian)
    ]


def signed_guard_growth(guard_jacobian: Matrix, guard_residual: Vector, step: Vector) -> Vector:
    raw_change = mat_vec(guard_jacobian, step)
    return [
        sign_value(guard_residual[index]) * value
        for index, value in enumerate(raw_change)
    ]


def local_active_set_step(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    guard_jacobian: Matrix,
    guard_residual: Vector,
    lm_lambda: float,
    tolerance: float = 1e-12,
) -> tuple[Vector, dict[str, Any]]:
    """Solve a tiny deterministic guard no-growth problem by active-set enumeration.

    This fallback is intentionally small and auditable.  It solves

        min_h 1/2 ||r + J h||^2 + lambda/2 ||h||^2
        subject to sign(g_i) J_g_i h <= 0.

    The synthetic cases have very few guard rows, so enumerating active subsets
    is clearer than embedding a general QP implementation in this harness.
    """

    if not primary_jacobian:
        raise ValueError("active-set fallback requires primary rows")
    guard_count = len(guard_jacobian)
    signed_constraints = signed_guard_jacobian(guard_jacobian, guard_residual)
    best_step: Vector | None = None
    best_objective = math.inf
    best_active_set: list[int] = []
    feasible_candidates = 0
    max_masks = 1 << guard_count
    for mask in range(max_masks):
        active_indices = [index for index in range(guard_count) if mask & (1 << index)]
        active_constraints = [signed_constraints[index] for index in active_indices]
        try:
            step, _report = guarded_kkt_step(
                primary_jacobian,
                primary_residual,
                active_constraints,
                lm_lambda,
            )
        except Exception:
            continue
        signed_growth = mat_vec(signed_constraints, step)
        if any(value > tolerance for value in signed_growth):
            continue
        feasible_candidates += 1
        objective = objective_value(primary_jacobian, primary_residual, step, lm_lambda)
        if objective < best_objective:
            best_step = step
            best_objective = objective
            best_active_set = active_indices
    if best_step is None:
        best_step = [0.0 for _column in range(len(primary_jacobian[0]))]
        best_objective = objective_value(primary_jacobian, primary_residual, best_step, lm_lambda)
    signed_growth = signed_guard_growth(guard_jacobian, guard_residual, best_step)
    return best_step, {
        "method": "local-active-set-enumeration",
        "variables": len(primary_jacobian[0]),
        "primary_rows": len(primary_jacobian),
        "guard_rows": guard_count,
        "lm_lambda": lm_lambda,
        "active_set": best_active_set,
        "enumerated_active_sets": max_masks,
        "feasible_candidates": feasible_candidates,
        "objective": best_objective,
        "signed_guard_growth_metrics": vector_metrics(signed_growth),
        "max_signed_guard_growth": max(signed_growth, default=0.0),
        "step_metrics": vector_metrics(best_step),
    }


def external_active_set_step(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    guard_jacobian: Matrix,
    guard_residual: Vector,
    lm_lambda: float,
) -> tuple[Vector, dict[str, Any]] | None:
    try:
        module = importlib.import_module("validators.guarded_kkt_active_set")
    except Exception:
        return None
    function_names = (
        "solve_guarded_active_set",
        "guarded_active_set_step",
        "guarded_ineq_kkt_step",
        "active_set_step",
        "solve_active_set",
    )
    for function_name in function_names:
        function = getattr(module, function_name, None)
        if not callable(function):
            continue
        try:
            result = function(
                primary_jacobian=primary_jacobian,
                primary_residual=primary_residual,
                guard_jacobian=guard_jacobian,
                guard_residual=guard_residual,
                lm_lambda=lm_lambda,
            )
        except TypeError:
            try:
                result = function(primary_jacobian, primary_residual, guard_jacobian, guard_residual, lm_lambda)
            except Exception:
                continue
        except Exception:
            continue
        if isinstance(result, tuple) and len(result) == 2:
            step, report = result
        elif isinstance(result, dict) and "step" in result:
            step = result["step"]
            report = result
        else:
            continue
        if not isinstance(step, list):
            continue
        return [float(value) for value in step], {
            "method": f"validators.guarded_kkt_active_set.{function_name}",
            **(report if isinstance(report, dict) else {}),
        }
    return None


def active_set_step(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    guard_jacobian: Matrix,
    guard_residual: Vector,
    lm_lambda: float,
) -> tuple[Vector, dict[str, Any]]:
    external = external_active_set_step(
        primary_jacobian,
        primary_residual,
        guard_jacobian,
        guard_residual,
        lm_lambda,
    )
    if external is not None:
        return external
    return local_active_set_step(
        primary_jacobian,
        primary_residual,
        guard_jacobian,
        guard_residual,
        lm_lambda,
    )


def column_norms(matrix: Matrix) -> Vector:
    if not matrix or not matrix[0]:
        return []
    return [norm2([row[column] for row in matrix]) for column in range(len(matrix[0]))]


def local_rank_report(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    constraint_jacobian: Matrix,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    variable_count = len(primary_jacobian[0]) if primary_jacobian else 0
    feasible_basis = nullspace(constraint_jacobian, variable_count, tolerance=tolerance)
    projected = mat_mat(primary_jacobian, feasible_basis)
    target = scale_vector(-1.0, primary_residual)
    target_norm = norm2(target)
    if not projected or not projected[0]:
        fitted = [0.0 for _ in primary_residual]
    else:
        coefficients = solve_least_squares(projected, target)
        fitted = mat_vec(projected, coefficients)
    best_residual = add_vectors(primary_residual, fitted)
    primary_gradient = mat_vec(transpose(primary_jacobian), primary_residual)
    feasible_gradient = mat_vec(transpose(feasible_basis), primary_gradient) if feasible_basis and feasible_basis[0] else []
    gradient_norm = norm2(primary_gradient)
    predicted_factor = linf(best_residual) / max(linf(primary_residual), 1e-300)
    rho_range = norm2(fitted) / target_norm if target_norm > 0.0 else 1.0
    rho_grad = norm2(feasible_gradient) / gradient_norm if gradient_norm > 0.0 else 1.0
    obstruction = bool(rho_range <= 1e-8 and rho_grad <= 1e-8 and predicted_factor >= 0.99)
    return {
        "backend": "local_fallback",
        "constraint_rank": matrix_rank(constraint_jacobian, tolerance),
        "nullity": len(feasible_basis[0]) if feasible_basis else 0,
        "projected_primary_rank": matrix_rank(projected, tolerance),
        "projected_primary_column_norms": column_norms(projected),
        "rho_range": rho_range,
        "rho_grad": rho_grad,
        "predicted_best_factor_linf": predicted_factor,
        "best_residual_metrics": vector_metrics(best_residual),
        "rank_obstruction": obstruction,
    }


def external_rank_report(
    primary_jacobian: Matrix,
    primary_residual: Vector,
    constraint_jacobian: Matrix,
) -> dict[str, Any] | None:
    try:
        module = importlib.import_module("validators.guarded_kkt_rank")
    except Exception:
        return None
    function = getattr(module, "compute_guarded_kkt_rank_report", None)
    if callable(function):
        residual = primary_residual + [0.0 for _row in constraint_jacobian]
        jacobian = primary_jacobian + constraint_jacobian
        labels = ["mortar" for _row in primary_jacobian] + ["active_guard" for _row in constraint_jacobian]
        variable_count = len(primary_jacobian[0]) if primary_jacobian else len(constraint_jacobian[0])
        report = function(
            residual,
            jacobian,
            labels,
            [f"x{index}" for index in range(variable_count)],
            {"mortar"},
            {"active_guard"},
            heldout_global_mortar_max=linf(primary_residual),
            active_primary_raw_max=linf(primary_residual),
        )
        return {"backend": "validators.guarded_kkt_rank.compute_guarded_kkt_rank_report", **report}
    return None


def row(row_id: str, label: str, q: float | None = None, side: str = "") -> dict[str, Any]:
    data: dict[str, Any] = {"row_id": row_id, "label": label}
    if q is not None:
        data["q"] = q
        data["q_string"] = f"{q:.12f}"
    if side:
        data["chart_side"] = side
    return data


def run_mortar_polynomial(args: argparse.Namespace) -> dict[str, Any]:
    if args.solve_mode != "guarded-kkt":
        raise ValueError("synthetic harness currently supports only --solve-mode guarded-kkt")
    true_step = [-3.0, 2.0, -1.0, 0.0]
    primary_jacobian = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [1.0, -1.0, 0.5, 0.0],
    ]
    primary_residual = scale_vector(-1.0, mat_vec(primary_jacobian, true_step))
    constraint_jacobian = [[0.0, 0.0, 0.0, 1.0]]
    guard_residual = [4.0]
    step, kkt_report = guarded_kkt_step(
        primary_jacobian,
        primary_residual,
        constraint_jacobian,
        args.lm_lambda,
    )
    final_primary = add_vectors(primary_residual, mat_vec(primary_jacobian, step))
    final_guard = add_vectors(guard_residual, mat_vec(constraint_jacobian, step))
    reduction_factor = linf(primary_residual) / max(linf(final_primary), 1e-300)
    guard_growth = linf(final_guard) / max(linf(guard_residual), 1e-300)
    passed = reduction_factor >= args.expect_mortar_factor and guard_growth <= args.expect_guard_growth
    return {
        "case": "mortar-polynomial",
        "status": PASS_STATUS if passed else FAIL_STATUS,
        "pass": passed,
        "not_proof": True,
        "inputs": {
            "degree_tail": args.degree_tail,
            "degree_origin": args.degree_origin,
            "guard_grid": args.guard_grid,
            "perturb": args.perturb,
            "expect_mortar_factor": args.expect_mortar_factor,
            "expect_guard_growth": args.expect_guard_growth,
        },
        "rows": [
            row("mortar-poly:x=-1", "mortar"),
            row("mortar-poly:x=0", "mortar"),
            row("mortar-poly:x=1", "mortar"),
            row("mortar-poly:blend", "mortar"),
            row("edge-guard:locks-guard-variable", "active_guard"),
        ],
        "primary_initial_metrics": vector_metrics(primary_residual),
        "primary_final_metrics": vector_metrics(final_primary),
        "guard_initial_metrics": vector_metrics(guard_residual),
        "guard_final_metrics": vector_metrics(final_guard),
        "reduction_factor_linf": reduction_factor,
        "guard_growth_linf": guard_growth,
        "step": step,
        "kkt_report": kkt_report,
    }


def run_seam_switch(args: argparse.Namespace) -> dict[str, Any]:
    sides: list[tuple[str, float]] = []
    if args.guard_seam_sides in {"below", "both"}:
        sides.append(("below", args.guard_seam_q - args.guard_seam_eps))
    if args.guard_seam_sides in {"above", "both"}:
        sides.append(("above", args.guard_seam_q + args.guard_seam_eps))
    rows = [
        row(f"seam-limit:{side}:q={q_value:.12f}", "seam_limit", q=q_value, side=side)
        for side, q_value in sides
    ]
    q_strings = {item["q_string"] for item in rows}
    expected = {
        f"{args.guard_seam_q - args.guard_seam_eps:.12f}",
        f"{args.guard_seam_q + args.guard_seam_eps:.12f}",
    }
    passed = args.guard_seam_sides != "both" or expected.issubset(q_strings)
    return {
        "case": "seam-switch",
        "status": PASS_STATUS if passed else FAIL_STATUS,
        "pass": passed,
        "not_proof": True,
        "inputs": {
            "guard_seam_sides": args.guard_seam_sides,
            "guard_seam_q": args.guard_seam_q,
            "guard_seam_eps": args.guard_seam_eps,
        },
        "expected_q_strings_for_both": sorted(expected),
        "rows": rows,
        "row_count": len(rows),
    }


def run_infeasible_edge(args: argparse.Namespace) -> dict[str, Any]:
    if args.solve_mode != "guarded-kkt":
        raise ValueError("synthetic harness currently supports only --solve-mode guarded-kkt")
    primary_jacobian = [[1.0, 0.0], [0.5, 0.0]]
    primary_residual = [10.0, 5.0]
    constraint_jacobian = [[1.0, 0.0]]
    guard_residual = [7.0]
    step, kkt_report = guarded_kkt_step(
        primary_jacobian,
        primary_residual,
        constraint_jacobian,
        args.lm_lambda,
    )
    rank_report = external_rank_report(primary_jacobian, primary_residual, constraint_jacobian)
    if rank_report is None:
        rank_report = local_rank_report(primary_jacobian, primary_residual, constraint_jacobian)
    final_primary = add_vectors(primary_residual, mat_vec(primary_jacobian, step))
    final_guard = add_vectors(guard_residual, mat_vec(constraint_jacobian, step))
    rank_obstruction = bool(rank_report.get("rank_obstruction", False))
    passed = rank_obstruction if args.expect_rank_obstruction else True
    return {
        "case": "infeasible-edge",
        "status": PASS_STATUS if passed else FAIL_STATUS,
        "pass": passed,
        "not_proof": True,
        "inputs": {
            "expect_rank_obstruction": args.expect_rank_obstruction,
        },
        "rows": [
            row("mortar-infeasible:main", "mortar"),
            row("mortar-infeasible:secondary", "mortar"),
            row("edge-guard:locks-primary-direction", "active_guard"),
        ],
        "primary_initial_metrics": vector_metrics(primary_residual),
        "primary_final_metrics": vector_metrics(final_primary),
        "guard_initial_metrics": vector_metrics(guard_residual),
        "guard_final_metrics": vector_metrics(final_guard),
        "step": step,
        "kkt_report": kkt_report,
        "rank_report": rank_report,
    }


def run_inequality_guard_improves(args: argparse.Namespace) -> dict[str, Any]:
    if args.solve_mode != "guarded-kkt":
        raise ValueError("synthetic harness currently supports only --solve-mode guarded-kkt")

    # One primary seam row and one positive guard row share the same direction.
    # Equality no-change forces h=0, while the true signed no-growth inequality
    # h <= 0 allows h=-10, removing the primary residual and improving the guard.
    primary_jacobian = [[1.0]]
    primary_residual = [10.0]
    guard_jacobian = [[1.0]]
    guard_residual = [5.0]

    equality_step, equality_report = guarded_kkt_step(
        primary_jacobian,
        primary_residual,
        guard_jacobian,
        args.lm_lambda,
    )
    inequality_step, inequality_report = active_set_step(
        primary_jacobian,
        primary_residual,
        guard_jacobian,
        guard_residual,
        args.lm_lambda,
    )

    equality_primary = add_vectors(primary_residual, mat_vec(primary_jacobian, equality_step))
    inequality_primary = add_vectors(primary_residual, mat_vec(primary_jacobian, inequality_step))
    equality_guard = add_vectors(guard_residual, mat_vec(guard_jacobian, equality_step))
    inequality_guard = add_vectors(guard_residual, mat_vec(guard_jacobian, inequality_step))
    equality_signed_growth = signed_guard_growth(guard_jacobian, guard_residual, equality_step)
    inequality_signed_growth = signed_guard_growth(guard_jacobian, guard_residual, inequality_step)

    equality_factor = linf(equality_primary) / max(linf(primary_residual), 1e-300)
    inequality_factor = linf(inequality_primary) / max(linf(primary_residual), 1e-300)
    inequality_reduction_factor = linf(primary_residual) / max(linf(inequality_primary), 1e-300)
    max_signed_growth = max(inequality_signed_growth, default=0.0)
    equality_bad = equality_factor >= 0.99
    inequality_good = inequality_reduction_factor >= args.expect_mortar_factor
    guard_threshold = min(args.expect_guard_growth, 0.0)
    guard_ok = max_signed_growth <= guard_threshold + 1e-12
    passed = equality_bad and inequality_good and guard_ok

    return {
        "case": "inequality-guard-improves",
        "status": PASS_STATUS if passed else FAIL_STATUS,
        "pass": passed,
        "not_proof": True,
        "inputs": {
            "expect_mortar_factor": args.expect_mortar_factor,
            "expect_guard_growth": args.expect_guard_growth,
        },
        "rows": [
            row("mortar-ineq:shared-descent-direction", "mortar"),
            row("edge-guard:positive-residual-allows-negative-change", "active_guard"),
        ],
        "equality_no_change": {
            "step": equality_step,
            "primary_final_metrics": vector_metrics(equality_primary),
            "guard_final_metrics": vector_metrics(equality_guard),
            "signed_guard_growth": equality_signed_growth,
            "primary_factor_linf": equality_factor,
            "kkt_report": equality_report,
        },
        "inequality_no_growth": {
            "step": inequality_step,
            "primary_final_metrics": vector_metrics(inequality_primary),
            "guard_final_metrics": vector_metrics(inequality_guard),
            "signed_guard_growth": inequality_signed_growth,
            "primary_reduction_factor_linf": inequality_reduction_factor,
            "max_signed_guard_growth": max_signed_growth,
            "signed_guard_growth_threshold": guard_threshold,
            "active_set_report": inequality_report,
        },
        "primary_initial_metrics": vector_metrics(primary_residual),
        "guard_initial_metrics": vector_metrics(guard_residual),
        "checks": {
            "equality_no_change_is_bad": equality_bad,
            "inequality_reduces_primary": inequality_good,
            "signed_guard_growth_nonpositive": guard_ok,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("mortar-polynomial", "seam-switch", "infeasible-edge", "inequality-guard-improves"),
        required=True,
    )
    parser.add_argument("--solve-mode", choices=("guarded-kkt",), default="guarded-kkt")
    parser.add_argument("--out", required=True)
    parser.add_argument("--degree-tail", type=int, default=8)
    parser.add_argument("--degree-origin", type=int, default=8)
    parser.add_argument("--guard-grid", default="edge")
    parser.add_argument("--perturb", default="")
    parser.add_argument("--expect-mortar-factor", type=float, default=100.0)
    parser.add_argument("--expect-guard-growth", type=float, default=1.0)
    parser.add_argument("--expect-rank-obstruction", type=parse_bool, default=False)
    parser.add_argument("--guard-seam-sides", choices=("none", "below", "above", "both"), default="none")
    parser.add_argument("--guard-seam-q", type=float, default=0.90)
    parser.add_argument("--guard-seam-eps", type=float, default=1e-12)
    parser.add_argument("--lm-lambda", type=float, default=1e-12)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.case == "mortar-polynomial":
            report = run_mortar_polynomial(args)
        elif args.case == "seam-switch":
            report = run_seam_switch(args)
        elif args.case == "infeasible-edge":
            report = run_infeasible_edge(args)
        elif args.case == "inequality-guard-improves":
            report = run_inequality_guard_improves(args)
        else:  # pragma: no cover - argparse prevents this.
            raise ValueError(f"unknown case {args.case!r}")
    except Exception as exc:
        report = {
            "case": args.case,
            "status": FAIL_STATUS,
            "pass": False,
            "not_proof": True,
            "error": f"{type(exc).__name__}: {exc}",
        }
    save_json(args.out, report)
    print(f"{report['status']} case={args.case} out={args.out}")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
