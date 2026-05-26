#!/usr/bin/env python3
"""Low-order coefficient search for the compactified profile residual.

This is a deliberately small, dependency-free optimizer. It tries to reduce the
axisymmetric residual over a low-order even polynomial ansatz for F(q,b), G(q,b).
It is not a substitute for the required Newton-Kantorovich validation.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from axisym_residual import residual_at
from compactified_profile import CompactifiedProfile, Coeff, grid


Basis = list[tuple[str, int, int]]


@dataclass
class Candidate:
    basis: Basis
    values: list[float]
    gamma: float

    def coeffs(self, kind: str) -> tuple[Coeff, ...]:
        coeffs: list[Coeff] = []
        for (basis_kind, i, j), value in zip(self.basis, self.values):
            if basis_kind == kind:
                coeffs.append((i, j, value))
        return tuple(coeffs)

    def profile(self) -> CompactifiedProfile:
        return CompactifiedProfile(
            gamma=self.gamma,
            f_coeffs=self.coeffs("F"),
            g_coeffs=self.coeffs("G"),
        )


def build_basis(q_order: int, b_order: int) -> Basis:
    basis: Basis = []
    for kind in ("F", "G"):
        for i in range(q_order + 1):
            for j in range(b_order + 1):
                basis.append((kind, i, j))
    return basis


def initial_values(basis: Basis, B: float) -> list[float]:
    values: list[float] = []
    for kind, i, j in basis:
        if kind == "F" and i == 0 and j == 0:
            values.append(0.5)
        elif kind == "G" and i == 0 and j == 0:
            values.append(B)
        else:
            values.append(0.0)
    return values


def objective(
    candidate: Candidate,
    r_min: float,
    r_max: float,
    z_min: float,
    z_max: float,
    n: int,
    h: float,
) -> float:
    profile = candidate.profile()
    total = 0.0
    count = 0
    for r in grid(r_min, r_max, n):
        if r <= 2.0 * h:
            continue
        for z in grid(z_min, z_max, n):
            res = residual_at(profile.psi, profile.swirl, candidate.gamma, r, z, h)
            total += res.e_psi * res.e_psi + res.e_gamma * res.e_gamma
            count += 2
    return math.sqrt(total / max(count, 1))


def coordinate_search(
    candidate: Candidate,
    B: float,
    r_min: float,
    r_max: float,
    z_min: float,
    z_max: float,
    n: int,
    h: float,
    step: float,
    iterations: int,
) -> tuple[Candidate, float]:
    best = objective(candidate, r_min, r_max, z_min, z_max, n, h)
    current_step = step
    for iteration in range(iterations):
        improved = False
        for k, label in enumerate(candidate.basis):
            # Keep the two constant coefficients anchored enough to avoid
            # collapsing immediately to the trivial zero profile.
            if label == ("F", 0, 0) or label == ("G", 0, 0):
                continue
            for direction in (1.0, -1.0):
                trial_values = list(candidate.values)
                trial_values[k] += direction * current_step
                trial = Candidate(candidate.basis, trial_values, candidate.gamma)
                score = objective(trial, r_min, r_max, z_min, z_max, n, h)
                if score < best:
                    candidate = trial
                    best = score
                    improved = True
                    print(
                        f"iter={iteration:03d} improved {label} "
                        f"dir={direction:+.0f} score={best:.12e}"
                    )
                    break
        if not improved:
            current_step *= 0.5
            print(
                f"iter={iteration:03d} no improvement; "
                f"step -> {current_step:.6e}; score={best:.12e}"
            )
        if current_step < 1e-6:
            break
    return candidate, best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--B", type=float, default=1.0)
    parser.add_argument("--q-order", type=int, default=2)
    parser.add_argument("--b-order", type=int, default=1)
    parser.add_argument("--r-min", type=float, default=0.8)
    parser.add_argument("--r-max", type=float, default=2.0)
    parser.add_argument("--z-min", type=float, default=-1.0)
    parser.add_argument("--z-max", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--h", type=float, default=1e-3)
    parser.add_argument("--step", type=float, default=0.1)
    parser.add_argument("--iterations", type=int, default=8)
    args = parser.parse_args()

    basis = build_basis(args.q_order, args.b_order)
    candidate = Candidate(basis=basis, values=initial_values(basis, args.B), gamma=args.gamma)
    initial = objective(candidate, args.r_min, args.r_max, args.z_min, args.z_max, args.n, args.h)
    print(f"initial objective={initial:.12e}")
    candidate, best = coordinate_search(
        candidate,
        B=args.B,
        r_min=args.r_min,
        r_max=args.r_max,
        z_min=args.z_min,
        z_max=args.z_max,
        n=args.n,
        h=args.h,
        step=args.step,
        iterations=args.iterations,
    )
    print(f"\nbest objective={best:.12e}")
    print("F coefficients:")
    for coeff in candidate.coeffs("F"):
        print(f"  {coeff[0]},{coeff[1]},{coeff[2]:+.12e}")
    print("G coefficients:")
    for coeff in candidate.coeffs("G"):
        print(f"  {coeff[0]},{coeff[1]},{coeff[2]:+.12e}")


if __name__ == "__main__":
    main()
