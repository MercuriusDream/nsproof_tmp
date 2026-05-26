#!/usr/bin/env python3
"""Emit honest failing spectrum certificate ledgers.

The repository does not yet have a true Leray-projected spectral validator.
This command creates the manifest-expected spectrum certificate files as
hash-linked ledgers with explicit blockers, not as proof certificates.
"""

from __future__ import annotations

import argparse
import json
import os
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


COMMON_BLOCKERS = [
    "profile NK certificate is not passing",
    "pressure reconstruction certificate is not passing",
    "true Leray projection missing",
    "geometric mode recovery missing",
    "interval resolvent/large-m/high-frequency bounds missing",
]


def resolve_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)


def relpath(path: str) -> str:
    return os.path.relpath(path, ROOT_DIR) if os.path.isabs(path) else path


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def optional_certificate(path: str) -> dict[str, Any]:
    full = resolve_path(path)
    if not os.path.exists(full):
        return {
            "path": path,
            "exists": False,
            "pass": False,
            "sha256": None,
            "schema_version": None,
            "certificate_name": None,
            "failure_reason": "missing dependency",
        }
    try:
        data = load_json(full)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "path": path,
            "exists": True,
            "pass": False,
            "sha256": sha256_file(full),
            "schema_version": None,
            "certificate_name": None,
            "failure_reason": f"could not parse dependency: {exc}",
        }
    return {
        "path": path,
        "exists": True,
        "pass": bool(data.get("pass", False)),
        "sha256": sha256_file(full),
        "schema_version": data.get("schema_version"),
        "certificate_name": data.get("certificate_name"),
        "profile_hash_sha256": data.get("profile_hash_sha256"),
        "failure_reason": data.get("failure_reason"),
    }


def profile_metadata(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": data.get("format"),
        "gamma": data.get("gamma"),
        "B": data.get("B"),
        "p": data.get("p"),
        "tail_legality_status": data.get("tail_legality", {}).get("status"),
        "floating_tail_gate_all_ok": data.get("tail_legality", {}).get("all_ok"),
    }


def dependency_blockers(profile_nk: dict[str, Any], pressure: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not profile_nk.get("pass"):
        reason = profile_nk.get("failure_reason") or "missing or failing dependency"
        blockers.append(f"profile NK certificate is not passing: {reason}")
    if not pressure.get("pass"):
        reason = pressure.get("failure_reason") or "missing or failing dependency"
        blockers.append(f"pressure reconstruction certificate is not passing: {reason}")
    blockers.extend(COMMON_BLOCKERS[2:])
    return blockers


def base_certificate(
    name: str,
    statement: str,
    profile_path: str,
    profile_data: dict[str, Any],
    profile_nk_path: str,
    pressure_path: str,
) -> dict[str, Any]:
    profile_hash = sha256_file(profile_path)
    profile_nk = optional_certificate(profile_nk_path)
    pressure = optional_certificate(pressure_path)
    blockers = dependency_blockers(profile_nk, pressure)
    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": name,
        "pass": False,
        "repo_commit": repo_commit(),
        "profile": relpath(profile_path),
        "profile_hash_sha256": profile_hash,
        "input_hashes": {
            "profile": profile_hash,
        },
        "dependency_hashes": {
            "profile_nk": profile_nk.get("sha256"),
            "pressure_reconstruction": pressure.get("sha256"),
        },
        "dependencies": {
            "profile_nk": profile_nk,
            "pressure_reconstruction": pressure,
        },
        "profile_metadata": profile_metadata(profile_data),
        "backend": "spectrum-scaffold-ledger",
        "precision_bits": None,
        "rounding_mode": None,
        "mathematical_statement": statement,
        "failure_reason": "; ".join(blockers),
        "blockers": blockers,
        "commands": [" ".join(sys.argv)],
    }


