#!/usr/bin/env python3
"""Survey numerical stability of indicial shooting candidates.

This is not an interval validator. It is a reproducibility tool that checks
whether candidate indicial exponents persist when the shooting truncation,
step count, and Frobenius order are changed. A real root should have a small
residual and should not drift substantially under these changes.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from indicial_solver import residual, residual_components


@dataclass(frozen=True)
class Setting:
    eps: float
    L: float
    steps: int
    terms: int


@dataclass(frozen=True)
class CandidateResult:
    start: complex
    z: complex
    score: float
    setting: Setting


def parse_candidates(raw: str) -> list[complex]:
    candidates: list[complex] = []
    for item in raw.split(";"):
        item = item.strip()
        if not item:
            continue
        parts = item.split(",")
        if len(parts) != 2:
            raise ValueError(f"bad candidate {item!r}; expected real,imag")
        candidates.append(complex(float(parts[0]), float(parts[1])))
    if not candidates:
        raise ValueError("at least one candidate is required")
    return candidates


def parse_settings(raw: str) -> list[Setting]:
    settings: list[Setting] = []
    for item in raw.split(";"):
        item = item.strip()
        if not item:
            continue
        parts = item.split(",")
        if len(parts) != 4:
            raise ValueError(f"bad setting {item!r}; expected eps,L,steps,terms")
        settings.append(
            Setting(
                eps=float(parts[0]),
                L=float(parts[1]),
                steps=int(parts[2]),
                terms=int(parts[3]),
            )
        )
    if not settings:
        raise ValueError("at least one setting is required")
    return settings


def quiet_optimize(
    start: complex,
    gamma: float,
    B: float,
    setting: Setting,
    step_real: float,
    step_imag: float,
    iterations: int,
    min_real: float,
    max_abs_imag: float,
) -> tuple[complex, float]:
    z = start
    best = residual(z, gamma, B, setting.eps, setting.L, setting.steps, setting.terms)
    directions = (
        complex(1.0, 0.0),
        complex(-1.0, 0.0),
        complex(0.0, 1.0),
        complex(0.0, -1.0),
        complex(1.0, 1.0),
        complex(1.0, -1.0),
        complex(-1.0, 1.0),
        complex(-1.0, -1.0),
    )
    dr = step_real
    di = step_imag
    for _ in range(iterations):
        improved = False
        candidate_z = z
        candidate_best = best
        for direction in directions:
            trial = z + complex(direction.real * dr, direction.imag * di)
            if trial.real < min_real or abs(trial.imag) > max_abs_imag:
                continue
            score = residual(
                trial,
                gamma,
                B,
                setting.eps,
                setting.L,
                setting.steps,
                setting.terms,
            )
            if score < candidate_best:
                candidate_z = trial
                candidate_best = score
                improved = True
        if improved:
            z = candidate_z
            best = candidate_best
        else:
            dr *= 0.5
            di *= 0.5
        if max(dr, di) < 1e-8:
            break
    return z, best


def cluster_width(values: list[complex]) -> float:
    width = 0.0
    for i, z_i in enumerate(values):
        for z_j in values[i + 1 :]:
            width = max(width, abs(z_i - z_j))
    return width


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument(
        "--candidates",
        default="0.13251953125,1.787841796875;0.045959472656,1.784820556641",
    )
    parser.add_argument(
        "--settings",
        default="1e-4,25,8000,10;1e-4,40,10000,10;5e-5,40,12000,12",
    )
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--step-real", type=float, default=0.02)
    parser.add_argument("--step-imag", type=float, default=0.08)
    parser.add_argument("--iterations", type=int, default=18)
    parser.add_argument("--min-real", type=float, default=1e-4)
    parser.add_argument("--max-abs-imag", type=float, default=8.0)
    parser.add_argument("--root-threshold", type=float, default=1e-3)
    parser.add_argument("--components", action="store_true")
    args = parser.parse_args()

    if not (0.4 < args.gamma < 0.5):
        raise SystemExit("gamma must lie in (2/5,1/2).")

    candidates = parse_candidates(args.candidates)
    settings = parse_settings(args.settings)
    if args.components:
        print("start,eps,L,steps,terms,opt_delta,residual,n_phi,n_chi,n_amp,n_h,root_like")
    else:
        print("start,eps,L,steps,terms,opt_delta,residual,root_like")
    grouped: dict[complex, list[CandidateResult]] = {}
    for start in candidates:
        grouped[start] = []
        for setting in settings:
            if args.optimize:
                z, score = quiet_optimize(
                    start,
                    args.gamma,
                    args.B,
                    setting,
                    args.step_real,
                    args.step_imag,
                    args.iterations,
                    args.min_real,
                    args.max_abs_imag,
                )
            else:
                z = start
                score = residual(
                    z,
                    args.gamma,
                    args.B,
                    setting.eps,
                    setting.L,
                    setting.steps,
                    setting.terms,
                )
            grouped[start].append(CandidateResult(start=start, z=z, score=score, setting=setting))
            root_like = "yes" if score <= args.root_threshold else "no"
            prefix = (
                f"{start.real:.12f}{start.imag:+.12f}i,"
                f"{setting.eps:.3e},{setting.L:.6g},{setting.steps},{setting.terms},"
                f"{z.real:.12f}{z.imag:+.12f}i,{score:.12e}"
            )
            if args.components:
                components = residual_components(
                    z,
                    args.gamma,
                    args.B,
                    setting.eps,
                    setting.L,
                    setting.steps,
                    setting.terms,
                )
                print(
                    f"{prefix},{components.n_phi:.12e},{components.n_chi:.12e},"
                    f"{components.n_amp:.12e},{components.n_h:.12e},{root_like}"
                )
            else:
                print(f"{prefix},{root_like}")

    print("\nSummary:")
    for start, results in grouped.items():
        scores = [item.score for item in results]
        zs = [item.z for item in results]
        print(
            f"start={start.real:.12f}{start.imag:+.12f}i "
            f"best={min(scores):.12e} worst={max(scores):.12e} "
            f"delta_spread={cluster_width(zs):.12e}"
        )


if __name__ == "__main__":
    main()
