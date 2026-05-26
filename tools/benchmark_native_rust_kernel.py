#!/usr/bin/env python3
"""Compile and probe the prototype Rust Chebyshev kernel.

The benchmark uses only Python stdlib. It builds native/rust/nsproof_kernel.rs
as a temporary cdylib with rustc, loads it with ctypes, checks deterministic
cases against validators.twochart_mortar_jacobian, then prints coarse timings.
"""

from __future__ import annotations

import argparse
import ctypes
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
RUST_SRC = ROOT_DIR / "native" / "rust" / "nsproof_kernel.rs"


def shared_library_name() -> str:
    if sys.platform == "darwin":
        return "libnsproof_kernel.dylib"
    if os.name == "nt":
        return "nsproof_kernel.dll"
    return "libnsproof_kernel.so"


def compile_rust_kernel(rustc: str, temp_dir: Path) -> Path:
    output_path = temp_dir / shared_library_name()
    command = [
        rustc,
        "--crate-type",
        "cdylib",
        "-O",
        str(RUST_SRC),
        "-o",
        str(output_path),
    ]
    proc = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        if proc.stdout.strip():
            print(proc.stdout, file=sys.stderr)
        if proc.stderr.strip():
            print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"rustc failed with exit code {proc.returncode}")
    return output_path


def configure_library(lib_path: Path) -> ctypes.CDLL:
    lib = ctypes.CDLL(str(lib_path))
    size_t = ctypes.c_size_t
    double = ctypes.c_double
    u32 = ctypes.c_uint32
    i32 = ctypes.c_int32
    double_ptr = ctypes.POINTER(double)

    lib.nsproof_kernel_abi_version.argtypes = []
    lib.nsproof_kernel_abi_version.restype = u32

    lib.nsproof_cheb_basis_values.argtypes = [size_t, double, u32, double_ptr]
    lib.nsproof_cheb_basis_values.restype = i32

    lib.nsproof_cheb_basis_table_order4.argtypes = [size_t, double, double_ptr]
    lib.nsproof_cheb_basis_table_order4.restype = i32

    lib.nsproof_cheb_basis_value.argtypes = [size_t, double, u32]
    lib.nsproof_cheb_basis_value.restype = double

    lib.nsproof_cheb_basis_partial.argtypes = [
        double,
        double,
        double,
        double,
        double,
        double,
        size_t,
        size_t,
        u32,
        u32,
    ]
    lib.nsproof_cheb_basis_partial.restype = double

    lib.nsproof_weighted_cheb_coeff_partial.argtypes = [
        double,
        double,
        double,
        double,
        double,
        double,
        double,
        size_t,
        size_t,
        u32,
        u32,
    ]
    lib.nsproof_weighted_cheb_coeff_partial.restype = double

    lib.nsproof_weighted_cheb_coeff_partials.argtypes = [
        double,
        double,
        double,
        double,
        double,
        double,
        double,
        size_t,
        size_t,
        u32,
        u32,
        double_ptr,
    ]
    lib.nsproof_weighted_cheb_coeff_partials.restype = i32
    return lib


def import_reference_functions():
    sys.path.insert(0, str(ROOT_DIR))
    from validators.twochart_mortar_jacobian import (  # noqa: PLC0415
        cheb_basis_partial,
        cheb_basis_values,
        weighted_cheb_coeff_partial,
    )

    return cheb_basis_values, cheb_basis_partial, weighted_cheb_coeff_partial


def require_status(status: int, label: str) -> None:
    if status != 0:
        raise AssertionError(f"{label} returned status {status}")


def assert_close(label: str, got: float, expected: float) -> None:
    if math.isnan(got) or math.isnan(expected):
        if math.isnan(got) and math.isnan(expected):
            return
        raise AssertionError(f"{label}: got {got!r}, expected {expected!r}")
    if not math.isclose(got, expected, rel_tol=2e-10, abs_tol=2e-10):
        raise AssertionError(f"{label}: got {got:.17g}, expected {expected:.17g}")


def derivative_pairs() -> list[tuple[int, int]]:
    return [(dq, total - dq) for total in range(5) for dq in range(total + 1)]


