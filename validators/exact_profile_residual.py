#!/usr/bin/env python3
"""Proof-facing two-chart residual-map audit.

The repository currently has floating Taylor-jet evaluators and native C hot
kernels, not a directed-rounding interval residual backend.  This module
therefore builds the exact residual-map *ledger*: stable hashes, quotient
factorization metadata, sampled block magnitudes, mortar magnitudes, and
explicit blockers.  It is the object a later interval NK validator should
consume, and it deliberately emits ``pass=false`` until interval bounds exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.compactified_equations_twochart import (  # noqa: E402
    SCAN_PRESETS,
    enforce_twochart_gate,
    load_json,
    projection_from_twochart,
    scan_to_json,
)
from validators.origin_chart import grid as local_grid  # noqa: E402
from validators.twochart_mortar_jacobian import (  # noqa: E402
    build_rz_rows,
    residuals_for_rows,
)


SCHEMA_VERSION = "nsproof-cert-v1"
CERTIFICATE_NAME = "exact_residual_twochart_audit"
STATUS = "EXACT_RESIDUAL_TWOCHART_AUDIT_FLOATING_NOT_INTERVAL"

RESIDUAL_MAP_STATEMENT = """
psi = r^2 z q^p F(q,x), Gamma = r^2 q^p G(q,x),
q = (1+r^2+z^2)^(-1/2), x = z^2/(r^2+z^2).

A = psi_rr - psi_r/r + psi_zz.

E_psi = (1-gamma) r^2 A + gamma r^3 A_r + gamma z r^2 A_z
        + r(psi_r A_z - psi_z A_r) + 2 psi_z A + (Gamma^2)_z.

E_Gamma = (1-2gamma) Gamma + gamma(r Gamma_r + z Gamma_z)
          + (psi_r Gamma_z - psi_z Gamma_r)/r.

