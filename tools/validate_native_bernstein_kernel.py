#!/usr/bin/env python3
"""Validate the native Bernstein coefficient-hull range batch ABI."""

from __future__ import annotations

import argparse
import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.bernstein_ball import Interval, coefficient_range, native_coefficient_ranges


def deterministic_cases() -> list[list[float | Interval]]:
    return [
        [-1.0, -0.25, 0.5, 2.0],
        [
            Interval(-1.0, -0.9999999999999998),
            0.25,
            0.5,
            Interval(1.0, 1.0000000000000002),
        ],
        [0.0, 0.125, -0.5, 0.75, -1.25, 1.5],
    ]


def validate() -> dict[str, float | int]:
    cases = deterministic_cases()
    expected = [coefficient_range(case) for case in cases]
    got = native_coefficient_ranges(cases)
    max_extra_width = 0.0
    for index, (lhs, rhs) in enumerate(zip(got, expected)):
        if lhs.lower > rhs.lower or lhs.upper < rhs.upper:
            raise AssertionError(
                f"case {index} native range [{lhs.lower}, {lhs.upper}] "
                f"does not contain expected [{rhs.lower}, {rhs.upper}]"
            )
        max_extra_width = max(max_extra_width, lhs.width - rhs.width)
    return {
        "cases": len(cases),
        "coefficients": sum(len(case) for case in cases),
        "max_extra_width": max_extra_width,
        "max_width": max(item.width for item in got),
    }


def benchmark(repeats: int) -> float:
    cases = deterministic_cases()
    start = time.perf_counter()
    for _ in range(repeats):
        native_coefficient_ranges(cases)
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1000)
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    report = validate()
    elapsed = benchmark(args.repeats)
    print("native Bernstein range validation: ok")
    print(
        "cases={cases} coefficients={coefficients} max_width={max_width:.17g} "
        "max_extra_width={max_extra_width:.17g}".format(**report)
    )
    print(f"benchmark: repeats={args.repeats} elapsed={elapsed:.6f}s")


if __name__ == "__main__":
    main()
