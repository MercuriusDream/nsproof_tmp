#!/usr/bin/env python3
"""Validate and lightly benchmark C-backed interval arithmetic kernels.

Expected C ABI:

    int nsproof_interval_add_batch(int count,
        const double *a_lo, const double *a_hi,
        const double *b_lo, const double *b_hi,
        double *out_lo, double *out_hi,
        int *statuses);

    int nsproof_interval_mul_batch(int count,
        const double *a_lo, const double *a_hi,
        const double *b_lo, const double *b_hi,
        double *out_lo, double *out_hi,
        int *statuses);

    int nsproof_interval_recip_batch(int count,
        const double *a_lo, const double *a_hi,
        double *out_lo, double *out_hi,
        int *statuses);

    int nsproof_interval_poly_eval_batch(int point_count, int coeff_count,
        const double *coeffs,
        const double *x_lo, const double *x_hi,
        double *out_lo, double *out_hi,
        int *statuses);

The tool loads the shared library through validators.twochart_mortar_jacobian
so it uses the same native C build path as the solver-side validators.
"""

from __future__ import annotations

import argparse
import ctypes
import math
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.twochart_mortar_jacobian import native_c_library  # noqa: E402


getcontext().prec = 80

OK = 0
REQUIRED_SYMBOLS = (
    "nsproof_interval_add_batch",
    "nsproof_interval_mul_batch",
    "nsproof_interval_recip_batch",
    "nsproof_interval_poly_eval_batch",
)


@dataclass(frozen=True)
class Interval:
    lo: Decimal
    hi: Decimal


def dec(value: str) -> Decimal:
    return Decimal(value)


def interval(lo: str, hi: str) -> Interval:
    return Interval(dec(lo), dec(hi))


def from_float_interval(lo: float, hi: float) -> Interval:
    return Interval(Decimal.from_float(lo), Decimal.from_float(hi))


def width(lo: float, hi: float) -> float:
    return hi - lo


def contains(got_lo: float, got_hi: float, expected: Interval) -> bool:
    if not (math.isfinite(got_lo) and math.isfinite(got_hi) and got_lo <= got_hi):
        return False
    got = from_float_interval(got_lo, got_hi)
    return got.lo <= expected.lo and expected.hi <= got.hi


def add_ref(a: Interval, b: Interval) -> Interval:
    return Interval(a.lo + b.lo, a.hi + b.hi)


def mul_ref(a: Interval, b: Interval) -> Interval:
    values = (a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi)
    return Interval(min(values), max(values))


def recip_ref(a: Interval) -> Interval:
    if a.lo <= 0 <= a.hi:
        raise ValueError(f"reciprocal interval crosses zero: {a}")
    values = (Decimal(1) / a.lo, Decimal(1) / a.hi)
    return Interval(min(values), max(values))


def poly_eval_ref(coeffs: list[Decimal], x: Interval) -> Interval:
    out = Interval(coeffs[-1], coeffs[-1])
    for coeff in reversed(coeffs[:-1]):
        out = add_ref(mul_ref(out, x), Interval(coeff, coeff))
    return out


def double_array(values: list[float]) -> ctypes.Array[ctypes.c_double]:
    return (ctypes.c_double * len(values))(*values)


