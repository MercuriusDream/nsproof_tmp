#!/usr/bin/env python3
"""Emit a smoke certificate for Bernstein range infrastructure."""

from __future__ import annotations

import argparse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.bernstein_ball import manufactured_self_test  # noqa: E402
from validators.exact_profile_residual import (  # noqa: E402
    SCHEMA_VERSION,
    repo_commit,
    save_json,
    sha256_file,
)


def build_certificate() -> dict[str, object]:
    smoke = manufactured_self_test()
    blockers = [
        "Bernstein backend is not yet wired to exact two-chart residual expressions",
        "directed-rounding coefficient generation from profile charts is missing",
        "subdivision/domain cover selection for profile NK is missing",
    ]
    if not smoke["pass"]:
        blockers.insert(0, "Bernstein manufactured self-test failed")
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": "bernstein_backend_smoke",
        "pass": False,
        "repo_commit": repo_commit(),
        "input_hashes": {
            "bernstein_ball": sha256_file(os.path.join(ROOT_DIR, "validators/bernstein_ball.py")),
            "interval_backend": sha256_file(os.path.join(ROOT_DIR, "validators/interval_backend.py")),
            "native_c_kernel": sha256_file(os.path.join(ROOT_DIR, "native/c/nsproof_kernel.c")),
            "native_bernstein_validator": sha256_file(
                os.path.join(ROOT_DIR, "tools/validate_native_bernstein_kernel.py")
            ),
        },
        "dependency_hashes": {},
        "backend": "native-c-bernstein-range+python-subdivision-smoke",
        "precision_bits": 53,
        "rounding_mode": "nearest for smoke; proof path must use directed intervals",
        "mathematical_statement": (
            "A Bernstein polynomial range on a domain is enclosed by the hull of "
            "its Bernstein coefficients; subdivision by de Casteljau preserves "
            "that hull enclosure."
        ),
        "smoke": smoke,
        "interval_widths": {
            "max": smoke["range"]["width"],
            "median": None,
        },
        "blockers": blockers,
        "failure_reason": "; ".join(blockers),
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="certs/infrastructure/bernstein_backend_smoke.json")
    args = parser.parse_args()
    cert = build_certificate()
    save_json(args.out, cert)
    print(f"pass={cert['pass']}")
    print(f"smoke_pass={cert['smoke']['pass']}")
    print(f"range=[{cert['smoke']['range']['lower']}, {cert['smoke']['range']['upper']}]")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
