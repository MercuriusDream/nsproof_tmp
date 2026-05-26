#!/usr/bin/env python3
"""Emit the pressure-reconstruction certificate ledger.

This is a proof-facing dependency ledger, not a pressure validator.  It reads
the profile and profile Newton-Kantorovich certificate, records the exact
pressure-reconstruction obligations, and deliberately emits ``pass=false``
until the profile NK gate passes and outward-rounded pressure/one-form
interval bounds exist.
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

from validators.compactified_equations_twochart import enforce_twochart_gate  # noqa: E402
from validators.exact_profile_residual import (  # noqa: E402
    SCHEMA_VERSION,
    basis_payload,
    relpath,
    repo_commit,
    resolve_path,
    save_json,
    sha256_file,
    stable_json_hash,
    tail_policy_payload,
)
from validators.pressure_exactness import (  # noqa: E402
    PRESSURE_RECONSTRUCTION_STATEMENT,
    formal_pressure_identity_self_test,
    missing_interval_blockers,
    pressure_obligations,
    pressure_reconstruction_hash,
)


CERTIFICATE_NAME = "pressure_reconstruction"
STATUS = "PRESSURE_RECONSTRUCTION_LEDGER_NOT_INTERVAL"


def load_json_object(path: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "JSON root is not an object"
    return data, None


def code_hashes() -> dict[str, str]:
    files = [
        "tools/validate_pressure_reconstruction.py",
        "validators/pressure_exactness.py",
        "validators/exact_profile_residual.py",
        "validators/compactified_equations_twochart.py",
    ]
    out: dict[str, str] = {}
    for item in files:
        path = os.path.join(ROOT_DIR, item)
        if os.path.exists(path):
            out[item] = sha256_file(path)
    return out


def profile_report(profile_arg: str) -> tuple[dict[str, Any], dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    path = resolve_path(profile_arg)
    report: dict[str, Any] = {
        "path": relpath(path),
        "exists": os.path.exists(path),
        "sha256": None,
        "format": None,
        "gamma": None,
        "B": None,
        "p": None,
        "basis_hash_sha256": None,
        "tail_policy_hash_sha256": None,
        "twochart_gate": False,
        "failure_reason": None,
    }
    if not report["exists"]:
        reason = f"profile file is missing: {relpath(path)}"
        report["failure_reason"] = reason
        blockers.append(reason)
        return report, None, blockers

    report["sha256"] = sha256_file(path)
    data, error = load_json_object(path)
    if data is None:
        reason = f"profile could not be parsed: {error}"
        report["failure_reason"] = reason
        blockers.append(reason)
        return report, None, blockers

    report.update(
        {
            "format": data.get("format"),
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "basis_hash_sha256": stable_json_hash(basis_payload(data)),
            "tail_policy_hash_sha256": stable_json_hash(tail_policy_payload(data)),
        }
    )
    try:
        enforce_twochart_gate(data, profile_arg)
    except (KeyError, TypeError, ValueError) as exc:
        reason = f"profile failed two-chart gate: {exc}"
        report["failure_reason"] = reason
        blockers.append(reason)
    else:
        report["twochart_gate"] = True
    return report, data, blockers


def profile_nk_report(profile_nk_arg: str, profile_sha256: str | None) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    path = resolve_path(profile_nk_arg)
    report: dict[str, Any] = {
        "path": relpath(path),
        "exists": os.path.exists(path),
        "sha256": None,
        "stable_json_hash_sha256": None,
        "schema_version": None,
        "certificate_name": None,
        "pass": False,
        "profile": None,
        "profile_hash_sha256": None,
        "failure_reason": None,
    }
    if not report["exists"]:
        reason = f"profile_nk certificate is missing: {relpath(path)}"
        report["failure_reason"] = reason
        blockers.append(reason)
        return report, blockers

    report["sha256"] = sha256_file(path)
    data, error = load_json_object(path)
    if data is None:
        reason = f"profile_nk certificate could not be parsed: {error}"
        report["failure_reason"] = reason
        blockers.append(reason)
        return report, blockers

    report.update(
        {
            "stable_json_hash_sha256": stable_json_hash(data),
            "schema_version": data.get("schema_version"),
            "certificate_name": data.get("certificate_name"),
            "pass": bool(data.get("pass", False)),
            "profile": data.get("profile"),
            "profile_hash_sha256": data.get("profile_hash_sha256"),
            "failure_reason": data.get("failure_reason"),
        }
    )
    if report["certificate_name"] != "profile_nk":
        blockers.append(
            f"profile_nk dependency has certificate_name={report['certificate_name']!r}, expected 'profile_nk'"
        )
    if profile_sha256 and report["profile_hash_sha256"] and report["profile_hash_sha256"] != profile_sha256:
        blockers.append(
            "profile_nk profile_hash_sha256 does not match --profile hash: "
            f"{report['profile_hash_sha256']} != {profile_sha256}"
        )
    if not report["pass"]:
        detail = report["failure_reason"] or "pass field is false or missing"
        blockers.append(f"profile_nk pass=false: {detail}")
    return report, blockers


def build_pressure_reconstruction_certificate(args: argparse.Namespace) -> dict[str, Any]:
    profile, profile_data, profile_blockers = profile_report(args.profile)
    profile_nk, nk_blockers = profile_nk_report(args.profile_nk, profile.get("sha256"))
    obligations = pressure_obligations()
    identity_self_test = formal_pressure_identity_self_test()
    hashes = code_hashes()

    blockers = []
    blockers.extend(profile_blockers)
    blockers.extend(nk_blockers)
    blockers.extend(
        [
            "pressure reconstruction interval backend is not implemented",
            "exact one-form/pressure interval bounds are not available",
        ]
    )
    blockers.extend(missing_interval_blockers(obligations))

    dependency_hashes = {
        "pressure_reconstruction_map": pressure_reconstruction_hash(hashes),
    }
    if profile.get("basis_hash_sha256"):
        dependency_hashes["basis"] = profile["basis_hash_sha256"]
    if profile.get("tail_policy_hash_sha256"):
        dependency_hashes["tail_policy"] = profile["tail_policy_hash_sha256"]
    if profile_nk.get("sha256"):
        dependency_hashes["profile_nk_file"] = profile_nk["sha256"]
    if profile_nk.get("stable_json_hash_sha256"):
        dependency_hashes["profile_nk_stable_json"] = profile_nk["stable_json_hash_sha256"]

    input_hashes = {
        "profile": profile.get("sha256"),
        "profile_nk": profile_nk.get("sha256"),
    }

    pass_gate = (
        bool(profile.get("twochart_gate"))
        and bool(profile_nk.get("pass"))
        and all(bool(item.get("validated")) for item in obligations)
    )
    if pass_gate:
        blockers.append("internal error: pressure ledger has no interval backend but pass gate evaluated true")
        pass_gate = False

    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "status": STATUS,
        "pass": False,
        "repo_commit": repo_commit(),
        "profile": profile["path"],
        "profile_hash_sha256": profile.get("sha256"),
        "input_hashes": input_hashes,
        "dependency_hashes": dependency_hashes,
        "basis_hash_sha256": profile.get("basis_hash_sha256"),
        "tail_policy_hash_sha256": profile.get("tail_policy_hash_sha256"),
        "pressure_reconstruction_hash_sha256": dependency_hashes["pressure_reconstruction_map"],
        "pressure_reconstruction_statement": PRESSURE_RECONSTRUCTION_STATEMENT,
        "formal_pressure_identity_self_test": identity_self_test,
        "mathematical_statement": (
            "Pressure reconstruction from the pressure-eliminated two-chart profile: "
            "build U from psi/Gamma, validate R^theta=0, validate "
            "partial_z R^r - partial_r R^z=0, construct chart pressures that match "
            "on overlaps up to one additive constant, and validate the pressure tail."
        ),
        "profile_summary": {
            "format": profile.get("format"),
            "gamma": profile.get("gamma"),
            "B": profile.get("B"),
            "p": profile.get("p"),
            "source_profile": profile_data.get("source_profile") if profile_data else None,
        },
        "profile_nk_dependency": profile_nk,
        "backend": "ledger-only-no-pressure-interval-backend",
        "native_c_requested": bool(args.native_c),
        "native_c_status": "not-used-pressure-interval-backend-missing",
        "precision_bits": None,
        "rounding_mode": None,
        "obligations": obligations,
        "interval_bounds": {
            "R_theta": None,
            "one_form_curl": None,
            "pressure_chart_matching": None,
            "pressure_tail": None,
        },
        "interval_widths": {
            "max": None,
            "median": None,
        },
        "blockers": blockers,
        "failure_reason": "; ".join(blockers),
        "commands": [" ".join(sys.argv)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-nk", default="certs/profile/profile_nk.json")
    parser.add_argument("--out", default="certs/profile/pressure_reconstruction.json")
    parser.add_argument("--native-c", action="store_true")
    args = parser.parse_args()

    cert = build_pressure_reconstruction_certificate(args)
    save_json(args.out, cert)
    print(f"profile={cert['profile']}")
    print(f"profile_nk={cert['profile_nk_dependency']['path']}")
    print(f"profile_nk_pass={cert['profile_nk_dependency']['pass']}")
    print(f"pass={cert['pass']} status={cert['status']}")
    print(f"saved={args.out}")
    print(f"failure_reason={cert['failure_reason']}")


if __name__ == "__main__":
    main()
