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
    return {
        "pass": bool(all_inside and split_inside and tensor_rng.lower <= -1.0 and tensor_rng.upper >= 1.0),
        "range": {**rng.__dict__, "width": rng.width},
        "left_split": left,
        "right_split": right,
        "sample_values": samples,
        "tensor_interval_range": {**tensor_rng.__dict__, "width": tensor_rng.width},
    }
