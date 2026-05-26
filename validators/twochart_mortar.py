#!/usr/bin/env python3
"""Read-only two-chart mortar audit scaffold.

The intended proof object is a hard two-chart profile with a tail chart in
``(q, x=b^2)`` and an origin chart in ``(R,Z)=(r^2,z^2)``.  That schema is not
present in this repository yet, so this validator also audits the existing
``transseries_cheb_projection_v1`` artifacts by comparing the rectangular
projection against the origin Taylor chart over the proposed overlap band.

This is diagnostic floating-point evidence only.  It is not an interval
smoothness proof and it does not certify a profile.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from compactified_profile import grid
from profile_newton_cheb import (  # type: ignore[import-not-found]
    as_patch_items,
    find_patch_index,
    load_json,
    patch_interval,
    total_partial_value,
)


STATUS = "TWOCHART_MORTAR_AUDIT_DIAGNOSTIC_NOT_PROOF"
TWOCHART_FORMATS = {"twochart_profile_v1", "compactified_twochart_profile_v1"}


@dataclass(frozen=True)
class DerivativeSpec:
    dq_order: int
    dx_order: int

    @property
    def order(self) -> int:
        return self.dq_order + self.dx_order

    @property
    def label(self) -> str:
        if self.order == 0:
            return "value"
        return f"dq{self.dq_order}_dx{self.dx_order}"


@dataclass(frozen=True)
class MortarRow:
    component: str
    q: float
    x: float
    dq_order: int
    dx_order: int
    rect_value: float
    origin_value: float
    diff: float

    @property
    def order(self) -> int:
        return self.dq_order + self.dx_order

    @property
    def abs_diff(self) -> float:
        return abs(self.diff)

    def as_json(self) -> dict[str, object]:
        return {
            "component": self.component,
            "q": self.q,
            "x": self.x,
            "derivative_order": self.order,
            "dq_order": self.dq_order,
            "dx_order": self.dx_order,
            "rect_value": self.rect_value,
            "origin_value": self.origin_value,
            "diff_rect_minus_origin": self.diff,
            "abs": self.abs_diff,
        }


def save_json(path: str, data: dict[str, object]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def derivative_specs(max_order: int) -> tuple[DerivativeSpec, ...]:
    if max_order < 0 or max_order > 3:
        raise ValueError("--max-order must be between 0 and 3")
    return tuple(
        DerivativeSpec(dq_order=dq, dx_order=total - dq)
        for total in range(max_order + 1)
        for dq in range(total + 1)
    )


def falling(value: float, order: int) -> float:
    out = 1.0
    for k in range(order):
        out *= value - k
    return out


def binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def cheb_basis_values(count: int, t: float, order: int) -> list[float]:
    if order < 0 or order > 3:
        raise ValueError("Chebyshev derivative order must be between 0 and 3")
    if count <= 0:
        return []
    derivs = [[0.0 for _ in range(count)] for _ in range(order + 1)]
    derivs[0][0] = 1.0
    if count > 1:
        derivs[0][1] = t
        if order >= 1:
            derivs[1][1] = 1.0
    for n in range(2, count):
        for m in range(order + 1):
            value = 2.0 * t * derivs[m][n - 1] - derivs[m][n - 2]
            if m > 0:
                value += 2.0 * m * derivs[m - 1][n - 1]
            derivs[m][n] = value
    return derivs[order]


def cheb_eval_tensor_partial3(
    coeffs: list[list[float]],
    q: float,
    x: float,
    q0: float,
    q1: float,
    x0: float,
    x1: float,
    dq_order: int,
    dx_order: int,
) -> float:
    if dq_order < 0 or dx_order < 0 or dq_order + dx_order > 3:
        raise ValueError("only partial derivatives through total order 3 are supported")
    if q1 == q0 or x1 == x0:
        raise ValueError("cannot differentiate degenerate Chebyshev patch")
    tq = (2.0 * q - q0 - q1) / (q1 - q0)
    tx = (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = cheb_basis_values(len(coeffs), tq, dq_order)
    x_count = len(coeffs[0]) if coeffs else 0
    x_values = cheb_basis_values(x_count, tx, dx_order)
    total = 0.0
    for iq, row in enumerate(coeffs):
        for ix, coeff in enumerate(row):
            total += float(coeff) * q_values[iq] * x_values[ix]
    total *= (2.0 / (q1 - q0)) ** dq_order
    total *= (2.0 / (x1 - x0)) ** dx_order
    return total


def eval_patch_item_partial3(
    patch: dict[str, object],
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    q0, q1, x0, x1 = patch_interval(patch)
    return cheb_eval_tensor_partial3(
        patch["coeffs"],  # type: ignore[arg-type,index]
        q,
        x,
        q0,
        q1,
        x0,
        x1,
        dq_order,
        dx_order,
    )


def weighted_patch_partial(
    patch: dict[str, object],
    alpha: float,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    total = 0.0
    for i in range(dq_order + 1):
        q_weight = falling(alpha, i) * (q ** (alpha - i))
        patch_partial = eval_patch_item_partial3(patch, q, x, dq_order - i, dx_order)
        total += binom(dq_order, i) * q_weight * patch_partial
    return total


def eval_rect_total_partial3(
    data: dict[str, object],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    if dq_order + dx_order <= 2:
        return total_partial_value(data, component, q, x, dq_order, dx_order, "rect")
    p = float(data["p"])
    if component == "F":
        constant = 0.5
        analytic_block = "F_an"
        frac_key = "F_frac"
    elif component == "G":
        constant = float(data["B"])
        analytic_block = "G_an"
        frac_key = "G_frac"
    else:
        raise ValueError(f"unknown component {component!r}")

    total = constant if dq_order == 0 and dx_order == 0 else 0.0
    analytic_patches = as_patch_items(data, analytic_block)
    analytic_patch = analytic_patches[find_patch_index(analytic_patches, q, x)]
    total += weighted_patch_partial(analytic_patch, 2.0, q, x, dq_order, dx_order)
    for k, block in enumerate(data["blocks"][frac_key], start=1):  # type: ignore[index]
        patch_index = find_patch_index(block, q, x)
        total += weighted_patch_partial(block[patch_index], k * p, q, x, dq_order, dx_order)
    return total


def origin_h_partial(power: int, q: float, order: int) -> float:
    if power == 0:
        return 1.0 if order == 0 else 0.0
    total = 0.0
    for k in range(power + 1):
        coeff = binom(power, k) * ((-1.0) ** (power - k))
        exponent = -2.0 * k
        total += coeff * falling(exponent, order) * (q ** (exponent - order))
    return total


def origin_x_partial(r_power: int, z_power: int, x: float, order: int) -> float:
    total = 0.0
    for i in range(order + 1):
        j = order - i
        if i > r_power or j > z_power:
            continue
        left = ((-1.0) ** i) * falling(float(r_power), i) * ((1.0 - x) ** (r_power - i))
        right = falling(float(z_power), j) * (x ** (z_power - j))
        total += binom(order, i) * left * right
    return total


def eval_origin_total_partial3(
    data: dict[str, object],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    if dq_order + dx_order <= 2:
        return total_partial_value(data, component, q, x, dq_order, dx_order, "origin")
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["blocks"][key]  # type: ignore[index]
    total = 0.0
    for entry in origin.get("basis", []):  # type: ignore[union-attr]
        r_power = int(entry["R_power"])
        z_power = int(entry["Z_power"])
        coeff = float(entry["coeff"])
        total += (
            coeff
            * origin_h_partial(r_power + z_power, q, dq_order)
            * origin_x_partial(r_power, z_power, x, dx_order)
        )
    return total


def is_existing_projection(data: dict[str, object]) -> bool:
    return data.get("format") == "transseries_cheb_projection_v1" and isinstance(data.get("blocks"), dict)


def is_twochart_candidate(data: dict[str, object]) -> bool:
    fmt = data.get("format")
    return fmt in TWOCHART_FORMATS or (
        isinstance(data.get("tail_chart"), dict) and isinstance(data.get("origin_chart"), dict)
    )


def origin_enabled(data: dict[str, object], component: str) -> bool:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["blocks"].get(key, {})  # type: ignore[union-attr]
    return bool(origin.get("enabled", False)) if isinstance(origin, dict) else False


def audit_existing_projection(
    data: dict[str, object],
    q_min: float,
    q_max: float,
    q_samples: int,
    x_samples: int,
    max_order: int,
) -> dict[str, object]:
    specs = derivative_specs(max_order)
    rows: list[MortarRow] = []
    skipped_components: list[str] = []
    for component in ("F", "G"):
        if not origin_enabled(data, component):
            skipped_components.append(component)
            continue
        for q in grid(q_min, q_max, q_samples):
            for x in grid(0.0, 1.0, x_samples):
                for spec in specs:
                    rect = eval_rect_total_partial3(data, component, q, x, spec.dq_order, spec.dx_order)
                    origin = eval_origin_total_partial3(data, component, q, x, spec.dq_order, spec.dx_order)
                    rows.append(
                        MortarRow(
                            component=component,
                            q=q,
                            x=x,
                            dq_order=spec.dq_order,
                            dx_order=spec.dx_order,
                            rect_value=rect,
                            origin_value=origin,
                            diff=rect - origin,
                        )
                    )
    return summarize_rows(rows, skipped_components)


def summarize_rows(rows: list[MortarRow], skipped_components: list[str]) -> dict[str, object]:
    groups: dict[str, dict[str, object]] = {}
    total_sq = 0.0
    worst = max(rows, key=lambda row: row.abs_diff, default=None)
    for row in rows:
        total_sq += row.diff * row.diff
        keys = (
            f"component:{row.component}",
            f"order:C{row.order}",
            f"component_order:{row.component}:C{row.order}",
            f"component_partial:{row.component}:dq{row.dq_order}_dx{row.dx_order}",
        )
        for key in keys:
            group = groups.setdefault(
                key,
                {
                    "key": key,
                    "count": 0,
                    "max_abs": 0.0,
                    "rms_sum": 0.0,
                    "worst": None,
                },
            )
            group["count"] = int(group["count"]) + 1
            group["rms_sum"] = float(group["rms_sum"]) + row.diff * row.diff
            if row.abs_diff > float(group["max_abs"]):
                group["max_abs"] = row.abs_diff
                group["worst"] = row.as_json()

    group_items = []
    for group in groups.values():
        count = int(group["count"])
        group_items.append(
            {
                "key": group["key"],
                "count": count,
                "max_abs": group["max_abs"],
                "rms": math.sqrt(float(group["rms_sum"]) / max(count, 1)),
                "worst": group["worst"],
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    top_rows = sorted(rows, key=lambda row: row.abs_diff, reverse=True)[:20]
    return {
        "count": len(rows),
        "max_abs": worst.abs_diff if worst else 0.0,
        "rms": math.sqrt(total_sq / max(len(rows), 1)),
        "worst": worst.as_json() if worst else {},
        "groups": group_items,
        "top_rows": [row.as_json() for row in top_rows],
        "skipped_components": skipped_components,
    }


def candidate_score(path: str, data: dict[str, object]) -> tuple[int, float, str]:
    name = os.path.basename(path)
    score = 0
    if "q2zero" in name:
        score += 100
    if "origin_refit" in name:
        score += 30
    if "c2" in name.lower():
        score += 20
    if "d6" in name.lower():
        score += 10
    if "formal" in name:
        score += 5
    if data.get("origin_mortar_refit_evidence"):
        score += 20
    if data.get("q2_trace_zeroing_evidence"):
        score += 20
    return score, os.path.getmtime(path), path


def choose_default_profile() -> tuple[str, list[str]]:
    candidates: list[tuple[int, float, str]] = []
    considered: list[str] = []
    for path in glob.glob(os.path.join(ROOT_DIR, "work", "*q2zero*.json")):
        try:
            data = load_json(path)
        except Exception:
            continue
        if not (is_existing_projection(data) or is_twochart_candidate(data)):
            continue
        considered.append(os.path.relpath(path, ROOT_DIR))
        candidates.append(candidate_score(path, data))
    if not candidates:
        for path in glob.glob(os.path.join(ROOT_DIR, "work", "*.json")):
            try:
                data = load_json(path)
            except Exception:
                continue
            if is_existing_projection(data) or is_twochart_candidate(data):
                considered.append(os.path.relpath(path, ROOT_DIR))
                candidates.append(candidate_score(path, data))
    if not candidates:
        raise FileNotFoundError("no usable profile JSON found; pass --profile explicitly")
    candidates.sort(reverse=True)
    return candidates[0][2], sorted(set(considered))


def audit_profile(args: argparse.Namespace) -> dict[str, object]:
    selected_by = "explicit"
    considered: list[str] = []
    profile = args.profile
    if not profile:
        profile, considered = choose_default_profile()
        selected_by = "auto-best-q2zero"
    data = load_json(profile)

    profile_rel = os.path.relpath(profile, ROOT_DIR) if os.path.isabs(profile) else profile
    base: dict[str, object] = {
        "status": STATUS,
        "profile": profile_rel,
        "selected_by": selected_by,
        "considered_profiles": considered,
        "q_band": [args.q_min, args.q_max],
        "q_samples": args.q_samples,
        "x_samples": args.x_samples,
        "max_order": args.max_order,
        "diagnostic_vs_proof": "diagnostic floating-point mortar audit; not an interval proof",
    }

    if is_existing_projection(data):
        summary = audit_existing_projection(
            data,
            q_min=args.q_min,
            q_max=args.q_max,
            q_samples=args.q_samples,
            x_samples=args.x_samples,
            max_order=args.max_order,
        )
        return {
            **base,
            "schema_mode": "existing_transseries_projection_rect_vs_origin",
            "summary": summary,
        }
    if is_twochart_candidate(data):
        return {
            **base,
            "schema_mode": "twochart_schema_detected_scaffold_only",
            "summary": {
                "count": 0,
                "max_abs": 0.0,
                "rms": 0.0,
                "worst": {},
                "groups": [],
                "top_rows": [],
                "note": (
                    "A two-chart-looking profile was detected, but no stable "
                    "repo evaluator for that schema exists yet. This scaffold "
                    "therefore refuses to report proof-like mismatch numbers."
                ),
            },
        }
    raise ValueError(f"unsupported profile schema in {profile!r}: format={data.get('format')!r}")


def print_summary(result: dict[str, object]) -> None:
    summary = result["summary"]  # type: ignore[index]
    print(f"profile={result['profile']}")
    print(f"schema_mode={result['schema_mode']}")
    print(f"q_band={result['q_band']} q_samples={result['q_samples']} x_samples={result['x_samples']}")
    print(f"max_order=C{result['max_order']}")
    print(f"rows={summary['count']}")
    print(f"max_abs={float(summary['max_abs']):.12e}")
    print(f"rms={float(summary['rms']):.12e}")
    print(f"worst={summary['worst']}")
    print("top_groups:")
    for group in summary.get("groups", [])[:12]:  # type: ignore[union-attr]
        print(
            f"  {group['key']} count={group['count']} "
            f"max_abs={float(group['max_abs']):.12e} rms={float(group['rms']):.12e}"
        )
    print(f"status={result['status']}")
    print(f"diagnostic_vs_proof={result['diagnostic_vs_proof']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="", help="Profile JSON. Default auto-picks best work/*q2zero*.json.")
    parser.add_argument("--q-min", type=float, default=0.84)
    parser.add_argument("--q-max", type=float, default=0.92)
    parser.add_argument("--q-samples", type=int, default=17)
    parser.add_argument("--x-samples", type=int, default=17)
    parser.add_argument("--max-order", type=int, default=2, help="Audit C0..Ck, k<=3.")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    if not (0.0 < args.q_min <= args.q_max < 1.0):
        raise ValueError("require 0 < --q-min <= --q-max < 1")
    if args.q_samples <= 0 or args.x_samples <= 0:
        raise ValueError("sample counts must be positive")

    result = audit_profile(args)
    print_summary(result)
    if args.json_out:
        save_json(args.json_out, result)


if __name__ == "__main__":
    main()
