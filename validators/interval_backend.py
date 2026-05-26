#!/usr/bin/env python3
"""C-backed outward-rounded double interval helpers.

This is a foundation layer for future exact residual and NK certificates.  It
is not a substitute for Arb/MPFI in the final theorem, but it gives the repo a
native batched interval API with explicit status codes and deterministic smoke
tests.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Iterable

from validators.twochart_mortar_jacobian import native_c_library


STATUS_OK = 0


@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError(f"bad interval [{self.lo}, {self.hi}]")


def _as_intervals(items: Iterable[Interval]) -> list[Interval]:
    out = list(items)
    if not out:
        raise ValueError("expected at least one interval")
    return out


def _arrays(items: list[Interval]) -> tuple[ctypes.Array[ctypes.c_double], ctypes.Array[ctypes.c_double]]:
    double_array = ctypes.c_double * len(items)
    return double_array(*[item.lo for item in items]), double_array(*[item.hi for item in items])


def _check_statuses(rc: int, statuses: ctypes.Array[ctypes.c_int], label: str) -> None:
    if rc == STATUS_OK:
        return
    bad = sorted({int(statuses[index]) for index in range(len(statuses)) if int(statuses[index]) != STATUS_OK})
    raise RuntimeError(f"{label} failed rc={rc} statuses={bad}")


def _binary_op(label: str, lhs: Iterable[Interval], rhs: Iterable[Interval]) -> list[Interval]:
    left = _as_intervals(lhs)
    right = _as_intervals(rhs)
    if len(left) != len(right):
        raise ValueError("interval batch length mismatch")
    count = len(left)
    left_lo, left_hi = _arrays(left)
    right_lo, right_hi = _arrays(right)
    double_array = ctypes.c_double * count
    int_array = ctypes.c_int * count
    out_lo = double_array()
    out_hi = double_array()
    statuses = int_array()
    lib = native_c_library()
    fn = getattr(lib, f"nsproof_interval_{label}_batch")
    rc = fn(count, left_lo, left_hi, right_lo, right_hi, out_lo, out_hi, statuses)
    _check_statuses(rc, statuses, f"interval_{label}")
    return [Interval(float(out_lo[index]), float(out_hi[index])) for index in range(count)]


def interval_add(lhs: Iterable[Interval], rhs: Iterable[Interval]) -> list[Interval]:
    return _binary_op("add", lhs, rhs)


def interval_sub(lhs: Iterable[Interval], rhs: Iterable[Interval]) -> list[Interval]:
    return _binary_op("sub", lhs, rhs)


def interval_mul(lhs: Iterable[Interval], rhs: Iterable[Interval]) -> list[Interval]:
    return _binary_op("mul", lhs, rhs)


def interval_recip(items: Iterable[Interval]) -> list[Interval]:
    values = _as_intervals(items)
    count = len(values)
    lo, hi = _arrays(values)
    double_array = ctypes.c_double * count
    int_array = ctypes.c_int * count
    out_lo = double_array()
    out_hi = double_array()
    statuses = int_array()
    lib = native_c_library()
    rc = lib.nsproof_interval_recip_batch(count, lo, hi, out_lo, out_hi, statuses)
    _check_statuses(rc, statuses, "interval_recip")
    return [Interval(float(out_lo[index]), float(out_hi[index])) for index in range(count)]


def interval_poly_eval(coeffs: list[float], points: Iterable[Interval]) -> list[Interval]:
    if not coeffs:
        raise ValueError("expected at least one polynomial coefficient")
    values = _as_intervals(points)
    point_count = len(values)
    coeff_count = len(coeffs)
    double_points = ctypes.c_double * point_count
    double_coeffs = ctypes.c_double * coeff_count
    int_array = ctypes.c_int * point_count
    x_lo = double_points(*[item.lo for item in values])
    x_hi = double_points(*[item.hi for item in values])
    c_values = double_coeffs(*[float(item) for item in coeffs])
    out_lo = double_points()
    out_hi = double_points()
    statuses = int_array()
    lib = native_c_library()
    rc = lib.nsproof_interval_poly_eval_batch(
        point_count,
        coeff_count,
        c_values,
        x_lo,
        x_hi,
        out_lo,
        out_hi,
        statuses,
    )
    _check_statuses(rc, statuses, "interval_poly_eval")
    return [Interval(float(out_lo[index]), float(out_hi[index])) for index in range(point_count)]

