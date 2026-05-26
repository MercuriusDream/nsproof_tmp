#!/usr/bin/env python3
"""Sampled indicial Evans/Pluecker box-cover scaffold.

This is a deterministic floating-point diagnostic, not a validator.  Each
complex delta box is sampled at its center and corners only; reported lower
bounds are sample minima and are explicitly heuristic.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
for path in (str(TOOLS_DIR), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from validators.pluecker import ComplexBox, DualMinMax, complex_box_cover


EvansMetricsFn = Callable[..., object]


try:
    from indicial_evans import evans_metrics as _evans_metrics
    from indicial_evans import parse_float_list as _parse_float_list
except ImportError as exc:
    _EVANS_IMPORT_ERROR: ImportError | None = exc
    _evans_metrics: EvansMetricsFn | None = None
    _parse_float_list = None
else:
    _EVANS_IMPORT_ERROR = None


@dataclass(frozen=True)
class PointHeuristic:
    delta: complex
    normalized_pluecker_lbound: float
    forbidden_contribution_lbound: float


@dataclass(frozen=True)
class BoxHeuristic:
    index: int
    box: ComplexBox
    samples: int
    bounds: DualMinMax
    failed_samples: tuple[str, ...]

    @property
    def has_failures(self) -> bool:
        return bool(self.failed_samples)


def parse_float_list(raw: str) -> tuple[float, ...]:
    if _parse_float_list is not None:
        return _parse_float_list(raw)
    values = tuple(float(item.strip()) for item in raw.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one float")
    return values


def format_complex(value: complex) -> str:
    return f"{value.real:.12g}{value.imag:+.12g}i"


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("expected a positive float")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0:
        raise argparse.ArgumentTypeError("expected a nonnegative float")
    return parsed


def metric_attr(metric: object, name: str) -> float:
    value = getattr(metric, name)
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{name} is non-finite: {parsed!r}")
    return parsed


def contribution_forbidden_fraction(metric: object) -> float:
    report = getattr(metric, "report")
    parsed = float(getattr(report, "contribution_forbidden_fraction"))
    if not math.isfinite(parsed):
        raise ValueError(
            f"contribution_forbidden_fraction is non-finite: {parsed!r}"
        )
    return parsed


def evaluate_point(
    delta: complex,
    gamma: float,
    B: float,
    eps: float,
    L_values: tuple[float, ...],
    steps_per_unit: float,
    series_terms: int,
) -> PointHeuristic:
    if _evans_metrics is None:
        raise RuntimeError(
            "could not import tools/indicial_evans.py functions"
        ) from _EVANS_IMPORT_ERROR

    normalized_pluecker_values: list[float] = []
    forbidden_contribution_values: list[float] = []
    for L in L_values:
        steps = max(1, int(round(steps_per_unit * L)))
        metric = _evans_metrics(
            delta=delta,
            gamma=gamma,
            B=B,
            eps=eps,
            L=L,
            steps=steps,
            terms=series_terms,
        )
        normalized_pluecker_values.append(
            metric_attr(metric, "normalized_minor_norm")
        )
        forbidden_contribution_values.append(contribution_forbidden_fraction(metric))

    return PointHeuristic(
        delta=delta,
        normalized_pluecker_lbound=min(normalized_pluecker_values),
        forbidden_contribution_lbound=min(forbidden_contribution_values),
    )


def evaluate_box(
    index: int,
    box: ComplexBox,
    gamma: float,
    B: float,
    eps: float,
    L_values: tuple[float, ...],
    steps_per_unit: float,
    series_terms: int,
) -> BoxHeuristic:
    bounds = DualMinMax.empty()
    failed_samples: list[str] = []
    for delta in box.samples():
        try:
            heuristic = evaluate_point(
                delta=delta,
                gamma=gamma,
                B=B,
                eps=eps,
                L_values=L_values,
                steps_per_unit=steps_per_unit,
                series_terms=series_terms,
            )
        except (OverflowError, RuntimeError, ValueError, ZeroDivisionError) as exc:
            failed_samples.append(f"{format_complex(delta)}: {exc}")
            continue
        bounds.normalized_pluecker.add(
            heuristic.normalized_pluecker_lbound,
            heuristic.delta,
        )
        bounds.forbidden_contribution.add(
            heuristic.forbidden_contribution_lbound,
            heuristic.delta,
        )

    return BoxHeuristic(
        index=index,
        box=box,
        samples=bounds.count,
        bounds=bounds,
        failed_samples=tuple(failed_samples),
    )


def heuristic_status(report: BoxHeuristic, fail_threshold: float) -> str:
    if report.has_failures or report.samples == 0:
        return "HEURISTIC_EVALUATION_ERROR"
    if (
        report.bounds.normalized_pluecker.minimum < fail_threshold
        or report.bounds.forbidden_contribution.minimum < fail_threshold
    ):
        return "HEURISTIC_FAIL_BELOW_THRESHOLD"
    return "HEURISTIC_PASS_ABOVE_THRESHOLD"


def print_box(report: BoxHeuristic, fail_threshold: float) -> None:
    box = report.box
    status = heuristic_status(report, fail_threshold)
    print(
        f"box={report.index} status={status} label='HEURISTIC NOT VALIDATED' "
        f"real=[{box.real_min:.12g},{box.real_max:.12g}] "
        f"imag=[{box.imag_min:.12g},{box.imag_max:.12g}] "
        f"samples={report.samples}"
    )
    if report.samples:
        normalized = report.bounds.normalized_pluecker
        forbidden = report.bounds.forbidden_contribution
        print(
            "  sampled_lbound_normalized_pluecker="
            f"{normalized.minimum:.12e} at {format_complex(normalized.min_point or 0j)} "
            f"sampled_max={normalized.maximum:.12e}"
        )
        print(
            "  sampled_lbound_forbidden_contribution="
            f"{forbidden.minimum:.12e} at {format_complex(forbidden.min_point or 0j)} "
            f"sampled_max={forbidden.maximum:.12e}"
        )
    for failure in report.failed_samples:
        print(f"  sample_error {failure}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "HEURISTIC NOT VALIDATED sampled box-cover check for the indicial "
            "Evans/Pluecker diagnostic."
        )
    )
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--eps", type=positive_float, default=1e-4)
    parser.add_argument("--real-min", type=float, default=0.02)
    parser.add_argument("--real-max", type=float, default=1.0)
    parser.add_argument("--real-count", type=positive_int, default=1)
    parser.add_argument("--imag-min", type=float, default=0.0)
    parser.add_argument("--imag-max", type=float, default=3.0)
    parser.add_argument("--imag-count", type=positive_int, default=1)
    parser.add_argument("--L-values", type=parse_float_list, default=(25.0, 40.0))
    parser.add_argument("--steps-per-unit", type=positive_float, default=220.0)
    parser.add_argument("--series-terms", type=positive_int, default=12)
    parser.add_argument("--fail-threshold", type=nonnegative_float, default=1e-6)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.real_max < args.real_min:
        raise SystemExit("--real-max must be >= --real-min")
    if args.imag_max < args.imag_min:
        raise SystemExit("--imag-max must be >= --imag-min")
    if any(L <= 1.0 for L in args.L_values):
        raise SystemExit("each --L-values entry must be larger than 1")

    print("HEURISTIC NOT VALIDATED")
    print(
        f"gamma={args.gamma:.12g} B={args.B:.12g} eps={args.eps:.12g} "
        f"L_values={','.join(f'{L:.12g}' for L in args.L_values)} "
        f"steps_per_unit={args.steps_per_unit:.12g} "
        f"series_terms={args.series_terms} "
        f"fail_threshold={args.fail_threshold:.12e}"
    )

    failed_count = 0
    box_count = 0
    for index, box in enumerate(
        complex_box_cover(
            real_min=args.real_min,
            real_max=args.real_max,
            real_count=args.real_count,
            imag_min=args.imag_min,
            imag_max=args.imag_max,
            imag_count=args.imag_count,
        ),
        start=1,
    ):
        box_count = index
        report = evaluate_box(
            index=index,
            box=box,
            gamma=args.gamma,
            B=args.B,
            eps=args.eps,
            L_values=args.L_values,
            steps_per_unit=args.steps_per_unit,
            series_terms=args.series_terms,
        )
        print_box(report, args.fail_threshold)
        if heuristic_status(report, args.fail_threshold) != "HEURISTIC_PASS_ABOVE_THRESHOLD":
            failed_count += 1

    print(
        f"summary label='HEURISTIC NOT VALIDATED' boxes={box_count} "
        f"threshold_failures={failed_count}"
    )
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
