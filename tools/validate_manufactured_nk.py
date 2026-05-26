#!/usr/bin/env python3
"""Emit a manufactured Newton-Kantorovich infrastructure certificate.

This certificate is a positive-control ledger for the scalar
radii-polynomial acceptance path only.  It is deliberately kept under
``certs/infrastructure`` and is not a dependency of the final theorem manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.radii_polynomial import manufactured_zero_self_test  # noqa: E402


SCHEMA_VERSION = "nsproof-cert-v1"
CERTIFICATE_NAME = "manufactured_nk"
RADIUS_HELPER = "validators/radii_polynomial.py"
DEFAULT_OUT = "certs/infrastructure/manufactured_nk.json"


def repo_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return out.strip()


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path: str, data: dict[str, Any]) -> None:
    full = resolve(path)
    out_dir = os.path.dirname(full)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def build_certificate(command: str) -> dict[str, Any]:
    manufactured_gate = manufactured_zero_self_test()
    helper_hash = sha256_file(resolve(RADIUS_HELPER))
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "pass": bool(manufactured_gate["pass"]),
        "repo_commit": repo_commit(),
        "backend": manufactured_gate["backend"],
        "precision_digits": manufactured_gate["precision_digits"],
        "mathematical_statement": (
            "For the manufactured scalar Newton-Kantorovich example with "
            "Y0=0, Z0=0.1, Z2=0.1, the scalar radii polynomial "
            "p(r)=Y0-(1-Z0)r+Z2*r^2 is strictly negative on the certified "
            "radius interval, so the infrastructure acceptance path can "
            "record a passing toy certificate."
        ),
        "scope": "infrastructure-only manufactured scalar NK positive control",
        "final_theorem_manifest_dependency": False,
        "input_hashes": {
            RADIUS_HELPER: helper_hash,
        },
        "dependency_hashes": {
            RADIUS_HELPER: helper_hash,
        },
        "manufactured_scalar_nk": manufactured_gate,
        "commands": [command],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    command = " ".join(sys.argv)
    cert = build_certificate(command)
    save_json(args.out, cert)
    print(f"certificate_name={cert['certificate_name']}")
    print(f"pass={cert['pass']}")
    print(f"radii_polynomial_interval={cert['manufactured_scalar_nk']['radii_polynomial_interval']}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()
