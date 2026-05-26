"""Conservative two-chart residual and mortar diagnostics.

This validator consumes the diagnostic ``twochart_profile_projection_v1`` schema
emitted by ``tools/profile_project_twochart.py``.  It deliberately forwards to
the existing floating Taylor-jet residual evaluator where possible, and it
reports sampled residual and mortar numbers only.  It makes no interval,
Newton-Kantorovich, or proof claim.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.compactified_equations import (  # noqa: E402
    RESIDUAL_KINDS,
    OriginTaylor,
    ProjectedProfile,
    compactified_residual_defined,
    qb_to_rz,
    residual_with_kind,
    scan_qb_exact,
)
from validators.origin_chart import (  # noqa: E402
    RectangularProjection,
    consistency_diagnostics,
    grid as local_grid,
)


STATUS = "DIAGNOSTIC_TWOCHART_RESIDUAL_BASELINE_NOT_PROOF"
MORTAR_STATUS = "DIAGNOSTIC_TWOCHART_MORTAR_BASELINE_NOT_PROOF"
TWOCHART_FORMAT = "twochart_profile_projection_v1"


SCAN_PRESETS: dict[str, dict[str, object]] = {
    "standard": {
        "label": "standard",
        "chart": "tail",
        "q_min": 0.345,
        "q_max": 0.495,
        "b_min": 0.18,
        "b_max": 0.38,
        "n_q": 17,
        "n_b": 17,
        "note": "Focused inherited tail/ridge diagnostic.",
    },
    "focused": {
        "label": "focused",
        "chart": "tail",
        "q_min": 0.345,
        "q_max": 0.495,
        "b_min": 0.18,
        "b_max": 0.38,
        "n_q": 17,
        "n_b": 17,
        "note": "Hidden low-|b| ridge diagnostic inherited from the projected-profile audits.",
    },
    "secondary": {
        "label": "secondary",
        "chart": "tail",
        "q_min": 0.57,
        "q_max": 0.64,
        "b_min": 0.20,
        "b_max": 0.27,
        "n_q": 13,
        "n_b": 13,
        "note": "Secondary tail/interior lobe near q ~= 0.608 and |b| ~= 0.241.",
    },
    "tail": {
        "label": "tail",
        "chart": "tail",
        "q_min": 0.345,
        "q_max": 0.495,
        "b_min": 0.18,
        "b_max": 0.38,
        "n_q": 17,
        "n_b": 17,
        "note": "Alias for standard.",
    },
    "overlap": {
        "label": "overlap",
        "chart": "overlap",
        "q_min": 0.84,
        "q_max": 0.92,
        "b_min": 0.05,
        "b_max": 0.95,
        "n_q": 17,
        "n_b": 17,
        "note": "Samples the stored tail-origin overlap band; may cross the diagnostic origin switch.",
    },
    "origin": {
        "label": "origin",
        "chart": "origin",
        "q_min": 0.91,
        "q_max": 0.98,
        "b_min": 0.05,
        "b_max": 0.80,
        "n_q": 17,
        "n_b": 17,
        "note": "Origin-chart residual quotient scan.",
    },
    "edge": {
        "label": "edge",
        "chart": "mixed_edge",
        "q_min": 0.34,
        "q_max": 0.98,
        "b_min": 0.02,
        "b_max": 0.98,
        "n_q": 17,
        "n_b": 17,
        "note": "Broad near-axis/high-|b| floating diagnostic; exact axes are excluded.",
    },
    "dense64": {
        "label": "dense64",
        "chart": "mixed_dense",
        "q_min": 0.34,
        "q_max": 0.98,
        "b_min": 0.02,
        "b_max": 0.98,
        "n_q": 64,
        "n_b": 64,
        "note": "Dense held-out diagnostic; still sampled floating arithmetic.",
    },
}


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


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


def resolve_profile_path(path: str, base_dir: str = ROOT_DIR) -> str:
    if os.path.isabs(path):
        return path
    direct = os.path.join(os.getcwd(), path)
    if os.path.exists(direct):
        return direct
    return os.path.join(base_dir, path)


def enforce_twochart_gate(data: dict[str, Any], profile: str) -> None:
    if data.get("format") != TWOCHART_FORMAT:
        raise ValueError(f"{profile!r} is not a {TWOCHART_FORMAT} JSON file")
    tail = data.get("tail_legality")
    if not isinstance(tail, dict):
        raise ValueError("two-chart profile is missing tail_legality metadata")
    if not bool(tail.get("all_ok", False)):
        raise ValueError(f"tail_legality.all_ok is not true: status={tail.get('status')!r}")
    q2_tail = tail.get("q2_policy")
    q2_requested = data.get("requested_options", {}).get("q2_policy") if isinstance(data.get("requested_options"), dict) else None
    if q2_tail != "zero" or q2_requested != "zero":
        raise ValueError(f"expected q2_policy=zero, got tail={q2_tail!r} requested={q2_requested!r}")
    if not bool(tail.get("q2_ok", False)):
        raise ValueError("q2_policy=zero was requested but tail_legality.q2_ok is false")


def projection_from_twochart(data: dict[str, Any]) -> ProjectedProfile:
    tail = data.get("tail_chart", {})
    origin = data.get("origin_chart", {})
    if not isinstance(tail, dict) or not isinstance(origin, dict):
        raise ValueError("two-chart profile must contain tail_chart and origin_chart objects")
    tail_blocks = tail.get("blocks", {})
    origin_blocks = origin.get("blocks", {})
    if not isinstance(tail_blocks, dict) or not isinstance(origin_blocks, dict):
        raise ValueError("two-chart blocks are malformed")
    return ProjectedProfile(
        gamma=float(data["gamma"]),
        B=float(data["B"]),
        p=float(data["p"]),
        f_an=ProjectedProfile._load_patches(tail_blocks.get("F_an", [])),
        g_an=ProjectedProfile._load_patches(tail_blocks.get("G_an", [])),
        f_frac=[ProjectedProfile._load_patches(block) for block in tail_blocks.get("F_frac", [])],
        g_frac=[ProjectedProfile._load_patches(block) for block in tail_blocks.get("G_frac", [])],
        f_origin=OriginTaylor.load(origin_blocks.get("F_origin_taylor")),
        g_origin=OriginTaylor.load(origin_blocks.get("G_origin_taylor")),
    )


def parse_scan_names(raw: str) -> list[str]:
    names = [item.strip() for item in raw.split(",") if item.strip()]
    if not names:
        raise ValueError("--scan must name at least one scan preset")
    unknown = [name for name in names if name not in SCAN_PRESETS]
    if unknown:
        raise ValueError(f"unknown scan preset(s): {', '.join(unknown)}")
    return names


def scan_to_json(
    projection: ProjectedProfile,
    spec: dict[str, object],
    residual_kind: str,
    h: float,
) -> dict[str, Any]:
    worst, point, rms, points, skipped = scan_qb_exact(
        projection,
        q_min=float(spec["q_min"]),
        q_max=float(spec["q_max"]),
        b_min=float(spec["b_min"]),
        b_max=float(spec["b_max"]),
        n_q=int(spec["n_q"]),
        n_b=int(spec["n_b"]),
        h=h,
        residual_kind=residual_kind,
    )
    q, b, r, z = point
    finite = math.isfinite(worst.e_psi) and math.isfinite(worst.e_gamma) and math.isfinite(rms)
    return {
        "label": spec["label"],
        "chart": spec["chart"],
        "q_range": [spec["q_min"], spec["q_max"]],
        "b_range": [spec["b_min"], spec["b_max"]],
        "grid": {"n_q": spec["n_q"], "n_b": spec["n_b"], "points": points, "skipped": skipped},
        "h": h,
        "residual_kind": residual_kind,
        "mode": "ProjectedProfile.exact_residual_at Taylor jet",
        "max_abs": worst.max_abs,
        "rms": rms,
        "finite": finite,
        "worst": {
            "q": q,
            "b": b,
            "r": r,
            "z": z,
            "e_psi": worst.e_psi,
            "e_gamma": worst.e_gamma,
            "max_abs": worst.max_abs,
        },
        "note": spec["note"],
    }


def compare_to_source(
    projection: ProjectedProfile,
    source: ProjectedProfile,
    spec: dict[str, object],
    residual_kind: str,
    h: float,
) -> dict[str, Any]:
    max_epsi = 0.0
    max_egamma = 0.0
    max_abs = 0.0
    worst: dict[str, Any] = {}
    compared = 0
    skipped = 0
    for q in local_grid(float(spec["q_min"]), float(spec["q_max"]), int(spec["n_q"])):
        for b in local_grid(float(spec["b_min"]), float(spec["b_max"]), int(spec["n_b"])):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h or r == 0.0:
                skipped += 1
                continue
            if not compactified_residual_defined(q, b, projection.p, residual_kind):
                skipped += 1
                continue
            lhs = residual_with_kind(projection.exact_residual_at(r, z), q, b, projection.p, residual_kind)
            rhs = residual_with_kind(source.exact_residual_at(r, z), q, b, source.p, residual_kind)
            depsi = lhs.e_psi - rhs.e_psi
            degamma = lhs.e_gamma - rhs.e_gamma
            local = max(abs(depsi), abs(degamma))
            compared += 1
            max_epsi = max(max_epsi, abs(depsi))
            max_egamma = max(max_egamma, abs(degamma))
            if local > max_abs:
                max_abs = local
                worst = {
                    "q": q,
                    "b": b,
                    "r": r,
                    "z": z,
                    "twochart_e_psi": lhs.e_psi,
                    "twochart_e_gamma": lhs.e_gamma,
                    "source_e_psi": rhs.e_psi,
                    "source_e_gamma": rhs.e_gamma,
                    "diff_e_psi": depsi,
                    "diff_e_gamma": degamma,
                    "max_abs": local,
                }
    return {
        "status": "SOURCE_FORWARD_COMPARE_OK_NOT_PROOF" if max_abs <= 1e-8 else "SOURCE_FORWARD_COMPARE_MISMATCH_NOT_PROOF",
        "tolerance": 1e-8,
        "compared": compared,
        "skipped": skipped,
        "max_abs": max_abs,
        "max_e_psi_abs": max_epsi,
        "max_e_gamma_abs": max_egamma,
        "worst": worst,
    }


def source_profile_path(data: dict[str, Any], twochart_path: str) -> str:
    raw = str(data.get("source_profile_json") or "")
    if not raw:
        raise ValueError("two-chart profile has no source_profile_json; cannot forward residual evaluator")
    base = os.path.dirname(os.path.abspath(twochart_path))
    direct = raw if os.path.isabs(raw) else os.path.join(ROOT_DIR, raw)
    if os.path.exists(direct):
        return direct
    return resolve_profile_path(raw, base)


def mortar_metadata(source_path: str, args: argparse.Namespace) -> dict[str, Any]:
    projection = RectangularProjection.load(source_path)
    q_values = local_grid(args.overlap_q_min, args.overlap_q_max, args.mortar_q_samples)
    x_values = local_grid(0.0, 1.0, args.mortar_x_samples)
    rz = consistency_diagnostics(
        projection=projection,
        q_values=q_values,
        x_values=x_values,
        derivative_order=args.mortar_order,
        tolerance=args.mortar_tolerance,
    )
    return {
        "status": MORTAR_STATUS,
        "diagnostic_vs_proof": "sampled floating mortar metadata only; no interval smoothness proof",
        "source_profile_json": relpath(source_path),
        "coordinate_derivatives": "R,Z",
        "orders": f"C0-C{args.mortar_order}",
        "overlap_q_range": [args.overlap_q_min, args.overlap_q_max],
        "x_range": [0.0, 1.0],
        "sample_shape": {"q_samples": args.mortar_q_samples, "x_samples": args.mortar_x_samples},
        "rz_mortar": rz,
    }


def summarize_overall(scans: dict[str, Any]) -> dict[str, Any]:
    worst_label = ""
    max_abs = 0.0
    total_sq = 0.0
    count = 0
    all_finite = True
    for label, item in scans.items():
        value = float(item["max_abs"])
        if value > max_abs:
            max_abs = value
            worst_label = label
        grid = item["grid"]
        total_sq += float(item["rms"]) ** 2 * max(int(grid["points"]) * 2, 1)
        count += max(int(grid["points"]) * 2, 1)
        all_finite = all_finite and bool(item["finite"])
    return {
        "max_abs": max_abs,
        "worst_scan": worst_label,
        "combined_rms": math.sqrt(total_sq / max(count, 1)),
        "all_finite": all_finite,
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_path = resolve_profile_path(args.profile)
    data = load_json(profile_path)
    enforce_twochart_gate(data, args.profile)

    projection = projection_from_twochart(data)
    source_path = source_profile_path(data, profile_path)
    source_projection = ProjectedProfile.load(source_path)

    scan_names = parse_scan_names(args.scan)
    executed_scan_names = list(scan_names)
    if "overlap" not in executed_scan_names:
        executed_scan_names.append("overlap")
    scans: dict[str, Any] = {}
    compares: dict[str, Any] = {}
    for name in executed_scan_names:
        spec = SCAN_PRESETS[name]
        scans[name] = scan_to_json(projection, spec, args.residual_kind, args.h)
        compares[name] = compare_to_source(projection, source_projection, spec, args.residual_kind, args.h)

    mortar = mortar_metadata(source_path, args)
    report = {
        "status": STATUS,
        "diagnostic_vs_proof": "sampled floating residual baseline only; no interval or proof claim",
        "profile": relpath(profile_path),
        "format": data.get("format"),
        "source_profile_json": relpath(source_path),
        "residual_kind": args.residual_kind,
        "scan_request": scan_names,
        "scan_executed": executed_scan_names,
        "tail_legality": data.get("tail_legality"),
        "requested_options": data.get("requested_options", {}),
        "projection_parameters": {
            "gamma": float(data["gamma"]),
            "B": float(data["B"]),
            "p": float(data["p"]),
        },
        "scans": scans,
        "source_forward_compare": compares,
        "mortar_summary": {
            "status": mortar["status"],
            "orders": mortar["orders"],
            "max_abs_diff": mortar["rz_mortar"]["max_abs_diff"],
            "sample_shape": mortar["sample_shape"],
            "coordinate_derivatives": mortar["coordinate_derivatives"],
        },
        "overall": summarize_overall(scans),
    }
    return report, mortar


def print_summary(report: dict[str, Any]) -> None:
    print(f"profile={report['profile']}")
    print(f"source_profile_json={report['source_profile_json']}")
    print(f"residual_kind={report['residual_kind']}")
    tail = report["tail_legality"]
    print(f"tail_legality_status={tail.get('status')}")
    print(f"tail_legality_all_ok={tail.get('all_ok')} q2_policy={tail.get('q2_policy')} q2_ok={tail.get('q2_ok')}")
    for name, scan in report["scans"].items():
        worst = scan["worst"]
        print(
            f"scan={name} chart={scan['chart']} points={scan['grid']['points']} "
            f"skipped={scan['grid']['skipped']} max_abs={float(scan['max_abs']):.12e} "
            f"rms={float(scan['rms']):.12e} worst_q={float(worst['q']):.6f} worst_b={float(worst['b']):.6f}"
        )
        compare = report["source_forward_compare"][name]
        print(
            f"source_compare={name} max_abs={float(compare['max_abs']):.12e} "
            f"status={compare['status']}"
        )
    mortar = report["mortar_summary"]
    print(
        f"mortar={mortar['orders']} {mortar['coordinate_derivatives']} "
        f"max_abs_diff={float(mortar['max_abs_diff']):.12e}"
    )
    overall = report["overall"]
    print(
        f"overall_max_abs={float(overall['max_abs']):.12e} "
        f"worst_scan={overall['worst_scan']} combined_rms={float(overall['combined_rms']):.12e} "
        f"all_finite={overall['all_finite']}"
    )
    print(f"status={report['status']}")
    print(f"diagnostic_vs_proof={report['diagnostic_vs_proof']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="twochart_profile_projection_v1 JSON profile")
    parser.add_argument("--residual-kind", choices=RESIDUAL_KINDS, default="normalized-structural")
    parser.add_argument("--scan", default="standard,origin,edge")
    parser.add_argument("--out", default="", help="Residual baseline JSON output")
    parser.add_argument("--mortar-out", default="", help="Optional standalone mortar baseline JSON output")
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--overlap-q-min", type=float, default=0.84)
    parser.add_argument("--overlap-q-max", type=float, default=0.92)
    parser.add_argument("--mortar-q-samples", type=int, default=9)
    parser.add_argument("--mortar-x-samples", type=int, default=9)
    parser.add_argument("--mortar-order", type=int, default=4)
    parser.add_argument("--mortar-tolerance", type=float, default=1e-8)
    args = parser.parse_args()

    if args.h <= 0.0:
        raise ValueError("--h must be positive")
    if not (0.0 < args.overlap_q_min <= args.overlap_q_max < 1.0):
        raise ValueError("require 0 < --overlap-q-min <= --overlap-q-max < 1")
    if args.mortar_q_samples <= 0 or args.mortar_x_samples <= 0:
        raise ValueError("mortar sample counts must be positive")
    if args.mortar_order < 0 or args.mortar_order > 4:
        raise ValueError("--mortar-order must be between 0 and 4")

    report, mortar = build_report(args)
    print_summary(report)
    if args.out:
        save_json(args.out, report)
        print(f"saved={args.out}")
    if args.mortar_out:
        save_json(args.mortar_out, mortar)
        print(f"mortar_saved={args.mortar_out}")


if __name__ == "__main__":
    main()
