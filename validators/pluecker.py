"""Reusable helpers for sampled Pluecker box diagnostics.

This module intentionally performs no interval arithmetic.  It only provides
deterministic complex-box sampling and small min/max aggregators that can be
replaced by validated bounds later.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Iterator


PointValue = tuple[complex, float]


@dataclass(frozen=True)
class ComplexBox:
    """Closed rectangular box in the complex plane."""

    real_min: float
    real_max: float
    imag_min: float
    imag_max: float

    def __post_init__(self) -> None:
        if self.real_max < self.real_min:
            raise ValueError("real_max must be >= real_min")
        if self.imag_max < self.imag_min:
            raise ValueError("imag_max must be >= imag_min")

    @property
    def center(self) -> complex:
        return complex(
            0.5 * (self.real_min + self.real_max),
            0.5 * (self.imag_min + self.imag_max),
        )

    @property
    def corners(self) -> tuple[complex, complex, complex, complex]:
        return (
            complex(self.real_min, self.imag_min),
            complex(self.real_min, self.imag_max),
            complex(self.real_max, self.imag_min),
            complex(self.real_max, self.imag_max),
        )

    def samples(self) -> tuple[complex, ...]:
        """Return center followed by corners, with duplicates removed."""

        seen: set[complex] = set()
        points: list[complex] = []
        for point in (self.center, *self.corners):
            if point not in seen:
                seen.add(point)
                points.append(point)
        return tuple(points)


@dataclass
class MinMax:
    """Sampled scalar min/max with points attaining each value."""

    minimum: float = math.inf
    maximum: float = -math.inf
    min_point: complex | None = None
    max_point: complex | None = None
    count: int = 0

    def add(self, value: float, point: complex | None = None) -> None:
        if not math.isfinite(value):
            raise ValueError(f"non-finite sample value: {value!r}")
        self.count += 1
        if value < self.minimum:
            self.minimum = value
            self.min_point = point
        if value > self.maximum:
            self.maximum = value
            self.max_point = point

    def extend(self, values: Iterable[PointValue]) -> None:
        for point, value in values:
            self.add(value, point)


@dataclass
class DualMinMax:
    """Convenience aggregate for Pluecker and forbidden-contribution metrics."""

    normalized_pluecker: MinMax
    forbidden_contribution: MinMax

    @classmethod
    def empty(cls) -> "DualMinMax":
        return cls(normalized_pluecker=MinMax(), forbidden_contribution=MinMax())

    @property
    def count(self) -> int:
        return min(self.normalized_pluecker.count, self.forbidden_contribution.count)


def axis_boxes(start: float, stop: float, count: int) -> tuple[tuple[float, float], ...]:
    """Split a closed interval into ``count`` deterministic subintervals."""

    if count <= 0:
        raise ValueError("count must be positive")
    if stop < start:
        raise ValueError("stop must be >= start")
    if count == 1:
        return ((start, stop),)
    step = (stop - start) / count
    return tuple((start + i * step, start + (i + 1) * step) for i in range(count))


def complex_box_cover(
    real_min: float,
    real_max: float,
    real_count: int,
    imag_min: float,
    imag_max: float,
    imag_count: int,
) -> Iterator[ComplexBox]:
    """Yield a row-major rectangular cover in the complex plane."""

    real_boxes = axis_boxes(real_min, real_max, real_count)
    imag_boxes = axis_boxes(imag_min, imag_max, imag_count)
    for real_lo, real_hi in real_boxes:
        for imag_lo, imag_hi in imag_boxes:
            yield ComplexBox(real_lo, real_hi, imag_lo, imag_hi)