def run_correctness_checks(lib: ctypes.CDLL) -> None:
    cheb_basis_values, cheb_basis_partial, weighted_cheb_coeff_partial = import_reference_functions()
    double = ctypes.c_double

    for count in (1, 2, 6, 12):
        for t in (-0.95, -0.25, 0.0, 0.3, 1.1):
            table_buffer = (double * (count * 5))()
            require_status(lib.nsproof_cheb_basis_table_order4(count, t, table_buffer), "basis table")
            for order in range(5):
                buffer = (double * count)()
                require_status(lib.nsproof_cheb_basis_values(count, t, order, buffer), "basis values")
                expected = cheb_basis_values(count, t, order)
                for n, expected_value in enumerate(expected):
                    assert_close(f"basis values count={count} t={t} order={order} n={n}", buffer[n], expected_value)
                    assert_close(
                        f"basis table count={count} t={t} order={order} n={n}",
                        table_buffer[n * 5 + order],
                        expected_value,
                    )
                    scalar = lib.nsproof_cheb_basis_value(n, t, order)
                    assert_close(f"basis scalar t={t} order={order} n={n}", scalar, expected_value)

    patch = {
        "q_interval": [0.18, 0.73],
        "x_interval": [0.05, 0.95],
        "coeffs": [[0.0 for _ in range(6)] for _ in range(7)],
    }
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    q_values = (0.23, 0.51, 0.70)
    x_values = (0.15, 0.42, 0.90)
    alphas = (2.0, 0.75, 1.5, -0.25)

    for q in q_values:
        for x in x_values:
            for kq in range(7):
                for kx in range(6):
                    for dq_order, dx_order in derivative_pairs():
                        expected_basis = cheb_basis_partial(patch, q, x, kq, kx, dq_order, dx_order)
                        got_basis = lib.nsproof_cheb_basis_partial(
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
                        )
                        assert_close(
                            f"basis partial q={q} x={x} k=({kq},{kx}) d=({dq_order},{dx_order})",
                            got_basis,
                            expected_basis,
                        )
                        for alpha in alphas:
                            expected_weighted = weighted_cheb_coeff_partial(
                                patch,
                                alpha,
                                q,
                                x,
                                kq,
                                kx,
                                dq_order,
                                dx_order,
                            )
                            got_weighted = lib.nsproof_weighted_cheb_coeff_partial(
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
                            )
                            assert_close(
                                f"weighted partial alpha={alpha} q={q} x={x} k=({kq},{kx}) d=({dq_order},{dx_order})",
                                got_weighted,
                                expected_weighted,
                            )

    for alpha, q, x, dq_order, dx_order in ((2.0, 0.51, 0.42, 4, 0), (0.75, 0.23, 0.90, 2, 2), (-0.25, 0.70, 0.15, 1, 3)):
        kq_count = 7
        kx_count = 6
        output = (double * (kq_count * kx_count))()
        status = lib.nsproof_weighted_cheb_coeff_partials(
            q0,
            q1,
            x0,
            x1,
            alpha,
            q,
            x,
            kq_count,
            kx_count,
            dq_order,
            dx_order,
            output,
        )
        require_status(status, "weighted batch partials")
        for kq in range(kq_count):
            for kx in range(kx_count):
                expected = weighted_cheb_coeff_partial(patch, alpha, q, x, kq, kx, dq_order, dx_order)
                got = output[kq * kx_count + kx]
                assert_close(f"weighted batch alpha={alpha} k=({kq},{kx}) d=({dq_order},{dx_order})", got, expected)


def print_timing(label: str, iterations: int, fn) -> None:
    start = time.perf_counter()
    checksum = fn()
    elapsed = time.perf_counter() - start
    per_iter_us = elapsed * 1_000_000.0 / max(iterations, 1)
    print(f"{label}: {elapsed:.6f}s total, {per_iter_us:.3f} us/iter, checksum={checksum:.6e}")


