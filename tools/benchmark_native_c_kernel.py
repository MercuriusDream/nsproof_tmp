#!/usr/bin/env python3
"""Compile and benchmark the C Chebyshev kernel prototype.

This script is self-contained: it uses clang, ctypes, and the Python standard
library only. The compiled shared library is written to a temporary directory.
"""

from __future__ import annotations

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
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.twochart_mortar_jacobian import (  # noqa: E402
    build_rz_rows,
    cheb_basis_partial,
    cheb_basis_values,
    enumerate_coefficients,
    grid,
    native_rz_residuals_for_rows,
    patch_interval,
    point_in_patch,
    residual_for_row,
    rz_coordinate_jets,
    rz_derivative_indices,
    variable_tail_patch,
    weighted_coeff_rz_jet,
    weighted_cheb_coeff_partial,
)
from validators.compactified_equations import qb_to_rz, residual_with_kind  # noqa: E402
from validators.compactified_equations_twochart import (  # noqa: E402
    PDE_RESIDUAL_KIND_IDS,
    base_linearization_scalars,
    linearized_residual_with_kind,
    native_tail_exact_residual_with_kind,
    projection_from_twochart,
)
from validators.origin_chart import qx_to_rz  # noqa: E402


def compile_library(tmpdir: Path) -> Path:
    clang = shutil.which("clang")
    if clang is None:
        raise RuntimeError("clang was not found on PATH")

    src = ROOT / "native" / "c" / "nsproof_kernel.c"
    lib = tmpdir / ("libnsproof_kernel.dylib" if platform.system() == "Darwin" else "libnsproof_kernel.so")
    cmd = [
        clang,
        "-O3",
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-fPIC",
    ]
    if platform.system() == "Darwin":
        cmd.append("-dynamiclib")
    else:
        cmd.append("-shared")
    cmd.extend([str(src), "-o", str(lib)])
    if platform.system() != "Darwin":
        cmd.append("-lm")

    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return lib


def load_library(path: Path) -> ctypes.CDLL:
    lib = ctypes.CDLL(str(path))

    c_int_p = ctypes.POINTER(ctypes.c_int)
    c_double_p = ctypes.POINTER(ctypes.c_double)

    lib.nsproof_cheb_basis_values.argtypes = [
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_int,
        c_double_p,
    ]
    lib.nsproof_cheb_basis_values.restype = ctypes.c_int

    lib.nsproof_cheb_basis_partial.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        c_int_p,
    ]
    lib.nsproof_cheb_basis_partial.restype = ctypes.c_double

    lib.nsproof_weighted_cheb_coeff_partial.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        c_int_p,
    ]
    lib.nsproof_weighted_cheb_coeff_partial.restype = ctypes.c_double

    lib.nsproof_weighted_cheb_coeff_partial_array.argtypes = [
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        c_double_p,
        c_double_p,
        c_double_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_int_p,
        c_double_p,
    ]
    lib.nsproof_weighted_cheb_coeff_partial_array.restype = ctypes.c_int

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
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        c_double_p,
        ctypes.POINTER(ctypes.c_int),
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

    return lib


def assert_close(label: str, got: float, expected: float, tol: float = 1e-10) -> None:
    scale = max(1.0, abs(expected))
    if abs(got - expected) > tol * scale:
        raise AssertionError(f"{label}: got {got!r}, expected {expected!r}")


def c_basis_values(lib: ctypes.CDLL, count: int, t: float, order: int) -> list[float]:
    if count <= 0:
        status = lib.nsproof_cheb_basis_values(count, t, order, None)
        if status != 0:
            raise AssertionError(f"basis status {status}")
        return []
    out = (ctypes.c_double * count)()
    status = lib.nsproof_cheb_basis_values(count, t, order, out)
    if status != 0:
        raise AssertionError(f"basis status {status}")
    return list(out)


