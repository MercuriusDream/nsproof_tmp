#!/usr/bin/env python3
"""Validate native interval finite-block linear algebra kernels."""

from __future__ import annotations

import argparse
import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.interval_backend import (  # noqa: E402
    Interval,
    interval_matrix_inf_norm,
    interval_matvec,
    interval_vector_inf_norm,
)


def manufactured_matrix() -> list[list[Interval]]:
    return [
        [Interval(1.0, 1.0000000000000002), Interval(-0.25, -0.24999999999999994)],
        [Interval(0.125, 0.12500000000000003), Interval(0.5, 0.5000000000000001)],
    ]


def manufactured_vector() -> list[Interval]:
    return [
        Interval(0.1, 0.10000000000000002),
        Interval(-0.2, -0.19999999999999996),
    ]


def validate() -> dict[str, float | int]:
    matrix = manufactured_matrix()
    vector = manufactured_vector()
    product = interval_matvec(matrix, vector)
    vector_norm = interval_vector_inf_norm(product)
    matrix_norm = interval_matrix_inf_norm(matrix)
    if not (product[0].lo <= 0.15 <= product[0].hi):
        raise AssertionError(f"first product interval does not contain 0.15: {product[0]}")
    if not (product[1].lo <= -0.0875 <= product[1].hi):
        raise AssertionError(f"second product interval does not contain -0.0875: {product[1]}")
    if vector_norm < 0.15:
        raise AssertionError(f"vector inf norm bound is too small: {vector_norm}")
    if matrix_norm < 1.25:
        raise AssertionError(f"matrix inf norm bound is too small: {matrix_norm}")
    return {
        "rows": len(matrix),
        "columns": len(matrix[0]),
        "product_inf_norm": vector_norm,
        "matrix_inf_norm": matrix_norm,
    }


def benchmark(repeats: int) -> float:
    matrix = manufactured_matrix()
    vector = manufactured_vector()
    start = time.perf_counter()
    for _ in range(repeats):
        interval_matvec(matrix, vector)
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1000)
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    report = validate()
    elapsed = benchmark(args.repeats)
    print("native interval linalg validation: ok")
    print(
        f"shape={report['rows']}x{report['columns']} "
        f"product_inf_norm={report['product_inf_norm']:.17g} "
        f"matrix_inf_norm={report['matrix_inf_norm']:.17g}"
    )
    print(f"benchmark: matvec repeats={args.repeats} elapsed={elapsed:.6f}s")


if __name__ == "__main__":
    main()

