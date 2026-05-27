#!/usr/bin/env python3
"""Floating two-chart overlap mortar residual/Jacobian rows.

This is a diagnostic builder for ``twochart_profile_projection_v1`` artifacts.
It compares tail total F/G against origin total F/G on the overlap in
``(q, x)`` coordinates and emits exact floating sparse Jacobian entries with
respect to the JSON coefficients.  It is not an interval proof and does not
certify smoothness or existence.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.origin_chart import (  # noqa: E402
    Jet2 as RZJet2,
    Patch as RZPatch,
    cheb_eval_tensor_jet as cheb_eval_tensor_rz_jet,
    derivative_indices as rz_derivative_indices,
    qx_to_rz,
)

STATUS = "TWOCHART_MORTAR_JACOBIAN_FLOATING_NOT_PROOF"
SUPPORTED_FORMAT = "twochart_profile_projection_v1"

_NATIVE_C_LIB: ctypes.CDLL | None = None
_NATIVE_C_BUILD_DIR: tempfile.TemporaryDirectory[str] | None = None
_NATIVE_C_RZ_STATS: dict[str, Any] = {
    "enabled": False,
    "available": False,
    "calls": 0,
    "cases": 0,
    "seconds": 0.0,
    "compile_seconds": 0.0,
}


@dataclass(frozen=True)
class DerivativeSpec:
    dq_order: int
    dx_order: int

    @property
    def total_order(self) -> int:
        return self.dq_order + self.dx_order

    @property
    def label(self) -> str:
        if self.total_order == 0:
            return "value"
        return "d" + ("q" * self.dq_order) + ("x" * self.dx_order)


@dataclass(frozen=True)
class CoefficientVariable:
    index: int
    chart: str
    component: str
    block: str
    path: tuple[Any, ...]
    label: str
    value: float
    alpha: float | None = None
    patch_index: int | None = None
    frac_index: int | None = None
    kq: int | None = None
    kx: int | None = None
    r_power: int | None = None
    z_power: int | None = None

    def as_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "index": self.index,
            "chart": self.chart,
            "component": self.component,
            "block": self.block,
            "path": list(self.path),
            "label": self.label,
            "value": self.value,
        }
        for key in ("alpha", "patch_index", "frac_index", "kq", "kx", "r_power", "z_power"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        return out


@dataclass(frozen=True)
class MortarRow:
    row_index: int
    component: str
    q: float
    x: float
    dq_order: int
    dx_order: int
    tail_value: float
    origin_value: float
    residual: float
    jacobian: tuple[tuple[int, float], ...]
    coordinate: str = "qx"

    @property
    def derivative(self) -> DerivativeSpec:
        return DerivativeSpec(self.dq_order, self.dx_order)

    @property
    def derivative_label(self) -> str:
        if self.coordinate == "RZ":
            if self.dq_order + self.dx_order == 0:
                return "value"
            return "d" + ("R" * self.dq_order) + ("Z" * self.dx_order)
        return self.derivative.label

    @property
    def abs_residual(self) -> float:
        return abs(self.residual)

    def as_json(self, variables: list[CoefficientVariable] | None = None) -> dict[str, Any]:
        if variables is None:
            jacobian: list[dict[str, Any]] = [
                {"var_index": var_index, "value": value} for var_index, value in self.jacobian
            ]
        else:
            jacobian = [
                {
                    "var_index": var_index,
                    "variable": variables[var_index].label,
                    "value": value,
                }
                for var_index, value in self.jacobian
            ]
        return {
            "row_index": self.row_index,
            "component": self.component,
            "coordinate": self.coordinate,
            "q": self.q,
            "x": self.x,
            "derivative": self.derivative_label,
            "dq_order": self.dq_order,
            "dx_order": self.dx_order,
            "total_order": self.dq_order + self.dx_order,
            "tail_value": self.tail_value,
            "origin_value": self.origin_value,
            "residual_tail_minus_origin": self.residual,
            "abs_residual": self.abs_residual,
            "jacobian_nnz": len(self.jacobian),
            "jacobian": jacobian,
        }


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != SUPPORTED_FORMAT:
        raise ValueError(f"{path!r} has format={data.get('format')!r}; expected {SUPPORTED_FORMAT!r}")
    enforce_tail_gate(data, path)
    return data


def enforce_tail_gate(data: dict[str, Any], profile: str) -> None:
    tail = data.get("tail_legality")
    if not isinstance(tail, dict):
        raise ValueError(f"{profile!r} is missing tail_legality")
    if tail.get("all_ok") is not True:
        raise ValueError(f"{profile!r} tail_legality.all_ok is not true: status={tail.get('status')!r}")
    if tail.get("q2_policy") != "zero" or tail.get("q2_ok") is not True:
        raise ValueError(
            f"{profile!r} must have q2_policy=zero and q2_ok=true; "
            f"got q2_policy={tail.get('q2_policy')!r} q2_ok={tail.get('q2_ok')!r}"
        )


def save_json(path: str, data: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def grid(lo: float, hi: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("sample count must be positive")
    if count == 1:
        return [(lo + hi) / 2.0]
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def derivative_specs(max_order: int) -> tuple[DerivativeSpec, ...]:
    if max_order < 0 or max_order > 4:
        raise ValueError("--max-order must be between 0 and 4")
    return tuple(
        DerivativeSpec(dq_order=dq, dx_order=total - dq)
        for total in range(max_order + 1)
        for dq in range(total + 1)
    )


def falling(value: float, order: int) -> float:
    out = 1.0
    for k in range(order):
        out *= value - k
    return out


def binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def patch_interval(patch: dict[str, Any]) -> tuple[float, float, float, float]:
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    return float(q0), float(q1), float(x0), float(x1)


def find_patch_index(patches: list[dict[str, Any]], q: float, x: float) -> int:
    for index, patch in enumerate(patches):
        q0, q1, x0, x1 = patch_interval(patch)
        if q0 - 1e-14 <= q <= q1 + 1e-14 and x0 - 1e-14 <= x <= x1 + 1e-14:
            return index
    raise ValueError(f"point outside patch inventory: q={q} x={x}")


def cheb_basis_values(count: int, t: float, order: int) -> list[float]:
    if order < 0 or order > 4:
        raise ValueError("Chebyshev derivative order must be between 0 and 4")
    if count <= 0:
        return []
    derivs = [[0.0 for _ in range(count)] for _ in range(order + 1)]
    derivs[0][0] = 1.0
    if count > 1:
        derivs[0][1] = t
        if order >= 1:
            derivs[1][1] = 1.0
    for n in range(2, count):
        for m in range(order + 1):
            value = 2.0 * t * derivs[m][n - 1] - derivs[m][n - 2]
            if m > 0:
                value += 2.0 * m * derivs[m - 1][n - 1]
            derivs[m][n] = value
    return derivs[order]


def cheb_basis_partial(
    patch: dict[str, Any],
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    q0, q1, x0, x1 = patch_interval(patch)
    if q1 == q0 or x1 == x0:
        raise ValueError("cannot differentiate degenerate Chebyshev patch")
    tq = (2.0 * q - q0 - q1) / (q1 - q0)
    tx = (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = cheb_basis_values(kq + 1, tq, dq_order)
    x_values = cheb_basis_values(kx + 1, tx, dx_order)
    return (
        q_values[kq]
        * x_values[kx]
        * ((2.0 / (q1 - q0)) ** dq_order)
        * ((2.0 / (x1 - x0)) ** dx_order)
    )


def cheb_eval_tensor_partial(
    patch: dict[str, Any],
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    coeffs = patch["coeffs"]
    total = 0.0
    for kq, row in enumerate(coeffs):
        for kx, coeff in enumerate(row):
            total += float(coeff) * cheb_basis_partial(patch, q, x, kq, kx, dq_order, dx_order)
    return total


def weighted_patch_partial(
    patch: dict[str, Any],
    alpha: float,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    total = 0.0
    for i in range(dq_order + 1):
        q_weight = falling(alpha, i) * (q ** (alpha - i))
        patch_partial = cheb_eval_tensor_partial(patch, q, x, dq_order - i, dx_order)
        total += binom(dq_order, i) * q_weight * patch_partial
    return total


def weighted_cheb_coeff_partial(
    patch: dict[str, Any],
    alpha: float,
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    total = 0.0
    for i in range(dq_order + 1):
        q_weight = falling(alpha, i) * (q ** (alpha - i))
        basis_partial = cheb_basis_partial(patch, q, x, kq, kx, dq_order - i, dx_order)
        total += binom(dq_order, i) * q_weight * basis_partial
    return total


def origin_h_partial(power: int, q: float, order: int) -> float:
    if power == 0:
        return 1.0 if order == 0 else 0.0
    total = 0.0
    for k in range(power + 1):
        coeff = binom(power, k) * ((-1.0) ** (power - k))
        exponent = -2.0 * k
        total += coeff * falling(exponent, order) * (q ** (exponent - order))
    return total


def origin_x_partial(r_power: int, z_power: int, x: float, order: int) -> float:
    total = 0.0
    for i in range(order + 1):
        j = order - i
        if i > r_power or j > z_power:
            continue
        left = ((-1.0) ** i) * falling(float(r_power), i) * ((1.0 - x) ** (r_power - i))
        right = falling(float(z_power), j) * (x ** (z_power - j))
        total += binom(order, i) * left * right
    return total


def origin_coeff_partial(
    r_power: int,
    z_power: int,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    return origin_h_partial(r_power + z_power, q, dq_order) * origin_x_partial(
        r_power, z_power, x, dx_order
    )


def rz_coordinate_jets(R0: float, Z0: float, order: int) -> tuple[RZJet2, RZJet2, RZJet2, RZJet2]:
    R = RZJet2.var_R(order, R0)
    Z = RZJet2.var_Z(order, Z0)
    rho2 = R + Z
    if rho2.value() <= 0.0:
        raise ValueError("R,Z mortar rows are undefined at R+Z=0")
    q = (1.0 + rho2).pow(-0.5)
    x = Z / rho2
    return R, Z, q, x


def one_hot_coeffs(patch: dict[str, Any], kq: int, kx: int) -> list[list[float]]:
    coeffs = patch["coeffs"]
    return [
        [1.0 if iq == kq and ix == kx else 0.0 for ix, _value in enumerate(row)]
        for iq, row in enumerate(coeffs)
    ]


def weighted_patch_rz_jet(patch: dict[str, Any], alpha: float, q: RZJet2, x: RZJet2) -> RZJet2:
    return q.pow(alpha) * cheb_eval_tensor_rz_jet(patch["coeffs"], q, x, RZPatch.from_json(patch))


def weighted_coeff_rz_jet(
    patch: dict[str, Any],
    alpha: float,
    q: RZJet2,
    x: RZJet2,
    kq: int,
    kx: int,
) -> RZJet2:
    coeffs = one_hot_coeffs(patch, kq, kx)
    return q.pow(alpha) * cheb_eval_tensor_rz_jet(coeffs, q, x, RZPatch.from_json(patch))


def tail_total_rz_jet(data: dict[str, Any], component: str, R0: float, Z0: float, order: int) -> RZJet2:
    _R, _Z, q, x = rz_coordinate_jets(R0, Z0, order)
    blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])
    if component == "F":
        total = RZJet2.const(order, 0.5)
        analytic_block = "F_an"
        frac_block = "F_frac"
    elif component == "G":
        total = RZJet2.const(order, float(data["B"]))
        analytic_block = "G_an"
        frac_block = "G_frac"
    else:
        raise ValueError(f"unknown component {component!r}")
    analytic_patch = blocks[analytic_block][find_patch_index(blocks[analytic_block], q.value(), x.value())]
    total = total + weighted_patch_rz_jet(analytic_patch, 2.0, q, x)
    for frac_index, frac_patches in enumerate(blocks.get(frac_block, []), start=1):
        frac_patch = frac_patches[find_patch_index(frac_patches, q.value(), x.value())]
        total = total + weighted_patch_rz_jet(frac_patch, frac_index * p, q, x)
    return total


def origin_total_rz_jet(data: dict[str, Any], component: str, R0: float, Z0: float, order: int) -> RZJet2:
    R, Z, _q, _x = rz_coordinate_jets(R0, Z0, order)
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    total = RZJet2.const(order, 0.0)
    for entry in data["origin_chart"]["blocks"][key].get("basis", []):
        total = total + float(entry["coeff"]) * (R ** int(entry["R_power"])) * (Z ** int(entry["Z_power"]))
    return total


def variable_tail_patch(data: dict[str, Any], variable: CoefficientVariable) -> dict[str, Any]:
    blocks = data["tail_chart"]["blocks"]
    if variable.frac_index is None:
        return blocks[variable.block][variable.patch_index]
    return blocks[variable.block][variable.frac_index - 1][variable.patch_index]


def point_in_patch(patch: dict[str, Any], q: float, x: float) -> bool:
    q0, q1, x0, x1 = patch_interval(patch)
    return q0 - 1e-14 <= q <= q1 + 1e-14 and x0 - 1e-14 <= x <= x1 + 1e-14


def variable_rz_residual_jet(
    data: dict[str, Any],
    variable: CoefficientVariable,
    component: str,
    R0: float,
    Z0: float,
    order: int,
) -> RZJet2:
    if variable.component != component:
        return RZJet2.const(order, 0.0)
    R, Z, q, x = rz_coordinate_jets(R0, Z0, order)
    if variable.chart == "tail":
        patch = variable_tail_patch(data, variable)
        if not point_in_patch(patch, q.value(), x.value()):
            return RZJet2.const(order, 0.0)
        return weighted_coeff_rz_jet(
            patch,
            float(variable.alpha),
            q,
            x,
            int(variable.kq),
            int(variable.kx),
        )
    if variable.chart == "origin":
        return -((R ** int(variable.r_power)) * (Z ** int(variable.z_power)))
    return RZJet2.const(order, 0.0)


def _native_c_library() -> ctypes.CDLL:
    global _NATIVE_C_LIB
    global _NATIVE_C_BUILD_DIR
    if _NATIVE_C_LIB is not None:
        return _NATIVE_C_LIB

    clang = shutil.which("clang")
    if clang is None:
        raise RuntimeError("clang not found; cannot build native C kernel")
    src = Path(ROOT_DIR) / "native" / "c" / "nsproof_kernel.c"
    if not src.exists():
        raise RuntimeError(f"native C source not found: {src}")

    start = time.perf_counter()
    _NATIVE_C_BUILD_DIR = tempfile.TemporaryDirectory(prefix="nsproof-native-c-")
    lib_path = Path(_NATIVE_C_BUILD_DIR.name) / (
        "libnsproof_kernel.dylib" if platform.system() == "Darwin" else "libnsproof_kernel.so"
    )
    cmd = [clang, "-O3", "-std=c99", "-Wall", "-Wextra", "-pedantic", "-fPIC"]
    if platform.system() == "Darwin":
        cmd.append("-dynamiclib")
    else:
        cmd.append("-shared")
    cmd.extend([str(src), "-o", str(lib_path)])
    if platform.system() != "Darwin":
        cmd.append("-lm")
    subprocess.run(cmd, check=True, cwd=ROOT_DIR)

    lib = ctypes.CDLL(str(lib_path))
    c_double_p = ctypes.POINTER(ctypes.c_double)
    c_int_p = ctypes.POINTER(ctypes.c_int)
    for name in ("add", "sub", "mul"):
        fn = getattr(lib, f"nsproof_interval_{name}_batch")
        fn.argtypes = [
            ctypes.c_int,
            c_double_p,
            c_double_p,
            c_double_p,
            c_double_p,
            c_double_p,
            c_double_p,
            c_int_p,
        ]
        fn.restype = ctypes.c_int
    lib.nsproof_interval_recip_batch.argtypes = [
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_interval_recip_batch.restype = ctypes.c_int
    lib.nsproof_interval_poly_eval_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_interval_poly_eval_batch.restype = ctypes.c_int
    lib.nsproof_bernstein_range_batch.argtypes = [
        ctypes.c_int,
        c_int_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_bernstein_range_batch.restype = ctypes.c_int
    lib.nsproof_interval_matvec_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_interval_matvec_batch.restype = ctypes.c_int
    lib.nsproof_interval_vector_inf_norm.argtypes = [
        ctypes.c_int,
        c_double_p,
        c_double_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_vector_inf_norm.restype = ctypes.c_int
    lib.nsproof_interval_matrix_inf_norm.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_matrix_inf_norm.restype = ctypes.c_int
    lib.nsproof_interval_matvec_inf_norm.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_matvec_inf_norm.restype = ctypes.c_int
    lib.nsproof_interval_left_matmul_identity_defect_inf_norm.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.nsproof_interval_left_matmul_identity_defect_inf_norm.restype = ctypes.c_int
    lib.nsproof_rz_weighted_coeff_partials_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_rz_weighted_coeff_partials_batch.restype = ctypes.c_int
    lib.nsproof_pde_tail_coeff_columns_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_pde_tail_coeff_columns_batch.restype = ctypes.c_int
    lib.nsproof_stage0_prediction_scan_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_stage0_prediction_scan_batch.restype = ctypes.c_int
    lib.nsproof_tail_exact_residual.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_tail_exact_residual.restype = ctypes.c_int
    lib.nsproof_tail_exact_residual_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        c_double_p,
        c_double_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_tail_exact_residual_batch.restype = ctypes.c_int
    lib.nsproof_rz_mortar_residual_terms_batch.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
        c_int_p,
    ]
    lib.nsproof_rz_mortar_residual_terms_batch.restype = ctypes.c_int
    _NATIVE_C_LIB = lib
    _NATIVE_C_RZ_STATS["available"] = True
    _NATIVE_C_RZ_STATS["compile_seconds"] += time.perf_counter() - start
    return lib


def native_c_library() -> ctypes.CDLL:
    return _native_c_library()


def native_c_rz_stats() -> dict[str, Any]:
    return dict(_NATIVE_C_RZ_STATS)


def reset_native_c_rz_stats() -> None:
    _NATIVE_C_RZ_STATS.update(
        {
            "enabled": False,
            "available": _NATIVE_C_LIB is not None,
            "calls": 0,
            "cases": 0,
            "seconds": 0.0,
            "compile_seconds": _NATIVE_C_RZ_STATS.get("compile_seconds", 0.0),
        }
    )


def _origin_rz_residual_partial(variable: CoefficientVariable, R0: float, Z0: float, dR: int, dZ: int) -> float:
    r_power = int(variable.r_power)
    z_power = int(variable.z_power)
    if dR > r_power or dZ > z_power:
        return 0.0
    return -(
        falling(float(r_power), dR)
        * falling(float(z_power), dZ)
        * (R0 ** (r_power - dR))
        * (Z0 ** (z_power - dZ))
    )


def _native_rz_tail_partials(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    component: str,
    q: float,
    x: float,
    max_order: int,
) -> dict[int, tuple[float, ...]]:
    cases: list[tuple[CoefficientVariable, tuple[float, float, float, float]]] = []
    for variable in variables:
        if variable.component != component or variable.chart != "tail":
            continue
        patch = variable_tail_patch(data, variable)
        if point_in_patch(patch, q, x):
            cases.append((variable, patch_interval(patch)))
    if not cases:
        return {}

    lib = _native_c_library()
    count = len(cases)
    spec_count = len(rz_derivative_indices(max_order))
    double_array = ctypes.c_double * count
    int_array = ctypes.c_int * count
    q_values = double_array(*([float(q)] * count))
    x_values = double_array(*([float(x)] * count))
    q0_values = double_array(*[interval[0] for _variable, interval in cases])
    q1_values = double_array(*[interval[1] for _variable, interval in cases])
    x0_values = double_array(*[interval[2] for _variable, interval in cases])
    x1_values = double_array(*[interval[3] for _variable, interval in cases])
    alpha_values = double_array(*[float(variable.alpha) for variable, _interval in cases])
    kq_values = int_array(*[int(variable.kq) for variable, _interval in cases])
    kx_values = int_array(*[int(variable.kx) for variable, _interval in cases])
    out = (ctypes.c_double * (count * spec_count))()
    statuses = int_array()

    start = time.perf_counter()
    rc = lib.nsproof_rz_weighted_coeff_partials_batch(
        count,
        max_order,
        q_values,
        x_values,
        q0_values,
        q1_values,
        x0_values,
        x1_values,
        alpha_values,
        kq_values,
        kx_values,
        out,
        statuses,
    )
    elapsed = time.perf_counter() - start
    _NATIVE_C_RZ_STATS["enabled"] = True
    _NATIVE_C_RZ_STATS["calls"] = int(_NATIVE_C_RZ_STATS.get("calls", 0)) + 1
    _NATIVE_C_RZ_STATS["cases"] = int(_NATIVE_C_RZ_STATS.get("cases", 0)) + count
    _NATIVE_C_RZ_STATS["seconds"] = float(_NATIVE_C_RZ_STATS.get("seconds", 0.0)) + elapsed
    if rc != 0:
        bad_statuses = sorted(set(int(statuses[index]) for index in range(count)))
        raise RuntimeError(f"native C RZ weighted partial batch failed rc={rc} statuses={bad_statuses}")

    return {
        variable.index: tuple(float(out[row * spec_count + col]) for col in range(spec_count))
        for row, (variable, _interval) in enumerate(cases)
    }


def _append_native_tail_residual_terms(
    terms: list[dict[str, Any]],
    data: dict[str, Any],
    row_index: int,
    component: str,
    q: float,
    x: float,
) -> None:
    blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])
    if component == "F":
        analytic_block = "F_an"
        frac_block = "F_frac"
    elif component == "G":
        analytic_block = "G_an"
        frac_block = "G_frac"
    else:
        raise ValueError(f"unknown component {component!r}")

    def add_patch_terms(patch: dict[str, Any], alpha: float) -> None:
        q0, q1, x0, x1 = patch_interval(patch)
        for kq, coeff_row in enumerate(patch.get("coeffs", [])):
            for kx, raw_coeff in enumerate(coeff_row):
                coeff = float(raw_coeff)
                if coeff == 0.0:
                    continue
                terms.append(
                    {
                        "row": row_index,
                        "kind": 0,
                        "coeff": coeff,
                        "q0": q0,
                        "q1": q1,
                        "x0": x0,
                        "x1": x1,
                        "alpha": alpha,
                        "kq": kq,
                        "kx": kx,
                        "r_power": 0,
                        "z_power": 0,
                    }
                )

    analytic_patches = blocks[analytic_block]
    add_patch_terms(analytic_patches[find_patch_index(analytic_patches, q, x)], 2.0)
    for frac_index, frac_patches in enumerate(blocks.get(frac_block, []), start=1):
        add_patch_terms(frac_patches[find_patch_index(frac_patches, q, x)], frac_index * p)


def _append_native_origin_residual_terms(
    terms: list[dict[str, Any]],
    data: dict[str, Any],
    row_index: int,
    component: str,
) -> None:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    for entry in data["origin_chart"]["blocks"][key].get("basis", []):
        coeff = float(entry["coeff"])
        if coeff == 0.0:
            continue
        terms.append(
            {
                "row": row_index,
                "kind": 1,
                "coeff": coeff,
                "q0": 0.0,
                "q1": 1.0,
                "x0": 0.0,
                "x1": 1.0,
                "alpha": 0.0,
                "kq": 0,
                "kx": 0,
                "r_power": int(entry["R_power"]),
                "z_power": int(entry["Z_power"]),
            }
        )


def native_rz_residuals_for_rows(data: dict[str, Any], rows: list[MortarRow]) -> tuple[list[float], dict[str, Any]]:
    if not rows:
        return [], {"enabled": True, "cases": 0, "seconds": 0.0}
    if any(row.coordinate != "RZ" for row in rows):
        raise ValueError("native R/Z mortar residual batch requires only RZ rows")

    terms: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        _append_native_tail_residual_terms(terms, data, row_index, row.component, row.q, row.x)
        _append_native_origin_residual_terms(terms, data, row_index, row.component)

    lib = _native_c_library()
    row_count = len(rows)
    term_count = len(terms)
    double_rows = ctypes.c_double * max(row_count, 1)
    int_rows = ctypes.c_int * max(row_count, 1)
    double_terms = ctypes.c_double * max(term_count, 1)
    int_terms = ctypes.c_int * max(term_count, 1)

    row_q = double_rows(*([float(row.q) for row in rows] or [0.0]))
    row_x = double_rows(*([float(row.x) for row in rows] or [0.0]))
    row_dR = int_rows(*([int(row.dq_order) for row in rows] or [0]))
    row_dZ = int_rows(*([int(row.dx_order) for row in rows] or [0]))
    row_component = int_rows(*([0 if row.component == "F" else 1 for row in rows] or [0]))

    term_row = int_terms(*([int(term["row"]) for term in terms] or [0]))
    term_kind = int_terms(*([int(term["kind"]) for term in terms] or [0]))
    coeff = double_terms(*([float(term["coeff"]) for term in terms] or [0.0]))
    q0_values = double_terms(*([float(term["q0"]) for term in terms] or [0.0]))
    q1_values = double_terms(*([float(term["q1"]) for term in terms] or [1.0]))
    x0_values = double_terms(*([float(term["x0"]) for term in terms] or [0.0]))
    x1_values = double_terms(*([float(term["x1"]) for term in terms] or [1.0]))
    alpha_values = double_terms(*([float(term["alpha"]) for term in terms] or [0.0]))
    kq_values = int_terms(*([int(term["kq"]) for term in terms] or [0]))
    kx_values = int_terms(*([int(term["kx"]) for term in terms] or [0]))
    r_power_values = int_terms(*([int(term["r_power"]) for term in terms] or [0]))
    z_power_values = int_terms(*([int(term["z_power"]) for term in terms] or [0]))
    out = double_rows()
    statuses = int_terms()

    start = time.perf_counter()
    rc = lib.nsproof_rz_mortar_residual_terms_batch(
        row_count,
        term_count,
        float(data["B"]),
        row_q,
        row_x,
        row_dR,
        row_dZ,
        row_component,
        term_row,
        term_kind,
        coeff,
        q0_values,
        q1_values,
        x0_values,
        x1_values,
        alpha_values,
        kq_values,
        kx_values,
        r_power_values,
        z_power_values,
        out,
        statuses,
    )
    elapsed = time.perf_counter() - start
    _NATIVE_C_RZ_STATS["enabled"] = True
    _NATIVE_C_RZ_STATS["calls"] = int(_NATIVE_C_RZ_STATS.get("calls", 0)) + 1
    _NATIVE_C_RZ_STATS["cases"] = int(_NATIVE_C_RZ_STATS.get("cases", 0)) + term_count
    _NATIVE_C_RZ_STATS["seconds"] = float(_NATIVE_C_RZ_STATS.get("seconds", 0.0)) + elapsed
    if rc != 0:
        bad_statuses = sorted(set(int(statuses[index]) for index in range(term_count)))
        raise RuntimeError(f"native C RZ mortar residual batch failed rc={rc} statuses={bad_statuses}")
    return [float(out[index]) for index in range(row_count)], {
        "enabled": True,
        "rows": row_count,
        "cases": term_count,
        "seconds": elapsed,
    }


def residuals_for_rows(
    data: dict[str, Any],
    rows: list[MortarRow],
    use_native_c: bool = False,
) -> tuple[list[float], dict[str, Any]]:
    if use_native_c and rows and all(row.coordinate == "RZ" for row in rows):
        return native_rz_residuals_for_rows(data, rows)
    return [float(residual_for_row(data, row)) for row in rows], {
        "enabled": bool(use_native_c),
        "rows": len(rows),
        "cases": 0,
        "seconds": 0.0,
        "fallback": "python",
    }


def tail_total_partial(
    data: dict[str, Any],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])
    if component == "F":
        constant = 0.5
        analytic_block = "F_an"
        frac_block = "F_frac"
    elif component == "G":
        constant = float(data["B"])
        analytic_block = "G_an"
        frac_block = "G_frac"
    else:
        raise ValueError(f"unknown component {component!r}")
    total = constant if dq_order == 0 and dx_order == 0 else 0.0
    analytic_patches = blocks[analytic_block]
    analytic_patch = analytic_patches[find_patch_index(analytic_patches, q, x)]
    total += weighted_patch_partial(analytic_patch, 2.0, q, x, dq_order, dx_order)
    for frac_index, frac_patches in enumerate(blocks.get(frac_block, []), start=1):
        frac_patch = frac_patches[find_patch_index(frac_patches, q, x)]
        total += weighted_patch_partial(frac_patch, frac_index * p, q, x, dq_order, dx_order)
    return total


def origin_total_partial(
    data: dict[str, Any],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["origin_chart"]["blocks"][key]
    total = 0.0
    for entry in origin.get("basis", []):
        r_power = int(entry["R_power"])
        z_power = int(entry["Z_power"])
        total += float(entry["coeff"]) * origin_coeff_partial(
            r_power, z_power, q, x, dq_order, dx_order
        )
    return total


def enumerate_coefficients(data: dict[str, Any]) -> list[CoefficientVariable]:
    variables: list[CoefficientVariable] = []
    tail_blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])

    def add_tail_block(component: str, block: str, patches: list[dict[str, Any]], alpha: float) -> None:
        for patch_index, patch in enumerate(patches):
            for kq, row in enumerate(patch["coeffs"]):
                for kx, value in enumerate(row):
                    path = (
                        "tail_chart",
                        "blocks",
                        block,
                        patch_index,
                        "coeffs",
                        kq,
                        kx,
                    )
                    variables.append(
                        CoefficientVariable(
                            index=len(variables),
                            chart="tail",
                            component=component,
                            block=block,
                            path=path,
                            label=f"tail.{block}[p{patch_index}].c[{kq},{kx}]",
                            value=float(value),
                            alpha=alpha,
                            patch_index=patch_index,
                            kq=kq,
                            kx=kx,
                        )
                    )

    def add_tail_frac(component: str, block: str, frac_blocks: list[list[dict[str, Any]]]) -> None:
        for frac_zero_index, patches in enumerate(frac_blocks):
            frac_index = frac_zero_index + 1
            for patch_index, patch in enumerate(patches):
                for kq, row in enumerate(patch["coeffs"]):
                    for kx, value in enumerate(row):
                        path = (
                            "tail_chart",
                            "blocks",
                            block,
                            frac_zero_index,
                            patch_index,
                            "coeffs",
                            kq,
                            kx,
                        )
                        variables.append(
                            CoefficientVariable(
                                index=len(variables),
                                chart="tail",
                                component=component,
                                block=block,
                                path=path,
                                label=f"tail.{block}[f{frac_index}][p{patch_index}].c[{kq},{kx}]",
                                value=float(value),
                                alpha=frac_index * p,
                                patch_index=patch_index,
                                frac_index=frac_index,
                                kq=kq,
                                kx=kx,
                            )
                        )

    add_tail_block("F", "F_an", tail_blocks["F_an"], 2.0)
    add_tail_frac("F", "F_frac", tail_blocks.get("F_frac", []))
    add_tail_block("G", "G_an", tail_blocks["G_an"], 2.0)
    add_tail_frac("G", "G_frac", tail_blocks.get("G_frac", []))

    origin_blocks = data["origin_chart"]["blocks"]
    for component, block in (("F", "F_origin_taylor"), ("G", "G_origin_taylor")):
        for basis_index, entry in enumerate(origin_blocks[block].get("basis", [])):
            r_power = int(entry["R_power"])
            z_power = int(entry["Z_power"])
            path = ("origin_chart", "blocks", block, "basis", basis_index, "coeff")
            variables.append(
                CoefficientVariable(
                    index=len(variables),
                    chart="origin",
                    component=component,
                    block=block,
                    path=path,
                    label=f"origin.{block}[{r_power},{z_power}]",
                    value=float(entry["coeff"]),
                    r_power=r_power,
                    z_power=z_power,
                )
            )
    return variables


def active_jacobian(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> tuple[tuple[int, float], ...]:
    blocks = data["tail_chart"]["blocks"]
    active_tail_patches: dict[str, int] = {}
    for block_name in ("F_an", "G_an"):
        active_tail_patches[block_name] = find_patch_index(blocks[block_name], q, x)
    for block_name in ("F_frac", "G_frac"):
        for frac_zero_index, frac_patches in enumerate(blocks.get(block_name, [])):
            active_tail_patches[f"{block_name}:{frac_zero_index + 1}"] = find_patch_index(frac_patches, q, x)

    jac: list[tuple[int, float]] = []
    for variable in variables:
        if variable.component != component:
            continue
        if variable.chart == "tail":
            if variable.frac_index is None:
                active_key = variable.block
                patch = blocks[variable.block][variable.patch_index]
            else:
                active_key = f"{variable.block}:{variable.frac_index}"
                patch = blocks[variable.block][variable.frac_index - 1][variable.patch_index]
            if active_tail_patches[active_key] != variable.patch_index:
                continue
            value = weighted_cheb_coeff_partial(
                patch,
                float(variable.alpha),
                q,
                x,
                int(variable.kq),
                int(variable.kx),
                dq_order,
                dx_order,
            )
        elif variable.chart == "origin":
            value = -origin_coeff_partial(
                int(variable.r_power),
                int(variable.z_power),
                q,
                x,
                dq_order,
                dx_order,
            )
        else:
            continue
        if value != 0.0:
            jac.append((variable.index, value))
    return tuple(jac)


def build_rows(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    q_values: Iterable[float],
    x_values: Iterable[float],
    max_order: int,
) -> list[MortarRow]:
    rows: list[MortarRow] = []
    specs = derivative_specs(max_order)
    for component in ("F", "G"):
        for q in q_values:
            for x in x_values:
                for spec in specs:
                    tail = tail_total_partial(data, component, q, x, spec.dq_order, spec.dx_order)
                    origin = origin_total_partial(data, component, q, x, spec.dq_order, spec.dx_order)
                    rows.append(
                        MortarRow(
                            row_index=len(rows),
                            component=component,
                            q=q,
                            x=x,
                            dq_order=spec.dq_order,
                            dx_order=spec.dx_order,
                            tail_value=tail,
                            origin_value=origin,
                            residual=tail - origin,
                            jacobian=active_jacobian(
                                data,
                                variables,
                                component,
                                q,
                                x,
                                spec.dq_order,
                                spec.dx_order,
                            ),
                        )
                    )
    return rows


def build_rz_rows(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    q_values: Iterable[float],
    x_values: Iterable[float],
    max_order: int,
    use_native_c: bool = False,
) -> list[MortarRow]:
    if max_order < 0 or max_order > 4:
        raise ValueError("--max-order must be between 0 and 4")
    rows: list[MortarRow] = []
    specs = rz_derivative_indices(max_order)
    component_variables = {
        component: [variable for variable in variables if variable.component == component]
        for component in ("F", "G")
    }
    for component in ("F", "G"):
        for q in q_values:
            for x in x_values:
                R0, Z0 = qx_to_rz(q, x)
                tail = tail_total_rz_jet(data, component, R0, Z0, max_order)
                origin = origin_total_rz_jet(data, component, R0, Z0, max_order)
                if use_native_c:
                    native_tail_partials = _native_rz_tail_partials(
                        data, component_variables[component], component, q, x, max_order
                    )
                    jacobian_by_spec: list[list[tuple[int, float]]] = [[] for _spec in specs]
                    for variable in component_variables[component]:
                        if variable.chart == "tail":
                            partials = native_tail_partials.get(variable.index)
                            if partials is None:
                                continue
                            for spec_index, value in enumerate(partials):
                                if value != 0.0:
                                    jacobian_by_spec[spec_index].append((variable.index, value))
                        elif variable.chart == "origin":
                            for spec_index, (dR_order, dZ_order) in enumerate(specs):
                                value = _origin_rz_residual_partial(variable, R0, Z0, dR_order, dZ_order)
                                if value != 0.0:
                                    jacobian_by_spec[spec_index].append((variable.index, value))
                else:
                    variable_jets = [
                        (variable.index, variable_rz_residual_jet(data, variable, component, R0, Z0, max_order))
                        for variable in component_variables[component]
                    ]
                    jacobian_by_spec = []
                    for dR_order, dZ_order in specs:
                        jacobian_by_spec.append(
                            [
                                (var_index, jet.partial(dR_order, dZ_order))
                                for var_index, jet in variable_jets
                                if jet.partial(dR_order, dZ_order) != 0.0
                            ]
                        )
                for spec_index, (dR_order, dZ_order) in enumerate(specs):
                    tail_value = tail.partial(dR_order, dZ_order)
                    origin_value = origin.partial(dR_order, dZ_order)
                    rows.append(
                        MortarRow(
                            row_index=len(rows),
                            component=component,
                            q=q,
                            x=x,
                            dq_order=dR_order,
                            dx_order=dZ_order,
                            tail_value=tail_value,
                            origin_value=origin_value,
                            residual=tail_value - origin_value,
                            jacobian=tuple(jacobian_by_spec[spec_index]),
                            coordinate="RZ",
                        )
                    )
    return rows


def get_path(data: dict[str, Any], path: tuple[Any, ...]) -> Any:
    node: Any = data
    for part in path:
        node = node[part]
    return node


def set_path(data: dict[str, Any], path: tuple[Any, ...], value: float) -> None:
    node: Any = data
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value


def residual_for_row(data: dict[str, Any], row: MortarRow) -> float:
    if row.coordinate == "RZ":
        R0, Z0 = qx_to_rz(row.q, row.x)
        order = row.dq_order + row.dx_order
        return tail_total_rz_jet(data, row.component, R0, Z0, order).partial(
            row.dq_order, row.dx_order
        ) - origin_total_rz_jet(data, row.component, R0, Z0, order).partial(row.dq_order, row.dx_order)
    return tail_total_partial(data, row.component, row.q, row.x, row.dq_order, row.dx_order) - origin_total_partial(
        data, row.component, row.q, row.x, row.dq_order, row.dx_order
    )


def smoke_finite_difference(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    rows: list[MortarRow],
    epsilon: float,
) -> dict[str, Any]:
    chosen: list[dict[str, Any]] = []
    used_variables: set[int] = set()
    target_specs = {
        ("F", 0, 0),
        ("F", 1, 1),
        ("G", 2, 0),
    }
    for row in rows:
        row_key = (row.component, row.dq_order, row.dx_order)
        if row_key not in target_specs:
            continue
        for var_index, exact in row.jacobian:
            if var_index in used_variables or abs(exact) < 1e-10:
                continue
            variable = variables[var_index]
            original = float(get_path(data, variable.path))
            plus_data = copy.deepcopy(data)
            minus_data = copy.deepcopy(data)
            set_path(plus_data, variable.path, original + epsilon)
            set_path(minus_data, variable.path, original - epsilon)
            fd = (residual_for_row(plus_data, row) - residual_for_row(minus_data, row)) / (2.0 * epsilon)
            chosen.append(
                {
                    "row_index": row.row_index,
                    "component": row.component,
                    "coordinate": row.coordinate,
                    "q": row.q,
                    "x": row.x,
                    "derivative": row.derivative_label,
                    "var_index": var_index,
                    "variable": variable.label,
                    "epsilon": epsilon,
                    "exact_jacobian": exact,
                    "finite_difference": fd,
                    "abs_diff": abs(fd - exact),
                    "relative_diff": abs(fd - exact) / max(1.0, abs(exact)),
                }
            )
            used_variables.add(var_index)
            target_specs.remove(row_key)
            break
        if not target_specs:
            break
    if len(chosen) != 3:
        raise RuntimeError(f"finite-difference smoke selected {len(chosen)} checks, expected 3")
    return {
        "epsilon": epsilon,
        "checks": chosen,
        "max_abs_diff": max(item["abs_diff"] for item in chosen),
        "max_relative_diff": max(item["relative_diff"] for item in chosen),
    }


def summarize_inventory(variables: list[CoefficientVariable]) -> dict[str, Any]:
    by_block: dict[str, int] = {}
    for variable in variables:
        key = f"{variable.chart}.{variable.block}"
        by_block[key] = by_block.get(key, 0) + 1
    return {
        "count": len(variables),
        "by_block": dict(sorted(by_block.items())),
        "preview": [variable.as_json() for variable in variables[:12]],
    }


def summarize_rows(rows: list[MortarRow]) -> dict[str, Any]:
    total_sq = 0.0
    total_nnz = 0
    worst = max(rows, key=lambda row: row.abs_residual, default=None)
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        total_sq += row.residual * row.residual
        total_nnz += len(row.jacobian)
        key = f"{row.coordinate}:{row.component}:{row.derivative_label}"
        group = groups.setdefault(
            key,
            {
                "key": key,
                "coordinate": row.coordinate,
                "component": row.component,
                "derivative": row.derivative_label,
                "dq_order": row.dq_order,
                "dx_order": row.dx_order,
                "count": 0,
                "rms_sum": 0.0,
                "max_abs": 0.0,
            },
        )
        group["count"] += 1
        group["rms_sum"] += row.residual * row.residual
        group["max_abs"] = max(group["max_abs"], row.abs_residual)
    group_items = []
    for group in groups.values():
        count = int(group["count"])
        group_items.append(
            {
                "key": group["key"],
                "coordinate": group["coordinate"],
                "component": group["component"],
                "derivative": group["derivative"],
                "dq_order": group["dq_order"],
                "dx_order": group["dx_order"],
                "count": count,
                "max_abs": group["max_abs"],
                "rms": math.sqrt(group["rms_sum"] / max(count, 1)),
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    return {
        "count": len(rows),
        "jacobian_total_nnz": total_nnz,
        "jacobian_nnz_per_row": total_nnz / max(len(rows), 1),
        "max_abs": worst.abs_residual if worst else 0.0,
        "rms": math.sqrt(total_sq / max(len(rows), 1)),
        "worst": worst.as_json() if worst else {},
        "groups": group_items,
    }


def default_profile_path() -> str:
    preferred = os.path.join(ROOT_DIR, "work", "v117_twochart_init.json")
    if os.path.exists(preferred):
        return preferred
    return os.path.join(ROOT_DIR, "work", "twochart_projection_v1.json")


def renumber_rows(rows: list[MortarRow]) -> list[MortarRow]:
    return [replace(row, row_index=index) for index, row in enumerate(rows)]


def run(args: argparse.Namespace) -> dict[str, Any]:
    data = load_json(args.profile)
    variables = enumerate_coefficients(data)
    q_values = grid(args.q_min, args.q_max, args.q_samples)
    x_values = grid(0.0, 1.0, args.x_samples)
    use_native_c = bool(getattr(args, "native_c", False))
    reset_native_c_rz_stats()
    if args.coordinates == "qx":
        rows = build_rows(data, variables, q_values, x_values, args.max_order)
    elif args.coordinates == "RZ":
        rows = build_rz_rows(data, variables, q_values, x_values, args.max_order, use_native_c=use_native_c)
    else:
        rows = renumber_rows(
            build_rows(data, variables, q_values, x_values, args.max_order)
            + build_rz_rows(data, variables, q_values, x_values, args.max_order, use_native_c=use_native_c)
        )
    smoke = smoke_finite_difference(data, variables, rows, args.fd_epsilon) if args.smoke else None

    profile_rel = os.path.relpath(args.profile, ROOT_DIR) if os.path.isabs(args.profile) else args.profile
    row_preview_count = len(rows) if args.include_rows else min(args.row_limit, len(rows))
    result: dict[str, Any] = {
        "status": STATUS,
        "profile": profile_rel,
        "format": SUPPORTED_FORMAT,
        "diagnostic_vs_proof": "floating residual/Jacobian assembly only; no interval proof or proof claim",
        "coordinates": args.coordinates,
        "residual_definition": (
            "tail_total_jet(R,Z) - origin_total_jet(R,Z)"
            if args.coordinates == "RZ"
            else "tail_total_partial(q,x) - origin_total_partial(q,x)"
            if args.coordinates == "qx"
            else "both q,x and composed R,Z overlap rows"
        ),
        "tail_legality": data.get("tail_legality"),
        "q_band": [args.q_min, args.q_max],
        "q_samples": args.q_samples,
        "x_samples": args.x_samples,
        "max_order": args.max_order,
        "derivative_specs": (
            [
                {"coordinate": "qx", "derivative": spec.label, "dq_order": spec.dq_order, "dx_order": spec.dx_order}
                for spec in derivative_specs(args.max_order)
            ]
            if args.coordinates == "qx"
            else [
                {
                    "coordinate": "RZ",
                    "derivative": "value" if dR + dZ == 0 else "d" + ("R" * dR) + ("Z" * dZ),
                    "dR_order": dR,
                    "dZ_order": dZ,
                }
                for dR, dZ in rz_derivative_indices(args.max_order)
            ]
            if args.coordinates == "RZ"
            else []
        ),
        "coefficient_inventory": summarize_inventory(variables),
        "summary": summarize_rows(rows),
        "native_c_rz": native_c_rz_stats(),
        "rows_included": row_preview_count,
        "rows_truncated": row_preview_count < len(rows),
        "rows": [row.as_json(variables) for row in rows[:row_preview_count]],
    }
    if smoke is not None:
        result["finite_difference_smoke"] = smoke
    return result


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print(f"profile={result['profile']}")
    print(f"status={result['status']}")
    print(f"coordinates={result['coordinates']}")
    print(f"q_band={result['q_band']} q_samples={result['q_samples']} x_samples={result['x_samples']}")
    print(f"max_order=C{result['max_order']}")
    print(f"coefficients={result['coefficient_inventory']['count']}")
    print(f"rows={summary['count']} jacobian_total_nnz={summary['jacobian_total_nnz']}")
    native_c = result.get("native_c_rz", {})
    if native_c.get("enabled"):
        print(
            f"native_c_rz_cases={native_c.get('cases', 0)} "
            f"native_c_rz_seconds={float(native_c.get('seconds', 0.0)):.6f}"
        )
    print(f"max_abs={float(summary['max_abs']):.12e}")
    print(f"rms={float(summary['rms']):.12e}")
    if "finite_difference_smoke" in result:
        smoke = result["finite_difference_smoke"]
        print(f"fd_checks={len(smoke['checks'])} fd_max_abs_diff={float(smoke['max_abs_diff']):.12e}")
    print(f"diagnostic_vs_proof={result['diagnostic_vs_proof']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=default_profile_path())
    parser.add_argument("--q-min", type=float, default=0.84)
    parser.add_argument("--q-max", type=float, default=0.92)
    parser.add_argument("--q-samples", type=int, default=5)
    parser.add_argument("--x-samples", type=int, default=9)
    parser.add_argument("--max-order", type=int, default=4)
    parser.add_argument("--coordinates", choices=("qx", "RZ", "both"), default="qx")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--row-limit", type=int, default=20)
    parser.add_argument("--include-rows", action="store_true", help="write all rows instead of a preview")
    parser.add_argument(
        "--native-c",
        action="store_true",
        help="Use native C for R/Z tail coefficient Jacobian jets when coordinates include RZ.",
    )
    parser.add_argument("--smoke", action="store_true", help="run three coefficient finite-difference checks")
    parser.add_argument("--fd-epsilon", type=float, default=1e-6)
    args = parser.parse_args()

    if not (0.0 < args.q_min <= args.q_max < 1.0):
        raise ValueError("require 0 < --q-min <= --q-max < 1")
    if args.q_samples <= 0 or args.x_samples <= 0:
        raise ValueError("sample counts must be positive")
    if args.row_limit < 0:
        raise ValueError("--row-limit must be nonnegative")
    if args.fd_epsilon <= 0.0:
        raise ValueError("--fd-epsilon must be positive")

    result = run(args)
    print_summary(result)
    if args.json_out:
        save_json(args.json_out, result)


if __name__ == "__main__":
    main()
