#!/usr/bin/env python3
"""Validate the exact rational exponent subclaim for a two-chart profile.

This is a proof-chain certificate for the algebraic part of the exponent gate:
``2/5 < gamma < 1/2`` and ``p = 1/gamma`` for the profile's fixed branch.
It deliberately does not certify the profile equation or the tail recurrence;
those remain separate manifest dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from fractions import Fraction
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.exact_profile_residual import SCHEMA_VERSION, save_json  # noqa: E402


CERTIFICATE_NAME = "exponent_admissibility"
SCRIPT_PATH = "tools/validate_exponent_admissibility.py"


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def relpath(path: str) -> str:
    return os.path.relpath(path, ROOT_DIR) if os.path.isabs(path) else path


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def load_profile(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("profile JSON root must be an object")
    return data


def fraction_from_text_or_number(raw: Any, *, label: str) -> Fraction:
    if raw is None:
        raise ValueError(f"missing {label}")
    if isinstance(raw, bool):
        raise ValueError(f"{label} must be numeric, got bool")
    if isinstance(raw, int):
        return Fraction(raw, 1)
    if isinstance(raw, float):
        return Fraction(str(raw))
    text = str(raw).strip()
    if not text:
        raise ValueError(f"empty {label}")
    return Fraction(text)


def exact_parameter(profile: dict[str, Any], key: str) -> Fraction:
    requested = profile.get("requested_options", {})
    if isinstance(requested, dict):
        override_key = f"{key}_override"
        if override_key in requested:
            return fraction_from_text_or_number(requested[override_key], label=override_key)
    return fraction_from_text_or_number(profile.get(key), label=key)


def decimal_string(value: Fraction) -> str:
    return format(float(value), ".17g")


def build_certificate(profile_arg: str, command: str, p_tol: float = 1e-15) -> dict[str, Any]:
    profile_path = resolve(profile_arg)
    profile = load_profile(profile_path)
    profile_hash = sha256_file(profile_path)
    script_hash = sha256_file(resolve(SCRIPT_PATH))

    blockers: list[str] = []
    gamma: Fraction | None = None
    p_expected: Fraction | None = None
    B: Fraction | None = None
    p_profile: Fraction | None = None
    try:
        gamma = exact_parameter(profile, "gamma")
        B = exact_parameter(profile, "B")
        p_expected = Fraction(1, 1) / gamma
        p_profile = fraction_from_text_or_number(profile.get("p"), label="p")
    except (ZeroDivisionError, ValueError) as exc:
        blockers.append(str(exc))

    exact_subclaims: dict[str, Any] = {}
    if gamma is not None and p_expected is not None and B is not None:
        in_wedge = Fraction(2, 5) < gamma < Fraction(1, 2)
        if not in_wedge:
            blockers.append(f"gamma={gamma} is not in the open wedge (2/5, 1/2)")
        p_profile_error = abs(float(p_profile) - float(p_expected)) if p_profile is not None else float("inf")
        p_matches = p_profile_error <= p_tol
        if not p_matches:
            blockers.append(
                f"profile decimal p={p_profile} differs from 1/gamma={p_expected} "
                f"by {p_profile_error:.17g} > {p_tol:.17g}"
            )
        exact_subclaims = {
            "gamma": str(gamma),
            "B": str(B),
            "p_expected": str(p_expected),
            "p_profile": str(p_profile),
            "gamma_decimal": decimal_string(gamma),
            "B_decimal": decimal_string(B),
            "p_expected_decimal": decimal_string(p_expected),
            "gamma_in_open_wedge_2_5_1_2": bool(in_wedge),
            "p_profile_decimal_matches_inverse_gamma": bool(p_matches),
            "p_profile_decimal_error": p_profile_error,
            "p_profile_decimal_tolerance": p_tol,
            "distance_to_lower_endpoint": str(gamma - Fraction(2, 5)),
            "distance_to_upper_endpoint": str(Fraction(1, 2) - gamma),
        }

    pass_gate = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "pass": bool(pass_gate),
        "repo_commit": repo_commit(),
        "profile": relpath(profile_path),
        "profile_hash_sha256": profile_hash,
        "input_hashes": {
            "profile": profile_hash,
            SCRIPT_PATH: script_hash,
        },
        "dependency_hashes": {
            SCRIPT_PATH: script_hash,
        },
        "backend": "python-fraction-exact-rational-arithmetic",
        "precision_bits": "exact",
        "rounding_mode": "not-applicable",
        "mathematical_statement": (
            "The fixed profile parameter gamma is an exact rational number in "
            "the open interval (2/5, 1/2), with exact exponent p=1/gamma. "
            "The profile's stored decimal p is checked against this exact value."
        ),
        "exact_subclaims": exact_subclaims,
        "profile_linkage_scope": (
            "This certificate links only the exact algebraic exponent subclaim "
            "to the supplied profile hash. It does not certify that the profile "
            "solves the PDE, that the tail recurrence closes, or that pressure "
            "reconstruction is valid."
        ),
        "blockers_for_stop_condition_gate": [
            "profile_nk.json must pass for an admissible profile at this exponent",
            "tail_recurrence.json must pass for the natural tail linked to this profile",
        ],
        "failure_reason": None if pass_gate else "; ".join(blockers),
        "blockers": blockers,
        "commands": [command],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--out", default="certs/profile/exponent_admissibility.json")
    parser.add_argument("--p-tol", type=float, default=1e-15)
    args = parser.parse_args()
    cert = build_certificate(args.profile, " ".join(sys.argv), p_tol=args.p_tol)
    save_json(args.out, cert)
    print(f"certificate_name={cert['certificate_name']}")
    print(f"pass={cert['pass']}")
    if cert["exact_subclaims"]:
        print(f"gamma={cert['exact_subclaims']['gamma']}")
        print(f"p_expected={cert['exact_subclaims']['p_expected']}")
    print(f"saved={args.out}")
    if not cert["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
