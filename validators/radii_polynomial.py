#!/usr/bin/env python3
"""Radii-polynomial helper for Newton-Kantorovich certificates.

This module is intentionally small and backend-agnostic.  It does not compute
the profile bounds ``Y0``, ``Z0`` or ``Z2``; it only checks the scalar
radii-polynomial inequality once an interval backend has produced those
outward-rounded bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any


DEFAULT_PRECISION = 80


@dataclass(frozen=True)
class RadiiBounds:
    Y0: Decimal
    Z0: Decimal
    Z2: Decimal


@dataclass(frozen=True)
class RadiusInterval:
    lower: Decimal
    upper: Decimal


def decimal_from(value: str | float | int | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def parse_bounds(Y0: str | float, Z0: str | float, Z2: str | float) -> RadiiBounds:
    bounds = RadiiBounds(decimal_from(Y0), decimal_from(Z0), decimal_from(Z2))
    if bounds.Y0 < 0:
        raise ValueError("Y0 must be nonnegative")
    if bounds.Z0 < 0:
        raise ValueError("Z0 must be nonnegative")
    if bounds.Z2 < 0:
        raise ValueError("Z2 must be nonnegative")
    return bounds


def parse_radius_interval(lower: str | float, upper: str | float) -> RadiusInterval:
    radius = RadiusInterval(decimal_from(lower), decimal_from(upper))
    if radius.lower <= 0:
        raise ValueError("radius lower endpoint must be positive")
    if radius.upper < radius.lower:
        raise ValueError("radius upper endpoint must be >= lower endpoint")
    return radius


def radii_polynomial(bounds: RadiiBounds, r: Decimal) -> Decimal:
    return bounds.Y0 - (Decimal(1) - bounds.Z0) * r + bounds.Z2 * r * r


def radii_polynomial_interval(
    bounds: RadiiBounds,
    radius: RadiusInterval,
    precision: int = DEFAULT_PRECISION,
) -> tuple[Decimal, Decimal]:
    """Return the min/max of the convex scalar polynomial on ``radius``."""

    with localcontext() as ctx:
        ctx.prec = precision
        left = radii_polynomial(bounds, radius.lower)
        right = radii_polynomial(bounds, radius.upper)
        vertex_values = [left, right]
        if bounds.Z2 > 0:
            vertex = (Decimal(1) - bounds.Z0) / (Decimal(2) * bounds.Z2)
            if radius.lower <= vertex <= radius.upper:
                vertex_values.append(radii_polynomial(bounds, vertex))
        return min(vertex_values), max(left, right)


def validate_radii_polynomial(
    Y0: str | float,
    Z0: str | float,
    Z2: str | float,
    radius_lower: str | float,
    radius_upper: str | float,
    precision: int = DEFAULT_PRECISION,
) -> dict[str, Any]:
    bounds = parse_bounds(Y0, Z0, Z2)
    radius = parse_radius_interval(radius_lower, radius_upper)
    lower, upper = radii_polynomial_interval(bounds, radius, precision=precision)
    pass_gate = upper < 0 and bounds.Z0 < 1
    return {
        "pass": bool(pass_gate),
        "backend": "decimal-scalar-radii-polynomial",
        "precision_digits": int(precision),
        "Y0": str(bounds.Y0),
        "Z0": str(bounds.Z0),
        "Z2": str(bounds.Z2),
        "radius_interval": [str(radius.lower), str(radius.upper)],
        "radii_polynomial_interval": [str(lower), str(upper)],
        "conditions": {
            "Z0_less_than_one": bool(bounds.Z0 < 1),
            "upper_bound_negative": bool(upper < 0),
        },
        "mathematical_statement": (
            "For p(r)=Y0-(1-Z0)r+Z2*r^2, the supplied radius interval "
            "has p(r)<0 throughout it."
        ),
    }


def manufactured_zero_self_test() -> dict[str, Any]:
    """A deterministic positive-control check for the scalar gate."""

    return validate_radii_polynomial(
        Y0="0",
        Z0="0.1",
        Z2="0.1",
        radius_lower="0.01",
        radius_upper="1",
    )