The discovery quotient residual divides by the configured compactified
mechanical factors only.  Physical two-chart mortar is evaluated in R=r^2,
Z=z^2 derivatives.
""".strip()


def save_json(path: str, data: dict[str, Any]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def relpath(path: str) -> str:
    if not path:
        return path
    return os.path.relpath(path, ROOT_DIR) if os.path.isabs(path) else path


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    direct = os.path.join(os.getcwd(), path)
    if os.path.exists(direct):
        return direct
    return os.path.join(ROOT_DIR, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


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


def code_hashes() -> dict[str, str]:
    files = [
        "validators/exact_profile_residual.py",
        "validators/compactified_equations.py",
        "validators/compactified_equations_twochart.py",
        "validators/twochart_mortar_jacobian.py",
        "native/c/nsproof_kernel.c",
    ]
    out: dict[str, str] = {}
    for item in files:
        path = os.path.join(ROOT_DIR, item)
        if os.path.exists(path):
            out[item] = sha256_file(path)
    return out


def basis_payload(data: dict[str, Any]) -> dict[str, Any]:
    def patch_shape(patch: dict[str, Any]) -> dict[str, Any]:
        coeffs = patch.get("coeffs", [])
        q_degree = len(coeffs)
        x_degree = max((len(row) for row in coeffs), default=0)
        return {
            "q_interval": patch.get("q_interval"),
            "x_interval": patch.get("x_interval"),
            "shape": [q_degree, x_degree],
        }

    tail_blocks = data.get("tail_chart", {}).get("blocks", {})
    origin_blocks = data.get("origin_chart", {}).get("blocks", {})
    payload: dict[str, Any] = {
        "format": data.get("format"),
        "gamma": data.get("gamma"),
        "B": data.get("B"),
        "p": data.get("p"),
        "tail": {},
        "origin": {},
    }
    for name in ("F_an", "G_an"):
        payload["tail"][name] = [patch_shape(patch) for patch in tail_blocks.get(name, [])]
    for name in ("F_frac", "G_frac"):
        payload["tail"][name] = [
            [patch_shape(patch) for patch in frac_block]
            for frac_block in tail_blocks.get(name, [])
        ]
    for name in ("F_origin_taylor", "G_origin_taylor"):
        block = origin_blocks.get(name, {})
        payload["origin"][name] = {
            "enabled": block.get("enabled"),
            "q_min": block.get("q_min"),
            "basis_powers": [
                [entry.get("R_power"), entry.get("Z_power")]
                for entry in block.get("basis", [])
            ],
        }
    return payload


def tail_policy_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "tail_legality": data.get("tail_legality", {}),
        "requested_options": data.get("requested_options", {}),
        "preserved_tail_constraints": data.get("preserved_metadata", {}).get("tail_constraints", {}),
    }


def residual_map_hash() -> str:
    return stable_json_hash(
        {
            "statement": RESIDUAL_MAP_STATEMENT,
            "code_hashes": code_hashes(),
        }
    )


def scan_names(raw: str) -> list[str]:
    names = [item.strip() for item in raw.split(",") if item.strip()]
    if not names:
        raise ValueError("at least one scan must be requested")
    unknown = [name for name in names if name not in SCAN_PRESETS]
    if unknown:
        raise ValueError(f"unknown scan preset(s): {', '.join(unknown)}")
    return names


def summarize_mortar_rows(rows: list[Any], values: list[float]) -> dict[str, Any]:
    if len(rows) != len(values):
        raise ValueError("row/value length mismatch")
    total_sq = 0.0
    groups: dict[str, dict[str, Any]] = {}
    worst_index = -1
    worst_abs = -1.0
    for index, (row, value) in enumerate(zip(rows, values)):
        value = float(value)
        abs_value = abs(value)
        total_sq += value * value
        if abs_value > worst_abs:
            worst_index = index
            worst_abs = abs_value
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
        group["rms_sum"] += value * value
        group["max_abs"] = max(float(group["max_abs"]), abs_value)

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
                "rms": math.sqrt(float(group["rms_sum"]) / max(count, 1)),
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    worst = rows[worst_index] if worst_index >= 0 else None
    worst_json = {}
    if worst is not None:
        worst_json = replace(worst, residual=float(values[worst_index])).as_json()
    return {
        "count": len(rows),
        "max_abs": max(worst_abs, 0.0),
        "rms": math.sqrt(total_sq / max(len(rows), 1)),
        "worst": worst_json,
        "groups": group_items,
    }


def build_exact_residual_audit(
    profile: str,
    residual_kind: str = "normalized-structural",
    scans: str = "standard,focused,secondary,origin,edge,overlap",
    h: float = 1e-3,
    mortar_order: int = 4,
    mortar_q_samples: int = 9,
    mortar_x_samples: int = 9,
    overlap_q_min: float = 0.84,
    overlap_q_max: float = 0.92,
    residual_threshold: float = 1e-8,
    mortar_threshold: float = 1e-8,
    use_native_c: bool = False,
) -> dict[str, Any]:
    profile_path = resolve_path(profile)
    data = load_json(profile_path)
    enforce_twochart_gate(data, profile)
    projection = projection_from_twochart(data)

    scan_reports = {
        name: scan_to_json(projection, SCAN_PRESETS[name], residual_kind, h)
        for name in scan_names(scans)
    }
    residual_max = max((float(item["max_abs"]) for item in scan_reports.values()), default=0.0)

    q_values = local_grid(overlap_q_min, overlap_q_max, mortar_q_samples)
    x_values = local_grid(0.0, 1.0, mortar_x_samples)
    rows = build_rz_rows(data, [], q_values, x_values, mortar_order)
    mortar_values, native_stats = residuals_for_rows(data, rows, use_native_c=use_native_c)
    mortar_summary = summarize_mortar_rows(rows, mortar_values)
    mortar_max = float(mortar_summary["max_abs"])

    input_hashes = {
        "profile": sha256_file(profile_path),
    }
    basis_hash = stable_json_hash(basis_payload(data))
    tail_policy_hash = stable_json_hash(tail_policy_payload(data))
    blockers = [
        "directed-rounding interval backend is not yet attached",
        "validated approximate inverse A is not yet supplied",
    ]
    if residual_max > residual_threshold:
        blockers.append(
            f"sampled quotient residual max {residual_max:.12e} exceeds entry threshold {residual_threshold:.12e}"
        )
    if mortar_max > mortar_threshold:
        blockers.append(
            f"C0-C{mortar_order} R/Z mortar max {mortar_max:.12e} exceeds entry threshold {mortar_threshold:.12e}"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "certificate_name": CERTIFICATE_NAME,
        "status": STATUS,
        "pass": False,
        "repo_commit": repo_commit(),
        "profile": relpath(profile_path),
        "profile_hash_sha256": input_hashes["profile"],
        "input_hashes": input_hashes,
        "dependency_hashes": {},
        "basis_hash_sha256": basis_hash,
        "tail_policy_hash_sha256": tail_policy_hash,
        "residual_map_hash_sha256": residual_map_hash(),
        "residual_map_statement": RESIDUAL_MAP_STATEMENT,
        "backend": "floating-taylor-jet+native-c-rz" if use_native_c else "floating-taylor-jet",
        "precision_bits": 53,
        "rounding_mode": "nearest",
        "mathematical_statement": (
            "Audit of the proof-intended two-chart residual map and physical R/Z mortar rows. "
            "This is not an interval zero certificate."
        ),
        "parameters": {
            "gamma": data.get("gamma"),
            "B": data.get("B"),
            "p": data.get("p"),
            "residual_kind": residual_kind,
        },
        "tail_policy": tail_policy_payload(data),
        "thresholds": {
            "nk_entry_residual_max": residual_threshold,
            "nk_entry_mortar_max": mortar_threshold,
        },
        "residual_blocks": {
            "scans": scan_reports,
            "max_abs": residual_max,
        },
        "mortar": {
            "coordinate_derivatives": "R,Z",
            "orders": f"C0-C{mortar_order}",
            "overlap_q_range": [overlap_q_min, overlap_q_max],
            "x_range": [0.0, 1.0],
            "sample_shape": {
                "q_samples": mortar_q_samples,
                "x_samples": mortar_x_samples,
            },
            "summary": mortar_summary,
            "native_c_rz_mortar": native_stats,
        },
        "entry_ready_for_interval_nk": False,
        "failure_reason": "; ".join(blockers),
        "blockers": blockers,
        "commands": [],
        "interval_widths": {
            "max": None,
            "median": None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--residual-kind", default="normalized-structural")
    parser.add_argument("--scan", default="standard,focused,secondary,origin,edge,overlap")
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--mortar-order", type=int, default=4)
    parser.add_argument("--mortar-q-samples", type=int, default=9)
    parser.add_argument("--mortar-x-samples", type=int, default=9)
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--residual-threshold", type=float, default=1e-8)
    parser.add_argument("--mortar-threshold", type=float, default=1e-8)
    parser.add_argument("--native-c", action="store_true")
    args = parser.parse_args()

    report = build_exact_residual_audit(
        profile=args.profile,
        residual_kind=args.residual_kind,
        scans=args.scan,
        h=args.h,
        mortar_order=args.mortar_order,
        mortar_q_samples=args.mortar_q_samples,
        mortar_x_samples=args.mortar_x_samples,
        overlap_q_min=args.overlap_q_min,
        overlap_q_max=args.overlap_q_max,
        residual_threshold=args.residual_threshold,
        mortar_threshold=args.mortar_threshold,
        use_native_c=args.native_c,
    )
    report["commands"] = [" ".join(sys.argv)]
    save_json(args.out, report)
    print(f"profile={report['profile']}")
    print(f"pass={report['pass']} status={report['status']}")
    print(f"residual_max={report['residual_blocks']['max_abs']:.12e}")
    print(f"mortar_max={report['mortar']['summary']['max_abs']:.12e}")
    print(f"failure_reason={report['failure_reason']}")
    print(f"saved={args.out}")


if __name__ == "__main__":
    main()