def c_basis_partial(
    lib: ctypes.CDLL,
    patch: dict[str, tuple[float, float]],
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    status = ctypes.c_int(0)
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    value = lib.nsproof_cheb_basis_partial(
        q0,
        q1,
        x0,
        x1,
        q,
        x,
        kq,
        kx,
        dq_order,
        dx_order,
        ctypes.byref(status),
    )
    if status.value != 0:
        raise AssertionError(f"basis partial status {status.value}")
    return float(value)


def c_weighted_partial(
    lib: ctypes.CDLL,
    patch: dict[str, tuple[float, float]],
    alpha: float,
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    status = ctypes.c_int(0)
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    value = lib.nsproof_weighted_cheb_coeff_partial(
        q0,
        q1,
        x0,
        x1,
        alpha,
        q,
        x,
        kq,
        kx,
        dq_order,
        dx_order,
        ctypes.byref(status),
    )
    if status.value != 0:
        raise AssertionError(f"weighted partial status {status.value}")
    return float(value)


def validate(lib: ctypes.CDLL) -> list[tuple[float, float, float, int, int, int, int]]:
    for count in (0, 1, 2, 5, 12, 32):
        for t in (-1.0, -0.75, -0.1, 0.0, 0.5, 0.95, 1.0, 1.2):
            for order in range(5):
                expected = cheb_basis_values(count, t, order)
                got = c_basis_values(lib, count, t, order)
                if len(got) != len(expected):
                    raise AssertionError("basis length mismatch")
                for index, (c_value, py_value) in enumerate(zip(got, expected)):
                    assert_close(f"basis count={count} t={t} order={order} index={index}", c_value, py_value)

    patch = {"q_interval": (0.5, 2.5), "x_interval": (-1.25, 1.75)}
    weighted_cases: list[tuple[float, float, float, int, int, int, int]] = []

    for q in (0.65, 1.1, 2.2):
        for x in (-1.0, -0.2, 1.4):
            for kq, kx in ((0, 0), (1, 3), (4, 2), (8, 7)):
                for dq_order, dx_order in ((0, 0), (1, 0), (0, 1), (2, 2), (4, 1), (3, 4)):
                    expected = cheb_basis_partial(patch, q, x, kq, kx, dq_order, dx_order)
                    got = c_basis_partial(lib, patch, q, x, kq, kx, dq_order, dx_order)
                    assert_close(
                        f"basis_partial q={q} x={x} k=({kq},{kx}) d=({dq_order},{dx_order})",
                        got,
                        expected,
                    )

    for alpha in (-1.25, 0.0, 0.5, 2.75):
        for q in (0.65, 1.1, 2.2):
            for x in (-1.0, -0.2, 1.4):
                for kq, kx in ((0, 0), (1, 3), (4, 2), (8, 7)):
                    for dq_order, dx_order in ((0, 0), (1, 0), (0, 1), (2, 2), (4, 1), (3, 4)):
                        expected = weighted_cheb_coeff_partial(
                            patch,
                            alpha,
                            q,
                            x,
                            kq,
                            kx,
                            dq_order,
                            dx_order,
                        )
                        got = c_weighted_partial(lib, patch, alpha, q, x, kq, kx, dq_order, dx_order)
                        assert_close(
                            (
                                "weighted_partial "
                                f"alpha={alpha} q={q} x={x} k=({kq},{kx}) d=({dq_order},{dx_order})"
                            ),
                            got,
                            expected,
                        )
                        weighted_cases.append((alpha, q, x, kq, kx, dq_order, dx_order))

    return weighted_cases


def validate_error_statuses(lib: ctypes.CDLL) -> None:
    status = ctypes.c_int(0)
    _ = lib.nsproof_weighted_cheb_coeff_partial(
        0.0,
        0.0,
        -1.0,
        1.0,
        2.0,
        0.5,
        0.1,
        1,
        1,
        0,
        0,
        ctypes.byref(status),
    )
    if status.value != -4:
        raise AssertionError(f"degenerate interval status {status.value}, expected -4")

    status = ctypes.c_int(0)
    _ = lib.nsproof_weighted_cheb_coeff_partial(
        0.0,
        1.0,
        -1.0,
        1.0,
        math.inf,
        0.5,
        0.1,
        1,
        1,
        0,
        0,
        ctypes.byref(status),
    )
    if status.value != -5:
        raise AssertionError(f"nonfinite input status {status.value}, expected -5")

    status = ctypes.c_int(0)
    _ = lib.nsproof_weighted_cheb_coeff_partial(
        0.0,
        1.0,
        -1.0,
        1.0,
        2.0,
        0.5,
        0.1,
        -1,
        1,
        0,
        0,
        ctypes.byref(status),
    )
    if status.value != -3:
        raise AssertionError(f"bad index status {status.value}, expected -3")


def validate_repeated(lib: ctypes.CDLL, passes: int) -> list[tuple[float, float, float, int, int, int, int]]:
    cases: list[tuple[float, float, float, int, int, int, int]] = []
    for _index in range(passes):
        cases = validate(lib)
        validate_rz_batch(lib)
        validate_pde_tail_batch(lib)
        validate_tail_exact_residual()
        validate_rz_mortar_residual_batch()
        validate_prediction_scan(lib)
        validate_error_statuses(lib)
    return cases


def validate_tail_exact_residual() -> dict[str, float]:
    profile_path = ROOT / "work" / "v117_twochart_init.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    projection = projection_from_twochart(data)
    residual_kind = "normalized-structural"
    point_list = [(0.45, 0.30), (0.61, 0.24), (0.76, 0.20), (0.88, 0.20)]
    max_abs = 0.0
    max_rel = 0.0
    total_cases = 0
    for q, b in point_list:
        r0, z0 = qb_to_rz(q, b)
        expected = residual_with_kind(projection.exact_residual_at(r0, z0), q, b, projection.p, residual_kind)
        got, stats = native_tail_exact_residual_with_kind(data, projection, q, b, residual_kind)
        if got is None:
            raise AssertionError(f"native exact tail residual unexpectedly fell back at q={q} b={b}")
        total_cases += int(stats.get("cases", 0))
        for c_value, py_value, component in (
            (got.e_psi, expected.e_psi, "e_psi"),
            (got.e_gamma, expected.e_gamma, "e_gamma"),
        ):
            diff = abs(c_value - py_value)
            scale = max(1.0, abs(py_value))
            max_abs = max(max_abs, diff)
            max_rel = max(max_rel, diff / scale)
            if diff > 1e-7 * scale:
                raise AssertionError(
                    f"tail exact residual mismatch q={q} b={b} component={component}: "
                    f"got={c_value!r} expected={py_value!r}"
                )
    return {"points": float(len(point_list)), "cases": float(total_cases), "max_abs": max_abs, "max_rel": max_rel}


def validate_rz_mortar_residual_batch() -> dict[str, float]:
    profile_path = ROOT / "work" / "v117_twochart_init.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    q_values = grid(0.84, 0.92, 5)
    x_values = grid(0.0, 1.0, 5)
    rows = build_rz_rows(data, [], q_values, x_values, 4, use_native_c=False)
    expected = [float(residual_for_row(data, row)) for row in rows]
    got, stats = native_rz_residuals_for_rows(data, rows)
    max_abs = 0.0
    max_rel = 0.0
    for c_value, py_value in zip(got, expected):
        diff = abs(c_value - py_value)
        scale = max(1.0, abs(py_value))
        max_abs = max(max_abs, diff)
        max_rel = max(max_rel, diff / scale)
        if diff > 1e-8 * scale:
            raise AssertionError(f"RZ mortar residual mismatch got={c_value!r} expected={py_value!r}")
    return {
        "rows": float(len(rows)),
        "cases": float(stats.get("cases", 0)),
        "max_abs": max_abs,
        "max_rel": max_rel,
        "seconds": float(stats.get("seconds", 0.0)),
    }


def validate_prediction_scan(lib: ctypes.CDLL) -> None:
    row_count = 7
    column_count = 5
    alpha_count = 4
    jacobian = [
        math.sin(0.37 * (row + 1) * (col + 2)) + 0.1 * (row - col)
        for row in range(row_count)
        for col in range(column_count)
    ]
    residuals = [math.cos(0.23 * (row + 3)) - 0.05 * row for row in range(row_count)]
    step = [0.2 * math.sin(0.41 * (col + 1)) for col in range(column_count)]
    alphas = [0.0, 0.125, 1.0, -0.5]

    double_array_j = ctypes.c_double * (row_count * column_count)
    double_array_rows = ctypes.c_double * row_count
    double_array_cols = ctypes.c_double * column_count
    double_array_alpha = ctypes.c_double * alpha_count
    int_array_alpha = ctypes.c_int * alpha_count
    out_l2 = double_array_alpha()
    out_max_abs = double_array_alpha()
    out_objective = double_array_alpha()
    statuses = int_array_alpha()
    status = lib.nsproof_stage0_prediction_scan_batch(
        row_count,
        column_count,
        alpha_count,
        double_array_j(*jacobian),
        double_array_rows(*residuals),
        double_array_cols(*step),
        double_array_alpha(*alphas),
        out_l2,
        out_max_abs,
        out_objective,
        statuses,
    )
    if status != 0:
        raise AssertionError(f"prediction scan status {status}")

    for alpha_index, alpha in enumerate(alphas):
        predicted = []
        for row in range(row_count):
            value = residuals[row]
            offset = row * column_count
            for col in range(column_count):
                value += alpha * jacobian[offset + col] * step[col]
            predicted.append(value)
        sumsq = sum(value * value for value in predicted)
        expected_l2 = math.sqrt(sumsq)
        expected_max_abs = max(abs(value) for value in predicted)
        expected_objective = 0.5 * sumsq
        assert_close(f"prediction l2 alpha={alpha}", float(out_l2[alpha_index]), expected_l2, tol=1e-12)
        assert_close(
            f"prediction max_abs alpha={alpha}",
            float(out_max_abs[alpha_index]),
            expected_max_abs,
            tol=1e-12,
        )
        assert_close(
            f"prediction objective alpha={alpha}",
            float(out_objective[alpha_index]),
            expected_objective,
            tol=1e-12,
        )


def validate_pde_tail_batch(lib: ctypes.CDLL) -> dict[str, float]:
    profile_path = ROOT / "work" / "v117_twochart_init.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    projection = projection_from_twochart(data)
    variables = enumerate_coefficients(data)
    residual_kind = "normalized-structural"
    point_list = [(0.45, 0.30), (0.61, 0.24), (0.88, 0.20), (0.90, 0.95)]
    max_abs = 0.0
    max_rel = 0.0
    total_cases = 0

    for q, b in point_list:
        x = b * b
        active = []
        for variable in variables:
            if variable.chart != "tail":
                continue
            patch = variable_tail_patch(data, variable)
            if point_in_patch(patch, q, x):
                active.append((variable, patch_interval(patch)))
            if len(active) >= 80:
                break
        if not active:
            raise AssertionError(f"no active tail variables at q={q} b={b}")

        count = len(active)
        total_cases += count
        double_array = ctypes.c_double * count
        int_array = ctypes.c_int * count
        q0_values = double_array(*[interval[0] for _variable, interval in active])
        q1_values = double_array(*[interval[1] for _variable, interval in active])
        x0_values = double_array(*[interval[2] for _variable, interval in active])
        x1_values = double_array(*[interval[3] for _variable, interval in active])
        alpha_values = double_array(*[float(variable.alpha) for variable, _interval in active])
        kq_values = int_array(*[int(variable.kq) for variable, _interval in active])
        kx_values = int_array(*[int(variable.kx) for variable, _interval in active])
        component_values = int_array(*[0 if variable.component == "F" else 1 for variable, _interval in active])
        out_e_psi = double_array()
        out_e_gamma = double_array()
        statuses = int_array()
        r0, z0 = qb_to_rz(q, b)
        scalars = base_linearization_scalars(projection, r0, z0)

        status = lib.nsproof_pde_tail_coeff_columns_batch(
            count,
            PDE_RESIDUAL_KIND_IDS[residual_kind],
            float(projection.gamma),
            float(projection.p),
            float(q),
            float(b),
            float(scalars["psi_r"]),
            float(scalars["psi_z"]),
            float(scalars["swirl"]),
            float(scalars["swirl_r"]),
            float(scalars["swirl_z"]),
            float(scalars["a"]),
            float(scalars["a_r"]),
            float(scalars["a_z"]),
            q0_values,
            q1_values,
            x0_values,
            x1_values,
            alpha_values,
            kq_values,
            kx_values,
            component_values,
            out_e_psi,
            out_e_gamma,
            statuses,
        )
        if status != 0:
            bad_statuses = sorted({int(statuses[index]) for index in range(count)})
            raise AssertionError(f"PDE tail batch status {status}, statuses={bad_statuses}")

        for row, (variable, _interval) in enumerate(active):
            expected = linearized_residual_with_kind(data, projection, variable, q, b, residual_kind)
            for got, py_value, component in (
                (float(out_e_psi[row]), expected.e_psi, "e_psi"),
                (float(out_e_gamma[row]), expected.e_gamma, "e_gamma"),
            ):
                diff = abs(got - py_value)
                scale = max(1.0, abs(py_value))
                max_abs = max(max_abs, diff)
                max_rel = max(max_rel, diff / scale)
                if diff > 1e-7 * scale:
                    raise AssertionError(
                        "PDE tail mismatch "
                        f"q={q} b={b} variable={variable.name} component={component}: "
                        f"got={got!r} expected={py_value!r}"
                    )

    return {"points": float(len(point_list)), "cases": float(total_cases), "max_abs": max_abs, "max_rel": max_rel}


def validate_rz_batch(lib: ctypes.CDLL) -> None:
    cases: list[tuple[float, float, float, float, float, float, float, int, int]] = []
    for alpha in (2.0, 20.0 / 9.0):
        for q in (0.84, 0.88, 0.92):
            for x in (0.0, 0.5, 1.0):
                for kq, kx in ((0, 0), (1, 2), (4, 3)):
                    cases.append((q, x, 0.80, 0.96, 0.0, 1.0, alpha, kq, kx))

    count = len(cases)
    max_order = 4
    spec_count = len(rz_derivative_indices(max_order))
    double_array = ctypes.c_double * count
    int_array = ctypes.c_int * count
    q_arr = double_array(*[case[0] for case in cases])
    x_arr = double_array(*[case[1] for case in cases])
    q0_arr = double_array(*[case[2] for case in cases])
    q1_arr = double_array(*[case[3] for case in cases])
    x0_arr = double_array(*[case[4] for case in cases])
    x1_arr = double_array(*[case[5] for case in cases])
    alpha_arr = double_array(*[case[6] for case in cases])
    kq_arr = int_array(*[case[7] for case in cases])
    kx_arr = int_array(*[case[8] for case in cases])
    out = (ctypes.c_double * (count * spec_count))()
    statuses = int_array()

    status = lib.nsproof_rz_weighted_coeff_partials_batch(
        count,
        max_order,
        q_arr,
        x_arr,
        q0_arr,
        q1_arr,
        x0_arr,
        x1_arr,
        alpha_arr,
        kq_arr,
        kx_arr,
        out,
        statuses,
    )
    if status != 0:
        raise AssertionError(f"RZ batch status {status}")

    for row, (q, x, q0, q1, x0, x1, alpha, kq, kx) in enumerate(cases):
        coeffs = [[0.0 for _ in range(kx + 1)] for _ in range(kq + 1)]
        coeffs[kq][kx] = 1.0
        patch = {"q_interval": [q0, q1], "x_interval": [x0, x1], "coeffs": coeffs}
        R0, Z0 = qx_to_rz(q, x)
        _R, _Z, q_jet, x_jet = rz_coordinate_jets(R0, Z0, max_order)
        expected_jet = weighted_coeff_rz_jet(patch, alpha, q_jet, x_jet, kq, kx)
        for spec_index, (dR, dZ) in enumerate(rz_derivative_indices(max_order)):
            got = float(out[row * spec_count + spec_index])
            expected = expected_jet.partial(dR, dZ)
            assert_close(
                f"rz_batch q={q} x={x} alpha={alpha} k=({kq},{kx}) d=({dR},{dZ})",
                got,
                expected,
                tol=1e-9,
            )


def benchmark_scalar(
    lib: ctypes.CDLL,
    patch: dict[str, tuple[float, float]],
    cases: list[tuple[float, float, float, int, int, int, int]],
    repeats: int,
) -> tuple[float, float, float]:
    t0 = time.perf_counter()
    py_acc = 0.0
    for _ in range(repeats):
        for alpha, q, x, kq, kx, dq_order, dx_order in cases:
            py_acc += weighted_cheb_coeff_partial(patch, alpha, q, x, kq, kx, dq_order, dx_order)
    py_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    c_acc = 0.0
    for _ in range(repeats):
        for alpha, q, x, kq, kx, dq_order, dx_order in cases:
            c_acc += c_weighted_partial(lib, patch, alpha, q, x, kq, kx, dq_order, dx_order)
    c_time = time.perf_counter() - t0

    assert_close("scalar timing accumulator", c_acc, py_acc, tol=1e-9)
    return py_time, c_time, c_acc


def benchmark_batch(
    lib: ctypes.CDLL,
    patch: dict[str, tuple[float, float]],
    cases: list[tuple[float, float, float, int, int, int, int]],
    repeats: int,
) -> tuple[float, float, float]:
    count = len(cases)
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    alpha_arr = (ctypes.c_double * count)(*[case[0] for case in cases])
    q_arr = (ctypes.c_double * count)(*[case[1] for case in cases])
    x_arr = (ctypes.c_double * count)(*[case[2] for case in cases])
    kq_arr = (ctypes.c_int * count)(*[case[3] for case in cases])
    kx_arr = (ctypes.c_int * count)(*[case[4] for case in cases])
    dq_arr = (ctypes.c_int * count)(*[case[5] for case in cases])
    dx_arr = (ctypes.c_int * count)(*[case[6] for case in cases])
    out = (ctypes.c_double * count)()

    t0 = time.perf_counter()
    py_acc = 0.0
    for _ in range(repeats):
        for alpha, q, x, kq, kx, dq_order, dx_order in cases:
            py_acc += weighted_cheb_coeff_partial(patch, alpha, q, x, kq, kx, dq_order, dx_order)
    py_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    c_acc = 0.0
    for _ in range(repeats):
        status = lib.nsproof_weighted_cheb_coeff_partial_array(
            count,
            q0,
            q1,
            x0,
            x1,
            alpha_arr,
            q_arr,
            x_arr,
            kq_arr,
            kx_arr,
            dq_arr,
            dx_arr,
            out,
        )
        if status != 0:
            raise AssertionError(f"batch status {status}")
        c_acc += sum(out)
    c_time = time.perf_counter() - t0

    assert_close("batch timing accumulator", c_acc, py_acc, tol=1e-9)
    return py_time, c_time, c_acc


def main() -> int:
    repeats = int(os.environ.get("NSPROOF_NATIVE_C_REPEATS", "500"))
    with tempfile.TemporaryDirectory(prefix="nsproof-c-kernel-") as tmp:
        lib_path = compile_library(Path(tmp))
        lib = load_library(lib_path)
        validation_passes = int(os.environ.get("NSPROOF_NATIVE_C_VALIDATION_PASSES", "3"))
        cases = validate_repeated(lib, validation_passes)
        pde_validation = validate_pde_tail_batch(lib)
        tail_exact_validation = validate_tail_exact_residual()
        rz_mortar_validation = validate_rz_mortar_residual_batch()

        patch = {"q_interval": (0.5, 2.5), "x_interval": (-1.25, 1.75)}
        scalar_py, scalar_c, scalar_acc = benchmark_scalar(lib, patch, cases, repeats)
        batch_py, batch_c, batch_acc = benchmark_batch(lib, patch, cases, repeats)

    print("native/c Chebyshev+RZ+PDE-tail+tail-exact+prediction kernel validation: ok")
    print(f"validation passes: {validation_passes}")
    print(
        "pde tail validation: "
        f"points={int(pde_validation['points'])} "
        f"cases={int(pde_validation['cases'])} "
        f"max_abs={pde_validation['max_abs']:.3e} "
        f"max_rel={pde_validation['max_rel']:.3e}"
    )
    print(
        "tail exact validation: "
        f"points={int(tail_exact_validation['points'])} "
        f"cases={int(tail_exact_validation['cases'])} "
        f"max_abs={tail_exact_validation['max_abs']:.3e} "
        f"max_rel={tail_exact_validation['max_rel']:.3e}"
    )
    print(
        "rz mortar validation: "
        f"rows={int(rz_mortar_validation['rows'])} "
        f"cases={int(rz_mortar_validation['cases'])} "
        f"max_abs={rz_mortar_validation['max_abs']:.3e} "
        f"max_rel={rz_mortar_validation['max_rel']:.3e} "
        f"seconds={rz_mortar_validation['seconds']:.6f}s"
    )
    print(f"weighted cases: {len(cases)}")
    print(f"repeats: {repeats}")
    print(f"scalar Python: {scalar_py:.6f}s")
    print(f"scalar ctypes C: {scalar_c:.6f}s ({scalar_py / scalar_c:.2f}x vs Python)")
    print(f"batch Python: {batch_py:.6f}s")
    print(f"batch ctypes C: {batch_c:.6f}s ({batch_py / batch_c:.2f}x vs Python)")
    print(f"accumulators: scalar={scalar_acc:.17g} batch={batch_acc:.17g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
