"""Conservative two-chart residual and mortar diagnostics.

This validator consumes the diagnostic ``twochart_profile_projection_v1`` schema
emitted by ``tools/profile_project_twochart.py``.  It deliberately forwards to
the existing floating Taylor-jet residual evaluator where possible, and it
reports sampled residual and mortar numbers only.  It makes no interval,
Newton-Kantorovich, or proof claim.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import sys
import time
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from validators.compactified_equations import (  # noqa: E402
    Jet2,
    RESIDUAL_KINDS,
    OriginTaylor,
    ProjectedProfile,
    Residual,
    cheb_eval_tensor_jet,
    compactified_residual_defined,
    qb_to_rz,
    residual_with_kind,
    scan_qb_exact,
)
from validators.twochart_mortar_jacobian import (  # noqa: E402
    CoefficientVariable,
    build_rz_rows,
    enumerate_coefficients,
    get_path,
    native_c_library,
    patch_interval,
    set_path,
    summarize_rows,
)
from validators.origin_chart import (  # noqa: E402
    grid as local_grid,
)


STATUS = "DIAGNOSTIC_TWOCHART_RESIDUAL_BASELINE_NOT_PROOF"
MORTAR_STATUS = "DIAGNOSTIC_TWOCHART_MORTAR_BASELINE_NOT_PROOF"
PDE_JACOBIAN_STATUS = "DIAGNOSTIC_TWOCHART_PDE_JACOBIAN_SMOKE_NOT_PROOF"
TWOCHART_FORMAT = "twochart_profile_projection_v1"
PDE_RESIDUAL_KIND_IDS = {
    "raw": 0,
    "geometric-normalized": 1,
    "normalized-structural": 2,
    "normalized-strict-tail": 3,
}


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


def point_in_patch(patch: dict[str, Any], q: float, x: float) -> bool:
    q0, q1, x0, x1 = patch_interval(patch)
    return q0 - 1e-14 <= q <= q1 + 1e-14 and x0 - 1e-14 <= x <= x1 + 1e-14


def one_hot_coeffs(patch: dict[str, Any], kq: int, kx: int) -> list[list[float]]:
    coeffs = patch["coeffs"]
    return [
        [1.0 if iq == kq and ix == kx else 0.0 for ix, _value in enumerate(row)]
        for iq, row in enumerate(coeffs)
    ]


def variable_tail_patch(data: dict[str, Any], variable: CoefficientVariable) -> dict[str, Any]:
    blocks = data["tail_chart"]["blocks"]
    if variable.frac_index is None:
        return blocks[variable.block][variable.patch_index]
    return blocks[variable.block][variable.frac_index - 1][variable.patch_index]


def delta_total_jet(
    data: dict[str, Any],
    variable: CoefficientVariable,
    component: str,
    r: Jet2,
    z: Jet2,
    q: Jet2,
    x: Jet2,
) -> Jet2:
    if variable.component != component:
        return Jet2.const(0.0)
    if variable.chart == "tail":
        patch = variable_tail_patch(data, variable)
        if not point_in_patch(patch, q.value(), x.value()):
            return Jet2.const(0.0)
        q0, q1, x0, x1 = patch_interval(patch)
        basis = cheb_eval_tensor_jet(
            one_hot_coeffs(patch, int(variable.kq), int(variable.kx)),
            q,
            x,
            q0,
            q1,
            x0,
            x1,
        )
        return q.pow(float(variable.alpha)) * basis
    if variable.chart == "origin":
        R = r * r
        Z = z * z
        return (R ** int(variable.r_power)) * (Z ** int(variable.z_power))
    return Jet2.const(0.0)


def delta_field_jets(
    data: dict[str, Any],
    projection: ProjectedProfile,
    variable: CoefficientVariable,
    r0: float,
    z0: float,
) -> tuple[Jet2, Jet2]:
    r = Jet2.var_r(r0)
    z = Jet2.var_z(z0)
    rho2 = r * r + z * z
    if rho2.value() <= 0.0:
        raise ValueError("PDE Jacobian rows are undefined at the physical origin")
    q = (1.0 + rho2).pow(-0.5)
    x = (z * z) / rho2
    dF = delta_total_jet(data, variable, "F", r, z, q, x)
    dG = delta_total_jet(data, variable, "G", r, z, q, x)
    dpsi = r * r * z * q.pow(projection.p) * dF
    dgamma = r * r * q.pow(projection.p) * dG
    return dpsi, dgamma


def linearized_raw_residual_at(
    data: dict[str, Any],
    projection: ProjectedProfile,
    variable: CoefficientVariable,
    r0: float,
    z0: float,
) -> Residual:
    if r0 <= 0.0:
        raise ValueError("PDE Jacobian rows are undefined on the axis r=0")
    r = Jet2.var_r(r0)
    z = Jet2.var_z(z0)
    psi = projection.psi_jet(r0, z0)
    gamma_field = projection.swirl_jet(r0, z0)
    dpsi, dgamma = delta_field_jets(data, projection, variable, r0, z0)

    psi_r = psi.dr()
    psi_z = psi.dz()
    gamma_r = gamma_field.dr()
    gamma_z = gamma_field.dz()
    dpsi_r = dpsi.dr()
    dpsi_z = dpsi.dz()
    dgamma_r = dgamma.dr()
    dgamma_z = dgamma.dz()

    a = psi.dr().dr() - psi.dr() / r + psi.dz().dz()
    da = dpsi.dr().dr() - dpsi.dr() / r + dpsi.dz().dz()
    a_r = a.dr()
    a_z = a.dz()
    da_r = da.dr()
    da_z = da.dz()

    e_psi = (
        (1.0 - projection.gamma) * r * r * da
        + projection.gamma * r * r * r * da_r
        + projection.gamma * z * r * r * da_z
        + r * (dpsi_r * a_z + psi_r * da_z - dpsi_z * a_r - psi_z * da_r)
        + 2.0 * dpsi_z * a
        + 2.0 * psi_z * da
        + (2.0 * gamma_field * dgamma).dz()
    )
    e_gamma = (
        (1.0 - 2.0 * projection.gamma) * dgamma
        + projection.gamma * (r * dgamma_r + z * dgamma_z)
        + (dpsi_r * gamma_z + psi_r * dgamma_z - dpsi_z * gamma_r - psi_z * dgamma_r) / r
    )
    return Residual(e_psi=e_psi.value(), e_gamma=e_gamma.value())


def linearized_residual_with_kind(
    data: dict[str, Any],
    projection: ProjectedProfile,
    variable: CoefficientVariable,
    q: float,
    b: float,
    residual_kind: str,
) -> Residual:
    r, z = qb_to_rz(q, b)
    raw = linearized_raw_residual_at(data, projection, variable, r, z)
    # The current normalized residual quotients depend only on q, b, and p.
    # If a future quotient depends on the profile itself, this linearization
    # must include the derivative of that normalization factor.
    return residual_with_kind(raw, q, b, projection.p, residual_kind)


def base_linearization_scalars(projection: ProjectedProfile, r0: float, z0: float) -> dict[str, float]:
    r = Jet2.var_r(r0)
    psi = projection.psi_jet(r0, z0)
    gamma_field = projection.swirl_jet(r0, z0)
    psi_r = psi.dr()
    psi_z = psi.dz()
    gamma_r = gamma_field.dr()
    gamma_z = gamma_field.dz()
    a = psi.dr().dr() - psi.dr() / r + psi.dz().dz()
    return {
        "psi_r": psi_r.value(),
        "psi_z": psi_z.value(),
        "swirl": gamma_field.value(),
        "swirl_r": gamma_r.value(),
        "swirl_z": gamma_z.value(),
        "a": a.value(),
        "a_r": a.dr().value(),
        "a_z": a.dz().value(),
    }


def native_tail_linearized_residuals_with_kind(
    data: dict[str, Any],
    projection: ProjectedProfile,
    variables: list[CoefficientVariable],
    q: float,
    b: float,
    residual_kind: str,
) -> tuple[dict[int, Residual], dict[str, Any]]:
    if residual_kind not in PDE_RESIDUAL_KIND_IDS:
        raise ValueError(f"unknown residual kind {residual_kind!r}")
    r0, z0 = qb_to_rz(q, b)
    if r0 <= 0.0:
        raise ValueError("native PDE rows are undefined on the axis r=0")
    x = b * b
    cases: list[tuple[CoefficientVariable, tuple[float, float, float, float]]] = []
    for variable in variables:
        if variable.chart != "tail":
            continue
        patch = variable_tail_patch(data, variable)
        if point_in_patch(patch, q, x):
            cases.append((variable, patch_interval(patch)))
    if not cases:
        return {}, {"enabled": True, "cases": 0, "seconds": 0.0}

    scalars = base_linearization_scalars(projection, r0, z0)
    lib = native_c_library()
    count = len(cases)
    double_array = ctypes.c_double * count
    int_array = ctypes.c_int * count
    q0_values = double_array(*[interval[0] for _variable, interval in cases])
    q1_values = double_array(*[interval[1] for _variable, interval in cases])
    x0_values = double_array(*[interval[2] for _variable, interval in cases])
    x1_values = double_array(*[interval[3] for _variable, interval in cases])
    alpha_values = double_array(*[float(variable.alpha) for variable, _interval in cases])
    kq_values = int_array(*[int(variable.kq) for variable, _interval in cases])
    kx_values = int_array(*[int(variable.kx) for variable, _interval in cases])
    component_values = int_array(*[0 if variable.component == "F" else 1 for variable, _interval in cases])
    out_e_psi = double_array()
    out_e_gamma = double_array()
    statuses = int_array()

    start = time.perf_counter()
    rc = lib.nsproof_pde_tail_coeff_columns_batch(
        count,
        PDE_RESIDUAL_KIND_IDS[residual_kind],
        float(projection.gamma),
        float(projection.p),
        float(q),
        float(b),
        float(scalars["psi_r"]),
        float(scalars["psi_z"]),
        float(scalars["swirl"]),
        float(scalars["swirl_r"]),
        float(scalars["swirl_z"]),
        float(scalars["a"]),
        float(scalars["a_r"]),
        float(scalars["a_z"]),
        q0_values,
        q1_values,
        x0_values,
        x1_values,
        alpha_values,
        kq_values,
        kx_values,
        component_values,
        out_e_psi,
        out_e_gamma,
        statuses,
    )
    elapsed = time.perf_counter() - start
    if rc != 0:
        bad_statuses = sorted(set(int(statuses[index]) for index in range(count)))
        raise RuntimeError(f"native C PDE tail batch failed rc={rc} statuses={bad_statuses}")

    return {
        variable.index: Residual(e_psi=float(out_e_psi[row]), e_gamma=float(out_e_gamma[row]))
        for row, (variable, _interval) in enumerate(cases)
    }, {"enabled": True, "cases": count, "seconds": elapsed}


def perturb_variable(data: dict[str, Any], variable: CoefficientVariable, delta: float) -> dict[str, Any]:
    out = json.loads(json.dumps(data))
    set_path(out, variable.path, float(get_path(out, variable.path)) + delta)
    return out


def finite_difference_column(
    data: dict[str, Any],
    variable: CoefficientVariable,
    q: float,
    b: float,
    residual_kind: str,
    epsilon: float,
) -> Residual:
    plus = perturb_variable(data, variable, epsilon)
    minus = perturb_variable(data, variable, -epsilon)
    plus_projection = projection_from_twochart(plus)
    minus_projection = projection_from_twochart(minus)
    r, z = qb_to_rz(q, b)
    plus_residual = residual_with_kind(
        plus_projection.exact_residual_at(r, z),
        q,
        b,
        plus_projection.p,
        residual_kind,
    )
    minus_residual = residual_with_kind(
        minus_projection.exact_residual_at(r, z),
        q,
        b,
        minus_projection.p,
        residual_kind,
    )
    scale = 1.0 / (2.0 * epsilon)
    return Residual(
        e_psi=(plus_residual.e_psi - minus_residual.e_psi) * scale,
        e_gamma=(plus_residual.e_gamma - minus_residual.e_gamma) * scale,
    )


def choose_smoke_variables(data: dict[str, Any], projection: ProjectedProfile) -> list[CoefficientVariable]:
    variables = enumerate_coefficients(data)
    wanted = {
        ("tail", "F", "F_an"),
        ("tail", "G", "G_an"),
        ("tail", "F", "F_frac"),
        ("tail", "G", "G_frac"),
        ("origin", "F", "F_origin_taylor"),
        ("origin", "G", "G_origin_taylor"),
    }
    chosen: list[CoefficientVariable] = []
    safe_points = [(0.45, 0.30), (0.61, 0.24), (0.93, 0.35), (0.96, 0.70)]
    for variable in variables:
        key = (variable.chart, variable.component, variable.block)
        if key not in wanted:
            continue
        if variable.chart == "origin" and int(variable.r_power) + int(variable.z_power) == 0:
            continue
        active = False
        for q, b in safe_points:
            if not compactified_residual_defined(q, b, projection.p, "normalized-structural"):
                continue
            value = linearized_residual_with_kind(data, projection, variable, q, b, "normalized-structural")
            if max(abs(value.e_psi), abs(value.e_gamma)) > 1e-12:
                active = True
                break
        if active:
            chosen.append(variable)
            wanted.remove(key)
        if not wanted:
            break
    if wanted:
        raise RuntimeError(f"could not choose active smoke variables for {sorted(wanted)}")
    return chosen


def eval_residual_and_jacobian(
    profile: str | dict[str, Any],
    residual_kind: str = "normalized-structural",
    epsilon: float = 1e-6,
) -> dict[str, Any]:
    """Small diagnostic PDE residual/Jacobian smoke hook.

    This is intentionally not the production Newton matrix.  It verifies the
    analytic linearized PDE columns on representative variables and points.
    """

    data = load_json(profile) if isinstance(profile, str) else profile
    enforce_twochart_gate(data, profile if isinstance(profile, str) else "<dict>")
    projection = projection_from_twochart(data)
    variables = choose_smoke_variables(data, projection)
    points = [(0.45, 0.30), (0.61, 0.24), (0.93, 0.35), (0.96, 0.70)]
    checks: list[dict[str, Any]] = []
    for variable in variables:
        best: dict[str, Any] | None = None
        for q, b in points:
            analytic = linearized_residual_with_kind(data, projection, variable, q, b, residual_kind)
            if max(abs(analytic.e_psi), abs(analytic.e_gamma)) <= 1e-12:
                continue
            fd = finite_difference_column(data, variable, q, b, residual_kind, epsilon)
            abs_e_psi = abs(analytic.e_psi - fd.e_psi)
            abs_e_gamma = abs(analytic.e_gamma - fd.e_gamma)
            rel = max(abs_e_psi, abs_e_gamma) / max(1.0, abs(analytic.e_psi), abs(analytic.e_gamma))
            candidate = {
                "variable": variable.as_json(),
                "q": q,
                "b": b,
                "analytic_e_psi": analytic.e_psi,
                "analytic_e_gamma": analytic.e_gamma,
                "fd_e_psi": fd.e_psi,
                "fd_e_gamma": fd.e_gamma,
                "abs_e_psi": abs_e_psi,
                "abs_e_gamma": abs_e_gamma,
                "relative": rel,
            }
            if best is None or candidate["relative"] < best["relative"]:
                best = candidate
        if best is None:
            raise RuntimeError(f"selected variable {variable.label} was inactive on all smoke points")
        checks.append(best)
    return {
        "status": PDE_JACOBIAN_STATUS,
        "diagnostic_vs_proof": "floating PDE Jacobian smoke only; no Newton solve or interval proof",
        "residual_kind": residual_kind,
        "epsilon": epsilon,
        "checks": checks,
        "max_abs_diff": max(max(item["abs_e_psi"], item["abs_e_gamma"]) for item in checks),
        "max_relative_diff": max(item["relative"] for item in checks),
    }


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


def mortar_metadata(data: dict[str, Any], profile_path: str, args: argparse.Namespace) -> dict[str, Any]:
    q_values = local_grid(args.overlap_q_min, args.overlap_q_max, args.mortar_q_samples)
    x_values = local_grid(0.0, 1.0, args.mortar_x_samples)
    rows = build_rz_rows(data, [], q_values, x_values, args.mortar_order)
    rz = summarize_rows(rows)
    return {
        "status": MORTAR_STATUS,
        "diagnostic_vs_proof": "sampled floating two-chart R,Z mortar metadata only; no interval smoothness proof",
        "profile": relpath(profile_path),
        "source_profile_json": relpath(str(data.get("source_profile_json") or "")),
        "coordinate_derivatives": "R,Z",
        "orders": f"C0-C{args.mortar_order}",
        "overlap_q_range": [args.overlap_q_min, args.overlap_q_max],
        "x_range": [0.0, 1.0],
        "sample_shape": {"q_samples": args.mortar_q_samples, "x_samples": args.mortar_x_samples},
        "rz_mortar": {
            "status": "TWOCHART_RZ_MORTAR_METADATA_NOT_INTERVAL",
            "max_abs_diff": rz["max_abs"],
            "rms_diff": rz["rms"],
            "summary": rz,
        },
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

    mortar = mortar_metadata(data, profile_path, args)
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
    parser.add_argument("--pde-jacobian-smoke-out", default="", help="Optional PDE Jacobian smoke JSON output")
    parser.add_argument("--pde-jacobian-epsilon", type=float, default=1e-6)
    args = parser.parse_args()

    if args.h <= 0.0:
        raise ValueError("--h must be positive")
    if not (0.0 < args.overlap_q_min <= args.overlap_q_max < 1.0):
        raise ValueError("require 0 < --overlap-q-min <= --overlap-q-max < 1")
    if args.mortar_q_samples <= 0 or args.mortar_x_samples <= 0:
        raise ValueError("mortar sample counts must be positive")
    if args.mortar_order < 0 or args.mortar_order > 4:
        raise ValueError("--mortar-order must be between 0 and 4")
    if args.pde_jacobian_epsilon <= 0.0:
        raise ValueError("--pde-jacobian-epsilon must be positive")

    report, mortar = build_report(args)
    print_summary(report)
    if args.out:
        save_json(args.out, report)
        print(f"saved={args.out}")
    if args.mortar_out:
        save_json(args.mortar_out, mortar)
        print(f"mortar_saved={args.mortar_out}")
    if args.pde_jacobian_smoke_out:
        smoke = eval_residual_and_jacobian(
            resolve_profile_path(args.profile),
            residual_kind=args.residual_kind,
            epsilon=args.pde_jacobian_epsilon,
        )
        save_json(args.pde_jacobian_smoke_out, smoke)
        print(
            "pde_jacobian_smoke="
            f"max_abs_diff={float(smoke['max_abs_diff']):.12e} "
            f"max_relative_diff={float(smoke['max_relative_diff']):.12e}"
        )
        print(f"pde_jacobian_smoke_saved={args.pde_jacobian_smoke_out}")


if __name__ == "__main__":
    main()
