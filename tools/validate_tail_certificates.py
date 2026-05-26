#!/usr/bin/env python3
"""Emit tail, indicial, and matching certificate ledgers.

The current repository has formal/floating tail diagnostics but not an interval
recurrence theorem, interval Pluecker/Evans cover, or matching determinant
certificate.  This command turns those missing theorem dependencies into
hash-linked certificate files with explicit blockers.
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
    stable_json_hash,
)
from validators.exact_tail_algebra import exact_tail_algebra_report  # noqa: E402


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
            "certificate_name": None,
            "failure_reason": "missing dependency",
        }
    data = load_json(full)
    return {
        "path": path,
        "exists": True,
        "pass": bool(data.get("pass", False)),
        "sha256": sha256_file(full),
        "certificate_name": data.get("certificate_name"),
        "profile_hash_sha256": data.get("profile_hash_sha256"),
        "failure_reason": data.get("failure_reason"),
    }


def profile_tail_metadata(data: dict[str, Any]) -> dict[str, Any]:
    fmt = data.get("format")
    if fmt == "twochart_profile_projection_v1":
        tail = data.get("tail_legality", {})
        requested = data.get("requested_options", {})
        return {
            "format": fmt,
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "q1_exclusion": "structural" if tail.get("q1_f_max") == 0 and tail.get("q1_g_max") == 0 else "floating-audited",
            "ordinary_q1_F_max": tail.get("q1_f_max"),
            "ordinary_q1_G_max": tail.get("q1_g_max"),
            "forced_qp_coeff_error": tail.get("forced_qp_coeff_error"),
            "ordinary_q2_F_trace_max": tail.get("q2_f_trace_max"),
            "ordinary_q2_G_trace_max": tail.get("q2_g_trace_max"),
            "q2_policy": tail.get("q2_policy") or requested.get("q2_policy"),
            "q2_ok": tail.get("q2_ok"),
            "floating_tail_gate_all_ok": tail.get("all_ok"),
            "floating_tail_gate_status": tail.get("status"),
        }
    if fmt == "transseries_cheb_projection_v1":
        tail = data.get("tail_constraints", {})
        return {
            "format": fmt,
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "q1_exclusion": "floating-audited",
            "ordinary_q1_F_max": tail.get("ordinary_q1", {}).get("F_max_abs"),
            "ordinary_q1_G_max": tail.get("ordinary_q1", {}).get("G_max_abs"),
            "forced_qp_coeff_error": None,
            "ordinary_q2_F_trace_max": None,
            "ordinary_q2_G_trace_max": None,
            "q2_policy": "unknown",
            "q2_ok": False,
            "floating_tail_gate_all_ok": False,
            "floating_tail_gate_status": "TRANSERIES_PROFILE_REQUIRES_FORMAL_RECURRENCE_RUN",
        }
    raise ValueError(f"unsupported profile format {fmt!r}")


def base_certificate(name: str, profile_path: str, data: dict[str, Any]) -> dict[str, Any]:
    profile_hash = sha256_file(profile_path)
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
        "dependency_hashes": {},
        "backend": "floating-formal-ledger",
        "precision_bits": 53,
        "rounding_mode": "nearest",
        "interval_widths": {
            "max": None,
            "median": None,
        },
        "commands": [" ".join(sys.argv)],
    }


def tail_recurrence_certificate(profile_path: str, data: dict[str, Any]) -> dict[str, Any]:
    tail = profile_tail_metadata(data)
    exact_tail = exact_tail_algebra_report(data, profile_path=relpath(profile_path))
    exact_subclaims = exact_tail["exact_subclaims"]
    blockers = [
        "tail recurrence is not interval-validated with directed rounding",
        "infinite tail remainder majorant is missing",
        "exponent semigroup closure certificate is missing",
    ]
    if not exact_tail["pass"]:
        blockers.append("fixed-branch exact tail algebra/profile link failed")
    if not tail.get("floating_tail_gate_all_ok"):
        blockers.append(f"floating tail gate is not clean: {tail.get('floating_tail_gate_status')}")
    if tail.get("q2_policy") != "zero" or not tail.get("q2_ok"):
        blockers.append("q2-zero policy is not confirmed by current profile metadata")
    cert = base_certificate("tail_recurrence", profile_path, data)
    cert.update(
        {
            "mathematical_statement": (
                "The profile tail belongs to the natural transseries class: q1 is absent, "
                "the forced q^p channel satisfies the formal recurrence, q2 is excluded "
                "unless certified legal, and all retained/infinite tail channels satisfy "
                "a directed-rounding recurrence with a remainder bound."
            ),
            "tail_metadata": tail,
            "exact_algebraic_subclaims": exact_subclaims,
            "exact_tail_algebra": exact_tail,
            "gamma_interval": [str(tail.get("gamma")), str(tail.get("gamma"))],
            "B_interval": [str(tail.get("B")), str(tail.get("B"))],
            "q1_exclusion": tail.get("q1_exclusion"),
            "forced_qp_coefficients": data.get("preserved_metadata", {})
            .get("tail_constraints", {})
            .get("forced_qp"),
            "q2_policy": tail.get("q2_policy"),
            "exponent_semigroup": None,
            "remainder_bound": None,
            "failure_reason": "; ".join(blockers),
            "blockers": blockers,
        }
    )
    return cert


def indicial_certificate(profile_path: str, data: dict[str, Any], tail_cert: dict[str, Any]) -> dict[str, Any]:
    blockers = [
        "tail recurrence certificate is not passing",
        "interval Pluecker/Evans box cover is not implemented",
        "large-Im(delta) exterior exclusion is missing",
        "delta=1 geometric/removable factorization is not interval-linked to the profile ball",
    ]
    cert = base_certificate("indicial_pluecker_cover", profile_path, data)
    cert.update(
        {
            "mathematical_statement": (
                "Only the geometric/removable delta=1 indicial root is admissible in "
                "the dangerous domain, and all non-geometric dangerous roots are "
                "excluded by an interval Pluecker/Evans cover plus exterior estimates."
            ),
            "dependency_hashes": {
                "tail_recurrence": stable_json_hash(tail_cert),
            },
            "delta_domain": {
                "re": [0.0, 1.10],
                "im": [0.0, 4.0],
            },
            "box_cover": None,
            "local_factorization_delta1": {
                "floating_classification": "Psi=r^2, G=0, a=0 geometric/removable",
                "interval_validated": False,
            },
            "exterior_exclusion": None,
            "failure_reason": "; ".join(blockers),
            "blockers": blockers,
        }
    )
    return cert


def matching_certificate(profile_path: str, data: dict[str, Any], tail_cert: dict[str, Any]) -> dict[str, Any]:
    blockers = [
        "profile NK certificate is not passing",
        "tail recurrence certificate is not passing",
        "interval matching determinant/transversality calculation is missing",
    ]
    cert = base_certificate("matching_determinant", profile_path, data)
    profile_nk = optional_certificate("certs/profile/profile_nk.json")
    cert.update(
        {
            "mathematical_statement": (
                "The profile matching and admissibility equations are transverse, "
                "so the certified profile is isolated modulo gauges and compatible "
                "with the certified tail class."
            ),
            "dependency_hashes": {
                "profile_nk": profile_nk.get("sha256"),
                "tail_recurrence": stable_json_hash(tail_cert),
            },
            "dependencies": {
                "profile_nk": profile_nk,
            },
            "determinant_interval": None,
            "transversality_margin": None,
            "failure_reason": "; ".join(blockers),
            "blockers": blockers,
        }
    )
    return cert


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--tail-out", default="certs/tail/tail_recurrence.json")
    parser.add_argument("--indicial-out", default="certs/tail/indicial_pluecker_cover.json")
    parser.add_argument("--matching-out", default="certs/profile/matching_determinant.json")
    args = parser.parse_args()

    profile_path = resolve_path(args.profile)
    data = load_json(profile_path)
    tail_cert = tail_recurrence_certificate(profile_path, data)
    indicial_cert = indicial_certificate(profile_path, data, tail_cert)
    matching_cert = matching_certificate(profile_path, data, tail_cert)
    save_json(args.tail_out, tail_cert)
    save_json(args.indicial_out, indicial_cert)
    save_json(args.matching_out, matching_cert)
    print(f"profile={relpath(profile_path)}")
    print(f"tail_recurrence_pass={tail_cert['pass']} saved={args.tail_out}")
    print(f"indicial_pluecker_cover_pass={indicial_cert['pass']} saved={args.indicial_out}")
    print(f"matching_determinant_pass={matching_cert['pass']} saved={args.matching_out}")


if __name__ == "__main__":
    main()
