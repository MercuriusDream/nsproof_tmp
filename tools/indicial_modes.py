#!/usr/bin/env python3
"""Far-field modal diagnostic for the conical-core indicial shot.

This tool is deliberately a diagnostic, not a validator.  It integrates the
regular Frobenius-normalized solution to ``zeta=L`` and decomposes the scaled
endpoint

    V = (phi, zeta phi', zeta chi, zeta^2 h)

against the leading constant-coefficient large-zeta modes.  A valid indicial
determinant should suppress the non-admissible channels; finite-cutoff scalar
residual minimization alone does not enforce that splitting.
"""

from __future__ import annotations

import argparse
import cmath
import math
from dataclasses import dataclass

from indicial_solver import integrate


Vector = tuple[complex, complex, complex, complex]
Matrix = list[list[complex]]


@dataclass(frozen=True)
class ModalBasis:
    s_admissible: complex
    s_growing: complex
    lambda_jordan: complex
    jordan_coupling: complex
    columns: tuple[Vector, Vector, Vector, Vector]


@dataclass(frozen=True)
class ModalReport:
    endpoint: Vector
    basis: ModalBasis
    coefficients: Vector
    reconstruction_error: float
    endpoint_norm: float
    column_norms: tuple[float, float, float, float]
    contribution_norms: tuple[float, float, float, float]

    @property
    def non_admissible_fraction(self) -> float:
        if self.endpoint_norm == 0.0:
            return math.inf
        tail = math.sqrt(sum(x * x for x in self.contribution_norms[1:]))
        return tail / self.endpoint_norm

    @property
    def admissible_fraction(self) -> float:
        if self.endpoint_norm == 0.0:
            return math.inf
        return self.contribution_norms[0] / self.endpoint_norm


def vector_norm(v: Vector) -> float:
    return math.sqrt(sum(abs(x) * abs(x) for x in v))


def vector_add(a: Vector, b: Vector, scale: complex = 1.0) -> Vector:
    return tuple(x + scale * y for x, y in zip(a, b))  # type: ignore[return-value]


def vector_scale(a: Vector, scale: complex) -> Vector:
    return tuple(scale * x for x in a)  # type: ignore[return-value]


def power(base: float, exponent: complex) -> complex:
    return cmath.exp(exponent * math.log(base))


def solve_complex_linear(a: Matrix, b: list[complex]) -> list[complex]:
    """Solve a small dense complex system by Gaussian elimination."""

    n = len(b)
    if len(a) != n or any(len(row) != n for row in a):
        raise ValueError("linear system must be square")
    mat = [row[:] + [rhs] for row, rhs in zip(a, b)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(mat[row][col]))
        if abs(mat[pivot][col]) < 1e-28:
            raise ZeroDivisionError("singular modal basis at this cutoff")
        if pivot != col:
            mat[col], mat[pivot] = mat[pivot], mat[col]
        pivot_value = mat[col][col]
        for j in range(col, n + 1):
            mat[col][j] /= pivot_value
        for row in range(n):
            if row == col:
                continue
            factor = mat[row][col]
            if factor == 0:
                continue
            for j in range(col, n + 1):
                mat[row][j] -= factor * mat[col][j]

    return [mat[i][n] for i in range(n)]


def scaled_endpoint(state: Vector, L: float) -> Vector:
    phi, phip, chi, h = state
    return (phi, L * phip, L * chi, L * L * h)


def eigen_vector_for_s(s: complex, lambda_jordan: complex, delta: complex, B: float, alpha: float) -> Vector:
    denom = s - lambda_jordan
    if abs(denom) < 1e-14:
        raise ZeroDivisionError("phi-mode exponent resonates with Jordan exponent")
    y_component = ((4.0 * B / 3.0) * s) / denom
    w_component = (
        (-(16.0 * B * B / 9.0) * s)
        + ((8.0 * B * alpha * delta / 9.0) * y_component)
    ) / denom
    return (1.0 + 0j, s, y_component, w_component)


