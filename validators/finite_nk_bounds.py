#!/usr/bin/env python3
"""C-backed finite-block Newton-Kantorovich interval bounds.

This module computes the finite-dimensional quantities needed by the profile
NK validator once a residual vector, Jacobian block, and approximate inverse
are exported:

    Y0 >= ||A r||_inf
    Z0 >= ||I - A J||_inf

The arithmetic is routed through ``validators.interval_backend``, whose hot
matvec and norm operations are native C kernels.  This is not the infinite-tail
or Bernstein residual validator; it is the finite-block bound primitive that
those validators will call.
"""

from __future__ import annotations

from typing import Any, Iterable

from validators.interval_backend import (
    Interval,
    interval_left_matmul_identity_defect_inf_norm,
    interval_matrix_inf_norm,
    interval_matvec,
    interval_matvec_inf_norm,
    interval_sub,
    interval_vector_inf_norm,
)


def _point_interval(value: float | int) -> Interval:
    return Interval(float(value), float(value))


def _coerce_interval(value: Interval | float | int | list[float] | tuple[float, float]) -> Interval:
    if isinstance(value, Interval):
        return value
    if isinstance(value, (float, int)):
        return _point_interval(value)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return Interval(float(value[0]), float(value[1]))
    raise TypeError(f"cannot coerce interval value {value!r}")


def coerce_vector(values: Iterable[Interval | float | int | list[float] | tuple[float, float]]) -> list[Interval]:
    out = [_coerce_interval(value) for value in values]
    if not out:
        raise ValueError("expected a nonempty vector")
    return out


def coerce_matrix(
    values: Iterable[Iterable[Interval | float | int | list[float] | tuple[float, float]]],
) -> list[list[Interval]]:
    rows = [coerce_vector(row) for row in values]
    if not rows:
        raise ValueError("expected a nonempty matrix")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix rows must have stable width")
    return rows


def interval_repr(value: Interval) -> list[float]:
    return [float(value.lo), float(value.hi)]


def vector_repr(values: list[Interval]) -> list[list[float]]:
    return [interval_repr(value) for value in values]


def matrix_repr(values: list[list[Interval]]) -> list[list[list[float]]]:
    return [vector_repr(row) for row in values]


def interval_matmul(lhs: list[list[Interval]], rhs: list[list[Interval]]) -> list[list[Interval]]:
    if len(lhs[0]) != len(rhs):
        raise ValueError("matrix product dimension mismatch")
    width = len(rhs[0])
    columns = [[rhs[row][column] for row in range(len(rhs))] for column in range(width)]
    column_products = [interval_matvec(lhs, column) for column in columns]
    return [
        [column_products[column][row] for column in range(width)]
        for row in range(len(lhs))
    ]


def identity_minus(matrix: list[list[Interval]]) -> list[list[Interval]]:
    if len(matrix) != len(matrix[0]):
        raise ValueError("I - matrix requires a square matrix")
    out: list[list[Interval]] = []
    for row_index, row in enumerate(matrix):
        out_row: list[Interval] = []
        for column_index, value in enumerate(row):
            identity = _point_interval(1.0 if row_index == column_index else 0.0)
            out_row.append(interval_sub([identity], [value])[0])
        out.append(out_row)
    return out


def finite_nk_bounds(
    residual: Iterable[Interval | float | int | list[float] | tuple[float, float]],
    jacobian: Iterable[Iterable[Interval | float | int | list[float] | tuple[float, float]]],
    approximate_inverse: Iterable[Iterable[Interval | float | int | list[float] | tuple[float, float]]],
) -> dict[str, Any]:
    """Compute finite-block NK bounds using native interval linear algebra.

    Shapes follow the overdetermined profile convention:

    - ``residual`` has length ``m``;
    - ``jacobian`` has shape ``m x n``;
    - ``approximate_inverse`` has shape ``n x m``.

    Then ``A r`` has length ``n`` and ``I_n - A J`` has shape ``n x n``.
    """

    residual_i = coerce_vector(residual)
    jacobian_i = coerce_matrix(jacobian)
    inverse_i = coerce_matrix(approximate_inverse)
    residual_dimension = len(residual_i)
    coefficient_dimension = len(jacobian_i[0])
    if len(jacobian_i) != residual_dimension:
        raise ValueError("jacobian row count must match residual length")
    if len(inverse_i) != coefficient_dimension or len(inverse_i[0]) != residual_dimension:
        raise ValueError(
            "approximate inverse must have shape coefficient_dimension x residual_dimension"
        )

    correction = interval_matvec(inverse_i, residual_i)
    inverse_jacobian = interval_matmul(inverse_i, jacobian_i)
    defect = identity_minus(inverse_jacobian)
    return {
        "residual_dimension": residual_dimension,
        "coefficient_dimension": coefficient_dimension,
        "backend": "native-c-outward-rounded-double-interval",
        "A_times_r": vector_repr(correction),
        "A_times_J": matrix_repr(inverse_jacobian),
        "defect_matrix_B_equals_I_minus_AJ": matrix_repr(defect),
        "Y0_infinity_norm_A_r": interval_vector_inf_norm(correction),
        "Z0_infinity_norm_B": interval_matrix_inf_norm(defect),
    }


def finite_nk_bound_summary(
    residual: Iterable[Interval | float | int | list[float] | tuple[float, float]],
    jacobian: Iterable[Iterable[Interval | float | int | list[float] | tuple[float, float]]],
    approximate_inverse: Iterable[Iterable[Interval | float | int | list[float] | tuple[float, float]]],
) -> dict[str, Any]:
    """Compute only finite-block NK norms through native C kernels."""

    residual_i = coerce_vector(residual)
    jacobian_i = coerce_matrix(jacobian)
    inverse_i = coerce_matrix(approximate_inverse)
    residual_dimension = len(residual_i)
    coefficient_dimension = len(jacobian_i[0])
    if len(jacobian_i) != residual_dimension:
        raise ValueError("jacobian row count must match residual length")
    if len(inverse_i) != coefficient_dimension or len(inverse_i[0]) != residual_dimension:
        raise ValueError(
            "approximate inverse must have shape coefficient_dimension x residual_dimension"
        )
    return {
        "residual_dimension": residual_dimension,
        "coefficient_dimension": coefficient_dimension,
        "backend": "native-c-outward-rounded-double-interval-summary",
        "Y0_infinity_norm_A_r": interval_matvec_inf_norm(inverse_i, residual_i),
        "Z0_infinity_norm_B": interval_left_matmul_identity_defect_inf_norm(inverse_i, jacobian_i),
    }
