#!/usr/bin/env python3
"""Compactified tail-factored profile residual scaffold.

The production profile solver in proof-problem.md must use

    q = (1 + r^2 + z^2)^(-1/2), b = z / sqrt(r^2 + z^2),
    psi = r^2 z q^(1/gamma) F(q,b),
    Gamma = r^2 q^(1/gamma) G(q,b).

This script makes that ansatz executable and evaluates the finite-difference
axisymmetric residual on a small grid. It is a scaffold for the future
Newton/Lyapunov-Schmidt solver, not a validated solver.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Iterable

from axisym_residual import Field, Residual, residual_at


Coeff = tuple[int, int, float]


def normalize_coeffs(raw: object) -> tuple[Coeff, ...]:
    coeffs: list[Coeff] = []
    if not isinstance(raw, list):
        raise ValueError("coefficients must be a list")
    for item in raw:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError(f"bad coefficient entry {item!r}")
        coeffs.append((int(item[0]), int(item[1]), float(item[2])))
    return tuple(coeffs)


def load_seed_json(path: str) -> tuple[float, float, tuple[Coeff, ...], tuple[Coeff, ...]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    gamma = float(data["gamma"])
    B = float(data.get("B", 1.0))
    f_coeffs = normalize_coeffs(data["f_coeffs"])
    g_coeffs = normalize_coeffs(data["g_coeffs"])
    return gamma, B, f_coeffs, g_coeffs


@dataclass(frozen=True)
class CompactifiedProfile:
    gamma: float
    f_coeffs: tuple[Coeff, ...]
    g_coeffs: tuple[Coeff, ...]
    f_edge_coeffs: tuple[Coeff, ...] = ()
    g_edge_coeffs: tuple[Coeff, ...] = ()
    f_bounded_edge_coeffs: tuple[Coeff, ...] = ()
    g_bounded_edge_coeffs: tuple[Coeff, ...] = ()
    f_vanishing_edge_coeffs: tuple[Coeff, ...] = ()
    g_vanishing_edge_coeffs: tuple[Coeff, ...] = ()
    vanishing_edge_power: float = 1.0
    f_interior_bump_coeffs: tuple[Coeff, ...] = ()
    g_interior_bump_coeffs: tuple[Coeff, ...] = ()
    interior_bump_q_centers: tuple[float, ...] = ()
    interior_bump_b2_centers: tuple[float, ...] = ()
    interior_bump_q_radius: float = 0.14
    interior_bump_b2_radius: float = 0.10
    interior_bump_shape: str = "compact"
    interior_bump_q_flatness: float = 1.0

    def qb(self, r: float, z: float) -> tuple[float, float]:
        rho = math.sqrt(r * r + z * z)
        q = 1.0 / math.sqrt(1.0 + rho * rho)
        b = z / rho if rho > 0.0 else 0.0
        return q, b

    @staticmethod
    def even_poly(q: float, b: float, coeffs: tuple[Coeff, ...]) -> float:
        value = 0.0
        b2 = b * b
        for i, j, c in coeffs:
            value += c * (q**i) * (b2**j)
        return value

    def F(self, q: float, b: float) -> float:
        return self.even_poly(q, b, self.f_coeffs)

    def G(self, q: float, b: float) -> float:
        return self.even_poly(q, b, self.g_coeffs)

    @staticmethod
    def edge_poly(q: float, b: float, coeffs: tuple[Coeff, ...]) -> float:
        value = 0.0
        b2 = b * b
        eta = b2 / max(1.0 - b2, 1e-12)
        one_minus_q = 1.0 - q
        for i, j, c in coeffs:
            value += c * (one_minus_q**i) * (eta**j)
        return value

    @staticmethod
    def bounded_edge_poly(q: float, b: float, coeffs: tuple[Coeff, ...]) -> float:
        value = 0.0
        b2 = b * b
        one_minus_q = 1.0 - q
        for i, j, c in coeffs:
            value += c * (one_minus_q**i) * (b2**j)
        return value

    def vanishing_edge_poly(self, q: float, b: float, coeffs: tuple[Coeff, ...]) -> float:
        return (q ** self.vanishing_edge_power) * self.bounded_edge_poly(q, b, coeffs)

    @staticmethod
    def compact_bump(x: float, center: float, radius: float) -> float:
        if radius <= 0.0:
            return 0.0
        scaled = (x - center) / radius
        if abs(scaled) >= 1.0:
            return 0.0
        return math.exp(1.0 - 1.0 / (1.0 - scaled * scaled))

    def interior_bump_poly(self, q: float, b: float, coeffs: tuple[Coeff, ...]) -> float:
        value = 0.0
        b2 = b * b
        for i, j, c in coeffs:
            if i < 0 or i >= len(self.interior_bump_q_centers):
                continue
            if j < 0 or j >= len(self.interior_bump_b2_centers):
                continue
            q_center = self.interior_bump_q_centers[i]
            b2_center = self.interior_bump_b2_centers[j]
            if self.interior_bump_shape == "flat_gaussian":
                if q <= 0.0 or q_center <= 0.0:
                    q_weight = 0.0
                else:
                    tail_flat = math.exp(
                        -self.interior_bump_q_flatness * (1.0 / q - 1.0 / q_center)
                    )
                    q_weight = tail_flat * math.exp(-((q - q_center) / self.interior_bump_q_radius) ** 2)
                b2_weight = math.exp(-((b2 - b2_center) / self.interior_bump_b2_radius) ** 2)
            else:
                q_weight = self.compact_bump(q, q_center, self.interior_bump_q_radius)
                b2_weight = self.compact_bump(b2, b2_center, self.interior_bump_b2_radius)
            value += c * q_weight * b2_weight
        return value

    def F_total(self, q: float, b: float) -> float:
        return (
            self.F(q, b)
            + self.edge_poly(q, b, self.f_edge_coeffs)
            + self.bounded_edge_poly(q, b, self.f_bounded_edge_coeffs)
            + self.vanishing_edge_poly(q, b, self.f_vanishing_edge_coeffs)
            + self.interior_bump_poly(q, b, self.f_interior_bump_coeffs)
        )

    def G_total(self, q: float, b: float) -> float:
        return (
            self.G(q, b)
            + self.edge_poly(q, b, self.g_edge_coeffs)
            + self.bounded_edge_poly(q, b, self.g_bounded_edge_coeffs)
            + self.vanishing_edge_poly(q, b, self.g_vanishing_edge_coeffs)
            + self.interior_bump_poly(q, b, self.g_interior_bump_coeffs)
        )

    def psi(self, r: float, z: float) -> float:
        q, b = self.qb(r, z)
        return r * r * z * (q ** (1.0 / self.gamma)) * self.F_total(q, b)

    def swirl(self, r: float, z: float) -> float:
        q, b = self.qb(r, z)
        return r * r * (q ** (1.0 / self.gamma)) * self.G_total(q, b)


def load_seed_json_profile(path: str) -> tuple[float, float, CompactifiedProfile]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    gamma = float(data["gamma"])
    B = float(data.get("B", 1.0))
    f_coeffs = normalize_coeffs(data["f_coeffs"])
    g_coeffs = normalize_coeffs(data["g_coeffs"])
    f_edge_coeffs = normalize_coeffs(data.get("f_edge_coeffs", []))
    g_edge_coeffs = normalize_coeffs(data.get("g_edge_coeffs", []))
    f_bounded_edge_coeffs = normalize_coeffs(data.get("f_bounded_edge_coeffs", []))
    g_bounded_edge_coeffs = normalize_coeffs(data.get("g_bounded_edge_coeffs", []))
    f_vanishing_edge_coeffs = normalize_coeffs(data.get("f_vanishing_edge_coeffs", []))
    g_vanishing_edge_coeffs = normalize_coeffs(data.get("g_vanishing_edge_coeffs", []))
    f_interior_bump_coeffs = normalize_coeffs(data.get("f_interior_bump_coeffs", []))
    g_interior_bump_coeffs = normalize_coeffs(data.get("g_interior_bump_coeffs", []))
    vanishing_edge_power = float(data.get("vanishing_edge_power", 1.0))
    if vanishing_edge_power <= 0.0:
        raise ValueError("vanishing_edge_power must be positive")
    interior_bump_q_centers = tuple(float(x) for x in data.get("interior_bump_q_centers", []))
    interior_bump_b2_centers = tuple(float(x) for x in data.get("interior_bump_b2_centers", []))
    interior_bump_q_radius = float(data.get("interior_bump_q_radius", 0.14))
    interior_bump_b2_radius = float(data.get("interior_bump_b2_radius", 0.10))
    interior_bump_shape = str(data.get("interior_bump_shape", "compact"))
    interior_bump_q_flatness = float(data.get("interior_bump_q_flatness", 1.0))
    profile = CompactifiedProfile(
        gamma=gamma,
        f_coeffs=f_coeffs,
        g_coeffs=g_coeffs,
        f_edge_coeffs=f_edge_coeffs,
        g_edge_coeffs=g_edge_coeffs,
        f_bounded_edge_coeffs=f_bounded_edge_coeffs,
        g_bounded_edge_coeffs=g_bounded_edge_coeffs,
        f_vanishing_edge_coeffs=f_vanishing_edge_coeffs,
        g_vanishing_edge_coeffs=g_vanishing_edge_coeffs,
        vanishing_edge_power=vanishing_edge_power,
        f_interior_bump_coeffs=f_interior_bump_coeffs,
        g_interior_bump_coeffs=g_interior_bump_coeffs,
        interior_bump_q_centers=interior_bump_q_centers,
        interior_bump_b2_centers=interior_bump_b2_centers,
        interior_bump_q_radius=interior_bump_q_radius,
        interior_bump_b2_radius=interior_bump_b2_radius,
        interior_bump_shape=interior_bump_shape,
        interior_bump_q_flatness=interior_bump_q_flatness,
    )
    return gamma, B, profile


def parse_coeffs(raw: str) -> tuple[Coeff, ...]:
    """Parse coefficients as i,j,c;i,j,c with b appearing only as b^(2j)."""

    coeffs: list[Coeff] = []
    if not raw.strip():
        return tuple(coeffs)
    for item in raw.split(";"):
        parts = item.split(",")
        if len(parts) != 3:
            raise ValueError(f"bad coefficient {item!r}; expected i,j,c")
        i = int(parts[0])
        j = int(parts[1])
        c = float(parts[2])
        coeffs.append((i, j, c))
    return tuple(coeffs)


def grid(start: float, stop: float, count: int) -> Iterable[float]:
    if count <= 1:
        yield start
        return
    step = (stop - start) / (count - 1)
    for k in range(count):
        yield start + k * step


def scan_residual(
    profile: CompactifiedProfile,
    gamma: float,
    r_min: float,
    r_max: float,
    z_min: float,
    z_max: float,
    n: int,
    h: float,
) -> tuple[Residual, tuple[float, float], float]:
    psi: Field = profile.psi
    swirl: Field = profile.swirl
    worst = Residual(0.0, 0.0)
    worst_point = (r_min, z_min)
    total = 0.0
    count = 0
    for r in grid(r_min, r_max, n):
        if r <= 2.0 * h:
            continue
        for z in grid(z_min, z_max, n):
            res = residual_at(psi, swirl, gamma, r, z, h)
            total += res.e_psi * res.e_psi + res.e_gamma * res.e_gamma
            count += 2
            if res.max_abs > worst.max_abs:
                worst = res
                worst_point = (r, z)
    rms = math.sqrt(total / max(count, 1))
    return worst, worst_point, rms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--f", default="0,0,0.5")
    parser.add_argument("--g", default="")
    parser.add_argument("--seed-json", default="")
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--h", type=float, default=1e-3)
    args = parser.parse_args()

    gamma = args.gamma
    B = args.B
    if args.seed_json:
        gamma, B, profile = load_seed_json_profile(args.seed_json)
    else:
        g_raw = args.g if args.g else f"0,0,{B}"
        f_coeffs = parse_coeffs(args.f)
        g_coeffs = parse_coeffs(g_raw)
        profile = CompactifiedProfile(gamma=gamma, f_coeffs=f_coeffs, g_coeffs=g_coeffs)
    worst, point, rms = scan_residual(
        profile,
        gamma=gamma,
        r_min=args.r_min,
        r_max=args.r_max,
        z_min=args.z_min,
        z_max=args.z_max,
        n=args.n,
        h=args.h,
    )
    print(f"gamma={gamma} B={B} grid={args.n}x{args.n}")
    print(f"F coeffs={profile.f_coeffs}")
    print(f"G coeffs={profile.g_coeffs}")
    if profile.f_edge_coeffs or profile.g_edge_coeffs:
        print(f"F edge coeffs={profile.f_edge_coeffs}")
        print(f"G edge coeffs={profile.g_edge_coeffs}")
    if profile.f_bounded_edge_coeffs or profile.g_bounded_edge_coeffs:
        print(f"F bounded edge coeffs={profile.f_bounded_edge_coeffs}")
        print(f"G bounded edge coeffs={profile.g_bounded_edge_coeffs}")
    if profile.f_vanishing_edge_coeffs or profile.g_vanishing_edge_coeffs:
        print(f"F vanishing edge coeffs={profile.f_vanishing_edge_coeffs}")
        print(f"G vanishing edge coeffs={profile.g_vanishing_edge_coeffs}")
    print(f"worst point r={point[0]:.6f} z={point[1]:.6f}")
    print(f"  psi-equation residual   = {worst.e_psi:.12e}")
    print(f"  Gamma-equation residual = {worst.e_gamma:.12e}")
    print(f"  max abs residual        = {worst.max_abs:.12e}")
    print(f"  RMS residual            = {rms:.12e}")


if __name__ == "__main__":
    main()
