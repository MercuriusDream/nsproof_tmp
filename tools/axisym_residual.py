#!/usr/bin/env python3
"""Finite-difference residual checks for the axisymmetric-with-swirl profile PDE.

This is a small dependency-free executable check for the equations quoted in
proof-problem.md. It is not the final compactified solver; it is a residual
oracle that can test candidate (psi,Gamma) functions at physical (r,z) points.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable


Field = Callable[[float, float], float]


@dataclass(frozen=True)
class Residual:
    e_psi: float
    e_gamma: float

    @property
    def max_abs(self) -> float:
        return max(abs(self.e_psi), abs(self.e_gamma))


def d_r(f: Field, r: float, z: float, h: float) -> float:
    return (f(r + h, z) - f(r - h, z)) / (2.0 * h)


def d_z(f: Field, r: float, z: float, h: float) -> float:
    return (f(r, z + h) - f(r, z - h)) / (2.0 * h)


def d_rr(f: Field, r: float, z: float, h: float) -> float:
    return (f(r + h, z) - 2.0 * f(r, z) + f(r - h, z)) / (h * h)


def d_zz(f: Field, r: float, z: float, h: float) -> float:
    return (f(r, z + h) - 2.0 * f(r, z) + f(r, z - h)) / (h * h)


def make_a(psi: Field, h: float) -> Field:
    def a_field(r: float, z: float) -> float:
        return d_rr(psi, r, z, h) - d_r(psi, r, z, h) / r + d_zz(psi, r, z, h)

    return a_field


def residual_at(
    psi: Field,
    swirl: Field,
    gamma: float,
    r: float,
    z: float,
    h: float,
) -> Residual:
    if r <= 2.0 * h:
        raise ValueError("Choose r > 2h so central differences stay away from the axis.")

    a_field = make_a(psi, h)
    a = a_field(r, z)
    a_r = d_r(a_field, r, z, h)
    a_z = d_z(a_field, r, z, h)
    psi_r = d_r(psi, r, z, h)
    psi_z = d_z(psi, r, z, h)
    swirl_r = d_r(swirl, r, z, h)
    swirl_z = d_z(swirl, r, z, h)

    def swirl_sq(rr: float, zz: float) -> float:
        value = swirl(rr, zz)
        return value * value

    swirl_sq_z = d_z(swirl_sq, r, z, h)

    e_psi = (
        (1.0 - gamma) * r * r * a
        + gamma * r**3 * a_r
        + gamma * z * r * r * a_z
        + r * (psi_r * a_z - psi_z * a_r)
        + 2.0 * psi_z * a
        + swirl_sq_z
    )

    e_gamma = (
        (1.0 - 2.0 * gamma) * swirl(r, z)
        + gamma * (r * swirl_r + z * swirl_z)
        + (psi_r * swirl_z - psi_z * swirl_r) / r
    )
    return Residual(e_psi=e_psi, e_gamma=e_gamma)


def conical_core(B: float) -> tuple[Field, Field]:
    def psi(r: float, z: float) -> float:
        return 0.5 * r * r * z

    def swirl(r: float, z: float) -> float:
        return B * r * r

    return psi, swirl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--r", type=float, default=1.3)
    parser.add_argument("--z", type=float, default=0.7)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--mode", choices=["conical-core"], default="conical-core")
    args = parser.parse_args()

    if args.mode == "conical-core":
        psi, swirl = conical_core(args.B)
    else:
        raise AssertionError("unreachable")

    res = residual_at(psi, swirl, args.gamma, args.r, args.z, args.h)
    print(f"mode={args.mode} gamma={args.gamma} B={args.B} r={args.r} z={args.z}")
    print(f"  psi-equation residual   = {res.e_psi:.12e}")
    print(f"  Gamma-equation residual = {res.e_gamma:.12e}")
    print(f"  max abs residual        = {res.max_abs:.12e}")


if __name__ == "__main__":
    main()
