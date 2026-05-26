#!/usr/bin/env python3
"""Small Bernstein interval helpers for future chart bounds.

For a polynomial represented by Bernstein coefficients on a box/simplex, the
range is enclosed by the min/max of its coefficients.  This module records that
basic enclosure and subdivision machinery for proof infrastructure.  It is not
yet wired to the exact profile residual map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from validators.interval_backend import Interval
from validators.twochart_mortar_jacobian import native_c_library


@dataclass(frozen=True)
class BernsteinRange:
    lower: float
    upper: float
    coefficient_count: int

    @property
    def width(self) -> float:
        return self.upper - self.lower


def coefficient_range(coefficients: Iterable[float | Interval]) -> BernsteinRange:
    lower: float | None = None
    upper: float | None = None
    count = 0
    for raw in coefficients:
        if isinstance(raw, Interval):
            lo = raw.lo
            hi = raw.hi
        else:
            lo = float(raw)
            hi = float(raw)
        if lo > hi:
            raise ValueError(f"bad coefficient interval [{lo}, {hi}]")
        lower = lo if lower is None else min(lower, lo)
        upper = hi if upper is None else max(upper, hi)
        count += 1
    if lower is None or upper is None:
        raise ValueError("expected at least one Bernstein coefficient")
    return BernsteinRange(lower=lower, upper=upper, coefficient_count=count)


def de_casteljau_split_1d(coefficients: list[float], t: float = 0.5) -> tuple[list[float], list[float]]:
    """Split one-dimensional Bernstein coefficients at ``t``."""

    if not coefficients:
        raise ValueError("expected at least one coefficient")
    if not 0.0 <= t <= 1.0:
        raise ValueError("split parameter must be in [0,1]")
    levels = [list(map(float, coefficients))]
    while len(levels[-1]) > 1:
        prev = levels[-1]
        levels.append([(1.0 - t) * prev[i] + t * prev[i + 1] for i in range(len(prev) - 1)])
    left = [level[0] for level in levels]
    right = [level[-1] for level in reversed(levels)]
    return left, right


def bernstein_eval_1d(coefficients: list[float], t: float) -> float:
    if not coefficients:
        raise ValueError("expected at least one coefficient")
    if not 0.0 <= t <= 1.0:
        raise ValueError("evaluation parameter must be in [0,1]")
    work = list(map(float, coefficients))
    while len(work) > 1:
        work = [(1.0 - t) * work[i] + t * work[i + 1] for i in range(len(work) - 1)]
    return work[0]


def tensor_coefficient_range(coefficients: list[list[float | Interval]]) -> BernsteinRange:
    if not coefficients:
        raise ValueError("expected at least one coefficient row")
    width = len(coefficients[0])
    if width == 0:
        raise ValueError("coefficient rows must not be empty")
    flat: list[float | Interval] = []
    for row in coefficients:
        if len(row) != width:
            raise ValueError("tensor Bernstein rows must have stable width")
        flat.extend(row)
    return coefficient_range(flat)


def native_coefficient_ranges(polynomials: list[list[float | Interval]]) -> list[BernsteinRange]:
    if not polynomials:
        raise ValueError("expected at least one polynomial")
    offsets: list[int] = []
    counts: list[int] = []
    coeff_lo: list[float] = []
    coeff_hi: list[float] = []
    for polynomial in polynomials:
        if not polynomial:
            raise ValueError("polynomial coefficient list must not be empty")
        offsets.append(len(coeff_lo))
        counts.append(len(polynomial))
        for raw in polynomial:
            if isinstance(raw, Interval):
                lo = raw.lo
                hi = raw.hi
            else:
                lo = float(raw)
                hi = float(raw)
            if lo > hi:
                raise ValueError(f"bad coefficient interval [{lo}, {hi}]")
            coeff_lo.append(lo)
            coeff_hi.append(hi)

    import ctypes

    poly_count = len(polynomials)
    coeff_count = len(coeff_lo)
    int_array = ctypes.c_int * poly_count
    double_poly_array = ctypes.c_double * poly_count
    double_coeff_array = ctypes.c_double * coeff_count
    offsets_arr = int_array(*offsets)
    counts_arr = int_array(*counts)
    lo_arr = double_coeff_array(*coeff_lo)
    hi_arr = double_coeff_array(*coeff_hi)
    out_lo = double_poly_array()
    out_hi = double_poly_array()
    statuses = int_array()
    lib = native_c_library()
    rc = lib.nsproof_bernstein_range_batch(
        poly_count,
        offsets_arr,
        counts_arr,
        lo_arr,
        hi_arr,
        out_lo,
        out_hi,
        statuses,
    )
    if rc != 0:
        bad = sorted({int(statuses[index]) for index in range(poly_count) if int(statuses[index]) != 0})
        raise RuntimeError(f"native Bernstein range batch failed rc={rc} statuses={bad}")
    return [
        BernsteinRange(float(out_lo[index]), float(out_hi[index]), counts[index])
        for index in range(poly_count)
    ]


def manufactured_self_test() -> dict[str, object]:
    coeffs = [-1.0, -0.25, 0.5, 2.0]
    rng = coefficient_range(coeffs)
    left, right = de_casteljau_split_1d(coeffs, 0.5)
    samples = [bernstein_eval_1d(coeffs, t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    all_inside = all(rng.lower <= value <= rng.upper for value in samples)
    split_inside = all(
        rng.lower <= value <= rng.upper
        for value in left + right
    )
    tensor_rng = tensor_coefficient_range(
        [
            [Interval(-1.0, -0.9999999999999998), 0.25],
            [0.5, Interval(1.0, 1.0000000000000002)],
        ]
    )
    native_ranges = native_coefficient_ranges(
        [
            coeffs,
            [
                Interval(-1.0, -0.9999999999999998),
                0.25,
                0.5,
                Interval(1.0, 1.0000000000000002),
            ],
        ]
    )
    native_inside = (
        native_ranges[0].lower <= rng.lower
        and native_ranges[0].upper >= rng.upper
        and native_ranges[1].lower <= tensor_rng.lower
        and native_ranges[1].upper >= tensor_rng.upper
    )
    return {
        "pass": bool(
            all_inside
            and split_inside
            and tensor_rng.lower <= -1.0
            and tensor_rng.upper >= 1.0
            and native_inside
        ),
        "range": {**rng.__dict__, "width": rng.width},
        "left_split": left,
        "right_split": right,
        "sample_values": samples,
        "tensor_interval_range": {**tensor_rng.__dict__, "width": tensor_rng.width},
        "native_ranges": [
            {**item.__dict__, "width": item.width}
            for item in native_ranges
        ],
    }
