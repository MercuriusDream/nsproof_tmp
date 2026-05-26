#!/usr/bin/env python3
"""Floating two-chart overlap mortar residual/Jacobian rows.

This is a diagnostic builder for ``twochart_profile_projection_v1`` artifacts.
It compares tail total F/G against origin total F/G on the overlap in
``(q, x)`` coordinates and emits exact floating sparse Jacobian entries with
respect to the JSON coefficients.  It is not an interval proof and does not
certify smoothness or existence.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Iterable


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
STATUS = "TWOCHART_MORTAR_JACOBIAN_FLOATING_NOT_PROOF"
SUPPORTED_FORMAT = "twochart_profile_projection_v1"


@dataclass(frozen=True)
class DerivativeSpec:
    dq_order: int
    dx_order: int

    @property
    def total_order(self) -> int:
        return self.dq_order + self.dx_order

    @property
    def label(self) -> str:
        if self.total_order == 0:
            return "value"
        return "d" + ("q" * self.dq_order) + ("x" * self.dx_order)


@dataclass(frozen=True)
class CoefficientVariable:
    index: int
    chart: str
    component: str
    block: str
    path: tuple[Any, ...]
    label: str
    value: float
    alpha: float | None = None
    patch_index: int | None = None
    frac_index: int | None = None
    kq: int | None = None
    kx: int | None = None
    r_power: int | None = None
    z_power: int | None = None

    def as_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "index": self.index,
            "chart": self.chart,
            "component": self.component,
            "block": self.block,
            "path": list(self.path),
            "label": self.label,
            "value": self.value,
        }
        for key in ("alpha", "patch_index", "frac_index", "kq", "kx", "r_power", "z_power"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        return out


@dataclass(frozen=True)
class MortarRow:
    row_index: int
    component: str
    q: float
    x: float
    dq_order: int
    dx_order: int
    tail_value: float
    origin_value: float
    residual: float
    jacobian: tuple[tuple[int, float], ...]

    @property
    def derivative(self) -> DerivativeSpec:
        return DerivativeSpec(self.dq_order, self.dx_order)

    @property
    def abs_residual(self) -> float:
        return abs(self.residual)

    def as_json(self, variables: list[CoefficientVariable] | None = None) -> dict[str, Any]:
        if variables is None:
            jacobian: list[dict[str, Any]] = [
                {"var_index": var_index, "value": value} for var_index, value in self.jacobian
            ]
        else:
            jacobian = [
                {
                    "var_index": var_index,
                    "variable": variables[var_index].label,
                    "value": value,
                }
                for var_index, value in self.jacobian
            ]
        return {
            "row_index": self.row_index,
            "component": self.component,
            "q": self.q,
            "x": self.x,
            "derivative": self.derivative.label,
            "dq_order": self.dq_order,
            "dx_order": self.dx_order,
            "total_order": self.dq_order + self.dx_order,
            "tail_value": self.tail_value,
            "origin_value": self.origin_value,
            "residual_tail_minus_origin": self.residual,
            "abs_residual": self.abs_residual,
            "jacobian_nnz": len(self.jacobian),
            "jacobian": jacobian,
        }


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != SUPPORTED_FORMAT:
        raise ValueError(f"{path!r} has format={data.get('format')!r}; expected {SUPPORTED_FORMAT!r}")
    enforce_tail_gate(data, path)
    return data


def enforce_tail_gate(data: dict[str, Any], profile: str) -> None:
    tail = data.get("tail_legality")
    if not isinstance(tail, dict):
        raise ValueError(f"{profile!r} is missing tail_legality")
    if tail.get("all_ok") is not True:
        raise ValueError(f"{profile!r} tail_legality.all_ok is not true: status={tail.get('status')!r}")
    if tail.get("q2_policy") != "zero" or tail.get("q2_ok") is not True:
        raise ValueError(
            f"{profile!r} must have q2_policy=zero and q2_ok=true; "
            f"got q2_policy={tail.get('q2_policy')!r} q2_ok={tail.get('q2_ok')!r}"
        )


def save_json(path: str, data: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def grid(lo: float, hi: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("sample count must be positive")
    if count == 1:
        return [(lo + hi) / 2.0]
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def derivative_specs(max_order: int) -> tuple[DerivativeSpec, ...]:
    if max_order < 0 or max_order > 4:
        raise ValueError("--max-order must be between 0 and 4")
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


def patch_interval(patch: dict[str, Any]) -> tuple[float, float, float, float]:
    q0, q1 = patch["q_interval"]
    x0, x1 = patch["x_interval"]
    return float(q0), float(q1), float(x0), float(x1)


def find_patch_index(patches: list[dict[str, Any]], q: float, x: float) -> int:
    for index, patch in enumerate(patches):
        q0, q1, x0, x1 = patch_interval(patch)
        if q0 - 1e-14 <= q <= q1 + 1e-14 and x0 - 1e-14 <= x <= x1 + 1e-14:
            return index
    raise ValueError(f"point outside patch inventory: q={q} x={x}")


def cheb_basis_values(count: int, t: float, order: int) -> list[float]:
    if order < 0 or order > 4:
        raise ValueError("Chebyshev derivative order must be between 0 and 4")
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


def cheb_basis_partial(
    patch: dict[str, Any],
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    q0, q1, x0, x1 = patch_interval(patch)
    if q1 == q0 or x1 == x0:
        raise ValueError("cannot differentiate degenerate Chebyshev patch")
    tq = (2.0 * q - q0 - q1) / (q1 - q0)
    tx = (2.0 * x - x0 - x1) / (x1 - x0)
    q_values = cheb_basis_values(kq + 1, tq, dq_order)
    x_values = cheb_basis_values(kx + 1, tx, dx_order)
    return (
        q_values[kq]
        * x_values[kx]
        * ((2.0 / (q1 - q0)) ** dq_order)
        * ((2.0 / (x1 - x0)) ** dx_order)
    )


def cheb_eval_tensor_partial(
    patch: dict[str, Any],
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    coeffs = patch["coeffs"]
    total = 0.0
    for kq, row in enumerate(coeffs):
        for kx, coeff in enumerate(row):
            total += float(coeff) * cheb_basis_partial(patch, q, x, kq, kx, dq_order, dx_order)
    return total


def weighted_patch_partial(
    patch: dict[str, Any],
    alpha: float,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    total = 0.0
    for i in range(dq_order + 1):
        q_weight = falling(alpha, i) * (q ** (alpha - i))
        patch_partial = cheb_eval_tensor_partial(patch, q, x, dq_order - i, dx_order)
        total += binom(dq_order, i) * q_weight * patch_partial
    return total


def weighted_cheb_coeff_partial(
    patch: dict[str, Any],
    alpha: float,
    q: float,
    x: float,
    kq: int,
    kx: int,
    dq_order: int,
    dx_order: int,
) -> float:
    total = 0.0
    for i in range(dq_order + 1):
        q_weight = falling(alpha, i) * (q ** (alpha - i))
        basis_partial = cheb_basis_partial(patch, q, x, kq, kx, dq_order - i, dx_order)
        total += binom(dq_order, i) * q_weight * basis_partial
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


def origin_coeff_partial(
    r_power: int,
    z_power: int,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    return origin_h_partial(r_power + z_power, q, dq_order) * origin_x_partial(
        r_power, z_power, x, dx_order
    )


def tail_total_partial(
    data: dict[str, Any],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])
    if component == "F":
        constant = 0.5
        analytic_block = "F_an"
        frac_block = "F_frac"
    elif component == "G":
        constant = float(data["B"])
        analytic_block = "G_an"
        frac_block = "G_frac"
    else:
        raise ValueError(f"unknown component {component!r}")
    total = constant if dq_order == 0 and dx_order == 0 else 0.0
    analytic_patches = blocks[analytic_block]
    analytic_patch = analytic_patches[find_patch_index(analytic_patches, q, x)]
    total += weighted_patch_partial(analytic_patch, 2.0, q, x, dq_order, dx_order)
    for frac_index, frac_patches in enumerate(blocks.get(frac_block, []), start=1):
        frac_patch = frac_patches[find_patch_index(frac_patches, q, x)]
        total += weighted_patch_partial(frac_patch, frac_index * p, q, x, dq_order, dx_order)
    return total


def origin_total_partial(
    data: dict[str, Any],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> float:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["origin_chart"]["blocks"][key]
    total = 0.0
    for entry in origin.get("basis", []):
        r_power = int(entry["R_power"])
        z_power = int(entry["Z_power"])
        total += float(entry["coeff"]) * origin_coeff_partial(
            r_power, z_power, q, x, dq_order, dx_order
        )
    return total


def enumerate_coefficients(data: dict[str, Any]) -> list[CoefficientVariable]:
    variables: list[CoefficientVariable] = []
    tail_blocks = data["tail_chart"]["blocks"]
    p = float(data["p"])

    def add_tail_block(component: str, block: str, patches: list[dict[str, Any]], alpha: float) -> None:
        for patch_index, patch in enumerate(patches):
            for kq, row in enumerate(patch["coeffs"]):
                for kx, value in enumerate(row):
                    path = (
                        "tail_chart",
                        "blocks",
                        block,
                        patch_index,
                        "coeffs",
                        kq,
                        kx,
                    )
                    variables.append(
                        CoefficientVariable(
                            index=len(variables),
                            chart="tail",
                            component=component,
                            block=block,
                            path=path,
                            label=f"tail.{block}[p{patch_index}].c[{kq},{kx}]",
                            value=float(value),
                            alpha=alpha,
                            patch_index=patch_index,
                            kq=kq,
                            kx=kx,
                        )
                    )

    def add_tail_frac(component: str, block: str, frac_blocks: list[list[dict[str, Any]]]) -> None:
        for frac_zero_index, patches in enumerate(frac_blocks):
            frac_index = frac_zero_index + 1
            for patch_index, patch in enumerate(patches):
                for kq, row in enumerate(patch["coeffs"]):
                    for kx, value in enumerate(row):
                        path = (
                            "tail_chart",
                            "blocks",
                            block,
                            frac_zero_index,
                            patch_index,
                            "coeffs",
                            kq,
                            kx,
                        )
                        variables.append(
                            CoefficientVariable(
                                index=len(variables),
                                chart="tail",
                                component=component,
                                block=block,
                                path=path,
                                label=f"tail.{block}[f{frac_index}][p{patch_index}].c[{kq},{kx}]",
                                value=float(value),
                                alpha=frac_index * p,
                                patch_index=patch_index,
                                frac_index=frac_index,
                                kq=kq,
                                kx=kx,
                            )
                        )

    add_tail_block("F", "F_an", tail_blocks["F_an"], 2.0)
    add_tail_frac("F", "F_frac", tail_blocks.get("F_frac", []))
    add_tail_block("G", "G_an", tail_blocks["G_an"], 2.0)
    add_tail_frac("G", "G_frac", tail_blocks.get("G_frac", []))

    origin_blocks = data["origin_chart"]["blocks"]
    for component, block in (("F", "F_origin_taylor"), ("G", "G_origin_taylor")):
        for basis_index, entry in enumerate(origin_blocks[block].get("basis", [])):
            r_power = int(entry["R_power"])
            z_power = int(entry["Z_power"])
            path = ("origin_chart", "blocks", block, "basis", basis_index, "coeff")
            variables.append(
                CoefficientVariable(
                    index=len(variables),
                    chart="origin",
                    component=component,
                    block=block,
                    path=path,
                    label=f"origin.{block}[{r_power},{z_power}]",
                    value=float(entry["coeff"]),
                    r_power=r_power,
                    z_power=z_power,
                )
            )
    return variables


def active_jacobian(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    component: str,
    q: float,
    x: float,
    dq_order: int,
    dx_order: int,
) -> tuple[tuple[int, float], ...]:
    blocks = data["tail_chart"]["blocks"]
    active_tail_patches: dict[str, int] = {}
    for block_name in ("F_an", "G_an"):
        active_tail_patches[block_name] = find_patch_index(blocks[block_name], q, x)
    for block_name in ("F_frac", "G_frac"):
        for frac_zero_index, frac_patches in enumerate(blocks.get(block_name, [])):
            active_tail_patches[f"{block_name}:{frac_zero_index + 1}"] = find_patch_index(frac_patches, q, x)

    jac: list[tuple[int, float]] = []
    for variable in variables:
        if variable.component != component:
            continue
        if variable.chart == "tail":
            if variable.frac_index is None:
                active_key = variable.block
                patch = blocks[variable.block][variable.patch_index]
            else:
                active_key = f"{variable.block}:{variable.frac_index}"
                patch = blocks[variable.block][variable.frac_index - 1][variable.patch_index]
            if active_tail_patches[active_key] != variable.patch_index:
                continue
            value = weighted_cheb_coeff_partial(
                patch,
                float(variable.alpha),
                q,
                x,
                int(variable.kq),
                int(variable.kx),
                dq_order,
                dx_order,
            )
        elif variable.chart == "origin":
            value = -origin_coeff_partial(
                int(variable.r_power),
                int(variable.z_power),
                q,
                x,
                dq_order,
                dx_order,
            )
        else:
            continue
        if value != 0.0:
            jac.append((variable.index, value))
    return tuple(jac)


def build_rows(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    q_values: Iterable[float],
    x_values: Iterable[float],
    max_order: int,
) -> list[MortarRow]:
    rows: list[MortarRow] = []
    specs = derivative_specs(max_order)
    for component in ("F", "G"):
        for q in q_values:
            for x in x_values:
                for spec in specs:
                    tail = tail_total_partial(data, component, q, x, spec.dq_order, spec.dx_order)
                    origin = origin_total_partial(data, component, q, x, spec.dq_order, spec.dx_order)
                    rows.append(
                        MortarRow(
                            row_index=len(rows),
                            component=component,
                            q=q,
                            x=x,
                            dq_order=spec.dq_order,
                            dx_order=spec.dx_order,
                            tail_value=tail,
                            origin_value=origin,
                            residual=tail - origin,
                            jacobian=active_jacobian(
                                data,
                                variables,
                                component,
                                q,
                                x,
                                spec.dq_order,
                                spec.dx_order,
                            ),
                        )
                    )
    return rows


def get_path(data: dict[str, Any], path: tuple[Any, ...]) -> Any:
    node: Any = data
    for part in path:
        node = node[part]
    return node


def set_path(data: dict[str, Any], path: tuple[Any, ...], value: float) -> None:
    node: Any = data
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value


def residual_for_row(data: dict[str, Any], row: MortarRow) -> float:
    return tail_total_partial(data, row.component, row.q, row.x, row.dq_order, row.dx_order) - origin_total_partial(
        data, row.component, row.q, row.x, row.dq_order, row.dx_order
    )


def smoke_finite_difference(
    data: dict[str, Any],
    variables: list[CoefficientVariable],
    rows: list[MortarRow],
    epsilon: float,
) -> dict[str, Any]:
    chosen: list[dict[str, Any]] = []
    used_variables: set[int] = set()
    target_specs = {
        ("F", 0, 0),
        ("F", 1, 1),
        ("G", 2, 0),
    }
    for row in rows:
        row_key = (row.component, row.dq_order, row.dx_order)
        if row_key not in target_specs:
            continue
        for var_index, exact in row.jacobian:
            if var_index in used_variables or abs(exact) < 1e-10:
                continue
            variable = variables[var_index]
            original = float(get_path(data, variable.path))
            plus_data = copy.deepcopy(data)
            minus_data = copy.deepcopy(data)
            set_path(plus_data, variable.path, original + epsilon)
            set_path(minus_data, variable.path, original - epsilon)
            fd = (residual_for_row(plus_data, row) - residual_for_row(minus_data, row)) / (2.0 * epsilon)
            chosen.append(
                {
                    "row_index": row.row_index,
                    "component": row.component,
                    "q": row.q,
                    "x": row.x,
                    "derivative": row.derivative.label,
                    "var_index": var_index,
                    "variable": variable.label,
                    "epsilon": epsilon,
                    "exact_jacobian": exact,
                    "finite_difference": fd,
                    "abs_diff": abs(fd - exact),
                    "relative_diff": abs(fd - exact) / max(1.0, abs(exact)),
                }
            )
            used_variables.add(var_index)
            target_specs.remove(row_key)
            break
        if not target_specs:
            break
    if len(chosen) != 3:
        raise RuntimeError(f"finite-difference smoke selected {len(chosen)} checks, expected 3")
    return {
        "epsilon": epsilon,
        "checks": chosen,
        "max_abs_diff": max(item["abs_diff"] for item in chosen),
        "max_relative_diff": max(item["relative_diff"] for item in chosen),
    }


def summarize_inventory(variables: list[CoefficientVariable]) -> dict[str, Any]:
    by_block: dict[str, int] = {}
    for variable in variables:
        key = f"{variable.chart}.{variable.block}"
        by_block[key] = by_block.get(key, 0) + 1
    return {
        "count": len(variables),
        "by_block": dict(sorted(by_block.items())),
        "preview": [variable.as_json() for variable in variables[:12]],
    }


def summarize_rows(rows: list[MortarRow]) -> dict[str, Any]:
    total_sq = 0.0
    total_nnz = 0
    worst = max(rows, key=lambda row: row.abs_residual, default=None)
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        total_sq += row.residual * row.residual
        total_nnz += len(row.jacobian)
        key = f"{row.component}:{row.derivative.label}"
        group = groups.setdefault(
            key,
            {
                "key": key,
                "component": row.component,
                "derivative": row.derivative.label,
                "dq_order": row.dq_order,
                "dx_order": row.dx_order,
                "count": 0,
                "rms_sum": 0.0,
                "max_abs": 0.0,
            },
        )
        group["count"] += 1
        group["rms_sum"] += row.residual * row.residual
        group["max_abs"] = max(group["max_abs"], row.abs_residual)
    group_items = []
    for group in groups.values():
        count = int(group["count"])
        group_items.append(
            {
                "key": group["key"],
                "component": group["component"],
                "derivative": group["derivative"],
                "dq_order": group["dq_order"],
                "dx_order": group["dx_order"],
                "count": count,
                "max_abs": group["max_abs"],
                "rms": math.sqrt(group["rms_sum"] / max(count, 1)),
            }
        )
    group_items.sort(key=lambda item: float(item["max_abs"]), reverse=True)
    return {
        "count": len(rows),
        "jacobian_total_nnz": total_nnz,
        "jacobian_nnz_per_row": total_nnz / max(len(rows), 1),
        "max_abs": worst.abs_residual if worst else 0.0,
        "rms": math.sqrt(total_sq / max(len(rows), 1)),
        "worst": worst.as_json() if worst else {},
        "groups": group_items,
    }


def default_profile_path() -> str:
    preferred = os.path.join(ROOT_DIR, "work", "v117_twochart_init.json")
    if os.path.exists(preferred):
        return preferred
    return os.path.join(ROOT_DIR, "work", "twochart_projection_v1.json")


def run(args: argparse.Namespace) -> dict[str, Any]:
    data = load_json(args.profile)
    variables = enumerate_coefficients(data)
    q_values = grid(args.q_min, args.q_max, args.q_samples)
    x_values = grid(0.0, 1.0, args.x_samples)
    rows = build_rows(data, variables, q_values, x_values, args.max_order)
    smoke = smoke_finite_difference(data, variables, rows, args.fd_epsilon) if args.smoke else None

    profile_rel = os.path.relpath(args.profile, ROOT_DIR) if os.path.isabs(args.profile) else args.profile
    row_preview_count = len(rows) if args.include_rows else min(args.row_limit, len(rows))
    result: dict[str, Any] = {
        "status": STATUS,
        "profile": profile_rel,
        "format": SUPPORTED_FORMAT,
        "diagnostic_vs_proof": "floating residual/Jacobian assembly only; no interval proof or proof claim",
        "residual_definition": "tail_total_partial(q,x) - origin_total_partial(q,x)",
        "tail_legality": data.get("tail_legality"),
        "q_band": [args.q_min, args.q_max],
        "q_samples": args.q_samples,
        "x_samples": args.x_samples,
        "max_order": args.max_order,
        "derivative_specs": [
            {"derivative": spec.label, "dq_order": spec.dq_order, "dx_order": spec.dx_order}
            for spec in derivative_specs(args.max_order)
        ],
        "coefficient_inventory": summarize_inventory(variables),
        "summary": summarize_rows(rows),
        "rows_included": row_preview_count,
        "rows_truncated": row_preview_count < len(rows),
        "rows": [row.as_json(variables) for row in rows[:row_preview_count]],
    }
    if smoke is not None:
        result["finite_difference_smoke"] = smoke
    return result


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print(f"profile={result['profile']}")
    print(f"status={result['status']}")
    print(f"q_band={result['q_band']} q_samples={result['q_samples']} x_samples={result['x_samples']}")
    print(f"max_order=C{result['max_order']}")
    print(f"coefficients={result['coefficient_inventory']['count']}")
    print(f"rows={summary['count']} jacobian_total_nnz={summary['jacobian_total_nnz']}")
    print(f"max_abs={float(summary['max_abs']):.12e}")
    print(f"rms={float(summary['rms']):.12e}")
    if "finite_difference_smoke" in result:
        smoke = result["finite_difference_smoke"]
        print(f"fd_checks={len(smoke['checks'])} fd_max_abs_diff={float(smoke['max_abs_diff']):.12e}")
    print(f"diagnostic_vs_proof={result['diagnostic_vs_proof']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=default_profile_path())
    parser.add_argument("--q-min", type=float, default=0.84)
    parser.add_argument("--q-max", type=float, default=0.92)
    parser.add_argument("--q-samples", type=int, default=5)
    parser.add_argument("--x-samples", type=int, default=9)
    parser.add_argument("--max-order", type=int, default=4)
    parser.add_argument("--json-out", default="")
    parser.add_argument("--row-limit", type=int, default=20)
    parser.add_argument("--include-rows", action="store_true", help="write all rows instead of a preview")
    parser.add_argument("--smoke", action="store_true", help="run three coefficient finite-difference checks")
    parser.add_argument("--fd-epsilon", type=float, default=1e-6)
    args = parser.parse_args()

    if not (0.0 < args.q_min <= args.q_max < 1.0):
        raise ValueError("require 0 < --q-min <= --q-max < 1")
    if args.q_samples <= 0 or args.x_samples <= 0:
        raise ValueError("sample counts must be positive")
    if args.row_limit < 0:
        raise ValueError("--row-limit must be nonnegative")
    if args.fd_epsilon <= 0.0:
        raise ValueError("--fd-epsilon must be positive")

    result = run(args)
    print_summary(result)
    if args.json_out:
        save_json(args.json_out, result)


if __name__ == "__main__":
    main()
