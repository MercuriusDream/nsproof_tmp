#!/usr/bin/env python3
"""Create a certificate ledger for the native interval backend smoke test."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.exact_profile_residual import (  # noqa: E402
    SCHEMA_VERSION,
    repo_commit,
    save_json,
    sha256_file,
)
from validators.interval_backend import (  # noqa: E402
    Interval,
    interval_add,
    interval_mul,
    interval_poly_eval,
    interval_recip,
)


def contains(interval: Interval, value: float) -> bool:
    return interval.lo <= value <= interval.hi


def run_smoke() -> dict[str, Any]:
    lhs = [
        Interval(-1.0, -0.9999999999999998),
        Interval(-0.125, 0.5),
        Interval(1.0, 1.0000000000000002),
    ]
    rhs = [
        Interval(0.25, 0.25000000000000006),
        Interval(-2.0, -1.9999999999999998),
        Interval(3.0, 3.0000000000000004),
    ]
    add = interval_add(lhs, rhs)
    mul = interval_mul(lhs, rhs)
    recip = interval_recip([Interval(0.25, 0.25000000000000006), Interval(-4.0, -3.999999999999999)])
    poly = interval_poly_eval([-0.125, 0.5, -1.25, 0.03125], [Interval(0.25, 0.25000000000000006)])
    checks = [
        contains(add[0], -0.75),
        contains(add[1], -1.5),
        contains(mul[0], -0.25),
        contains(mul[1], -1.0),
        contains(recip[0], 4.0),
        contains(recip[1], -0.25),
        contains(poly[0], -0.07763671875),
    ]
    intervals = add + mul + recip + poly
    return {
        "pass": all(checks),
        "case_count": len(checks),
        "max_width": max(item.hi - item.lo for item in intervals),
        "sample_intervals": {
            "add": [add[0].__dict__, add[1].__dict__],
            "mul": [mul[0].__dict__, mul[1].__dict__],
            "recip": [recip[0].__dict__, recip[1].__dict__],
            "poly": [poly[0].__dict__],
        },
    }


def optional_benchmark_output(repeats: int) -> dict[str, Any]:
    try:
        out = subprocess.check_output(
            [sys.executable, "tools/validate_interval_kernel.py", "--repeats", str(repeats)],
            cwd=ROOT_DIR,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return {
            "ran": False,
            "output": getattr(exc, "output", str(exc)),
        }
    return {
        "ran": True,
        "output": out,
    }


def build_certificate(repeats: int) -> dict[str, Any]:
    smoke = run_smoke()
    benchmark = optional_benchmark_output(repeats)
    blockers = [
        "backend uses outward-rounded double intervals, not Arb/MPFI multiprecision balls",
        "elementary functions and matrix/operator interval kernels are not implemented",
        "exact residual/NK validators do not yet consume this backend for theorem gates",
    ]
    if not smoke["pass"]:
        blockers.insert(0, "native interval smoke test failed")
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "interval_backend_smoke",
        "pass": False,
        "repo_commit": repo_commit(),
        "input_hashes": {
            "native_c_kernel": sha256_file(os.path.join(ROOT_DIR, "native/c/nsproof_kernel.c")),
            "interval_backend": sha256_file(os.path.join(ROOT_DIR, "validators/interval_backend.py")),
            "interval_kernel_validator": sha256_file(os.path.join(ROOT_DIR, "tools/validate_interval_kernel.py")),
        },
        "dependency_hashes": {},
        "backend": "native-c-outward-double-intervals",
        "precision_bits": 53,
        "rounding_mode": "nextafter outward enclosure",
        "mathematical_statement": (
            "Batched interval add/sub/mul/reciprocal/polynomial primitives return "
            "outward double enclosures for deterministic smoke cases."
        ),
        "smoke": smoke,
        "benchmark": benchmark,
        "interval_widths": {
            "max": smoke["max_width"],
            "median": None,
        },
        "blockers": blockers,
        "failure_reason": "; ".join(blockers),
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="certs/infrastructure/interval_backend_smoke.json")
    parser.add_argument("--repeats", type=int, default=100)
    args = parser.parse_args()
    cert = build_certificate(args.repeats)
    save_json(args.out, cert)
    print(f"pass={cert['pass']}")
    print(f"smoke_pass={cert['smoke']['pass']}")
    print(f"case_count={cert['smoke']['case_count']}")
    print(f"max_width={cert['smoke']['max_width']:.17g}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
