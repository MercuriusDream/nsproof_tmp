#!/usr/bin/env python3
"""Pluecker/Evans-style diagnostic for the conical indicial pencil.

This is still a floating-point diagnostic, not a validator.  It makes the
rank-drop condition explicit: the two-dimensional analytic local space must
have a nonzero combination whose three forbidden far-field modal coefficients
vanish.  Equivalently, the 3x2 forbidden coefficient matrix must have rank
less than two, so all three 2x2 Pluecker minors vanish.

The existing ``indicial_match.py`` reports singular values for the same
forbidden matrix.  This tool adds a scan-oriented aggregate over one or more
far cutoffs L and prints the individual complex minors so candidate roots can
be checked for truncation stability.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from indicial_match import MatchReport, build_match_report, forbidden_matrix
from indicial_modes import format_complex


ComplexPair = tuple[complex, complex]
PlueckerVector = tuple[complex, complex, complex]


@dataclass(frozen=True)
class EvansMetrics:
    delta: complex
    L: float
    report: MatchReport
    matrix_norm: float
    minors: PlueckerVector
    minor_norm: float
    normalized_minor_norm: float
    sigma_ratio: float


@dataclass(frozen=True)
class ScanAggregate:
    delta: complex
    metrics: tuple[EvansMetrics, ...]

    @property
    def worst_normalized_minor_norm(self) -> float:
        return max(metric.normalized_minor_norm for metric in self.metrics)

    @property
    def worst_sigma_ratio(self) -> float:
        return max(metric.sigma_ratio for metric in self.metrics)

    @property
    def worst_contribution_forbidden_fraction(self) -> float:
        return max(metric.report.contribution_forbidden_fraction for metric in self.metrics)

    @property
    def worst_coefficient_forbidden_fraction(self) -> float:
        return max(metric.report.coefficient_forbidden_fraction for metric in self.metrics)

    @property
    def best_sigma_min(self) -> float:
        return min(metric.report.forbidden_singular_values[1] for metric in self.metrics)


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in raw.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one float")
    return values


def scan_values(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def pluecker_minors(rows: list[ComplexPair]) -> PlueckerVector:
    if len(rows) != 3:
        raise ValueError("expected exactly three forbidden rows")
    r0, r1, r2 = rows
    return (
        r0[0] * r1[1] - r1[0] * r0[1],
        r0[0] * r2[1] - r2[0] * r0[1],
        r1[0] * r2[1] - r2[0] * r1[1],
    )


def complex_vector_norm(values: tuple[complex, ...]) -> float:
    return math.sqrt(sum(abs(value) * abs(value) for value in values))


def forbidden_matrix_norm(rows: list[ComplexPair]) -> float:
    return math.sqrt(
        sum(abs(value) * abs(value) for row in rows for value in row)
    )


def evans_metrics(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L: float,
    steps: int,
    terms: int,
) -> EvansMetrics:
    report = build_match_report(
        delta=delta,
        gamma=gamma,
        B=B,
        eps=eps,
        L=L,
        steps=steps,
        terms=terms,
    )
    rows = forbidden_matrix(report.branches)
    minors = pluecker_minors(rows)
    matrix_norm = forbidden_matrix_norm(rows)
    minor_norm = complex_vector_norm(minors)
    sigma_max, sigma_min = report.forbidden_singular_values
    return EvansMetrics(
        delta=delta,
        L=L,
        report=report,
        matrix_norm=matrix_norm,
        minors=minors,
        minor_norm=minor_norm,
        normalized_minor_norm=minor_norm / (matrix_norm * matrix_norm + 1e-300),
        sigma_ratio=sigma_min / (sigma_max + 1e-300),
    )


def aggregate_metrics(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L_values: tuple[float, ...],
    steps_per_unit: float,
    min_steps: int,
    terms: int,
) -> ScanAggregate:
    metrics: list[EvansMetrics] = []
    for L in L_values:
        steps = max(min_steps, int(round(steps_per_unit * L)))
        metrics.append(
            evans_metrics(
                delta=delta,
                gamma=gamma,
                B=B,
                eps=eps,
                L=L,
                steps=steps,
                terms=terms,
            )
        )
    return ScanAggregate(delta=delta, metrics=tuple(metrics))


def print_point(aggregate: ScanAggregate) -> None:
    delta = aggregate.delta
    print(f"delta={delta.real:.12f}{delta.imag:+.12f}i")
    for metric in aggregate.metrics:
        report = metric.report
        sigma_max, sigma_min = report.forbidden_singular_values
        print(
            f"L={metric.L:.6g} "
            f"sigma_ratio={metric.sigma_ratio:.12e} "
            f"sigma_min={sigma_min:.12e} sigma_max={sigma_max:.12e} "
            f"minor_norm={metric.minor_norm:.12e} "
            f"normalized_minor_norm={metric.normalized_minor_norm:.12e} "
            f"coeff_forbid={report.coefficient_forbidden_fraction:.12e} "
            f"contrib_forbid={report.contribution_forbidden_fraction:.12e}"
        )
        labels = ("grow^w", "grow^ylog", "w^ylog")
        for label, minor in zip(labels, metric.minors):
            print(f"  minor {label} = {format_complex(minor)}")
        print(
            f"  best_combo=({format_complex(report.best_local_combo[0])}, "
            f"{format_complex(report.best_local_combo[1])})"
        )
    print(
        "aggregate "
        f"worst_normalized_minor_norm={aggregate.worst_normalized_minor_norm:.12e} "
        f"worst_sigma_ratio={aggregate.worst_sigma_ratio:.12e} "
        f"worst_coeff_forbid={aggregate.worst_coefficient_forbidden_fraction:.12e} "
        f"worst_contrib_forbid={aggregate.worst_contribution_forbidden_fraction:.12e}"
    )


def aggregate_sort_key(aggregate: ScanAggregate) -> tuple[float, float, float]:
    return (
        aggregate.worst_normalized_minor_norm,
        aggregate.worst_contribution_forbidden_fraction,
        aggregate.worst_sigma_ratio,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--eps", type=float, default=1e-4)
    parser.add_argument("--L-values", type=parse_float_list, default=(25.0, 40.0))
    parser.add_argument("--steps-per-unit", type=float, default=220.0)
    parser.add_argument("--min-steps", type=int, default=4000)
    parser.add_argument("--series-terms", type=int, default=12)
    parser.add_argument("--delta-real", type=float, default=1.0)
    parser.add_argument("--delta-imag", type=float, default=0.0)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--delta-min", type=float, default=0.02)
    parser.add_argument("--delta-max", type=float, default=1.0)
    parser.add_argument("--count", type=int, default=13)
    parser.add_argument("--imag-min", type=float, default=0.0)
    parser.add_argument("--imag-max", type=float, default=3.0)
    parser.add_argument("--imag-count", type=int, default=13)
    parser.add_argument("--top", type=int, default=16)
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2).")
    if any(L <= 1.0 for L in args.L_values):
        raise SystemExit("each L value must be larger than 1.")
    if args.steps_per_unit <= 0.0:
        raise SystemExit("--steps-per-unit must be positive")
    if args.min_steps <= 0:
        raise SystemExit("--min-steps must be positive")

    if not args.scan:
        print_point(
            aggregate_metrics(
                delta=complex(args.delta_real, args.delta_imag),
                gamma=args.gamma,
                B=args.B,
                eps=args.eps,
                L_values=args.L_values,
                steps_per_unit=args.steps_per_unit,
                min_steps=args.min_steps,
                terms=args.series_terms,
            )
        )
        return

    aggregates: list[ScanAggregate] = []
    for delta_real in scan_values(args.delta_min, args.delta_max, args.count):
        for delta_imag in scan_values(args.imag_min, args.imag_max, args.imag_count):
            delta = complex(delta_real, delta_imag)
            try:
                aggregate = aggregate_metrics(
                    delta=delta,
                    gamma=args.gamma,
                    B=args.B,
                    eps=args.eps,
                    L_values=args.L_values,
                    steps_per_unit=args.steps_per_unit,
                    min_steps=args.min_steps,
                    terms=args.series_terms,
                )
            except (OverflowError, ZeroDivisionError, ValueError) as exc:
                print(f"delta={delta.real:.8f}{delta.imag:+.8f}i failed: {exc}")
                continue
            aggregates.append(aggregate)
            print(
                f"delta={delta.real:.8f}{delta.imag:+.8f}i "
                f"worst_norm_minor={aggregate.worst_normalized_minor_norm:.6e} "
                f"worst_sigma_ratio={aggregate.worst_sigma_ratio:.6e} "
                f"best_sigma_min={aggregate.best_sigma_min:.6e} "
                f"coeff_forbid={aggregate.worst_coefficient_forbidden_fraction:.6e} "
                f"contrib_forbid={aggregate.worst_contribution_forbidden_fraction:.6e}"
            )

    print("\nBest candidates by normalized Pluecker minor and forbidden contribution:")
    for aggregate in sorted(aggregates, key=aggregate_sort_key)[: args.top]:
        delta = aggregate.delta
        print(
            f"  delta={delta.real:.10f}{delta.imag:+.10f}i "
            f"worst_norm_minor={aggregate.worst_normalized_minor_norm:.6e} "
            f"worst_sigma_ratio={aggregate.worst_sigma_ratio:.6e} "
            f"best_sigma_min={aggregate.best_sigma_min:.6e} "
            f"coeff_forbid={aggregate.worst_coefficient_forbidden_fraction:.6e} "
            f"contrib_forbid={aggregate.worst_contribution_forbidden_fraction:.6e}"
        )


if __name__ == "__main__":
    main()
