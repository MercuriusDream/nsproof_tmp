"""Projection-backed compactified profile evaluator.

This module bridges the new transseries-Chebyshev projection format to the
existing finite-difference residual oracle.  It is not the final exact residual
expression DAG; it provides a deterministic self-test that projected profiles
evaluate consistently and keep the same finite-difference obstruction as the
source seed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from axisym_residual import Residual, residual_at
from compactified_collocation import qb_to_rz
from compactified_profile import grid, load_seed_json_profile
from profile_project_cheb import Patch, cheb_eval_tensor, find_patch

JET_ORDER = 3
Index = tuple[int, int]
RESIDUAL_KINDS = ("raw", "geometric-normalized", "normalized-structural", "normalized-strict-tail")


class Jet2:
    """Two-variable Taylor jet with coefficients divided by factorials."""

    def __init__(self, coeffs: dict[Index, float] | None = None):
        self.coeffs: dict[Index, float] = {}
        for (i, j), value in (coeffs or {}).items():
            if i + j <= JET_ORDER and abs(value) > 0.0:
                self.coeffs[(i, j)] = float(value)

    @staticmethod
    def const(value: float) -> "Jet2":
        return Jet2({(0, 0): value})

    @staticmethod
    def var_r(value: float) -> "Jet2":
        return Jet2({(0, 0): value, (1, 0): 1.0})

    @staticmethod
    def var_z(value: float) -> "Jet2":
        return Jet2({(0, 0): value, (0, 1): 1.0})

    def value(self) -> float:
        return self.coeffs.get((0, 0), 0.0)

    def _coerce(self, other: object) -> "Jet2":
        if isinstance(other, Jet2):
            return other
        if isinstance(other, (int, float)):
            return Jet2.const(float(other))
        return NotImplemented  # type: ignore[return-value]

    def __add__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out = dict(self.coeffs)
        for key, value in rhs.coeffs.items():
            out[key] = out.get(key, 0.0) + value
        return Jet2(out)

    def __radd__(self, other: object) -> "Jet2":
        return self.__add__(other)

    def __sub__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out = dict(self.coeffs)
        for key, value in rhs.coeffs.items():
            out[key] = out.get(key, 0.0) - value
        return Jet2(out)

    def __rsub__(self, other: object) -> "Jet2":
        return self._coerce(other).__sub__(self)

    def __neg__(self) -> "Jet2":
        return Jet2({key: -value for key, value in self.coeffs.items()})

    def __mul__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out: dict[Index, float] = {}
        for (i1, j1), v1 in self.coeffs.items():
            for (i2, j2), v2 in rhs.coeffs.items():
                i = i1 + i2
                j = j1 + j2
                if i + j <= JET_ORDER:
                    out[(i, j)] = out.get((i, j), 0.0) + v1 * v2
        return Jet2(out)

    def __rmul__(self, other: object) -> "Jet2":
        return self.__mul__(other)

    def reciprocal(self) -> "Jet2":
        c0 = self.value()
        if abs(c0) < 1e-30:
            raise ZeroDivisionError("jet reciprocal around zero")
        h = (self - c0) * (1.0 / c0)
        out = Jet2.const(0.0)
        power = Jet2.const(1.0)
        sign = 1.0
        for _n in range(JET_ORDER + 1):
            out = out + sign * power
            power = power * h
            sign *= -1.0
        return (1.0 / c0) * out

    def __truediv__(self, other: object) -> "Jet2":
        return self * self._coerce(other).reciprocal()

    def __rtruediv__(self, other: object) -> "Jet2":
        return self._coerce(other) * self.reciprocal()

    def pow(self, alpha: float) -> "Jet2":
        c0 = self.value()
        if c0 <= 0.0:
            raise ValueError("jet fractional power requires positive base")
        h = (self - c0) * (1.0 / c0)
        out = Jet2.const(0.0)
        power = Jet2.const(1.0)
        binom = 1.0
        for n in range(JET_ORDER + 1):
            if n > 0:
                binom *= (alpha - (n - 1)) / n
            out = out + binom * power
            power = power * h
        return (c0**alpha) * out

    def __pow__(self, alpha: object) -> "Jet2":
        if isinstance(alpha, int):
            if alpha == 0:
                return Jet2.const(1.0)
            if alpha < 0:
                return (self ** (-alpha)).reciprocal()
            out = Jet2.const(1.0)
            for _ in range(alpha):
                out = out * self
            return out
        if isinstance(alpha, float):
            return self.pow(alpha)
        return NotImplemented  # type: ignore[return-value]

    def dr(self) -> "Jet2":
        out: dict[Index, float] = {}
        for (i, j), value in self.coeffs.items():
            if i > 0:
                out[(i - 1, j)] = out.get((i - 1, j), 0.0) + i * value
        return Jet2(out)

    def dz(self) -> "Jet2":
        out: dict[Index, float] = {}
        for (i, j), value in self.coeffs.items():
            if j > 0:
                out[(i, j - 1)] = out.get((i, j - 1), 0.0) + j * value
        return Jet2(out)


def cheb_eval_1d_jet(coeffs: list[float], t: Jet2) -> Jet2:
    if not coeffs:
        return Jet2.const(0.0)
    b_k2 = Jet2.const(0.0)
    b_k1 = Jet2.const(0.0)
    for c in reversed(coeffs[1:]):
        b_k0 = 2.0 * t * b_k1 - b_k2 + c
        b_k2 = b_k1
        b_k1 = b_k0
    return coeffs[0] + t * b_k1 - b_k2


def cheb_eval_tensor_jet(coeffs: list[list[float]], q: Jet2, x: Jet2, q0: float, q1: float, x0: float, x1: float) -> Jet2:
    tq = (2.0 * q - q0 - q1) / (q1 - q0)
    tx = (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = [cheb_eval_1d_jet(row, tx) for row in coeffs]
    return cheb_eval_1d_jet(q_values, tq)


@dataclass(frozen=True)
class OriginTaylor:
    enabled: bool
    q_min: float
    basis: list[tuple[int, int, float]]

    @staticmethod
    def disabled() -> "OriginTaylor":
        return OriginTaylor(enabled=False, q_min=2.0, basis=[])

    @classmethod
    def load(cls, item: dict[str, Any] | None) -> "OriginTaylor":
        if not item or not item.get("enabled", False):
            return cls.disabled()
        basis = [
            (int(entry["R_power"]), int(entry["Z_power"]), float(entry["coeff"]))
            for entry in item.get("basis", [])
        ]
        return cls(enabled=True, q_min=float(item["q_min"]), basis=basis)

    def eval_qx(self, q: float, x: float) -> float:
        rho2 = 1.0 / (q * q) - 1.0
        r2 = rho2 * (1.0 - x)
        z2 = rho2 * x
        return sum(coeff * (r2**a) * (z2**b) for a, b, coeff in self.basis)

    def eval_qx_jet(self, q: Jet2, x: Jet2) -> Jet2:
        rho2 = (q ** -2) - 1.0
        r2 = rho2 * (1.0 - x)
        z2 = rho2 * x
        out = Jet2.const(0.0)
        for a, b, coeff in self.basis:
            out = out + coeff * (r2 ** a) * (z2 ** b)
        return out


@dataclass(frozen=True)
class ProjectedProfile:
    gamma: float
    B: float
    p: float
    f_an: list[Patch]
    g_an: list[Patch]
    f_frac: list[list[Patch]]
    g_frac: list[list[Patch]]
    f_origin: OriginTaylor
    g_origin: OriginTaylor

    @staticmethod
    def _load_patches(items: list[dict[str, Any]]) -> list[Patch]:
        patches: list[Patch] = []
        for item in items:
            q0, q1 = item["q_interval"]
            x0, x1 = item["x_interval"]
            patches.append(Patch(float(q0), float(q1), float(x0), float(x1), item["coeffs"]))
        return patches

    @classmethod
    def load(cls, path: str) -> "ProjectedProfile":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("format") != "transseries_cheb_projection_v1":
            raise ValueError(f"{path} is not a transseries_cheb_projection_v1 file")
        blocks = data["blocks"]
        return cls(
            gamma=float(data["gamma"]),
            B=float(data["B"]),
            p=float(data["p"]),
            f_an=cls._load_patches(blocks["F_an"]),
            g_an=cls._load_patches(blocks["G_an"]),
            f_frac=[cls._load_patches(block) for block in blocks.get("F_frac", [])],
            g_frac=[cls._load_patches(block) for block in blocks.get("G_frac", [])],
            f_origin=OriginTaylor.load(blocks.get("F_origin_taylor")),
            g_origin=OriginTaylor.load(blocks.get("G_origin_taylor")),
        )

    @staticmethod
    def _eval_patch(patches: list[Patch], q: float, x: float) -> float:
        patch = find_patch(patches, q, x)
        return cheb_eval_tensor(patch.coeffs, q, x, patch.q0, patch.q1, patch.x0, patch.x1)

    @staticmethod
    def _eval_patch_jet(patches: list[Patch], q: Jet2, x: Jet2) -> Jet2:
        patch = find_patch(patches, q.value(), x.value())
        return cheb_eval_tensor_jet(patch.coeffs, q, x, patch.q0, patch.q1, patch.x0, patch.x1)

    def F_total(self, q: float, b: float) -> float:
        x = b * b
        if self.f_origin.enabled and q >= self.f_origin.q_min:
            return self.f_origin.eval_qx(q, x)
        value = 0.5 + q * q * self._eval_patch(self.f_an, q, x)
        for k, patches in enumerate(self.f_frac, start=1):
            value += (q ** (k * self.p)) * self._eval_patch(patches, q, x)
        return value

    def G_total(self, q: float, b: float) -> float:
        x = b * b
        if self.g_origin.enabled and q >= self.g_origin.q_min:
            return self.g_origin.eval_qx(q, x)
        value = self.B + q * q * self._eval_patch(self.g_an, q, x)
        for k, patches in enumerate(self.g_frac, start=1):
            value += (q ** (k * self.p)) * self._eval_patch(patches, q, x)
        return value

    def F_total_jet(self, q: Jet2, x: Jet2) -> Jet2:
        if self.f_origin.enabled and q.value() >= self.f_origin.q_min:
            return self.f_origin.eval_qx_jet(q, x)
        value = Jet2.const(0.5) + q * q * self._eval_patch_jet(self.f_an, q, x)
        for k, patches in enumerate(self.f_frac, start=1):
            value = value + q.pow(k * self.p) * self._eval_patch_jet(patches, q, x)
        return value

    def G_total_jet(self, q: Jet2, x: Jet2) -> Jet2:
        if self.g_origin.enabled and q.value() >= self.g_origin.q_min:
            return self.g_origin.eval_qx_jet(q, x)
        value = Jet2.const(self.B) + q * q * self._eval_patch_jet(self.g_an, q, x)
        for k, patches in enumerate(self.g_frac, start=1):
            value = value + q.pow(k * self.p) * self._eval_patch_jet(patches, q, x)
        return value

    @staticmethod
    def qb(r: float, z: float) -> tuple[float, float]:
        rho = math.sqrt(r * r + z * z)
        q = 1.0 / math.sqrt(1.0 + rho * rho)
        b = z / rho if rho > 0.0 else 0.0
        return q, b

    def psi(self, r: float, z: float) -> float:
        q, b = self.qb(r, z)
        return r * r * z * (q ** self.p) * self.F_total(q, b)

    def swirl(self, r: float, z: float) -> float:
        q, b = self.qb(r, z)
        return r * r * (q ** self.p) * self.G_total(q, b)

    def psi_jet(self, r0: float, z0: float) -> Jet2:
        r = Jet2.var_r(r0)
        z = Jet2.var_z(z0)
        rho2 = r * r + z * z
        q = (1.0 + rho2).pow(-0.5)
        x = (z * z) / rho2
        return r * r * z * q.pow(self.p) * self.F_total_jet(q, x)

    def swirl_jet(self, r0: float, z0: float) -> Jet2:
        r = Jet2.var_r(r0)
        z = Jet2.var_z(z0)
        rho2 = r * r + z * z
        q = (1.0 + rho2).pow(-0.5)
        x = (z * z) / rho2
        return r * r * q.pow(self.p) * self.G_total_jet(q, x)

    def exact_residual_at(self, r0: float, z0: float) -> Residual:
        r = Jet2.var_r(r0)
        z = Jet2.var_z(z0)
        psi = self.psi_jet(r0, z0)
        swirl = self.swirl_jet(r0, z0)
        psi_r = psi.dr()
        psi_z = psi.dz()
        swirl_r = swirl.dr()
        swirl_z = swirl.dz()
        a = psi.dr().dr() - psi.dr() / r + psi.dz().dz()
        a_r = a.dr()
        a_z = a.dz()
        e_psi = (
            (1.0 - self.gamma) * r * r * a
            + self.gamma * r * r * r * a_r
            + self.gamma * z * r * r * a_z
            + r * (psi_r * a_z - psi_z * a_r)
            + 2.0 * psi_z * a
            + (swirl * swirl).dz()
        )
        e_gamma = (
            (1.0 - 2.0 * self.gamma) * swirl
            + self.gamma * (r * swirl_r + z * swirl_z)
            + (psi_r * swirl_z - psi_z * swirl_r) / r
        )
        return Residual(e_psi=e_psi.value(), e_gamma=e_gamma.value())


def normalize_residual_geometric(raw: Residual, q: float, b: float, p: float) -> Residual:
    """Discovery normalization by known compactified homogeneity factors.

    This is not the final proof quotient.  It removes the leading far-tail,
    origin, and axis vanishing weights expected from

        psi = r^2 z q^p F,    Gamma = r^2 q^p G.

    In terms of rho = sqrt(r^2 + z^2), the far nonlinear residual scales like
    rho^(3-2p) for the streamfunction equation and rho^(2-2p) for the Gamma
    equation; near the origin the same compact factors scale like rho^3 and
    rho^2.  The axis factors reflect the exact cylindrical prefactors.
    """

    rho2 = max(0.0, 1.0 / (q * q) - 1.0)
    rho = math.sqrt(rho2)
    one_minus_b2 = max(0.0, 1.0 - b * b)
    q_factor = q ** (2.0 * p)
    epsi_factor = q_factor * (rho**3) * (one_minus_b2**2)
    egamma_factor = q_factor * (rho**2) * one_minus_b2
    floor = 1e-14
    return Residual(
        e_psi=raw.e_psi / max(epsi_factor, floor),
        e_gamma=raw.e_gamma / max(egamma_factor, floor),
    )


def compactified_residual_factors(q: float, b: float, p: float, residual_kind: str) -> tuple[float, float]:
    x = b * b
    one_minus_x = max(0.0, 1.0 - x)
    one_minus_q2 = max(0.0, 1.0 - q * q)
    if residual_kind == "normalized-structural":
        fac_psi = b * (one_minus_x**2) * (one_minus_q2**2.5) * (q ** (p - 1.0))
        fac_gamma = one_minus_x * one_minus_q2 * (q**p)
        return fac_psi, fac_gamma
    if residual_kind == "normalized-strict-tail":
        fac_psi = b * (one_minus_x**2) * (one_minus_q2**2.5) * (q ** (2.0 * p - 3.0))
        fac_gamma = one_minus_x * one_minus_q2 * (q ** (2.0 * p - 2.0))
        return fac_psi, fac_gamma
    raise ValueError(f"{residual_kind!r} does not have compactified factors")


def compactified_residual_defined(q: float, b: float, p: float, residual_kind: str, floor: float = 1e-14) -> bool:
    if residual_kind in ("raw", "geometric-normalized"):
        return True
    fac_psi, fac_gamma = compactified_residual_factors(q, b, p, residual_kind)
    return abs(fac_psi) > floor and abs(fac_gamma) > floor


def residual_with_kind(raw: Residual, q: float, b: float, p: float, residual_kind: str) -> Residual:
    if residual_kind == "raw":
        return raw
    if residual_kind == "geometric-normalized":
        return normalize_residual_geometric(raw, q, b, p)
    if residual_kind in ("normalized-structural", "normalized-strict-tail"):
        fac_psi, fac_gamma = compactified_residual_factors(q, b, p, residual_kind)
        floor = 1e-14
        if abs(fac_psi) <= floor or abs(fac_gamma) <= floor:
            raise ZeroDivisionError(f"compactified residual factor vanished for q={q} b={b}")
        return Residual(e_psi=raw.e_psi / fac_psi, e_gamma=raw.e_gamma / fac_gamma)
    raise ValueError(f"unknown residual kind {residual_kind!r}")


def scan_qb_fields(
    psi: Callable[[float, float], float],
    swirl: Callable[[float, float], float],
    gamma: float,
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
    residual_kind: str,
    p: float,
) -> tuple[Residual, tuple[float, float, float, float], float, int, int]:
    worst = Residual(0.0, 0.0)
    worst_point = (q_min, b_min, 0.0, 0.0)
    total = 0.0
    count = 0
    point_count = 0
    skipped = 0
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h:
                skipped += 1
                continue
            if not compactified_residual_defined(q, b, p, residual_kind):
                skipped += 1
                continue
            raw = residual_at(psi, swirl, gamma, r, z, h)
            residual = residual_with_kind(raw, q, b, p, residual_kind)
            total += residual.e_psi * residual.e_psi + residual.e_gamma * residual.e_gamma
            count += 2
            point_count += 1
            if residual.max_abs > worst.max_abs:
                worst = residual
                worst_point = (q, b, r, z)
    rms = math.sqrt(total / max(count, 1))
    return worst, worst_point, rms, point_count, skipped


def scan_qb_exact(
    projection: ProjectedProfile,
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
    residual_kind: str,
) -> tuple[Residual, tuple[float, float, float, float], float, int, int]:
    worst = Residual(0.0, 0.0)
    worst_point = (q_min, b_min, 0.0, 0.0)
    total = 0.0
    count = 0
    point_count = 0
    skipped = 0
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h or r == 0.0 or (r == 0.0 and z == 0.0):
                skipped += 1
                continue
            if not compactified_residual_defined(q, b, projection.p, residual_kind):
                skipped += 1
                continue
            raw = projection.exact_residual_at(r, z)
            residual = residual_with_kind(raw, q, b, projection.p, residual_kind)
            total += residual.e_psi * residual.e_psi + residual.e_gamma * residual.e_gamma
            count += 2
            point_count += 1
            if residual.max_abs > worst.max_abs:
                worst = residual
                worst_point = (q, b, r, z)
    rms = math.sqrt(total / max(count, 1))
    return worst, worst_point, rms, point_count, skipped


def compare_source_projection(
    projection: ProjectedProfile,
    source_seed: str,
    check_n: int,
) -> tuple[float, float]:
    _gamma, _B, source = load_seed_json_profile(source_seed)
    max_f = 0.0
    max_g = 0.0
    origin_q_min = min(
        [
            origin.q_min
            for origin in (projection.f_origin, projection.g_origin)
            if origin.enabled
        ],
        default=2.0,
    )
    for q in grid(0.0, 1.0, check_n):
        if q >= origin_q_min:
            continue
        for x in grid(0.0, 1.0, check_n):
            b = math.sqrt(max(0.0, x))
            max_f = max(max_f, abs(projection.F_total(q, b) - source.F_total(q, b)))
            max_g = max(max_g, abs(projection.G_total(q, b) - source.G_total(q, b)))
    return max_f, max_g


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--source-seed", default="")
    parser.add_argument("--compare-n", type=int, default=17)
    parser.add_argument("--q-min", type=float, default=0.345)
    parser.add_argument("--q-max", type=float, default=0.495)
    parser.add_argument("--b-min", type=float, default=0.18)
    parser.add_argument("--b-max", type=float, default=0.38)
    parser.add_argument("--n-q", type=int, default=17)
    parser.add_argument("--n-b", type=int, default=17)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--mode", choices=["finite-difference", "jet"], default="finite-difference")
    parser.add_argument("--residual-kind", choices=RESIDUAL_KINDS, default="raw")
    args = parser.parse_args()

    projection = ProjectedProfile.load(args.profile)
    print(f"profile={args.profile}")
    print(f"gamma={projection.gamma:.15g} B={projection.B:.15g} p={projection.p:.15g}")
    if args.source_seed:
        max_f, max_g = compare_source_projection(projection, args.source_seed, args.compare_n)
        print(f"source_seed={args.source_seed}")
        print(f"source_projection_F_error={max_f:.12e}")
        print(f"source_projection_G_error={max_g:.12e}")

    if args.mode == "finite-difference":
        worst, point, rms, points, skipped = scan_qb_fields(
            projection.psi,
            projection.swirl,
            projection.gamma,
            q_min=args.q_min,
            q_max=args.q_max,
            b_min=args.b_min,
            b_max=args.b_max,
            n_q=args.n_q,
            n_b=args.n_b,
            h=args.h,
            residual_kind=args.residual_kind,
            p=projection.p,
        )
        status = "FINITE_DIFFERENCE_BRIDGE_NOT_EXACT_RESIDUAL_DAG"
    else:
        worst, point, rms, points, skipped = scan_qb_exact(
            projection,
            q_min=args.q_min,
            q_max=args.q_max,
            b_min=args.b_min,
            b_max=args.b_max,
            n_q=args.n_q,
            n_b=args.n_b,
            h=args.h,
            residual_kind=args.residual_kind,
        )
        status = "TAYLOR_JET_RESIDUAL_NOT_INTERVAL_VALIDATION"
    q, b, r, z = point
    print(f"grid={args.n_q}x{args.n_b} points={points} skipped={skipped} h={args.h:.3e}")
    print(f"q=[{args.q_min}, {args.q_max}] b=[{args.b_min}, {args.b_max}]")
    print(f"residual_kind={args.residual_kind}")
    print(f"worst q={q:.6f} b={b:.6f} r={r:.6f} z={z:.6f}")
    print(f"e_psi={worst.e_psi:.12e}")
    print(f"e_gamma={worst.e_gamma:.12e}")
    print(f"max_abs={worst.max_abs:.12e}")
    print(f"rms={rms:.12e}")
    print(f"status={status}")


if __name__ == "__main__":
    main()