def configure_interval_symbols(lib: ctypes.CDLL) -> None:
    missing = [name for name in REQUIRED_SYMBOLS if not hasattr(lib, name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "native interval symbols are not exported yet: "
            f"{joined}. Expected names: {', '.join(REQUIRED_SYMBOLS)}"
        )

    double_p = ctypes.POINTER(ctypes.c_double)
    for name in ("nsproof_interval_add_batch", "nsproof_interval_mul_batch"):
        fn = getattr(lib, name)
        fn.argtypes = [
            ctypes.c_int,
            double_p,
            double_p,
            double_p,
            double_p,
            double_p,
            double_p,
            ctypes.POINTER(ctypes.c_int),
        ]
        fn.restype = ctypes.c_int

    lib.nsproof_interval_recip_batch.argtypes = [
        ctypes.c_int,
        double_p,
        double_p,
        double_p,
        double_p,
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_recip_batch.restype = ctypes.c_int

    lib.nsproof_interval_poly_eval_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        double_p,
        double_p,
        double_p,
        double_p,
        double_p,
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_poly_eval_batch.restype = ctypes.c_int


def assert_status(status: int, label: str) -> None:
    if status != OK:
        raise RuntimeError(f"{label} returned status {status}, expected {OK}")


def validate_binary(
    lib: ctypes.CDLL,
    symbol: str,
    cases: list[tuple[Interval, Interval]],
    refs: list[Interval],
) -> tuple[int, float]:
    count = len(cases)
    a_lo = double_array([float(a.lo) for a, _ in cases])
    a_hi = double_array([float(a.hi) for a, _ in cases])
    b_lo = double_array([float(b.lo) for _, b in cases])
    b_hi = double_array([float(b.hi) for _, b in cases])
    out_lo = (ctypes.c_double * count)()
    out_hi = (ctypes.c_double * count)()
    statuses = (ctypes.c_int * count)()

    status = getattr(lib, symbol)(count, a_lo, a_hi, b_lo, b_hi, out_lo, out_hi, statuses)
    assert_status(status, symbol)

    max_width = 0.0
    for idx, expected in enumerate(refs):
        assert_status(statuses[idx], f"{symbol}[{idx}]")
        if not contains(out_lo[idx], out_hi[idx], expected):
            raise AssertionError(
                f"{symbol}[{idx}] does not contain Decimal reference: "
                f"got [{out_lo[idx]}, {out_hi[idx]}], "
                f"expected [{expected.lo}, {expected.hi}]"
            )
        max_width = max(max_width, width(out_lo[idx], out_hi[idx]))
    return count, max_width


def validate_recip(lib: ctypes.CDLL, cases: list[Interval]) -> tuple[int, float]:
    count = len(cases)
    a_lo = double_array([float(a.lo) for a in cases])
    a_hi = double_array([float(a.hi) for a in cases])
    out_lo = (ctypes.c_double * count)()
    out_hi = (ctypes.c_double * count)()
    statuses = (ctypes.c_int * count)()

    status = lib.nsproof_interval_recip_batch(count, a_lo, a_hi, out_lo, out_hi, statuses)
    assert_status(status, "nsproof_interval_recip_batch")

    max_width = 0.0
    for idx, case in enumerate(cases):
        assert_status(statuses[idx], f"nsproof_interval_recip_batch[{idx}]")
        expected = recip_ref(case)
        if not contains(out_lo[idx], out_hi[idx], expected):
            raise AssertionError(
                f"nsproof_interval_recip_batch[{idx}] does not contain Decimal reference: "
                f"got [{out_lo[idx]}, {out_hi[idx]}], "
                f"expected [{expected.lo}, {expected.hi}]"
            )
        max_width = max(max_width, width(out_lo[idx], out_hi[idx]))
    return count, max_width


def validate_poly(lib: ctypes.CDLL) -> tuple[int, float]:
    coeffs = [dec("-0.125"), dec("0.5"), dec("-1.25"), dec("0.03125")]
    cases = [
        interval("-0.75", "-0.7499999999999999"),
        interval("-0.125", "-0.12499999999999998"),
        interval("0.25", "0.25000000000000006"),
        interval("0.875", "0.8750000000000001"),
    ]
    count = len(cases)
    coeff_count = len(coeffs)
    coeff_arr = double_array([float(c) for c in coeffs])
    x_lo = double_array([float(x.lo) for x in cases])
    x_hi = double_array([float(x.hi) for x in cases])
    out_lo = (ctypes.c_double * count)()
    out_hi = (ctypes.c_double * count)()
    statuses = (ctypes.c_int * count)()

    status = lib.nsproof_interval_poly_eval_batch(
        count,
        coeff_count,
        coeff_arr,
        x_lo,
        x_hi,
        out_lo,
        out_hi,
        statuses,
    )
    assert_status(status, "nsproof_interval_poly_eval_batch")

    max_width = 0.0
    for idx, x in enumerate(cases):
        assert_status(statuses[idx], f"nsproof_interval_poly_eval_batch[{idx}]")
        expected = poly_eval_ref(coeffs, x)
        if not contains(out_lo[idx], out_hi[idx], expected):
            raise AssertionError(
                f"nsproof_interval_poly_eval_batch[{idx}] does not contain Decimal reference: "
                f"got [{out_lo[idx]}, {out_hi[idx]}], "
                f"expected [{expected.lo}, {expected.hi}]"
            )
        max_width = max(max_width, width(out_lo[idx], out_hi[idx]))
    return count, max_width


def benchmark(lib: ctypes.CDLL, repeats: int) -> float:
    cases = [
        (interval("-1.0", "-0.9999999999999998"), interval("0.25", "0.25000000000000006")),
        (interval("-0.125", "0.5"), interval("-2.0", "-1.9999999999999998")),
        (interval("1.0", "1.0000000000000002"), interval("3.0", "3.0000000000000004")),
        (interval("-0.75", "-0.25"), interval("-0.5", "0.125")),
    ]
    count = len(cases)
    a_lo = double_array([float(a.lo) for a, _ in cases])
    a_hi = double_array([float(a.hi) for a, _ in cases])
    b_lo = double_array([float(b.lo) for _, b in cases])
    b_hi = double_array([float(b.hi) for _, b in cases])
    out_lo = (ctypes.c_double * count)()
    out_hi = (ctypes.c_double * count)()
    statuses = (ctypes.c_int * count)()

    start = time.perf_counter()
    for _ in range(repeats):
        status = lib.nsproof_interval_mul_batch(count, a_lo, a_hi, b_lo, b_hi, out_lo, out_hi, statuses)
        if status != OK:
            raise RuntimeError(f"benchmark mul batch returned status {status}")
    elapsed = time.perf_counter() - start
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=1000, help="tiny benchmark repeat count")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")

    lib = native_c_library()
    configure_interval_symbols(lib)

    binary_cases = [
        (interval("-1.0", "-0.9999999999999998"), interval("0.25", "0.25000000000000006")),
        (interval("-0.125", "0.5"), interval("-2.0", "-1.9999999999999998")),
        (interval("1.0", "1.0000000000000002"), interval("3.0", "3.0000000000000004")),
        (interval("-0.75", "-0.25"), interval("-0.5", "0.125")),
    ]
    recip_cases = [
        interval("0.25", "0.25000000000000006"),
        interval("2.0", "2.0000000000000004"),
        interval("-4.0", "-3.999999999999999"),
    ]

    add_count, add_width = validate_binary(
        lib,
        "nsproof_interval_add_batch",
        binary_cases,
        [add_ref(a, b) for a, b in binary_cases],
    )
    mul_count, mul_width = validate_binary(
        lib,
        "nsproof_interval_mul_batch",
        binary_cases,
        [mul_ref(a, b) for a, b in binary_cases],
    )
    recip_count, recip_width = validate_recip(lib, recip_cases)
    poly_count, poly_width = validate_poly(lib)
    elapsed = benchmark(lib, args.repeats)

    total_cases = add_count + mul_count + recip_count + poly_count
    max_width = max(add_width, mul_width, recip_width, poly_width)
    print("interval kernel validation: ok")
    print(
        "case counts: "
        f"add={add_count} mul={mul_count} recip={recip_count} poly={poly_count} total={total_cases}"
    )
    print(
        "max widths: "
        f"add={add_width:.17g} mul={mul_width:.17g} "
        f"recip={recip_width:.17g} poly={poly_width:.17g} overall={max_width:.17g}"
    )
    print(f"benchmark: mul_batch count=4 repeats={args.repeats} elapsed={elapsed:.6f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
