#!/usr/bin/env python3
"""Damped Gauss-Newton scaffold for transseries-Chebyshev projections.

This tool operates on the JSON produced by `profile_project_cheb.py`.  It is
not an interval Newton-Kantorovich validator.  It is a discovery step toward
one: variables are proof-native Chebyshev coefficients in the structurally
q1-free transseries representation, and residuals are evaluated with the
Taylor-jet compactified equation bridge.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import tempfile
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from compactified_collocation import qb_to_rz
from compactified_profile import grid
from profile_project_cheb import cheb_eval_tensor
from validators.compactified_equations import (
    ProjectedProfile,
    RESIDUAL_KINDS,
    compactified_residual_defined,
    residual_with_kind,
)


@dataclass(frozen=True)
class Variable:
    block: str
    frac_index: int
    patch_index: int
    kq: int
    kx: int

    @property
    def label(self) -> str:
        if self.block in ("F_origin", "G_origin"):
            return f"{self.block}[{self.patch_index}][R^{self.kq}Z^{self.kx}]"
        if self.frac_index >= 0:
            return f"{self.block}[{self.frac_index}][{self.patch_index}][{self.kq},{self.kx}]"
        return f"{self.block}[{self.patch_index}][{self.kq},{self.kx}]"


@dataclass(frozen=True)
class Point:
    q: float
    b: float
    weight: float

    @property
    def label(self) -> str:
        return f"q={self.q:.6f} b={self.b:.6f}"


@dataclass(frozen=True)
class ContinuityConstraint:
    component: str
    q: float
    x: float
    weight: float
    kind: str
    left: int
    right: int
    derivative_direction: str = ""
    derivative_order: int = 0
    derivative_step: float = 0.0


@dataclass(frozen=True)
class DerivativeLoss:
    d1_weight: float
    d2_weight: float
    dq: float
    db: float


def load_json(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: str, data: dict[str, object]) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def parse_blocks(raw: str) -> tuple[str, ...]:
    blocks = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"F_an", "G_an", "F_frac0", "G_frac0", "F_origin", "G_origin"}
    unknown = [block for block in blocks if block not in allowed]
    if unknown:
        raise ValueError(f"unknown block(s): {', '.join(unknown)}")
    if not blocks:
        raise ValueError("at least one block is required")
    return blocks


def parse_points(raw: str) -> tuple[Point, ...]:
    points: list[Point] = []
    if not raw.strip():
        return ()
    for item in raw.split(";"):
        if not item.strip():
            continue
        parts = [part.strip() for part in item.split(",") if part.strip()]
        if len(parts) not in (2, 3):
            raise ValueError(f"bad active point {item!r}; expected q,b[,weight]")
        q = float(parts[0])
        b = float(parts[1])
        weight = float(parts[2]) if len(parts) == 3 else 1.0
        if not (0.0 < q < 1.0):
            raise ValueError(f"q must lie in (0,1): {q}")
        if not (-1.0 < b < 1.0):
            raise ValueError(f"b must lie in (-1,1): {b}")
        if weight <= 0.0:
            raise ValueError("point weights must be positive")
        points.append(Point(q=q, b=b, weight=weight))
    return tuple(points)


def parse_q_values(raw: str) -> tuple[float, ...]:
    if not raw.strip():
        return ()
    return tuple(float(item) for item in raw.split(",") if item.strip())


def grid_points(q_min: float, q_max: float, b_min: float, b_max: float, n_q: int, n_b: int) -> tuple[Point, ...]:
    points: list[Point] = []
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            points.append(Point(q=q, b=b, weight=1.0))
    return tuple(points)


def as_patch_items(data: dict[str, object], block: str) -> list[dict[str, object]]:
    blocks = data["blocks"]  # type: ignore[index]
    if block == "F_frac0":
        return blocks["F_frac"][0]  # type: ignore[index,return-value]
    if block == "G_frac0":
        return blocks["G_frac"][0]  # type: ignore[index,return-value]
    return blocks[block]  # type: ignore[index,return-value]


def patch_interval(patch: dict[str, object]) -> tuple[float, float, float, float]:
    q0, q1 = patch["q_interval"]  # type: ignore[index]
    x0, x1 = patch["x_interval"]  # type: ignore[index]
    return float(q0), float(q1), float(x0), float(x1)


def eval_patch_item(patch: dict[str, object], q: float, x: float) -> float:
    q0, q1, x0, x1 = patch_interval(patch)
    return cheb_eval_tensor(patch["coeffs"], q, x, q0, q1, x0, x1)  # type: ignore[arg-type,index]


def find_patch_index(patches: list[dict[str, object]], q: float, x: float) -> int:
    for index, patch in enumerate(patches):
        q0, q1, x0, x1 = patch_interval(patch)
        if q0 - 1e-15 <= q <= q1 + 1e-15 and x0 - 1e-15 <= x <= x1 + 1e-15:
            return index
    raise ValueError(f"point outside JSON patches q={q} x={x}")


def eval_rect_total(data: dict[str, object], component: str, q: float, x: float) -> float:
    p = float(data["p"])
    if component == "F":
        value = 0.5 + q * q * eval_patch_item(as_patch_items(data, "F_an")[find_patch_index(as_patch_items(data, "F_an"), q, x)], q, x)
        for k, block in enumerate(data["blocks"]["F_frac"], start=1):  # type: ignore[index]
            patch_index = find_patch_index(block, q, x)
            value += (q ** (k * p)) * eval_patch_item(block[patch_index], q, x)
        return value
    value = float(data["B"]) + q * q * eval_patch_item(as_patch_items(data, "G_an")[find_patch_index(as_patch_items(data, "G_an"), q, x)], q, x)
    for k, block in enumerate(data["blocks"]["G_frac"], start=1):  # type: ignore[index]
        patch_index = find_patch_index(block, q, x)
        value += (q ** (k * p)) * eval_patch_item(block[patch_index], q, x)
    return value


def eval_origin_total(data: dict[str, object], component: str, q: float, x: float) -> float:
    key = "F_origin_taylor" if component == "F" else "G_origin_taylor"
    origin = data["blocks"][key]  # type: ignore[index]
    rho2 = 1.0 / (q * q) - 1.0
    r2 = rho2 * (1.0 - x)
    z2 = rho2 * x
    return sum(
        float(entry["coeff"]) * (r2 ** int(entry["R_power"])) * (z2 ** int(entry["Z_power"]))
        for entry in origin.get("basis", [])  # type: ignore[union-attr]
    )


def finite_derivative_1d(
    func: object,
    q: float,
    x: float,
    direction: str,
    order: int,
    step: float,
    lower: float,
    upper: float,
) -> float:
    if order == 0:
        return func(q, x)  # type: ignore[operator]
    if order not in (1, 2):
        raise ValueError("only derivative orders 0, 1, and 2 are supported")
    if direction not in ("q", "x"):
        raise ValueError("derivative direction must be q or x")
    if step <= 0.0:
        raise ValueError("derivative step must be positive")
    coordinate = q if direction == "q" else x

    def value(offset: float) -> float:
        if direction == "q":
            return func(q + offset, x)  # type: ignore[operator]
        return func(q, x + offset)  # type: ignore[operator]

    can_plus = coordinate + step <= upper + 1e-15
    can_minus = coordinate - step >= lower - 1e-15
    can_plus2 = coordinate + 2.0 * step <= upper + 1e-15
    can_minus2 = coordinate - 2.0 * step >= lower - 1e-15
    if order == 1:
        if can_plus and can_minus:
            return (value(step) - value(-step)) / (2.0 * step)
        if can_plus:
            return (value(step) - value(0.0)) / step
        if can_minus:
            return (value(0.0) - value(-step)) / step
    else:
        if can_plus and can_minus:
            return (value(step) - 2.0 * value(0.0) + value(-step)) / (step * step)
        if can_plus2:
            return (value(2.0 * step) - 2.0 * value(step) + value(0.0)) / (step * step)
        if can_minus2:
            return (value(0.0) - 2.0 * value(-step) + value(-2.0 * step)) / (step * step)
    raise ValueError(f"cannot take derivative at {direction}={coordinate} with step {step}")


def patch_derivative_value(
    patch: dict[str, object],
    q: float,
    x: float,
    direction: str,
    order: int,
    step: float,
    normal_side: int,
) -> float:
    if order == 0:
        return eval_patch_item(patch, q, x)
    q0, q1, x0, x1 = patch_interval(patch)
    if direction == "q":
        lower, upper = q0, q1
    elif direction == "x":
        lower, upper = x0, x1
    else:
        raise ValueError("derivative direction must be q or x")

    def value(offset: float) -> float:
        if direction == "q":
            return eval_patch_item(patch, q + offset, x)
        return eval_patch_item(patch, q, x + offset)

    if normal_side < 0:
        if order == 1:
            return (value(0.0) - value(-step)) / step
        return (value(0.0) - 2.0 * value(-step) + value(-2.0 * step)) / (step * step)
    if normal_side > 0:
        if order == 1:
            return (value(step) - value(0.0)) / step
        return (value(2.0 * step) - 2.0 * value(step) + value(0.0)) / (step * step)
    return finite_derivative_1d(lambda qq, xx: eval_patch_item(patch, qq, xx), q, x, direction, order, step, lower, upper)


def total_derivative_value(
    data: dict[str, object],
    component: str,
    q: float,
    x: float,
    direction: str,
    order: int,
    step: float,
    source: str,
) -> float:
    if source == "rect":
        func = lambda qq, xx: eval_rect_total(data, component, qq, xx)
    elif source == "origin":
        func = lambda qq, xx: eval_origin_total(data, component, qq, xx)
    else:
        raise ValueError("source must be rect or origin")
    lower, upper = (0.0, 1.0)
    return finite_derivative_1d(func, q, x, direction, order, step, lower, upper)


def derivative_constraint_specs(max_order: int, weight: float, derivative_weight: float, step: float) -> list[tuple[str, int, float, float]]:
    specs: list[tuple[str, int, float, float]] = [("", 0, weight, 0.0)]
    if max_order <= 0:
        return specs
    if derivative_weight <= 0.0:
        return specs
    for order in range(1, min(max_order, 2) + 1):
        for direction in ("q", "x"):
            specs.append((direction, order, weight * derivative_weight, step))
    return specs


def build_patch_continuity_constraints(
    data: dict[str, object],
    blocks: tuple[str, ...],
    samples: int,
    weight: float,
    derivative_order: int,
    derivative_weight: float,
    derivative_step: float,
) -> list[ContinuityConstraint]:
    if weight <= 0.0 or samples <= 0:
        return []
    constraints: list[ContinuityConstraint] = []
    specs = derivative_constraint_specs(derivative_order, weight, derivative_weight, derivative_step)
    block_names = [block for block in blocks if block in ("F_an", "G_an", "F_frac0", "G_frac0")]
    for block in block_names:
        patches = as_patch_items(data, block)
        for i, left in enumerate(patches):
            lq0, lq1, lx0, lx1 = patch_interval(left)
            for j in range(i + 1, len(patches)):
                right = patches[j]
                rq0, rq1, rx0, rx1 = patch_interval(right)
                if abs(lq1 - rq0) <= 1e-14:
                    x0 = max(lx0, rx0)
                    x1 = min(lx1, rx1)
                    if x1 > x0 + 1e-14:
                        for x in grid(x0, x1, samples):
                            for direction, order, constraint_weight, step in specs:
                                constraints.append(
                                    ContinuityConstraint(
                                        block,
                                        lq1,
                                        x,
                                        constraint_weight,
                                        "q-seam",
                                        i,
                                        j,
                                        direction,
                                        order,
                                        step,
                                    )
                                )
                if abs(lx1 - rx0) <= 1e-14:
                    q0 = max(lq0, rq0)
                    q1 = min(lq1, rq1)
                    if q1 > q0 + 1e-14:
                        for q in grid(q0, q1, samples):
                            for direction, order, constraint_weight, step in specs:
                                constraints.append(
                                    ContinuityConstraint(
                                        block,
                                        q,
                                        lx1,
                                        constraint_weight,
                                        "x-seam",
                                        i,
                                        j,
                                        direction,
                                        order,
                                        step,
                                    )
                                )
    return constraints


def build_origin_matching_constraints(
    data: dict[str, object],
    q_values: tuple[float, ...],
    x_samples: int,
    weight: float,
    derivative_order: int,
    derivative_weight: float,
    derivative_step: float,
) -> list[ContinuityConstraint]:
    if weight <= 0.0 or x_samples <= 0:
        return []
    constraints: list[ContinuityConstraint] = []
    specs = derivative_constraint_specs(derivative_order, weight, derivative_weight, derivative_step)
    for component in ("F", "G"):
        for q in q_values:
            for x in grid(0.0, 1.0, x_samples):
                for direction, order, constraint_weight, step in specs:
                    constraints.append(
                        ContinuityConstraint(
                            component,
                            q,
                            x,
                            constraint_weight,
                            "origin-match",
                            -1,
                            -1,
                            direction,
                            order,
                            step,
                        )
                    )
    return constraints


def coefficient_table(data: dict[str, object], variable: Variable) -> list[list[float]]:
    blocks = data["blocks"]  # type: ignore[index]
    if not isinstance(blocks, dict):
        raise ValueError("blocks must be an object")
    if variable.block == "F_frac0":
        block_items = blocks["F_frac"]  # type: ignore[index]
        if not isinstance(block_items, list):
            raise ValueError("F_frac must be a list")
        patch = block_items[0][variable.patch_index]
        return patch["coeffs"]  # type: ignore[index,return-value]
    if variable.block == "G_frac0":
        block_items = blocks["G_frac"]  # type: ignore[index]
        if not isinstance(block_items, list):
            raise ValueError("G_frac must be a list")
        patch = block_items[0][variable.patch_index]
        return patch["coeffs"]  # type: ignore[index,return-value]
    if variable.frac_index >= 0:
        block_items = blocks[variable.block]  # type: ignore[index]
        if not isinstance(block_items, list):
            raise ValueError(f"{variable.block} must be a list")
        patch = block_items[variable.frac_index][variable.patch_index]
    else:
        patch = blocks[variable.block][variable.patch_index]  # type: ignore[index]
    return patch["coeffs"]  # type: ignore[index,return-value]


def get_coeff(data: dict[str, object], variable: Variable) -> float:
    if variable.block in ("F_origin", "G_origin"):
        blocks = data["blocks"]  # type: ignore[index]
        key = "F_origin_taylor" if variable.block == "F_origin" else "G_origin_taylor"
        basis = blocks[key]["basis"]  # type: ignore[index]
        return float(basis[variable.patch_index]["coeff"])
    table = coefficient_table(data, variable)
    return float(table[variable.kq][variable.kx])


def set_coeff(data: dict[str, object], variable: Variable, value: float) -> None:
    if variable.block in ("F_origin", "G_origin"):
        blocks = data["blocks"]  # type: ignore[index]
        key = "F_origin_taylor" if variable.block == "F_origin" else "G_origin_taylor"
        basis = blocks[key]["basis"]  # type: ignore[index]
        basis[variable.patch_index]["coeff"] = float(value)
        return
    table = coefficient_table(data, variable)
    table[variable.kq][variable.kx] = float(value)


def block_patch_items(data: dict[str, object], block: str) -> tuple[int, list[dict[str, object]]]:
    blocks = data["blocks"]  # type: ignore[index]
    if block == "F_frac0":
        return 0, blocks["F_frac"][0]  # type: ignore[index,return-value]
    if block == "G_frac0":
        return 0, blocks["G_frac"][0]  # type: ignore[index,return-value]
    return -1, blocks[block]  # type: ignore[index,return-value]


def origin_variables(
    data: dict[str, object],
    block: str,
    q_max: float,
    max_mode_r: int,
    max_mode_z: int,
    skip_constant: bool,
) -> list[Variable]:
    blocks = data["blocks"]  # type: ignore[index]
    key = "F_origin_taylor" if block == "F_origin" else "G_origin_taylor"
    origin = blocks.get(key, {})  # type: ignore[union-attr]
    if not isinstance(origin, dict) or not origin.get("enabled", False):
        return []
    if q_max < float(origin.get("q_min", 2.0)):
        return []
    variables: list[Variable] = []
    for index, entry in enumerate(origin.get("basis", [])):
        r_power = int(entry["R_power"])
        z_power = int(entry["Z_power"])
        if r_power > max_mode_r or z_power > max_mode_z:
            continue
        if skip_constant and r_power == 0 and z_power == 0:
            continue
        variables.append(
            Variable(block=block, frac_index=-1, patch_index=index, kq=r_power, kx=z_power)
        )
    return variables


def intervals_intersect(a0: float, a1: float, b0: float, b1: float) -> bool:
    return min(a1, b1) > max(a0, b0) + 1e-14


def limit_variables_round_robin(groups: dict[str, list[Variable]], max_variables: int) -> list[Variable]:
    ordered: list[Variable] = []
    block_names = list(groups)
    if max_variables <= 0:
        for block in block_names:
            ordered.extend(groups[block])
        return ordered
    offsets = {block: 0 for block in block_names}
    while len(ordered) < max_variables:
        added = False
        for block in block_names:
            offset = offsets[block]
            if offset >= len(groups[block]):
                continue
            ordered.append(groups[block][offset])
            offsets[block] = offset + 1
            added = True
            if len(ordered) >= max_variables:
                break
        if not added:
            break
    return ordered


def variables_from_projection(
    data: dict[str, object],
    blocks: tuple[str, ...],
    q_min: float,
    q_max: float,
    x_min: float,
    x_max: float,
    max_mode_q: int,
    max_mode_x: int,
    skip_constant: bool,
    max_variables: int,
    support_points: tuple[Point, ...] = (),
) -> list[Variable]:
    support_x = tuple((point.q, point.b * point.b) for point in support_points)

    def patch_is_supported(patch: dict[str, object]) -> bool:
        if not support_x:
            return False
        q0, q1, x0, x1 = patch_interval(patch)
        for q, x in support_x:
            if q0 - 1e-15 <= q <= q1 + 1e-15 and x0 - 1e-15 <= x <= x1 + 1e-15:
                return True
        return False

    groups: dict[str, list[Variable]] = {block: [] for block in blocks}
    for block in blocks:
        if block in ("F_origin", "G_origin"):
            groups[block].extend(
                origin_variables(
                    data,
                    block,
                    q_max=q_max,
                    max_mode_r=max_mode_q,
                    max_mode_z=max_mode_x,
                    skip_constant=skip_constant,
                )
            )
            continue
        frac_index, patches = block_patch_items(data, block)
        patch_order = sorted(range(len(patches)), key=lambda index: (not patch_is_supported(patches[index]), index))
        for patch_index in patch_order:
            patch = patches[patch_index]
            q0, q1 = patch["q_interval"]
            x0, x1 = patch["x_interval"]
            if not intervals_intersect(float(q0), float(q1), q_min, q_max):
                continue
            if not intervals_intersect(float(x0), float(x1), x_min, x_max):
                continue
            coeffs = patch["coeffs"]
            q_count = min(len(coeffs), max_mode_q + 1)
            x_count = min(len(coeffs[0]), max_mode_x + 1) if q_count else 0
            for kq in range(q_count):
                for kx in range(x_count):
                    if skip_constant and kq == 0 and kx == 0:
                        continue
                    groups[block].append(
                        Variable(block=block, frac_index=frac_index, patch_index=patch_index, kq=kq, kx=kx)
                    )
    return limit_variables_round_robin(groups, max_variables)


def variable_counts(variables: list[Variable]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for variable in variables:
        counts[variable.block] = counts.get(variable.block, 0) + 1
    return counts


def load_profile_from_data(data: dict[str, object], tmp_dir: str) -> ProjectedProfile:
    # ProjectedProfile currently loads from JSON.  Keep this mechanical until
    # the validator gets a direct from-dict constructor.
    os.makedirs(tmp_dir, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=tmp_dir,
        prefix=".profile_newton_cheb_",
        suffix=".json",
        delete=False,
    )
    tmp_path = handle.name
    try:
        with handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return ProjectedProfile.load(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def residual_vector(
    profile: ProjectedProfile,
    data: dict[str, object],
    points: tuple[Point, ...],
    residual_kind: str,
    constraints: tuple[ContinuityConstraint, ...],
    derivative_loss: DerivativeLoss,
) -> tuple[list[float], dict[str, object]]:
    def residual_values(q: float, b: float) -> tuple[float, float, float, float] | None:
        if not (0.0 < q < 1.0 and -1.0 < b < 1.0):
            return None
        if not compactified_residual_defined(q, b, profile.p, residual_kind):
            return None
        r_local, z_local = qb_to_rz(q, b)
        raw_local = profile.exact_residual_at(r_local, z_local)
        residual_local = residual_with_kind(raw_local, q, b, profile.p, residual_kind)
        return residual_local.e_psi, residual_local.e_gamma, r_local, z_local

    def add_component_rows(
        components: tuple[float, float],
        scale: float,
        metadata: dict[str, object],
    ) -> None:
        nonlocal worst_abs, worst_item, total, count
        scaled = (scale * components[0], scale * components[1])
        values.extend(scaled)
        total += scaled[0] * scaled[0] + scaled[1] * scaled[1]
        count += 2
        scaled_max = max(abs(scaled[0]), abs(scaled[1]))
        if scaled_max > worst_abs:
            worst_abs = scaled_max
            worst_item = dict(metadata)
            worst_item.update({"e_psi": scaled[0], "e_gamma": scaled[1], "max_abs": scaled_max})

    values: list[float] = []
    worst_abs = 0.0
    worst_item: dict[str, object] = {}
    total = 0.0
    count = 0
    for point in points:
        base = residual_values(point.q, point.b)
        if base is None:
            continue
        scale = math.sqrt(point.weight)
        add_component_rows(
            (base[0], base[1]),
            scale,
            {
                "type": "pde",
                "q": point.q,
                "b": point.b,
                "r": base[2],
                "z": base[3],
            },
        )
        for direction, step in (("q", derivative_loss.dq), ("b", derivative_loss.db)):
            if step <= 0.0:
                continue
            q_plus = point.q + step if direction == "q" else point.q
            q_minus = point.q - step if direction == "q" else point.q
            b_plus = point.b + step if direction == "b" else point.b
            b_minus = point.b - step if direction == "b" else point.b
            plus = residual_values(q_plus, b_plus)
            minus = residual_values(q_minus, b_minus)
            if plus is None or minus is None:
                continue
            if derivative_loss.d1_weight > 0.0:
                derivative = ((plus[0] - minus[0]) / (2.0 * step), (plus[1] - minus[1]) / (2.0 * step))
                add_component_rows(
                    derivative,
                    math.sqrt(point.weight * derivative_loss.d1_weight),
                    {
                        "type": "derivative",
                        "order": 1,
                        "direction": direction,
                        "q": point.q,
                        "b": point.b,
                        "step": step,
                    },
                )
            if derivative_loss.d2_weight > 0.0:
                second = (
                    (plus[0] - 2.0 * base[0] + minus[0]) / (step * step),
                    (plus[1] - 2.0 * base[1] + minus[1]) / (step * step),
                )
                add_component_rows(
                    second,
                    math.sqrt(point.weight * derivative_loss.d2_weight),
                    {
                        "type": "derivative",
                        "order": 2,
                        "direction": direction,
                        "q": point.q,
                        "b": point.b,
                        "step": step,
                    },
                )
    for constraint in constraints:
        scale = math.sqrt(constraint.weight)
        if constraint.kind == "origin-match":
            diff = total_derivative_value(
                data,
                constraint.component,
                constraint.q,
                constraint.x,
                constraint.derivative_direction,
                constraint.derivative_order,
                constraint.derivative_step,
                "rect",
            ) - total_derivative_value(
                data,
                constraint.component,
                constraint.q,
                constraint.x,
                constraint.derivative_direction,
                constraint.derivative_order,
                constraint.derivative_step,
                "origin",
            )
        else:
            patches = as_patch_items(data, constraint.component)
            normal_direction = (
                (constraint.kind == "q-seam" and constraint.derivative_direction == "q")
                or (constraint.kind == "x-seam" and constraint.derivative_direction == "x")
            )
            left_side = -1 if normal_direction else 0
            right_side = 1 if normal_direction else 0
            diff = patch_derivative_value(
                patches[constraint.left],
                constraint.q,
                constraint.x,
                constraint.derivative_direction,
                constraint.derivative_order,
                constraint.derivative_step,
                left_side,
            ) - patch_derivative_value(
                patches[constraint.right],
                constraint.q,
                constraint.x,
                constraint.derivative_direction,
                constraint.derivative_order,
                constraint.derivative_step,
                right_side,
            )
        value = scale * diff
        values.append(value)
        total += value * value
        count += 1
        if abs(value) > worst_abs:
            worst_abs = abs(value)
            worst_item = {
                "type": "constraint",
                "kind": constraint.kind,
                "component": constraint.component,
                "q": constraint.q,
                "x": constraint.x,
                "residual": value,
                "max_abs": abs(value),
                "derivative_direction": constraint.derivative_direction,
                "derivative_order": constraint.derivative_order,
            }
    return values, {"max_abs": worst_abs, "rms": math.sqrt(total / max(count, 1)), "worst": worst_item}


def solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-24:
            raise ValueError("singular normal matrix")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]
        for item in range(col, n + 1):
            a[col][item] /= pivot_value
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for item in range(col, n + 1):
                a[row][item] -= factor * a[col][item]
    return [a[i][n] for i in range(n)]


def gn_step(
    data: dict[str, object],
    variables: list[Variable],
    points: tuple[Point, ...],
    constraints: tuple[ContinuityConstraint, ...],
    fd_step: float,
    damping: float,
    tmp_dir: str,
    residual_kind: str,
    derivative_loss: DerivativeLoss,
) -> tuple[list[float], dict[str, object]]:
    base_profile = load_profile_from_data(data, tmp_dir)
    base_vec, base_metrics = residual_vector(
        base_profile,
        data,
        points,
        residual_kind,
        constraints,
        derivative_loss,
    )
    m = len(base_vec)
    n = len(variables)
    jac_columns: list[list[float]] = []
    for variable in variables:
        perturbed = copy.deepcopy(data)
        set_coeff(perturbed, variable, get_coeff(perturbed, variable) + fd_step)
        profile = load_profile_from_data(perturbed, tmp_dir)
        vec, _metrics = residual_vector(profile, perturbed, points, residual_kind, constraints, derivative_loss)
        jac_columns.append([(vec[i] - base_vec[i]) / fd_step for i in range(m)])
    normal = [[0.0 for _ in range(n)] for _ in range(n)]
    rhs = [0.0 for _ in range(n)]
    for a in range(n):
        col_a = jac_columns[a]
        rhs[a] = -sum(col_a[i] * base_vec[i] for i in range(m))
        for b in range(a, n):
            value = sum(col_a[i] * jac_columns[b][i] for i in range(m))
            normal[a][b] = value
            normal[b][a] = value
        normal[a][a] += damping
    delta = solve_linear(normal, rhs)
    return delta, base_metrics


def apply_delta(
    data: dict[str, object],
    variables: list[Variable],
    delta: list[float],
    alpha: float,
    max_update_norm: float,
) -> dict[str, object]:
    norm = math.sqrt(sum(value * value for value in delta))
    scale = alpha
    if max_update_norm > 0.0 and norm * scale > max_update_norm:
        scale = max_update_norm / norm
    out = copy.deepcopy(data)
    for variable, change in zip(variables, delta):
        set_coeff(out, variable, get_coeff(out, variable) + scale * change)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--blocks", default="F_an,G_an")
    parser.add_argument("--q-min", type=float, default=0.345)
    parser.add_argument("--q-max", type=float, default=0.495)
    parser.add_argument("--b-min", type=float, default=0.18)
    parser.add_argument("--b-max", type=float, default=0.38)
    parser.add_argument("--n-q", type=int, default=7)
    parser.add_argument("--n-b", type=int, default=7)
    parser.add_argument("--active-qb-points", default="")
    parser.add_argument("--var-q-min", type=float, default=0.34)
    parser.add_argument("--var-q-max", type=float, default=0.52)
    parser.add_argument("--var-x-min", type=float, default=0.04)
    parser.add_argument("--var-x-max", type=float, default=0.20)
    parser.add_argument("--max-mode-q", type=int, default=2)
    parser.add_argument("--max-mode-x", type=int, default=2)
    parser.add_argument("--max-variables", type=int, default=80)
    parser.add_argument("--include-constant", action="store_true")
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--fd-step", type=float, default=1e-6)
    parser.add_argument("--damping", type=float, default=1e-4)
    parser.add_argument("--max-update-norm", type=float, default=0.02)
    parser.add_argument("--line-search", default="1,0.5,0.25,0.125")
    parser.add_argument("--residual-kind", choices=RESIDUAL_KINDS, default="raw")
    parser.add_argument("--continuity-weight", type=float, default=0.0)
    parser.add_argument("--continuity-samples", type=int, default=3)
    parser.add_argument("--continuity-derivative-order", type=int, default=0)
    parser.add_argument("--origin-match-weight", type=float, default=0.0)
    parser.add_argument("--origin-match-q", default="0.9")
    parser.add_argument("--origin-match-x-samples", type=int, default=7)
    parser.add_argument("--origin-match-derivative-order", type=int, default=0)
    parser.add_argument("--mortar-derivative-weight", type=float, default=1.0)
    parser.add_argument("--mortar-derivative-step", type=float, default=1e-4)
    parser.add_argument("--d1-weight", type=float, default=0.0)
    parser.add_argument("--d2-weight", type=float, default=0.0)
    parser.add_argument("--derivative-step-q", type=float, default=0.005)
    parser.add_argument("--derivative-step-b", type=float, default=0.005)
    args = parser.parse_args()

    data = load_json(args.input)
    if data.get("format") != "transseries_cheb_projection_v1":
        raise ValueError("input must be a transseries_cheb_projection_v1 JSON file")
    blocks = parse_blocks(args.blocks)
    points = grid_points(args.q_min, args.q_max, args.b_min, args.b_max, args.n_q, args.n_b)
    points = points + parse_points(args.active_qb_points)
    variables = variables_from_projection(
        data,
        blocks=blocks,
        q_min=args.var_q_min,
        q_max=args.var_q_max,
        x_min=args.var_x_min,
        x_max=args.var_x_max,
        max_mode_q=args.max_mode_q,
        max_mode_x=args.max_mode_x,
        skip_constant=not args.include_constant,
        max_variables=args.max_variables,
        support_points=points,
    )
    if not variables:
        raise ValueError("no Chebyshev variables selected")
    constraints = tuple(
        build_patch_continuity_constraints(
            data,
            blocks,
            samples=args.continuity_samples,
            weight=args.continuity_weight,
            derivative_order=args.continuity_derivative_order,
            derivative_weight=args.mortar_derivative_weight,
            derivative_step=args.mortar_derivative_step,
        )
        + build_origin_matching_constraints(
            data,
            q_values=parse_q_values(args.origin_match_q),
            x_samples=args.origin_match_x_samples,
            weight=args.origin_match_weight,
            derivative_order=args.origin_match_derivative_order,
            derivative_weight=args.mortar_derivative_weight,
            derivative_step=args.mortar_derivative_step,
        )
    )

    tmp_dir = os.path.dirname(args.out) or "."
    line_search = tuple(float(item) for item in args.line_search.split(",") if item.strip())
    derivative_loss = DerivativeLoss(
        d1_weight=args.d1_weight,
        d2_weight=args.d2_weight,
        dq=args.derivative_step_q,
        db=args.derivative_step_b,
    )
    print(f"input={args.input}")
    print(f"variables={len(variables)} blocks={','.join(blocks)} counts={variable_counts(variables)}")
    print(
        f"points={len(points)} iterations={args.iterations} damping={args.damping:.3e} "
        f"residual_kind={args.residual_kind}"
    )
    print(
        f"constraints={len(constraints)} continuity_weight={args.continuity_weight:.3e} "
        f"origin_match_weight={args.origin_match_weight:.3e}"
    )
    print(
        f"mortar_derivatives continuity_order={args.continuity_derivative_order} "
        f"origin_order={args.origin_match_derivative_order} "
        f"weight={args.mortar_derivative_weight:.3e} step={args.mortar_derivative_step:.3e}"
    )
    print(
        f"derivative_loss d1_weight={args.d1_weight:.3e} d2_weight={args.d2_weight:.3e} "
        f"dq={args.derivative_step_q:.3e} db={args.derivative_step_b:.3e}"
    )
    best_data = copy.deepcopy(data)
    best_profile = load_profile_from_data(best_data, tmp_dir)
    _vec, best_metrics = residual_vector(
        best_profile,
        best_data,
        points,
        args.residual_kind,
        constraints,
        derivative_loss,
    )
    print(
        "iter=-01 "
        f"max_abs={best_metrics['max_abs']:.12e} rms={best_metrics['rms']:.12e} "
        f"worst={best_metrics['worst']}"
    )
    history: list[dict[str, object]] = [best_metrics]
    for iteration in range(args.iterations):
        delta, base_metrics = gn_step(
            best_data,
            variables,
            points,
            constraints,
            args.fd_step,
            args.damping,
            tmp_dir,
            args.residual_kind,
            derivative_loss,
        )
        accepted = False
        for alpha in line_search:
            candidate = apply_delta(best_data, variables, delta, alpha, args.max_update_norm)
            profile = load_profile_from_data(candidate, tmp_dir)
            _vec, metrics = residual_vector(
                profile,
                candidate,
                points,
                args.residual_kind,
                constraints,
                derivative_loss,
            )
            if metrics["max_abs"] < best_metrics["max_abs"]:
                best_data = candidate
                best_metrics = metrics
                history.append(metrics)
                accepted = True
                print(
                    f"iter={iteration:03d} accept alpha={alpha:.6g} "
                    f"max_abs={metrics['max_abs']:.12e} rms={metrics['rms']:.12e} "
                    f"worst={metrics['worst']}"
                )
                break
            print(
                f"iter={iteration:03d} reject alpha={alpha:.6g} "
                f"max_abs={metrics['max_abs']:.12e} rms={metrics['rms']:.12e}"
            )
        if not accepted:
            print(f"iter={iteration:03d} no accepted update; stopping")
            break
    best_data["profile_newton_cheb_evidence"] = {
        "status": "damped_gauss_newton_scaffold_not_validated",
        "source": args.input,
        "blocks": list(blocks),
        "variables": [variable.label for variable in variables],
        "points": [{"q": point.q, "b": point.b, "weight": point.weight} for point in points],
        "constraints": [
            {
                "component": constraint.component,
                "q": constraint.q,
                "x": constraint.x,
                "weight": constraint.weight,
                "kind": constraint.kind,
                "left": constraint.left,
                "right": constraint.right,
                "derivative_direction": constraint.derivative_direction,
                "derivative_order": constraint.derivative_order,
                "derivative_step": constraint.derivative_step,
            }
            for constraint in constraints
        ],
        "history": history,
        "fd_step": args.fd_step,
        "damping": args.damping,
        "max_update_norm": args.max_update_norm,
        "residual_kind": args.residual_kind,
        "derivative_loss": {
            "d1_weight": args.d1_weight,
            "d2_weight": args.d2_weight,
            "dq": args.derivative_step_q,
            "db": args.derivative_step_b,
        },
        "mortar_derivatives": {
            "continuity_order": args.continuity_derivative_order,
            "origin_match_order": args.origin_match_derivative_order,
            "weight": args.mortar_derivative_weight,
            "step": args.mortar_derivative_step,
        },
    }
    save_json(args.out, best_data)
    print(f"saved={args.out}")
    print(f"final_max_abs={best_metrics['max_abs']:.12e}")
    print(f"final_rms={best_metrics['rms']:.12e}")


if __name__ == "__main__":
    main()