def leading_modal_basis(delta: complex, gamma: float, B: float, L: float) -> ModalBasis:
    alpha = 0.5 - gamma
    s_admissible = 1.0 - delta
    s_growing = 3.0 - delta
    lambda_jordan = 1.0 - (2.0 / 3.0) * alpha * delta
    jordan_coupling = (8.0 * B * alpha * delta) / 9.0

    v_adm = eigen_vector_for_s(s_admissible, lambda_jordan, delta, B, alpha)
    v_grow = eigen_vector_for_s(s_growing, lambda_jordan, delta, B, alpha)
    v_w: Vector = (0j, 0j, 0j, 1.0 + 0j)
    v_ylog: Vector = (0j, 0j, 1.0 + 0j, jordan_coupling * math.log(L))

    columns = (
        vector_scale(v_adm, power(L, s_admissible)),
        vector_scale(v_grow, power(L, s_growing)),
        vector_scale(v_w, power(L, lambda_jordan)),
        vector_scale(v_ylog, power(L, lambda_jordan)),
    )
    return ModalBasis(
        s_admissible=s_admissible,
        s_growing=s_growing,
        lambda_jordan=lambda_jordan,
        jordan_coupling=jordan_coupling,
        columns=columns,
    )


def decompose_endpoint(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    series_terms: int,
) -> ModalReport:
    state = integrate(delta, gamma, B, eps, L, steps, series_terms)
    endpoint = scaled_endpoint(state, L)
    basis = leading_modal_basis(delta, gamma, B, L)
    matrix = [[basis.columns[col][row] for col in range(4)] for row in range(4)]
    coefficients = tuple(solve_complex_linear(matrix, list(endpoint)))  # type: ignore[assignment]
    reconstructed = (0j, 0j, 0j, 0j)
    for coefficient, column in zip(coefficients, basis.columns):
        reconstructed = vector_add(reconstructed, column, coefficient)
    reconstruction_error = vector_norm(vector_add(endpoint, reconstructed, -1.0)) / (
        vector_norm(endpoint) + 1e-30
    )
    column_norms = tuple(vector_norm(column) for column in basis.columns)
    contribution_norms = tuple(abs(c) * n for c, n in zip(coefficients, column_norms))
    return ModalReport(
        endpoint=endpoint,
        basis=basis,
        coefficients=coefficients,
        reconstruction_error=reconstruction_error,
        endpoint_norm=vector_norm(endpoint),
        column_norms=column_norms,
        contribution_norms=contribution_norms,
    )


def format_complex(z: complex) -> str:
    return f"{z.real:.12e}{z.imag:+.12e}i"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--eps", type=float, default=1e-4)
    parser.add_argument("--L", type=float, default=40.0)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--series-terms", type=int, default=6)
    parser.add_argument("--delta-real", type=float, default=0.1)
    parser.add_argument("--delta-imag", type=float, default=1.79)
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2).")
    if args.L <= 1.0:
        raise SystemExit("L must be larger than 1 for a far-field modal split.")

    delta = complex(args.delta_real, args.delta_imag)
    report = decompose_endpoint(
        delta=delta,
        gamma=args.gamma,
        B=args.B,
        eps=args.eps,
        L=args.L,
        steps=args.steps,
        series_terms=args.series_terms,
    )

    print(
        f"gamma={args.gamma} B={args.B} "
        f"delta={delta.real:.12f}{delta.imag:+.12f}i "
        f"eps={args.eps:.3e} L={args.L:.6g} steps={args.steps} terms={args.series_terms}"
    )
    print("leading exponents:")
    print(f"  s_admissible = {format_complex(report.basis.s_admissible)}")
    print(f"  s_growing    = {format_complex(report.basis.s_growing)}")
    print(f"  lambda       = {format_complex(report.basis.lambda_jordan)}")
    print(f"  jordan c     = {format_complex(report.basis.jordan_coupling)}")
    print("scaled endpoint V=(phi,L phi',L chi,L^2 h):")
    for label, value in zip(("phi", "p", "y", "w"), report.endpoint):
        print(f"  {label} = {format_complex(value)}")
    print(f"endpoint norm = {report.endpoint_norm:.12e}")
    print("modal coefficients and endpoint-scale contributions:")
    labels = ("admissible_s1", "growing_s2", "lambda_w", "lambda_ylog")
    for label, coeff, column_norm, contribution in zip(
        labels,
        report.coefficients,
        report.column_norms,
        report.contribution_norms,
    ):
        rel = contribution / (report.endpoint_norm + 1e-30)
        print(
            f"  {label}: coeff={format_complex(coeff)} "
            f"column_norm={column_norm:.12e} contribution={contribution:.12e} "
            f"rel={rel:.12e}"
        )
    print(f"admissible contribution fraction     = {report.admissible_fraction:.12e}")
    print(f"non-admissible contribution fraction = {report.non_admissible_fraction:.12e}")
    print(f"modal reconstruction relative error  = {report.reconstruction_error:.12e}")


if __name__ == "__main__":
    main()
