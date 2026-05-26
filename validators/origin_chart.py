"""Floating origin-chart diagnostics for the two-chart profile route.

This module is deliberately conservative.  It evaluates triangular Taylor
blocks in the smooth origin variables

    R = r^2,  Z = z^2,

and compares their R/Z derivatives against the rectangular q/x chart on an
overlap set.  The diagnostics are useful for representation work, but they are
not interval arithmetic and they do not certify a profile.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Iterable


Index = tuple[int, int]
ChebTable = list[list[float]]


def factorial(value: int) -> int:
    return math.factorial(value)


def falling(power: int, order: int) -> float:
    if order > power:
        return 0.0
    out = 1.0
    for item in range(order):
        out *= power - item
    return out


def derivative_indices(max_order: int) -> list[Index]:
    return [(a, total - a) for total in range(max_order + 1) for a in range(total + 1)]


def grid(start: float, stop: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("grid count must be positive")
    if count == 1:
        return [0.5 * (start + stop)]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def parse_values(raw: str, default: Iterable[float]) -> list[float]:
    text = raw.strip()
    if not text:
        return list(default)
    return [float(item) for item in text.split(",") if item.strip()]


def qx_to_rz(q: float, x: float) -> tuple[float, float]:
    if not 0.0 < q <= 1.0:
        raise ValueError("q must lie in (0, 1]")
    if not 0.0 <= x <= 1.0:
        raise ValueError("x must lie in [0, 1]")
    rho2 = max(0.0, 1.0 / (q * q) - 1.0)
    return rho2 * (1.0 - x), rho2 * x


class Jet2:
    """Two-variable Taylor jet with factorial-divided coefficients."""

    def __init__(self, order: int, coeffs: dict[Index, float] | None = None):
        if order < 0:
            raise ValueError("jet order must be nonnegative")
        self.order = order
        self.coeffs: dict[Index, float] = {}
        for (a, b), value in (coeffs or {}).items():
            if a < 0 or b < 0:
                raise ValueError("jet indices must be nonnegative")
            if a + b <= order and value != 0.0:
                self.coeffs[(a, b)] = float(value)

    @classmethod
    def const(cls, order: int, value: float) -> "Jet2":
        return cls(order, {(0, 0): value})

    @classmethod
    def var_R(cls, order: int, value: float) -> "Jet2":
        return cls(order, {(0, 0): value, (1, 0): 1.0})

    @classmethod
    def var_Z(cls, order: int, value: float) -> "Jet2":
        return cls(order, {(0, 0): value, (0, 1): 1.0})

    def value(self) -> float:
        return self.coeffs.get((0, 0), 0.0)

    def partial(self, dR: int, dZ: int) -> float:
        return self.coeffs.get((dR, dZ), 0.0) * factorial(dR) * factorial(dZ)

    def _coerce(self, other: object) -> "Jet2":
        if isinstance(other, Jet2):
            if other.order != self.order:
                raise ValueError("cannot combine jets with different orders")
            return other
        if isinstance(other, (int, float)):
            return Jet2.const(self.order, float(other))
        return NotImplemented  # type: ignore[return-value]

    def __add__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out = dict(self.coeffs)
        for key, value in rhs.coeffs.items():
            out[key] = out.get(key, 0.0) + value
        return Jet2(self.order, out)

    def __radd__(self, other: object) -> "Jet2":
        return self.__add__(other)

    def __sub__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out = dict(self.coeffs)
        for key, value in rhs.coeffs.items():
            out[key] = out.get(key, 0.0) - value
        return Jet2(self.order, out)

    def __rsub__(self, other: object) -> "Jet2":
        return self._coerce(other).__sub__(self)

    def __neg__(self) -> "Jet2":
        return Jet2(self.order, {key: -value for key, value in self.coeffs.items()})

    def __mul__(self, other: object) -> "Jet2":
        rhs = self._coerce(other)
        out: dict[Index, float] = {}
        for (a1, b1), v1 in self.coeffs.items():
            for (a2, b2), v2 in rhs.coeffs.items():
                key = (a1 + a2, b1 + b2)
                if key[0] + key[1] <= self.order:
                    out[key] = out.get(key, 0.0) + v1 * v2
        return Jet2(self.order, out)

    def __rmul__(self, other: object) -> "Jet2":
        return self.__mul__(other)

    def reciprocal(self) -> "Jet2":
        return self.pow(-1.0)

    def __truediv__(self, other: object) -> "Jet2":
        return self * self._coerce(other).reciprocal()

    def __rtruediv__(self, other: object) -> "Jet2":
        return self._coerce(other) * self.reciprocal()

    def __pow__(self, exponent: object) -> "Jet2":
        if isinstance(exponent, int):
            if exponent == 0:
                return Jet2.const(self.order, 1.0)
            if exponent < 0:
                return (self ** (-exponent)).reciprocal()
            out = Jet2.const(self.order, 1.0)
            for _ in range(exponent):
                out = out * self
            return out
        if isinstance(exponent, float):
            return self.pow(exponent)
        return NotImplemented  # type: ignore[return-value]

    def pow(self, exponent: float) -> "Jet2":
        base = self.value()
        if base <= 0.0:
            raise ValueError("fractional jet power requires positive base")
        h = (self - base) * (1.0 / base)
        out = Jet2.const(self.order, 0.0)
        power = Jet2.const(self.order, 1.0)
        binom = 1.0
        for n in range(self.order + 1):
            if n > 0:
                binom *= (exponent - (n - 1)) / n
            out = out + binom * power
            power = power * h
        return (base**exponent) * out


@dataclass(frozen=True)
class TriangularTaylor:
    """Triangular Taylor polynomial in R and Z."""

    degree: int
    coefficients: tuple[tuple[int, int, float], ...]

    @classmethod
    def from_json(cls, item: dict[str, Any]) -> "TriangularTaylor":
        if not item.get("enabled", False):
            raise ValueError("origin Taylor block is disabled")
        coeffs = tuple(
            (int(entry["R_power"]), int(entry["Z_power"]), float(entry["coeff"]))
            for entry in item.get("basis", [])
        )
        degree = int(item.get("degree", max((a + b for a, b, _c in coeffs), default=0)))
        for a, b, _coeff in coeffs:
            if a < 0 or b < 0:
                raise ValueError("Taylor powers must be nonnegative")
            if a + b > degree:
                raise ValueError("origin Taylor block is not triangular through declared degree")
        return cls(degree=degree, coefficients=coeffs)

    def eval(self, R: float, Z: float) -> float:
        return sum(coeff * (R**a) * (Z**b) for a, b, coeff in self.coefficients)

    def partial(self, R: float, Z: float, dR: int, dZ: int) -> float:
        total = 0.0
        for a, b, coeff in self.coefficients:
            if a >= dR and b >= dZ:
                total += (
                    coeff
                    * falling(a, dR)
                    * falling(b, dZ)
                    * (R ** (a - dR))
                    * (Z ** (b - dZ))
                )
        return total

    def jet(self, R: Jet2, Z: Jet2) -> Jet2:
        out = Jet2.const(R.order, 0.0)
        for a, b, coeff in self.coefficients:
            out = out + coeff * (R ** a) * (Z ** b)
        return out


@dataclass(frozen=True)
class Patch:
    q0: float
    q1: float
    x0: float
    x1: float
    coeffs: ChebTable

    @classmethod
    def from_json(cls, item: dict[str, Any]) -> "Patch":
        q0, q1 = item["q_interval"]
        x0, x1 = item["x_interval"]
        return cls(float(q0), float(q1), float(x0), float(x1), item["coeffs"])


def find_patch(patches: list[Patch], q: float, x: float) -> Patch:
    for patch in patches:
        if patch.q0 - 1e-14 <= q <= patch.q1 + 1e-14 and patch.x0 - 1e-14 <= x <= patch.x1 + 1e-14:
            return patch
    raise ValueError(f"point outside rectangular patches q={q} x={x}")


def cheb_eval_1d_jet(coeffs: list[float], t: Jet2) -> Jet2:
    if not coeffs:
        return Jet2.const(t.order, 0.0)
    b_k2 = Jet2.const(t.order, 0.0)
    b_k1 = Jet2.const(t.order, 0.0)
    for coeff in reversed(coeffs[1:]):
        b_k0 = 2.0 * t * b_k1 - b_k2 + coeff
        b_k2 = b_k1
        b_k1 = b_k0
    return coeffs[0] + t * b_k1 - b_k2


def cheb_eval_tensor_jet(coeffs: ChebTable, q: Jet2, x: Jet2, patch: Patch) -> Jet2:
    tq = (2.0 * q - patch.q0 - patch.q1) / (patch.q1 - patch.q0)
    tx = (2.0 * x - patch.x0 - patch.x1) / (patch.x1 - patch.x0)
    q_values = [cheb_eval_1d_jet(row, tx) for row in coeffs]
    return cheb_eval_1d_jet(q_values, tq)


@dataclass(frozen=True)
class RectangularProjection:
    gamma: float
    B: float
    p: float
    f_an: list[Patch]
    g_an: list[Patch]
    f_frac: list[list[Patch]]
    g_frac: list[list[Patch]]
    f_origin: TriangularTaylor
    g_origin: TriangularTaylor

    @staticmethod
    def _load_patches(items: list[dict[str, Any]]) -> list[Patch]:
        return [Patch.from_json(item) for item in items]

    @classmethod
    def load(cls, path: str) -> "RectangularProjection":
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
            f_origin=TriangularTaylor.from_json(blocks["F_origin_taylor"]),
            g_origin=TriangularTaylor.from_json(blocks["G_origin_taylor"]),
        )

    @staticmethod
    def _eval_patch_jet(patches: list[Patch], q: Jet2, x: Jet2) -> Jet2:
        patch = find_patch(patches, q.value(), x.value())
        return cheb_eval_tensor_jet(patch.coeffs, q, x, patch)

    def rect_total_jet(self, component: str, R0: float, Z0: float, order: int) -> Jet2:
        R = Jet2.var_R(order, R0)
        Z = Jet2.var_Z(order, Z0)
        rho2 = R + Z
        if rho2.value() <= 0.0:
            raise ValueError("rectangular chart is undefined at R+Z=0")
        q = (1.0 + rho2).pow(-0.5)
        x = Z / rho2
        if component == "F":
            value = Jet2.const(order, 0.5) + q * q * self._eval_patch_jet(self.f_an, q, x)
            for k, patches in enumerate(self.f_frac, start=1):
                value = value + q.pow(k * self.p) * self._eval_patch_jet(patches, q, x)
            return value
        if component == "G":
            value = Jet2.const(order, self.B) + q * q * self._eval_patch_jet(self.g_an, q, x)
            for k, patches in enumerate(self.g_frac, start=1):
                value = value + q.pow(k * self.p) * self._eval_patch_jet(patches, q, x)
            return value
        raise ValueError("component must be F or G")

    def origin_total_jet(self, component: str, R0: float, Z0: float, order: int) -> Jet2:
        R = Jet2.var_R(order, R0)
        Z = Jet2.var_Z(order, Z0)
        if component == "F":
            return self.f_origin.jet(R, Z)
        if component == "G":
            return self.g_origin.jet(R, Z)
        raise ValueError("component must be F or G")


def consistency_diagnostics(
    projection: RectangularProjection,
    q_values: list[float],
    x_values: list[float],
    derivative_order: int,
    tolerance: float,
) -> dict[str, Any]:
    if derivative_order < 0:
        raise ValueError("derivative_order must be nonnegative")
    indices = derivative_indices(derivative_order)
    component_reports: dict[str, Any] = {}
    global_max = 0.0
    for component in ("F", "G"):
        worst: dict[str, Any] = {"abs_diff": -1.0}
        total = 0.0
        count = 0
        failures: list[dict[str, Any]] = []
        for q in q_values:
            for x in x_values:
                R0, Z0 = qx_to_rz(q, x)
                try:
                    rect = projection.rect_total_jet(component, R0, Z0, derivative_order)
                    origin = projection.origin_total_jet(component, R0, Z0, derivative_order)
                except Exception as exc:  # pragma: no cover - reported through CLI
                    failures.append({"q": q, "x": x, "R": R0, "Z": Z0, "error": str(exc)})
                    continue
                for dR, dZ in indices:
                    rect_value = rect.partial(dR, dZ)
                    origin_value = origin.partial(dR, dZ)
                    diff = origin_value - rect_value
                    abs_diff = abs(diff)
                    total += diff * diff
                    count += 1
                    if abs_diff > worst["abs_diff"]:
                        worst = {
                            "component": component,
                            "q": q,
                            "x": x,
                            "R": R0,
                            "Z": Z0,
                            "dR": dR,
                            "dZ": dZ,
                            "origin": origin_value,
                            "rectangular": rect_value,
                            "diff": diff,
                            "abs_diff": abs_diff,
                        }
        max_abs = max(0.0, float(worst["abs_diff"]))
        global_max = max(global_max, max_abs)
        component_reports[component] = {
            "sampled_rows": count,
            "evaluation_failures": failures,
            "max_abs_diff": max_abs,
            "rms_diff": math.sqrt(total / max(count, 1)),
            "worst": worst,
            "ok": not failures and max_abs <= tolerance,
        }
    all_ok = all(item["ok"] for item in component_reports.values())
    return {
        "status": "RECT_ORIGIN_CONSISTENCY_OK_NOT_INTERVAL"
        if all_ok
        else "RECT_ORIGIN_CONSISTENCY_FAIL_NOT_INTERVAL",
        "gate_status": "DIAGNOSTIC_ONLY_NO_INTERVAL_OR_PROOF_CLAIM",
        "derivative_order": derivative_order,
        "tolerance": tolerance,
        "q_values": q_values,
        "x_values": x_values,
        "max_abs_diff": global_max,
        "components": component_reports,
    }


def polynomial_via_qx_jet(coeffs: tuple[tuple[int, int, float], ...], R0: float, Z0: float, order: int) -> Jet2:
    R = Jet2.var_R(order, R0)
    Z = Jet2.var_Z(order, Z0)
    rho2 = R + Z
    q = (1.0 + rho2).pow(-0.5)
    x = Z / rho2
    rho2_back = (q ** -2) - 1.0
    R_back = rho2_back * (1.0 - x)
    Z_back = rho2_back * x
    out = Jet2.const(order, 0.0)
    for a, b, coeff in coeffs:
        out = out + coeff * (R_back ** a) * (Z_back ** b)
    return out


def fake_smooth_x_jet(R0: float, Z0: float, order: int) -> Jet2:
    R = Jet2.var_R(order, R0)
    Z = Jet2.var_Z(order, Z0)
    return Z / (R + Z)


def self_test(derivative_order: int = 4, tolerance: float = 1e-10) -> dict[str, Any]:
    coeffs = (
        (0, 0, 1.25),
        (1, 0, -0.75),
        (0, 1, 0.5),
        (2, 0, 0.125),
        (1, 1, -0.375),
        (0, 2, 0.25),
        (3, 1, 0.03125),
    )
    origin = TriangularTaylor(degree=4, coefficients=coeffs)
    indices = derivative_indices(derivative_order)
    chart_worst: dict[str, Any] = {"abs_diff": -1.0}
    for q in (0.84, 0.88, 0.92):
        for x in (0.1, 0.35, 0.7, 0.95):
            R0, Z0 = qx_to_rz(q, x)
            direct = origin.jet(Jet2.var_R(derivative_order, R0), Jet2.var_Z(derivative_order, Z0))
            via_qx = polynomial_via_qx_jet(coeffs, R0, Z0, derivative_order)
            for dR, dZ in indices:
                diff = direct.partial(dR, dZ) - via_qx.partial(dR, dZ)
                if abs(diff) > chart_worst["abs_diff"]:
                    chart_worst = {
                        "q": q,
                        "x": x,
                        "R": R0,
                        "Z": Z0,
                        "dR": dR,
                        "dZ": dZ,
                        "diff": diff,
                        "abs_diff": abs(diff),
                    }

    ray_x = (0.0, 0.25, 0.5, 0.75, 1.0)
    rho2 = 1e-8
    ray_values = []
    for x in ray_x:
        R0 = rho2 * (1.0 - x)
        Z0 = rho2 * x
        ray_values.append(fake_smooth_x_jet(R0, Z0, 1).value())
    ray_spread = max(ray_values) - min(ray_values)
    derivative_scale_1 = abs(fake_smooth_x_jet(0.5e-6, 0.5e-6, 1).partial(1, 0))
    derivative_scale_2 = abs(fake_smooth_x_jet(0.5e-7, 0.5e-7, 1).partial(1, 0))
    derivative_growth = derivative_scale_2 / max(derivative_scale_1, 1e-300)
    fake_rejected = ray_spread > 0.5 and derivative_growth > 5.0
    chart_ok = float(chart_worst["abs_diff"]) <= tolerance
    all_ok = chart_ok and fake_rejected
    return {
        "status": "ORIGIN_CHART_SELFTEST_OK_NOT_INTERVAL" if all_ok else "ORIGIN_CHART_SELFTEST_FAIL",
        "gate_status": "SELFTEST_ONLY_NO_INTERVAL_OR_PROOF_CLAIM",
        "derivative_order": derivative_order,
        "tolerance": tolerance,
        "triangular_polynomial_chart_consistency": {
            "ok": chart_ok,
            "max_abs_diff": chart_worst["abs_diff"],
            "worst": chart_worst,
        },
        "fake_smooth_rejection": {
            "ok": fake_rejected,
            "function": "H(q,x)=x=Z/(R+Z)",
            "ray_x": list(ray_x),
            "ray_values_at_rho2_1e_minus_8": ray_values,
            "ray_spread": ray_spread,
            "dR_abs_at_rho2_1e_minus_6_x_1_2": derivative_scale_1,
            "dR_abs_at_rho2_1e_minus_7_x_1_2": derivative_scale_2,
            "derivative_growth": derivative_growth,
            "rejection_reason": "ray-dependent origin limit and derivative growth in R,Z",
        },
    }


def write_report(path: str, report: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")


def print_report_summary(report: dict[str, Any]) -> None:
    print(f"status={report['status']}")
    print(f"gate_status={report['gate_status']}")
    if "max_abs_diff" in report:
        print(f"max_abs_diff={float(report['max_abs_diff']):.12e}")
        for component, item in report["components"].items():
            print(
                f"{component}: rows={item['sampled_rows']} "
                f"max_abs_diff={float(item['max_abs_diff']):.12e} "
                f"rms={float(item['rms_diff']):.12e} ok={item['ok']}"
            )
    if "triangular_polynomial_chart_consistency" in report:
        chart = report["triangular_polynomial_chart_consistency"]
        fake = report["fake_smooth_rejection"]
        print(f"chart_consistency_max_abs_diff={float(chart['max_abs_diff']):.12e}")
        print(f"fake_smooth_rejected={fake['ok']} ray_spread={float(fake['ray_spread']):.12e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="", help="transseries_cheb_projection_v1 JSON profile to diagnose")
    parser.add_argument("--self-test", action="store_true", help="run built-in origin chart self-test")
    parser.add_argument("--out", default="", help="optional JSON report path")
    parser.add_argument("--derivative-order", type=int, default=2)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--q-values", default="0.9")
    parser.add_argument("--x-values", default="0.05,0.25,0.5,0.75,0.95")
    args = parser.parse_args()

    reports: dict[str, Any] = {
        "status": "ORIGIN_CHART_DIAGNOSTICS_NOT_INTERVAL_VALIDATION",
        "gate_status": "DIAGNOSTIC_ONLY_NO_INTERVAL_OR_PROOF_CLAIM",
    }
    if args.self_test:
        reports["self_test"] = self_test(args.derivative_order, args.tolerance)
    if args.profile:
        projection = RectangularProjection.load(args.profile)
        q_values = parse_values(args.q_values, [0.9])
        x_values = parse_values(args.x_values, [0.05, 0.25, 0.5, 0.75, 0.95])
        reports["profile"] = args.profile
        reports["consistency"] = consistency_diagnostics(
            projection=projection,
            q_values=q_values,
            x_values=x_values,
            derivative_order=args.derivative_order,
            tolerance=args.tolerance,
        )
    if not args.self_test and not args.profile:
        reports["self_test"] = self_test(args.derivative_order, args.tolerance)

    if args.out:
        write_report(args.out, reports)
        print(f"saved={args.out}")
    if "self_test" in reports:
        print("self_test:")
        print_report_summary(reports["self_test"])
    if "consistency" in reports:
        print("consistency:")
        print_report_summary(reports["consistency"])


if __name__ == "__main__":
    main()
