#!/usr/bin/env python3
"""Max-aware coordinate search for compactified profile seeds.

The Gauss-Newton solvers in this workspace minimize a least-squares training
objective.  This diagnostic instead performs a conservative pattern search on
selected coefficient families and accepts a move only when it reduces the max
absolute residual on the requested gate grids.  It is intended for small
tail-flat interior bump corrections after an RMS step has identified a useful
direction but overshot the independent max gates.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import dataclass
from typing import Iterable

from axisym_residual import Residual, residual_at
from compactified_collocation import qb_to_rz
from compactified_profile import CompactifiedProfile, Coeff, grid


COEFF_KEYS = {
    "f_coeffs",
    "g_coeffs",
    "f_bounded_edge_coeffs",
    "g_bounded_edge_coeffs",
    "f_vanishing_edge_coeffs",
    "g_vanishing_edge_coeffs",
    "f_interior_bump_coeffs",
    "g_interior_bump_coeffs",
}


@dataclass(frozen=True)
class Variable:
    key: str
    i: int
    j: int

    @property
    def label(self) -> str:
        return f"{self.key}[{self.i},{self.j}]"


@dataclass(frozen=True)
class Point:
    r: float
    z: float
    where: str


@dataclass(frozen=True)
class GateResult:
    name: str
    max_abs: float
    rms: float
    e_psi: float
    e_gamma: float
    where: str


@dataclass(frozen=True)
class Evaluation:
    gate_results: dict[str, GateResult]
    score_gates: tuple[str, ...]

    @property
    def score_max(self) -> float:
        return max(self.gate_results[name].max_abs for name in self.score_gates)

    @property
    def score_rms(self) -> float:
        total = sum(self.gate_results[name].rms ** 2 for name in self.score_gates)
        return math.sqrt(total / max(len(self.score_gates), 1))

    @property
    def report_max(self) -> float:
        return max(result.max_abs for result in self.gate_results.values())


def load_data(path: str) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def coeff_tuples(data: dict[str, object], key: str) -> tuple[Coeff, ...]:
    raw = data.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    return tuple((int(i), int(j), float(value)) for i, j, value in raw)


def profile_from_data(data: dict[str, object]) -> CompactifiedProfile:
    return CompactifiedProfile(
        gamma=float(data["gamma"]),
        f_coeffs=coeff_tuples(data, "f_coeffs"),
        g_coeffs=coeff_tuples(data, "g_coeffs"),
        f_edge_coeffs=coeff_tuples(data, "f_edge_coeffs"),
        g_edge_coeffs=coeff_tuples(data, "g_edge_coeffs"),
        f_bounded_edge_coeffs=coeff_tuples(data, "f_bounded_edge_coeffs"),
        g_bounded_edge_coeffs=coeff_tuples(data, "g_bounded_edge_coeffs"),
        f_vanishing_edge_coeffs=coeff_tuples(data, "f_vanishing_edge_coeffs"),
        g_vanishing_edge_coeffs=coeff_tuples(data, "g_vanishing_edge_coeffs"),
        vanishing_edge_power=float(data.get("vanishing_edge_power", 1.0)),
        f_interior_bump_coeffs=coeff_tuples(data, "f_interior_bump_coeffs"),
        g_interior_bump_coeffs=coeff_tuples(data, "g_interior_bump_coeffs"),
        interior_bump_q_centers=tuple(
            float(x) for x in data.get("interior_bump_q_centers", [])  # type: ignore[union-attr]
        ),
        interior_bump_b2_centers=tuple(
            float(x) for x in data.get("interior_bump_b2_centers", [])  # type: ignore[union-attr]
        ),
        interior_bump_q_radius=float(data.get("interior_bump_q_radius", 0.14)),
        interior_bump_b2_radius=float(data.get("interior_bump_b2_radius", 0.10)),
        interior_bump_shape=str(data.get("interior_bump_shape", "compact")),
        interior_bump_q_flatness=float(data.get("interior_bump_q_flatness", 1.0)),
    )


def coeff_map(data: dict[str, object], key: str) -> dict[tuple[int, int], float]:
    return {(i, j): value for i, j, value in coeff_tuples(data, key)}


def write_coeff_map(data: dict[str, object], key: str, values: dict[tuple[int, int], float]) -> None:
    data[key] = [[i, j, values[(i, j)]] for i, j in sorted(values)]


def get_coeff(data: dict[str, object], variable: Variable) -> float:
    return coeff_map(data, variable.key)[(variable.i, variable.j)]


def set_coeff(data: dict[str, object], variable: Variable, value: float) -> None:
    values = coeff_map(data, variable.key)
    values[(variable.i, variable.j)] = value
    write_coeff_map(data, variable.key, values)


def parse_csv(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def parse_families(raw: str) -> tuple[str, ...]:
    families = parse_csv(raw)
    if not families:
        raise ValueError("at least one coefficient family is required")
    unknown = [family for family in families if family not in COEFF_KEYS]
    if unknown:
        raise ValueError(f"unknown coefficient families: {', '.join(unknown)}")
    return families


def parse_bump_kinds(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()
    kinds = tuple(item.strip().upper() for item in raw.split(",") if item.strip())
    if any(kind not in ("F", "G") for kind in kinds):
        raise ValueError("--add-missing-interior-bumps accepts only F, G, or F,G")
    return kinds


def parse_qb_points(raw: str) -> tuple[tuple[float, float], ...]:
    points: list[tuple[float, float]] = []
    if not raw.strip():
        return ()
    for item in raw.split(";"):
        if not item.strip():
            continue
        parts = [part.strip() for part in item.split(",") if part.strip()]
        if len(parts) != 2:
            raise ValueError(f"bad active qb point {item!r}; expected q,b")
        q = float(parts[0])
        b = float(parts[1])
        if not (0.0 < q < 1.0):
            raise ValueError(f"active q must lie in (0,1): {q}")
        if not (-1.0 < b < 1.0):
            raise ValueError(f"active b must lie in (-1,1): {b}")
        points.append((q, b))
    return tuple(points)


def ensure_missing_interior_bumps(data: dict[str, object], kinds: Iterable[str]) -> None:
    q_centers = data.get("interior_bump_q_centers", [])
    b2_centers = data.get("interior_bump_b2_centers", [])
    if not isinstance(q_centers, list) or not isinstance(b2_centers, list):
        raise ValueError("interior bump centers must be lists")
    for kind in kinds:
        key = "f_interior_bump_coeffs" if kind == "F" else "g_interior_bump_coeffs"
        values = coeff_map(data, key)
        for i in range(len(q_centers)):
            for j in range(len(b2_centers)):
                values.setdefault((i, j), 0.0)
        write_coeff_map(data, key, values)


def variables_from_data(
    data: dict[str, object],
    families: tuple[str, ...],
    zero_only_tol: float,
) -> list[Variable]:
    variables: list[Variable] = []
    for key in families:
        for i, j, _value in coeff_tuples(data, key):
            if zero_only_tol >= 0.0 and abs(_value) > zero_only_tol:
                continue
            variables.append(Variable(key, i, j))
    return variables


def qb_points(
    q_min: float,
    q_max: float,
    b_min: float,
    b_max: float,
    n_q: int,
    n_b: int,
    h: float,
) -> list[Point]:
    points: list[Point] = []
    for q in grid(q_min, q_max, n_q):
        for b in grid(b_min, b_max, n_b):
            r, z = qb_to_rz(q, b)
            if r <= 2.0 * h:
                continue
            points.append(Point(r=r, z=z, where=f"q={q:.6f} b={b:.6f} r={r:.6f} z={z:.6f}"))
    return points


def rz_points(
    r_min: float,
    r_max: float,
    z_min: float,
    z_max: float,
    n: int,
    h: float,
) -> list[Point]:
    points: list[Point] = []
    for r in grid(r_min, r_max, n):
        if r <= 2.0 * h:
            continue
        for z in grid(z_min, z_max, n):
            points.append(Point(r=r, z=z, where=f"r={r:.6f} z={z:.6f}"))
    return points


def build_gate_points(args: argparse.Namespace, gate_names: tuple[str, ...]) -> dict[str, list[Point]]:
    points: dict[str, list[Point]] = {}
    for name in gate_names:
        if name == "wide":
            points[name] = qb_points(0.35, 0.90, -0.80, 0.80, args.wide_n_q, args.wide_n_b, args.h)
        elif name == "interior":
            points[name] = qb_points(
                0.45, 0.85, -0.65, 0.65, args.interior_n_q, args.interior_n_b, args.h
            )
        elif name == "local":
            points[name] = rz_points(0.8, 2.0, -1.0, 1.0, args.local_n, args.h)
        elif name == "farther":
            points[name] = qb_points(
                0.18, 0.30, -0.90, 0.90, args.farther_n_q, args.farther_n_b, args.h
            )
        elif name == "extreme":
            points[name] = qb_points(
                0.25, 0.90, -0.90, 0.90, args.extreme_n_q, args.extreme_n_b, args.h
            )
        elif name == "active":
            active_points: list[Point] = []
            for q, b in parse_qb_points(args.active_qb_points):
                r, z = qb_to_rz(q, b)
                if r <= 2.0 * args.h:
                    continue
                active_points.append(
                    Point(r=r, z=z, where=f"q={q:.6f} b={b:.6f} r={r:.6f} z={z:.6f}")
                )
            if not active_points:
                raise ValueError("active gate requested, but --active-qb-points is empty")
            points[name] = active_points
        else:
            raise ValueError(f"unknown gate {name!r}")
    return points


def evaluate(
    data: dict[str, object],
    gate_points: dict[str, list[Point]],
    score_gates: tuple[str, ...],
    h: float,
    abort_score_max: float | None = None,
) -> Evaluation | None:
    profile = profile_from_data(data)
    gamma = float(data["gamma"])
    gate_results: dict[str, GateResult] = {}
    ordered_gate_names = list(score_gates) + [
        gate_name for gate_name in gate_points if gate_name not in score_gates
    ]
    for gate_name in ordered_gate_names:
        points = gate_points[gate_name]
        is_score_gate = gate_name in score_gates
        worst = Residual(0.0, 0.0)
        worst_where = ""
        total = 0.0
        count = 0
        for point in points:
            residual = residual_at(profile.psi, profile.swirl, gamma, point.r, point.z, h)
            if (
                is_score_gate
                and abort_score_max is not None
                and residual.max_abs > abort_score_max
            ):
                return None
            total += residual.e_psi * residual.e_psi + residual.e_gamma * residual.e_gamma
            count += 2
            if residual.max_abs > worst.max_abs:
                worst = residual
                worst_where = point.where
        gate_results[gate_name] = GateResult(
            name=gate_name,
            max_abs=worst.max_abs,
            rms=math.sqrt(total / max(count, 1)),
            e_psi=worst.e_psi,
            e_gamma=worst.e_gamma,
            where=worst_where,
        )
    return Evaluation(gate_results=gate_results, score_gates=score_gates)


def better(new: Evaluation, old: Evaluation, min_improvement: float) -> bool:
    if new.score_max < old.score_max - min_improvement:
        return True
    if abs(new.score_max - old.score_max) <= min_improvement:
        return new.score_rms < old.score_rms - min_improvement
    return False


def metric_summary(evaluation: Evaluation) -> str:
    parts = [
        f"score_max={evaluation.score_max:.12e}",
        f"score_rms={evaluation.score_rms:.12e}",
        f"report_max={evaluation.report_max:.12e}",
    ]
    for name in sorted(evaluation.gate_results):
        result = evaluation.gate_results[name]
        parts.append(f"{name}={result.max_abs:.12e}")
    return " ".join(parts)


def save_data(
    path: str,
    data: dict[str, object],
    source: str,
    evaluation: Evaluation,
    args: argparse.Namespace,
) -> None:
    out = copy.deepcopy(data)
    out["evidence"] = {
        "status": "approximate_non_validated_minimax_coordinate_seed",
        "source": source,
        "h": args.h,
        "score_gates": list(evaluation.score_gates),
        "report_gates": sorted(evaluation.gate_results),
        "score_max": evaluation.score_max,
        "score_rms": evaluation.score_rms,
        "report_max": evaluation.report_max,
        "initial_step": args.step,
        "final_step": args._final_step,
        "minimax_gate_metrics": {
            name: {
                "max_abs": result.max_abs,
                "rms": result.rms,
                "e_psi": result.e_psi,
                "e_gamma": result.e_gamma,
                "where": result.where,
            }
            for name, result in sorted(evaluation.gate_results.items())
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")


def run_search(
    data: dict[str, object],
    variables: list[Variable],
    gate_points: dict[str, list[Point]],
    score_gates: tuple[str, ...],
    args: argparse.Namespace,
) -> tuple[dict[str, object], Evaluation, float]:
    best_data = copy.deepcopy(data)
    best_eval = evaluate(best_data, gate_points, score_gates, args.h)
    if best_eval is None:
        raise RuntimeError("initial evaluation unexpectedly aborted")
    step = args.step
    print(f"iter=-01 step={step:.12e} {metric_summary(best_eval)}")
    for pass_index in range(args.passes):
        accepted = 0
        for variable in variables:
            current = get_coeff(best_data, variable)
            local_data = best_data
            local_eval = best_eval
            local_value = current
            for direction in (1.0, -1.0):
                trial_value = current + direction * step
                if args.max_coeff_abs > 0.0 and abs(trial_value) > args.max_coeff_abs:
                    continue
                trial_data = copy.deepcopy(best_data)
                set_coeff(trial_data, variable, trial_value)
                trial_eval = evaluate(
                    trial_data,
                    gate_points,
                    score_gates,
                    args.h,
                    abort_score_max=local_eval.score_max + args.min_improvement,
                )
                if trial_eval is None:
                    continue
                if better(trial_eval, local_eval, args.min_improvement):
                    local_data = trial_data
                    local_eval = trial_eval
                    local_value = trial_value
            if local_data is not best_data:
                delta = local_value - current
                best_data = local_data
                best_eval = local_eval
                accepted += 1
                print(
                    f"iter={pass_index:03d} accept {variable.label} "
                    f"delta={delta:.12e} value={local_value:.12e} {metric_summary(best_eval)}"
                )
        print(
            f"pass={pass_index:03d} accepted={accepted} step={step:.12e} "
            f"{metric_summary(best_eval)}"
        )
        if accepted == 0:
            step *= args.shrink
            if step < args.min_step:
                break
    return best_data, best_eval, step


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--save-json", default="")
    parser.add_argument(
        "--families",
        default="f_interior_bump_coeffs",
        help="Comma-separated coefficient families to vary.",
    )
    parser.add_argument(
        "--add-missing-interior-bumps",
        default="",
        help="Optionally add zero F/G interior bump coefficients before varying.",
    )
    parser.add_argument("--score-gates", default="wide,interior,local")
    parser.add_argument("--report-gates", default="wide,interior,local,farther")
    parser.add_argument(
        "--active-qb-points",
        default="",
        help="Semicolon-separated q,b points for an optional active gate.",
    )
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--passes", type=positive_int, default=4)
    parser.add_argument("--step", type=float, default=2.5e-4)
    parser.add_argument("--min-step", type=float, default=1e-5)
    parser.add_argument("--shrink", type=float, default=0.5)
    parser.add_argument("--min-improvement", type=float, default=1e-8)
    parser.add_argument(
        "--max-coeff-abs",
        type=float,
        default=5e-2,
        help="Positive cap for varied coefficient absolute values; set <=0 to disable.",
    )
    parser.add_argument(
        "--zero-only-tol",
        type=float,
        default=-1.0,
        help=(
            "If nonnegative, vary only coefficients whose starting absolute "
            "value is at most this tolerance. Useful after expanding a bump grid."
        ),
    )
    parser.add_argument("--wide-n-q", type=positive_int, default=15)
    parser.add_argument("--wide-n-b", type=positive_int, default=15)
    parser.add_argument("--interior-n-q", type=positive_int, default=15)
    parser.add_argument("--interior-n-b", type=positive_int, default=15)
    parser.add_argument("--local-n", type=positive_int, default=23)
    parser.add_argument("--farther-n-q", type=positive_int, default=9)
    parser.add_argument("--farther-n-b", type=positive_int, default=17)
    parser.add_argument("--extreme-n-q", type=positive_int, default=15)
    parser.add_argument("--extreme-n-b", type=positive_int, default=15)
    args = parser.parse_args()

    if args.step <= 0.0:
        raise SystemExit("--step must be positive")
    if not (0.0 < args.shrink < 1.0):
        raise SystemExit("--shrink must lie in (0,1)")

    data = load_data(args.seed_json)
    ensure_missing_interior_bumps(data, parse_bump_kinds(args.add_missing_interior_bumps))
    families = parse_families(args.families)
    score_gates = parse_csv(args.score_gates)
    report_gates = tuple(dict.fromkeys(score_gates + parse_csv(args.report_gates)))
    gate_points = build_gate_points(args, report_gates)
    variables = variables_from_data(data, families, args.zero_only_tol)
    if not variables:
        raise SystemExit("no variables selected")
    missing_score = [name for name in score_gates if name not in gate_points]
    if missing_score:
        raise SystemExit(f"score gates missing from report gates: {', '.join(missing_score)}")
    print(
        f"seed={args.seed_json} variables={len(variables)} "
        f"families={','.join(families)} score_gates={','.join(score_gates)} "
        f"report_gates={','.join(report_gates)} h={args.h:.3e}"
    )
    for name, points in gate_points.items():
        print(f"gate_points {name}={len(points)}")

    best_data, best_eval, final_step = run_search(data, variables, gate_points, score_gates, args)
    args._final_step = final_step
    print(f"\nfinal step={final_step:.12e} {metric_summary(best_eval)}")
    for name in sorted(best_eval.gate_results):
        result = best_eval.gate_results[name]
        print(
            f"gate {name}: max_abs={result.max_abs:.12e} rms={result.rms:.12e} "
            f"e_psi={result.e_psi:.12e} e_gamma={result.e_gamma:.12e} {result.where}"
        )
    if args.save_json:
        save_data(args.save_json, best_data, args.seed_json, best_eval, args)
        print(f"saved seed json: {args.save_json}")


if __name__ == "__main__":
    main()