def projected_spectrum_certificate(
    profile_path: str,
    profile_data: dict[str, Any],
    profile_nk_path: str,
    pressure_path: str,
) -> dict[str, Any]:
    cert = base_certificate(
        "projected_spectrum",
        (
            "For the Leray-projected linearization L around the certified profile, "
            "the spectrum in the unstable search domain consists exactly of a "
            "finite listed set of eigenvalues/eigenspaces, with all geometric "
            "symmetry modes recovered and separated from physical unstable modes."
        ),
        profile_path,
        profile_data,
        profile_nk_path,
        pressure_path,
    )
    cert.update(
        {
            "spectral_domain": {
                "re_min": None,
                "re_max": None,
                "im_max": None,
                "mode_range": None,
            },
            "leray_projection": {
                "implemented": False,
                "validated": False,
                "pressure_coupling": "missing true pressure/Leray-projected operator",
            },
            "geometric_modes": {
                "recovered": False,
                "expected": [
                    "scaling/time-translation mode",
                    "axial translation mode",
                    "gauge/removable pressure modes, if present in formulation",
                ],
            },
            "eigenvalue_boxes": [],
            "unstable_projection_rank_interval": None,
        }
    )
    return cert


def high_frequency_certificate(
    profile_path: str,
    profile_data: dict[str, Any],
    profile_nk_path: str,
    pressure_path: str,
) -> dict[str, Any]:
    cert = base_certificate(
        "high_frequency_exclusion",
        (
            "All spectral points of the Leray-projected linearized operator outside "
            "the finite low-frequency/mode computation are excluded from the closed "
            "right half-plane by interval resolvent estimates, large-m bounds, and "
            "compactified high-frequency coercivity inequalities."
        ),
        profile_path,
        profile_data,
        profile_nk_path,
        pressure_path,
    )
    cert.update(
        {
            "covered_complement": {
                "large_angular_modes": None,
                "large_imaginary_frequency": None,
                "compactified_tail_frequency": None,
            },
            "resolvent_bounds": None,
            "large_m_threshold": None,
            "coercivity_margins": None,
            "exclusion_region": {
                "re_lambda_lower_bound": 0.0,
                "validated": False,
            },
        }
    )
    return cert


def stable_semigroup_certificate(
    profile_path: str,
    profile_data: dict[str, Any],
    profile_nk_path: str,
    pressure_path: str,
) -> dict[str, Any]:
    cert = base_certificate(
        "stable_semigroup",
        (
            "On the Leray-projected stable complement after removing the certified "
            "finite unstable/geometric spectral subspace, the generated semigroup "
            "obeys a validated decay estimate ||e^{t L_s}|| <= C exp(-c t) with "
            "explicit interval constants C < infinity and c > 0."
        ),
        profile_path,
        profile_data,
        profile_nk_path,
        pressure_path,
    )
    cert.update(
        {
            "stable_projection": {
                "constructed": False,
                "rank_linked_to_projected_spectrum": False,
            },
            "decay_rate_interval": None,
            "semigroup_constant_interval": None,
            "resolvent_to_semigroup_argument": None,
            "energy_norm_equivalence": None,
        }
    )
    return cert


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-nk", default="certs/profile/profile_nk.json")
    parser.add_argument("--pressure", default="certs/profile/pressure_reconstruction.json")
    parser.add_argument("--out-dir", default="certs/spectrum")
    args = parser.parse_args()

    profile_path = resolve_path(args.profile)
    profile_data = load_json(profile_path)

    certs = [
        ("projected_spectrum.json", projected_spectrum_certificate),
        ("high_frequency_exclusion.json", high_frequency_certificate),
        ("stable_semigroup.json", stable_semigroup_certificate),
    ]
    for filename, builder in certs:
        cert = builder(profile_path, profile_data, args.profile_nk, args.pressure)
        out_path = os.path.join(args.out_dir, filename)
        save_json(out_path, cert)
        print(f"{cert['certificate_name']}_pass={cert['pass']} saved={out_path}")


if __name__ == "__main__":
    main()