def run_timings(lib: ctypes.CDLL, iterations: int, batch_iterations: int) -> None:
    cheb_basis_values, _, weighted_cheb_coeff_partial = import_reference_functions()
    double = ctypes.c_double
    patch = {
        "q_interval": [0.18, 0.73],
        "x_interval": [0.05, 0.95],
        "coeffs": [[0.0 for _ in range(16)] for _ in range(16)],
    }
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]

    def python_basis_loop() -> float:
        total = 0.0
        for _ in range(iterations):
            total += cheb_basis_values(64, 0.37, 4)[-1]
        return total

    def rust_basis_loop() -> float:
        total = 0.0
        buffer = (double * 64)()
        for _ in range(iterations):
            status = lib.nsproof_cheb_basis_values(64, 0.37, 4, buffer)
            if status != 0:
                raise AssertionError(f"basis timing returned status {status}")
            total += buffer[63]
        return total

    scalar_cases = [
        (2.0, 0.51, 0.42, 7, 5, 4, 0),
        (0.75, 0.23, 0.90, 3, 9, 2, 2),
        (1.5, 0.70, 0.15, 12, 4, 1, 3),
        (-0.25, 0.51, 0.42, 15, 15, 0, 4),
    ]

    def python_weighted_scalar_loop() -> float:
        total = 0.0
        for index in range(iterations):
            alpha, q, x, kq, kx, dq_order, dx_order = scalar_cases[index % len(scalar_cases)]
            total += weighted_cheb_coeff_partial(patch, alpha, q, x, kq, kx, dq_order, dx_order)
        return total

    def rust_weighted_scalar_loop() -> float:
        total = 0.0
        for index in range(iterations):
            alpha, q, x, kq, kx, dq_order, dx_order = scalar_cases[index % len(scalar_cases)]
            total += lib.nsproof_weighted_cheb_coeff_partial(q0, q1, x0, x1, alpha, q, x, kq, kx, dq_order, dx_order)
        return total

    def python_weighted_batch_loop() -> float:
        total = 0.0
        for _ in range(batch_iterations):
            for kq in range(16):
                for kx in range(16):
                    total += weighted_cheb_coeff_partial(patch, 0.75, 0.51, 0.42, kq, kx, 2, 2)
        return total

    def rust_weighted_batch_loop() -> float:
        total = 0.0
        output = (double * (16 * 16))()
        for _ in range(batch_iterations):
            status = lib.nsproof_weighted_cheb_coeff_partials(q0, q1, x0, x1, 0.75, 0.51, 0.42, 16, 16, 2, 2, output)
            if status != 0:
                raise AssertionError(f"batch timing returned status {status}")
            total += output[0] + output[127] + output[255]
        return total

    print_timing("Python cheb_basis_values(count=64, order=4)", iterations, python_basis_loop)
    print_timing("Rust ctypes nsproof_cheb_basis_values(count=64, order=4)", iterations, rust_basis_loop)
    print_timing("Python weighted scalar coefficient partial", iterations, python_weighted_scalar_loop)
    print_timing("Rust ctypes weighted scalar coefficient partial", iterations, rust_weighted_scalar_loop)
    print_timing("Python weighted 16x16 coefficient batch", batch_iterations, python_weighted_batch_loop)
    print_timing("Rust ctypes weighted 16x16 coefficient batch", batch_iterations, rust_weighted_batch_loop)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20_000, help="scalar timing iterations")
    parser.add_argument("--batch-iterations", type=int, default=300, help="batch timing iterations")
    args = parser.parse_args()

    if args.iterations <= 0 or args.batch_iterations <= 0:
        raise ValueError("iteration counts must be positive")
    if not RUST_SRC.exists():
        raise SystemExit(f"missing Rust source: {RUST_SRC}")

    rustc = shutil.which("rustc")
    if rustc is None:
        print(
            f"rustc not found on PATH; cannot compile {RUST_SRC.relative_to(ROOT_DIR)}. "
            "Install Rust or provide rustc to run the native benchmark.",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="nsproof-rust-kernel-") as temp_name:
        lib_path = compile_rust_kernel(rustc, Path(temp_name))
        lib = configure_library(lib_path)
        print(f"Compiled {RUST_SRC.relative_to(ROOT_DIR)} with {rustc}")
        print(f"Loaded ABI version {lib.nsproof_kernel_abi_version()}")
        run_correctness_checks(lib)
        print("Correctness checks passed")
        run_timings(lib, args.iterations, args.batch_iterations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
