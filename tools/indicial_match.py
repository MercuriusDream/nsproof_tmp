#!/usr/bin/env python3
"""Two-branch analytic Frobenius matching diagnostic for the indicial ODE.

The parity-restricted shot in ``indicial_solver.py`` uses the analytic branch
with ``phi(0)=0`` and ``chi(0)=1``.  The full analytic local space at
``zeta=0`` has two generic amplitudes, which may be taken as ``phi(0)`` and
``chi(0)``.  This tool integrates both branches, projects them onto the
leading far-field modal basis, and measures whether a linear combination can
annihilate the forbidden modes.

It is still floating-point diagnostics only.  Its purpose is to define the
finite-dimensional matching obstruction that a validated Evans determinant
would later enclose with interval or ball arithmetic.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from indicial_modes import (
    Vector,
    format_complex,
    leading_modal_basis,
    solve_complex_linear,
    vector_add,
    vector_norm,
)
from indicial_solver import Params, rk4_step


@dataclass(frozen=True)
class SeriesCoefficients:
    phi: list[complex]
    chi: list[complex]
    h: list[complex]


@dataclass(frozen=True)
class BranchReport:
    label: str
    local_amplitudes: tuple[complex, complex]
    endpoint: Vector
    modal_coefficients: Vector


@dataclass(frozen=True)
class MatchReport:
    branches: tuple[BranchReport, BranchReport]
    best_local_combo: tuple[complex, complex]
    best_modal_coefficients: Vector
    forbidden_singular_values: tuple[float, float]
    forbidden_plucker_norm: float
    coefficient_forbidden_fraction: float
    contribution_forbidden_fraction: float
    contribution_norms: Vector


def c_second(n: int, alpha: float, delta: complex) -> complex:
    return 1.5 * n + alpha * delta


def d_third(n: int, alpha: float, delta: complex) -> complex:
    return 1.5 * n + 1.5 + alpha * delta


def a_first(n: int, delta: complex) -> complex:
    return (
        n * (n - 1)
        - (3.0 - 2.0 * delta) * n
        + (3.0 - delta) * (1.0 - delta)
    )


def analytic_frobenius_coefficients(
    delta: complex,
    gamma: float,
    B: float,
    terms: int,
    phi0: complex,
    chi0: complex,
) -> SeriesCoefficients:
    """Return analytic coefficients for chosen ``phi(0)``, ``chi(0)``.

    The recurrence follows from

        phi = sum p_n zeta^n,
        chi = sum q_n zeta^n,
        h = sum r_n zeta^n.

    For generic parameters the regular analytic space is two-dimensional.
    The branch ``phi0=0, chi0=1`` is the parity branch used by the older
    scalar shooting tool.
    """

    if terms < 2:
        raise ValueError("terms must be >= 2")
    if abs(B) < 1e-14:
        raise ValueError("This recurrence assumes B != 0.")

    alpha = 0.5 - gamma
    phi = [0j for _ in range(terms + 1)]
    chi = [0j for _ in range(terms + 2)]
    h = [0j for _ in range(terms + 1)]
    phi[0] = phi0
    chi[0] = chi0

    for n in range(terms + 1):
        if n >= 1:
            phi[n] = c_second(n - 1, alpha, delta) * chi[n - 1] / (2.0 * B * n)
        denom = (n + 1) * (
            c_second(n + 1, alpha, delta) / (2.0 * B)
            + 2.0 * B / d_third(n, alpha, delta)
        )
        if abs(denom) < 1e-28:
            raise ZeroDivisionError("zero-resonance denominator in analytic recurrence")
        chi[n + 1] = -a_first(n, delta) * phi[n] / denom
        h[n] = -2.0 * B * (n + 1) * chi[n + 1] / d_third(n, alpha, delta)

    return SeriesCoefficients(phi=phi, chi=chi[: terms + 1], h=h)


def initial_state(coefficients: SeriesCoefficients, eps: float) -> Vector:
    phi = 0j
    phip = 0j
    chi = 0j
    h = 0j
    for n, coeff in enumerate(coefficients.phi):
        phi += coeff * eps**n
        if n:
            phip += n * coeff * eps ** (n - 1)
    for n, coeff in enumerate(coefficients.chi):
        chi += coeff * eps**n
    for n, coeff in enumerate(coefficients.h):
        h += coeff * eps**n
    return (phi, phip, chi, h)


def integrate_initial(
    initial: Vector,
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
) -> Vector:
    params = Params(gamma=gamma, B=B, delta=delta)
    y = initial
    zeta = eps
    dz = (L - eps) / steps
    for _ in range(steps):
        y = rk4_step(zeta, y, dz, params)
        zeta += dz
    return y


def scaled_endpoint(state: Vector, L: float) -> Vector:
    phi, phip, chi, h = state
    return (phi, L * phip, L * chi, L * L * h)


def modal_coefficients(endpoint: Vector, delta: complex, gamma: float, B: float, L: float) -> Vector:
    basis = leading_modal_basis(delta, gamma, B, L)
    matrix = [[basis.columns[col][row] for col in range(4)] for row in range(4)]
    return tuple(solve_complex_linear(matrix, list(endpoint)))  # type: ignore[return-value]


def branch_report(
    label: str,
    phi0: complex,
    chi0: complex,
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    terms: int,
) -> BranchReport:
    coeffs = analytic_frobenius_coefficients(delta, gamma, B, terms, phi0, chi0)
    endpoint = scaled_endpoint(
        integrate_initial(
            initial_state(coeffs, eps),
            delta=delta,
            gamma=gamma,
            B=B,
            eps=eps,
            L=L,
            steps=steps,
        ),
        L,
    )
    return BranchReport(
        label=label,
        local_amplitudes=(phi0, chi0),
        endpoint=endpoint,
        modal_coefficients=modal_coefficients(endpoint, delta, gamma, B, L),
    )


def forbidden_matrix(branches: tuple[BranchReport, BranchReport]) -> list[tuple[complex, complex]]:
    return [
        (branches[0].modal_coefficients[row], branches[1].modal_coefficients[row])
        for row in (1, 2, 3)
    ]


def singular_values_3x2(rows: list[tuple[complex, complex]]) -> tuple[float, float, tuple[complex, complex]]:
    a = sum(abs(row[0]) * abs(row[0]) for row in rows)
    d = sum(abs(row[1]) * abs(row[1]) for row in rows)
    b = sum(row[0].conjugate() * row[1] for row in rows)
    trace = a + d
    gap = math.sqrt(max(0.0, (a - d) * (a - d) + 4.0 * abs(b) * abs(b)))
    lambda_max = max(0.0, 0.5 * (trace + gap))
    lambda_min = max(0.0, 0.5 * (trace - gap))

    if abs(b) + abs(lambda_min - a) > 1e-28:
        v0 = b
        v1 = lambda_min - a
    elif a <= d:
        v0 = 1.0 + 0j
        v1 = 0j
    else:
        v0 = 0j
        v1 = 1.0 + 0j
    norm = math.sqrt(abs(v0) * abs(v0) + abs(v1) * abs(v1))
    if norm == 0.0:
        v0 = 1.0 + 0j
        v1 = 0j
        norm = 1.0
    return (math.sqrt(lambda_max), math.sqrt(lambda_min), (v0 / norm, v1 / norm))


def plucker_norm(rows: list[tuple[complex, complex]]) -> float:
    total = 0.0
    for i, row_i in enumerate(rows):
        for row_j in rows[i + 1 :]:
            minor = row_i[0] * row_j[1] - row_j[0] * row_i[1]
            total += abs(minor) * abs(minor)
    return math.sqrt(total)


def combine_coefficients(
    branches: tuple[BranchReport, BranchReport],
    combo: tuple[complex, complex],
) -> Vector:
    return tuple(
        combo[0] * branches[0].modal_coefficients[i]
        + combo[1] * branches[1].modal_coefficients[i]
        for i in range(4)
    )  # type: ignore[return-value]


def build_match_report(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    terms: int,
) -> MatchReport:
    branches = (
        branch_report("phi0", 1.0 + 0j, 0j, delta, gamma, B, eps, L, steps, terms),
        branch_report("chi0", 0j, 1.0 + 0j, delta, gamma, B, eps, L, steps, terms),
    )
    rows = forbidden_matrix(branches)
    sigma_max, sigma_min, combo = singular_values_3x2(rows)
    best_modal = combine_coefficients(branches, combo)
    coeff_total = math.sqrt(sum(abs(x) * abs(x) for x in best_modal))
    coeff_forbidden = math.sqrt(sum(abs(best_modal[i]) * abs(best_modal[i]) for i in (1, 2, 3)))

    basis = leading_modal_basis(delta, gamma, B, L)
    column_norms = tuple(vector_norm(column) for column in basis.columns)
    contribution_norms = tuple(
        abs(best_modal[i]) * column_norms[i] for i in range(4)
    )  # type: ignore[assignment]
    contribution_total = math.sqrt(sum(x * x for x in contribution_norms))
    contribution_forbidden = math.sqrt(sum(contribution_norms[i] * contribution_norms[i] for i in (1, 2, 3)))

    return MatchReport(
        branches=branches,
        best_local_combo=combo,
        best_modal_coefficients=best_modal,
        forbidden_singular_values=(sigma_max, sigma_min),
        forbidden_plucker_norm=plucker_norm(rows),
        coefficient_forbidden_fraction=coeff_forbidden / (coeff_total + 1e-30),
        contribution_forbidden_fraction=contribution_forbidden / (contribution_total + 1e-30),
        contribution_norms=contribution_norms,
    )


def print_report(report: MatchReport) -> None:
    for branch in report.branches:
        print(f"branch {branch.label}:")
        print(
            f"  local amplitudes phi0={format_complex(branch.local_amplitudes[0])} "
            f"chi0={format_complex(branch.local_amplitudes[1])}"
        )
        print("  modal coefficients:")
        for label, value in zip(
            ("admissible_s1", "growing_s2", "lambda_w", "lambda_ylog"),
            branch.modal_coefficients,
        ):
            print(f"    {label} = {format_complex(value)}")
    print("forbidden-mode matching:")
    print(f"  sigma_max = {report.forbidden_singular_values[0]:.12e}")
    print(f"  sigma_min = {report.forbidden_singular_values[1]:.12e}")
    ratio = report.forbidden_singular_values[1] / (report.forbidden_singular_values[0] + 1e-30)
    print(f"  sigma_min/sigma_max = {ratio:.12e}")
    print(f"  plucker_norm = {report.forbidden_plucker_norm:.12e}")
    print(
        f"  best local combo phi0_branch={format_complex(report.best_local_combo[0])} "
        f"chi0_branch={format_complex(report.best_local_combo[1])}"
    )
    print("  best-combo modal coefficients:")
    for label, value, contribution in zip(
        ("admissible_s1", "growing_s2", "lambda_w", "lambda_ylog"),
        report.best_modal_coefficients,
        report.contribution_norms,
    ):
        print(
            f"    {label} = {format_complex(value)} "
            f"contribution_norm={contribution:.12e}"
        )
    print(f"  coefficient forbidden fraction = {report.coefficient_forbidden_fraction:.12e}")
    print(f"  contribution forbidden fraction = {report.contribution_forbidden_fraction:.12e}")


def scan_values(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--eps", type=float, default=1e-4)
    parser.add_argument("--L", type=float, default=40.0)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--series-terms", type=int, default=12)
    parser.add_argument("--delta-real", type=float, default=0.1)
    parser.add_argument("--delta-imag", type=float, default=1.79)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--delta-min", type=float, default=0.02)
    parser.add_argument("--delta-max", type=float, default=1.0)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--imag-min", type=float, default=0.0)
    parser.add_argument("--imag-max", type=float, default=3.0)
    parser.add_argument("--imag-count", type=int, default=13)
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2).")
    if args.L <= 1.0:
        raise SystemExit("L must be larger than 1 for far-field matching.")

    if args.scan:
        scored = []
        for delta_real in scan_values(args.delta_min, args.delta_max, args.count):
            for delta_imag in scan_values(args.imag_min, args.imag_max, args.imag_count):
                delta = complex(delta_real, delta_imag)
                try:
                    report = build_match_report(
                        delta=delta,
                        gamma=args.gamma,
                        B=args.B,
                        eps=args.eps,
                        L=args.L,
                        steps=args.steps,
                        terms=args.series_terms,
                    )
                except (OverflowError, ZeroDivisionError, ValueError) as exc:
                    print(
                        f"delta={delta.real:.8f}{delta.imag:+.8f}i failed: {exc}"
                    )
                    continue
                sigma_max, sigma_min = report.forbidden_singular_values
                sigma_ratio = sigma_min / (sigma_max + 1e-30)
                scored.append(
                    (
                        sigma_ratio,
                        sigma_min,
                        report.coefficient_forbidden_fraction,
                        report.contribution_forbidden_fraction,
                        delta,
                    )
                )
                print(
                    f"delta={delta.real:.8f}{delta.imag:+.8f}i "
                    f"sigma_ratio={sigma_ratio:.6e} "
                    f"sigma_min={sigma_min:.6e} "
                    f"coeff_forbid={report.coefficient_forbidden_fraction:.6e} "
                    f"contrib_forbid={report.contribution_forbidden_fraction:.6e}"
                )
        print("\nBest candidates by sigma_min/sigma_max:")
        for sigma_ratio, sigma_min, coeff_forbid, contrib_forbid, delta in sorted(scored)[: args.top]:
            print(
                f"  delta={delta.real:.10f}{delta.imag:+.10f}i "
                f"sigma_ratio={sigma_ratio:.6e} "
                f"sigma_min={sigma_min:.6e} "
                f"coeff_forbid={coeff_forbid:.6e} "
                f"contrib_forbid={contrib_forbid:.6e}"
            )
    else:
        delta = complex(args.delta_real, args.delta_imag)
        print(
            f"gamma={args.gamma} B={args.B} "
            f"delta={delta.real:.12f}{delta.imag:+.12f}i "
            f"eps={args.eps:.3e} L={args.L:.6g} steps={args.steps} terms={args.series_terms}"
        )
        print_report(
            build_match_report(
                delta=delta,
                gamma=args.gamma,
                B=args.B,
                eps=args.eps,
                L=args.L,
                steps=args.steps,
                terms=args.series_terms,
            )
        )


if __name__ == "__main__":
    main()
